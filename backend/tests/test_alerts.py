"""Tests for /alerts endpoints: settings, telegram, SMS tier gates."""


def test_get_alert_settings(client, auth_headers):
    resp = client.get("/alerts/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["web_push_enabled"] is False
    assert data["telegram_enabled"] is False
    assert data["sms_enabled"] is False
    assert data["phone_verified"] is False


def test_enable_web_push(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.put("/alerts/settings", json={"web_push_enabled": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["web_push_enabled"] is True


def test_web_push_blocked_for_free_tier(client, auth_headers):
    """Free users must receive 403 when attempting to enable web push."""
    resp = client.put("/alerts/settings", json={"web_push_enabled": True}, headers=auth_headers)
    assert resp.status_code == 403
    assert "Basic or VIP" in resp.json()["detail"]


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


def test_web_push_enabled_independent_of_push_subscription(client, db, auth_headers, registered_user):
    """Setting web_push_enabled=True without providing push_subscription succeeds for paid tier.
    The two fields are independent — enabling the flag does not require a subscription object."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.put("/alerts/settings", json={"web_push_enabled": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["web_push_enabled"] is True


def test_telegram_start_called_twice_overwrites_code(client, db, auth_headers, registered_user):
    """Calling telegram/start twice returns a new code each time (no 409).
    The second code overwrites the first; the old code is then invalid for verification."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp1 = client.post("/alerts/telegram/start", headers=auth_headers)
    assert resp1.status_code == 200
    code1 = resp1.json()["code"]

    resp2 = client.post("/alerts/telegram/start", headers=auth_headers)
    assert resp2.status_code == 200
    code2 = resp2.json()["code"]

    # Second call must succeed (not 409) and return a code
    assert code2 is not None
    # Old code is now stale — trying to verify with it should fail
    resp_verify = client.post("/alerts/telegram/verify",
                              json={"code": code1}, headers=auth_headers)
    assert resp_verify.status_code == 400
    assert "Invalid" in resp_verify.json()["detail"]


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
    """GET /alerts/settings includes telegram_verified, phone_number, phone_verified.
    telegram_chat_id must NOT appear — it is internal infrastructure, never exposed to clients."""
    resp = client.get("/alerts/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "telegram_verified" in data
    assert "phone_number" in data
    assert "phone_verified" in data
    assert "telegram_chat_id" not in data  # sensitive — must never be in any API response


def test_sms_start_happy_path(client, db, auth_headers, registered_user):
    """VIP user with valid E.164 phone and Twilio configured → 200 with sent=True."""
    from unittest.mock import AsyncMock, patch
    _make_vip(db, registered_user)
    import app.routes.alerts as alerts_module
    original_sid = alerts_module.settings.twilio_account_sid
    original_tok = alerts_module.settings.twilio_auth_token
    alerts_module.settings.twilio_account_sid = "ACtest"
    alerts_module.settings.twilio_auth_token = "testtoken"
    try:
        with patch("app.routes.alerts.send_sms", new=AsyncMock(return_value=True)):
            resp = client.post("/alerts/sms/start", json={"phone_number": "+14155552671"},
                               headers=auth_headers)
    finally:
        alerts_module.settings.twilio_account_sid = original_sid
        alerts_module.settings.twilio_auth_token = original_tok
    assert resp.status_code == 200
    data = resp.json()
    assert data["sent"] is True
    assert "+14155552671" in data["message"]


def test_telegram_verify_requires_auth(client):
    """POST /alerts/telegram/verify without an auth token returns 403."""
    resp = client.post("/alerts/telegram/verify", json={"code": "ABCD1234"})
    assert resp.status_code == 403


def test_sms_verify_requires_auth(client):
    """POST /alerts/sms/verify without an auth token returns 403."""
    resp = client.post("/alerts/sms/verify", json={"code": "123456"})
    assert resp.status_code == 403


def test_sms_verify_response_includes_verified_and_message(client, db, auth_headers, registered_user):
    """POST /alerts/sms/verify success response must include BOTH verified=True AND message string."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    user.phone_number = "+14155552671"
    user.phone_verify_code = "654321"
    db.commit()

    resp = client.post("/alerts/sms/verify", json={"code": "654321"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["message"] == "Phone number verified successfully"


def test_telegram_verify_response_includes_verified_and_message(client, db, auth_headers, registered_user):
    """POST /alerts/telegram/verify success response must include BOTH verified=True AND message string."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verify_code = "DEADBEEF"
    db.commit()

    resp = client.post("/alerts/telegram/verify", json={"code": "DEADBEEF"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verified"] is True
    assert data["message"] == "Telegram linked successfully"


def test_disable_telegram_for_basic_user(client, db, auth_headers, registered_user):
    """Basic user can explicitly set telegram_enabled=False after enabling it."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    # Enable telegram first
    resp = client.put("/alerts/settings", json={"telegram_enabled": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["telegram_enabled"] is True

    # Now explicitly disable it
    resp = client.put("/alerts/settings", json={"telegram_enabled": False}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["telegram_enabled"] is False


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


# ── AlertSetting auto-create branches ────────────────────────────────────────


def test_get_alert_settings_autocreates_when_no_row_exists(client, db):
    """GET /alerts/settings auto-creates an AlertSetting row when the user
    was created directly in the DB (bypassing registration which normally creates one).
    Returns 200 with default values."""
    from app.auth import hash_password, create_access_token
    from app.models import User

    user = User(
        email="noalert_get@x.com",
        hashed_password=hash_password("pass"),
        name="NoAlert",
        subscription_tier="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/alerts/settings", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["web_push_enabled"] is False
    assert data["telegram_enabled"] is False
    assert data["sms_enabled"] is False


def test_put_alert_settings_autocreates_when_no_row_exists(client, db):
    """PUT /alerts/settings auto-creates an AlertSetting row when the user
    has no existing AlertSetting, then applies the update.
    Returns 200 with the updated value."""
    from app.auth import hash_password, create_access_token
    from app.models import User

    user = User(
        email="noalert_put@x.com",
        hashed_password=hash_password("pass"),
        name="NoAlertPut",
        subscription_tier="basic",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put("/alerts/settings", json={"web_push_enabled": True}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["web_push_enabled"] is True


def test_put_alert_settings_empty_body_returns_200_no_changes(client, auth_headers):
    """PUT /alerts/settings with an empty body {} (all Optional fields = None)
    executes none of the field-update branches and returns the current settings unchanged."""
    resp = client.put("/alerts/settings", json={}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    # Default values unchanged
    assert data["web_push_enabled"] is False
    assert data["telegram_enabled"] is False
    assert data["sms_enabled"] is False


def test_telegram_start_response_includes_instructions_and_bot_link(client, db, auth_headers, registered_user):
    """POST /alerts/telegram/start response must include code, instructions, and bot_link."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.post("/alerts/telegram/start", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert "instructions" in data
    assert "bot_link" in data


def test_telegram_verify_lowercase_code_is_accepted(client, db, auth_headers, registered_user):
    """POST /alerts/telegram/verify accepts lowercase code — route normalises with .upper()."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verify_code = "ABCD1234"
    db.commit()

    resp = client.post(
        "/alerts/telegram/verify",
        json={"code": "abcd1234"},  # lowercase submission
        headers=auth_headers,
    )

    assert resp.status_code == 200
    assert resp.json()["verified"] is True


def test_put_alert_settings_response_includes_telegram_and_phone_verified(client, db, auth_headers, registered_user):
    """PUT /alerts/settings response body must include telegram_verified and phone_verified fields."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.put("/alerts/settings", json={"web_push_enabled": True}, headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "telegram_verified" in data
    assert "phone_verified" in data


def test_put_alerts_settings_invalid_push_subscription_returns_422(client, auth_headers):
    """PUT /alerts/settings with push_subscription set to an invalid JSON string must return 422.
    The route validates push_subscription via json.loads() and raises HTTPException(422) on failure.
    This guards against browsers sending malformed push subscription objects that would later
    crash GET /alerts/settings when it tries to json.loads() the stored value."""
    resp = client.put(
        "/alerts/settings",
        json={"push_subscription": "not_valid_json"},
        headers=auth_headers,
    )

    assert resp.status_code == 422


def test_put_alerts_settings_valid_push_subscription_stores_and_get_retrieves(client, auth_headers):
    """PUT /alerts/settings with a valid JSON push_subscription string must store it,
    and GET /alerts/settings must return it as a parsed dict with the 'endpoint' key.
    Guards against the json.loads() validation/store path breaking silently."""
    sub_json = '{"endpoint": "https://push.example.com/sub/xyz", "keys": {"auth": "aaa", "p256dh": "bbb"}}'

    put_resp = client.put(
        "/alerts/settings",
        json={"push_subscription": sub_json},
        headers=auth_headers,
    )
    assert put_resp.status_code == 200

    get_resp = client.get("/alerts/settings", headers=auth_headers)
    assert get_resp.status_code == 200
    result = get_resp.json()["push_subscription"]
    assert isinstance(result, dict)
    assert result["endpoint"] == "https://push.example.com/sub/xyz"


# ── Telegram bot webhook ──────────────────────────────────────────────────────


def test_telegram_webhook_valid_verify_sets_chat_id(client, db, registered_user):
    """Telegram webhook with a valid /verify CODE sets telegram_chat_id and telegram_verified=True in DB."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    user.telegram_verify_code = "AABBCCDD"
    db.commit()

    update = {
        "update_id": 1001,
        "message": {
            "message_id": 1,
            "chat": {"id": 987654321, "type": "private"},
            "text": "/verify AABBCCDD",
        },
    }
    resp = client.post("/alerts/telegram/webhook", json=update)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    db.refresh(user)
    assert user.telegram_chat_id == "987654321"
    assert user.telegram_verified is True
    assert user.telegram_verify_code is None


def test_telegram_webhook_lowercase_code_is_accepted(client, db, registered_user):
    """Webhook accepts /verify with lowercase code — handler normalises with .upper()."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.telegram_verify_code = "DEADBEEF"
    db.commit()

    update = {
        "update_id": 1002,
        "message": {
            "message_id": 2,
            "chat": {"id": 111222333, "type": "private"},
            "text": "/verify deadbeef",
        },
    }
    resp = client.post("/alerts/telegram/webhook", json=update)
    assert resp.status_code == 200
    db.refresh(user)
    assert user.telegram_chat_id == "111222333"


def test_telegram_webhook_unknown_code_returns_ok_no_db_change(client, db, registered_user):
    """Webhook with an unrecognised verify code returns 200 ok=True but changes nothing."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.telegram_verify_code = "REALCODE"
    user.telegram_chat_id = None
    db.commit()

    update = {
        "update_id": 1003,
        "message": {
            "message_id": 3,
            "chat": {"id": 999, "type": "private"},
            "text": "/verify WRONGCOD",
        },
    }
    resp = client.post("/alerts/telegram/webhook", json=update)
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    db.refresh(user)
    assert user.telegram_chat_id is None  # unchanged
    assert user.telegram_verify_code == "REALCODE"  # unchanged


def test_telegram_webhook_no_message_returns_ok(client):
    """Webhook update with no 'message' key (e.g. channel post) returns 200 ok=True."""
    resp = client.post("/alerts/telegram/webhook", json={"update_id": 1004, "channel_post": {}})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_telegram_webhook_non_verify_text_returns_ok_no_change(client, db, registered_user):
    """Webhook with non-/verify text (e.g. /start) returns 200 and makes no DB changes."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.telegram_verify_code = "STARTTEST"
    user.telegram_chat_id = None
    db.commit()

    update = {
        "update_id": 1005,
        "message": {
            "message_id": 5,
            "chat": {"id": 555, "type": "private"},
            "text": "/start",
        },
    }
    resp = client.post("/alerts/telegram/webhook", json=update)
    assert resp.status_code == 200
    db.refresh(user)
    assert user.telegram_chat_id is None  # unchanged
