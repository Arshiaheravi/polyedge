import time
from typing import Optional

from fastapi import APIRouter, Depends

from app.auth import get_current_user_optional
from app.models import User
from app.services.polymarket import get_consensus_signals

router = APIRouter(prefix="/markets", tags=["markets"])

_consensus_cache: dict = {"data": None, "ts": 0}
CONSENSUS_TTL = 300  # 5 minutes — fetching 100 bettors' positions is expensive


@router.get("/consensus")
async def consensus(
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Markets where 3+ top-100 bettors hold the same outcome.

    Tier rules:
    - Free / unauthenticated: top 3 consensus markets only, whale_names hidden (empty list)
    - Basic: all markets, whale_names hidden
    - VIP: all markets, whale_names visible
    """
    now = time.time()
    if _consensus_cache["data"] and (now - _consensus_cache["ts"]) < CONSENSUS_TTL:
        signals = _consensus_cache["data"]
    else:
        signals = await get_consensus_signals(min_whales=3)
        _consensus_cache["data"] = signals
        _consensus_cache["ts"] = now

    tier = (current_user.subscription_tier if current_user else "free") or "free"
    show_names = tier == "vip"
    limit = None if tier in ("basic", "vip") else 3

    result = []
    for s in (signals[:limit] if limit else signals):
        result.append({
            "market_title": s["market_title"],
            "condition_id": s["condition_id"],
            "outcome": s["outcome"],
            "whale_count": s["whale_count"],
            "avg_entry_price": s["avg_entry_price"],
            "current_price": s["current_price"],
            "whale_names": s["whale_names"] if show_names else [],
            "event_slug": s["event_slug"],
        })

    return {
        "signals": result,
        "total_available": len(signals),
        "tier": tier,
        "names_visible": show_names,
    }
