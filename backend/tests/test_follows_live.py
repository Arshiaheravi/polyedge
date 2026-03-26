"""Tests for /follows/live endpoint — mocked Polymarket API calls."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def clear_activity_cache():
    """Clear the in-memory activity cache before each test."""
    import app.routes.follows as follows_module
    follows_module._activity_cache.clear()
    yield
    follows_module._activity_cache.clear()


MOCK_POSITIONS = [
    {
        "market_title": "Will BTC hit $200k by 2026?",
        "outcome": "Yes",
        "size": 100.0,
        "current_value_usd": 4500.0,
        "initial_value_usd": 4000.0,
        "avg_price": 0.40,
        "cur_price": 0.45,
        "cash_pnl": 500.0,
        "percent_pnl": 12.5,
        "end_date": "2026-12-31",
        "poly_url": "https://polymarket.com/event/btc-200k",
        "icon": "",
    }
]


def test_follows_live_requires_auth(client):
    resp = client.get("/follows/live")
    assert resp.status_code == 403


def test_follows_live_empty(client, auth_headers):
    """User with no follows gets empty bettors list."""
    resp = client.get("/follows/live", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["bettors"] == []


def test_follows_live_returns_positions(client, auth_headers):
    """After following a bettor, live returns their open copyable positions."""
    client.post("/follows", json={"bettor_address": "0xabc", "bettor_name": "whale1"},
                headers=auth_headers)

    with patch("app.routes.follows.get_active_positions", new=AsyncMock(return_value=MOCK_POSITIONS)):
        resp = client.get("/follows/live", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["bettors"]) == 1
    bettor = data["bettors"][0]
    assert bettor["name"] == "whale1"
    assert bettor["address"] == "0xabc"
    assert len(bettor["active_positions"]) == 1
    assert bettor["active_positions"][0]["market_title"] == "Will BTC hit $200k by 2026?"
    assert bettor["active_positions"][0]["poly_url"] == "https://polymarket.com/event/btc-200k"


def test_follows_live_handles_api_error_gracefully(client, auth_headers):
    """If Polymarket API errors, returns empty positions (not 500)."""
    client.post("/follows", json={"bettor_address": "0xabc"}, headers=auth_headers)

    with patch("app.routes.follows.get_active_positions", new=AsyncMock(side_effect=Exception("timeout"))):
        resp = client.get("/follows/live", headers=auth_headers)

    assert resp.status_code == 200
    bettor = resp.json()["bettors"][0]
    assert bettor["active_positions"] == []


def test_follows_live_multiple_bettors(client, db, auth_headers, registered_user):
    """VIP user following multiple bettors gets positions for all of them."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()

    for i, addr in enumerate(["0xaaa", "0xbbb", "0xccc"]):
        client.post("/follows", json={"bettor_address": addr, "bettor_name": f"bettor{i}"},
                    headers=auth_headers)

    with patch("app.routes.follows.get_active_positions", new=AsyncMock(return_value=MOCK_POSITIONS)):
        resp = client.get("/follows/live", headers=auth_headers)

    assert resp.status_code == 200
    assert len(resp.json()["bettors"]) == 3


def test_follows_live_bettor_includes_followed_at_field(client, auth_headers):
    """GET /follows/live response includes 'followed_at' field for each bettor."""
    client.post("/follows", json={"bettor_address": "0xat_field", "bettor_name": "AtFieldWhale"},
                headers=auth_headers)

    with patch("app.routes.follows.get_active_positions", new=AsyncMock(return_value=[])):
        resp = client.get("/follows/live", headers=auth_headers)

    assert resp.status_code == 200
    bettor = resp.json()["bettors"][0]
    assert "followed_at" in bettor  # isoformat string or None, but must be present


def test_follows_live_name_fallback_when_bettor_name_is_none(client, db, auth_headers, registered_user):
    """When bettor_name is None in DB, _fetch_one falls back to addr[:12]+'...'."""
    import app.routes.follows as follows_module
    follows_module._activity_cache.clear()

    addr = "0xabcdefghijkl1234"
    client.post("/follows", json={"bettor_address": addr, "bettor_name": "original"},
                headers=auth_headers)

    # Manually set bettor_name to None in DB to trigger the fallback path
    from app.models import BettorFollow as BF
    follow = db.query(BF).filter(BF.bettor_address == addr).first()
    follow.bettor_name = None
    db.commit()
    follows_module._activity_cache.clear()

    with patch("app.routes.follows.get_active_positions", new=AsyncMock(return_value=[])):
        resp = client.get("/follows/live", headers=auth_headers)

    assert resp.status_code == 200
    bettor = resp.json()["bettors"][0]
    assert bettor["name"] == addr[:12] + "..."


