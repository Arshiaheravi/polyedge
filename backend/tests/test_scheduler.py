"""Tests for scheduler — _parse_timestamp and _poll_bets logic."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.services.scheduler as scheduler_module
from app.auth import hash_password
from app.config import get_settings
from app.database import Base
from app.models import BetEvent, BettorFollow, User
from app.services.scheduler import _parse_timestamp, _poll_bets, _poll_vip_bets


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sched_db(tmp_path):
    """File-based SQLite so two sessions (test + scheduler) share the same DB."""
    db_path = tmp_path / "sched_test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session, Session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_last_check():
    """Set _last_check to a known past time before each test and restore after."""
    original = scheduler_module._last_check
    scheduler_module._last_check = datetime(2000, 1, 1, tzinfo=timezone.utc)
    yield
    scheduler_module._last_check = original


@pytest.fixture(autouse=True)
def reset_last_positions():
    """Clear _last_positions before and after each test to prevent state bleed."""
    scheduler_module._last_positions.clear()
    yield
    scheduler_module._last_positions.clear()


# Helper: run an async coroutine synchronously in tests.
def run(coro):
    return asyncio.run(coro)


# ── _parse_timestamp ──────────────────────────────────────────────────────────


def test_parse_timestamp_none():
    assert _parse_timestamp(None) is None


def test_parse_timestamp_empty_string():
    assert _parse_timestamp("") is None


def test_parse_timestamp_unix_int():
    dt = _parse_timestamp(1700000000)
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_timestamp_unix_float():
    dt = _parse_timestamp(1700000000.5)
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_timestamp_iso_z():
    dt = _parse_timestamp("2024-01-15T10:00:00Z")
    assert dt is not None
    assert dt.year == 2024
    assert dt.tzinfo is not None


def test_parse_timestamp_iso_with_microseconds():
    dt = _parse_timestamp("2024-01-15T10:00:00.123456Z")
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_timestamp_iso_with_offset():
    dt = _parse_timestamp("2024-01-15T10:00:00+00:00")
    assert dt is not None
    assert dt.tzinfo is not None


def test_parse_timestamp_datetime_naive():
    naive_dt = datetime(2024, 1, 15, 10, 0, 0)
    result = _parse_timestamp(naive_dt)
    assert result is not None
    assert result.tzinfo is not None


def test_parse_timestamp_datetime_aware():
    aware_dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    result = _parse_timestamp(aware_dt)
    assert result == aware_dt


def test_parse_timestamp_invalid_string():
    assert _parse_timestamp("not-a-date") is None


# ── _poll_bets ────────────────────────────────────────────────────────────────

# Timestamp safely in the future so it's always newer than _last_check.
FUTURE_TS = datetime(2099, 1, 1, tzinfo=timezone.utc)

SAMPLE_BET = {
    "timestamp": FUTURE_TS,
    "market_id": "mkt1",
    "market_question": "Will X happen?",
    "outcome": "Yes",
    "amount_usd": 50.0,
}


def test_poll_bets_no_follows_skips_api(sched_db):
    """If no BettorFollow rows exist, poll returns without calling the API."""
    _, Session = sched_db

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock()) as mock_fetch:
        run(_poll_bets())

    mock_fetch.assert_not_called()


def test_poll_bets_creates_bet_event(sched_db):
    """A new bet from Polymarket is saved as a BetEvent."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_bets())

    # Use a fresh session to avoid identity-map cache
    verify = Session()
    events = verify.query(BetEvent).all()
    verify.close()

    assert len(events) == 1
    assert events[0].market_id == "mkt1"
    assert events[0].bettor_address == "0xabc"
    assert events[0].notified is True


def test_poll_bets_skips_old_bets(sched_db):
    """Bets with timestamp <= _last_check are ignored."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc"))
    session.commit()

    old_bet = dict(SAMPLE_BET, timestamp=datetime(1999, 1, 1, tzinfo=timezone.utc))

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[old_bet])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())

    verify = Session()
    count = verify.query(BetEvent).count()
    verify.close()

    assert count == 0
    mock_notify.assert_not_called()


def test_poll_bets_skips_duplicate_bet(sched_db):
    """A bet already in BetEvent table is not re-inserted and triggers no notification."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc"))
    # Pre-existing event for this exact bet
    session.add(BetEvent(
        bettor_address="0xabc", market_id="mkt1",
        market_question="Will X happen?", outcome="Yes",
        amount_usd=50.0, timestamp=FUTURE_TS, notified=True,
    ))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())

    verify = Session()
    count = verify.query(BetEvent).count()
    verify.close()

    assert count == 1  # no new row
    mock_notify.assert_not_called()


