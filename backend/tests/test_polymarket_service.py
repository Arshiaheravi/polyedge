"""Tests for polymarket service — normalisation functions and active positions filter."""
import time
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


def test_normalise_leaderboard_accuracy_from_percentProfitable():
    """percentProfitable (0-100) must be converted to accuracy (0.0-1.0)."""
    raw = {
        "rank": "1", "proxyWallet": "0xabc", "vol": "1000", "pnl": "500",
        "percentProfitable": 68.5,
    }
    result = _normalise_leaderboard_entry(raw)
    assert result["accuracy"] == pytest.approx(0.685, abs=1e-4)


def test_normalise_leaderboard_accuracy_none_when_missing():
    """accuracy must be None when percentProfitable is absent from the API response."""
    raw = {"rank": "2", "proxyWallet": "0xdef", "vol": "200", "pnl": "100"}
    result = _normalise_leaderboard_entry(raw)
    assert result["accuracy"] is None


def test_normalise_leaderboard_accuracy_none_when_null():
    """accuracy must be None when percentProfitable is explicitly null in the API response."""
    raw = {"rank": "3", "proxyWallet": "0xghi", "vol": "300", "pnl": "150",
           "percentProfitable": None}
    result = _normalise_leaderboard_entry(raw)
    assert result["accuracy"] is None


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
    assert result["type"] == "BUY"  # raw.get("side") or "BUY" — absent side defaults to BUY


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


# ── get_active_positions poly_url branches ────────────────────────────────────

@pytest.mark.asyncio
async def test_get_active_positions_uses_slug_when_no_event_slug():
    """When eventSlug is absent but slug is present, poly_url uses slug."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_response_data = [
        {
            "redeemable": False,
            "title": "Slug Market",
            "outcome": "Yes",
            "slug": "slug-only-market",
            "curPrice": 0.50,
            # no eventSlug key
        }
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
    assert result[0]["poly_url"] == "https://polymarket.com/event/slug-only-market"


@pytest.mark.asyncio
async def test_get_active_positions_uses_default_url_when_no_slugs():
    """When neither eventSlug nor slug is present, poly_url falls back to 'https://polymarket.com'."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_response_data = [
        {
            "redeemable": False,
            "title": "No Slug Market",
            "outcome": "No",
            "curPrice": 0.50,
            # no eventSlug, no slug
        }
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
    assert result[0]["poly_url"] == "https://polymarket.com"


# ── get_live_trades non-list response ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_live_trades_non_list_response_returns_empty():
    """When API returns a non-list (e.g. dict), get_live_trades returns empty list."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "unexpected format"}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_live_trades
        result = await get_live_trades(limit=10)

    assert result == []


# ── get_active_positions non-list response ────────────────────────────────────

@pytest.mark.asyncio
async def test_get_active_positions_non_list_response_returns_empty():
    """When API returns a non-list (e.g. dict), get_active_positions returns []."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "unexpected format"}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")

    assert result == []


# ── get_live_trades anon name when proxyWallet empty ─────────────────────────

@pytest.mark.asyncio
async def test_get_live_trades_empty_proxy_wallet_generates_anon_name():
    """When proxyWallet is '' and no name/pseudonym, get_live_trades uses 'anon'."""
    from unittest.mock import AsyncMock, MagicMock, patch

    trades = [{"proxyWallet": "", "usdcSize": "10"}]
    mock_resp = MagicMock()
    mock_resp.json.return_value = trades
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_live_trades
        result = await get_live_trades(limit=10)

    assert len(result) == 1
    assert result[0]["name"] == "anon"
    assert result[0]["amount_usd"] == 10.0


