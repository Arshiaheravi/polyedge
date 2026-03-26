"""Tests for /bettors endpoints — leaderboard and bettor detail (mocked)."""
from unittest.mock import AsyncMock, patch
import pytest


MOCK_LEADERBOARD = [
    {"rank": 1, "address": "0xaaa", "name": "beachboy", "volume_usd": 1000.0, "pnl_usd": 500.0, "avatar_url": ""},
    {"rank": 2, "address": "0xbbb", "name": "trader2",  "volume_usd": 800.0,  "pnl_usd": 200.0, "avatar_url": ""},
]


def test_leaderboard_public_no_auth(client):
    """Leaderboard must be accessible without authentication."""
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=MOCK_LEADERBOARD)):
        resp = client.get("/bettors?sort=profit&time_period=month&limit=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "bettors" in data
    assert len(data["bettors"]) == 2


def test_leaderboard_sort_profit(client):
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=MOCK_LEADERBOARD)) as mock:
        resp = client.get("/bettors?sort=profit&time_period=month")
    assert resp.status_code == 200
    mock.assert_called_once_with(sort_by="profit", time_period="month", limit=50)


def test_leaderboard_sort_volume(client):
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=MOCK_LEADERBOARD)) as mock:
        resp = client.get("/bettors?sort=volume&time_period=all")
    assert resp.status_code == 200
    mock.assert_called_once_with(sort_by="volume", time_period="all", limit=50)


def test_leaderboard_sort_accuracy(client):
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=MOCK_LEADERBOARD)) as mock:
        resp = client.get("/bettors?sort=accuracy&time_period=week")
    assert resp.status_code == 200
    mock.assert_called_once_with(sort_by="accuracy", time_period="week", limit=50)


def test_leaderboard_invalid_sort(client):
    # FastAPI str enum is advisory for docs — unknown sort falls back gracefully
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=[])):
        resp = client.get("/bettors?sort=invalid_sort")
    assert resp.status_code == 200


def test_leaderboard_invalid_period(client):
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=[])):
        resp = client.get("/bettors?time_period=quarterly")
    assert resp.status_code == 200


def test_leaderboard_limit_capped(client):
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=[])):
        resp = client.get("/bettors?limit=200")
    assert resp.status_code == 422  # > 100 not allowed


def test_recent_trades_public(client):
    mock_trades = [
        {"name": "Alice", "market": "Will X happen?", "outcome": "Yes",
         "amount_usd": 100.0, "side": "BUY", "timestamp": "2026-01-01", "market_slug": "x"}
    ]
    with patch("app.routes.bettors.get_live_trades", new=AsyncMock(return_value=mock_trades)):
        resp = client.get("/bettors/trades/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert "trades" in data
    assert data["trades"][0]["name"] == "Alice"


def test_leaderboard_api_error_returns_502(client):
    """When Polymarket API fails on leaderboard, route must return 502."""
    # Use time_period=day to avoid colliding with any cached profit_month_* entry
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(side_effect=Exception("API down"))):
        resp = client.get("/bettors?sort=profit&time_period=day")
    assert resp.status_code == 502
    assert "Polymarket" in resp.json()["detail"]


def test_recent_trades_limit_too_low_returns_422(client):
    """limit < 5 is below ge=5 constraint — FastAPI returns 422."""
    resp = client.get("/bettors/trades/recent?limit=4")
    assert resp.status_code == 422


def test_recent_trades_limit_too_high_returns_422(client):
    """limit > 50 is above le=50 constraint — FastAPI returns 422."""
    resp = client.get("/bettors/trades/recent?limit=51")
    assert resp.status_code == 422


def test_recent_trades_api_error_returns_502(client):
    """When Polymarket API fails on live trades, route must return 502."""
    import app.routes.bettors as bettors_mod
    # Clear the trades cache so we don't get a cached 200 from a prior test
    bettors_mod._trades_cache["data"] = None
    bettors_mod._trades_cache["ts"] = 0
    with patch("app.routes.bettors.get_live_trades", new=AsyncMock(side_effect=Exception("feed down"))):
        resp = client.get("/bettors/trades/recent")
    assert resp.status_code == 502
    assert "Polymarket" in resp.json()["detail"]


def test_bettor_detail_api_error_returns_502(client):
    """When Polymarket API fails on bettor detail, route must return 502."""
    import app.routes.bettors as bettors_mod
    bettors_mod._profile_cache.clear()
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(side_effect=Exception("profile down"))):
        resp = client.get("/bettors/0xBAD")
    assert resp.status_code == 502
    assert "Polymarket" in resp.json()["detail"]


