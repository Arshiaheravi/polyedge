"""Tests for /alerts endpoints: settings, telegram, SMS tier gates."""


def test_get_alert_settings(client, auth_headers):
    resp = client.get("/alerts/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["web_push_enabled"] is False
    assert data["telegram_enabled"] is False
    assert data["sms_enabled"] is False
    assert data["phone_verified"] is False


def test_enable_web_push(client, auth_headers):
    resp = client.put("/alerts/settings", json={"web_push_enabled": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["web_push_enabled"] is True


def test_disable_web_push_returns_false(client, auth_headers):
    """Disabling web_push after it was enabled returns web_push_enabled=False."""
    client.put("/alerts/settings", json={"web_push_enabled": True}, headers=auth_headers)
    resp = client.put("/alerts/settings", json={"web_push_enabled": False}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["web_push_enabled"] is False


def test_telegram_requires_paid_tier(client, auth_headers):
    resp = client.put("/alerts/settings", json={"telegram_enabled": True}, headers=auth_headers)
    assert resp.status_code == 403
    assert "Basic or VIP" in resp.json()["detail"]


def test_telegram_enabled_for_basic(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.put("/alerts/settings", json={"telegram_enabled": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["telegram_enabled"] is True


def test_sms_requires_vip(client, auth_headers):
    resp = client.put("/alerts/settings", json={"sms_enabled": True}, headers=auth_headers)
    assert resp.status_code == 403
    assert "VIP" in resp.json()["detail"]


def test_sms_requires_vip_even_for_basic(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.put("/alerts/settings", json={"sms_enabled": True}, headers=auth_headers)
    assert resp.status_code == 403


def test_sms_enable_requires_verified_phone(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()

    # VIP but phone not verified yet
    resp = client.put("/alerts/settings", json={"sms_enabled": True}, headers=auth_headers)
    assert resp.status_code == 400
    assert "Verify your phone" in resp.json()["detail"]


def test_sms_enable_after_phone_verified(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    user.phone_verified = True
    user.phone_number = "+14155552671"
    db.commit()

    resp = client.put("/alerts/settings", json={"sms_enabled": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["sms_enabled"] is True


def test_sms_start_requires_vip(client, auth_headers):
    resp = client.post("/alerts/sms/start", json={"phone_number": "+14155552671"},
                       headers=auth_headers)
    assert resp.status_code == 403


def test_sms_verify_no_pending(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()

    resp = client.post("/alerts/sms/verify", json={"code": "123456"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "No pending verification" in resp.json()["detail"]


def test_sms_verify_wrong_code(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    user.phone_number = "+14155552671"
    user.phone_verify_code = "999999"
    db.commit()

    resp = client.post("/alerts/sms/verify", json={"code": "000000"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "Invalid" in resp.json()["detail"]


def test_sms_verify_correct_code(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    user.phone_number = "+14155552671"
    user.phone_verify_code = "123456"
    db.commit()

    resp = client.post("/alerts/sms/verify", json={"code": "123456"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["verified"] is True

    # Check phone is now verified in DB
    db.refresh(user)
    assert user.phone_verified is True
    assert user.phone_verify_code is None


def test_telegram_start_requires_paid(client, auth_headers):
    resp = client.post("/alerts/telegram/start", headers=auth_headers)
    assert resp.status_code == 403


def test_telegram_start_for_basic(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.post("/alerts/telegram/start", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert len(data["code"]) == 8  # 8-char hex


def test_telegram_start_for_vip(client, db, auth_headers, registered_user):
    """VIP tier can also call /alerts/telegram/start and receives a code."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()

    resp = client.post("/alerts/telegram/start", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert len(data["code"]) == 8


def test_alerts_require_auth(client):
    resp = client.get("/alerts/settings")
    assert resp.status_code == 403


def test_put_alert_settings_requires_auth(client):
    """PUT /alerts/settings without an auth token returns 403, not 200 or 500."""
    resp = client.put("/alerts/settings", json={"web_push_enabled": True})
    assert resp.status_code == 403


# ── Telegram /verify flow ────────────────────────────────────────────────────


def test_telegram_verify_no_pending_code_returns_400(client, db, auth_headers, registered_user):
    """Calling /verify without a pending code returns 400."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verify_code = None
    db.commit()

    resp = client.post("/alerts/telegram/verify", json={"code": "ABCD1234"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "No pending verification" in resp.json()["detail"]


def test_telegram_verify_wrong_code_returns_400(client, db, auth_headers, registered_user):
    """Submitting the wrong verification code returns 400."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verify_code = "ABCDEF12"
    db.commit()

    resp = client.post("/alerts/telegram/verify", json={"code": "WRONGCOD"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "Invalid" in resp.json()["detail"]


def test_telegram_verify_correct_code_links_account(client, db, auth_headers, registered_user):
    """Correct code sets telegram_verified=True and clears the code."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verify_code = "ABCDEF12"
    db.commit()

    resp = client.post("/alerts/telegram/verify", json={"code": "ABCDEF12"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["verified"] is True

    db.refresh(user)
    assert user.telegram_verified is True
    assert user.telegram_verify_code is None


def test_telegram_start_then_verify_full_round_trip(client, db, auth_headers, registered_user):
    """Full round-trip: start → get code → verify → account linked."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    # Step 1: start — get the code
    start_resp = client.post("/alerts/telegram/start", headers=auth_headers)
    assert start_resp.status_code == 200
    code = start_resp.json()["code"]
    assert len(code) == 8

    # Step 2: verify with the returned code
    verify_resp = client.post("/alerts/telegram/verify", json={"code": code}, headers=auth_headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True


def test_telegram_already_verified_can_start_again(client, db, auth_headers, registered_user):
    """A user already verified can call /start again — generates a new code (200)."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verified = True
    user.telegram_chat_id = "existing_chat_id"
    db.commit()

    resp = client.post("/alerts/telegram/start", headers=auth_headers)
    assert resp.status_code == 200
    assert "code" in resp.json()


# ── GET /alerts/settings with stored push_subscription ──────────────────────


def test_get_alert_settings_returns_parsed_push_subscription(client, db, auth_headers, registered_user):
    """GET /alerts/settings returns push_subscription as a parsed dict, not a raw string."""
    from app.models import AlertSetting, User
    import json as _json
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    sub_dict = {"endpoint": "https://push.example.com/sub/abc", "keys": {"p256dh": "AAAA", "auth": "BBBB"}}
    alert = db.query(AlertSetting).filter(AlertSetting.user_id == user.id).first()
    if not alert:
        alert = AlertSetting(user_id=user.id)
        db.add(alert)
    alert.push_subscription = _json.dumps(sub_dict)
    db.commit()

    resp = client.get("/alerts/settings", headers=auth_headers)
    assert resp.status_code == 200
    result = resp.json()["push_subscription"]
    assert isinstance(result, dict)
    assert result["endpoint"] == "https://push.example.com/sub/abc"


# ── SMS /sms/start edge cases ────────────────────────────────────────────────


def _make_vip(db, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()


def test_sms_start_twilio_not_configured_returns_503(client, db, auth_headers, registered_user):
    """If Twilio credentials are not set, /sms/start returns 503."""
    _make_vip(db, registered_user)
    import app.routes.alerts as alerts_module
    original_sid = alerts_module.settings.twilio_account_sid
    original_tok = alerts_module.settings.twilio_auth_token
    alerts_module.settings.twilio_account_sid = ""
    alerts_module.settings.twilio_auth_token = ""
    try:
        resp = client.post("/alerts/sms/start", json={"phone_number": "+14155552671"},
                           headers=auth_headers)
    finally:
        alerts_module.settings.twilio_account_sid = original_sid
        alerts_module.settings.twilio_auth_token = original_tok
    assert resp.status_code == 503
    assert "SMS service not configured" in resp.json()["detail"]


def test_sms_start_invalid_phone_format_returns_400(client, db, auth_headers, registered_user):
    """Phone number without leading '+' returns 400."""
    _make_vip(db, registered_user)
    import app.routes.alerts as alerts_module
    original_sid = alerts_module.settings.twilio_account_sid
    original_tok = alerts_module.settings.twilio_auth_token
    alerts_module.settings.twilio_account_sid = "ACtest"
    alerts_module.settings.twilio_auth_token = "testtoken"
    try:
        resp = client.post("/alerts/sms/start", json={"phone_number": "14155552671"},
                           headers=auth_headers)
    finally:
        alerts_module.settings.twilio_account_sid = original_sid
        alerts_module.settings.twilio_auth_token = original_tok
    assert resp.status_code == 400
    assert "E.164" in resp.json()["detail"]


def test_get_alert_settings_includes_phone_and_telegram_fields(client, auth_headers):
    """GET /alerts/settings response includes telegram_chat_id, phone_number, and phone_verified fields."""
    resp = client.get("/alerts/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "telegram_chat_id" in data
    assert "phone_number" in data
    assert "phone_verified" in data


def test_sms_start_send_fails_returns_502(client, db, auth_headers, registered_user):
    """If send_sms returns False (Twilio rejects), /sms/start returns 502."""
    from unittest.mock import AsyncMock, patch
    _make_vip(db, registered_user)
    import app.routes.alerts as alerts_module
    original_sid = alerts_module.settings.twilio_account_sid
    original_tok = alerts_module.settings.twilio_auth_token
    alerts_module.settings.twilio_account_sid = "ACtest"
    alerts_module.settings.twilio_auth_token = "testtoken"
    try:
        with patch("app.routes.alerts.send_sms", new=AsyncMock(return_value=False)):
            resp = client.post("/alerts/sms/start", json={"phone_number": "+14155552671"},
                               headers=auth_headers)
    finally:
        alerts_module.settings.twilio_account_sid = original_sid
        alerts_module.settings.twilio_auth_token = original_tok
    assert resp.status_code == 502
    assert "Failed to send SMS" in resp.json()["detail"]
