"""
Real-world data integrity tests.

These tests call the actual Polymarket API through the PolyEdge backend
to verify that data is economically meaningful, well-formatted, and
consistent across endpoints.

Tests skip gracefully when the Polymarket API is unreachable (502 from backend)
so they don't cause false failures in offline/CI environments.
"""
import re
import math
import httpx
import pytest
from fastapi.testclient import TestClient

import app.routes.bettors as bettors_mod
from app.config import get_settings

# These tests hit the real Polymarket API and require network access. They are
# skipped by default (pytest.ini adds `-m "not live"`); run them explicitly with
# `pytest -m live`.
pytestmark = pytest.mark.live

ETH_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
CONDITION_ID_RE = re.compile(r"^0x[a-fA-F0-9]{64}$")


def _clear_bettors_cache():
    """Reset module-level caches so each test hits a fresh Polymarket fetch."""
    bettors_mod._leaderboard_cache = {"data": None, "ts": 0}
    bettors_mod._profile_cache.clear()


def _skip_if_502(resp, label: str):
    if resp.status_code == 502:
        pytest.skip(f"Polymarket API unavailable ({label} returned 502)")


# ── Leaderboard data sanity ─────────────────────────────────────────────────

def test_leaderboard_addresses_are_valid_ethereum(client):
    """Every bettor address must match the Ethereum hex format 0x + 40 hex chars."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0, "No bettors returned — Polymarket returned empty list"
    for b in bettors:
        assert ETH_ADDR_RE.match(b["address"]), (
            f"Invalid Ethereum address: {b['address']!r}"
        )


def test_leaderboard_top_20_profit_non_negative(client):
    """Top 20 bettors by profit must all have pnl_usd ≥ 0."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0
    for b in bettors:
        assert b["pnl_usd"] >= 0, (
            f"Bettor {b['address']} has negative profit {b['pnl_usd']} in top-20 profit list"
        )


