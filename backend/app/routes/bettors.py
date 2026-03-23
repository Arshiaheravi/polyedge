import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import get_current_user
from app.models import User
from app.services.polymarket import get_bettor_profile, get_leaderboard, get_recent_bets

router = APIRouter(prefix="/bettors", tags=["bettors"])

_leaderboard_cache: dict = {"data": None, "ts": 0, "sort": None}
_profile_cache: dict = {}
CACHE_TTL = 600  # 10 minutes


@router.get("")
async def list_bettors(
    sort: str = Query("profit", enum=["profit", "accuracy", "volume"]),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
):
    now = time.time()
    cache_key = f"{sort}_{limit}"

    cached = _leaderboard_cache.get(cache_key)
    if cached and (now - cached["ts"]) < CACHE_TTL:
        return {"bettors": cached["data"], "cached": True}

    try:
        data = await get_leaderboard(sort_by=sort, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Polymarket API error: {str(exc)}")

    _leaderboard_cache[cache_key] = {"data": data, "ts": now}
    return {"bettors": data, "cached": False}


@router.get("/{address}")
async def bettor_detail(
    address: str,
    current_user: Optional[User] = Depends(get_current_user),
):
    now = time.time()
    cache_entry = _profile_cache.get(address)
    if cache_entry and (now - cache_entry["ts"]) < CACHE_TTL:
        return cache_entry["data"]

    try:
        profile = await get_bettor_profile(address)
        bets = await get_recent_bets(address, limit=20)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Polymarket API error: {str(exc)}")

    result = {"profile": profile, "recent_bets": bets}
    _profile_cache[address] = {"data": result, "ts": now}
    return result
