import asyncio
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user_optional
from app.models import User
from app.services.polymarket import get_bettor_profile, get_leaderboard, get_recent_bets, get_live_trades, compute_copy_simulator

router = APIRouter(prefix="/bettors", tags=["bettors"])

_leaderboard_cache: dict = {"data": None, "ts": 0, "sort": None}
_profile_cache: dict = {}
_trades_cache: dict = {"data": None, "ts": 0}
CACHE_TTL = 600  # 10 minutes
TRADES_TTL = 30  # 30 seconds — live ticker


@router.get("")
async def list_bettors(
    sort: str = Query("profit", enum=["profit", "volume"]),
    time_period: str = Query("month", enum=["day", "week", "month", "all"]),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    now = time.time()
    cache_key = f"{sort}_{time_period}_{limit}"

    cached = _leaderboard_cache.get(cache_key)
    if cached and (now - cached["ts"]) < CACHE_TTL:
        return {"bettors": cached["data"], "cached": True}

    try:
        data = await get_leaderboard(sort_by=sort, time_period=time_period, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Polymarket API error: {str(exc)}")

    _leaderboard_cache[cache_key] = {"data": data, "ts": now}
    return {"bettors": data, "cached": False}


@router.get("/trades/recent")
async def recent_trades(limit: int = Query(20, ge=5, le=50)):
    """Live feed of recent global Polymarket trades — powers the ticker."""
    now = time.time()
    if _trades_cache["data"] and (now - _trades_cache["ts"]) < TRADES_TTL:
        return {"trades": _trades_cache["data"], "cached": True}

    try:
        data = await get_live_trades(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Polymarket API error: {str(exc)}")

    _trades_cache["data"] = data
    _trades_cache["ts"] = now
    return {"trades": data, "cached": False}


@router.get("/{address}")
async def bettor_detail(
    address: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    now = time.time()
    # Cache key must include tier — VIP gets unlocked simulator, free gets locked.
    # Caching by address alone would serve a VIP response to free users (paywall bypass).
    tier = getattr(current_user, "subscription_tier", "free") if current_user else "free"
    cache_key = (address, tier)
    cache_entry = _profile_cache.get(cache_key)
    if cache_entry and (now - cache_entry["ts"]) < CACHE_TTL:
        return cache_entry["data"]

    try:
        profile, bets, simulator_raw = await asyncio.gather(
            get_bettor_profile(address),
            get_recent_bets(address, limit=20),
            compute_copy_simulator(address, limit=10),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Polymarket API error: {str(exc)}")

    # Tier-gate the simulator: Free users see locked=True placeholder
    if tier in ("basic", "vip"):
        copy_simulator = simulator_raw
    else:
        copy_simulator = {"locked": True}

    result = {"profile": profile, "recent_bets": bets, "copy_simulator": copy_simulator}
    _profile_cache[cache_key] = {"data": result, "ts": now}
    return result
