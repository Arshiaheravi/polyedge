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
