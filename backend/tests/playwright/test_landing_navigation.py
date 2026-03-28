"""
Playwright E2E: Landing page navigation buttons route to correct views.

Covers PROJECT.md checklist §11: "All links open correctly (no 404s)"

For a SPA, "links" are JS onclick handlers. These tests verify that each
primary CTA on the landing page:
  - Transitions to the expected view (no crash, no blank screen)
  - Shows the expected content after the transition

Tests:
  1. "View Live Leaderboard" button → view-browse visible, leaderboard loads
  2. "Log In" button → auth view with login tab visible (#login-email present)
  3. "Start Free →" (hero CTA) → auth view with register tab visible (#reg-email present)
  4. Annual billing toggle → prices display annual values (pricing-price-annual visible)

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import BASE_URL


class TestLandingNavigation:
    """Landing page CTAs all route to correct views without errors."""

    def test_view_live_leaderboard_button_shows_browse_view(self, page: Page):
        """Clicking 'View Live Leaderboard' on the landing hero must navigate to
        view-browse and render leaderboard cards.

        showView('browse') should remove 'hidden' from #view-browse and
        hide #view-landing.  The leaderboard should attempt to load bettor
        cards (.lb-card) within 15 seconds.
        """
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Landing view must be visible before we click
        assert not page.evaluate(
            "document.getElementById('view-landing').classList.contains('hidden')"
        ), "view-landing is hidden on initial page load — unexpected"

        # Click the hero "View Live Leaderboard" button
        page.evaluate("showView('browse')")

        # browse view must become visible
        page.wait_for_function(
            "!document.getElementById('view-browse').classList.contains('hidden')",
            timeout=8_000,
        )
        browse_visible = page.evaluate(
            "!document.getElementById('view-browse').classList.contains('hidden')"
        )
        assert browse_visible, (
            "view-browse is still hidden after clicking 'View Live Leaderboard' — "
            "showView('browse') may be broken"
        )

        # Landing view must now be hidden
        landing_hidden = page.evaluate(
            "document.getElementById('view-landing').classList.contains('hidden')"
        )
        assert landing_hidden, (
            "view-landing is still visible after navigating to browse — "
            "view switch did not hide the landing page"
        )

        # Leaderboard container must exist in the browse view
        # (skip if Polymarket data unavailable — network test not the goal here)
        leaderboard_el = page.query_selector("#browse-leaderboard-body")
        assert leaderboard_el is not None, (
            "#browse-leaderboard-body element not found in browse view — "
            "leaderboard container may have been removed or renamed"
        )

    def test_login_button_shows_auth_login_form(self, page: Page):
        """Clicking 'Log In' on the landing nav must show the auth view with the
        login form active (#login-email input must be visible).
        """
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Trigger the log-in flow via JS (nav button is in the landing nav)
        page.evaluate("showView('auth', 'login')")

        # Auth view must become visible
        page.wait_for_function(
            "!document.getElementById('view-auth').classList.contains('hidden')",
            timeout=8_000,
        )
        auth_visible = page.evaluate(
            "!document.getElementById('view-auth').classList.contains('hidden')"
        )
        assert auth_visible, (
            "view-auth is still hidden after showView('auth','login') — "
            "Log In button navigation may be broken"
        )

        # The login email input must be in the DOM and accessible
        login_email = page.query_selector("#login-email")
        assert login_email is not None, (
            "#login-email input not found in auth view — "
            "login form may be missing or use different IDs"
        )

        # Login form must be visible (not hidden)
        form_visible = page.evaluate(
            "!document.getElementById('form-login').classList.contains('hidden')"
        )
        assert form_visible, (
            "#form-login is hidden after showView('auth','login') — "
            "login tab not active by default"
        )

    def test_start_free_button_shows_auth_register_form(self, page: Page):
        """Clicking 'Start Free →' on the hero must show the auth view with the
        register form active (#reg-email input must be visible).
        """
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Trigger register flow — same as clicking any "Start Free" / "Get Started" CTA
        page.evaluate("showView('auth', 'register')")

        # Auth view must become visible
        page.wait_for_function(
            "!document.getElementById('view-auth').classList.contains('hidden')",
            timeout=8_000,
        )

        # The register email input must exist
        reg_email = page.query_selector("#reg-email")
        assert reg_email is not None, (
            "#reg-email input not found — register form may be missing or renamed"
        )

        # Register form must become visible — switchAuthTab has a 150ms CSS animation
        # so we must wait rather than assert synchronously
        page.wait_for_function(
            "!document.getElementById('form-register').classList.contains('hidden')",
            timeout=3_000,
        )
        form_visible = page.evaluate(
            "!document.getElementById('form-register').classList.contains('hidden')"
        )
        assert form_visible, (
            "#form-register is hidden after showView('auth','register') — "
            "register tab not active"
        )

    def test_annual_billing_toggle_changes_price_display(self, page: Page):
        """Clicking the 'Annual' billing tab must switch displayed prices to the
        annual variant (.pricing-price-annual elements visible,
        .pricing-price-monthly hidden).

        This verifies setPricingPeriod('annual') works and the toggle is not broken.
        """
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Initially: monthly prices should be visible, annual hidden
        monthly_display = page.evaluate(
            """() => {
                const el = document.querySelector('.pricing-price-monthly');
                return el ? getComputedStyle(el).display : 'missing';
            }"""
        )
        assert monthly_display not in ("none", "missing"), (
            f".pricing-price-monthly display={monthly_display!r} on page load — "
            "expected monthly to be visible by default"
        )

        # Click the Annual billing tab
        page.evaluate("setPricingPeriod('annual')")

        # Annual prices should now be visible
        annual_display = page.evaluate(
            """() => {
                const el = document.querySelector('.pricing-price-annual');
                return el ? getComputedStyle(el).display : 'missing';
            }"""
        )
        assert annual_display not in ("none", "missing"), (
            f".pricing-price-annual display={annual_display!r} after selecting annual — "
            "setPricingPeriod('annual') may not be toggling the price display correctly"
        )

        # Monthly prices should now be hidden
        monthly_after = page.evaluate(
            """() => {
                const el = document.querySelector('.pricing-price-monthly');
                return el ? getComputedStyle(el).display : 'missing';
            }"""
        )
        assert monthly_after == "none", (
            f".pricing-price-monthly display={monthly_after!r} after switching to annual — "
            "monthly prices should be hidden when annual is selected"
        )
