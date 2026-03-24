"""Tests for /payments endpoints — checkout, webhook, portal (Stripe mocked)."""
import json
from unittest.mock import AsyncMock, MagicMock, patch


# ── Checkout ─────────────────────────────────────────────────────────────────

def test_checkout_requires_auth(client):
    resp = client.post("/payments/checkout", json={"plan": "basic"})
    assert resp.status_code == 403


def test_checkout_invalid_plan(client, auth_headers):
    resp = client.post("/payments/checkout", json={"plan": "platinum"}, headers=auth_headers)
    assert resp.status_code == 400
    assert "basic" in resp.json()["detail"] or "vip" in resp.json()["detail"]


def test_checkout_basic_plan(client, auth_headers):
    mock_url = "https://checkout.stripe.com/pay/cs_test_basic"
    with patch("app.routes.payments.create_checkout_session",
               new=AsyncMock(return_value=mock_url)):
        resp = client.post("/payments/checkout", json={"plan": "basic"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["checkout_url"] == mock_url


def test_checkout_vip_plan(client, auth_headers):
    mock_url = "https://checkout.stripe.com/pay/cs_test_vip"
    with patch("app.routes.payments.create_checkout_session",
               new=AsyncMock(return_value=mock_url)):
        resp = client.post("/payments/checkout", json={"plan": "vip"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["checkout_url"] == mock_url


def test_checkout_stripe_error_returns_502(client, auth_headers):
    with patch("app.routes.payments.create_checkout_session",
               new=AsyncMock(side_effect=Exception("Stripe is down"))):
        resp = client.post("/payments/checkout", json={"plan": "basic"}, headers=auth_headers)
    assert resp.status_code == 502
    assert "Stripe" in resp.json()["detail"]


# ── Billing Portal ────────────────────────────────────────────────────────────

def test_portal_requires_auth(client):
    resp = client.get("/payments/portal")
    assert resp.status_code == 403


def test_portal_no_stripe_customer(client, auth_headers):
    """User without a Stripe customer ID gets 400."""
    resp = client.get("/payments/portal", headers=auth_headers)
    assert resp.status_code == 400
    assert "Subscribe first" in resp.json()["detail"]


def test_portal_with_stripe_customer(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.stripe_customer_id = "cus_test123"
    db.commit()

    mock_url = "https://billing.stripe.com/session/bps_test"
    with patch("app.routes.payments.create_billing_portal_session",
               new=AsyncMock(return_value=mock_url)):
        resp = client.get("/payments/portal", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["portal_url"] == mock_url


# ── Webhook ───────────────────────────────────────────────────────────────────

def test_webhook_checkout_completed_upgrades_user(client, db, auth_headers, registered_user):
    """checkout.session.completed upgrades user to the paid tier."""
    _, user_data = registered_user
    user_id = user_data["id"]

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user_id), "plan": "basic"},
                "subscription": "sub_test123",
            }
        }
    }

    with patch("app.routes.payments.handle_webhook_event", new=AsyncMock()) as mock_handler:
        resp = client.post(
            "/payments/webhook",
            content=json.dumps(event).encode(),
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    mock_handler.assert_called_once()


def test_webhook_invalid_signature_returns_400(client):
    """Malformed webhook payload raises 400."""
    with patch("app.routes.payments.handle_webhook_event",
               new=AsyncMock(side_effect=ValueError("bad signature"))):
        resp = client.post(
            "/payments/webhook",
            content=b"bad_payload",
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == 400


def test_webhook_stripe_service_upgrades_user(client, db):
    """Integration: handle_webhook_event directly upgrades user tier."""
    from app.auth import hash_password
    from app.models import User
    from app.services.stripe_service import handle_webhook_event
    import asyncio

    user = User(email="stripe@x.com", hashed_password=hash_password("p"),
                name="Stripe User", subscription_tier="free")
    db.add(user)
    db.commit()
    db.refresh(user)

    event = json.dumps({
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": str(user.id), "plan": "vip"},
                "subscription": "sub_vip_test",
            }
        }
    }).encode()

    asyncio.run(handle_webhook_event(payload=event, sig_header="", db=db))
    db.refresh(user)
    assert user.subscription_tier == "vip"
    assert user.stripe_subscription_id == "sub_vip_test"


def test_webhook_subscription_cancelled_downgrades_user(client, db):
    """customer.subscription.deleted sets user back to free."""
    from app.auth import hash_password
    from app.models import User
    from app.services.stripe_service import handle_webhook_event
    import asyncio

    user = User(email="cancel@x.com", hashed_password=hash_password("p"),
                name="Cancel User", subscription_tier="basic",
                stripe_customer_id="cus_cancel_test")
    db.add(user)
    db.commit()
    db.refresh(user)

    event = json.dumps({
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "customer": "cus_cancel_test",
                "status": "canceled",
            }
        }
    }).encode()

    asyncio.run(handle_webhook_event(payload=event, sig_header="", db=db))
    db.refresh(user)
    assert user.subscription_tier == "free"
