"""
Polymarket API client.

Confirmed working endpoints (no auth required):
  GET https://data-api.polymarket.com/v1/leaderboard
      ?timePeriod=day|week|month|all
      &orderBy=PNL|VOL
      &limit=50
      &offset=0
      &category=overall
    → Returns: rank, proxyWallet, userName, vol, pnl, profileImage

  GET https://data-api.polymarket.com/trades?limit=N
    → Recent global trades (for live ticker)

  GET https://data-api.polymarket.com/activity?user=ADDR&limit=N
    → Trades for a specific wallet (for bettor profiles)
"""
from typing import Optional

import httpx

BASE_URL = "https://data-api.polymarket.com"

TIMEOUT = 15.0


def _blockies_url(address: str) -> str:
    seed = address.lower() if address else "unknown"
    return f"https://api.dicebear.com/7.x/identicon/svg?seed={seed}"


def _normalise_leaderboard_entry(raw: dict) -> dict:
    address = raw.get("proxyWallet") or ""
    name = raw.get("userName") or (address[:10] + "..." if address else "Unknown")
    avatar_url = raw.get("profileImage") or _blockies_url(address)
    vol = float(raw.get("vol") or 0)
    pnl = float(raw.get("pnl") or 0)
    # rank comes as string from API
    rank = int(raw.get("rank") or 0)
    return {
        "rank": rank,
        "address": address,
        "name": name,
        "volume_usd": round(vol, 2),
        "pnl_usd": round(pnl, 2),
        "avatar_url": avatar_url,
    }


def _normalise_profile(raw: dict, volume: float = 0.0, trade_count: int = 0) -> dict:
    address = raw.get("proxyWallet") or raw.get("address") or ""
    name = raw.get("userName") or raw.get("name") or raw.get("pseudonym") or (address[:10] + "..." if address else "Unknown")
    avatar_url = raw.get("profileImageOptimized") or raw.get("profileImage") or _blockies_url(address)
    avg_bet = round(volume / trade_count, 2) if trade_count > 0 else 0.0

    return {
        "address": address,
        "name": name,
        "volume_usd": round(float(volume), 2),
        "total_bets": int(raw.get("numTrades") or raw.get("total_bets") or trade_count),
        "avg_bet_usd": avg_bet,
        "avatar_url": avatar_url,
    }


def _normalise_bet(raw: dict) -> dict:
    return {
        "market_id": raw.get("conditionId") or raw.get("market_id") or "",
        "market_question": raw.get("title") or raw.get("question") or raw.get("market_question") or "Unknown Market",
        "outcome": raw.get("outcome") or raw.get("side") or "",
        "amount_usd": round(float(raw.get("usdcSize") or raw.get("size") or 0), 2),
        "timestamp": raw.get("timestamp") or raw.get("createdAt") or "",
        "price": round(float(raw.get("price") or 0), 4),
        "type": raw.get("side") or "BUY",
        "tx_hash": raw.get("transactionHash") or "",
        "market_icon": raw.get("icon") or "",
        "market_slug": raw.get("eventSlug") or raw.get("slug") or "",
    }


