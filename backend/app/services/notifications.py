"""
Notification dispatcher — Telegram + Web Push + SMS (Twilio).
"""
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


async def send_telegram(chat_id: str, message: str, bot_token: str) -> bool:
    """Send a Telegram message. Returns True on success."""
    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            )
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.warning("Telegram send failed for chat_id=%s: %s", chat_id, exc)
        return False


def format_bet_message(
    bettor_name: str,
    market: str,
    outcome: str,
    amount: float,
    conviction_score: float = 1.0,
    conviction_label: str = "",
) -> str:
    """Format a bet notification message for Telegram."""
    market_display = market[:80] + "..." if len(market) > 80 else market
    conviction_line = ""
    if conviction_label == "EXTREME":
        conviction_line = f"🔥 <b>EXTREME conviction bet ({conviction_score:.1f}x avg)</b>\n"
    elif conviction_label == "HIGH":
        conviction_line = f"⚡ <b>HIGH conviction bet ({conviction_score:.1f}x avg)</b>\n"
    return (
        f"<b>{bettor_name}</b> just placed a bet!\n"
        f"{conviction_line}\n"
        f"<b>Market:</b> {market_display}\n"
        f"<b>Outcome:</b> {outcome}\n"
        f"<b>Amount:</b> ${amount:,.2f}\n\n"
        f"Copy this bet now on Polymarket!"
    )


def format_exit_message(bettor_name: str, market: str, outcome: str) -> str:
    """Format an exit alert notification message for Telegram."""
    market_display = market[:80] + "..." if len(market) > 80 else market
    return (
        f"⚡ <b>{bettor_name}</b> is EXITING a position!\n\n"
        f"<b>Market:</b> {market_display}\n"
        f"<b>Outcome:</b> {outcome}\n\n"
        f"Consider taking profit on this position."
    )


async def send_web_push(
    push_subscription_json: str,
    payload: dict,
    vapid_private_key: str = "",
    vapid_public_key: str = "",
    vapid_claims_email: str = "admin@polyedge.com",
) -> bool:
    """
    Send a Web Push notification using VAPID signing (pywebpush).
    Returns True on success, False if VAPID keys are not configured or send fails.

    Requires VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY in .env.
    Generate keys with: py -c "from pywebpush import Vapid; v=Vapid(); v.generate_keys(); print('Private:', v.private_key.encode()); print('Public:', v.public_key.encode())"
    """
    if not vapid_private_key or not vapid_public_key:
        logger.info("Web push skipped: VAPID keys not configured (set VAPID_PUBLIC_KEY + VAPID_PRIVATE_KEY in .env)")
        return False

    try:
        from pywebpush import webpush, WebPushException  # noqa: PLC0415

        sub = json.loads(push_subscription_json) if isinstance(push_subscription_json, str) else push_subscription_json
        endpoint = sub.get("endpoint")
        if not endpoint:
            return False

        import asyncio  # noqa: PLC0415
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: webpush(
                subscription_info=sub,
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": f"mailto:{vapid_claims_email}"},
            ),
        )
        return True
    except Exception as exc:
        logger.warning("Web push failed: %s", exc)
        return False


async def send_sms(to_number: str, message: str, account_sid: str, auth_token: str, from_number: str) -> bool:
    """Send an SMS via Twilio REST API. Returns True on success."""
    if not all([account_sid, auth_token, from_number, to_number]):
        return False
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                url,
                data={"To": to_number, "From": from_number, "Body": message},
                auth=(account_sid, auth_token),
            )
            resp.raise_for_status()
            return True
    except Exception as exc:
        logger.warning("SMS send failed for %s: %s", to_number, exc)
        return False


def format_sms_message(bettor_name: str, market: str, outcome: str, amount: float) -> str:
    """Short SMS format (160 chars max)."""
    short_market = market[:60] + "..." if len(market) > 60 else market
    return f"PolyEdge: {bettor_name} bet ${amount:,.0f} on {outcome} — {short_market}"


async def dispatch_bet_notification(
    *,
    bettor_name: str,
    market: str,
    outcome: str,
    amount: float,
    telegram_chat_id: Optional[str],
    telegram_bot_token: str,
    push_subscription_json: Optional[str],
    phone_number: Optional[str] = None,
    sms_enabled: bool = False,
    twilio_account_sid: str = "",
    twilio_auth_token: str = "",
    twilio_from_number: str = "",
    user_tier: str,
    conviction_score: float = 1.0,
    conviction_label: str = "",
    vapid_private_key: str = "",
    vapid_public_key: str = "",
    vapid_claims_email: str = "admin@polyedge.com",
) -> dict:
    """
    Dispatch notifications to a single user for a new bet event.
    Tier rules:
      Basic: web push + Telegram
      VIP:   web push + Telegram + SMS
    conviction_score: bet_amount / bettor_avg_bet (1.0 = baseline, 3x = HIGH, 10x = EXTREME)
    Returns a dict of {channel: success_bool}.
    """
    results = {}
    message = format_bet_message(bettor_name, market, outcome, amount, conviction_score, conviction_label)

    # Telegram: Basic and VIP
    if user_tier in ("basic", "vip") and telegram_chat_id and telegram_bot_token:
        results["telegram"] = await send_telegram(telegram_chat_id, message, telegram_bot_token)

    # Web push: Basic and VIP
    if user_tier in ("basic", "vip") and push_subscription_json:
        push_title = f"{bettor_name} placed a bet!"
        if conviction_label == "EXTREME":
            push_title = f"🔥 EXTREME conviction — {bettor_name} bet {conviction_score:.1f}x avg!"
        elif conviction_label == "HIGH":
            push_title = f"⚡ HIGH conviction — {bettor_name} bet {conviction_score:.1f}x avg!"
        push_payload = {
            "title": push_title,
            "body": f"{market[:60]}... — ${amount:,.2f} on {outcome}",
            "icon": "/icon.png",
        }
        results["web_push"] = await send_web_push(
            push_subscription_json,
            push_payload,
            vapid_private_key=vapid_private_key,
            vapid_public_key=vapid_public_key,
            vapid_claims_email=vapid_claims_email,
        )

    # SMS: VIP only
    if user_tier == "vip" and sms_enabled and phone_number:
        sms_body = format_sms_message(bettor_name, market, outcome, amount)
        results["sms"] = await send_sms(
            phone_number, sms_body, twilio_account_sid, twilio_auth_token, twilio_from_number
        )

    return results
