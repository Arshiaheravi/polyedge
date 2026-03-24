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


def test_alerts_require_auth(client):
    resp = client.get("/alerts/settings")
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
