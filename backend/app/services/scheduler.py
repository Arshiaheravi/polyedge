"""
APScheduler background job — polls Polymarket every 30 seconds for new bets
and fires notifications to subscribed users.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import AlertSetting, BetEvent, BettorFollow, User
from app.services.notifications import dispatch_bet_notification, format_exit_message, send_telegram, send_web_push
from app.services.polymarket import get_active_positions, get_recent_bets

logger = logging.getLogger(__name__)

_scheduler: Optional[AsyncIOScheduler] = None
_last_check: datetime = datetime.now(tz=timezone.utc)
# Maps bettor_address → {condition_id: size} from the previous poll cycle
_last_positions: dict = {}


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


async def _detect_exits(db: Session, addresses: list) -> None:
    """
    Compare current open positions to last poll's positions per bettor.
    If a conditionId disappears or drops >50% in size, treat it as an exit.
    Fire exit notifications to VIP-tier followers only.
    Store a BetEvent(event_type="EXIT") for every exit detected (all tiers).
    """
    global _last_positions

    cfg = get_settings()

    for address in addresses:
        try:
            positions = await get_active_positions(address)
        except Exception as exc:
            logger.warning("Exit detection: failed to fetch positions for %s: %s", address, exc)
            continue

        # Build current position map: {condition_id: size}
        current_map = {p["condition_id"]: p["size"] for p in positions if p.get("condition_id")}
        prev_map: dict = _last_positions.get(address, {})

        if not prev_map:
            # First run for this address — just record current state
            _last_positions[address] = current_map
            continue

        # Find exits: condition_ids present before but gone or shrunk >50%
        exits = []
        for cid, prev_size in prev_map.items():
            cur_size = current_map.get(cid, 0.0)
            if cur_size == 0.0 or (prev_size > 0 and cur_size < prev_size * 0.5):
                # Find the position metadata from the previous positions list
                # Use the title from current positions if still present, else log plain
                market_title = ""
                outcome = ""
                for p in positions:
                    if p.get("condition_id") == cid:
                        market_title = p.get("market_title", "")
                        outcome = p.get("outcome", "")
                        break
                exits.append({"condition_id": cid, "market_title": market_title, "outcome": outcome})

        # Update stored positions
        _last_positions[address] = current_map

        if not exits:
            continue

        # Get bettor name from any follow record
        follow_for_name = (
            db.query(BettorFollow)
            .filter(BettorFollow.bettor_address == address)
            .first()
        )
        bettor_name = (follow_for_name.bettor_name or address[:12]) if follow_for_name else address[:12]

        # All followers of this bettor
        followers = (
            db.query(BettorFollow)
            .filter(BettorFollow.bettor_address == address)
            .all()
        )

        for exit_pos in exits:
            # Store BetEvent(event_type="EXIT") for all tiers (analytics)
            exit_event = BetEvent(
                bettor_address=address,
                market_id=exit_pos["condition_id"],
                market_question=exit_pos["market_title"],
                outcome=exit_pos["outcome"],
                amount_usd=0.0,
                timestamp=datetime.now(tz=timezone.utc),
                notified=False,
                event_type="EXIT",
            )
            db.add(exit_event)
            db.flush()

            message = format_exit_message(bettor_name, exit_pos["market_title"], exit_pos["outcome"])

            # Send notifications to VIP followers only
            for follow in followers:
                user: Optional[User] = db.query(User).filter(User.id == follow.user_id).first()
                if not user or not user.is_active or user.subscription_tier != "vip":
                    continue

                alert = (
                    db.query(AlertSetting)
                    .filter(AlertSetting.user_id == user.id)
                    .first()
                )

                try:
                    # Telegram
                    if alert and alert.telegram_enabled and user.telegram_verified and user.telegram_chat_id:
                        await send_telegram(user.telegram_chat_id, message, cfg.telegram_bot_token)
                    # Web push
                    if alert and alert.web_push_enabled and alert.push_subscription:
                        push_payload = {
                            "title": f"⚡ {bettor_name} is exiting a position!",
                            "body": f"{exit_pos['market_title'][:60]} — consider taking profit",
                            "icon": "/icon.png",
                        }
                        await send_web_push(alert.push_subscription, push_payload)
                except Exception as exc:
                    logger.warning("Exit notification failed for user %s: %s", user.id, exc)

            exit_event.notified = True


async def _poll_bets() -> None:
    global _last_check

    db: Session = SessionLocal()
    try:
        # Gather unique bettor addresses being followed
        addresses = [row[0] for row in db.query(BettorFollow.bettor_address).distinct().all()]
        if not addresses:
            return

        # Purge stale _last_positions entries for bettors no longer followed
        stale = [addr for addr in _last_positions if addr not in addresses]
        for addr in stale:
            del _last_positions[addr]

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

                # Compute conviction score here so it can be stored on the event
                bet_amount = bet.get("amount_usd", 0.0)
                if avg_bet_usd > 0 and bet_amount > 0:
                    _conviction_score = round(bet_amount / avg_bet_usd, 1)
                else:
                    _conviction_score = 1.0
                if _conviction_score >= 10.0:
                    _conviction_label = "EXTREME"
                elif _conviction_score >= 3.0:
                    _conviction_label = "HIGH"
                else:
                    _conviction_label = ""

                # Save new bet event
                event = BetEvent(
                    bettor_address=address,
                    market_id=bet.get("market_id", ""),
                    market_question=bet.get("market_question", ""),
                    outcome=str(bet.get("outcome", "")),
                    amount_usd=bet.get("amount_usd", 0.0),
                    timestamp=ts,
                    notified=False,
                    conviction_score=_conviction_score,
                    conviction_label=_conviction_label,
                )
                db.add(event)
                db.flush()

                # Find all users following this bettor
                followers = (
                    db.query(BettorFollow)
                    .filter(BettorFollow.bettor_address == address)
                    .all()
                )

                cfg = get_settings()

                for follow in followers:
                    user: Optional[User] = db.query(User).filter(User.id == follow.user_id).first()
                    if not user or not user.is_active or user.subscription_tier == "free":
                        continue

                    alert = (
                        db.query(AlertSetting)
                        .filter(AlertSetting.user_id == user.id)
                        .first()
                    )

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
                            conviction_score=_conviction_score,
                            conviction_label=_conviction_label,
                            vapid_private_key=cfg.vapid_private_key,
                            vapid_public_key=cfg.vapid_public_key,
                            vapid_claims_email=cfg.vapid_claims_email,
                        )
                    except Exception as exc:
                        logger.warning("Notification failed for user %s: %s", user.id, exc)

                event.notified = True

        # --- Exit detection ---
        await _detect_exits(db, addresses)

        db.commit()
        _last_check = check_time

    except Exception as exc:
        logger.error("Scheduler poll_bets error: %s", exc)
        db.rollback()
    finally:
        db.close()


async def _poll_vip_bets() -> None:
    """Fast-path poll (every 5s) for bettor addresses followed by at least one VIP user."""
    global _last_check

    db: Session = SessionLocal()
    try:
        # Only poll addresses where a VIP user is a follower
        vip_user_ids = [
            row[0]
            for row in db.query(User.id).filter(User.subscription_tier == "vip").all()
        ]
        if not vip_user_ids:
            return

        addresses = [
            row[0]
            for row in db.query(BettorFollow.bettor_address)
            .filter(BettorFollow.user_id.in_(vip_user_ids))
            .distinct()
            .all()
        ]
        if not addresses:
            return

        check_time = datetime.now(tz=timezone.utc)

        for address in addresses:
            try:
                bets = await get_recent_bets(address, limit=10)
            except Exception as exc:
                logger.warning("VIP poll: failed to fetch bets for %s: %s", address, exc)
                continue

            bet_amounts = [b.get("amount_usd", 0.0) for b in bets if b.get("amount_usd", 0.0) > 0]
            avg_bet_usd = sum(bet_amounts) / len(bet_amounts) if bet_amounts else 0.0

            for bet in bets:
                ts = _parse_timestamp(bet.get("timestamp"))
                if ts and ts <= _last_check:
                    continue

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

                bet_amount = bet.get("amount_usd", 0.0)
                if avg_bet_usd > 0 and bet_amount > 0:
                    _conviction_score = round(bet_amount / avg_bet_usd, 1)
                else:
                    _conviction_score = 1.0
                _conviction_label = (
                    "EXTREME" if _conviction_score >= 10.0 else "HIGH" if _conviction_score >= 3.0 else ""
                )

                event = BetEvent(
                    bettor_address=address,
                    market_id=bet.get("market_id", ""),
                    market_question=bet.get("market_question", ""),
                    outcome=str(bet.get("outcome", "")),
                    amount_usd=bet_amount,
                    timestamp=ts,
                    notified=False,
                    conviction_score=_conviction_score,
                    conviction_label=_conviction_label,
                )
                db.add(event)
                db.flush()

                followers = (
                    db.query(BettorFollow)
                    .filter(BettorFollow.bettor_address == address)
                    .all()
                )

                cfg = get_settings()

                for follow in followers:
                    user: Optional[User] = db.query(User).filter(User.id == follow.user_id).first()
                    if not user or not user.is_active or user.subscription_tier == "free":
                        continue

                    alert = (
                        db.query(AlertSetting)
                        .filter(AlertSetting.user_id == user.id)
                        .first()
                    )

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
                            conviction_score=_conviction_score,
                            conviction_label=_conviction_label,
                            vapid_private_key=cfg.vapid_private_key,
                            vapid_public_key=cfg.vapid_public_key,
                            vapid_claims_email=cfg.vapid_claims_email,
                        )
                    except Exception as exc:
                        logger.warning("VIP notification failed for user %s: %s", user.id, exc)

                event.notified = True

        db.commit()
        _last_check = check_time

    except Exception as exc:
        logger.error("VIP poll_bets error: %s", exc)
        db.rollback()
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    cfg = get_settings()
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_poll_bets, "interval", seconds=cfg.default_poll_interval_seconds, id="poll_bets", replace_existing=True)
    _scheduler.add_job(_poll_vip_bets, "interval", seconds=cfg.vip_poll_interval_seconds, id="poll_vip_bets", replace_existing=True)
    _scheduler.start()
    logger.info(
        "Scheduler started — default poll every %ds, VIP poll every %ds",
        cfg.default_poll_interval_seconds,
        cfg.vip_poll_interval_seconds,
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