def test_poll_bets_no_notification_for_free_tier(sched_db):
    """Free tier followers get a BetEvent saved but do NOT receive a notification."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="free",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())

    verify = Session()
    events = verify.query(BetEvent).all()
    verify.close()

    assert len(events) == 1
    mock_notify.assert_not_called()


def test_poll_bets_dispatches_notification_for_basic_user(sched_db):
    """Basic tier followers trigger dispatch_bet_notification."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())

    mock_notify.assert_called_once()


def test_poll_bets_bet_event_all_fields_correct(sched_db):
    """BetEvent row stores all fields from the bet dict with correct values."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_bets())

    verify = Session()
    event = verify.query(BetEvent).first()
    verify.close()

    assert event is not None
    assert event.bettor_address == "0xabc"
    assert event.market_id == "mkt1"
    assert event.market_question == "Will X happen?"
    assert event.outcome == "Yes"
    assert event.amount_usd == 50.0
    # SQLite strips tzinfo on round-trip; compare naive-normalised values
    stored_naive = event.timestamp.replace(tzinfo=None) if event.timestamp.tzinfo else event.timestamp
    assert stored_naive == FUTURE_TS.replace(tzinfo=None)


def test_poll_bets_bet_event_missing_fields_use_defaults(sched_db):
    """BetEvent fields default to empty string / 0.0 when bet dict is missing keys."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc"))
    session.commit()

    sparse_bet = {"timestamp": FUTURE_TS}  # only timestamp — everything else absent

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[sparse_bet])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_bets())

    verify = Session()
    event = verify.query(BetEvent).first()
    verify.close()

    assert event is not None
    assert event.bettor_address == "0xabc"
    assert event.market_id == ""
    assert event.market_question == ""
    assert event.outcome == ""
    assert event.amount_usd == 0.0


def test_poll_bets_bet_event_timestamp_timezone_aware(sched_db):
    """BetEvent timestamp stored from a Unix integer is timezone-aware."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc"))
    session.commit()

    # Use a Unix timestamp far in the future so it passes the _last_check guard
    unix_ts = 9_999_999_999  # year 2286
    unix_bet = dict(SAMPLE_BET, timestamp=unix_ts)

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[unix_bet])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_bets())

    verify = Session()
    event = verify.query(BetEvent).first()
    verify.close()

    assert event is not None
    expected = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    # SQLite strips tzinfo on round-trip; compare naive-normalised values
    stored_naive = event.timestamp.replace(tzinfo=None) if event.timestamp.tzinfo else event.timestamp
    expected_naive = expected.replace(tzinfo=None)
    assert stored_naive == expected_naive


def test_poll_bets_api_error_continues_to_next_address(sched_db):
    """If Polymarket API fails for one address, polling continues for the remaining ones."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xfail"))
    session.add(BettorFollow(user_id=user.id, bettor_address="0xok"))
    session.commit()

    good_bet = dict(SAMPLE_BET, bettor_address="0xok")

    async def mock_get_bets(address, limit=10):
        if address == "0xfail":
            raise Exception("API timeout")
        return [good_bet]

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=mock_get_bets), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_bets())

    verify = Session()
    events = verify.query(BetEvent).filter(BetEvent.bettor_address == "0xok").all()
    verify.close()

    assert len(events) == 1


