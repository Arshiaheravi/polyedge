"""
Playwright E2E: free user enabling web push triggers upgrade modal.

Flow: login as free user → showTab('alerts') → call toggleWebPush() via
page.evaluate → assert:
  1. #upgrade-modal loses its 'hidden' class (modal becomes visible)
  2. #toggle-push does NOT gain the 'on' class (toggle stays OFF)

Proves BUG #8 is fixed: free users are gated from web push (tier check runs
before VAPID availability check so it fires even in dev with VAPID unconfigured).

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


def _open_alerts_tab(page: Page) -> None:
    page.evaluate("showTab('alerts')")
    page.wait_for_function(
        "!document.getElementById('tab-alerts').classList.contains('hidden')",
        timeout=8_000,
    )
    page.wait_for_load_state("networkidle", timeout=8_000)


class TestFreePushUpgradeModal:

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_free_web_push_toggle_opens_upgrade_modal(self, page: Page):
        """Free user calling toggleWebPush() must open the upgrade modal."""
        login(page, "free")
        _open_alerts_tab(page)

        # Upgrade modal must be hidden before the action
        modal_visible_before = page.evaluate(
            "!document.getElementById('upgrade-modal').classList.contains('hidden')"
        )
        assert not modal_visible_before, "Upgrade modal should not be visible before clicking push toggle"

        # Call toggleWebPush — free-tier gate must fire
        page.evaluate("toggleWebPush()")
        page.wait_for_timeout(300)

        modal_visible_after = page.evaluate(
            "!document.getElementById('upgrade-modal').classList.contains('hidden')"
        )
        assert modal_visible_after, \
            "Upgrade modal must appear when free user tries to enable web push"

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_free_web_push_toggle_stays_off(self, page: Page):
        """After free-tier gate fires, the push toggle must remain OFF."""
        login(page, "free")
        _open_alerts_tab(page)

        # Close any lingering modal
        page.evaluate("closeModal('upgrade-modal')")

        # Call toggleWebPush — free-tier gate must prevent enabling
        page.evaluate("toggleWebPush()")
        page.wait_for_timeout(300)

        toggle_on = page.evaluate(
            "document.getElementById('toggle-push').classList.contains('on')"
        )
        assert not toggle_on, "Push toggle must remain OFF when free-tier gate fires"