def test_bettor_detail_public(client):
    mock_profile = {"address": "0xaaa", "name": "beachboy", "volume_usd": 1000.0, "total_bets": 10, "avg_bet_usd": 100.0, "avatar_url": ""}
    mock_bets = []
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=mock_bets)):
        resp = client.get("/bettors/0xaaa")
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["name"] == "beachboy"


def test_leaderboard_response_includes_cached_field(client):
    """GET /bettors response always includes a 'cached' boolean field."""
    import app.routes.bettors as bettors_mod
    # Use a unique combo (volume_week_20) to guarantee uncached first call
    bettors_mod._leaderboard_cache.pop("volume_week_20", None)
    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=MOCK_LEADERBOARD)):
        resp = client.get("/bettors?sort=volume&time_period=week&limit=20")
    assert resp.status_code == 200
    data = resp.json()
    assert "cached" in data
    assert isinstance(data["cached"], bool)
    assert data["cached"] is False  # First call to this combo — not cached


def test_recent_trades_cached_field_is_true_on_second_call(client):
    """Second call to GET /bettors/trades/recent within TTL returns cached=True."""
    import app.routes.bettors as bettors_mod
    # Clear the trades cache so first call is guaranteed fresh
    bettors_mod._trades_cache["data"] = None
    bettors_mod._trades_cache["ts"] = 0
    mock_trades = [
        {"name": "Alice", "market": "Will X happen?", "outcome": "Yes",
         "amount_usd": 100.0, "side": "BUY", "timestamp": "2026-01-01", "market_slug": "x"}
    ]
    mock_fn = AsyncMock(return_value=mock_trades)
    with patch("app.routes.bettors.get_live_trades", new=mock_fn):
        resp1 = client.get("/bettors/trades/recent")
        resp2 = client.get("/bettors/trades/recent")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["cached"] is False   # First call — live
    assert resp2.json()["cached"] is True    # Second call — from cache
    assert mock_fn.call_count == 1           # API called only once


def test_leaderboard_cached_field_is_true_on_second_call(client):
    """Second leaderboard call with the same params within TTL returns cached=True."""
    import app.routes.bettors as bettors_mod
    # Clear the specific cache key so the first call is guaranteed fresh
    bettors_mod._leaderboard_cache.pop("profit_all_7", None)
    mock_lb = AsyncMock(return_value=MOCK_LEADERBOARD)
    with patch("app.routes.bettors.get_leaderboard", new=mock_lb):
        resp1 = client.get("/bettors?sort=profit&time_period=all&limit=7")
        resp2 = client.get("/bettors?sort=profit&time_period=all&limit=7")
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["cached"] is False  # First call — live
    assert resp2.json()["cached"] is True   # Second call — served from cache
    assert mock_lb.call_count == 1          # API called only once


def test_leaderboard_limit_zero_returns_422(client):
    """limit=0 is below ge=1 constraint — FastAPI returns 422."""
    resp = client.get("/bettors?limit=0")
    assert resp.status_code == 422


def test_bettor_detail_response_shape_has_required_keys(client):
    """GET /bettors/{address} always returns both 'profile' and 'recent_bets' keys."""
    import app.routes.bettors as bettors_mod
    addr = "0xSHAPE_CHECK"
    bettors_mod._profile_cache.pop(addr, None)
    mock_profile = {"address": addr, "name": "ShapeChecker", "volume_usd": 100.0,
                    "total_bets": 1, "avg_bet_usd": 100.0, "avatar_url": ""}
    mock_bets = [{"market_id": "m1", "outcome": "Yes", "amount_usd": 50.0, "timestamp": "2026-01-01"}]
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=mock_bets)):
        resp = client.get(f"/bettors/{addr}")
    assert resp.status_code == 200
    data = resp.json()
    assert "profile" in data, "bettor detail must always include 'profile' key"
    assert "recent_bets" in data, "bettor detail must always include 'recent_bets' key"
    assert isinstance(data["recent_bets"], list)


