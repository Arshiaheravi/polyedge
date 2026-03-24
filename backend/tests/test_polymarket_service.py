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


# ── get_bettor_profile ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_bettor_profile_returns_normalised_profile():
    """get_bettor_profile builds profile from activity: name, volume, trade_count."""
    from unittest.mock import AsyncMock, MagicMock, patch

    activity = [
        {"proxyWallet": "0xwhale", "name": "Whale", "usdcSize": "500.0"},
        {"proxyWallet": "0xwhale", "name": "Whale", "usdcSize": "300.0"},
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = activity
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_bettor_profile
        result = await get_bettor_profile("0xwhale")

    assert result["name"] == "Whale"
    assert result["volume_usd"] == 800.0
    assert result["avg_bet_usd"] == 400.0
    assert result["address"] == "0xwhale"


# ── get_recent_bets ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_recent_bets_returns_normalised_bets():
    """get_recent_bets fetches activity and normalises each entry into a bet dict."""
    from unittest.mock import AsyncMock, MagicMock, patch

    activity = [
        {
            "conditionId": "cond1",
            "title": "Will X win?",
            "outcome": "Yes",
            "usdcSize": "100.0",
            "price": "0.65",
            "side": "BUY",
            "transactionHash": "0xtxhash",
        }
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = activity
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_recent_bets
        result = await get_recent_bets("0xwhale", limit=20)

    assert len(result) == 1
    assert result[0]["market_id"] == "cond1"
    assert result[0]["market_question"] == "Will X win?"
    assert result[0]["amount_usd"] == 100.0
    assert result[0]["type"] == "BUY"


# ── get_live_trades ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_live_trades_returns_normalised_trades():
    """get_live_trades fetches /trades and returns name/market/side/amount_usd per entry."""
    from unittest.mock import AsyncMock, MagicMock, patch

    trades = [
        {
            "proxyWallet": "0xabc",
            "name": "Alice",
            "title": "Market A",
            "outcome": "Yes",
            "usdcSize": "200.0",
            "side": "buy",
            "timestamp": "2026-03-24T10:00:00",
            "slug": "market-a",
        }
    ]
    mock_resp = MagicMock()
    mock_resp.json.return_value = trades
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_live_trades
        result = await get_live_trades(limit=20)

    assert len(result) == 1
    assert result[0]["name"] == "Alice"
    assert result[0]["market"] == "Market A"
    assert result[0]["side"] == "BUY"
    assert result[0]["amount_usd"] == 200.0


# ── get_bettor_profile when activity is empty ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_bettor_profile_empty_activity_returns_address_profile():
    """When Polymarket returns no activity, get_bettor_profile returns address-only profile with zeros."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_bettor_profile
        result = await get_bettor_profile("0xempty")

    assert result["address"] == "0xempty"
    assert result["volume_usd"] == 0.0
    assert result["avg_bet_usd"] == 0.0
    assert result["total_bets"] == 0


# ── get_recent_bets when API returns dict instead of list ─────────────────────

@pytest.mark.asyncio
async def test_get_recent_bets_dict_response_with_data_key_returns_bets():
    """When API returns a dict with a 'data' key, get_recent_bets uses that list."""
    from unittest.mock import AsyncMock, MagicMock, patch

    bet = {
        "conditionId": "cond_dict",
        "title": "Dict Market",
        "outcome": "No",
        "usdcSize": "75.0",
        "side": "SELL",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"data": [bet]}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_recent_bets
        result = await get_recent_bets("0xwhale", limit=20)

    assert len(result) == 1
    assert result[0]["market_id"] == "cond_dict"
    assert result[0]["amount_usd"] == 75.0


# ── get_leaderboard pagination ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_leaderboard_paginates_when_first_page_full():
    """When first page returns page_size (50) items a second API call is made."""
    from unittest.mock import AsyncMock, MagicMock, patch

    page1 = [{"rank": str(i), "proxyWallet": f"0x{i:04x}", "vol": "100", "pnl": "10"} for i in range(50)]
    page2 = [{"rank": str(50 + i), "proxyWallet": f"0x{50+i:04x}", "vol": "50", "pnl": "5"} for i in range(10)]

    def make_resp(data):
        r = MagicMock()
        r.json.return_value = data
        r.raise_for_status = MagicMock()
        return r

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=[make_resp(page1), make_resp(page2)])

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_leaderboard
        result = await get_leaderboard(sort_by="profit", time_period="week", limit=100)

    assert mock_client.get.call_count == 2
    assert len(result) == 60
