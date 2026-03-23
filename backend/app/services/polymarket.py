"""
Polymarket API client.
All functions are async and return normalised Python dicts ready for the API response.
"""
from typing import Optional

import httpx

BASE_URL = "https://data-api.polymarket.com"
GAMMA_URL = "https://gamma-api.polymarket.com"

_SORT_MAP = {
    "profit": "profit",
    "accuracy": "pnl",       # closest available
    "volume": "volume",
}

TIMEOUT = 15.0


def _normalise_profile(raw: dict) -> dict:
    """Flatten/rename Polymarket profile fields into consistent shape."""
    address = raw.get("proxyWallet") or raw.get("address") or raw.get("id") or ""
    name = raw.get("name") or raw.get("pseudonym") or (address[:10] + "..." if address else "Unknown")
    profit = raw.get("pnl") or raw.get("profit") or 0.0
    volume = raw.get("volume") or 0.0
    win_rate = raw.get("winRate") or raw.get("win_rate") or 0.0
    total_bets = raw.get("numTrades") or raw.get("total_bets") or 0
    avatar_url = raw.get("profileImage") or raw.get("avatar") or _blockies_url(address)

    return {
        "address": address,
        "name": name,
        "profit_usd": round(float(profit), 2),
        "win_rate": round(float(win_rate) * 100, 1) if win_rate <= 1.0 else round(float(win_rate), 1),
        "total_bets": int(total_bets),
        "volume_usd": round(float(volume), 2),
        "avatar_url": avatar_url,
    }


def _blockies_url(address: str) -> str:
    """Return a deterministic avatar URL using DiceBear based on the address."""
    seed = address.lower() if address else "unknown"
    return f"https://api.dicebear.com/7.x/identicon/svg?seed={seed}"


def _normalise_bet(raw: dict) -> dict:
    """Normalise a single bet/activity entry."""
    return {
        "market_id": raw.get("conditionId") or raw.get("market_id") or raw.get("marketId") or "",
        "market_question": raw.get("title") or raw.get("question") or raw.get("market_question") or "Unknown Market",
        "outcome": raw.get("outcome") or raw.get("side") or raw.get("outcomeIndex") or "",
        "amount_usd": round(float(raw.get("usdcSize") or raw.get("amount") or raw.get("size") or 0), 2),
        "timestamp": raw.get("timestamp") or raw.get("createdAt") or raw.get("created_at") or "",
        "price": round(float(raw.get("price") or 0), 4),
        "type": raw.get("type") or raw.get("side") or "buy",
    }


async def get_leaderboard(sort_by: str = "profit", limit: int = 100) -> list[dict]:
    """Fetch top bettors from Polymarket data API."""
    sort_param = _SORT_MAP.get(sort_by, "profit")
    params = {"limit": limit, "sortBy": sort_param, "offset": 0}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/profiles", params=params)
            resp.raise_for_status()
            raw_list = resp.json()
            if isinstance(raw_list, dict):
                raw_list = raw_list.get("data") or raw_list.get("profiles") or []
        except httpx.HTTPStatusError as exc:
            # Try gamma API as fallback
            resp2 = await client.get(
                f"{GAMMA_URL}/users",
                params={"limit": limit, "order": sort_param, "ascending": "false"},
            )
            resp2.raise_for_status()
            raw_list = resp2.json()
            if isinstance(raw_list, dict):
                raw_list = raw_list.get("data") or raw_list.get("users") or []
        except Exception:
            raw_list = []

    return [_normalise_profile(p) for p in raw_list if isinstance(p, dict)]


async def get_bettor_profile(address: str) -> dict:
    """Get a specific bettor's profile."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/profiles/{address}")
            resp.raise_for_status()
            raw = resp.json()
            if isinstance(raw, list) and raw:
                raw = raw[0]
        except Exception:
            raw = {"address": address}

    return _normalise_profile(raw)


async def get_recent_bets(address: str, limit: int = 20) -> list[dict]:
    """Get recent bets/activity for a specific address."""
    params = {"user": address, "limit": limit}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{BASE_URL}/activity", params=params)
            resp.raise_for_status()
            raw_list = resp.json()
            if isinstance(raw_list, dict):
                raw_list = raw_list.get("data") or raw_list.get("activity") or []
        except Exception:
            # Try alternate endpoint
            try:
                resp2 = await client.get(
                    f"{BASE_URL}/trades",
                    params={"maker": address, "limit": limit},
                )
                resp2.raise_for_status()
                raw_list = resp2.json()
                if isinstance(raw_list, dict):
                    raw_list = raw_list.get("data") or raw_list.get("trades") or []
            except Exception:
                raw_list = []

    return [_normalise_bet(b) for b in raw_list if isinstance(b, dict)]