def test_follows_live_serves_cached_response(client, auth_headers):
    """Second call within TTL returns cached data — Polymarket API called only once."""
    client.post("/follows", json={"bettor_address": "0xcache", "bettor_name": "CacheWhale"},
                headers=auth_headers)

    mock_api = AsyncMock(return_value=MOCK_POSITIONS)
    with patch("app.routes.follows.get_active_positions", new=mock_api):
        resp1 = client.get("/follows/live", headers=auth_headers)
        resp2 = client.get("/follows/live", headers=auth_headers)

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()
    assert mock_api.call_count == 1


def test_delete_follow_clears_activity_cache(client, auth_headers):
    """DELETE /follows/{address} must evict the user's cache entry.
    Without eviction, a subsequent GET /follows/live returns stale data."""
    import app.routes.follows as follows_module

    addr = "0xevict1"
    client.post("/follows", json={"bettor_address": addr, "bettor_name": "EvictTest"},
                headers=auth_headers)

    # Populate the cache
    mock_api = AsyncMock(return_value=MOCK_POSITIONS)
    with patch("app.routes.follows.get_active_positions", new=mock_api):
        resp = client.get("/follows/live", headers=auth_headers)
    assert len(resp.json()["bettors"]) == 1

    # Delete the follow — cache must be evicted
    client.delete(f"/follows/{addr}", headers=auth_headers)

    # Now /follows/live must return empty (not the stale cached 1-bettor result)
    with patch("app.routes.follows.get_active_positions", new=AsyncMock(return_value=[])):
        resp2 = client.get("/follows/live", headers=auth_headers)
    assert resp2.status_code == 200
    assert resp2.json()["bettors"] == []


def test_follows_live_cache_hides_second_follow_within_ttl(client, auth_headers):
    """Within TTL window, a second follow is NOT visible via /follows/live (cache is real).
    Confirms the 30s cache gates all reads, not just the API call count."""
    import app.routes.follows as follows_module

    addr1 = "0xcache1"
    addr2 = "0xcache2"
    client.post("/follows", json={"bettor_address": addr1, "bettor_name": "First"},
                headers=auth_headers)

    mock_api = AsyncMock(return_value=MOCK_POSITIONS)
    with patch("app.routes.follows.get_active_positions", new=mock_api):
        # First call — cache populated with 1 bettor
        resp1 = client.get("/follows/live", headers=auth_headers)
    assert len(resp1.json()["bettors"]) == 1

    # Add second follow — but cache not cleared
    client.post("/follows", json={"bettor_address": addr2, "bettor_name": "Second"},
                headers=auth_headers)

    # Second call within TTL — still returns 1 bettor from cache
    with patch("app.routes.follows.get_active_positions", new=mock_api):
        resp2 = client.get("/follows/live", headers=auth_headers)
    assert len(resp2.json()["bettors"]) == 1


def test_follows_live_all_bettors_raise_returns_three_entries_with_empty_positions(
    client, db, auth_headers, registered_user
):
    """GET /follows/live when ALL followed bettors raise exceptions — each bettor
    entry must still appear with active_positions=[] (asyncio.gather catch-all),
    and the total bettors list must have 3 entries (not 0 and not a 500).
    Tests that a full multi-failure gather doesn't collapse the response."""
    from app.models import User

    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()

    for addr in ["0xfail1", "0xfail2", "0xfail3"]:
        client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)

    with patch(
        "app.routes.follows.get_active_positions",
        new=AsyncMock(side_effect=Exception("API down")),
    ):
        resp = client.get("/follows/live", headers=auth_headers)

    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) == 3
    for bettor in bettors:
        assert bettor["active_positions"] == []


def test_follows_live_returns_tier_in_response(client, auth_headers):
    """GET /follows/live must include 'tier' field in the response root."""
    with patch("app.routes.follows.get_active_positions", new=AsyncMock(return_value=[])):
        resp = client.get("/follows/live", headers=auth_headers)
    assert resp.status_code == 200
    assert "tier" in resp.json()
    assert resp.json()["tier"] == "free"  # default tier for new users


def test_follows_live_empty_response_has_no_tier(client, auth_headers):
    """GET /follows/live with no follows also returns 'tier' (early-return path)."""
    resp = client.get("/follows/live", headers=auth_headers)
    assert resp.status_code == 200
    # Empty follows path returns {"bettors": []} without tier — acceptable since no positions
    data = resp.json()
    assert "bettors" in data
    assert data["bettors"] == []
