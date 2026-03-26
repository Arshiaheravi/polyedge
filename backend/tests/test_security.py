"""
Security and business-rule edge-case tests.
Covers: JWT tampering, expiry, missing sub; VIP unlimited follows;
register input validation; unfollow-then-re-follow; bettor unknown address;
bcrypt hash storage; rate-limit stability under rapid login attempts.
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
    """Corrupt the JWT signature by flipping the first character.

    The last character of a base64url-encoded HMAC-SHA256 signature (43 chars
    for 32 bytes) has 2 unused padding bits, so flipping between 'A' and 'B'
    only changes those padding bits — the decoded signature bytes are identical
    and JWT verification passes. Tampering the first character guarantees all
    6 bits are significant and the decoded signature changes.
    """
    parts = token.split(".")
    sig = parts[-1]
    first = sig[0]
    tampered_first = "B" if first != "B" else "A"
    parts[-1] = tampered_first + sig[1:]
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

    def test_token_missing_sub_treated_as_free_on_optional_auth_endpoint(self, client):
        """JWT with no 'sub' claim → get_current_user_optional returns None → treated as free tier.

        Covers auth.py:72-73: `user_id = payload.get("sub"); if user_id is None: return None`
        The caller (/markets/consensus) must handle None as anonymous/free, not as a 401.
        """
        import app.routes.markets as markets_mod
        import time
        from unittest.mock import AsyncMock, patch

        markets_mod._consensus_cache["data"] = None
        markets_mod._consensus_cache["ts"] = 0

        no_sub = _make_no_sub_token()
        with patch(
            "app.routes.markets.get_consensus_signals",
            new=AsyncMock(return_value=[]),
        ):
            resp = client.get(
                "/markets/consensus",
                headers={"Authorization": f"Bearer {no_sub}"},
            )
        assert resp.status_code == 200, (
            f"Optional-auth endpoint must return 200, not reject a no-sub JWT: {resp.json()}"
        )
        data = resp.json()
        assert data["tier"] == "free", (
            "No-sub JWT must be treated as anonymous (free tier), not authenticated"
        )

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


# ---------------------------------------------------------------------------
# Bcrypt Hash Storage
# ---------------------------------------------------------------------------

def test_password_stored_as_bcrypt_hash(client, db):
    """Registered user's password must be stored as a bcrypt hash ($2b$), never plaintext."""
    from app.models import User

    client.post("/auth/register", json={
        "email": "hashcheck@example.com",
        "password": "supersecretpass",
        "name": "HashUser",
    })

    user = db.query(User).filter(User.email == "hashcheck@example.com").first()
    assert user is not None
    assert user.hashed_password.startswith("$2b$"), (
        f"Expected bcrypt prefix '$2b$' but got: {user.hashed_password[:10]}"
    )
    assert "supersecretpass" not in user.hashed_password, (
        "Plaintext password must never appear in hashed_password column"
    )


# ---------------------------------------------------------------------------
# Rate Limiting — server stability under rapid repeated login attempts
# ---------------------------------------------------------------------------

def test_rapid_login_attempts_never_500(client):
    """10 rapid login attempts must not produce any 500 errors.

    The server has no formal rate limiting — this test verifies that repeated
    failed auth requests are handled gracefully (400/401/422) and never crash
    with a 500 Internal Server Error, which would indicate a bug in auth logic.
    """
    client.post("/auth/register", json={
        "email": "ratelimit@example.com",
        "password": "correctpass",
        "name": "RateUser",
    })

    for _ in range(10):
        resp = client.post("/auth/login", json={
            "email": "ratelimit@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code != 500, (
            f"Server returned 500 on a login attempt — auth must never crash: {resp.text}"
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Mass Assignment — register body must not accept subscription_tier
# ---------------------------------------------------------------------------

class TestMassAssignment:
    """Verify that clients cannot set privileged fields during registration."""

    def test_register_with_vip_tier_in_body_creates_free_user(self, client):
        """Posting subscription_tier:'vip' in register body must be ignored — user gets 'free'."""
        resp = client.post("/auth/register", json={
            "email": "massassign@example.com",
            "password": "securepass123",
            "name": "MassAssignUser",
            "subscription_tier": "vip",  # attacker-supplied privilege escalation attempt
        })
        # Pydantic ignores unknown fields by default — request succeeds
        assert resp.status_code == 201, f"Expected 201 got {resp.status_code}: {resp.json()}"
        data = resp.json()
        assert data["user"]["subscription_tier"] == "free", (
            f"Mass assignment succeeded — user got tier '{data['user']['subscription_tier']}' "
            "instead of 'free'. The register route must hardcode tier='free'."
        )

    def test_register_with_basic_tier_in_body_creates_free_user(self, client):
        """subscription_tier:'basic' in body must also be ignored."""
        resp = client.post("/auth/register", json={
            "email": "massassign2@example.com",
            "password": "securepass123",
            "name": "MassAssignUser2",
            "subscription_tier": "basic",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["user"]["subscription_tier"] == "free"

    def test_register_with_admin_flag_in_body_creates_free_user(self, client):
        """Extra privilege fields must be silently dropped — no 500 or unexpected tier."""
        resp = client.post("/auth/register", json={
            "email": "massassign3@example.com",
            "password": "securepass123",
            "name": "MassAssignUser3",
            "is_admin": True,
            "subscription_tier": "vip",
            "stripe_customer_id": "cus_attacker",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["user"]["subscription_tier"] == "free"


# ---------------------------------------------------------------------------
# Sensitive Data Leakage — no internal fields in API responses
# ---------------------------------------------------------------------------

_SENSITIVE_FIELDS = ("hashed_password", "stripe_customer_id", "telegram_chat_id")


class TestSensitiveDataLeakage:
    """Verify that internal DB fields never appear in any API response body."""

    def _assert_no_sensitive_fields(self, body: str, endpoint: str):
        for field in _SENSITIVE_FIELDS:
            assert field not in body, (
                f"Sensitive field '{field}' found in {endpoint} response. "
                "This data must never be returned to API consumers."
            )

    def test_register_response_has_no_sensitive_fields(self, client):
        resp = client.post("/auth/register", json={
            "email": "sensitivecheck@example.com",
            "password": "testpass123",
            "name": "SensCheck",
        })
        assert resp.status_code == 201
        self._assert_no_sensitive_fields(resp.text, "POST /auth/register")

    def test_login_response_has_no_sensitive_fields(self, client):
        client.post("/auth/register", json={
            "email": "sensitivelogin@example.com",
            "password": "testpass123",
            "name": "SensLogin",
        })
        resp = client.post("/auth/login", json={
            "email": "sensitivelogin@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        self._assert_no_sensitive_fields(resp.text, "POST /auth/login")

    def test_get_me_response_has_no_sensitive_fields(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        self._assert_no_sensitive_fields(resp.text, "GET /auth/me")

    def test_admin_stats_response_has_no_sensitive_fields(self, client):
        from app.config import get_settings
        pw = get_settings().admin_password
        resp = client.get("/admin/stats", headers={"x-admin-password": pw})
        assert resp.status_code == 200
        self._assert_no_sensitive_fields(resp.text, "GET /admin/stats")
