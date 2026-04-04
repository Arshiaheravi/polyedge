"""
Playwright E2E: Leaderboard sort toggle switches active button and keeps cards loaded.

Verifies that:
  1. On dashboard load, #sort-profit has the 'active' CSS class.
  2. After switching to volume sort via loadLeaderboard('volume'), #sort-profit loses
     the 'active' class and #sort-volume gains it.
  3. After the sort switch, at least one .lb-card is still present (cards reloaded OK).

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


def _open_leaderboard_tab(page: Page) -> None:
    """Navigate to the dashboard Leaderboard tab and wait for cards to load."""
    page.evaluate("showTab('leaderboard')")
    # Wait for leaderboard tab to become visible
    page.wait_for_function(
        "!document.getElementById('tab-leaderboard').classList.contains('hidden')",
        timeout=8_000,
    )
    # Wait for the API call to /bettors to complete
    page.wait_for_load_state("networkidle", timeout=10_000)


class TestLeaderboardSortToggle:
    """Leaderboard sort pills correctly update active state and reload cards."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_sort_profit_is_active_on_initial_load(self, page: Page):
        """#sort-profit must have the 'active' class when the leaderboard first loads."""
        login(page, "basic")
        _open_leaderboard_tab(page)

        profit_active = page.evaluate(
            "document.getElementById('sort-profit').classList.contains('active')"
        )
        assert profit_active, (
            "#sort-profit should have 'active' class on initial leaderboard load"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_switch_to_volume_sort_changes_active_button(self, page: Page):
        """Switching sort to 'volume' must move the 'active' class from #sort-profit to #sort-volume."""
        login(page, "basic")
        _open_leaderboard_tab(page)

        # Confirm initial state
        profit_active_before = page.evaluate(
            "document.getElementById('sort-profit').classList.contains('active')"
        )
        assert profit_active_before, "Precondition: #sort-profit must be active before sort switch"

        # Switch sort to volume via the same JS function the UI buttons call
        page.evaluate("loadLeaderboard('volume', currentPeriod)")
        page.wait_for_load_state("networkidle", timeout=10_000)

        # #sort-profit must no longer be active
        profit_active_after = page.evaluate(
            "document.getElementById('sort-profit').classList.contains('active')"
        )
        assert not profit_active_after, (
            "#sort-profit should lose 'active' class after switching to volume sort"
        )

        # #sort-volume must now be active
        volume_active = page.evaluate(
            "document.getElementById('sort-volume').classList.contains('active')"
        )
        assert volume_active, (
            "#sort-volume should gain 'active' class after switching to volume sort"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_sort_switch_keeps_cards_loaded(self, page: Page):
        """After switching sort, at least one .lb-card must still be present (no blank state)."""
        login(page, "basic")
        _open_leaderboard_tab(page)

        # Switch to volume sort
        page.evaluate("loadLeaderboard('volume', currentPeriod)")
        page.wait_for_load_state("networkidle", timeout=10_000)

        cards = page.query_selector_all(".lb-card")
        assert len(cards) > 0, (
            "No .lb-card elements found after switching to volume sort — "
            "leaderboard may have crashed or cleared on sort change"
        )
