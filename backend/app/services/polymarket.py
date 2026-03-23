"""
Polymarket API client.
Endpoints confirmed working (no auth required):
  GET /trades?limit=N          — recent global trades
  GET /activity?user=ADDR&limit=N — trades for a specific wallet
"""
from typing import Optional

import httpx

BASE_URL = "https://data-api.polymarket.com"

TIMEOUT = 15.0


def _blockies_url(address: str) -> str:
    seed = address.lower() if address else "unknown"
    return f"https://api.dicebear.com/7.x/identicon/svg?seed={seed}"


def _normalise_profile(raw: dict, volume: float = 0.0, trade_count: int = 0, win_rate: float = 0.0) -> dict:
    address = raw.get("proxyWallet") or raw.get("address") or ""
    name = raw.get("name") or raw.get("pseudonym") or (address[:10] + "..." if address else "Unknown")
    avatar_url = raw.get("profileImageOptimized") or raw.get("profileImage") or _blockies_url(address)
    profit = raw.get("pnl") or raw.get("profit") or 0.0
    raw_wr = raw.get("winRate") or raw.get("win_rate") or win_rate
    if raw_wr <= 1.0:
        raw_wr = round(float(raw_wr) * 100, 1)
    else:
        raw_wr = round(float(raw_wr), 1)

    return {
        "address": address,
        "name": name,
        "profit_usd": round(float(profit), 2),
        "win_rate": raw_wr,
        "total_bets": int(raw.get("numTrades") or raw.get("total_bets") or trade_count),
        "volume_usd": round(float(raw.get("volume") or volume), 2),
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
        "market_slug": raw.get("slug") or raw.get("eventSlug") or "",
    }


async def get_leaderboard(sort_by: str = "profit", limit: int = 100) -> list[dict]:
    """
    Build a leaderboard from recent global trades.
    Aggregates by proxyWallet, sorts by volume (most active bettors).
    Fetches 1000 recent trades to build a meaningful list.
    """
    fetch_limit = min(max(limit * 10, 500), 1000)
    params = {"limit": fetch_limit}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/trades", params=params)
            resp.raise_for_status()
            trades = resp.json()
            if not isinstance(trades, list):
                trades = []
        except Exception:
            trades = []

    # Aggregate by wallet
    users: dict[str, dict] = {}
    for t in trades:
        addr = t.get("proxyWallet") or ""
        if not addr:
            continue
        if addr not in users:
            users[addr] = {
                "proxyWallet": addr,
                "name": t.get("name") or t.get("pseudonym") or "",
                "profileImage": t.get("profileImageOptimized") or t.get("profileImage") or "",
                "volume": 0.0,
                "trades": 0,
                "wins": 0,
            }
        size = float(t.get("usdcSize") or t.get("size") or 0)
        users[addr]["volume"] += size
        users[addr]["trades"] += 1

    # Sort
    sort_key = "volume"  # trades is the only reliable metric from public API
    sorted_users = sorted(users.values(), key=lambda x: x[sort_key], reverse=True)[:limit]

    result = []
    for u in sorted_users:
        win_rate = (u["wins"] / u["trades"] * 100) if u["trades"] > 0 else 0.0
        result.append(_normalise_profile(u, volume=u["volume"], trade_count=u["trades"], win_rate=win_rate))

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

    # Pull name/avatar from first trade record
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
