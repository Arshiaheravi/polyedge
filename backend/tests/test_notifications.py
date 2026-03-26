"""Unit tests for notification service functions."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import app.services.notifications as notif_mod
from app.services.notifications import (
    format_bet_message,
    format_sms_message,
    dispatch_bet_notification,
    send_telegram,
    send_sms,
    send_web_push,
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


@pytest.mark.asyncio
async def test_send_telegram_returns_false_when_bot_token_empty():
    """send_telegram returns False immediately when bot_token is empty — no HTTP call made."""
    result = await send_telegram(chat_id="12345", message="hello", bot_token="")
    assert result is False


@pytest.mark.asyncio
async def test_send_telegram_returns_false_when_chat_id_empty():
    """send_telegram returns False immediately when chat_id is empty — no HTTP call made."""
    result = await send_telegram(chat_id="", message="hello", bot_token="bottoken123")
    assert result is False


# ── send_web_push direct unit tests ──────────────────────────────────────────


def _make_mock_http_client(status_code: int):
    """Helper: returns a mock AsyncClient whose .post() returns a response with the given status."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(return_value=mock_resp)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    return mock_instance


@pytest.mark.asyncio
async def test_send_web_push_happy_path_json_string_201():
    """send_web_push returns True when endpoint is present and HTTP returns 201."""
    sub_json = '{"endpoint": "https://push.example.com/abc", "keys": {"p256dh": "x", "auth": "y"}}'
    mock_client = _make_mock_http_client(201)
    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_client):
        result = await send_web_push(sub_json, {"title": "test", "body": "hello"})
    assert result is True


@pytest.mark.asyncio
async def test_send_web_push_happy_path_dict_200():
    """send_web_push accepts a dict (not a string) and returns True when HTTP returns 200."""
    sub_dict = {"endpoint": "https://push.example.com/def"}
    mock_client = _make_mock_http_client(200)
    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_client):
        result = await send_web_push(sub_dict, {"title": "test"})
    assert result is True


@pytest.mark.asyncio
async def test_send_web_push_no_endpoint_returns_false():
    """send_web_push returns False immediately when endpoint key is missing — no HTTP call."""
    sub_json = '{"keys": {"p256dh": "x", "auth": "y"}}'  # no "endpoint"
    mock_client = _make_mock_http_client(201)
    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_client):
        result = await send_web_push(sub_json, {"title": "test"})
    assert result is False
    mock_client.post.assert_not_called()


@pytest.mark.asyncio
async def test_send_web_push_http_410_returns_false():
    """send_web_push returns False when the push endpoint returns a non-200/201 status (e.g. 410 Gone)."""
    sub_json = '{"endpoint": "https://push.example.com/expired"}'
    mock_client = _make_mock_http_client(410)
    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_client):
        result = await send_web_push(sub_json, {"title": "test"})
    assert result is False


@pytest.mark.asyncio
async def test_send_web_push_http_exception_returns_false():
    """send_web_push returns False and does not raise when an httpx error occurs."""
    sub_json = '{"endpoint": "https://push.example.com/broken"}'
    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(side_effect=Exception("Connection refused"))
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_instance):
        result = await send_web_push(sub_json, {"title": "test"})
    assert result is False


@pytest.mark.asyncio
async def test_send_telegram_returns_true_when_http_succeeds():
    """send_telegram returns True when bot_token and chat_id are set and HTTP call succeeds."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()  # does not raise
    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(return_value=mock_resp)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)

    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_instance):
        result = await send_telegram(chat_id="999", message="hello", bot_token="bot_abc")

    assert result is True


# ── send_sms unit tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_sms_returns_false_when_credentials_missing():
    """send_sms returns False immediately when any credential is empty."""
    result = await send_sms(
        to_number="+14155552671",
        message="test",
        account_sid="",  # missing
        auth_token="token",
        from_number="+15005550006",
    )
    assert result is False


@pytest.mark.asyncio
async def test_send_sms_returns_true_on_http_success():
    """send_sms returns True when Twilio HTTP call succeeds (raise_for_status does not raise)."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()  # does not raise
    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(return_value=mock_resp)
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)

    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_instance):
        result = await send_sms(
            to_number="+14155552671",
            message="test",
            account_sid="ACtest",
            auth_token="authtoken",
            from_number="+15005550006",
        )

    assert result is True