def test_bettor_detail_cache_hit_returns_cached_data(client):
    """Second call to GET /bettors/{address} within TTL returns cached data without re-calling API."""
    import app.routes.bettors as bettors_mod
    addr = "0xCACHEHIT"
    bettors_mod._profile_cache.pop(addr, None)

    mock_profile = {"address": addr, "name": "CacheHitter", "volume_usd": 500.0,
                    "total_bets": 5, "avg_bet_usd": 100.0, "avatar_url": ""}
    mock_fn = AsyncMock(return_value=mock_profile)

    with patch("app.routes.bettors.get_bettor_profile", new=mock_fn), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=[])):
        resp1 = client.get(f"/bettors/{addr}")

    # Second call — no mock active; should be served from _profile_cache
    resp2 = client.get(f"/bettors/{addr}")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["profile"]["name"] == "CacheHitter"
    assert resp2.json()["profile"]["name"] == "CacheHitter"
    assert mock_fn.call_count == 1  # API called only once


def test_bettor_detail_none_profile_returns_200(client):
    """GET /bettors/{address} returns 200 with profile=null when Polymarket returns None.
    PROJECT.md spec says 'bad address = 404 or empty' — actual behavior is empty (null profile)."""
    import app.routes.bettors as bettors_mod
    addr = "0xNONEXISTENT"
    bettors_mod._profile_cache.pop(addr, None)

    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=None)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=[])):
        resp = client.get(f"/bettors/{addr}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"] is None
    assert data["recent_bets"] == []


def test_leaderboard_limit_param_passed_to_service(client):
    """GET /bettors?limit=5 must call get_leaderboard with limit=5."""
    import app.routes.bettors as bettors_mod
    bettors_mod._leaderboard_cache.pop("profit_month_5", None)

    mock_fn = AsyncMock(return_value=MOCK_LEADERBOARD[:1])
    with patch("app.routes.bettors.get_leaderboard", new=mock_fn):
        resp = client.get("/bettors?sort=profit&time_period=month&limit=5")

    assert resp.status_code == 200
    mock_fn.assert_called_once()
    call_kwargs = mock_fn.call_args.kwargs
    assert call_kwargs.get("limit") == 5, f"expected limit=5 but got {call_kwargs}"


def test_bettor_detail_profile_includes_rank_and_pnl_usd(client):
    """GET /bettors/{address} profile must include rank and pnl_usd fields (added session 112)."""
    import app.routes.bettors as bettors_mod
    addr = "0xRANK_CHECK"
    bettors_mod._profile_cache.pop(addr, None)
    mock_profile = {
        "address": addr, "name": "RankTrader",
        "rank": 7, "pnl_usd": 1234.56,
        "volume_usd": 5000.0, "total_bets": 20, "avg_bet_usd": 250.0, "avatar_url": "",
    }
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=[])):
        resp = client.get(f"/bettors/{addr}")
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert "rank" in profile, "profile must contain 'rank' field"
    assert "pnl_usd" in profile, "profile must contain 'pnl_usd' field"
    assert profile["rank"] == 7
    assert profile["pnl_usd"] == 1234.56


def test_bettor_detail_recent_bets_have_outcome_and_price(client):
    """GET /bettors/{address} recent_bets must include outcome and price for each bet."""
    import app.routes.bettors as bettors_mod
    addr = "0xBET_OUTCOME"
    bettors_mod._profile_cache.pop(addr, None)
    mock_profile = {"address": addr, "name": "BetOutcomeTrader", "rank": 0, "pnl_usd": 0.0,
                    "volume_usd": 100.0, "total_bets": 1, "avg_bet_usd": 100.0, "avatar_url": ""}
    mock_bets = [
        {"market_id": "m1", "market_question": "Will it rain?",
         "outcome": "Yes", "price": 0.65,
         "amount_usd": 100.0, "timestamp": "2026-03-01", "type": "BUY", "tx_hash": "", "market_icon": "", "market_slug": ""},
    ]
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=mock_bets)):
        resp = client.get(f"/bettors/{addr}")
    assert resp.status_code == 200
    bets = resp.json()["recent_bets"]
    assert len(bets) == 1
    assert bets[0]["outcome"] == "Yes"
    assert bets[0]["price"] == 0.65