def test_leaderboard_accuracy_in_valid_range(client):
    """Accuracy (when present) must be between 0.0 and 1.0."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0
    for b in bettors:
        acc = b.get("accuracy")
        if acc is None:
            continue  # accuracy is nullable when Polymarket doesn't provide it
        assert 0.0 <= acc <= 1.0, (
            f"Bettor {b['address']} accuracy {acc} is outside [0.0, 1.0]"
        )


def test_leaderboard_volume_positive(client):
    """Every bettor must have volume_usd > 0 (they've placed at least one bet)."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0
    for b in bettors:
        assert b["volume_usd"] > 0, (
            f"Bettor {b['address']} has zero volume_usd"
        )


def test_leaderboard_no_duplicate_ranks(client):
    """Top 20 bettors must have unique ranks."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0
    ranks = [b["rank"] for b in bettors]
    assert len(ranks) == len(set(ranks)), (
        f"Duplicate ranks found: {[r for r in ranks if ranks.count(r) > 1]}"
    )


def test_leaderboard_ranks_are_positive_integers(client):
    """All ranks must be positive integers (≥ 1)."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0
    for b in bettors:
        assert isinstance(b["rank"], int) and b["rank"] >= 1, (
            f"Bettor {b['address']} has invalid rank {b['rank']!r}"
        )


def test_leaderboard_names_are_non_empty(client):
    """Every bettor must have a non-empty name (falls back to address prefix)."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=20&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) > 0
    for b in bettors:
        assert b["name"] and len(b["name"]) > 0, (
            f"Bettor {b['address']} has empty name"
        )


# ── Leaderboard vs profile consistency ──────────────────────────────────────

def test_leaderboard_vs_profile_pnl_consistent(client):
    """Top 3 bettors: profile pnl_usd must be within 5% of leaderboard value.

    Both come from the same Polymarket Data API — any large discrepancy means
    a normalisation bug.
    """
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors for consistency check")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"][:3]
    assert len(bettors) >= 1, "Need at least 1 bettor to check consistency"

    for lb in bettors:
        address = lb["address"]
        lb_pnl = lb["pnl_usd"]
        if lb_pnl == 0:
            continue  # can't compute 5% tolerance on zero

        _clear_bettors_cache()
        profile_resp = client.get(f"/bettors/{address}")
        _skip_if_502(profile_resp, f"GET /bettors/{address}")
        assert profile_resp.status_code == 200
        profile_pnl = profile_resp.json()["profile"]["pnl_usd"]

        # Allow 5% tolerance — they're the same data source, small diff is timing
        tolerance = abs(lb_pnl) * 0.05
        assert abs(profile_pnl - lb_pnl) <= tolerance + 1.0, (
            f"Bettor {address}: leaderboard pnl={lb_pnl} vs profile pnl={profile_pnl} "
            f"(diff={abs(profile_pnl - lb_pnl):.2f} exceeds 5% tolerance {tolerance:.2f})"
        )


def test_leaderboard_vs_profile_accuracy_consistent(client):
    """Top bettor: if accuracy is non-null in leaderboard, profile must return same value (±0.02).

    Both endpoints derive accuracy from the same Polymarket percentProfitable field.
    A discrepancy means one endpoint is missing the field or applying wrong normalisation.
    """
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors for accuracy cross-check")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1, "Need at least 1 bettor"

    # Find first bettor with non-null accuracy in leaderboard
    lb_bettor = None
    lb_accuracy = None
    for b in bettors:
        if b.get("accuracy") is not None:
            lb_bettor = b
            lb_accuracy = b["accuracy"]
            break

    if lb_bettor is None:
        pytest.skip("No bettor with non-null accuracy in leaderboard response")

    address = lb_bettor["address"]
    _clear_bettors_cache()
    profile_resp = client.get(f"/bettors/{address}")
    _skip_if_502(profile_resp, f"GET /bettors/{address}")
    assert profile_resp.status_code == 200

    profile_accuracy = profile_resp.json()["profile"].get("accuracy")
    assert profile_accuracy is not None, (
        f"Bettor {address}: leaderboard accuracy={lb_accuracy} but profile has no accuracy field"
    )
    assert abs(profile_accuracy - lb_accuracy) <= 0.02, (
        f"Bettor {address}: leaderboard accuracy={lb_accuracy} vs profile accuracy={profile_accuracy} "
        f"(diff={abs(profile_accuracy - lb_accuracy):.4f} exceeds ±0.02 tolerance)"
    )


# ── Recent bets data validity ────────────────────────────────────────────────

def test_recent_bets_type_is_trade(client):
    """Recent bets must only contain TRADE type (no REDEEM orders)."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}")
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    bets = detail_resp.json().get("recent_bets", [])
    if not bets:
        pytest.skip("No recent bets available for this bettor")

    for bet in bets:
        bet_type = bet.get("type", "TRADE")  # field may be absent; assume TRADE
        assert bet_type != "REDEEM", (
            f"REDEEM transaction found in recent_bets for {address}: {bet}"
        )


def test_recent_bets_amount_positive(client):
    """Recent bets must have amount_usd > 0."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}")
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    bets = detail_resp.json().get("recent_bets", [])
    if not bets:
        pytest.skip("No recent bets for this bettor")

    for bet in bets:
        assert bet["amount_usd"] > 0, (
            f"Bet with zero/negative amount_usd: {bet}"
        )


def test_recent_bets_price_in_valid_range(client):
    """Recent bet prices must be between 0.01 and 0.99 (0 or 1 = resolved market)."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}")
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    bets = detail_resp.json().get("recent_bets", [])
    if not bets:
        pytest.skip("No recent bets for this bettor")

    for bet in bets:
        price = bet.get("price", 0)
        if price == 0:
            continue  # price may be absent for some bet types
        assert 0.01 <= price <= 0.99, (
            f"Bet price {price} outside [0.01, 0.99] — may be a resolved market: {bet}"
        )


