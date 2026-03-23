from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import BettorFollow, User

router = APIRouter(prefix="/follows", tags=["follows"])

TIER_LIMITS = {
    "free": 0,
    "basic": 5,
    "vip": 999999,
}


class FollowRequest(BaseModel):
    bettor_address: str
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

    if max_follows == 0:
        raise HTTPException(
            status_code=403,
            detail="Free tier cannot follow bettors. Upgrade to Basic or VIP.",
        )

    current_count = (
        db.query(BettorFollow).filter(BettorFollow.user_id == current_user.id).count()
    )

    if current_count >= max_follows:
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
    return None
