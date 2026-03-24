"""Unit tests for stripe_service — checkout, portal, webhook handling."""
import json
import pytest
from unittest.mock import MagicMock, patch


# ── create_checkout_session ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_checkout_no_price_id(db):
    """Raises ValueError if price ID not configured for the plan."""
    from app.models import User
    from app.auth import hash_password
    from app.services.stripe_service import create_checkout_session

    user = User(email="co@x.com", hashed_password=hash_password("p"), name="CO")
    db.add(user)
    db.commit()

    with patch("app.services.stripe_service._get_stripe_client") as mock_stripe:
        mock_stripe.return_value = MagicMock()
        # Clear price IDs
        with patch("app.services.stripe_service.PLAN_PRICE_MAP", {"basic": None, "vip": None}):
            with pytest.raises(ValueError, match="No Stripe price ID"):
                await create_checkout_session(user=user, plan="basic", db=db)


@pytest.mark.asyncio
async def test_create_checkout_creates_customer_if_missing(db):
    """Creates a Stripe customer when user doesn't have one yet."""
    from app.models import User
    from app.auth import hash_password
    from app.services.stripe_service import create_checkout_session

    user = User(email="newco@x.com", hashed_password=hash_password("p"), name="New")
    db.add(user)
    db.commit()

    mock_stripe = MagicMock()
    mock_stripe.Customer.create.return_value = {"id": "cus_new123"}
    mock_stripe.checkout.Session.create.return_value = {"url": "https://checkout.stripe.com/pay/test"}

    with patch("app.services.stripe_service._get_stripe_client", return_value=mock_stripe), \
         patch("app.services.stripe_service.PLAN_PRICE_MAP", {"basic": "price_basic", "vip": "price_vip"}):
        url = await create_checkout_session(user=user, plan="basic", db=db)

    assert url == "https://checkout.stripe.com/pay/test"
    mock_stripe.Customer.create.assert_called_once()
    db.refresh(user)
    assert user.stripe_customer_id == "cus_new123"


@pytest.mark.asyncio
async def test_create_checkout_reuses_existing_customer(db):
    """Does not create a new Stripe customer if user already has one."""
    from app.models import User
    from app.auth import hash_password
    from app.services.stripe_service import create_checkout_session

    user = User(email="existing@x.com", hashed_password=hash_password("p"),
                name="Existing", stripe_customer_id="cus_existing")
    db.add(user)
    db.commit()

    mock_stripe = MagicMock()
    mock_stripe.checkout.Session.create.return_value = {"url": "https://checkout.stripe.com/pay/existing"}

    with patch("app.services.stripe_service._get_stripe_client", return_value=mock_stripe), \
         patch("app.services.stripe_service.PLAN_PRICE_MAP", {"basic": "price_basic", "vip": "price_vip"}):
        url = await create_checkout_session(user=user, plan="vip", db=db)

    assert url == "https://checkout.stripe.com/pay/existing"
    mock_stripe.Customer.create.assert_not_called()


# ── handle_webhook_event ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_unknown_event_type_is_ignored(db):
    """Unknown event types are silently ignored (no crash)."""
    from app.services.stripe_service import handle_webhook_event

    event = json.dumps({"type": "payment_intent.created", "data": {"object": {}}}).encode()
    # Should not raise
    await handle_webhook_event(payload=event, sig_header="", db=db)


@pytest.mark.asyncio
async def test_webhook_checkout_unknown_user_is_ignored(db):
    """checkout.session.completed with unknown user_id does nothing."""
    from app.services.stripe_service import handle_webhook_event

    event = json.dumps({
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"user_id": "99999", "plan": "basic"}, "subscription": None}}
    }).encode()
    # Should not raise
    await handle_webhook_event(payload=event, sig_header="", db=db)


