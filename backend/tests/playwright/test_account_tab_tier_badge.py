"""
Playwright E2E: Account tab shows correct tier badge and upgrade button for free user.

Verifies that a free-tier user navigating to the Account tab sees:
  - #acct-plan-badge with class 'tier-free' and text "Free"
  - #acct-upgrade-btn visible and not hidden (renderAccount() removes 'hidden' for free tier)

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
    # Wait for renderAccount() to update the DOM
    page.wait_for_load_state("networkidle", timeout=8_000)


class TestAccountTabTierBadge:
    """Account tab must show Free tier badge and upgrade button for free users."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_shows_free_tier_badge(self, page: Page):
        """#acct-plan-badge must have class 'tier-free' for a free-tier user."""
        login(page, "free")
        _open_account_tab(page)

        badge = page.query_selector("#acct-plan-badge")
        assert badge is not None, "#acct-plan-badge not found in #tab-account"

        badge_classes = page.evaluate(
            "() => document.getElementById('acct-plan-badge').className"
        )
        assert "tier-free" in badge_classes, (
            f"Expected #acct-plan-badge to have class 'tier-free', got: {badge_classes}"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_badge_text_is_free(self, page: Page):
        """#acct-plan-badge text must be 'Free' for a free-tier user."""
        login(page, "free")
        _open_account_tab(page)

        badge_text = page.evaluate(
            "() => (document.getElementById('acct-plan-badge')?.textContent || '').trim()"
        )
        assert badge_text == "Free", (
            f"Expected badge text 'Free', got: '{badge_text}'"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_upgrade_button_visible_for_free_user(self, page: Page):
        """#acct-upgrade-btn must be visible (not hidden) for a free-tier user."""
        login(page, "free")
        _open_account_tab(page)

        upgrade_btn = page.query_selector("#acct-upgrade-btn")
        assert upgrade_btn is not None, "#acct-upgrade-btn not found in #tab-account"

        # renderAccount() calls upgradeBtn.classList.remove('hidden') for free tier
        is_hidden = page.evaluate(
            "() => document.getElementById('acct-upgrade-btn').classList.contains('hidden')"
        )
        assert not is_hidden, (
            "#acct-upgrade-btn still has 'hidden' class — renderAccount() did not show it for free user"
        )

        # Also verify it has non-zero size (rendered, not display:none)
        visible = page.evaluate(
            """() => {
                const el = document.getElementById('acct-upgrade-btn');
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            }"""
        )
        assert visible, "#acct-upgrade-btn has zero size — it may be invisible despite lacking 'hidden' class"
