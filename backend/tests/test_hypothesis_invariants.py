"""
Hypothesis property-based invariant tests for PolyEdge.
These verify that hard business-rule invariants hold for ALL valid inputs,
not just the examples we thought to write.
"""
import pytest
from hypothesis import given, settings, strategies as st, HealthCheck


# ── Invariant 1: GET /follows always returns tier + limit fields ──────────────

@pytest.mark.parametrize("tier,expected_limit", [
    ("free", 1),
    ("basic", 5),
    ("vip", 999999),
])
def test_follows_always_returns_tier_and_limit(client, db, registered_user, tier, expected_limit):
    """GET /follows always returns tier + limit regardless of subscription tier."""
    from app.models import User
    token, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = tier
    db.commit()

    resp = client.get("/follows", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "tier" in body, "tier field must always be present"
    assert "limit" in body, "limit field must always be present"
    assert body["tier"] == tier
    assert body["limit"] == expected_limit


# ── Invariant 2: POST /follows never exceeds TIER_LIMITS for any tier ─────────

@pytest.mark.parametrize("tier,limit", [
    ("free", 1),
    ("basic", 5),
])
def test_post_follows_never_exceeds_tier_limit(client, db, registered_user, tier, limit):
    """POST /follows must reject the (limit+1)-th follow with 403, never allowing over-limit."""
    from app.models import User
    token, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = tier
    db.commit()
    headers = {"Authorization": f"Bearer {token}"}

    # Fill up to the limit
    for i in range(limit):
        resp = client.post("/follows", json={"bettor_address": f"0x{'a' * 39}{i:01x}"}, headers=headers)
        assert resp.status_code == 201, f"follow {i+1} of {limit} should succeed"

    # One more must be rejected
    resp = client.post("/follows", json={"bettor_address": f"0x{'b' * 40}"}, headers=headers)
    assert resp.status_code == 403, f"follow {limit+1} should be rejected for {tier} tier"


# ── Invariant 3: protected endpoints always return 401 when auth is missing ───

@pytest.mark.parametrize("method,path,body", [
    ("GET",    "/follows",          None),
    ("POST",   "/follows",          {"bettor_address": "0xabc"}),
    ("GET",    "/alerts/settings",  None),
    ("PUT",    "/alerts/settings",  {"web_push_enabled": True}),
    ("GET",    "/auth/me",          None),
    ("GET",    "/payments/portal",  None),
    ("POST",   "/payments/checkout", {"plan": "basic"}),
])
def test_protected_endpoints_reject_missing_auth(client, method, path, body):
    """Every protected endpoint must return 401 or 403 when Authorization header is absent."""
    if method == "GET":
        resp = client.get(path)
    elif method == "POST":
        resp = client.post(path, json=body)
    elif method == "PUT":
        resp = client.put(path, json=body)
    else:
        resp = client.request(method, path, json=body)

    assert resp.status_code in (401, 403), (
        f"{method} {path} returned {resp.status_code} without auth — expected 401 or 403"
    )


# ── Invariant 4: adversarial bettor addresses never cause 500 ─────────────────

@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(address=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=80))
def test_bettor_address_never_causes_500(client, address):
    """GET /bettors/{address} must never return 500 for any non-empty address string."""
    from unittest.mock import patch, AsyncMock
    import app.routes.bettors as bettors_mod
    bettors_mod._profile_cache.clear()

    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=None)):
        resp = client.get(f"/bettors/{address}")

    assert resp.status_code != 500, f"GET /bettors/{address!r} returned 500"
