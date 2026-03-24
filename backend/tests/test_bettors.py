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