def test_poll_bets_api_returns_none_does_not_crash(sched_db):
    """If get_recent_bets returns None instead of a list, _poll_bets handles it gracefully."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xnone"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=None)), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())  # must not raise

    verify = Session()
    count = verify.query(BetEvent).count()
    verify.close()

    assert count == 0
    mock_notify.assert_not_called()


def test_parse_timestamp_overflow_int_returns_none():
    """An integer too large for fromtimestamp() causes OverflowError, caught → None."""
    result = _parse_timestamp(10**20)  # far beyond valid Unix timestamp range
    assert result is None


def test_poll_bets_inactive_user_is_skipped(sched_db):
    """A follower with is_active=False is not notified — dispatch never called."""
    session, Session = sched_db

    user = User(
        email="inactive@x.com", hashed_password=hash_password("p"),
        name="Inactive", subscription_tier="basic", is_active=False,
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())

    mock_notify.assert_not_called()


def test_poll_bets_orphaned_follow_is_skipped(sched_db):
    """A BettorFollow whose user_id has no matching User row is skipped gracefully."""
    session, Session = sched_db

    # Insert follow with user_id 99999 — no User with that id exists
    session.add(BettorFollow(user_id=99999, bettor_address="0xorphan", bettor_name="ghost"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())  # must not raise

    mock_notify.assert_not_called()


def test_poll_bets_dispatches_with_telegram_chat_id_when_enabled(sched_db):
    """When a basic user has telegram_enabled=True and telegram_verified=True,
    dispatch_bet_notification is called with the user's telegram_chat_id, not None."""
    from app.models import AlertSetting
    session, Session = sched_db

    user = User(
        email="tg@x.com", hashed_password=hash_password("p"),
        name="TG", subscription_tier="basic",
        telegram_chat_id="chat_12345",
        telegram_verified=True,
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xtg", bettor_name="tgwhale"))
    alert = AlertSetting(user_id=user.id, telegram_enabled=True, web_push_enabled=False)
    session.add(alert)
    session.commit()

    mock_dispatch = AsyncMock()
    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=mock_dispatch):
        run(_poll_bets())

    mock_dispatch.assert_called_once()
    call_kwargs = mock_dispatch.call_args[1]
    assert call_kwargs["telegram_chat_id"] == "chat_12345"


def test_poll_bets_multiple_followers_each_notified(sched_db):
    """When two users follow the same bettor, dispatch_bet_notification is called once per follower."""
    session, Session = sched_db

    user_a = User(email="a@x.com", hashed_password=hash_password("p"), name="A", subscription_tier="basic")
    user_b = User(email="b@x.com", hashed_password=hash_password("p"), name="B", subscription_tier="vip")
    session.add(user_a)
    session.add(user_b)
    session.flush()
    session.add(BettorFollow(user_id=user_a.id, bettor_address="0xshared", bettor_name="whale"))
    session.add(BettorFollow(user_id=user_b.id, bettor_address="0xshared", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_bets())

    assert mock_notify.call_count == 2


def test_poll_bets_dispatches_both_channels_when_both_enabled(sched_db):
    """When a user has BOTH telegram_enabled AND web_push_enabled, dispatch is called
    with both telegram_chat_id and push_subscription_json set simultaneously."""
    from app.models import AlertSetting
    session, Session = sched_db

    push_sub = '{"endpoint": "https://push.example.com/sub123"}'
    user = User(
        email="both@x.com", hashed_password=hash_password("p"),
        name="Both", subscription_tier="basic",
        telegram_chat_id="chat_both999",
        telegram_verified=True,
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xboth", bettor_name="dualwhale"))
    alert = AlertSetting(
        user_id=user.id,
        telegram_enabled=True,
        web_push_enabled=True,
        push_subscription=push_sub,
    )
    session.add(alert)
    session.commit()

    mock_dispatch = AsyncMock()
    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=mock_dispatch):
        run(_poll_bets())

    mock_dispatch.assert_called_once()
    call_kwargs = mock_dispatch.call_args[1]
    assert call_kwargs["telegram_chat_id"] == "chat_both999"
    assert call_kwargs["push_subscription_json"] == push_sub


def test_poll_bets_dispatches_web_push_only_when_telegram_disabled(sched_db):
    """When telegram_enabled=False but web_push_enabled=True, dispatch is called
    with push_subscription_json set but telegram_chat_id=None."""
    from app.models import AlertSetting
    session, Session = sched_db

    push_sub = '{"endpoint": "https://push.example.com/webonly"}'
    user = User(
        email="webonly@x.com", hashed_password=hash_password("p"),
        name="WebOnly", subscription_tier="basic",
        telegram_chat_id="chat_webonly",
        telegram_verified=True,
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xwebonly", bettor_name="webwhale"))
    alert = AlertSetting(
        user_id=user.id,
        telegram_enabled=False,
        web_push_enabled=True,
        push_subscription=push_sub,
    )
    session.add(alert)
    session.commit()

    mock_dispatch = AsyncMock()
    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=mock_dispatch):
        run(_poll_bets())

    mock_dispatch.assert_called_once()
    call_kwargs = mock_dispatch.call_args[1]
    assert call_kwargs["telegram_chat_id"] is None
    assert call_kwargs["push_subscription_json"] == push_sub


def test_poll_bets_dispatch_exception_does_not_crash_poll_loop(sched_db):
    """If dispatch_bet_notification raises, the exception is caught, the poll continues,
    and event.notified is still set to True (the bet was seen, just not notified)."""
    session, Session = sched_db

    user = User(
        email="u@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xabc", bettor_name="whale"))
    session.commit()

    failing_dispatch = AsyncMock(side_effect=RuntimeError("simulated dispatch failure"))
    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=failing_dispatch):
        run(_poll_bets())  # must not raise

    verify = Session()
    events = verify.query(BetEvent).all()
    verify.close()

    assert len(events) == 1
    assert events[0].notified is True  # event marked notified even though dispatch failed