def test_bettor_detail_redeem_bets_not_in_response(client):
    """GET /bettors/{address} must not include REDEEM-type bets in recent_bets."""
    import app.routes.bettors as bettors_mod
    addr = "0xNO_REDEEM"
    bettors_mod._profile_cache.pop(addr, None)
    mock_profile = {"address": addr, "name": "NoRedeemTrader", "rank": 0, "pnl_usd": 0.0,
                    "volume_usd": 100.0, "total_bets": 1, "avg_bet_usd": 100.0, "avatar_url": ""}
    # Service layer already filters REDEEM — this confirms the route passes through only TRADE bets
    mock_bets = [
        {"market_id": "t1", "market_question": "Trade Q", "outcome": "No",
         "price": 0.45, "amount_usd": 50.0, "timestamp": "2026-03-01",
         "type": "BUY", "tx_hash": "", "market_icon": "", "market_slug": ""},
    ]
    mock_sim = {"simulated_pnl_usd": -100.0, "simulated_roi_pct": -100.0, "bets_analysed": 1}
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=mock_bets)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=mock_sim)):
        resp = client.get(f"/bettors/{addr}")
    assert resp.status_code == 200
    bets = resp.json()["recent_bets"]
    assert all(b["outcome"] != "" for b in bets), "all returned bets must have an outcome (REDEEM filtered)"


# ── copy_simulator tier gate ───────────────────────────────────────────────────

MOCK_PROFILE_SIM = {"address": "0xSIM", "name": "SimTrader", "rank": 1, "pnl_usd": 500.0,
                    "volume_usd": 1000.0, "total_bets": 10, "avg_bet_usd": 100.0, "avatar_url": ""}
MOCK_BETS_SIM = []
MOCK_SIM_RESULT = {"simulated_pnl_usd": 347.5, "simulated_roi_pct": 34.75, "bets_analysed": 10}


def test_bettor_detail_free_user_copy_simulator_locked(client, auth_headers):
    """Free user (no subscription) sees copy_simulator.locked=True."""
    import app.routes.bettors as bettors_mod
    addr = "0xFREE_SIM"
    bettors_mod._profile_cache.pop(addr, None)
    # auth_headers fixture is a free-tier user by default
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        resp = client.get(f"/bettors/{addr}", headers=auth_headers)
    assert resp.status_code == 200
    sim = resp.json().get("copy_simulator", {})
    assert sim.get("locked") is True, "free user must see locked=True in copy_simulator"
    assert "simulated_pnl_usd" not in sim


def test_bettor_detail_unauthenticated_copy_simulator_locked(client):
    """Unauthenticated request (no token) → copy_simulator.locked=True."""
    import app.routes.bettors as bettors_mod
    addr = "0xANON_SIM"
    bettors_mod._profile_cache.pop(addr, None)
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        resp = client.get(f"/bettors/{addr}")
    assert resp.status_code == 200
    assert resp.json()["copy_simulator"]["locked"] is True


def test_bettor_detail_basic_user_copy_simulator_unlocked(client, db):
    """Basic-tier user sees full copy_simulator data (not locked)."""
    import app.routes.bettors as bettors_mod
    from app.models import User
    from app.auth import hash_password, create_access_token
    addr = "0xBASIC_SIM"
    bettors_mod._profile_cache.pop(addr, None)
    # Create a basic-tier user
    user = User(email="basic_sim@test.com", hashed_password=hash_password("pw"),
                name="BasicSimUser", subscription_tier="basic")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "tier": "basic"})
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        resp = client.get(f"/bettors/{addr}", headers=headers)
    assert resp.status_code == 200
    sim = resp.json()["copy_simulator"]
    assert "locked" not in sim
    assert sim["simulated_pnl_usd"] == pytest.approx(347.5, rel=0.01)
    assert sim["bets_analysed"] == 10


def test_bettor_detail_vip_user_copy_simulator_unlocked(client, db):
    """VIP-tier user sees full copy_simulator data (not locked)."""
    import app.routes.bettors as bettors_mod
    from app.models import User
    from app.auth import hash_password, create_access_token
    addr = "0xVIP_SIM"
    bettors_mod._profile_cache.pop(addr, None)
    user = User(email="vip_sim@test.com", hashed_password=hash_password("pw"),
                name="VipSimUser", subscription_tier="vip")
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "tier": "vip"})
    headers = {"Authorization": f"Bearer {token}"}
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        resp = client.get(f"/bettors/{addr}", headers=headers)
    assert resp.status_code == 200
    sim = resp.json()["copy_simulator"]
    assert "locked" not in sim
    assert sim["simulated_roi_pct"] == pytest.approx(34.75, rel=0.01)


