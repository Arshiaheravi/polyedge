"""
Playwright E2E: logout() clears pe_token from localStorage and returns to landing.

Flow: login as free user → call logout() via page.evaluate → assert:
  1. localStorage.getItem('pe_token') is null (token removed)
  2. #view-landing is visible (not hidden)
  3. #view-dashboard is hidden (user is not still on dashboard)

Proves full auth cleanup on logout — token cleared, UI resets to unauthenticated state.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


class TestLogoutClearsToken:

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_logout_removes_pe_token_from_localstorage(self, page: Page):
        """After logout(), pe_token must be null in localStorage."""
        login(page, "free")

        # Confirm token exists before logout
        token_before = page.evaluate("localStorage.getItem('pe_token')")
        assert token_before is not None, "Token should be set after login"

        # Call logout via JS (avoids click on hidden nav elements)
        page.evaluate("logout()")
        page.wait_for_timeout(300)

        token_after = page.evaluate("localStorage.getItem('pe_token')")
        assert token_after is None, \
            f"pe_token must be null after logout, got: {token_after!r}"

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_logout_shows_landing_view(self, page: Page):
        """After logout(), #view-landing must be visible (hidden class removed)."""
        login(page, "free")
        page.evaluate("logout()")

        page.wait_for_function(
            "!document.getElementById('view-landing').classList.contains('hidden')",
            timeout=5_000,
        )
        landing_hidden = page.evaluate(
            "document.getElementById('view-landing').classList.contains('hidden')"
        )
        assert not landing_hidden, "#view-landing should be visible after logout"

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_logout_hides_dashboard_view(self, page: Page):
        """After logout(), #view-dashboard must be hidden."""
        login(page, "free")

        # Dashboard is visible after login
        dash_hidden_before = page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        )
        assert not dash_hidden_before, "Dashboard should be visible after login"

        page.evaluate("logout()")
        page.wait_for_timeout(300)

        dash_hidden_after = page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        )
        assert dash_hidden_after, "#view-dashboard must be hidden after logout"
