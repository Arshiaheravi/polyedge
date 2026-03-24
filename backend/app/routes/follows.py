import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import BettorFollow, User
from app.services.polymarket import get_active_positions

router = APIRouter(prefix="/follows", tags=["follows"])

_activity_cache: dict = {}   # keyed by user_id
ACTIVITY_TTL = 30            # seconds

TIER_LIMITS = {
    "free": 1,
    "basic": 5,
    "vip": 999999,
}


class FollowRequest(BaseModel):
    bettor_address: str = Field(..., min_length=1)
    bettor_name: str = ""


@router.get("")
def list_follows(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follows = (
        db.query(BettorFollow)
        .filter(BettorFollow.user_id == current_user.id)
        .order_by(BettorFollow.created_at.desc())
        .all()
    )
    return {
        "follows": [
            {
                "id": f.id,
                "bettor_address": f.bettor_address,
                "bettor_name": f.bettor_name,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in follows
        ],
        "tier": current_user.subscription_tier,
        "limit": TIER_LIMITS.get(current_user.subscription_tier, 0),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def add_follow(
    payload: FollowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tier = current_user.subscription_tier
    max_follows = TIER_LIMITS.get(tier, 0)

    current_count = (
        db.query(BettorFollow).filter(BettorFollow.user_id == current_user.id).count()
    )

    if current_count >= max_follows:
        if tier == "free":
            raise HTTPException(
                status_code=403,
                detail="Free tier allows 1 follow. Upgrade to Basic for 5 or VIP for unlimited.",
            )
        raise HTTPException(
            status_code=403,
            detail=f"{tier.title()} tier allows max {max_follows} follows. Upgrade to VIP for unlimited.",
        )

    existing = (
        db.query(BettorFollow)
        .filter(
            BettorFollow.user_id == current_user.id,
            BettorFollow.bettor_address == payload.bettor_address,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already following this bettor")

    follow = BettorFollow(
        user_id=current_user.id,
        bettor_address=payload.bettor_address,
        bettor_name=payload.bettor_name or payload.bettor_address[:12] + "...",
    )
    db.add(follow)
    db.commit()
    db.refresh(follow)

    return {
        "id": follow.id,
        "bettor_address": follow.bettor_address,
        "bettor_name": follow.bettor_name,
        "created_at": follow.created_at.isoformat() if follow.created_at else None,
    }


@router.get("/live")
async def follows_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns two things for the logged-in user's followed bettors:
      - recent_bets: last 5 trades per followed bettor (sorted newest first)
      - active_positions: open unredeemed positions per followed bettor

    Cached 30 seconds per user to avoid hammering the Polymarket API.
    """
    now = time.time()
    cached = _activity_cache.get(current_user.id)
    if cached and (now - cached["ts"]) < ACTIVITY_TTL:
        return cached["data"]

    follows = (
        db.query(BettorFollow)
        .filter(BettorFollow.user_id == current_user.id)
        .all()
    )

    if not follows:
        result = {"bettors": []}
        _activity_cache[current_user.id] = {"data": result, "ts": now}
        return result

    async def _fetch_one(follow: BettorFollow):
        addr = follow.bettor_address
        try:
            positions = await get_active_positions(addr)
        except Exception:
            positions = []
        return {
            "address": addr,
            "name": follow.bettor_name or addr[:12] + "...",
            "followed_at": follow.created_at.isoformat() if follow.created_at else None,
            "active_positions": positions,
        }

    bettors = await asyncio.gather(*[_fetch_one(f) for f in follows])
    result = {"bettors": list(bettors)}
    _activity_cache[current_user.id] = {"data": result, "ts": now}
    return result


@router.delete("/{bettor_address}", status_code=status.HTTP_204_NO_CONTENT)
def remove_follow(
    bettor_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow = (
        db.query(BettorFollow)
        .filter(
            BettorFollow.user_id == current_user.id,
            BettorFollow.bettor_address == bettor_address,
        )
        .first()
    )
    if not follow:
        raise HTTPException(status_code=404, detail="Follow not found")

    db.delete(follow)
    db.commit()
    _activity_cache.pop(current_user.id, None)
    return None