def test_profile_cache_tier_gate_not_bypassed(client, db):
    """VIP fetches an address → free user fetching the SAME address must still see locked=True.

    This is Bug #1 regression: the old cache was keyed by address only. A VIP response cached
    for address X would be served to a free user requesting the same address — paywall bypass.
    Fix: cache key is now (address, tier) so each tier gets its own cache entry.
    """
    import app.routes.bettors as bettors_mod
    from app.models import User
    from app.auth import hash_password, create_access_token

    addr = "0xCACHE_TIER_GATE"
    # Clear ALL tier-keyed entries for this address
    for tier in ("free", "basic", "vip"):
        bettors_mod._profile_cache.pop((addr, tier), None)

    # Create a VIP user
    vip_user = User(email="vip_tier_gate@test.com", hashed_password=hash_password("pw"),
                    name="VipGateUser", subscription_tier="vip")
    db.add(vip_user)
    db.commit()
    db.refresh(vip_user)
    vip_token = create_access_token({"sub": str(vip_user.id)})
    vip_headers = {"Authorization": f"Bearer {vip_token}"}

    # VIP fetches the profile first — populates cache with unlocked simulator
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        vip_resp = client.get(f"/bettors/{addr}", headers=vip_headers)
    assert vip_resp.status_code == 200
    assert vip_resp.json()["copy_simulator"].get("locked") is not True, "VIP should see unlocked simulator"

    # Free user (auth_headers is free tier) fetches the SAME address
    # Must get their own cache entry (locked=True), NOT the VIP entry
    free_user = User(email="free_tier_gate@test.com", hashed_password=hash_password("pw"),
                     name="FreeGateUser", subscription_tier="free")
    db.add(free_user)
    db.commit()
    db.refresh(free_user)
    free_token = create_access_token({"sub": str(free_user.id)})
    free_headers = {"Authorization": f"Bearer {free_token}"}

    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        free_resp = client.get(f"/bettors/{addr}", headers=free_headers)
    assert free_resp.status_code == 200
    assert free_resp.json()["copy_simulator"].get("locked") is True, (
        "Free user must see locked=True even after VIP cached the same address — "
        "cache key must include tier to prevent paywall bypass (Bug #1 regression)"
    )


def test_profile_cache_free_first_then_vip_gets_unlocked(client, db):
    """Free user fetches first (caches locked entry) → VIP fetches same address → locked=False.

    Reverse-order complement to test_profile_cache_tier_gate_not_bypassed.
    Confirms the (address, tier) cache key works in BOTH directions:
    - VIP must not see a stale locked entry from a prior free-user fetch.
    """
    import app.routes.bettors as bettors_mod
    from app.models import User
    from app.auth import hash_password, create_access_token

    addr = "0xCACHE_FREE_FIRST"
    for tier in ("free", "basic", "vip"):
        bettors_mod._profile_cache.pop((addr, tier), None)

    # Free user fetches first — populates cache with locked entry
    free_user = User(email="free_ff@test.com", hashed_password=hash_password("pw"),
                     name="FreeFFirst", subscription_tier="free")
    db.add(free_user)
    db.commit()
    db.refresh(free_user)
    free_token = create_access_token({"sub": str(free_user.id)})
    free_headers = {"Authorization": f"Bearer {free_token}"}

    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        free_resp = client.get(f"/bettors/{addr}", headers=free_headers)
    assert free_resp.status_code == 200
    assert free_resp.json()["copy_simulator"].get("locked") is True, "Free user should see locked=True"

    # VIP user fetches the SAME address — must get their own unlocked entry
    vip_user = User(email="vip_ff@test.com", hashed_password=hash_password("pw"),
                    name="VipFFirst", subscription_tier="vip")
    db.add(vip_user)
    db.commit()
    db.refresh(vip_user)
    vip_token = create_access_token({"sub": str(vip_user.id)})
    vip_headers = {"Authorization": f"Bearer {vip_token}"}

    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=MOCK_PROFILE_SIM)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=MOCK_BETS_SIM)), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=MOCK_SIM_RESULT)):
        vip_resp = client.get(f"/bettors/{addr}", headers=vip_headers)
    assert vip_resp.status_code == 200
    assert vip_resp.json()["copy_simulator"].get("locked") is not True, (
        "VIP user must see locked=False even after free user cached the same address — "
        "cache key must include tier (Bug #1 reverse-order regression)"
    )


# ── Polymarket HTTP 500 resilience (httpx transport level) ────────────────────


