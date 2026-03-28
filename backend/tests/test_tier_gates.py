"""
Tier gate tests — verify that /markets/consensus and /follows/live
correctly enforce tier restrictions for free, basic, and VIP users.

Tests:
  - Consensus: unauthenticated (free) → ≤3 signals, names_visible=False
  - Consensus: basic → all signals, names_visible=False, whale_names=[]
  - Consensus: VIP → all signals, names_visible=True, whale_names populated
  - Follows/live: tier field is always current user's tier (free/basic/vip)
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.models import User
from app.auth import hash_password, create_access_token


# ---------------------------------------------------------------------------
# Mock data
# ---------------------------------------------------------------------------

# 5 consensus signals — more than the free-tier cap of 3
MOCK_SIGNALS = [
    {
        "market_title": f"Market {i}",
        "condition_id": f"0x{'a' * 64}",
        "outcome": "Yes",
        "whale_count": 5,
        "avg_entry_price": 0.60,
        "current_price": 0.65,
        "whale_names": [f"whale_{i}_a", f"whale_{i}_b"],
        "event_slug": f"market-{i}",
    }
    for i in range(5)
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_caches():
    """Isolate module-level caches between tests."""
    import app.routes.markets as markets_mod
    import app.routes.follows as follows_mod
    markets_mod._consensus_cache["data"] = None
    markets_mod._consensus_cache["ts"] = 0
    follows_mod._activity_cache.clear()
    yield
    markets_mod._consensus_cache["data"] = None
    markets_mod._consensus_cache["ts"] = 0
    follows_mod._activity_cache.clear()


def _make_user(db, email: str, tier: str):
    """Create a user with the given tier and return (user, token, headers)."""
    user = User(
        email=email,
        hashed_password=hash_password("pw"),
        name=f"{tier.title()}User",
        subscription_tier=tier,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}
    return user, token, headers


# ---------------------------------------------------------------------------
# /markets/consensus — tier gate
# ---------------------------------------------------------------------------

def test_consensus_unauthenticated_free_tier_limit(client):
    """Unauthenticated request → free tier: ≤3 signals, names_visible=False."""
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "free"
    assert data["names_visible"] is False
    assert len(data["signals"]) <= 3, (
        "Free/unauthenticated users must see at most 3 consensus signals"
    )


def test_consensus_unauthenticated_whale_names_hidden(client):
    """Unauthenticated request → whale_names is empty list on every signal."""
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus")
    assert resp.status_code == 200
    for signal in resp.json()["signals"]:
        assert signal["whale_names"] == [], (
            "Unauthenticated users must never see whale names"
        )


def test_consensus_basic_tier_gets_all_signals(client, db):
    """Basic user → all signals returned (not capped at 3)."""
    _, _, headers = _make_user(db, "basic_cons@test.com", "basic")
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "basic"
    assert data["names_visible"] is False
    assert len(data["signals"]) == len(MOCK_SIGNALS), (
        "Basic users must see all consensus signals, not just the free-tier top 3"
    )


def test_consensus_basic_tier_whale_names_hidden(client, db):
    """Basic user → whale_names empty on every signal."""
    _, _, headers = _make_user(db, "basic_names@test.com", "basic")
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus", headers=headers)
    assert resp.status_code == 200
    for signal in resp.json()["signals"]:
        assert signal["whale_names"] == [], (
            "Basic users must not see whale names — VIP feature only"
        )


def test_consensus_vip_tier_gets_all_signals(client, db):
    """VIP user → all signals returned."""
    _, _, headers = _make_user(db, "vip_cons@test.com", "vip")
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "vip"
    assert data["names_visible"] is True
    assert len(data["signals"]) == len(MOCK_SIGNALS), (
        "VIP users must see all consensus signals"
    )


def test_consensus_vip_tier_whale_names_visible(client, db):
    """VIP user → whale_names populated on every signal."""
    _, _, headers = _make_user(db, "vip_names@test.com", "vip")
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus", headers=headers)
    assert resp.status_code == 200
    for signal in resp.json()["signals"]:
        assert len(signal["whale_names"]) > 0, (
            "VIP users must see whale names — they are populated in mock data"
        )


def test_consensus_response_has_required_fields(client):
    """Consensus response always includes tier, names_visible, total_available, signals."""
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus")
    assert resp.status_code == 200
    data = resp.json()
    for key in ("signals", "tier", "names_visible", "total_available"):
        assert key in data, f"Response missing required field: {key}"


def test_consensus_cache_hit_returns_cached_data_without_calling_service(client):
    """Cache hit path: pre-populated cache is served without invoking get_consensus_signals.

    Covers markets.py:29 — the branch `if _consensus_cache["data"] and (now - ts) < TTL`
    was never exercised because every test clears the cache before calling the endpoint.
    """
    import time
    import app.routes.markets as markets_mod

    # Pre-populate cache with fresh data (ts = now → well within TTL)
    cached_signals = MOCK_SIGNALS[:2]
    markets_mod._consensus_cache["data"] = cached_signals
    markets_mod._consensus_cache["ts"] = time.time()

    mock_service = AsyncMock()
    with patch("app.routes.markets.get_consensus_signals", new=mock_service):
        resp = client.get("/markets/consensus")

    assert resp.status_code == 200
    mock_service.assert_not_called(), "Cache hit must NOT call get_consensus_signals"
    data = resp.json()
    assert data["total_available"] == len(cached_signals), (
        "Cache hit must return the pre-populated signals, not a fresh fetch"
    )


def test_consensus_total_available_reflects_all_signals(client, db):
    """total_available always equals the full signal count, regardless of tier cap."""
    _, _, headers = _make_user(db, "free_total@test.com", "free")
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_available"] == len(MOCK_SIGNALS), (
        "total_available must reflect the full count, even if signals list is capped"
    )


def test_consensus_api_error_returns_502(client):
    """If get_consensus_signals raises, /markets/consensus must return 502 (not 500).

    Bug: markets.py had no try/except around get_consensus_signals, so any API
    failure produced an unhandled 500. Fixed to match other endpoints that return 502.
    Cache must NOT be updated on error (so next request retries the API).
    """
    import app.routes.markets as markets_mod

    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(side_effect=Exception("connection timeout"))):
        resp = client.get("/markets/consensus")

    assert resp.status_code == 502, (
        f"Expected 502 on Polymarket API error, got {resp.status_code}. "
        "markets.py must wrap get_consensus_signals in try/except."
    )
    assert "Polymarket API error" in resp.json().get("detail", ""), (
        "502 response must include 'Polymarket API error' in detail"
    )
    # Cache must NOT be poisoned by the error
    assert markets_mod._consensus_cache["data"] is None, (
        "Cache must not be updated when the API call fails — next request must retry"
    )


def test_consensus_each_signal_has_required_fields(client):
    """Every signal item in the response must include all 7 required fields.

    Regression guard: if the service or route drops a field (e.g. event_slug),
    this test will fail before the silent frontend breakage reaches users.
    """
    REQUIRED_SIGNAL_FIELDS = {
        "market_title", "condition_id", "outcome",
        "whale_count", "avg_entry_price", "current_price",
        "whale_names", "event_slug",
    }
    with patch("app.routes.markets.get_consensus_signals",
               new=AsyncMock(return_value=MOCK_SIGNALS)):
        resp = client.get("/markets/consensus")

    assert resp.status_code == 200
    signals = resp.json()["signals"]
    assert len(signals) > 0, "Must have at least one signal to check fields"
    for i, sig in enumerate(signals):
        missing = REQUIRED_SIGNAL_FIELDS - set(sig.keys())
        assert not missing, (
            f"Signal[{i}] is missing required fields: {missing}. "
            f"Got keys: {set(sig.keys())}"
        )


# ---------------------------------------------------------------------------
# /follows/live — tier field correctness
# ---------------------------------------------------------------------------

def test_follows_live_free_user_tier_field(client, db):
    """GET /follows/live for a free user returns tier='free'."""
    _, _, headers = _make_user(db, "free_live@test.com", "free")
    resp = client.get("/follows/live", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "free"


def test_follows_live_basic_user_tier_field(client, db):
    """GET /follows/live for a basic user returns tier='basic'."""
    _, _, headers = _make_user(db, "basic_live@test.com", "basic")
    resp = client.get("/follows/live", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "basic"


def test_follows_live_vip_user_tier_field(client, db):
    """GET /follows/live for a VIP user returns tier='vip'."""
    _, _, headers = _make_user(db, "vip_live@test.com", "vip")
    resp = client.get("/follows/live", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "vip"


def test_follows_live_tier_not_stale_after_upgrade(client, db):
    """Cached /follows/live response must reflect current tier, not tier at cache-fill time.

    Regression test for Bug #140: the cache stored tier at fill-time; after free→VIP upgrade
    the cached response would return tier='free' until the TTL expired.
    Fix (session 140): route always injects current_user.subscription_tier on cache hit.
    """
    import app.routes.follows as follows_mod

    # Start as free, fill cache
    user, _, free_headers = _make_user(db, "upgrade_live@test.com", "free")
    resp = client.get("/follows/live", headers=free_headers)
    assert resp.status_code == 200
    assert resp.json()["tier"] == "free"

    # Simulate upgrade: change tier in DB directly
    user.subscription_tier = "vip"
    db.commit()
    db.refresh(user)

    # Cache still has the old entry — but tier should be live from DB
    new_token = create_access_token({"sub": str(user.id)})
    vip_headers = {"Authorization": f"Bearer {new_token}"}
    resp2 = client.get("/follows/live", headers=vip_headers)
    assert resp2.status_code == 200
    assert resp2.json()["tier"] == "vip", (
        "tier must reflect current DB value, not cached tier at fill time (Bug #140 regression)"
    )
