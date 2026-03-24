"""
Edge-case tests covering the remaining coverage gaps:
  1. Follow limit error message wording (Free + Basic tier 403s contain "Upgrade")
  2. SQL injection on /auth/login email field → 401 not 500
  3. Admin /stats with zero users → all counts 0, mrr_estimate 0.0
  4. PUT /alerts/settings with invalid JSON in push_subscription → 422
"""
import pytest
from app.models import User
from app.auth import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _admin_headers():
    from app.config import get_settings
    return {"x-admin-password": get_settings().admin_password}


# ---------------------------------------------------------------------------
# Follow Limit — Error Message Wording
# ---------------------------------------------------------------------------

class TestFollowLimitErrorMessages:
    """Confirm 403 responses contain the word 'Upgrade' so users know what to do."""

    def test_free_tier_second_follow_returns_403_with_upgrade(self, client, auth_headers):
        """Free tier: add one follow (success), then a second → 403 + 'Upgrade' in message."""
        client.post("/follows", json={"bettor_address": "0xfree001"}, headers=auth_headers)
        resp = client.post("/follows", json={"bettor_address": "0xfree002"}, headers=auth_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.json()}"
        detail = resp.json().get("detail", "")
        assert "Upgrade" in detail, f"'Upgrade' not found in detail: {detail!r}"

    def test_basic_tier_sixth_follow_returns_403_with_upgrade(self, client, db, auth_headers, registered_user):
        """Basic tier: add 5 follows (success), then a 6th → 403 + 'Upgrade' in message."""
        _, user_data = registered_user
        # Upgrade user to basic
        user = db.query(User).filter(User.id == user_data["id"]).first()
        user.subscription_tier = "basic"
        db.commit()

        for i in range(5):
            resp = client.post(
                "/follows",
                json={"bettor_address": f"0xbasic{i:036x}"},
                headers=auth_headers,
            )
            assert resp.status_code == 201, f"Basic follow #{i+1} failed: {resp.json()}"

        resp = client.post("/follows", json={"bettor_address": "0xbasicoverlimit"}, headers=auth_headers)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.json()}"
        detail = resp.json().get("detail", "")
        assert "Upgrade" in detail, f"'Upgrade' not found in detail: {detail!r}"


# ---------------------------------------------------------------------------
# Security — SQL Injection on Login
# ---------------------------------------------------------------------------

class TestSQLInjectionLogin:
    """SQL injection payloads in email/password fields must return 401 (not 500 or 200)."""

    def test_sql_injection_in_email_returns_401(self, client):
        """Classic UNION/OR injection in email field — SQLAlchemy ORM prevents bypass."""
        resp = client.post("/auth/login", json={
            "email": "' OR '1'='1",
            "password": "anything",
        })
        assert resp.status_code == 401, f"Expected 401 for SQL injection, got {resp.status_code}: {resp.json()}"

    def test_sql_injection_comment_in_email_returns_401(self, client):
        """-- comment injection should not crash and returns 401."""
        resp = client.post("/auth/login", json={
            "email": "admin'--",
            "password": "ignored",
        })
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"


# ---------------------------------------------------------------------------
# Admin Stats — Zero Users (Empty DB)
# ---------------------------------------------------------------------------

class TestAdminStatsEmptyDB:
    """admin/stats on a fresh DB must return all zeros and zero MRR."""

    def test_stats_with_no_users_returns_all_zeros(self, client):
        resp = client.get("/admin/stats", headers=_admin_headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.json()}"
        data = resp.json()
        assert data["users"]["total"] == 0
        assert data["users"]["free"] == 0
        assert data["users"]["basic"] == 0
        assert data["users"]["vip"] == 0
        assert data["follows"]["total"] == 0
        assert data["bet_events"]["total"] == 0
        assert data["bet_events"]["notified"] == 0

    def test_stats_mrr_is_zero_with_no_users(self, client):
        resp = client.get("/admin/stats", headers=_admin_headers())
        assert resp.status_code == 200
        assert resp.json()["mrr_estimate"] == 0.0


# ---------------------------------------------------------------------------
# Alerts Settings — Invalid push_subscription JSON
# ---------------------------------------------------------------------------

class TestAlertsInvalidPushSubscription:
    """PUT /alerts/settings must reject an invalid JSON string in push_subscription with 422."""

    def test_invalid_json_push_subscription_returns_422(self, client, auth_headers):
        resp = client.put(
            "/alerts/settings",
            json={"push_subscription": "not valid json {{{{"},
            headers=auth_headers,
        )
        assert resp.status_code == 422, (
            f"Expected 422 for invalid JSON push_subscription, got {resp.status_code}: {resp.json()}"
        )

    def test_valid_json_push_subscription_is_accepted(self, client, auth_headers):
        """Sanity-check: a real JSON string must still be accepted (200)."""
        valid_sub = '{"endpoint":"https://push.example.com/sub/abc","keys":{"p256dh":"AAAA","auth":"BBBB"}}'
        resp = client.put(
            "/alerts/settings",
            json={"push_subscription": valid_sub},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Valid push_subscription rejected: {resp.status_code}: {resp.json()}"