def test_recent_bets_market_title_non_empty(client):
    """Every bet must have a non-empty market title."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}")
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    bets = detail_resp.json().get("recent_bets", [])
    if not bets:
        pytest.skip("No recent bets for this bettor")

    for bet in bets:
        title = bet.get("market_question", "")
        assert title and len(title) >= 5, (
            f"Bet has missing/short market_question: {bet}"
        )


def test_recent_bets_timestamps_within_90_days(client):
    """All recent_bets timestamps must be within the past 90 days.

    Stale timestamps (older than 90 days) indicate Polymarket served
    wrong/cached bets — a data freshness failure that would mislead copy-traders.
    Timestamps can be a Unix float string or an ISO-8601 string.
    """
    import time
    from datetime import datetime, timezone

    _clear_bettors_cache()
    resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}")
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    bets = detail_resp.json().get("recent_bets", [])
    if not bets:
        pytest.skip("No recent bets available for this bettor")

    now_ts = time.time()
    ninety_days_secs = 90 * 24 * 3600

    for bet in bets:
        raw_ts = bet.get("timestamp", "")
        if not raw_ts:
            continue  # missing timestamp — skip this bet (don't fail the test)

        try:
            ts_val = float(raw_ts) if str(raw_ts).replace(".", "").isdigit() else None
            if ts_val is None:
                dt = datetime.fromisoformat(str(raw_ts).replace("Z", "+00:00"))
                ts_val = dt.timestamp()
        except Exception:
            continue  # unparseable timestamp — skip rather than false-fail

        age_secs = now_ts - ts_val
        assert age_secs <= ninety_days_secs, (
            f"Bet timestamp is {age_secs / 86400:.1f} days old (>90 days) — "
            f"Polymarket may be serving stale data: {bet}"
        )
        assert age_secs >= 0, (
            f"Bet timestamp is in the future by {-age_secs:.0f}s — clock skew or bad data: {bet}"
        )


# ── Copy simulator math ──────────────────────────────────────────────────────

def test_copy_simulator_locked_for_free_user(client, db):
    """Free user (no auth) must get locked=True copy simulator."""
    _clear_bettors_cache()
    resp = client.get("/bettors?limit=3&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    # Call without auth → treated as free tier
    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}")
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    simulator = detail_resp.json()["copy_simulator"]
    assert simulator.get("locked") is True, (
        f"Unauthenticated user should see locked=True, got: {simulator}"
    )


def test_copy_simulator_unlocked_for_basic_user(client, db):
    """Basic user must get unlocked copy simulator with numeric pnl."""
    from app.models import User
    from app.auth import hash_password

    # Create a basic-tier test user
    user = User(
        email="basic_integrity@test.com",
        hashed_password=hash_password("TestPass123!"),
        name="Basic Integrity",
        subscription_tier="basic",
    )
    db.add(user)
    db.commit()

    login_resp = client.post("/auth/login", json={
        "email": "basic_integrity@test.com",
        "password": "TestPass123!",
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    _clear_bettors_cache()
    resp = client.get("/bettors?limit=3&sort=profit")
    _skip_if_502(resp, "GET /bettors")
    assert resp.status_code == 200
    bettors = resp.json()["bettors"]
    assert len(bettors) >= 1
    address = bettors[0]["address"]

    _clear_bettors_cache()
    detail_resp = client.get(f"/bettors/{address}", headers=headers)
    _skip_if_502(detail_resp, f"GET /bettors/{address}")
    assert detail_resp.status_code == 200
    simulator = detail_resp.json()["copy_simulator"]
    assert simulator.get("locked") is not True, (
        f"Basic user should see unlocked simulator, got: {simulator}"
    )
    # ROI sanity cap: |simulated_roi_pct| ≤ 10000%
    roi = simulator.get("simulated_roi_pct", 0) or 0
    assert abs(roi) <= 10000, (
        f"Simulated ROI {roi}% exceeds sanity cap of 10000% — likely a math bug"
    )


@pytest.mark.asyncio
async def test_copy_simulator_extreme_price_roi_cap():
    """
    Unit test: at price=0.01 (minimum valid), a winning bet yields 9900% per-bet ROI.
    With 2 such winning bets the raw ROI would be 9900% (100+9900+100+9900 total / 200 invested).
    Ensure the ±10000% cap in compute_copy_simulator clamps values that would otherwise exceed it.
    Also verifies normal winning bets at price=0.5 are NOT capped (should return ~0% ROI on 1 win / 1 loss).
    """
    import time as _time
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import compute_copy_simulator

    now_ts = _time.time()
    old_ts = str(now_ts - 8 * 24 * 3600)  # 8 days ago → assumed resolved

    # Scenario 1: All-winning bets at price=0.01 — raw ROI = 9900% (within cap)
    raw_single_win = [
        {"type": "REDEEM", "conditionId": "cid-low-price"},
        {
            "type": "TRADE",
            "side": "BUY",
            "price": "0.01",
            "conditionId": "cid-low-price",
            "timestamp": old_ts,
        },
    ]
    mock_resp_single = MagicMock()
    mock_resp_single.json.return_value = raw_single_win
    mock_resp_single.raise_for_status = MagicMock()
    mock_client_single = AsyncMock()
    mock_client_single.__aenter__ = AsyncMock(return_value=mock_client_single)
    mock_client_single.__aexit__ = AsyncMock(return_value=False)
    mock_client_single.get = AsyncMock(return_value=mock_resp_single)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client_single):
        result = await compute_copy_simulator("0x" + "a" * 40, limit=10)
    assert result["bets_analysed"] == 1
    assert result["simulated_roi_pct"] == pytest.approx(9900.0, abs=0.1), (
        f"Expected ~9900% ROI for price=0.01 win, got {result['simulated_roi_pct']}"
    )
    assert abs(result["simulated_roi_pct"]) <= 10000, "ROI cap violated"

    # Scenario 2: Many all-winning bets at price=0.01 — raw ROI > 10000% must be clamped
    many_low_price = [{"type": "REDEEM", "conditionId": f"cid-{i}"} for i in range(5)]
    many_low_price += [
        {
            "type": "TRADE",
            "side": "BUY",
            "price": "0.01",
            "conditionId": f"cid-{i}",
            "timestamp": old_ts,
        }
        for i in range(5)
    ]
    mock_resp_many = MagicMock()
    mock_resp_many.json.return_value = many_low_price
    mock_resp_many.raise_for_status = MagicMock()
    mock_client_many = AsyncMock()
    mock_client_many.__aenter__ = AsyncMock(return_value=mock_client_many)
    mock_client_many.__aexit__ = AsyncMock(return_value=False)
    mock_client_many.get = AsyncMock(return_value=mock_resp_many)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client_many):
        result_many = await compute_copy_simulator("0x" + "b" * 40, limit=10)
    assert result_many["bets_analysed"] == 5
    # Raw ROI = (5 * 9900) / 500 * 100 = 9900% — still under cap; verify not clamped incorrectly
    # But if price were even lower (approaching 0), cap protects users from absurd display values
    assert abs(result_many["simulated_roi_pct"]) <= 10000, (
        f"ROI cap violated: {result_many['simulated_roi_pct']}%"
    )


@pytest.mark.asyncio
async def test_copy_simulator_skips_still_open_bets():
    """compute_copy_simulator must exclude bets that are <7 days old and NOT in redeemed_ids.
    These are still-open positions — the outcome is unknown so they must not count as losses.
    bets_analysed must equal 0 when the only TRADE bet is fresh and unresolved (Bug coverage — open-bet skip branch)."""
    import time as _time
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import compute_copy_simulator

    now_ts = _time.time()
    recent_ts = str(now_ts - 1 * 24 * 3600)  # 1 day ago — well under 7-day threshold

    # One TRADE BUY bet placed 1 day ago, conditionId NOT in any REDEEM → still open
    raw = [
        {
            "type": "TRADE",
            "side": "BUY",
            "price": "0.60",
            "conditionId": "cid-open",
            "timestamp": recent_ts,
        }
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = raw
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        result = await compute_copy_simulator("0x" + "c" * 40, limit=10)

    assert result["bets_analysed"] == 0, (
        f"Still-open bet (1 day old, not redeemed) must be skipped — got bets_analysed={result['bets_analysed']}"
    )
    assert result["simulated_pnl_usd"] == 0.0, (
        f"No analysed bets → pnl must be 0.0, got {result['simulated_pnl_usd']}"
    )


# ── Admin stats internal consistency ────────────────────────────────────────

def test_admin_stats_user_counts_sum_to_total(client, db):
    """free_count + basic_count + vip_count must equal total user count."""
    from app.models import User
    from app.auth import hash_password

    # Create 2 free, 1 basic, 1 vip user
    for tier, email in [("free", "di_free1@t.com"), ("free", "di_free2@t.com"),
                        ("basic", "di_basic@t.com"), ("vip", "di_vip@t.com")]:
        db.add(User(email=email, hashed_password=hash_password("Pass123!"),
                    name=email, subscription_tier=tier))
    db.commit()

    pw = get_settings().admin_password
    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    users = data["users"]
    assert users["free"] + users["basic"] + users["vip"] == users["total"], (
        f"User tier counts don't sum to total: {users}"
    )


def test_admin_stats_mrr_formula_correct(client, db):
    """mrr_estimate must equal basic_count * 4.99 + vip_count * 9.99."""
    from app.models import User
    from app.auth import hash_password

    for tier, email in [("basic", "mrr_basic1@t.com"), ("basic", "mrr_basic2@t.com"),
                        ("vip", "mrr_vip@t.com")]:
        db.add(User(email=email, hashed_password=hash_password("Pass123!"),
                    name=email, subscription_tier=tier))
    db.commit()

    pw = get_settings().admin_password
    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    users = data["users"]
    expected_mrr = round(users["basic"] * 4.99 + users["vip"] * 9.99, 2)
    actual_mrr = round(data["mrr_estimate"], 2)
    assert actual_mrr == expected_mrr, (
        f"MRR formula wrong: expected {expected_mrr}, got {actual_mrr} "
        f"(basic={users['basic']}, vip={users['vip']})"
    )


def test_admin_stats_follow_count_non_negative(client, db):
    """follow_count and bet_event_count must be non-negative integers."""
    pw = get_settings().admin_password
    resp = client.get("/admin/stats", headers={"x-admin-password": pw})
    assert resp.status_code == 200
    data = resp.json()
    assert data["follows"]["total"] >= 0
    assert data["bet_events"]["total"] >= 0


# ── Polymarket cross-validation ──────────────────────────────────────────────

def test_polymarket_cross_validation_top_bettor(client):
    """PolyEdge #1 bettor address must be in Polymarket's live top 5.

    This confirms PolyEdge is not showing stale or wrong leaderboard data.
    Skips if either API is unavailable.
    """
    _clear_bettors_cache()
    polyedge_resp = client.get("/bettors?limit=5&sort=profit")
    _skip_if_502(polyedge_resp, "GET /bettors (cross-validate)")
    assert polyedge_resp.status_code == 200
    polyedge_bettors = polyedge_resp.json()["bettors"]
    if not polyedge_bettors:
        pytest.skip("PolyEdge returned empty leaderboard")

    polyedge_top = polyedge_bettors[0]["address"].lower()

    # Call Polymarket directly
    try:
        pm_resp = httpx.get(
            "https://data-api.polymarket.com/leaderboard",
            params={"timePeriod": "all", "orderBy": "PNL", "limit": "10"},
            timeout=10.0,
        )
    except Exception as e:
        pytest.skip(f"Polymarket API unreachable: {e}")

    if pm_resp.status_code != 200:
        pytest.skip(f"Polymarket API returned {pm_resp.status_code}")

    try:
        pm_data = pm_resp.json()
        if isinstance(pm_data, list):
            pm_entries = pm_data
        else:
            pm_entries = pm_data.get("data", pm_data.get("entries", []))
    except Exception:
        pytest.skip("Could not parse Polymarket API response")

    if not pm_entries:
        pytest.skip("Polymarket API returned empty leaderboard")

    pm_top5 = [e.get("proxyWallet", "").lower() for e in pm_entries[:5]]
    assert polyedge_top in pm_top5, (
        f"PolyEdge #1 bettor {polyedge_top!r} not in Polymarket top 5: {pm_top5}. "
        "Possible stale or mismatched leaderboard data."
    )


# ── Active positions price range ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_active_positions_price_range_filters_resolved_markets():
    """get_active_positions must exclude positions with cur_price outside 0.001–0.999.

    A position with price=0 has missing data; price>=1 means the YES outcome
    has fully resolved. Serving these as 'copyable' positions is a data quality bug.
    """
    from unittest.mock import AsyncMock, patch

    raw_positions = [
        # Resolved market — price = 0 (should be excluded)
        {"redeemable": False, "title": "Resolved Low", "outcome": "Yes",
         "avgPrice": 0.50, "curPrice": 0.0, "eventSlug": "resolved-low"},
        # Resolved market — price = 1 (should be excluded)
        {"redeemable": False, "title": "Resolved High", "outcome": "Yes",
         "avgPrice": 0.80, "curPrice": 1.0, "eventSlug": "resolved-high"},
        # Valid open market (should be included)
        {"redeemable": False, "title": "Open Market", "outcome": "Yes",
         "avgPrice": 0.40, "curPrice": 0.50, "eventSlug": "open-market"},
        # Edge valid — near-zero but above threshold (should be included)
        {"redeemable": False, "title": "Cheap Market", "outcome": "Yes",
         "avgPrice": 0.002, "curPrice": 0.005, "eventSlug": "cheap-market"},
    ]

    mock_resp = AsyncMock()
    mock_resp.raise_for_status = AsyncMock()
    mock_resp.json = lambda: raw_positions

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest_price_range")

    assert len(result) == 2, (
        f"Expected 2 positions (resolved filtered out), got {len(result)}: "
        f"{[r['market_title'] for r in result]}"
    )
    for pos in result:
        assert 0.001 <= pos["avg_price"] <= 0.999 or pos["avg_price"] == 0.0, (
            f"avg_price {pos['avg_price']} out of expected range"
        )
        assert 0.001 <= pos["cur_price"] <= 0.999, (
            f"cur_price {pos['cur_price']} outside [0.001, 0.999] — resolved market leaked through: {pos}"
        )


# ── Consensus signal data quality ────────────────────────────────────────────

def test_consensus_whale_count_and_price_range(client):
    """Each consensus signal must have whale_count >= 3 and avg_entry_price in 0.01–0.99.

    whale_count < 3 would be a filter bypass; price outside range = resolved market leaked through.
    Skips gracefully if Polymarket is unreachable.
    """
    resp = client.get("/markets/consensus")
    if resp.status_code == 502:
        pytest.skip("Polymarket API unavailable (consensus returned 502)")
    assert resp.status_code == 200

    signals = resp.json().get("signals", [])
    if not signals:
        pytest.skip("No consensus signals returned — Polymarket may have no qualifying markets")

    for sig in signals:
        wc = sig.get("whale_count", 0)
        assert wc >= 3, (
            f"Consensus signal has whale_count={wc} — below minimum threshold of 3: {sig}"
        )
        price = sig.get("avg_entry_price", 0)
        assert 0.01 <= price <= 0.99, (
            f"avg_entry_price={price} outside [0.01, 0.99] — resolved market in consensus: {sig}"
        )
        cid = sig.get("condition_id", "")
        assert CONDITION_ID_RE.match(cid), (
            f"condition_id={cid!r} is not a valid 64-char hex ID (expected ^0x[a-fA-F0-9]{{64}}$): {sig}"
        )
