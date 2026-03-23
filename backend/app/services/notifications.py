"""
Notification dispatcher — Telegram + Web Push.
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


def format_bet_message(bettor_name: str, market: str, outcome: str, amount: float) -> str:
    """Format a bet notification message for Telegram."""
    market_display = market[:80] + "..." if len(market) > 80 else market
    return (
        f"<b>{bettor_name}</b> just placed a bet!\n\n"
        f"<b>Market:</b> {market_display}\n"
        f"<b>Outcome:</b> {outcome}\n"
        f"<b>Amount:</b> ${amount:,.2f}\n\n"
        f"Copy this bet now on Polymarket!"
    )


async def send_web_push(push_subscription_json: str, payload: dict) -> bool:
    """
    Send a Web Push notification.
    push_subscription_json is the JSON string of the browser PushSubscription object.
    Returns True on success.

    NOTE: For production use, install pywebpush and use the VAPID keys.
    This implementation sends a raw POST to the push endpoint for demo purposes.
    In production, replace with:
        from pywebpush import webpush, WebPushException
        webpush(subscription_info=..., data=..., vapid_private_key=..., vapid_claims=...)
    """
    try:
        sub = json.loads(push_subscription_json) if isinstance(push_subscription_json, str) else push_subscription_json
        endpoint = sub.get("endpoint")
        if not endpoint:
            return False

        message = json.dumps(payload)
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                endpoint,
                content=message.encode(),
                headers={"Content-Type": "application/json", "TTL": "86400"},
            )
            # 201 or 200 means queued/delivered
            return resp.status_code in (200, 201)
    except Exception as exc:
        logger.warning("Web push failed: %s", exc)
        return False


async def dispatch_bet_notification(
    *,
    bettor_name: str,
    market: str,
    outcome: str,
    amount: float,
    telegram_chat_id: Optional[str],
    telegram_bot_token: str,
    push_subscription_json: Optional[str],
    user_tier: str,
) -> dict:
    """
    Dispatch notifications to a single user for a new bet event.
    Respects tier: VIP gets Telegram + push, Basic gets push only.
    Returns a dict of {channel: success_bool}.
    """
    results = {}
    message = format_bet_message(bettor_name, market, outcome, amount)

    # Telegram: Basic and VIP
    if user_tier in ("basic", "vip") and telegram_chat_id and telegram_bot_token:
        results["telegram"] = await send_telegram(telegram_chat_id, message, telegram_bot_token)

    # Web push: Basic and VIP
    if user_tier in ("basic", "vip") and push_subscription_json:
        push_payload = {
            "title": f"{bettor_name} placed a bet!",
            "body": f"{market[:60]}... — ${amount:,.2f} on {outcome}",
            "icon": "/icon.png",
        }
        results["web_push"] = await send_web_push(push_subscription_json, push_payload)

    return results
