"""Tests for scheduler — _parse_timestamp and _poll_bets logic."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.services.scheduler as scheduler_module
from app.auth import hash_password
from app.database import Base
from app.models import BetEvent, BettorFollow, User
from app.services.scheduler import _parse_timestamp, _poll_bets


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
