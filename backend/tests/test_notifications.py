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


# ── 6 new targeted tests for dispatch_bet_notification ──────────────────────


@pytest.mark.asyncio
async def test_dispatch_basic_both_channels_none_returns_empty():
    """Basic tier with no chat_id and no push_subscription → nothing sent."""
    results = await dispatch_bet_notification(
        bettor_name="Alice",
        market="Test",
        outcome="Yes",
        amount=50.0,
        telegram_chat_id=None,
        telegram_bot_token="token",
        push_subscription_json=None,
        user_tier="basic",
    )
    assert results == {}


@pytest.mark.asyncio
async def test_dispatch_no_chat_id_skips_telegram():
    """telegram_chat_id=None → send_telegram never called even on basic tier."""
    with patch("app.services.notifications.send_telegram", new=AsyncMock(return_value=True)) as mock_tg:
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=50.0,
            telegram_chat_id=None,
            telegram_bot_token="sometoken",
            push_subscription_json=None,
            user_tier="basic",
        )
    assert "telegram" not in results
    mock_tg.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_no_push_subscription_skips_web_push():
    """push_subscription_json=None → send_web_push never called even on basic tier."""
    with patch("app.services.notifications.send_web_push", new=AsyncMock(return_value=True)) as mock_push:
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=50.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json=None,
            user_tier="basic",
        )
    assert "web_push" not in results
    mock_push.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_telegram_called_with_correct_args():
    """send_telegram is called with correct chat_id, message, and bot_token."""
    mock_tg = AsyncMock(return_value=True)
    with patch("app.services.notifications.send_telegram", new=mock_tg):
        await dispatch_bet_notification(
            bettor_name="Alice",
            market="Will BTC reach 100k?",
            outcome="Yes",
            amount=200.0,
            telegram_chat_id="chat_999",
            telegram_bot_token="bot_abc",
            push_subscription_json=None,
            user_tier="basic",
        )
    mock_tg.assert_called_once()
    call_args = mock_tg.call_args
    assert call_args[0][0] == "chat_999"   # first positional: chat_id
    assert call_args[0][2] == "bot_abc"    # third positional: bot_token
    assert "Alice" in call_args[0][1]      # second positional: message


@pytest.mark.asyncio
async def test_dispatch_web_push_called_with_subscription():
    """send_web_push is called with the push_subscription_json when present."""
    mock_push = AsyncMock(return_value=True)
    sub_json = '{"endpoint":"https://push.example.com","keys":{"p256dh":"abc","auth":"def"}}'
    with patch("app.services.notifications.send_web_push", new=mock_push):
        await dispatch_bet_notification(
            bettor_name="Bob",
            market="Test market",
            outcome="No",
            amount=75.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json=sub_json,
            user_tier="basic",
        )
    mock_push.assert_called_once()
    assert mock_push.call_args[0][0] == sub_json


@pytest.mark.asyncio
async def test_dispatch_telegram_failure_does_not_prevent_web_push():
    """If send_telegram returns False (API error), web push is still attempted and can succeed."""
    mock_tg = AsyncMock(return_value=False)   # telegram failed internally
    mock_push = AsyncMock(return_value=True)
    with patch("app.services.notifications.send_telegram", new=mock_tg), \
         patch("app.services.notifications.send_web_push", new=mock_push):
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=50.0,
            telegram_chat_id="chat_123",
            telegram_bot_token="bot_token",
            push_subscription_json='{"endpoint":"https://push.example.com"}',
            user_tier="basic",
        )
    # Both were attempted — telegram failed, push succeeded
    assert results.get("telegram") is False
    assert results.get("web_push") is True
    mock_push.assert_called_once()
