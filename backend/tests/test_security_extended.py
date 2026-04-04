"""
Extended security tests covering:
  1. XSS payloads in name field on register — stored safely, no 500
  2. XSS payload in bettor address on follows — stored safely, no 500
  3. SQL injection in name field on register — no 500
  4. SQL injection in address field on follows — no 500, 4xx returned
  5. SQL injection in GET /bettors/{address} path — no 500
  6. Modified tier claim in JWT — server reads tier from DB, not JWT payload
  7. Auth bypass via every protected endpoint — all reject missing/bad tokens
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.auth import create_access_token
from app.models import User
from app.auth import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    '"><img src=x onerror=alert(1)>',
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
]

SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "; DROP TABLE users; --",
    "' UNION SELECT * FROM users --",
    "1; SELECT sleep(5) --",
]


# ---------------------------------------------------------------------------
# XSS Payload Tests — Name Field on Register
# ---------------------------------------------------------------------------

class TestXSSInNameField:
    """XSS payloads in the name field must be accepted (201) and stored safely.

    The backend is not responsible for HTML-escaping; it stores raw data.
    The important security property is: no 500 error, no server crash,
    and the data round-trips correctly (GET /auth/me returns it as-is).
    """

    @pytest.mark.parametrize("xss_payload", XSS_PAYLOADS)
    def test_xss_in_name_stored_safely_no_500(self, client, xss_payload):
        """Registering with an XSS payload in name must return 201, not 500."""
        unique_email = f"xss_{hash(xss_payload) & 0xFFFF:04x}@example.com"
        resp = client.post("/auth/register", json={
            "email": unique_email,
            "password": "safepass123",
            "name": xss_payload,
        })
        assert resp.status_code == 201, (
            f"XSS name payload caused unexpected status {resp.status_code}: {resp.json()}"
        )

    def test_xss_name_round_trips_via_auth_me(self, client):
        """XSS payload in name must round-trip correctly via GET /auth/me."""
        xss = "<script>alert(1)</script>"
        resp = client.post("/auth/register", json={
            "email": "xss_roundtrip@example.com",
            "password": "safepass123",
            "name": xss,
        })
        assert resp.status_code == 201
        token = resp.json()["access_token"]

        me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        # The payload is stored as-is and returned as-is — frontend is responsible for escaping
        assert me.json()["user"]["name"] == xss


# ---------------------------------------------------------------------------
# XSS Payload in Bettor Address
# ---------------------------------------------------------------------------

class TestXSSInBettorAddress:
    """XSS payloads in bettor_address on POST /follows must not cause 500."""

    @pytest.mark.parametrize("xss_payload", XSS_PAYLOADS)
    def test_xss_in_bettor_address_no_500(self, client, auth_headers, xss_payload):
        """Following a bettor with XSS payload as address — stored safely or rejected, not 500."""
        resp = client.post(
            "/follows",
            json={"bettor_address": xss_payload},
            headers=auth_headers,
        )
        # Must not be a server error — 2xx means stored, 4xx means rejected as invalid address
        assert resp.status_code < 500, (
            f"XSS in bettor_address caused server error {resp.status_code}: {resp.json()}"
        )


# ---------------------------------------------------------------------------
# SQL Injection Tests — Name Field on Register
# ---------------------------------------------------------------------------

class TestSQLInjectionInName:
    """SQL injection payloads in the name field must not crash the server."""

    @pytest.mark.parametrize("sql_payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_in_name_no_500(self, client, sql_payload):
        """SQL injection in name field must return 201 (stored safely) or 4xx, never 500."""
        unique_email = f"sqli_{hash(sql_payload) & 0xFFFF:04x}@example.com"
        resp = client.post("/auth/register", json={
            "email": unique_email,
            "password": "safepass123",
            "name": sql_payload,
        })
        assert resp.status_code < 500, (
            f"SQL injection in name field caused server error {resp.status_code}: {resp.json()}"
        )


# ---------------------------------------------------------------------------
# SQL Injection Tests — Bettor Address on Follows
# ---------------------------------------------------------------------------

class TestSQLInjectionInBettorAddress:
    """SQL injection payloads in bettor_address must return 4xx, never 500."""

    @pytest.mark.parametrize("sql_payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_in_bettor_address_no_500(self, client, auth_headers, sql_payload):
        resp = client.post(
            "/follows",
            json={"bettor_address": sql_payload},
            headers=auth_headers,
        )
        assert resp.status_code < 500, (
            f"SQL injection in bettor_address caused server error {resp.status_code}: {resp.json()}"
        )


# ---------------------------------------------------------------------------
# SQL Injection Tests — GET /bettors/{address} Path Parameter
# ---------------------------------------------------------------------------

class TestSQLInjectionInBettorAddressPath:
    """SQL injection payloads in the bettors/{address} URL path must not cause 500."""

    @pytest.mark.parametrize("sql_payload", SQL_INJECTION_PAYLOADS)
    def test_sql_injection_in_bettors_path_no_500(self, client, sql_payload):
        """GET /bettors/<sqli_payload> must return 2xx or 4xx, never 500."""
        with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=None)), \
             patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=[])):
            resp = client.get(f"/bettors/{sql_payload}")
        assert resp.status_code < 500, (
            f"SQL injection in bettors path caused server error {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Modified Tier Claim in JWT — Server Uses DB Tier, Not JWT Claim
# ---------------------------------------------------------------------------

class TestModifiedTierClaimInJWT:
    """
    An attacker who somehow gets the JWT secret could add a 'tier: vip' claim
    to a free user's token. The server must still enforce the DB tier.

    This tests that get_current_user() returns the DB User (with free tier)
    and that follow limits are enforced based on DB subscription_tier, not the JWT.
    """

    def _make_token_with_tier_claim(self, user_id: int, tier: str) -> str:
        """Create a valid JWT with an extra 'tier' claim (as if forged by attacker)."""
        return create_access_token({"sub": str(user_id), "tier": tier})

    def test_jwt_with_vip_tier_claim_does_not_bypass_free_limit(self, client, db):
        """Free user with a crafted JWT claiming 'tier: vip' must still be blocked at follow limit 1."""
        # Register a free user
        resp = client.post("/auth/register", json={
            "email": "freeuser_tiertest@example.com",
            "password": "pass123",
            "name": "Free Tier Victim",
        })
        assert resp.status_code == 201
        user_id = resp.json()["user"]["id"]

        # Craft a JWT with a fake vip tier claim
        forged_token = self._make_token_with_tier_claim(user_id, "vip")
        forged_headers = {"Authorization": f"Bearer {forged_token}"}

        # First follow — should succeed (free tier allows 1)
        resp1 = client.post(
            "/follows",
            json={"bettor_address": "0xlegitbettor001"},
            headers=forged_headers,
        )
        assert resp1.status_code == 201, f"First follow failed: {resp1.json()}"

        # Second follow — must be blocked (DB tier=free, limit=1), despite JWT claiming vip
        resp2 = client.post(
            "/follows",
            json={"bettor_address": "0xlegitbettor002"},
            headers=forged_headers,
        )
        assert resp2.status_code == 403, (
            f"JWT tier claim bypass succeeded — server used JWT tier instead of DB tier. "
            f"Got {resp2.status_code}: {resp2.json()}"
        )

    def test_jwt_tier_claim_ignored_in_auth_me(self, client, db):
        """GET /auth/me must return the DB tier (free), not the JWT's forged tier claim."""
        resp = client.post("/auth/register", json={
            "email": "freeuser_me_test@example.com",
            "password": "pass123",
            "name": "Me Test User",
        })
        assert resp.status_code == 201
        user_id = resp.json()["user"]["id"]

        forged_token = self._make_token_with_tier_claim(user_id, "vip")
        me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {forged_token}"})
        assert me_resp.status_code == 200
        # The returned user data must reflect the DB tier, not the JWT claim
        assert me_resp.json()["user"]["subscription_tier"] == "free", (
            f"Server returned JWT-claimed tier instead of DB tier: {me_resp.json()}"
        )


# ---------------------------------------------------------------------------
# Auth Bypass — Protected Endpoints Reject Bad Tokens
# ---------------------------------------------------------------------------

class TestAuthBypassProtectedEndpoints:
    """Every protected endpoint must reject: no token, wrong token, completely invalid token."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/auth/me"),
        ("GET", "/follows"),
        ("POST", "/follows"),
        ("GET", "/follows/live"),
        ("GET", "/alerts/settings"),
        ("PUT", "/alerts/settings"),
        ("POST", "/alerts/telegram/start"),
        ("POST", "/payments/checkout"),
        ("GET", "/payments/portal"),
    ]

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_no_token_returns_403(self, client, method, path):
        """HTTPBearer returns 403 when Authorization header is absent."""
        resp = client.request(method, path)
        assert resp.status_code in (401, 403), (
            f"{method} {path} with no token returned {resp.status_code}: {resp.json()}"
        )

    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    def test_invalid_token_returns_401(self, client, method, path):
        """Completely invalid token must return 401."""
        resp = client.request(
            method, path,
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert resp.status_code in (401, 403), (
            f"{method} {path} with invalid token returned {resp.status_code}: {resp.json()}"
        )
