"""
Tests for app/database.py — covers the get_db() generator (lines 20-24).
Uses mocked SessionLocal to avoid file-system dependencies.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.database import get_db


def test_get_db_yields_session():
    """get_db() yields the SessionLocal instance and closes it when the generator is closed."""
    mock_session = MagicMock()
    with patch("app.database.SessionLocal", return_value=mock_session):
        gen = get_db()
        db = next(gen)

        assert db is mock_session

        gen.close()  # triggers the finally: db.close() block

    mock_session.close.assert_called_once()


def test_get_db_closes_on_exception():
    """get_db() calls db.close() in finally block even when the consumer raises."""
    mock_session = MagicMock()
    with patch("app.database.SessionLocal", return_value=mock_session):
        gen = get_db()
        next(gen)

        with pytest.raises(RuntimeError):
            gen.throw(RuntimeError("boom"))

    mock_session.close.assert_called_once()
