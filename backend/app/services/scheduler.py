"""
APScheduler background job — polls Polymarket every 30 seconds for new bets
and fires notifications to subscribed users.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import AlertSetting, BetEvent, BettorFollow, User
from app.services.notifications import dispatch_bet_notification
from app.services.polymarket import get_recent_bets

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None
_last_check: datetime = datetime.now(tz=timezone.utc)


def _parse_timestamp(ts_value) -> Optional[datetime]:
    """Parse various timestamp formats into a timezone-aware datetime."""
    if not ts_value:
        return None
    if isinstance(ts_value, datetime):
        return ts_value if ts_value.tzinfo else ts_value.replace(tzinfo=timezone.utc)
    if isinstance(ts_value, (int, float)):
        try:
            return datetime.fromtimestamp(ts_value, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(ts_value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                dt = datetime.strptime(ts_value, fmt)
                return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


async def _poll_bets() -> None:
    global _last_check

    db: Session = SessionLocal()
    try:
        # Gather unique bettor addresses being followed
        addresses = [row[0] for row in db.query(BettorFollow.bettor_address).distinct().all()]
        if not addresses:
            return

        check_time = datetime.now(tz=timezone.utc)

        for address in addresses:
            try:
                bets = await get_recent_bets(address, limit=10)
            except Exception as exc:
                logger.warning("Failed to fetch bets for %s: %s", address, exc)
                continue

            # Compute avg bet size from recent bets for conviction score
            bet_amounts = [b.get("amount_usd", 0.0) for b in bets if b.get("amount_usd", 0.0) > 0]
            avg_bet_usd = sum(bet_amounts) / len(bet_amounts) if bet_amounts else 0.0

            for bet in bets:
                ts = _parse_timestamp(bet.get("timestamp"))
                if ts and ts <= _last_check:
                    continue  # Already seen

                # Check for duplicate in DB
                exists = (
                    db.query(BetEvent)
                    .filter(
                        BetEvent.bettor_address == address,
                        BetEvent.market_id == bet.get("market_id", ""),
                        BetEvent.timestamp == ts,
                    )
                    .first()
                )
                if exists:
                    continue

                # Save new bet event
                event = BetEvent(
                    bettor_address=address,
                    market_id=bet.get("market_id", ""),
                    market_question=bet.get("market_question", ""),
                    outcome=str(bet.get("outcome", "")),
                    amount_usd=bet.get("amount_usd", 0.0),
                    timestamp=ts,
                    notified=False,
                )
                db.add(event)
                db.flush()

                # Find all users following this bettor
                followers = (
                    db.query(BettorFollow)
                    .filter(BettorFollow.bettor_address == address)
                    .all()
                )

                for follow in followers:
                    user: Optional[User] = db.query(User).filter(User.id == follow.user_id).first()
                    if not user or not user.is_active or user.subscription_tier == "free":
                        continue

                    alert = (
                        db.query(AlertSetting)
                        .filter(AlertSetting.user_id == user.id)
                        .first()
                    )

                    from app.config import get_settings
                    cfg = get_settings()

                    # Compute conviction score: how large is this bet vs bettor's average?
                    bet_amount = bet.get("amount_usd", 0.0)
                    if avg_bet_usd > 0 and bet_amount > 0:
                        conviction_score = round(bet_amount / avg_bet_usd, 1)
                    else:
                        conviction_score = 1.0
                    if conviction_score >= 10.0:
                        conviction_label = "EXTREME"
                    elif conviction_score >= 3.0:
                        conviction_label = "HIGH"
                    else:
                        conviction_label = ""

                    try:
                        await dispatch_bet_notification(
                            bettor_name=follow.bettor_name or address[:12],
                            market=bet.get("market_question", ""),
                            outcome=str(bet.get("outcome", "")),
                            amount=bet_amount,
                            telegram_chat_id=user.telegram_chat_id if (alert and alert.telegram_enabled and user.telegram_verified) else None,
                            telegram_bot_token=cfg.telegram_bot_token,
                            push_subscription_json=alert.push_subscription if (alert and alert.web_push_enabled) else None,
                            phone_number=user.phone_number if (alert and alert.sms_enabled and user.phone_verified) else None,
                            sms_enabled=bool(alert and alert.sms_enabled and user.phone_verified),
                            twilio_account_sid=cfg.twilio_account_sid,
                            twilio_auth_token=cfg.twilio_auth_token,
                            twilio_from_number=cfg.twilio_from_number,
                            user_tier=user.subscription_tier,
                            conviction_score=conviction_score,
                            conviction_label=conviction_label,
                        )
                    except Exception as exc:
                        logger.warning("Notification failed for user %s: %s", user.id, exc)

                event.notified = True

        db.commit()
        _last_check = check_time

    except Exception as exc:
        logger.error("Scheduler poll_bets error: %s", exc)
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_poll_bets, "interval", seconds=30, id="poll_bets", replace_existing=True)
    _scheduler.start()
    logger.info("Scheduler started — polling every 30 seconds")
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
