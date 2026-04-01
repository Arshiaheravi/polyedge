from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.services.stripe_service import (
    create_billing_portal_session,
    create_checkout_session,
    handle_webhook_event,
)

router = APIRouter(prefix="/payments", tags=["payments"])
settings = get_settings()


class CheckoutRequest(BaseModel):
    plan: str  # "basic" or "vip"


@router.post("/checkout")
async def create_checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.plan not in ("basic", "vip"):
        raise HTTPException(status_code=400, detail="Plan must be 'basic' or 'vip'")

    try:
        url = await create_checkout_session(
            user=current_user,
            plan=payload.plan,
            db=db,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(exc)}")

    return {"checkout_url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        await handle_webhook_event(payload=payload, sig_header=sig_header, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return {"status": "ok"}


@router.get("/portal")
async def billing_portal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer found. Subscribe first.")

    try:
        url = await create_billing_portal_session(customer_id=current_user.stripe_customer_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(exc)}")

    return {"portal_url": url}