def test_poll_bets_dispatches_sms_for_vip_user(sched_db):
    """Scheduler passes phone_number and sms_enabled=True to dispatch when
    the user is VIP tier with phone_verified=True and alert.sms_enabled=True."""
    from app.models import AlertSetting

    session, Session = sched_db

    user = User(
        email="vipsms@x.com", hashed_password=hash_password("p"),
        name="VipSms", subscription_tier="vip",
        phone_number="+14155559999",
        phone_verified=True,
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xvipsms", bettor_name="smswhale"))
    alert = AlertSetting(
        user_id=user.id,
        telegram_enabled=False,
        web_push_enabled=False,
        sms_enabled=True,
    )
    session.add(alert)
    session.commit()

    mock_dispatch = AsyncMock()
    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=mock_dispatch):
        run(_poll_bets())

    mock_dispatch.assert_called_once()
    call_kwargs = mock_dispatch.call_args[1]
    assert call_kwargs["phone_number"] == "+14155559999"
    assert call_kwargs["sms_enabled"] is True


def test_poll_bets_last_check_updated_after_poll(sched_db):
    """After _poll_bets() completes, scheduler._last_check must be updated to
    the check_time captured at the start of the poll — not left at the
    autouse-reset value of datetime(2000, 1, 1)."""
    session, Session = sched_db

    user = User(
        email="lcupdate@x.com", hashed_password=hash_password("p"),
        name="LCUser", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xlcaddr", bettor_name="whale"))
    session.commit()

    # Capture a lower bound for the expected _last_check value
    before_poll = datetime.now(tz=timezone.utc)

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[])):
        run(_poll_bets())

    assert scheduler_module._last_check >= before_poll, (
        f"_last_check was not updated: got {scheduler_module._last_check!r}, "
        f"expected >= {before_poll!r}"
    )


def test_poll_bets_multiple_bets_per_address_all_saved(sched_db):
    """When get_recent_bets returns 2 new bets for the same address, both are
    saved as BetEvent rows.  The inner `for bet in bets:` loop must not
    short-circuit after the first hit."""
    session, Session = sched_db

    user = User(
        email="multi@x.com", hashed_password=hash_password("p"),
        name="Multi", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xmulti", bettor_name="whale"))
    session.commit()

    bet1 = dict(SAMPLE_BET, market_id="mkt_a", timestamp=datetime(2099, 1, 1, tzinfo=timezone.utc))
    bet2 = dict(SAMPLE_BET, market_id="mkt_b", timestamp=datetime(2099, 1, 2, tzinfo=timezone.utc))

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[bet1, bet2])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_bets())

    verify = Session()
    events = verify.query(BetEvent).all()
    verify.close()

    assert len(events) == 2
    market_ids = {e.market_id for e in events}
    assert market_ids == {"mkt_a", "mkt_b"}


