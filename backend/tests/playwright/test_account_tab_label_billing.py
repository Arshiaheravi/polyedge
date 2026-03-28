"""
Playwright E2E: Account tab tier-label text, billing button visibility,
and upgrade-nudge hidden state for Basic and VIP users.

Verifies:
  Basic: #acct-tier-label text "Basic — $4.99/mo"
  VIP:   #acct-tier-label text "VIP — $9.99/mo"
  Basic: #acct-billing-btn NOT hidden (billing shown for paid tiers)
  VIP:   #acct-billing-btn NOT hidden
  Basic: #acct-upgrade-nudge has class 'hidden'
  VIP:   #acct-upgrade-nudge has class 'hidden'

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


def _open_account_tab(page: Page) -> None:
    """Navigate to the Account tab using JS (nav elements are display:none at desktop)."""
    page.evaluate("showTab('account')")
    page.wait_for_function(
        "!document.getElementById('tab-account').classList.contains('hidden')",
        timeout=8_000,
    )
    page.wait_for_load_state("networkidle", timeout=8_000)


class TestAccountTabTierLabel:
    """#acct-tier-label must show the correct plan string per tier."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_tier_label_basic(self, page: Page):
        """#acct-tier-label must read 'Basic — $4.99/mo' for a basic-tier user."""
        login(page, "basic")
        _open_account_tab(page)

        label_text = page.evaluate(
            "() => (document.getElementById('acct-tier-label')?.textContent || '').trim()"
        )
        assert label_text == "Basic — $4.99/mo", (
            f"Expected 'Basic — $4.99/mo', got: '{label_text}'"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_tier_label_vip(self, page: Page):
        """#acct-tier-label must read 'VIP — $9.99/mo' for a VIP user."""
        login(page, "vip")
        _open_account_tab(page)

        label_text = page.evaluate(
            "() => (document.getElementById('acct-tier-label')?.textContent || '').trim()"
        )
        assert label_text == "VIP — $9.99/mo", (
            f"Expected 'VIP — $9.99/mo', got: '{label_text}'"
        )


class TestAccountTabBillingButton:
    """#acct-billing-btn must be visible (not hidden) for paid tiers."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_billing_btn_visible_for_basic(self, page: Page):
        """#acct-billing-btn must NOT have class 'hidden' for a basic-tier user."""
        login(page, "basic")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-billing-btn').classList.contains('hidden')"
        )
        assert not is_hidden, (
            "#acct-billing-btn has 'hidden' class for basic user — renderAccount() should show it"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_billing_btn_visible_for_vip(self, page: Page):
        """#acct-billing-btn must NOT have class 'hidden' for a VIP user."""
        login(page, "vip")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-billing-btn').classList.contains('hidden')"
        )
        assert not is_hidden, (
            "#acct-billing-btn has 'hidden' class for VIP user — renderAccount() should show it"
        )


class TestAccountTabUpgradeNudge:
    """#acct-upgrade-nudge must be hidden for paid tiers (only shown for free)."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_upgrade_nudge_hidden_for_basic(self, page: Page):
        """#acct-upgrade-nudge must have class 'hidden' for basic-tier users."""
        login(page, "basic")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-upgrade-nudge').classList.contains('hidden')"
        )
        assert is_hidden, (
            "#acct-upgrade-nudge does NOT have 'hidden' class for basic user — "
            "renderAccount() should hide the upgrade nudge for paid tiers"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_upgrade_nudge_hidden_for_vip(self, page: Page):
        """#acct-upgrade-nudge must have class 'hidden' for VIP users."""
        login(page, "vip")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-upgrade-nudge').classList.contains('hidden')"
        )
        assert is_hidden, (
            "#acct-upgrade-nudge does NOT have 'hidden' class for VIP user — "
            "renderAccount() should hide the upgrade nudge for paid tiers"
        )