# ── get_leaderboard empty first page ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_leaderboard_empty_first_page_returns_empty_list():
    """When first API page is [], get_leaderboard returns [] without a second call."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_leaderboard
        result = await get_leaderboard(sort_by="profit", time_period="week", limit=100)

    assert result == []
    assert mock_client.get.call_count == 1  # breaks on first empty page, no second call


# ── _normalise_profile includes rank and pnl_usd ─────────────────────────────

def test_normalise_profile_includes_rank_and_pnl_usd():
    """_normalise_profile must expose rank and pnl_usd fields (added session 112)."""
    from app.services.polymarket import _normalise_profile
    raw = {"proxyWallet": "0xabc", "userName": "Whale"}
    result = _normalise_profile(raw, volume=1000.0, trade_count=5, pnl_usd=420.75, rank=3)
    assert result["rank"] == 3
    assert result["pnl_usd"] == 420.75
    assert result["volume_usd"] == 1000.0
    assert result["address"] == "0xabc"


def test_normalise_profile_rank_and_pnl_default_to_zero():
    """When rank/pnl_usd not supplied, they default to 0."""
    from app.services.polymarket import _normalise_profile
    raw = {"proxyWallet": "0xdef"}
    result = _normalise_profile(raw)
    assert result["rank"] == 0
    assert result["pnl_usd"] == 0.0


def test_normalise_profile_accuracy_from_pct():
    """_normalise_profile converts accuracy_pct (0-100) to 0.0-1.0 float."""
    from app.services.polymarket import _normalise_profile
    raw = {"proxyWallet": "0xabc"}
    result = _normalise_profile(raw, accuracy_pct=75.5)
    assert result["accuracy"] == pytest.approx(0.7550, abs=1e-4)


def test_normalise_profile_accuracy_none_when_not_provided():
    """accuracy is None when accuracy_pct is omitted (bettor not on leaderboard)."""
    from app.services.polymarket import _normalise_profile
    raw = {"proxyWallet": "0xabc"}
    result = _normalise_profile(raw)
    assert result["accuracy"] is None


def test_normalise_profile_accuracy_zero():
    """accuracy_pct=0 (0% profitable) normalises to 0.0, not None."""
    from app.services.polymarket import _normalise_profile
    raw = {"proxyWallet": "0xabc"}
    result = _normalise_profile(raw, accuracy_pct=0)
    assert result["accuracy"] == 0.0


# ── get_recent_bets REDEEM filter ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_recent_bets_filters_out_redeem_type():
    """get_recent_bets must exclude entries where type=='REDEEM' — only TRADE returned."""
    from unittest.mock import AsyncMock, MagicMock, patch

    activity = [
        {"conditionId": "trade1", "title": "Trade Market", "outcome": "Yes",
         "usdcSize": "100.0", "price": "0.6", "side": "BUY", "type": "TRADE"},
        {"conditionId": "redeem1", "title": "Redeem Market", "outcome": "",
         "usdcSize": "80.0", "price": "0.0", "type": "REDEEM"},
        {"conditionId": "trade2", "title": "Another Trade", "outcome": "No",
         "usdcSize": "50.0", "price": "0.45", "side": "BUY", "type": "TRADE"},
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

    assert len(result) == 2
    ids = [r["market_id"] for r in result]
    assert "trade1" in ids
    assert "trade2" in ids
    assert "redeem1" not in ids


@pytest.mark.asyncio
async def test_get_recent_bets_outcome_and_price_populated_for_trade():
    """TRADE entries must have outcome ('Yes'/'No') and price (0-1 float) populated."""
    from unittest.mock import AsyncMock, MagicMock, patch

    activity = [
        {"conditionId": "t1", "title": "Win Bet", "outcome": "Yes",
         "usdcSize": "200.0", "price": "0.7500", "side": "BUY", "type": "TRADE"},
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
    assert result[0]["outcome"] == "Yes"
    assert result[0]["price"] == 0.75


# ── get_recent_bets "activity" key fallback ───────────────────────────────────

@pytest.mark.asyncio
async def test_get_recent_bets_dict_response_with_activity_key_returns_bets():
    """When API returns a dict with an 'activity' key, get_recent_bets uses that list."""
    from unittest.mock import AsyncMock, MagicMock, patch

    bet = {
        "conditionId": "cond_activity",
        "title": "Activity Key Market",
        "outcome": "Yes",
        "usdcSize": "55.0",
        "side": "BUY",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"activity": [bet]}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_recent_bets
        result = await get_recent_bets("0xwhale", limit=20)

    assert len(result) == 1
    assert result[0]["market_id"] == "cond_activity"
    assert result[0]["amount_usd"] == 55.0


# ── copy_signal in get_active_positions ──────────────────────────────────────

def _make_mock_positions_client(positions_data):
    """Helper: returns a mock httpx AsyncClient that returns positions_data."""
    from unittest.mock import AsyncMock, MagicMock
    mock_resp = MagicMock()
    mock_resp.json.return_value = positions_data
    mock_resp.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


@pytest.mark.asyncio
async def test_copy_signal_good_when_price_within_10_pct():
    """copy_signal='good' when cur_price <= avg_price * 1.10."""
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0.40, "curPrice": 0.42, "eventSlug": "s"}]  # +5%
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert result[0]["copy_signal"] == "good"
    assert result[0]["copy_value_pct"] == pytest.approx(5.0, abs=0.2)


@pytest.mark.asyncio
async def test_copy_signal_fair_when_price_10_to_30_pct_above():
    """copy_signal='fair' when cur_price is 10-30% above avg_price."""
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0.40, "curPrice": 0.48, "eventSlug": "s"}]  # +20%
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert result[0]["copy_signal"] == "fair"
    assert result[0]["copy_value_pct"] == pytest.approx(20.0, abs=0.2)


@pytest.mark.asyncio
async def test_copy_signal_late_when_price_over_30_pct_above():
    """copy_signal='late' when cur_price is >30% above avg_price."""
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0.30, "curPrice": 0.50, "eventSlug": "s"}]  # +66.7%
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert result[0]["copy_signal"] == "late"
    assert result[0]["copy_value_pct"] > 30


@pytest.mark.asyncio
async def test_copy_signal_good_when_price_dropped_below_entry():
    """Price below entry is still 'good' — even better than whale's price."""
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0.50, "curPrice": 0.35, "eventSlug": "s"}]  # -30%
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert result[0]["copy_signal"] == "good"
    assert result[0]["copy_value_pct"] < 0