def test_poll_bets_outer_exception_leaves_last_check_unchanged(sched_db):
    """When db.commit() raises, the outer except fires and _last_check must NOT advance.
    _last_check = check_time is placed AFTER db.commit(), so any exception there
    must leave _last_check at its pre-poll value — preventing bets from being skipped
    on the next run."""
    session, Session = sched_db

    user = User(
        email="outerexc@x.com", hashed_password=hash_password("p"),
        name="OE", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xoeaddr", bettor_name="whale"))
    session.commit()

    # Wrap a real session but override commit() to raise
    inner = Session()

    def _fail_commit():
        raise RuntimeError("forced commit failure")

    inner.commit = _fail_commit

    def failing_factory():
        return inner

    before = scheduler_module._last_check  # datetime(2000,1,1,utc) from autouse fixture

    with patch("app.services.scheduler.SessionLocal", failing_factory), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[])):
        run(_poll_bets())

    assert scheduler_module._last_check == before, (
        f"_last_check should not advance after outer exception; "
        f"got {scheduler_module._last_check!r}, expected {before!r}"
    )


# ── _detect_exits ─────────────────────────────────────────────────────────────

from app.services.scheduler import _detect_exits  # noqa: E402


SAMPLE_POSITION = {
    "condition_id": "cid_abc",
    "market_title": "Will X happen?",
    "outcome": "Yes",
    "size": 10.0,
    "current_value_usd": 8.0,
    "initial_value_usd": 10.0,
    "avg_price": 0.5,
    "cur_price": 0.55,
    "copy_value_pct": 10.0,
    "copy_signal": "fair",
    "cash_pnl": -2.0,
    "percent_pnl": -20.0,
    "end_date": "",
    "poly_url": "https://polymarket.com",
    "icon": "",
}


def test_detect_exits_first_run_no_event(sched_db):
    """First poll for an address — no previous positions, so no exit events stored."""
    session, Session = sched_db

    user = User(email="ex@x.com", hashed_password=hash_password("p"), name="Ex", subscription_tier="vip")
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xexit", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.get_active_positions", new=AsyncMock(return_value=[SAMPLE_POSITION])):
        run(_detect_exits(session, ["0xexit"]))
    session.commit()

    verify = Session()
    events = verify.query(BetEvent).filter(BetEvent.event_type == "EXIT").all()
    verify.close()
    assert len(events) == 0
    # Position map should now be recorded
    assert "0xexit" in scheduler_module._last_positions
    assert scheduler_module._last_positions["0xexit"]["cid_abc"] == 10.0


def test_detect_exits_position_gone_creates_exit_event(sched_db):
    """When a conditionId present in _last_positions is gone in the current poll, an EXIT BetEvent is created."""
    session, Session = sched_db

    user = User(email="ex@x.com", hashed_password=hash_password("p"), name="Ex", subscription_tier="vip")
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xexit", bettor_name="whale"))
    session.commit()

    # Pre-seed last_positions: bettor had cid_abc
    scheduler_module._last_positions["0xexit"] = {"cid_abc": 10.0}

    # Current positions: empty (position closed)
    with patch("app.services.scheduler.get_active_positions", new=AsyncMock(return_value=[])), \
         patch("app.services.scheduler.send_telegram", new=AsyncMock()), \
         patch("app.services.scheduler.send_web_push", new=AsyncMock()):
        run(_detect_exits(session, ["0xexit"]))
    session.commit()

    verify = Session()
    events = verify.query(BetEvent).filter(BetEvent.event_type == "EXIT").all()
    verify.close()
    assert len(events) == 1
    assert events[0].bettor_address == "0xexit"
    assert events[0].market_id == "cid_abc"


def test_detect_exits_size_reduced_50pct_creates_exit_event(sched_db):
    """When a position's size drops by more than 50%, an EXIT BetEvent is stored."""
    session, Session = sched_db

    user = User(email="ex2@x.com", hashed_password=hash_password("p"), name="Ex2", subscription_tier="vip")
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xreduce", bettor_name="whale"))
    session.commit()

    scheduler_module._last_positions["0xreduce"] = {"cid_abc": 10.0}
    reduced_position = dict(SAMPLE_POSITION, size=4.0)  # 4 < 10 * 0.5 = 5 → exit

    with patch("app.services.scheduler.get_active_positions", new=AsyncMock(return_value=[reduced_position])), \
         patch("app.services.scheduler.send_telegram", new=AsyncMock()), \
         patch("app.services.scheduler.send_web_push", new=AsyncMock()):
        run(_detect_exits(session, ["0xreduce"]))
    session.commit()

    verify = Session()
    events = verify.query(BetEvent).filter(BetEvent.event_type == "EXIT").all()
    verify.close()
    assert len(events) == 1


