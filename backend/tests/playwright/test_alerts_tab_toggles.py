"""
Playwright E2E: Alerts tab renders push and Telegram toggles for authenticated users.

Verifies that a basic-tier user navigating to the Alerts tab sees both:
  - #toggle-push  (web push notification toggle)
  - #toggle-telegram  (Telegram notification toggle)

These toggles must be present in the DOM and visible inside #tab-alerts after
loadAlertSettings() fetches from /alerts/settings.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


def _open_alerts_tab(page: Page) -> None:
    """Navigate to the Alerts tab using JS (nav elements are display:none at desktop)."""
    page.evaluate("showTab('alerts')")
    page.wait_for_function(
        "!document.getElementById('tab-alerts').classList.contains('hidden')",
        timeout=8_000,
    )
    # Wait for loadAlertSettings() to fetch from /alerts/settings
    page.wait_for_load_state("networkidle", timeout=8_000)


class TestAlertsTabToggles:
    """Alerts tab must render both notification toggles for authenticated users."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_alerts_tab_shows_push_toggle(self, page: Page):
        """#toggle-push must exist in the Alerts tab for a basic-tier user."""
        login(page, "basic")
        _open_alerts_tab(page)

        toggle = page.query_selector("#toggle-push")
        assert toggle is not None, (
            "#toggle-push not found in #tab-alerts — web push toggle is missing"
        )

        # Confirm it is actually inside the visible alerts tab (not hidden elsewhere)
        visible = page.evaluate(
            """() => {
                const el = document.getElementById('toggle-push');
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }"""
        )
        assert visible, "#toggle-push exists but has zero size — it may be hidden"

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_alerts_tab_shows_telegram_toggle(self, page: Page):
        """#toggle-telegram must exist in the Alerts tab for a basic-tier user."""
        login(page, "basic")
        _open_alerts_tab(page)

        toggle = page.query_selector("#toggle-telegram")
        assert toggle is not None, (
            "#toggle-telegram not found in #tab-alerts — Telegram toggle is missing"
        )

        visible = page.evaluate(
            """() => {
                const el = document.getElementById('toggle-telegram');
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }"""
        )
        assert visible, "#toggle-telegram exists but has zero size — it may be hidden"

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_alerts_tab_both_toggles_present(self, page: Page):
        """Both #toggle-push and #toggle-telegram must be present in a single Alerts tab load."""
        login(page, "basic")
        _open_alerts_tab(page)

        push_el = page.query_selector("#toggle-push")
        tg_el = page.query_selector("#toggle-telegram")

        assert push_el is not None and tg_el is not None, (
            f"Expected both toggles — push={'found' if push_el else 'MISSING'}, "
            f"telegram={'found' if tg_el else 'MISSING'}"
        )
