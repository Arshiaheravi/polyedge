import json
import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import AlertSetting, User

router = APIRouter(prefix="/alerts", tags=["alerts"])
settings = get_settings()


class AlertSettingsUpdate(BaseModel):
    web_push_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    push_subscription: Optional[str] = None  # JSON string from browser


class TelegramVerifyRequest(BaseModel):
    code: str


@router.get("/settings")
def get_alert_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(AlertSetting).filter(AlertSetting.user_id == current_user.id).first()
    if not alert:
        alert = AlertSetting(user_id=current_user.id)
        db.add(alert)
        db.commit()
        db.refresh(alert)

    return {
        "web_push_enabled": alert.web_push_enabled,
        "telegram_enabled": alert.telegram_enabled,
        "push_subscription": json.loads(alert.push_subscription) if alert.push_subscription else None,
        "telegram_verified": current_user.telegram_verified,
        "telegram_chat_id": current_user.telegram_chat_id,
    }


@router.put("/settings")
def update_alert_settings(
    payload: AlertSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Telegram requires VIP or Basic
    if payload.telegram_enabled and current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="Telegram alerts require Basic or VIP tier")

    alert = db.query(AlertSetting).filter(AlertSetting.user_id == current_user.id).first()
    if not alert:
        alert = AlertSetting(user_id=current_user.id)
        db.add(alert)

    if payload.web_push_enabled is not None:
        alert.web_push_enabled = payload.web_push_enabled
    if payload.telegram_enabled is not None:
        alert.telegram_enabled = payload.telegram_enabled
    if payload.push_subscription is not None:
        # Accept either a dict or a JSON string from the frontend
        if isinstance(payload.push_subscription, dict):
            alert.push_subscription = json.dumps(payload.push_subscription)
        else:
            alert.push_subscription = payload.push_subscription

    db.commit()
    db.refresh(alert)

    return {
        "web_push_enabled": alert.web_push_enabled,
        "telegram_enabled": alert.telegram_enabled,
        "telegram_verified": current_user.telegram_verified,
    }


@router.post("/telegram/start")
def telegram_start(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="Telegram alerts require Basic or VIP tier")

    code = secrets.token_hex(4).upper()  # 8-char hex code like "A3F2B190"
    current_user.telegram_verify_code = code
    db.commit()

    bot_username = "PolyEdgeBot"  # Replace with your actual bot username
    return {
        "code": code,
        "instructions": f"Send this code to @{bot_username} on Telegram: /verify {code}",
        "bot_link": f"https://t.me/{bot_username}",
    }


@router.post("/telegram/verify")
def telegram_verify(
    payload: TelegramVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.telegram_verify_code:
        raise HTTPException(status_code=400, detail="No pending verification. Start the process first.")

    if payload.code.upper().strip() != current_user.telegram_verify_code.upper().strip():
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Code matches — mark as verified (chat_id would be set by the bot webhook)
    current_user.telegram_verified = True
    current_user.telegram_verify_code = None
    db.commit()

    return {"verified": True, "message": "Telegram linked successfully"}