async def get_live_trades(limit: int = 20) -> list[dict]:
    """
    Fetch the most recent global Polymarket trades for the live ticker.
    Returns normalised trade objects with bettor name, market, outcome, and size.
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/trades", params={"limit": limit})
            resp.raise_for_status()
            trades = resp.json()
            if not isinstance(trades, list):
                trades = []
        except Exception:
            trades = []

    result = []
    for t in trades:
        addr = t.get("proxyWallet") or ""
        name = t.get("name") or t.get("pseudonym") or (addr[:8] + "..." if addr else "anon")
        market = t.get("title") or t.get("question") or "Unknown Market"
        outcome = t.get("outcome") or t.get("side") or ""
        size = round(float(t.get("usdcSize") or t.get("size") or 0), 2)
        side = (t.get("side") or "").upper()
        result.append({
            "name": name,
            "market": market,
            "outcome": outcome,
            "amount_usd": size,
            "side": side,
            "timestamp": t.get("timestamp") or t.get("createdAt") or "",
            "market_slug": t.get("slug") or t.get("eventSlug") or "",
        })
    return result


async def get_leaderboard(
    sort_by: str = "profit",
    time_period: str = "month",
    limit: int = 100,
) -> list[dict]:
    """
    Fetch the real Polymarket leaderboard from data-api.polymarket.com/v1/leaderboard.
    Returns actual profit (pnl) and volume data — same data Polymarket's own site shows.

    sort_by:    "profit" | "volume"
    time_period: "day" | "week" | "month" | "all"
    limit:      max 50 per page; we paginate to reach requested limit
    """
    order_by = "PNL" if sort_by == "profit" else "VOL"
    page_size = 50
    results: list[dict] = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        offset = 0
        while len(results) < limit:
            try:
                resp = await client.get(
                    f"{BASE_URL}/v1/leaderboard",
                    params={
                        "timePeriod": time_period,
                        "orderBy": order_by,
                        "limit": page_size,
                        "offset": offset,
                        "category": "overall",
                    },
                )
                resp.raise_for_status()
                page = resp.json()
                if not isinstance(page, list) or len(page) == 0:
                    break
                results.extend(page)
                if len(page) < page_size:
                    break
                offset += page_size
            except Exception:
                break

    return [_normalise_leaderboard_entry(r) for r in results[:limit]]


async def get_active_positions(address: str, limit: int = 20) -> list[dict]:
    """
    Fetch ONLY open (still-tradeable) positions for a wallet.

    redeemable=False  → market is still live, price is still moving, user CAN copy this bet
    redeemable=True   → market resolved, position is settled — skip these

    Fetches up to 500 positions to find open ones (settled positions pile up and
    can push open ones far down the list).
    """
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(
                f"{BASE_URL}/positions",
                params={"user": address, "sizeThreshold": "0.01", "limit": 500},
            )
            resp.raise_for_status()
            raw = resp.json()
            if not isinstance(raw, list):
                raw = []
        except Exception:
            raw = []

    result = []
    for p in raw:
        # Skip settled/resolved positions — not copyable
        if p.get("redeemable"):
            continue

        event_slug = p.get("eventSlug") or ""
        slug = p.get("slug") or ""
        condition_id = p.get("conditionId") or ""

        # Build the direct Polymarket link
        if event_slug:
            poly_url = f"https://polymarket.com/event/{event_slug}"
        elif slug:
            poly_url = f"https://polymarket.com/event/{slug}"
        else:
            poly_url = "https://polymarket.com"

        cur_price = float(p.get("curPrice") or 0)
        avg_price = float(p.get("avgPrice") or 0)

        result.append({
            "market_title": p.get("title") or "Unknown Market",
            "outcome": p.get("outcome") or "",
            "size": round(float(p.get("size") or 0), 4),
            "current_value_usd": round(float(p.get("currentValue") or 0), 2),
            "initial_value_usd": round(float(p.get("initialValue") or 0), 2),
            "avg_price": round(avg_price, 4),
            "cur_price": round(cur_price, 4),
            "cash_pnl": round(float(p.get("cashPnl") or 0), 2),
            "percent_pnl": round(float(p.get("percentPnl") or 0), 2),
            "end_date": p.get("endDate") or "",
            "poly_url": poly_url,
            "icon": p.get("icon") or "",
        })
    return result


async def get_bettor_profile(address: str) -> dict:
    """Get a specific bettor's profile from their recent activity."""
    params = {"user": address, "limit": 50}
    raw_list = []

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/activity", params=params)
            resp.raise_for_status()
            raw_list = resp.json()
            if not isinstance(raw_list, list):
                raw_list = []
        except Exception:
            raw_list = []

    if not raw_list:
        return _normalise_profile({"proxyWallet": address})

    first = raw_list[0]
    profile_raw = {
        "proxyWallet": address,
        "name": first.get("name") or first.get("pseudonym") or "",
        "profileImage": first.get("profileImageOptimized") or first.get("profileImage") or "",
    }
    volume = sum(float(t.get("usdcSize") or t.get("size") or 0) for t in raw_list)
    return _normalise_profile(profile_raw, volume=volume, trade_count=len(raw_list))


async def get_recent_bets(address: str, limit: int = 20) -> list[dict]:
    """Get recent bets/activity for a specific address."""
    params = {"user": address, "limit": limit}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/activity", params=params)
            resp.raise_for_status()
            raw_list = resp.json()
            if not isinstance(raw_list, list):
                raw_list = raw_list.get("data") or raw_list.get("activity") or []
        except Exception:
            raw_list = []

    return [_normalise_bet(b) for b in raw_list if isinstance(b, dict)]
