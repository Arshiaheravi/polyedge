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
from app.services.notifications import send_sms

router = APIRouter(prefix="/alerts", tags=["alerts"])
settings = get_settings()


class AlertSettingsUpdate(BaseModel):
    web_push_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_subscription: Optional[str] = None  # JSON string from browser


class TelegramVerifyRequest(BaseModel):
    code: str


class PhoneSaveRequest(BaseModel):
    phone_number: str  # E.164 format: +14155552671


class PhoneVerifyRequest(BaseModel):
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
        "sms_enabled": alert.sms_enabled,
        "push_subscription": json.loads(alert.push_subscription) if alert.push_subscription else None,
        "telegram_verified": current_user.telegram_verified,
        "telegram_chat_id": current_user.telegram_chat_id,
        "phone_number": current_user.phone_number,
        "phone_verified": current_user.phone_verified,
    }


@router.put("/settings")
def update_alert_settings(
    payload: AlertSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Tier checks
    if payload.telegram_enabled and current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="Telegram alerts require Basic or VIP tier")
    if payload.sms_enabled and current_user.subscription_tier != "vip":
        raise HTTPException(status_code=403, detail="SMS alerts require VIP tier")
    if payload.sms_enabled and not current_user.phone_verified:
        raise HTTPException(status_code=400, detail="Verify your phone number before enabling SMS alerts")

    alert = db.query(AlertSetting).filter(AlertSetting.user_id == current_user.id).first()
    if not alert:
        alert = AlertSetting(user_id=current_user.id)
        db.add(alert)

    if payload.web_push_enabled is not None:
        alert.web_push_enabled = payload.web_push_enabled
    if payload.telegram_enabled is not None:
        alert.telegram_enabled = payload.telegram_enabled
    if payload.sms_enabled is not None:
        alert.sms_enabled = payload.sms_enabled
    if payload.push_subscription is not None:
        if isinstance(payload.push_subscription, dict):
            alert.push_subscription = json.dumps(payload.push_subscription)
        else:
            alert.push_subscription = payload.push_subscription

    db.commit()
    db.refresh(alert)

    return {
        "web_push_enabled": alert.web_push_enabled,
        "telegram_enabled": alert.telegram_enabled,
        "sms_enabled": alert.sms_enabled,
        "telegram_verified": current_user.telegram_verified,
        "phone_verified": current_user.phone_verified,
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


# ── SMS / Phone routes ──────────────────────────────────────────

@router.post("/sms/start")
async def sms_start(
    payload: PhoneSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save phone number and send a 6-digit OTP via SMS. VIP only."""
    if current_user.subscription_tier != "vip":
        raise HTTPException(status_code=403, detail="SMS alerts require VIP tier")

    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        raise HTTPException(status_code=503, detail="SMS service not configured. Add Twilio credentials to .env")

    phone = payload.phone_number.strip()
    if not phone.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must be in E.164 format: +14155552671")

    code = str(secrets.randbelow(900000) + 100000)  # 6-digit OTP
    current_user.phone_number = phone
    current_user.phone_verified = False
    current_user.phone_verify_code = code
    db.commit()

    message = f"Your PolyEdge verification code is: {code}"
    ok = await send_sms(phone, message, settings.twilio_account_sid, settings.twilio_auth_token, settings.twilio_from_number)
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to send SMS. Check your Twilio credentials and phone number.")

    return {"sent": True, "message": f"OTP sent to {phone}"}


@router.post("/sms/verify")
def sms_verify(
    payload: PhoneVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify the 6-digit OTP to confirm phone ownership."""
    if not current_user.phone_verify_code:
        raise HTTPException(status_code=400, detail="No pending verification. Start the process first.")

    if payload.code.strip() != current_user.phone_verify_code.strip():
        raise HTTPException(status_code=400, detail="Invalid verification code")

    current_user.phone_verified = True
    current_user.phone_verify_code = None
    db.commit()

    return {"verified": True, "message": "Phone number verified successfully"}
