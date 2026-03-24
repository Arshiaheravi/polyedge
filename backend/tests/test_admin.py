"""Tests for /admin endpoints."""


ADMIN_PW = "testadmin"


def _admin_headers(password=ADMIN_PW):
    return {"x-admin-password": password}


def test_admin_stats_no_header(client):
    resp = client.get("/admin/stats")
    assert resp.status_code == 422  # missing required header


def test_admin_stats_wrong_password(client):
    resp = client.get("/admin/stats", headers={"x-admin-password": "wrongpassword"})
    assert resp.status_code == 403
    assert "Invalid admin password" in resp.json()["detail"]


def test_admin_stats_correct_password(client, monkeypatch):
    """Admin stats returns correct shape with real admin password."""
    from app.config import get_settings
    settings = get_settings()
    pw = settings.admin_password  # use whatever is configured

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "follows" in data
    assert "bet_events" in data
    assert "mrr_estimate" in data
    assert isinstance(data["users"]["total"], int)


def test_admin_stats_counts_users(client, monkeypatch):
    """Register two users and verify stats reflects them."""
    from app.config import get_settings
    pw = get_settings().admin_password

    client.post("/auth/register", json={"email": "a@x.com", "password": "p", "name": "A"})
    client.post("/auth/register", json={"email": "b@x.com", "password": "p", "name": "B"})

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    assert resp.json()["users"]["total"] == 2
    assert resp.json()["users"]["free"] == 2


def test_admin_stats_mrr_calculation(client, db):
    """MRR = basic * 4.99 + vip * 9.99."""
    from app.config import get_settings
    from app.models import User
    from app.auth import hash_password

    pw = get_settings().admin_password

    # Create 1 basic and 1 vip user directly in DB
    db.add(User(email="basic@x.com", hashed_password=hash_password("p"), name="B",
                subscription_tier="basic"))
    db.add(User(email="vip@x.com", hashed_password=hash_password("p"), name="V",
                subscription_tier="vip"))
    db.commit()

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    expected_mrr = 1 * 4.99 + 1 * 9.99
    assert abs(resp.json()["mrr_estimate"] - expected_mrr) < 0.01
