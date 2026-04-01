"""
Stripe checkout and webhook handling.
"""
import logging

import stripe
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

PLAN_PRICE_MAP = {
    "basic": settings.stripe_basic_price_id,
    "vip": settings.stripe_vip_price_id,
}

PLAN_TIER_MAP = {
    "basic": "basic",
    "vip": "vip",
}


def _get_stripe_client():
    stripe.api_key = settings.stripe_secret_key
    return stripe


async def create_checkout_session(user: User, plan: str, db: Session) -> str:
    """Create a Stripe Checkout Session and return the URL."""
    s = _get_stripe_client()

    price_id = PLAN_PRICE_MAP.get(plan)
    if not price_id:
        raise ValueError(f"No Stripe price ID configured for plan: {plan}")

    # Create or retrieve Stripe customer
    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = s.Customer.create(email=user.email, name=user.name, metadata={"user_id": str(user.id)})
        customer_id = customer["id"]
        user.stripe_customer_id = customer_id
        db.commit()

    session = s.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.frontend_url}?checkout=success&plan={plan}",
        cancel_url=f"{settings.frontend_url}?checkout=cancelled",
        metadata={"user_id": str(user.id), "plan": plan},
    )
    return session["url"]


async def create_billing_portal_session(customer_id: str) -> str:
    """Create a Stripe Billing Portal session and return the URL."""
    s = _get_stripe_client()
    session = s.billing_portal.Session.create(
        customer=customer_id,
        return_url=settings.frontend_url,
    )
    return session["url"]


async def handle_webhook_event(payload: bytes, sig_header: str, db: Session) -> None:
    """Process a Stripe webhook event."""
    s = _get_stripe_client()

    if settings.stripe_webhook_secret:
        try:
            event = s.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
        except stripe.error.SignatureVerificationError as exc:
            raise ValueError(f"Webhook signature verification failed: {exc}")
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data_object, db)

    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        _handle_subscription_change(data_object, db)

    elif event_type == "invoice.payment_failed":
        logger.warning("Payment failed for customer: %s", data_object.get("customer"))


def _handle_checkout_completed(session: dict, db: Session) -> None:
    user_id = session.get("metadata", {}).get("user_id")
    plan = session.get("metadata", {}).get("plan")
    subscription_id = session.get("subscription")

    if not user_id or not plan:
        return

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return

    new_tier = PLAN_TIER_MAP.get(plan, "basic")
    user.subscription_tier = new_tier
    if subscription_id:
        user.stripe_subscription_id = subscription_id
    db.commit()
    logger.info("User %s upgraded to %s", user_id, new_tier)


def _handle_subscription_change(subscription: dict, db: Session) -> None:
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
    if not user:
        return

    if status in ("canceled", "unpaid", "past_due"):
        user.subscription_tier = "free"
        db.commit()
        logger.info("User %s downgraded to free (subscription %s)", user.id, status)
    elif status == "active":
        # Determine plan from subscription items
        items = subscription.get("items", {}).get("data", [])
        for item in items:
            price_id = item.get("price", {}).get("id")
            if price_id == settings.stripe_basic_price_id:
                user.subscription_tier = "basic"
            elif price_id == settings.stripe_vip_price_id:
                user.subscription_tier = "vip"
        db.commit()
