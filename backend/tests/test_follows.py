"""Tests for /follows endpoints and tier limits."""

BETTOR_A = "0xabc123"
BETTOR_B = "0xdef456"


def test_list_follows_empty(client, auth_headers):
    resp = client.get("/follows", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["follows"] == []
    assert resp.json()["tier"] == "free"
    assert resp.json()["limit"] == 1


def test_follow_bettor(client, auth_headers):
    resp = client.post("/follows", json={"bettor_address": BETTOR_A, "bettor_name": "Alpha"},
                       headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["bettor_address"] == BETTOR_A


def test_free_tier_follow_limit(client, auth_headers):
    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    # Second follow should fail for free tier
    resp = client.post("/follows", json={"bettor_address": BETTOR_B}, headers=auth_headers)
    assert resp.status_code == 403
    assert "1 follow" in resp.json()["detail"] or "Upgrade" in resp.json()["detail"]


def test_duplicate_follow_rejected(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"  # need headroom to reach the dup check
    db.commit()

    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    resp = client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    assert resp.status_code == 409


def test_duplicate_follow_detail_message(client, db, auth_headers, registered_user):
    """409 response must include an actionable detail message so the user knows why it failed."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    resp = client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    assert resp.status_code == 409
    assert "Already following" in resp.json()["detail"]


def test_unfollow(client, auth_headers):
    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    resp = client.delete(f"/follows/{BETTOR_A}", headers=auth_headers)
    assert resp.status_code == 204

    # Should be gone
    resp = client.get("/follows", headers=auth_headers)
    assert resp.json()["follows"] == []


def test_unfollow_nonexistent(client, auth_headers):
    resp = client.delete("/follows/0xnonexistent", headers=auth_headers)
    assert resp.status_code == 404


def test_basic_tier_allows_5_follows(client, db, auth_headers, registered_user):
    from app.models import User
    _, user_data = registered_user
    # Upgrade to basic in DB
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    addresses = [f"0x{i:040x}" for i in range(5)]
    for addr in addresses:
        resp = client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)
        assert resp.status_code == 201

    # 6th should fail
    resp = client.post("/follows", json={"bettor_address": "0xextra"}, headers=auth_headers)
    assert resp.status_code == 403


def test_follows_require_auth(client):
    resp = client.get("/follows")
    assert resp.status_code == 403


def test_basic_tier_limit_error_message(client, db, auth_headers, registered_user):
    """When basic user hits the 5-follow cap, error message mentions VIP upgrade."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    for i in range(5):
        client.post("/follows", json={"bettor_address": f"0x{i:040x}"}, headers=auth_headers)

    resp = client.post("/follows", json={"bettor_address": "0xextra"}, headers=auth_headers)
    assert resp.status_code == 403
    assert "VIP" in resp.json()["detail"]


def test_follow_bettor_name_defaults_to_truncated_address(client, auth_headers):
    """When bettor_name is omitted, stored name defaults to address[:12]+'...'."""
    addr = "0xabcdefghij1234567890"
    resp = client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["bettor_name"] == addr[:12] + "..."


def test_follows_list_contains_bettor_fields(client, auth_headers):
    """GET /follows returns bettor_address and bettor_name for each follow."""
    client.post("/follows",
                json={"bettor_address": BETTOR_A, "bettor_name": "Alpha Trader"},
                headers=auth_headers)
    resp = client.get("/follows", headers=auth_headers)
    assert resp.status_code == 200
    follows = resp.json()["follows"]
    assert len(follows) == 1
    assert follows[0]["bettor_address"] == BETTOR_A
    assert follows[0]["bettor_name"] == "Alpha Trader"
    assert "created_at" in follows[0]


def test_delete_follows_requires_auth(client):
    """DELETE /follows/{address} without a token returns 403, not 500."""
    resp = client.delete("/follows/0xsomeaddress")
    assert resp.status_code == 403


def test_post_follows_requires_auth(client):
    """POST /follows without an auth token returns 403, not 201 or 500."""
    resp = client.post("/follows", json={"bettor_address": "0xtest"})
    assert resp.status_code == 403


def test_post_follows_response_body_includes_all_fields(client, auth_headers):
    """POST /follows response body includes id, bettor_address, bettor_name, and created_at."""
    resp = client.post("/follows",
                       json={"bettor_address": BETTOR_A, "bettor_name": "AlphaTrader"},
                       headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["bettor_address"] == BETTOR_A
    assert data["bettor_name"] == "AlphaTrader"
    assert "created_at" in data


def test_post_follows_empty_bettor_address_rejected(client, auth_headers):
    """POST /follows with empty bettor_address string must return 422 (not create a follow)."""
    resp = client.post("/follows", json={"bettor_address": ""}, headers=auth_headers)
    assert resp.status_code == 422


def test_free_tier_duplicate_at_limit_returns_403_not_409(client, auth_headers):
    """When a free-tier user is already at their follow limit and tries to re-follow the same
    bettor, they must get 403 (tier limit hit), NOT 409 (duplicate), because the count check
    happens before the duplicate check in add_follow()."""
    # Free tier: add the one allowed follow
    client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    # Try to re-follow the same bettor — count is now at max, so 403 fires before the 409 check
    resp = client.post("/follows", json={"bettor_address": BETTOR_A}, headers=auth_headers)
    assert resp.status_code == 403


def test_delete_follow_by_different_user_returns_404(client, db):
    """User B cannot delete User A's follow — the route filters by current_user.id."""
    from app.auth import hash_password, create_access_token
    from app.models import BettorFollow, User

    # Create user A and have them follow a bettor
    user_a = User(email="usera@x.com", hashed_password=hash_password("p"), name="A")
    db.add(user_a)
    db.flush()
    db.add(BettorFollow(user_id=user_a.id, bettor_address="0xshared_bettor", bettor_name="whale"))
    db.commit()

    # Create user B with their own token
    user_b = User(email="userb@x.com", hashed_password=hash_password("p"), name="B")
    db.add(user_b)
    db.commit()
    token_b = create_access_token(data={"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B tries to delete user A's follow — must get 404
    resp = client.delete("/follows/0xshared_bettor", headers=headers_b)
    assert resp.status_code == 404


def test_delete_follow_success_response_body_is_empty(client, auth_headers):
    """DELETE /follows/{address} returns 204 NO CONTENT — response body must be empty bytes."""
    client.post("/follows", json={"bettor_address": "0xbody_check"}, headers=auth_headers)
    resp = client.delete("/follows/0xbody_check", headers=auth_headers)
    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_follow_not_found_detail_message(client, auth_headers):
    """DELETE /follows/{address} for an address not followed returns 404 with exact detail."""
    resp = client.delete("/follows/0xnever_followed_addr", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Follow not found"



def test_post_follows_unknown_subscription_tier_is_blocked(client, db, auth_headers, registered_user):
    """A user with an unrecognised subscription tier (not free/basic/vip) can never add a follow.
    TIER_LIMITS.get(unknown_tier, 0) returns 0, so current_count (0) >= max_follows (0) is True
    and the route raises 403 immediately."""
    from app.models import User
    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "enterprise"  # not in TIER_LIMITS
    db.commit()

    resp = client.post("/follows", json={"bettor_address": "0xtest_unknown_tier"}, headers=auth_headers)
    assert resp.status_code == 403


def test_vip_tier_can_add_six_plus_follows(client, db, auth_headers, registered_user):
    """VIP tier has no artificial cap — 6+ follows succeed.
    TIER_LIMITS["vip"] = 999999 means any real-world usage is well within limit.
    GET /follows also reports tier='vip' and limit=999999 for VIP users."""
    from app.models import User

    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "vip"
    db.commit()

    for i in range(6):
        resp = client.post("/follows", json={"bettor_address": f"0xvip{i}"}, headers=auth_headers)
        assert resp.status_code == 201, f"Follow {i} failed: {resp.json()}"

    list_resp = client.get("/follows", headers=auth_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["tier"] == "vip"
    assert data["limit"] == 999999
    assert len(data["follows"]) == 6


def test_delete_follow_url_encoded_slash_in_address_returns_404(client, auth_headers):
    """DELETE /follows/0x%2Ftest — TestClient sends the literal %2F in the path; Starlette
    decodes it to '/' giving bettor_address='0x/test'. No follow exists → 404, not 500 or 422."""
    resp = client.delete("/follows/0x%2Ftest", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_follow_unencoded_slash_in_path_returns_404(client, auth_headers):
    """DELETE /follows/0x/test — unencoded slash creates an extra path segment.
    Route /follows/{bettor_address} is single-segment; multi-segment path returns 404, not 500 or 422."""
    resp = client.delete("/follows/0x/test", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_follow_with_multiple_follows_removes_only_correct_one(client, db, auth_headers, registered_user):
    """DELETE /follows/{address} with 2 follows must remove only the targeted address.
    Guards against accidental cascade deletes that would remove all follows."""
    from app.models import User

    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"  # basic allows 5 follows
    db.commit()

    client.post("/follows", json={"bettor_address": "0xaaa_multi", "bettor_name": "alpha"},
                headers=auth_headers)
    client.post("/follows", json={"bettor_address": "0xbbb_multi", "bettor_name": "beta"},
                headers=auth_headers)

    del_resp = client.delete("/follows/0xaaa_multi", headers=auth_headers)
    assert del_resp.status_code == 204

    list_resp = client.get("/follows", headers=auth_headers)
    addresses = [f["bettor_address"] for f in list_resp.json()["follows"]]
    assert "0xbbb_multi" in addresses
    assert "0xaaa_multi" not in addresses


def test_follows_list_order_is_newest_first(client, db, auth_headers, registered_user):
    """GET /follows returns follows ordered newest-first (created_at DESC).

    Directly sets created_at timestamps after DB insert to guarantee a deterministic
    ordering gap — avoids flakiness from fast execution collapsing timestamps to same second.
    """
    from datetime import datetime, timedelta, timezone
    from app.models import BettorFollow, User

    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "basic"
    db.commit()

    addresses = ["0xorder_first", "0xorder_second", "0xorder_third"]
    for addr in addresses:
        client.post("/follows", json={"bettor_address": addr}, headers=auth_headers)

    # Assign explicit created_at values so order is unambiguous
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    follows = (
        db.query(BettorFollow)
        .filter(BettorFollow.user_id == user.id)
        .order_by(BettorFollow.id)
        .all()
    )
    assert len(follows) == 3
    follows[0].created_at = now - timedelta(hours=2)   # oldest
    follows[1].created_at = now - timedelta(hours=1)   # middle
    follows[2].created_at = now                        # newest
    db.commit()

    resp = client.get("/follows", headers=auth_headers)
    assert resp.status_code == 200
    result = resp.json()["follows"]
    assert len(result) == 3

    # First item must have the most recent created_at
    ts0 = result[0]["created_at"]
    ts1 = result[1]["created_at"]
    ts2 = result[2]["created_at"]
    assert ts0 > ts1 > ts2, (
        f"Follows not ordered newest-first: {ts0} > {ts1} > {ts2} violated"
    )


def test_get_follows_unknown_tier_returns_limit_zero(client, db, auth_headers, registered_user):
    """GET /follows for a user with an unrecognised tier returns limit=0.
    TIER_LIMITS.get("enterprise", 0) == 0; tier field reflects the actual DB value."""
    from app.models import User

    _, user_data = registered_user
    user = db.query(User).filter(User.id == user_data["id"]).first()
    user.subscription_tier = "enterprise"
    db.commit()

    resp = client.get("/follows", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "enterprise"
    assert data["limit"] == 0
    assert data["follows"] == []


def test_free_tier_error_message_mentions_basic_upgrade(client, auth_headers):
    """Free-tier error message must specifically mention the Basic upgrade path.

    Mutation kill: `if tier == "free":` → `if tier != "free":` routes free users to the
    generic message "Upgrade to VIP for unlimited." instead of the specific message
    "Upgrade to Basic for 5 or VIP for unlimited." Both contain "Upgrade" so the weaker
    assertion in test_free_tier_follow_limit survives the mutation. Asserting "Basic" kills it.
    """
    client.post("/follows", json={"bettor_address": "0xfirst"}, headers=auth_headers)
    resp = client.post("/follows", json={"bettor_address": "0xsecond"}, headers=auth_headers)
    assert resp.status_code == 403
    detail = resp.json()["detail"]
    assert "Basic" in detail, (
        f"Free-tier error must mention Basic upgrade path; got: '{detail}'"
    )
