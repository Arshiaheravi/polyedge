"""Tests for polymarket service — normalisation functions and active positions filter."""
import pytest

from app.services.polymarket import (
    _normalise_leaderboard_entry,
    _normalise_bet,
    _blockies_url,
)


# ── Normalise leaderboard entry ───────────────────────────────────────────────

def test_normalise_leaderboard_full_entry():
    raw = {
        "rank": "1",
        "proxyWallet": "0xabc123",
        "userName": "beachboy",
        "vol": "12345.67",
        "pnl": "4321.99",
        "profileImage": "https://example.com/avatar.png",
    }
    result = _normalise_leaderboard_entry(raw)
    assert result["rank"] == 1
    assert result["address"] == "0xabc123"
    assert result["name"] == "beachboy"
    assert result["volume_usd"] == 12345.67
    assert result["pnl_usd"] == 4321.99
    assert result["avatar_url"] == "https://example.com/avatar.png"


def test_normalise_leaderboard_missing_name_uses_truncated_address():
    raw = {"rank": "5", "proxyWallet": "0x" + "a" * 20, "vol": "100", "pnl": "50"}
    result = _normalise_leaderboard_entry(raw)
    assert result["name"].endswith("...")
    assert len(result["name"]) <= 15


def test_normalise_leaderboard_missing_avatar_generates_identicon():
    raw = {"rank": "2", "proxyWallet": "0xabc", "vol": "0", "pnl": "0"}
    result = _normalise_leaderboard_entry(raw)
    assert "dicebear" in result["avatar_url"]


def test_normalise_leaderboard_zero_values():
    raw = {"rank": "0", "proxyWallet": "", "vol": None, "pnl": None}
    result = _normalise_leaderboard_entry(raw)
    assert result["volume_usd"] == 0.0
    assert result["pnl_usd"] == 0.0
    assert result["rank"] == 0


# ── Normalise bet ─────────────────────────────────────────────────────────────

def test_normalise_bet_full():
    raw = {
        "conditionId": "cond_001",
        "title": "Will X win?",
        "outcome": "Yes",
        "usdcSize": "250.50",
        "timestamp": "2026-03-01T12:00:00",
        "price": "0.6500",
        "side": "BUY",
        "transactionHash": "0xtx",
        "icon": "https://img.example.com/icon.png",
        "eventSlug": "x-championship",
        "slug": "will-x-win",
    }
    result = _normalise_bet(raw)
    assert result["market_id"] == "cond_001"
    assert result["market_question"] == "Will X win?"
    assert result["outcome"] == "Yes"
    assert result["amount_usd"] == 250.50
    assert result["price"] == 0.65
    assert result["type"] == "BUY"
    assert result["tx_hash"] == "0xtx"
    # eventSlug takes priority over slug for correct Polymarket URLs
    assert result["market_slug"] == "x-championship"


def test_normalise_bet_missing_fields():
    result = _normalise_bet({})
    assert result["market_question"] == "Unknown Market"
    assert result["amount_usd"] == 0.0
    assert result["price"] == 0.0


# ── blockies URL ──────────────────────────────────────────────────────────────

def test_blockies_url_format():
    url = _blockies_url("0xABC")
    assert "dicebear" in url
    assert "0xabc" in url  # lowercased


def test_blockies_url_empty_address():
    url = _blockies_url("")
    assert "unknown" in url


# ── Active positions filter (mocked HTTP) ─────────────────────────────────────

@pytest.mark.asyncio
async def test_get_active_positions_filters_redeemable():
    """Only redeemable=False positions are returned."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_response_data = [
        {"redeemable": True,  "title": "Resolved Market", "outcome": "Yes",
         "currentValue": 0, "eventSlug": "resolved"},
        {"redeemable": False, "title": "Live Market",     "outcome": "No",
         "currentValue": 500.0, "eventSlug": "live-market", "curPrice": 0.5, "avgPrice": 0.4},
        {"redeemable": True,  "title": "Another Resolved", "outcome": "Yes",
         "currentValue": 0, "eventSlug": "resolved2"},
    ]

    mock_resp = MagicMock()
    mock_resp.json.return_value = mock_response_data
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")

    assert len(result) == 1
    assert result[0]["market_title"] == "Live Market"
    assert result[0]["poly_url"] == "https://polymarket.com/event/live-market"


@pytest.mark.asyncio
async def test_get_active_positions_empty_on_api_error():
    """Returns empty list if Polymarket API fails."""
    from unittest.mock import AsyncMock, patch

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=Exception("connection error"))

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")

    assert result == []