@pytest.mark.asyncio
async def test_send_sms_returns_false_on_http_exception():
    """send_sms returns False and does not raise when an httpx error occurs."""
    mock_instance = AsyncMock()
    mock_instance.post = AsyncMock(side_effect=Exception("Connection refused"))
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)

    with patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_instance):
        result = await send_sms(
            to_number="+14155552671",
            message="test",
            account_sid="ACtest",
            auth_token="authtoken",
            from_number="+15005550006",
        )

    assert result is False


@pytest.mark.asyncio
async def test_dispatch_vip_sms_enabled_but_no_phone_number_skips_sms():
    """dispatch_bet_notification does not call send_sms when phone_number is None,
    even if sms_enabled=True and user_tier='vip'."""
    with patch("app.services.notifications.send_sms", new=AsyncMock(return_value=True)) as mock_sms:
        results = await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test market",
            outcome="Yes",
            amount=100.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json=None,
            phone_number=None,  # no phone despite sms_enabled=True
            sms_enabled=True,
            user_tier="vip",
        )
    assert "sms" not in results
    mock_sms.assert_not_called()


# ── Conviction Score tests ────────────────────────────────────────────────────


def test_format_bet_message_extreme_conviction():
    """EXTREME conviction label (>=10x) shows 🔥 in Telegram message."""
    msg = format_bet_message("Alice", "Will BTC hit 100k?", "Yes", 5000.0, conviction_score=12.5, conviction_label="EXTREME")
    assert "🔥" in msg
    assert "EXTREME" in msg
    assert "12.5x" in msg


def test_format_bet_message_high_conviction():
    """HIGH conviction label (>=3x) shows ⚡ in Telegram message."""
    msg = format_bet_message("Bob", "Will Trump win?", "No", 1500.0, conviction_score=4.2, conviction_label="HIGH")
    assert "⚡" in msg
    assert "HIGH" in msg
    assert "4.2x" in msg


def test_format_bet_message_no_conviction_label():
    """No conviction label → no conviction line in message, core fields still present."""
    msg = format_bet_message("Carol", "Will Fed cut rates?", "Yes", 200.0, conviction_score=1.5, conviction_label="")
    assert "🔥" not in msg
    assert "⚡" not in msg
    assert "Carol" in msg
    assert "$200.00" in msg


def test_format_bet_message_default_params():
    """format_bet_message works with default conviction params (backwards compatible)."""
    msg = format_bet_message("Dave", "Test market", "Yes", 100.0)
    assert "Dave" in msg
    assert "$100.00" in msg


@pytest.mark.asyncio
async def test_dispatch_extreme_conviction_push_title():
    """EXTREME conviction sets 🔥 title in web push payload."""
    mock_push = AsyncMock(return_value=True)
    with patch("app.services.notifications.send_web_push", new=mock_push):
        await dispatch_bet_notification(
            bettor_name="Alice",
            market="Test",
            outcome="Yes",
            amount=10000.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json='{"endpoint":"https://push.example.com"}',
            user_tier="basic",
            conviction_score=15.0,
            conviction_label="EXTREME",
        )
    mock_push.assert_called_once()
    push_payload = mock_push.call_args[0][1]
    assert "🔥" in push_payload["title"]
    assert "EXTREME" in push_payload["title"]


@pytest.mark.asyncio
async def test_dispatch_high_conviction_push_title():
    """HIGH conviction sets ⚡ title in web push payload."""
    mock_push = AsyncMock(return_value=True)
    with patch("app.services.notifications.send_web_push", new=mock_push):
        await dispatch_bet_notification(
            bettor_name="Bob",
            market="Test",
            outcome="No",
            amount=3000.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json='{"endpoint":"https://push.example.com"}',
            user_tier="basic",
            conviction_score=5.0,
            conviction_label="HIGH",
        )
    mock_push.assert_called_once()
    push_payload = mock_push.call_args[0][1]
    assert "⚡" in push_payload["title"]
    assert "HIGH" in push_payload["title"]


@pytest.mark.asyncio
async def test_dispatch_no_conviction_push_title():
    """No conviction label → generic push title."""
    mock_push = AsyncMock(return_value=True)
    with patch("app.services.notifications.send_web_push", new=mock_push):
        await dispatch_bet_notification(
            bettor_name="Carol",
            market="Test",
            outcome="Yes",
            amount=100.0,
            telegram_chat_id=None,
            telegram_bot_token="",
            push_subscription_json='{"endpoint":"https://push.example.com"}',
            user_tier="basic",
            conviction_score=1.5,
            conviction_label="",
        )
    mock_push.assert_called_once()
    push_payload = mock_push.call_args[0][1]
    assert "Carol" in push_payload["title"]
    assert "🔥" not in push_payload["title"]
    assert "⚡" not in push_payload["title"]
