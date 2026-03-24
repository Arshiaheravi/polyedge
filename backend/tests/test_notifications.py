"""Unit tests for notification service functions."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.notifications import (
    format_bet_message,
    format_sms_message,
    dispatch_bet_notification,
)


def test_format_bet_message():
    msg = format_bet_message("Alice", "Will BTC hit 100k?", "Yes", 500.0)
    assert "Alice" in msg
    assert "$500.00" in msg
    assert "Yes" in msg


def test_format_bet_message_truncates_long_market():
    long_market = "A" * 100
    msg = format_bet_message("Bob", long_market, "No", 100.0)
    assert len(msg) < 500  # sanity check — no runaway strings


def test_format_sms_message():
    msg = format_sms_message("Alice", "Will BTC hit 100k?", "Yes", 500.0)
    assert "Alice" in msg
    assert "Yes" in msg
    assert len(msg) <= 160  # SMS limit


def test_format_sms_message_truncates_market():
    long_market = "B" * 100
    msg = format_sms_message("Bob", long_market, "No", 200.0)
    assert len(msg) <= 160


@pytest.mark.asyncio
async def test_dispatch_free_tier_no_notifications():
    results = await dispatch_bet_notification(
        bettor_name="Alice",
        market="Test market",
        outcome="Yes",
        amount=100.0,
        telegram_chat_id="12345",
        telegram_bot_token="token",
        push_subscription_json='{"endpoint":"https://example.com"}',
        user_tier="free",
    )
    # Free tier gets nothing
    assert results == {}


@pytest.mark.asyncio
async def test_dispatch_basic_tier_gets_telegram_and_push():
    with patch("app.services.notifications.send_telegram", new=AsyncMock(return_value=True)) as mock_tg, \
         patch("app.services.notifications.send_web_push", new=AsyncMock(return_value=True)) as mock_push:
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=50.0,
            telegram_chat_id="999",
            telegram_bot_token="bottoken",
            push_subscription_json='{"endpoint":"https://push.example.com"}',
            user_tier="basic",
        )
    assert results.get("telegram") is True
    assert results.get("web_push") is True
    assert "sms" not in results


@pytest.mark.asyncio
async def test_dispatch_vip_gets_sms():
    with patch("app.services.notifications.send_telegram", new=AsyncMock(return_value=True)), \
         patch("app.services.notifications.send_web_push", new=AsyncMock(return_value=True)), \
         patch("app.services.notifications.send_sms", new=AsyncMock(return_value=True)) as mock_sms:
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=50.0,
            telegram_chat_id="999",
            telegram_bot_token="bottoken",
            push_subscription_json='{"endpoint":"https://push.example.com"}',
            phone_number="+14155552671",
            sms_enabled=True,
            twilio_account_sid="ACtest",
            twilio_auth_token="authtoken",
            twilio_from_number="+15005550006",
            user_tier="vip",
        )
    assert results.get("sms") is True
    mock_sms.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_vip_no_sms_if_disabled():
    with patch("app.services.notifications.send_sms", new=AsyncMock(return_value=True)) as mock_sms:
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=50.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json=None,
            phone_number="+14155552671",
            sms_enabled=False,  # disabled
            user_tier="vip",
        )
    assert "sms" not in results
    mock_sms.assert_not_called()
