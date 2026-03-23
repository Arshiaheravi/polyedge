from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import BetEvent, BettorFollow, User

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


def verify_admin(x_admin_password: str = Header(...)):
    if x_admin_password != settings.admin_password:
        raise HTTPException(status_code=403, detail="Invalid admin password")


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _=Depends(verify_admin)):
    total_users = db.query(User).count()
    free_users = db.query(User).filter(User.subscription_tier == "free").count()
    basic_users = db.query(User).filter(User.subscription_tier == "basic").count()
    vip_users = db.query(User).filter(User.subscription_tier == "vip").count()
    total_follows = db.query(BettorFollow).count()
    total_bet_events = db.query(BetEvent).count()
    notified_events = db.query(BetEvent).filter(BetEvent.notified == True).count()

    return {
        "users": {
            "total": total_users,
            "free": free_users,
            "basic": basic_users,
            "vip": vip_users,
        },
        "follows": {"total": total_follows},
        "bet_events": {
            "total": total_bet_events,
            "notified": notified_events,
        },
        "mrr_estimate": basic_users * 4.99 + vip_users * 14.99,
    }
