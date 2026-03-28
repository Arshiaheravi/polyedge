"""
Playwright E2E: Leaderboard period filter (Today/Week/Month/All Time) switches correctly.

Verifies:
  - On load, #period-month has 'active' class (the default period)
  - After calling loadLeaderboard(currentSort, 'week'), #period-week gains 'active'
    and #period-month loses it
  - Bettor cards still render after the period switch (no blank/crash state)

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


def _open_leaderboard_tab(page: Page) -> None:
    """Navigate to the leaderboard tab and wait for initial data load."""
    page.evaluate("showTab('leaderboard')")
    page.wait_for_function(
        "!document.getElementById('tab-leaderboard').classList.contains('hidden')",
        timeout=8_000,
    )
    page.wait_for_load_state("networkidle", timeout=10_000)


class TestPeriodFilter:
    """Leaderboard period filter must switch active state and re-render cards."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_period_month_active_by_default(self, page: Page):
        """#period-month must have 'active' class when leaderboard first loads."""
        login(page, "basic")
        _open_leaderboard_tab(page)

        is_active = page.evaluate(
            "() => document.getElementById('period-month')?.classList.contains('active')"
        )
        assert is_active, (
            "#period-month does not have 'active' class after initial leaderboard load — "
            "default period is not 'month'"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_period_week_becomes_active_after_switch(self, page: Page):
        """After loadLeaderboard(currentSort, 'week'), #period-week must be active and #period-month inactive."""
        login(page, "basic")
        _open_leaderboard_tab(page)

        # Switch to week period via JS (same as clicking the Week button)
        page.evaluate("loadLeaderboard(currentSort, 'week')")
        page.wait_for_load_state("networkidle", timeout=10_000)

        week_active = page.evaluate(
            "() => document.getElementById('period-week')?.classList.contains('active')"
        )
        month_active = page.evaluate(
            "() => document.getElementById('period-month')?.classList.contains('active')"
        )

        assert week_active, (
            "#period-week does not have 'active' class after switching to week period"
        )
        assert not month_active, (
            "#period-month still has 'active' class after switching to week — old active state not cleared"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_period_switch_does_not_blank_cards(self, page: Page):
        """After a period switch, leaderboard cards must still be present (no blank/crash state)."""
        login(page, "basic")
        _open_leaderboard_tab(page)

        # Switch to 'all' period
        page.evaluate("loadLeaderboard(currentSort, 'all')")
        page.wait_for_load_state("networkidle", timeout=10_000)

        card_count = page.evaluate(
            "() => document.querySelectorAll('.lb-card').length"
        )
        assert card_count > 0, (
            f"No .lb-card elements found after switching to 'all' period — "
            f"leaderboard may have crashed or returned empty"
        )
