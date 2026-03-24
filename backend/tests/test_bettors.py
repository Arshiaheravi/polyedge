"""Tests for /bettors endpoints — leaderboard and bettor detail (mocked)."""
from unittest.mock import AsyncMock, patch


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


def test_bettor_detail_public(client):
    mock_profile = {"address": "0xaaa", "name": "beachboy", "volume_usd": 1000.0, "total_bets": 10, "avg_bet_usd": 100.0, "avatar_url": ""}
    mock_bets = []
    with patch("app.routes.bettors.get_bettor_profile", new=AsyncMock(return_value=mock_profile)), \
         patch("app.routes.bettors.get_recent_bets", new=AsyncMock(return_value=mock_bets)):
        resp = client.get("/bettors/0xaaa")
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["name"] == "beachboy"