def test_leaderboard_polymarket_http500_returns_200_empty_list(client):
    """When Polymarket returns HTTP 500, get_leaderboard swallows it and returns [].
    The route must return 200 with an empty bettors list — not propagate the 500.

    This tests the service layer's resilience at the httpx level, not just the
    route-level try/except (which is covered by test_leaderboard_api_error_returns_502).
    """
    import httpx
    from unittest.mock import MagicMock

    import app.routes.bettors as bettors_mod
    # Use a unique cache key so this test doesn't collide with cached results
    bettors_mod._leaderboard_cache.pop("profit_all_3", None)

    # Build a mock that simulates Polymarket returning HTTP 500
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error",
        request=MagicMock(),
        response=mock_resp,
    )

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_resp)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_cm):
        resp = client.get("/bettors?sort=profit&time_period=all&limit=3")

    assert resp.status_code == 200, (
        f"Route must return 200 (graceful) when Polymarket is down, got {resp.status_code}"
    )
    data = resp.json()
    assert "bettors" in data
    assert data["bettors"] == [], (
        "Service swallows upstream 500 — route must return empty list, not propagate the error"
    )


def test_bettor_detail_polymarket_http500_returns_200_empty_profile(client):
    """When Polymarket returns HTTP 500 for activity/profile, service returns empty data.
    Route must return 200 with a fallback profile — not propagate the upstream 500.
    """
    import httpx
    from unittest.mock import MagicMock

    import app.routes.bettors as bettors_mod
    addr = "0xHTTP500TEST"
    for tier in ("free", "basic", "vip"):
        bettors_mod._profile_cache.pop((addr, tier), None)

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error",
        request=MagicMock(),
        response=mock_resp,
    )

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_resp)

    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_cm):
        resp = client.get(f"/bettors/{addr}")

    assert resp.status_code == 200, (
        f"Route must not propagate Polymarket 500 to callers, got {resp.status_code}"
    )
    data = resp.json()
    assert "profile" in data
    assert "recent_bets" in data


# ── Concurrent requests ───────────────────────────────────────────────────────


def test_concurrent_leaderboard_requests_all_succeed(client):
    """10 threads firing GET /bettors simultaneously must all return 200.

    Verifies the module-level _leaderboard_cache dict and async service layer
    handle concurrent access without crashing or returning errors.
    Unauthenticated GET /bettors does not touch the DB — safe to share one client.
    """
    import threading

    import app.routes.bettors as bettors_mod
    # Use a unique cache key so this test's concurrent writes don't collide with others
    bettors_mod._leaderboard_cache.pop("volume_day_4", None)

    mock_data = [
        {"rank": 1, "address": "0xaaa", "name": "whale1", "volume_usd": 1000.0,
         "pnl_usd": 500.0, "avatar_url": "", "accuracy": 0.65},
    ]

    results: list[int] = []
    errors: list[str] = []
    lock = threading.Lock()

    def make_request():
        try:
            resp = client.get("/bettors?sort=volume&time_period=day&limit=4")
            with lock:
                results.append(resp.status_code)
        except Exception as exc:
            with lock:
                errors.append(str(exc))

    with patch("app.routes.bettors.get_leaderboard", new=AsyncMock(return_value=mock_data)):
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

    assert len(errors) == 0, f"Concurrent requests raised exceptions: {errors}"
    assert len(results) == 10, f"Not all 10 threads completed — got {len(results)} results"
    assert all(s == 200 for s in results), f"Not all 200: {results}"


def test_bettor_detail_profile_includes_accuracy(client):
    """GET /bettors/{address} profile must include 'accuracy' field (added session 176)."""
    import app.routes.bettors as bettors_mod
    addr = "0xACCURACY_CHECK"
    bettors_mod._profile_cache.pop((addr, "free"), None)
    mock_profile = {
        "address": addr, "name": "AccuracyTrader",
        "rank": 3, "pnl_usd": 500.0, "accuracy": 0.72,
        "volume_usd": 2000.0, "total_bets": 10, "avg_bet_usd": 200.0, "avatar_url": "",
    }
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=[])), \
         patch("app.routes.bettors.compute_copy_simulator", new=AsyncMock(return_value=None)):
        resp = client.get(f"/bettors/{addr}")
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert "accuracy" in profile, "profile must contain 'accuracy' field (added session 176)"
    assert profile["accuracy"] == pytest.approx(0.72)


def test_auth_me_does_not_contain_accuracy(client, auth_headers):
    """GET /auth/me is user data — it must NOT contain an 'accuracy' field (bettor metric, not user)."""
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "accuracy" not in data, (
        "GET /auth/me must not expose 'accuracy' — that is a bettor-profile metric, not user account data"
    )
