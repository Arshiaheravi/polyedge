"""
Playwright E2E: Account tab free-tier complement tests + tier-description text.

Verifies:
  Free: #acct-billing-btn HAS class 'hidden' (no subscription to manage)
  Free: #acct-upgrade-nudge does NOT have class 'hidden' (CTA shown for free)
  Free:  #acct-tier-desc starts with "You can follow 1 bettor"
  Basic: #acct-tier-desc starts with "Follow up to 5 bettors"
  VIP:   #acct-tier-desc starts with "Unlimited follows"

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


class TestAccountTabFreeTierElements:
    """Free tier must show billing button as hidden and upgrade nudge as visible."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_billing_btn_hidden_for_free_user(self, page: Page):
        """#acct-billing-btn must have class 'hidden' for a free user — no subscription."""
        login(page, "free")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-billing-btn').classList.contains('hidden')"
        )
        assert is_hidden, (
            "#acct-billing-btn is NOT hidden for free user — "
            "renderAccount() should add 'hidden' for free tier (no subscription to manage)"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_upgrade_nudge_visible_for_free_user(self, page: Page):
        """#acct-upgrade-nudge must NOT have class 'hidden' for free users."""
        login(page, "free")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-upgrade-nudge').classList.contains('hidden')"
        )
        assert not is_hidden, (
            "#acct-upgrade-nudge has 'hidden' class for free user — "
            "renderAccount() should show the upgrade nudge for free tier"
        )


class TestAccountTabTierDescription:
    """#acct-tier-desc must show the correct description string per tier."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_tier_desc_free(self, page: Page):
        """Free tier description must mention '1 bettor'."""
        login(page, "free")
        _open_account_tab(page)

        desc = page.evaluate(
            "() => (document.getElementById('acct-tier-desc')?.textContent || '').trim()"
        )
        assert "1 bettor" in desc, (
            f"Expected free tier description to mention '1 bettor', got: '{desc}'"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_tier_desc_basic(self, page: Page):
        """Basic tier description must mention '5 bettors'."""
        login(page, "basic")
        _open_account_tab(page)

        desc = page.evaluate(
            "() => (document.getElementById('acct-tier-desc')?.textContent || '').trim()"
        )
        assert "5 bettors" in desc, (
            f"Expected basic tier description to mention '5 bettors', got: '{desc}'"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_tier_desc_vip(self, page: Page):
        """VIP tier description must mention 'Unlimited'."""
        login(page, "vip")
        _open_account_tab(page)

        desc = page.evaluate(
            "() => (document.getElementById('acct-tier-desc')?.textContent || '').trim()"
        )
        assert "Unlimited" in desc, (
            f"Expected VIP tier description to mention 'Unlimited', got: '{desc}'"
        )