def test_detect_exits_size_unchanged_no_exit_event(sched_db):
    """When a position's size is unchanged, no EXIT BetEvent is created."""
    session, Session = sched_db

    user = User(email="ex3@x.com", hashed_password=hash_password("p"), name="Ex3", subscription_tier="vip")
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xhold", bettor_name="whale"))
    session.commit()

    scheduler_module._last_positions["0xhold"] = {"cid_abc": 10.0}
    same_position = dict(SAMPLE_POSITION, size=10.0)  # unchanged

    with patch("app.services.scheduler.get_active_positions", new=AsyncMock(return_value=[same_position])):
        run(_detect_exits(session, ["0xhold"]))
    session.commit()

    verify = Session()
    events = verify.query(BetEvent).filter(BetEvent.event_type == "EXIT").all()
    verify.close()
    assert len(events) == 0


def test_detect_exits_only_notifies_vip(sched_db):
    """EXIT notifications are only sent to VIP-tier users — basic and free users are skipped."""
    from app.models import AlertSetting
    session, Session = sched_db

    vip_user = User(
        email="vip@x.com", hashed_password=hash_password("p"), name="VIP",
        subscription_tier="vip", telegram_chat_id="chat_vip", telegram_verified=True,
    )
    basic_user = User(
        email="basic@x.com", hashed_password=hash_password("p"), name="Basic",
        subscription_tier="basic", telegram_chat_id="chat_basic", telegram_verified=True,
    )
    session.add(vip_user)
    session.add(basic_user)
    session.flush()

    for u in [vip_user, basic_user]:
        session.add(BettorFollow(user_id=u.id, bettor_address="0xmixed", bettor_name="whale"))
        session.add(AlertSetting(user_id=u.id, telegram_enabled=True))
    session.commit()

    scheduler_module._last_positions["0xmixed"] = {"cid_abc": 10.0}

    mock_telegram = AsyncMock()
    with patch("app.services.scheduler.get_active_positions", new=AsyncMock(return_value=[])), \
         patch("app.services.scheduler.send_telegram", new=mock_telegram), \
         patch("app.services.scheduler.send_web_push", new=AsyncMock()):
        run(_detect_exits(session, ["0xmixed"]))

    # Only 1 Telegram call — to VIP, not basic
    assert mock_telegram.call_count == 1
    call_args = mock_telegram.call_args[0]
    assert call_args[0] == "chat_vip"  # chat_id arg


def test_detect_exits_api_error_skips_address(sched_db):
    """If get_active_positions raises, the address is skipped and no BetEvent is stored."""
    session, Session = sched_db

    user = User(email="ex4@x.com", hashed_password=hash_password("p"), name="Ex4", subscription_tier="vip")
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xfail", bettor_name="whale"))
    session.commit()

    scheduler_module._last_positions["0xfail"] = {"cid_abc": 10.0}

    with patch("app.services.scheduler.get_active_positions", new=AsyncMock(side_effect=Exception("API error"))):
        run(_detect_exits(session, ["0xfail"]))  # must not raise
    session.commit()

    verify = Session()
    events = verify.query(BetEvent).filter(BetEvent.event_type == "EXIT").all()
    verify.close()
    assert len(events) == 0


def test_poll_bets_purges_stale_last_positions(sched_db):
    """When a bettor is no longer followed, _poll_bets purges its _last_positions entry.

    Scenario:
    - _last_positions contains "0xstale" (a previously-followed bettor now unfollowed).
    - DB has a different bettor "0xactive" still followed by a user.
    - After _poll_bets runs, "0xstale" must be gone from _last_positions.
    """
    session, Session = sched_db

    user = User(
        email="purge@x.com", hashed_password=hash_password("p"),
        name="U", subscription_tier="basic",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xactive"))
    session.commit()

    # Pre-seed stale entry for a bettor that is no longer followed
    scheduler_module._last_positions["0xstale"] = {"cid_old": 5.0}

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[])):
        run(_poll_bets())

    assert "0xstale" not in scheduler_module._last_positions


def test_vip_poll_interval_config():
    """VIP poll interval is 5s and default poll interval is 30s."""
    cfg = get_settings()
    assert cfg.vip_poll_interval_seconds == 5
    assert cfg.default_poll_interval_seconds == 30


