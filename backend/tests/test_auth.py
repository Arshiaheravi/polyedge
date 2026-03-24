"""Tests for /auth endpoints: register, login, /me."""


def test_register_success(client):
    resp = client.post("/auth/register", json={
        "email": "user@example.com",
        "password": "password123",
        "name": "Alice",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "user@example.com"
    assert data["user"]["subscription_tier"] == "free"


def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "pass", "name": "Bob"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@example.com", "password": "mypass", "name": "Carol"
    })
    resp = client.post("/auth/login", json={
        "email": "login@example.com", "password": "mypass"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_response_includes_user_fields(client):
    """POST /auth/login response includes a user dict with email, name, and subscription_tier."""
    client.post("/auth/register", json={
        "email": "fields@example.com", "password": "mypass", "name": "FieldUser"
    })
    resp = client.post("/auth/login", json={
        "email": "fields@example.com", "password": "mypass"
    })
    assert resp.status_code == 200
    data = resp.json()
    user = data["user"]
    assert user["email"] == "fields@example.com"
    assert user["name"] == "FieldUser"
    assert user["subscription_tier"] == "free"


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "email": "wrong@example.com", "password": "correct", "name": "Dan"
    })
    resp = client.post("/auth/login", json={
        "email": "wrong@example.com", "password": "incorrect"
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/login", json={
        "email": "nobody@example.com", "password": "pass"
    })
    assert resp.status_code == 401


def test_get_me_authenticated(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "test@example.com"


def test_get_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 403


def test_login_disabled_account(client, db):
    """Login with is_active=False returns 403 Account is disabled."""
    from app.models import User

    client.post("/auth/register", json={
        "email": "disabled@example.com", "password": "pass", "name": "Disabled"
    })
    user = db.query(User).filter(User.email == "disabled@example.com").first()
    user.is_active = False
    db.commit()

    resp = client.post("/auth/login", json={
        "email": "disabled@example.com", "password": "pass"
    })
    assert resp.status_code == 403
    assert "disabled" in resp.json()["detail"].lower()


def test_login_with_uppercase_email_succeeds(client):
    """Login email is lowercased before lookup — UPPER@EXAMPLE.COM matches user@example.com."""
    client.post("/auth/register", json={
        "email": "casetest@example.com", "password": "mypass", "name": "CaseUser"
    })
    resp = client.post("/auth/login", json={
        "email": "CASETEST@EXAMPLE.COM", "password": "mypass"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_register_uppercase_email_is_treated_as_duplicate(client):
    """Registering UPPER@EXAMPLE.COM after user@example.com already exists returns 400."""
    client.post("/auth/register", json={
        "email": "dupcase@example.com", "password": "pass", "name": "DupCase"
    })
    resp = client.post("/auth/register", json={
        "email": "DUPCASE@EXAMPLE.COM", "password": "pass2", "name": "DupCase2"
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


def test_get_me_returns_all_user_fields(client, auth_headers):
    """GET /auth/me response includes id, email, name, subscription_tier, telegram_verified, telegram_chat_id, created_at."""
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert "id" in user
    assert "email" in user
    assert "name" in user
    assert "subscription_tier" in user
    assert "telegram_verified" in user
    assert "telegram_chat_id" in user
    assert "created_at" in user


def test_register_whitespace_padded_email_strips_and_deduplicates(client):
    """Email with surrounding whitespace ' user@example.com ' is stored stripped.
    A second register with the same padded email must return 400 (not 500 from DB constraint)."""
    # First registration with padded email — stored as stripped "ws@example.com"
    resp1 = client.post("/auth/register", json={
        "email": " ws@example.com ", "password": "pass", "name": "WS"
    })
    assert resp1.status_code == 201
    assert resp1.json()["user"]["email"] == "ws@example.com"

    # Second registration with same padded email — duplicate check must catch it (400, not 500)
    resp2 = client.post("/auth/register", json={
        "email": " ws@example.com ", "password": "pass2", "name": "WS2"
    })
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["detail"].lower()


def test_login_with_stripped_email_after_whitespace_register(client):
    """After registering with padded email, login with the clean (unpadded) email works."""
    client.post("/auth/register", json={
        "email": " clean@example.com ", "password": "pass", "name": "Clean"
    })
    resp = client.post("/auth/login", json={
        "email": "clean@example.com", "password": "pass"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_with_whitespace_padded_email_works(client):
    """Login with a whitespace-padded email (e.g. ' user@example.com ') must succeed.
    Registration strips the email to 'user@example.com', and login must strip too."""
    client.post("/auth/register", json={
        "email": "padlogin@example.com", "password": "pass", "name": "PadLogin"
    })
    resp = client.post("/auth/login", json={
        "email": "  padlogin@example.com  ", "password": "pass"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_get_me_reflects_updated_subscription_tier(client, db, auth_headers, registered_user):
    """GET /auth/me returns the current subscription_tier after a Stripe webhook upgrades the user."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["user"]["subscription_tier"] == "basic"
