"""Tests for /follows endpoints and tier limits."""

BETTOR_A = "0xabc123"
BETTOR_B = "0xdef456"
BETTOR_C = "0xghi789"


def test_list_follows_empty(client, auth_headers):
    resp = client.get("/follows", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["follows"] == []
    assert resp.json()["tier"] == "free"
    assert resp.json()["limit"] == 1


def test_follow_bettor(client, auth_headers):
    resp = client.post("/follows", json={"bettor_address": BETTOR_A, "bettor_name": "Alpha"},
                       headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["bettor_address"] == BETTOR_A


def test_free_tier_follow_limit(client, auth_headers):
    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    # Second follow should fail for free tier
    resp = client.post("/follows", json={"bettor_address": BETTOR_B}, headers=auth_headers)
    assert resp.status_code == 403
    assert "1 follow" in resp.json()["detail"] or "Upgrade" in resp.json()["detail"]


def test_duplicate_follow_rejected(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"  # need headroom to reach the dup check
    db.commit()

    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    resp = client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    assert resp.status_code == 409


def test_unfollow(client, auth_headers):
    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    resp = client.delete(f"/follows/{BETTOR_A}", headers=auth_headers)
    assert resp.status_code == 204

    # Should be gone
    resp = client.get("/follows", headers=auth_headers)
    assert resp.json()["follows"] == []


def test_unfollow_nonexistent(client, auth_headers):
    resp = client.delete("/follows/0xnonexistent", headers=auth_headers)
    assert resp.status_code == 404


def test_basic_tier_allows_5_follows(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    # Upgrade to basic in DB
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    addresses = [f"0x{i:040x}" for i in range(5)]
    for addr in addresses:
        resp = client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)
        assert resp.status_code == 201

    # 6th should fail
    resp = client.post("/follows", json={"bettor_address": "0xextra"}, headers=auth_headers)
    assert resp.status_code == 403


def test_follows_require_auth(client):
    resp = client.get("/follows")
    assert resp.status_code == 403


def test_basic_tier_limit_error_message(client, db, auth_headers, registered_user):
    """When basic user hits the 5-follow cap, error message mentions VIP upgrade."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    for i in range(5):
        client.post("/follows", json={"bettor_address": f"0x{i:040x}"}, headers=auth_headers)

    resp = client.post("/follows", json={"bettor_address": "0xextra"}, headers=auth_headers)
    assert resp.status_code == 403
    assert "VIP" in resp.json()["detail"]


def test_follow_bettor_name_defaults_to_truncated_address(client, auth_headers):
    """When bettor_name is omitted, stored name defaults to address[:12]+'...'."""
    addr = "0xabcdefghij1234567890"
    resp = client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["bettor_name"] == addr[:12] + "..."


def test_follows_list_contains_bettor_fields(client, auth_headers):
    """GET /follows returns bettor_address and bettor_name for each follow."""
    client.post("/follows",
                json={"bettor_address": BETTOR_A, "bettor_name": "Alpha Trader"},
                headers=auth_headers)
    resp = client.get("/follows", headers=auth_headers)
    assert resp.status_code == 200
    follows = resp.json()["follows"]
    assert len(follows) == 1
    assert follows[0]["bettor_address"] == BETTOR_A
    assert follows[0]["bettor_name"] == "Alpha Trader"
    assert "created_at" in follows[0]


def test_list_follows_basic_tier_reports_tier_and_limit(client, db, auth_headers, registered_user):
    """GET /follows for a basic-tier user returns tier='basic' and limit=5."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    resp = client.get("/follows", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "basic"
    assert data["limit"] == 5


def test_delete_follows_requires_auth(client):
    """DELETE /follows/{address} without a token returns 403, not 500."""
    resp = client.delete("/follows/0xsomeaddress")
    assert resp.status_code == 403


def test_post_follows_requires_auth(client):
    """POST /follows without an auth token returns 403, not 201 or 500."""
    resp = client.post("/follows", json={"bettor_address": "0xtest"})
    assert resp.status_code == 403