@pytest.mark.asyncio
async def test_webhook_subscription_active_upgrades_to_vip(db):
    """customer.subscription.updated with active status and VIP price sets vip tier."""
    from app.models import User
    from app.auth import hash_password
    from app.services.stripe_service import handle_webhook_event

    user = User(email="sub@x.com", hashed_password=hash_password("p"),
                name="Sub", subscription_tier="free", stripe_customer_id="cus_subtest")
    db.add(user)
    db.commit()

    event = json.dumps({
        "type": "customer.subscription.updated",
        "data": {"object": {
            "customer": "cus_subtest",
            "status": "active",
            "items": {"data": [{"price": {"id": "price_vip_id"}}]},
        }}
    }).encode()

    with patch("app.services.stripe_service.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = ""
        mock_settings.stripe_basic_price_id = "price_basic_id"
        mock_settings.stripe_vip_price_id = "price_vip_id"
        await handle_webhook_event(payload=event, sig_header="", db=db)

    db.refresh(user)
    assert user.subscription_tier == "vip"


@pytest.mark.asyncio
async def test_webhook_invoice_payment_failed_does_not_crash(db):
    """invoice.payment_failed is logged but doesn't raise."""
    from app.services.stripe_service import handle_webhook_event

    event = json.dumps({
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_xxx"}}
    }).encode()
    await handle_webhook_event(payload=event, sig_header="", db=db)


# ── Subscription lifecycle — downgrade path ────────────────────────────────────
#
# DOCUMENTED BEHAVIOR: follows are NOT automatically removed on tier downgrade.
# A user who had 8 follows as VIP will still have 8 follows after downgrading.
# They can no longer ADD new follows beyond the new tier's limit, but existing
# follows remain in place and continue to trigger notifications (until manually
# unfollowed or tier is re-upgraded).


@pytest.mark.asyncio
async def test_vip_downgrade_to_free_follows_not_removed(db):
    """
    VIP user with 8 follows is downgraded to free via subscription cancellation.
    EXPECTED: tier becomes 'free', all 8 follows are preserved (no auto-removal).
    """
    from app.models import BettorFollow, User
    from app.auth import hash_password
    from app.services.stripe_service import handle_webhook_event

    user = User(email="vip@x.com", hashed_password=hash_password("p"),
                name="VIP", subscription_tier="vip", stripe_customer_id="cus_vip1")
    db.add(user)
    db.flush()
    for i in range(8):
        db.add(BettorFollow(user_id=user.id, bettor_address=f"0x{i:040x}"))
    db.commit()

    event = json.dumps({
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_vip1", "status": "canceled"}}
    }).encode()
    await handle_webhook_event(payload=event, sig_header="", db=db)

    db.refresh(user)
    follow_count = db.query(BettorFollow).filter(BettorFollow.user_id == user.id).count()

    assert user.subscription_tier == "free"
    assert follow_count == 8  # follows preserved — no auto-removal on downgrade


@pytest.mark.asyncio
async def test_vip_downgrade_to_basic_follows_not_removed(db):
    """
    VIP user with 8 follows is updated to basic plan via subscription update.
    EXPECTED: tier becomes 'basic', all 8 follows are preserved.
    """
    from app.models import BettorFollow, User
    from app.auth import hash_password
    from app.services.stripe_service import handle_webhook_event

    user = User(email="vip2@x.com", hashed_password=hash_password("p"),
                name="VIP2", subscription_tier="vip", stripe_customer_id="cus_vip2")
    db.add(user)
    db.flush()
    for i in range(8):
        db.add(BettorFollow(user_id=user.id, bettor_address=f"0xb{i:039x}"))
    db.commit()

    event = json.dumps({
        "type": "customer.subscription.updated",
        "data": {"object": {
            "customer": "cus_vip2",
            "status": "active",
            "items": {"data": [{"price": {"id": "price_basic_test"}}]},
        }}
    }).encode()

    with patch("app.services.stripe_service.settings") as mock_settings:
        mock_settings.stripe_webhook_secret = ""
        mock_settings.stripe_basic_price_id = "price_basic_test"
        mock_settings.stripe_vip_price_id = "price_vip_test"
        await handle_webhook_event(payload=event, sig_header="", db=db)

    db.refresh(user)
    follow_count = db.query(BettorFollow).filter(BettorFollow.user_id == user.id).count()

    assert user.subscription_tier == "basic"
    assert follow_count == 8  # follows preserved after downgrade to basic


@pytest.mark.asyncio
async def test_downgraded_user_blocked_from_adding_new_follow(client, db):
    """
    After downgrade to basic (already at 8 follows > basic limit of 5),
    POST /follows returns 403 — new follows blocked at the new tier's limit.
    """
    from app.models import BettorFollow, User
    from app.auth import hash_password, create_access_token

    user = User(email="downgraded@x.com", hashed_password=hash_password("p"),
                name="DG", subscription_tier="basic")
    db.add(user)
    db.flush()
    for i in range(5):  # exactly at basic limit
        db.add(BettorFollow(user_id=user.id, bettor_address=f"0xc{i:039x}"))
    db.commit()

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/follows", json={"bettor_address": "0xnewbettor"},
                       headers=headers)
    assert resp.status_code == 403
    assert "Basic" in resp.json()["detail"] or "basic" in resp.json()["detail"].lower()