@pytest.mark.asyncio
async def test_copy_signal_good_when_avg_price_is_zero():
    """When avg_price=0 (missing data), copy_signal defaults to 'good' with pct=0."""
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0, "curPrice": 0.50, "eventSlug": "s"}]
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert result[0]["copy_signal"] == "good"
    assert result[0]["copy_value_pct"] == 0.0


# ── compute_copy_simulator ────────────────────────────────────────────────────

def _make_simulator_mock_client(activity_data):
    """Build async mock client returning activity_data as JSON."""
    from unittest.mock import AsyncMock, MagicMock
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=activity_data)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)
    return mock_client


@pytest.mark.asyncio
async def test_copy_simulator_win_returns_positive_pnl():
    """One TRADE BUY + matching REDEEM → simulated win → positive P&L."""
    from unittest.mock import patch
    old_ts = str(int(time.time()) - 10 * 24 * 3600)  # 10 days ago
    activity = [
        {"type": "TRADE", "side": "BUY", "price": "0.25", "conditionId": "cid1", "timestamp": old_ts},
        {"type": "REDEEM", "conditionId": "cid1"},
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result["bets_analysed"] == 1
    assert result["simulated_pnl_usd"] == pytest.approx(300.0, rel=0.01)  # $100 * (1/0.25 - 1) = $300
    assert result["simulated_roi_pct"] == pytest.approx(300.0, rel=0.01)


@pytest.mark.asyncio
async def test_copy_simulator_loss_returns_negative_pnl():
    """TRADE BUY with old timestamp and no REDEEM → assumed loss → -$100."""
    from unittest.mock import patch
    old_ts = str(int(time.time()) - 10 * 24 * 3600)
    activity = [
        {"type": "TRADE", "side": "BUY", "price": "0.50", "conditionId": "cid_lose", "timestamp": old_ts},
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result["bets_analysed"] == 1
    assert result["simulated_pnl_usd"] == pytest.approx(-100.0, rel=0.01)
    assert result["simulated_roi_pct"] == pytest.approx(-100.0, rel=0.01)


@pytest.mark.asyncio
async def test_copy_simulator_mixed_win_and_loss():
    """One win (redeemed) + one loss (old, no redeem) → net P&L is sum of both."""
    from unittest.mock import patch
    old_ts = str(int(time.time()) - 10 * 24 * 3600)
    activity = [
        {"type": "TRADE", "side": "BUY", "price": "0.50", "conditionId": "cid_win", "timestamp": old_ts},
        {"type": "REDEEM", "conditionId": "cid_win"},
        {"type": "TRADE", "side": "BUY", "price": "0.50", "conditionId": "cid_lose", "timestamp": old_ts},
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result["bets_analysed"] == 2
    # win: $100 * (1/0.5 - 1) = $100; loss: -$100; net = $0
    assert result["simulated_pnl_usd"] == pytest.approx(0.0, abs=0.01)
    assert result["simulated_roi_pct"] == pytest.approx(0.0, abs=0.1)


@pytest.mark.asyncio
async def test_copy_simulator_recent_bets_skipped():
    """Bets < 7 days old with no REDEEM are open positions — skip them."""
    from unittest.mock import patch
    recent_ts = str(int(time.time()) - 1 * 24 * 3600)  # 1 day ago
    activity = [
        {"type": "TRADE", "side": "BUY", "price": "0.50", "conditionId": "cid_open", "timestamp": recent_ts},
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result["bets_analysed"] == 0
    assert result["simulated_pnl_usd"] == 0.0


@pytest.mark.asyncio
async def test_copy_simulator_zero_price_skipped():
    """BUY with price=0 is bad data — skip it."""
    from unittest.mock import patch
    old_ts = str(int(time.time()) - 10 * 24 * 3600)
    activity = [
        {"type": "TRADE", "side": "BUY", "price": "0", "conditionId": "cid_zero", "timestamp": old_ts},
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result["bets_analysed"] == 0


@pytest.mark.asyncio
async def test_copy_simulator_empty_response_returns_zeros():
    """Empty activity list → bets_analysed=0, pnl=0."""
    from unittest.mock import patch
    mock_client = _make_simulator_mock_client([])
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result == {"simulated_pnl_usd": 0.0, "simulated_roi_pct": 0.0, "bets_analysed": 0}


@pytest.mark.asyncio
async def test_copy_simulator_limit_enforced():
    """Only up to `limit` bets are scored even if more are available."""
    from unittest.mock import patch
    old_ts = str(int(time.time()) - 10 * 24 * 3600)
    # 15 losing BUY trades (old, no REDEEMs)
    activity = [
        {"type": "TRADE", "side": "BUY", "price": "0.5", "conditionId": f"cid{i}", "timestamp": old_ts}
        for i in range(15)
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=5)
    assert result["bets_analysed"] == 5


@pytest.mark.asyncio
async def test_copy_simulator_sell_side_excluded():
    """SELL-side trades are exit trades — they must be skipped and not counted in bets_analysed.
    Covers the `if side not in ("BUY", ""): continue` branch (polymarket.py:358-359)."""
    from unittest.mock import patch
    old_ts = str(int(time.time()) - 10 * 24 * 3600)
    # Only SELL trades — none should be analysed
    activity = [
        {"type": "TRADE", "side": "SELL", "price": "0.80", "conditionId": "cid_sell_1", "timestamp": old_ts},
        {"type": "TRADE", "side": "SELL", "price": "0.60", "conditionId": "cid_sell_2", "timestamp": old_ts},
    ]
    mock_client = _make_simulator_mock_client(activity)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest", limit=10)
    assert result["bets_analysed"] == 0
    assert result["simulated_pnl_usd"] == 0.0
    assert result["simulated_roi_pct"] == 0.0


@pytest.mark.asyncio
async def test_copy_simulator_api_connect_error_returns_zeros():
    """ConnectError on client.get() → except Exception branch → returns safe zeros.
    Covers polymarket.py:333-334 — the exception path not hit by empty-response test."""
    import httpx
    from unittest.mock import patch, AsyncMock

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("simulated network failure"))

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import compute_copy_simulator
        result = await compute_copy_simulator("0xtest")

    assert result == {"simulated_pnl_usd": 0.0, "simulated_roi_pct": 0.0, "bets_analysed": 0}


# ── get_consensus_signals (mocked Polymarket API) ─────────────────────────────

MOCK_CONDITION_ID = "0x" + "a" * 64  # valid 64-char hex


@pytest.mark.asyncio
async def test_get_consensus_signals_with_mocked_api():
    """Unit test: 5 whales all hold YES on the same market → whale_count=5 in output.

    Mocks get_leaderboard (returns 5 entries) and httpx.AsyncClient (returns
    1 position each with the same conditionId + outcome).  Verifies:
    - whale_count == 5
    - avg_entry_price is in (0.01, 0.99)
    - condition_id matches MOCK_CONDITION_ID
    - result is not skipped due to CI/network unavailability
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import get_consensus_signals

    # 5 whale leaderboard entries
    mock_leaderboard = [
        {"address": f"0x{i:040x}", "name": f"whale{i}", "pnl_usd": 1000.0 * (5 - i), "rank": i}
        for i in range(1, 6)
    ]

    # Position response: each whale holds YES on MOCK_CONDITION_ID at avg_price=0.60
    mock_position = {
        "conditionId": MOCK_CONDITION_ID,
        "outcome": "Yes",
        "title": "Will X happen?",
        "avgPrice": "0.60",
        "curPrice": "0.65",
        "redeemable": False,
        "eventSlug": "test-event",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = [mock_position]
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("app.services.polymarket.get_leaderboard", new=AsyncMock(return_value=mock_leaderboard)),
        patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client),
    ):
        signals = await get_consensus_signals(min_whales=3)

    assert len(signals) >= 1, "Expected at least 1 consensus signal from 5-whale mock"
    # Find the signal for our mock market
    target = next((s for s in signals if s["condition_id"] == MOCK_CONDITION_ID), None)
    assert target is not None, f"Signal for {MOCK_CONDITION_ID} not found in: {signals}"
    assert target["whale_count"] == 5, f"Expected 5 whales, got {target['whale_count']}"
    assert 0.01 < target["avg_entry_price"] < 0.99, (
        f"avg_entry_price {target['avg_entry_price']} out of expected range"
    )
    assert target["condition_id"] == MOCK_CONDITION_ID


@pytest.mark.asyncio
async def test_get_consensus_signals_filters_resolved_markets():
    """Unit test: positions with curPrice=0.98 (near-settled YES) must be excluded.

    The guard `cur_price > 0.95` must filter these out, producing 0 signals
    even when 5 whales all hold the same market.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import get_consensus_signals

    mock_leaderboard = [
        {"address": f"0x{i:040x}", "name": f"whale{i}", "pnl_usd": 1000.0 * (5 - i), "rank": i}
        for i in range(1, 6)
    ]

    # curPrice=0.98 — near-settled YES market; should be filtered by the > 0.95 guard
    mock_position = {
        "conditionId": MOCK_CONDITION_ID,
        "outcome": "Yes",
        "title": "Already decided market",
        "avgPrice": "0.50",
        "curPrice": "0.98",
        "redeemable": False,
        "eventSlug": "settled-event",
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = [mock_position]
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("app.services.polymarket.get_leaderboard", new=AsyncMock(return_value=mock_leaderboard)),
        patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client),
    ):
        signals = await get_consensus_signals(min_whales=3)

    # No signal should be returned — the market is near-settled (curPrice > 0.95)
    resolved_signal = next((s for s in signals if s.get("condition_id") == MOCK_CONDITION_ID), None)
    assert resolved_signal is None, (
        f"get_consensus_signals must filter out near-settled markets (curPrice=0.98), "
        f"but returned: {resolved_signal}"
    )


# ── get_recent_bets conviction score / label ──────────────────────────────────

@pytest.mark.asyncio
async def test_get_recent_bets_single_bet_conviction_score_is_one():
    """Single bet → conviction_score=1.0 and conviction_label='' (avg equals amount)."""
    from unittest.mock import AsyncMock, MagicMock, patch

    activity = [
        {"conditionId": "c1", "title": "Market Q", "outcome": "Yes",
         "usdcSize": "250.0", "price": "0.60", "side": "BUY", "type": "TRADE"},
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
    assert result[0]["conviction_score"] == 1.0
    assert result[0]["conviction_label"] == ""


@pytest.mark.asyncio
async def test_get_recent_bets_extreme_conviction_label_when_10x_average():
    """19 bets of $1 + 1 bet of $1000: avg=$50.95, score=19.6 -> conviction_label='EXTREME'."""
    from unittest.mock import AsyncMock, MagicMock, patch

    # avg = (19*1 + 1000) / 20 = 50.95; score for $1000 = round(1000/50.95, 1) = 19.6 >= 10 -> EXTREME
    activity = [
        {"conditionId": f"c{i}", "title": f"Market {i}", "outcome": "Yes",
         "usdcSize": "1.0", "price": "0.50", "side": "BUY", "type": "TRADE"}
        for i in range(19)
    ] + [
        {"conditionId": "cbig", "title": "Big Bet Market", "outcome": "Yes",
         "usdcSize": "1000.0", "price": "0.50", "side": "BUY", "type": "TRADE"},
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

    big_bet = next(r for r in result if r["market_id"] == "cbig")
    assert big_bet["conviction_label"] == "EXTREME"
    assert big_bet["conviction_score"] >= 10.0


# ── copy_value_pct exact formula verification ─────────────────────────────────


@pytest.mark.asyncio
async def test_copy_value_pct_exact_math_25_percent():
    """avg_price=0.40, cur_price=0.50 must produce copy_value_pct == 25.0 exactly.

    Formula: round((cur_price - avg_price) / avg_price * 100, 1)
    (0.50 - 0.40) / 0.40 * 100 = 25.0  →  signal='fair' (10 < 25 ≤ 30)
    """
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0.40, "curPrice": 0.50, "eventSlug": "slug"}]
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert len(result) == 1
    assert result[0]["copy_value_pct"] == 25.0, (
        f"Expected copy_value_pct=25.0 for avg=0.40, cur=0.50, got {result[0]['copy_value_pct']}"
    )
    assert result[0]["copy_signal"] == "fair", (
        f"25% gain must produce copy_signal='fair', got {result[0]['copy_signal']!r}"
    )


@pytest.mark.asyncio
async def test_copy_value_pct_exact_math_50_percent():
    """avg_price=0.20, cur_price=0.30 must produce copy_value_pct == 50.0 exactly.

    Formula: round((cur_price - avg_price) / avg_price * 100, 1)
    (0.30 - 0.20) / 0.20 * 100 = 50.0  →  signal='late' (50 > 30)
    """
    from unittest.mock import patch
    data = [{"redeemable": False, "title": "T", "outcome": "Yes",
             "avgPrice": 0.20, "curPrice": 0.30, "eventSlug": "slug"}]
    mock_client = _make_mock_positions_client(data)
    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_active_positions
        result = await get_active_positions("0xtest")
    assert len(result) == 1
    assert result[0]["copy_value_pct"] == 50.0, (
        f"Expected copy_value_pct=50.0 for avg=0.20, cur=0.30, got {result[0]['copy_value_pct']}"
    )
    assert result[0]["copy_signal"] == "late", (
        f"50% gain must produce copy_signal='late', got {result[0]['copy_signal']!r}"
    )


@pytest.mark.asyncio
async def test_get_recent_bets_api_exception_returns_empty_list():
    """API exception must return empty list without raising — conviction fields not needed."""
    from unittest.mock import AsyncMock, patch
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_recent_bets
        result = await get_recent_bets("0xdeadbeef", limit=20)

    assert result == []


@pytest.mark.asyncio
async def test_get_live_trades_api_exception_returns_empty_list():
    """ConnectError on client.get() → except Exception branch (polymarket.py lines 104-105)
    → trades = [] → get_live_trades returns [] without raising."""
    from unittest.mock import AsyncMock, patch
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("simulated connection error"))

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_live_trades
        result = await get_live_trades(limit=20)

    assert result == []


@pytest.mark.asyncio
async def test_get_recent_bets_conviction_score_fallback_when_amount_zero():
    """When all bets have amount_usd == 0 (usdcSize=0), avg <= 0 triggers
    the fallback branch at polymarket.py line 429: score = 1.0 and label = ''.

    Verify: conviction_score == 1.0, conviction_label == ''
    """
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = [
        {
            "type": "TRADE",
            "proxyWallet": "0xtest",
            "usdcSize": "0",       # amount_usd will be 0.0
            "price": "0.50",
            "side": "BUY",
            "outcome": "Yes",
            "market": "Will X happen?",
            "timestamp": 1700000000,
        }
    ]

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        from app.services.polymarket import get_recent_bets  # noqa: PLC0415
        result = await get_recent_bets("0xtest", limit=20)

    assert len(result) == 1
    assert result[0]["conviction_score"] == 1.0, (
        f"Expected conviction_score=1.0 for zero-amount bet, got {result[0]['conviction_score']}"
    )
    assert result[0]["conviction_label"] == "", (
        f"Expected empty conviction_label for score=1.0, got {result[0]['conviction_label']!r}"
    )


@pytest.mark.asyncio
async def test_fetch_positions_dict_response_produces_no_signal():
    """_fetch_positions inside get_consensus_signals resets raw=[] when the
    API returns a dict instead of a list (polymarket.py line 467:
    if not isinstance(raw, list): raw = []).

    With 3 whales but each getting an empty position list, whale_count < min_whales=3
    → no signals returned.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import get_consensus_signals

    mock_leaderboard = [
        {"address": f"0x{i:040x}", "name": f"whale{i}", "pnl_usd": 1000.0, "rank": i}
        for i in range(1, 4)
    ]

    # API returns a dict instead of a list → _fetch_positions sets raw=[]
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "unexpected dict response"}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("app.services.polymarket.get_leaderboard", new=AsyncMock(return_value=mock_leaderboard)),
        patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client),
    ):
        signals = await get_consensus_signals(min_whales=3)

    assert signals == [], (
        f"Dict API response in _fetch_positions must produce empty positions → no signals, got {signals}"
    )


@pytest.mark.asyncio
async def test_fetch_positions_connect_error_produces_no_signal():
    """_fetch_positions inside get_consensus_signals catches ConnectError and sets
    raw=[] (polymarket.py line 469: except Exception: raw = []).

    With all fetches failing, no positions → no consensus signals returned.
    """
    from unittest.mock import AsyncMock, patch
    import httpx
    from app.services.polymarket import get_consensus_signals

    mock_leaderboard = [
        {"address": f"0x{i:040x}", "name": f"whale{i}", "pnl_usd": 1000.0, "rank": i}
        for i in range(1, 4)
    ]

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

    with (
        patch("app.services.polymarket.get_leaderboard", new=AsyncMock(return_value=mock_leaderboard)),
        patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client),
    ):
        signals = await get_consensus_signals(min_whales=3)

    assert signals == [], (
        f"ConnectError in _fetch_positions must produce empty positions → no signals, got {signals}"
    )


# ── get_bettor_profile: paginated non-list break (line 279) ──────────────────

@pytest.mark.asyncio
async def test_get_bettor_profile_leaderboard_dict_response_returns_profile_without_lb_data():
    """_fetch_leaderboard_entry inside get_bettor_profile breaks immediately when
    the leaderboard API returns a dict instead of a list (polymarket.py line 279:
    if not isinstance(page, list): break).

    lb_entry is None → has_lb_data=False → profile built from activity only.
    Function must NOT raise; returns a valid profile dict with address populated.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import get_bettor_profile

    async def url_dependent_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "leaderboard" in url:
            resp.json.return_value = {"error": "not a list"}
        else:
            resp.json.return_value = []
        return resp

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = url_dependent_get

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        result = await get_bettor_profile("0xdeadbeef")

    assert isinstance(result, dict), f"Expected dict profile, got {type(result)}"
    assert result["address"] == "0xdeadbeef", (
        f"Profile address must be preserved when leaderboard returns dict, got {result.get('address')!r}"
    )


# ── compute_copy_simulator: non-list activity response (line 332) ─────────────

@pytest.mark.asyncio
async def test_compute_copy_simulator_dict_response_returns_zero_pnl():
    """compute_copy_simulator resets raw_list=[] when the activity API returns a
    dict instead of a list (polymarket.py line 332:
    if not isinstance(raw_list, list): raw_list = []).

    With no tradeable items, bets_analysed==0 → returns zero-pnl sentinel dict.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import compute_copy_simulator

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"error": "bad"}
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client):
        result = await compute_copy_simulator("0xaddr", limit=10)

    assert result == {"simulated_pnl_usd": 0.0, "simulated_roi_pct": 0.0, "bets_analysed": 0}, (
        f"Dict API response must produce zero-pnl result, got {result}"
    )


# ── _fetch_positions: empty conditionId skip (line 477) ──────────────────────

@pytest.mark.asyncio
async def test_fetch_positions_empty_condition_id_position_skipped():
    """_fetch_positions inside get_consensus_signals skips any position where
    conditionId is empty (polymarket.py line 477:
    if not cid or not outcome: continue).

    3 whales each get a position with conditionId="" → all skipped → result=[].
    With no valid positions, no consensus signals are generated.
    """
    from unittest.mock import AsyncMock, MagicMock, patch
    from app.services.polymarket import get_consensus_signals

    mock_leaderboard = [
        {"address": f"0x{i:040x}", "name": f"whale{i}", "pnl_usd": 1000.0, "rank": i}
        for i in range(1, 4)
    ]

    # Position with empty conditionId — passes redeemable check but hits line 477
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {"conditionId": "", "outcome": "Yes", "avgPrice": "0.5", "curPrice": "0.55",
         "title": "Test Market", "redeemable": False}
    ]
    mock_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("app.services.polymarket.get_leaderboard", new=AsyncMock(return_value=mock_leaderboard)),
        patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client),
    ):
        signals = await get_consensus_signals(min_whales=3)

    assert signals == [], (
        f"Positions with empty conditionId must be skipped → no signals, got {signals}"
    )
