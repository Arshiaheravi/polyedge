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


def test_admin_stats_basic_and_vip_user_counts(client, db):
    """admin/stats reports correct users.basic and users.vip counts."""
    from app.config import get_settings
    from app.models import User
    from app.auth import hash_password

    pw = get_settings().admin_password
    db.add(User(email="ba2@x.com", hashed_password=hash_password("p"), name="Ba", subscription_tier="basic"))
    db.add(User(email="vi2@x.com", hashed_password=hash_password("p"), name="Vi", subscription_tier="vip"))
    db.commit()

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    assert data["users"]["basic"] == 1
    assert data["users"]["vip"] == 1


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


def test_admin_stats_follows_total_reflects_actual_follows(client, db):
    """admin/stats follows.total reflects the actual number of BettorFollow rows."""
    from app.config import get_settings
    from app.models import BettorFollow, User
    from app.auth import hash_password

    pw = get_settings().admin_password
    user = User(email="adminfollow@x.com", hashed_password=hash_password("p"), name="AF")
    db.add(user)
    db.flush()
    db.add(BettorFollow(user_id=user.id, bettor_address="0xfollow1", bettor_name="w1"))
    db.add(BettorFollow(user_id=user.id, bettor_address="0xfollow2", bettor_name="w2"))
    db.commit()

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    assert resp.json()["follows"]["total"] == 2


def test_admin_stats_bet_events_count(client, db):
    """admin/stats bet_events.total and bet_events.notified reflect actual BetEvent rows."""
    from app.config import get_settings
    from app.models import BetEvent

    pw = get_settings().admin_password

    import datetime
    now = datetime.datetime.utcnow()
    db.add(BetEvent(bettor_address="0xaaa", market_question="Q1", outcome="Yes",
                    amount_usd=10.0, timestamp=now, notified=True))
    db.add(BetEvent(bettor_address="0xbbb", market_question="Q2", outcome="No",
                    amount_usd=20.0, timestamp=now, notified=True))
    db.add(BetEvent(bettor_address="0xccc", market_question="Q3", outcome="Yes",
                    amount_usd=30.0, timestamp=now, notified=False))
    db.commit()

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    assert data["bet_events"]["total"] == 3
    assert data["bet_events"]["notified"] == 2


def test_admin_stats_zero_users_all_counts_zero(client):
    """GET /admin/stats with empty DB returns 0 for every count and MRR=0.0.
    Guards against None returns or crashes when the DB has no rows."""
    from app.config import get_settings
    pw = get_settings().admin_password

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    assert data["users"]["total"] == 0
    assert data["users"]["free"] == 0
    assert data["users"]["basic"] == 0
    assert data["users"]["vip"] == 0
    assert data["follows"]["total"] == 0
    assert data["bet_events"]["total"] == 0
    assert data["mrr_estimate"] == 0.0


def test_admin_stats_full_nested_shape_contract(client):
    """GET /admin/stats response must have the exact nested shape with correct types.
    Contract: users.{total,free,basic,vip} are ints; follows.total is int;
    bet_events.{total,notified} are ints; mrr_estimate is a float/int (numeric)."""
    from app.config import get_settings
    pw = get_settings().admin_password

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()

    # users nested shape
    assert isinstance(data["users"]["total"], int)
    assert isinstance(data["users"]["free"], int)
    assert isinstance(data["users"]["basic"], int)
    assert isinstance(data["users"]["vip"], int)

    # follows nested shape
    assert isinstance(data["follows"]["total"], int)

    # bet_events nested shape
    assert isinstance(data["bet_events"]["total"], int)
    assert isinstance(data["bet_events"]["notified"], int)

    # mrr_estimate is numeric
    assert isinstance(data["mrr_estimate"], (int, float))


def test_admin_stats_mrr_multi_user_decimal_precision(client, db):
    """MRR with 3 basic + 2 VIP uses float arithmetic (not integer rounding).
    3*4.99 + 2*9.99 = 14.97 + 19.98 = 34.95 — must not be rounded to an integer."""
    from app.config import get_settings
    from app.models import User
    from app.auth import hash_password

    pw = get_settings().admin_password

    for i in range(3):
        db.add(User(email=f"basic_multi{i}@x.com", hashed_password=hash_password("p"),
                    name=f"B{i}", subscription_tier="basic"))
    for i in range(2):
        db.add(User(email=f"vip_multi{i}@x.com", hashed_password=hash_password("p"),
                    name=f"V{i}", subscription_tier="vip"))
    db.commit()

    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    mrr = resp.json()["mrr_estimate"]
    expected = 3 * 4.99 + 2 * 9.99  # 34.95
    assert abs(mrr - expected) < 0.001, f"MRR {mrr} != expected {expected} (integer rounding?)"
    # Confirm it's NOT rounded to an integer (34.95 != 35)
    assert mrr != round(mrr), f"MRR appears to be integer-rounded: {mrr}"
