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
    assert resp.json() == {"bettors": []}


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
