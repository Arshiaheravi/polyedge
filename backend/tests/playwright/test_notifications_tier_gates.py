"""
Playwright E2E: Notifications / Alerts settings page — tier gate visual verification.

Tests that the Alerts tab correctly blocks or grants access to notification channels
based on the user's subscription tier:

  - Free user: Telegram toggle click → upgrade modal fires (tier gate works)
  - Free user: SMS label shows "VIP required"; SMS toggle → upgrade modal fires
  - VIP user:  SMS label shows "Not verified" (no gate); Telegram toggle NOT blocked

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_alerts_tab(page: Page) -> None:
    """Navigate to the Alerts tab using JS (nav elements are display:none at desktop)."""
    page.evaluate("showTab('alerts')")
    # Wait for the alerts tab to become visible
    page.wait_for_function(
        "!document.getElementById('tab-alerts').classList.contains('hidden')",
        timeout=8_000,
    )
    # Give loadAlertSettings() time to fetch from /alerts/settings
    page.wait_for_load_state("networkidle", timeout=8_000)


def _is_upgrade_modal_visible(page: Page) -> bool:
    """Return True if the upgrade modal is currently shown (not hidden)."""
    return page.evaluate(
        "!document.getElementById('upgrade-modal').classList.contains('hidden')"
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFreeTierAlertsGates:
    """Free-tier user should be blocked from enabling Telegram or SMS."""

    @pytest.mark.skipif(
        not BASE_URL,
        reason="frontend server not configured",
    )
    def test_free_telegram_toggle_opens_upgrade_modal(self, page: Page):
        """Clicking Telegram toggle as free user must open the upgrade modal."""
        login(page, "free")
        _open_alerts_tab(page)

        # Confirm upgrade modal is currently hidden before clicking
        assert not _is_upgrade_modal_visible(page), "Upgrade modal should not be visible before click"

        # Click the Telegram toggle via JS to avoid display:none issues with overlay cards
        page.evaluate("toggleTelegram()")

        # Upgrade modal must now be visible
        page.wait_for_function(
            "!document.getElementById('upgrade-modal').classList.contains('hidden')",
            timeout=5_000,
        )
        assert _is_upgrade_modal_visible(page), \
            "Upgrade modal should appear when free user clicks Telegram toggle"

        # Telegram toggle must NOT be turned on (gate prevented activation)
        tg_on = page.evaluate(
            "document.getElementById('toggle-telegram').classList.contains('on')"
        )
        assert not tg_on, "Telegram toggle must remain OFF after free-tier gate fires"

    @pytest.mark.skipif(
        not BASE_URL,
        reason="frontend server not configured",
    )
    def test_free_sms_label_and_toggle_blocked(self, page: Page):
        """Free user: SMS status label shows 'VIP required'; SMS toggle opens upgrade modal."""
        login(page, "free")
        _open_alerts_tab(page)

        # The SMS status label must show "VIP required" for non-VIP users
        sms_label = page.evaluate(
            "document.getElementById('slabel-sms').textContent"
        )
        assert sms_label == "VIP required", \
            f"Expected SMS label 'VIP required' for free user, got '{sms_label}'"

        # Close any upgrade modal that may be lingering from a previous check
        page.evaluate("closeModal('upgrade-modal')")

        # Clicking SMS toggle as free user should open the upgrade modal
        page.evaluate("toggleSms()")

        page.wait_for_function(
            "!document.getElementById('upgrade-modal').classList.contains('hidden')",
            timeout=5_000,
        )
        assert _is_upgrade_modal_visible(page), \
            "Upgrade modal should appear when free user clicks SMS toggle"

        # SMS toggle must remain OFF
        sms_on = page.evaluate(
            "document.getElementById('toggle-sms').classList.contains('on')"
        )
        assert not sms_on, "SMS toggle must remain OFF after free-tier gate fires"


class TestBasicTierAlertsAccess:
    """Basic-tier user should have full access to Telegram and web push channels."""

    @pytest.mark.skipif(
        not BASE_URL,
        reason="frontend server not configured",
    )
    def test_basic_telegram_toggle_does_not_open_upgrade_modal(self, page: Page):
        """Basic user clicking Telegram toggle must NOT trigger the upgrade modal.

        NORTH_STAR: 'Notifications: Basic = enabled'. Free users get an upgrade modal;
        basic users must NOT — they have paid for notification access.
        """
        login(page, "basic")
        _open_alerts_tab(page)

        assert not _is_upgrade_modal_visible(page), \
            "Upgrade modal should not be visible before any action"

        page.evaluate("toggleTelegram()")
        page.wait_for_timeout(500)

        assert not _is_upgrade_modal_visible(page), \
            "Upgrade modal must NOT appear when basic user clicks Telegram toggle — " \
            "basic tier has paid access to Telegram notifications"

    @pytest.mark.skipif(
        not BASE_URL,
        reason="frontend server not configured",
    )
    def test_basic_push_toggle_does_not_open_upgrade_modal(self, page: Page):
        """Basic user calling toggleWebPush() must NOT trigger the upgrade modal.

        VAPID may not be configured in test env (a toast error may appear instead),
        but the free-tier upgrade modal gate must not fire for basic tier users.
        Free users get the upgrade modal; basic users must NOT.
        """
        login(page, "basic")
        _open_alerts_tab(page)

        assert not _is_upgrade_modal_visible(page), \
            "Upgrade modal should not be visible before any action"

        page.evaluate("toggleWebPush()")
        page.wait_for_timeout(500)

        assert not _is_upgrade_modal_visible(page), \
            "Upgrade modal must NOT appear when basic user calls toggleWebPush() — " \
            "only a VAPID toast error is expected in test env, not the upgrade modal"


class TestVipTierAlertsAccess:
    """VIP user should have full access to all notification channels."""

    @pytest.mark.skipif(
        not BASE_URL,
        reason="frontend server not configured",
    )
    def test_vip_sms_label_not_gated(self, page: Page):
        """VIP user: SMS label must NOT show 'VIP required'."""
        login(page, "vip")
        _open_alerts_tab(page)

        sms_label = page.evaluate(
            "document.getElementById('slabel-sms').textContent"
        )
        assert sms_label != "VIP required", \
            f"VIP user should not see 'VIP required' SMS label, got '{sms_label}'"
        # VIP with no phone verified → label should be "Not verified"
        assert "Not verified" in sms_label or "Active" in sms_label or sms_label == "Off", \
            f"Expected VIP SMS label to be 'Not verified', 'Active', or 'Off', got '{sms_label}'"

    @pytest.mark.skipif(
        not BASE_URL,
        reason="frontend server not configured",
    )
    def test_vip_telegram_toggle_does_not_open_upgrade_modal(self, page: Page):
        """VIP user clicking Telegram toggle must NOT trigger the upgrade modal."""
        login(page, "vip")
        _open_alerts_tab(page)

        assert not _is_upgrade_modal_visible(page), \
            "Upgrade modal should not be visible before any action"

        # Call toggleTelegram — for VIP this should attempt the API call, not open upgrade modal
        # We don't assert the API succeeds (Telegram not configured in test env)
        # We only assert the upgrade modal does NOT appear
        page.evaluate("toggleTelegram()")

        # Give it a moment to settle — upgrade modal should NOT appear
        page.wait_for_timeout(500)

        assert not _is_upgrade_modal_visible(page), \
            "Upgrade modal must NOT appear when VIP user clicks Telegram toggle"
