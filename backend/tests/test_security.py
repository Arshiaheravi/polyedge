"""
Security and business-rule edge-case tests.
Covers: JWT tampering, expiry, missing sub; VIP unlimited follows;
register input validation; unfollow-then-re-follow; bettor unknown address.
"""
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_expired_token():
    """Create a JWT that expired 1 second ago."""
    from app.auth import create_access_token
    return create_access_token({"sub": "99999"}, expires_delta=timedelta(seconds=-1))


def _make_no_sub_token():
    """Create a JWT that has no 'sub' claim."""
    from app.auth import create_access_token
    return create_access_token({"data": "no_subject_here"})


def _tamper_token(token: str) -> str:
    """Flip the last character of the signature to break HMAC."""
    parts = token.split(".")
    sig = parts[-1]
    # Flip last char: 'A' <-> 'B'
    last = sig[-1]
    tampered_last = "B" if last != "B" else "A"
    parts[-1] = sig[:-1] + tampered_last
    return ".".join(parts)


# ---------------------------------------------------------------------------
# JWT Security Tests
# ---------------------------------------------------------------------------

class TestJWTSecurity:
    def test_tampered_signature_returns_401(self, client, registered_user):
        token, _ = registered_user
        bad_token = _tamper_token(token)
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"

    def test_expired_token_returns_401(self, client):
        expired = _make_expired_token()
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"

    def test_token_missing_sub_returns_401(self, client):
        no_sub = _make_no_sub_token()
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {no_sub}"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"

    def test_completely_invalid_token_returns_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.json()}"

    def test_no_auth_header_returns_403(self, client):
        """HTTPBearer returns 403 when Authorization header is absent entirely."""
        resp = client.get("/auth/me")
        assert resp.status_code == 403

    def test_tampered_token_blocked_on_follows(self, client, registered_user):
        """Tampered token must not allow access to protected follows endpoint."""
        token, _ = registered_user
        bad_token = _tamper_token(token)
        resp = client.post(
            "/follows",
            json={"bettor_address": "0xhacker"},
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# VIP Tier — Unlimited Follows
# ---------------------------------------------------------------------------

class TestVIPUnlimitedFollows:
    def _upgrade_to_vip(self, db, registered_user):
        from app.models import User
        _, user_data = registered_user
        user = db.query(User).filter(User.id == user_data["id"]).first()
        user.subscription_tier = "vip"
        db.commit()

    def test_vip_can_add_more_than_5_follows(self, client, db, auth_headers, registered_user):
        self._upgrade_to_vip(db, registered_user)
        addresses = [f"0x{i:040x}" for i in range(6)]
        for addr in addresses:
            resp = client.post(
                "/follows",
                json={"bettor_address": addr},
                headers=auth_headers,
            )
            assert resp.status_code == 201, f"VIP follow #{addresses.index(addr)+1} failed: {resp.json()}"

    def test_vip_can_add_10_follows(self, client, db, auth_headers, registered_user):
        self._upgrade_to_vip(db, registered_user)
        for i in range(10):
            resp = client.post(
                "/follows",
                json={"bettor_address": f"0xvip{i:036x}"},
                headers=auth_headers,
            )
            assert resp.status_code == 201, f"VIP follow #{i+1} failed: {resp.json()}"

    def test_follows_endpoint_reports_vip_limit(self, client, db, auth_headers, registered_user):
        self._upgrade_to_vip(db, registered_user)
        resp = client.get("/follows", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "vip"
        assert data["limit"] == 999999


# ---------------------------------------------------------------------------
# Input Validation — Register Missing Fields
# ---------------------------------------------------------------------------

class TestRegisterInputValidation:
    def test_register_missing_email_returns_422(self, client):
        resp = client.post("/auth/register", json={"password": "pass123", "name": "Alice"})
        assert resp.status_code == 422

    def test_register_missing_password_returns_422(self, client):
        resp = client.post("/auth/register", json={"email": "a@b.com", "name": "Alice"})
        assert resp.status_code == 422

    def test_register_missing_name_returns_422(self, client):
        resp = client.post("/auth/register", json={"email": "a@b.com", "password": "pass123"})
        assert resp.status_code == 422

    def test_register_empty_body_returns_422(self, client):
        resp = client.post("/auth/register", json={})
        assert resp.status_code == 422

    def test_login_missing_email_returns_422(self, client):
        resp = client.post("/auth/login", json={"password": "pass123"})
        assert resp.status_code == 422

    def test_login_missing_password_returns_422(self, client):
        resp = client.post("/auth/login", json={"email": "a@b.com"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Unfollow Then Re-follow
# ---------------------------------------------------------------------------

class TestUnfollowThenRefollow:
    def test_unfollow_then_refollow_succeeds(self, client, auth_headers):
        """After unfollowing, re-following the same address must not return 409."""
        addr = "0xrefollow123"
        # Follow
        resp = client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)
        assert resp.status_code == 201
        # Unfollow
        resp = client.delete(f"/follows/{addr}", headers=auth_headers)
        assert resp.status_code == 204
        # Re-follow — must not be 409
        resp = client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)
        assert resp.status_code == 201, f"Re-follow failed: {resp.status_code} {resp.json()}"


# ---------------------------------------------------------------------------
# Bettor Detail — Unknown Address Returns Gracefully
# ---------------------------------------------------------------------------

class TestBettorUnknownAddress:
    def test_unknown_address_returns_200_not_500(self, client):
        """GET /bettors/{bad_address} should return 200 with empty/None profile, not 500."""
        with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=None)), \
             patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=[])):
            resp = client.get("/bettors/0xunknownaddress999")
        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert data["profile"] is None
        assert data["recent_bets"] == []

    def test_bettor_api_error_returns_502(self, client):
        """When Polymarket API fails, bettor detail must return 502, not 500."""
        with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(side_effect=Exception("API down"))):
            resp = client.get("/bettors/0xbadaddress")
        assert resp.status_code == 502
