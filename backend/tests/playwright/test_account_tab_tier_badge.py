"""
Playwright E2E: Account tab shows correct tier badge and upgrade button per tier.

Verifies:
  Free:  #acct-plan-badge class 'tier-free', text "Free", upgrade button visible
  Basic: #acct-plan-badge class 'tier-basic', text "Basic", upgrade btn shows "Upgrade to VIP →"
  VIP:   #acct-plan-badge class 'tier-vip', text "VIP", upgrade button hidden

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


class TestAccountTabBasicTierBadge:
    """Account tab must show Basic tier badge for basic-tier users."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_shows_basic_tier_badge(self, page: Page):
        """#acct-plan-badge must have class 'tier-basic' for a basic-tier user."""
        login(page, "basic")
        _open_account_tab(page)

        badge_classes = page.evaluate(
            "() => document.getElementById('acct-plan-badge').className"
        )
        assert "tier-basic" in badge_classes, (
            f"Expected #acct-plan-badge to have class 'tier-basic', got: {badge_classes}"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_badge_text_is_basic(self, page: Page):
        """#acct-plan-badge text must be 'Basic' for a basic-tier user."""
        login(page, "basic")
        _open_account_tab(page)

        badge_text = page.evaluate(
            "() => (document.getElementById('acct-plan-badge')?.textContent || '').trim()"
        )
        assert badge_text == "Basic", (
            f"Expected badge text 'Basic', got: '{badge_text}'"
        )


class TestAccountTabVipTierBadge:
    """Account tab must show VIP tier badge for VIP users."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_shows_vip_tier_badge(self, page: Page):
        """#acct-plan-badge must have class 'tier-vip' for a VIP user."""
        login(page, "vip")
        _open_account_tab(page)

        badge_classes = page.evaluate(
            "() => document.getElementById('acct-plan-badge').className"
        )
        assert "tier-vip" in badge_classes, (
            f"Expected #acct-plan-badge to have class 'tier-vip', got: {badge_classes}"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_badge_text_is_vip(self, page: Page):
        """#acct-plan-badge text must be 'VIP' for a VIP user."""
        login(page, "vip")
        _open_account_tab(page)

        badge_text = page.evaluate(
            "() => (document.getElementById('acct-plan-badge')?.textContent || '').trim()"
        )
        assert badge_text == "VIP", (
            f"Expected badge text 'VIP', got: '{badge_text}'"
        )


class TestAccountTabUpgradeButtonPaidTiers:
    """Upgrade button behaviour differs for Basic (shows VIP upgrade) and VIP (hidden)."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_upgrade_button_hidden_for_vip_user(self, page: Page):
        """#acct-upgrade-btn must have 'hidden' class for VIP users — no upgrade path."""
        login(page, "vip")
        _open_account_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('acct-upgrade-btn').classList.contains('hidden')"
        )
        assert is_hidden, (
            "#acct-upgrade-btn is NOT hidden for VIP user — renderAccount() should add 'hidden' for VIP tier"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_account_tab_upgrade_button_shows_vip_upsell_for_basic_user(self, page: Page):
        """For basic tier, upgrade button must say 'Upgrade to VIP →' (not the generic free-tier text)."""
        login(page, "basic")
        _open_account_tab(page)

        btn_text = page.evaluate(
            "() => (document.getElementById('acct-upgrade-btn')?.textContent || '').trim()"
        )
        assert "VIP" in btn_text, (
            f"Expected upgrade button to mention 'VIP' for basic user, got: '{btn_text}'"
        )
        assert btn_text != "Upgrade Plan →", (
            "Basic user should see 'Upgrade to VIP →', not the generic 'Upgrade Plan →' shown to free users"
        )