# ── _poll_vip_bets behavioural ────────────────────────────────────────────────


def test_poll_vip_bets_no_vip_users_skips_api(sched_db):
    """When no VIP users exist in DB, _poll_vip_bets returns without calling Polymarket.

    Scenario: only free/basic users are in DB → early-return guard fires and
    get_recent_bets must never be called.
    """
    session, Session = sched_db

    # Free user with a follow — but no VIP users
    user = User(
        email="free_vip@x.com", hashed_password=hash_password("p"),
        name="FreeUser", subscription_tier="free",
    )
    session.add(user)
    session.flush()
    session.add(BettorFollow(user_id=user.id, bettor_address="0xfreeaddr", bettor_name="whale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock()) as mock_fetch:
        run(_poll_vip_bets())

    mock_fetch.assert_not_called()


def test_poll_vip_bets_only_polls_vip_followed_addresses(sched_db):
    """_poll_vip_bets only fetches bets for addresses followed by VIP users.

    A free-user-only followed address (0xfreeonly) must NOT be polled.
    The VIP-followed address (0xvipaddr) MUST be polled exactly once.
    """
    session, Session = sched_db

    free_user = User(
        email="free2@x.com", hashed_password=hash_password("p"),
        name="FreeUser2", subscription_tier="free",
    )
    vip_user = User(
        email="vip2@x.com", hashed_password=hash_password("p"),
        name="VipUser2", subscription_tier="vip",
    )
    session.add_all([free_user, vip_user])
    session.flush()
    # Free user follows 0xfreeonly; VIP user follows 0xvipaddr
    session.add(BettorFollow(user_id=free_user.id, bettor_address="0xfreeonly"))
    session.add(BettorFollow(user_id=vip_user.id, bettor_address="0xvipaddr"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[])) as mock_fetch, \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()):
        run(_poll_vip_bets())

    polled = [call.args[0] for call in mock_fetch.call_args_list]
    assert "0xvipaddr" in polled, "VIP-followed address must be polled"
    assert "0xfreeonly" not in polled, "Free-only-followed address must NOT be polled by VIP fast-path"


def test_poll_vip_bets_new_bet_creates_event_and_notifies_vip_follower(sched_db):
    """New bet on a VIP-followed address is saved as BetEvent and VIP follower is notified.

    Mirrors test_poll_bets_creates_bet_event but for the VIP fast-path.
    """
    session, Session = sched_db

    vip_user = User(
        email="vip3@x.com", hashed_password=hash_password("p"),
        name="VipUser3", subscription_tier="vip",
    )
    session.add(vip_user)
    session.flush()
    session.add(BettorFollow(user_id=vip_user.id, bettor_address="0xvip3", bettor_name="bigwhale"))
    session.commit()

    with patch("app.services.scheduler.SessionLocal", Session), \
         patch("app.services.scheduler.get_recent_bets", new=AsyncMock(return_value=[SAMPLE_BET])), \
         patch("app.services.scheduler.dispatch_bet_notification", new=AsyncMock()) as mock_notify:
        run(_poll_vip_bets())

    verify = Session()
    events = verify.query(BetEvent).all()
    verify.close()

    assert len(events) == 1, "BetEvent must be created for the new bet"
    assert events[0].bettor_address == "0xvip3"
    assert events[0].market_id == "mkt1"
    assert events[0].notified is True
    assert mock_notify.call_count == 1, "dispatch_bet_notification must fire for the VIP follower"


def test_start_scheduler_registers_two_jobs():
    """start_scheduler registers both poll_bets (30s) and poll_vip_bets (5s) jobs."""
    import app.services.scheduler as sched_mod
    from app.services.scheduler import start_scheduler

    # Patch .start() so APScheduler doesn't need a running event loop in tests
    with patch.object(sched_mod.AsyncIOScheduler, "start"):
        scheduler = start_scheduler()

    job_ids = {job.id for job in scheduler.get_jobs()}
    assert "poll_bets" in job_ids
    assert "poll_vip_bets" in job_ids

    jobs = {job.id: job for job in scheduler.get_jobs()}
    assert jobs["poll_vip_bets"].trigger.interval.total_seconds() == 5
    assert jobs["poll_bets"].trigger.interval.total_seconds() == 30

    # Reset module-level _scheduler so other tests aren't affected
    sched_mod._scheduler = None
