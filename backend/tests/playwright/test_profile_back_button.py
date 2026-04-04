"""
Playwright E2E: Profile back-button returns to leaderboard.

Tests the navigation from profile view back to leaderboard:
  1. Login as basic@polyedge.com
  2. Navigate to leaderboard — wait for bettor cards to load
  3. Get first bettor's address from data-addr attribute
  4. Call showProfile(addr) — #tab-profile becomes visible, #tab-leaderboard hidden
  5. Click #profile-back-btn (calls showTab('leaderboard'))
  6. Assert #tab-leaderboard is no longer hidden
  7. Assert #tab-profile has the 'hidden' class

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login


class TestProfileBackButton:
    """Back button on profile tab returns user to the leaderboard."""

    def test_back_button_returns_to_leaderboard(self, page: Page):
        """
        Login as basic → leaderboard → showProfile(addr) → click #profile-back-btn
        → assert #tab-leaderboard visible, #tab-profile hidden.

        Steps:
        1. Login as basic@polyedge.com
        2. Navigate to leaderboard via showView('browse'), wait for .lb-card[data-addr]
        3. Read first bettor address from data-addr attribute
        4. Call showProfile(addr) — #tab-profile must lose 'hidden' class
        5. Click #profile-back-btn
        6. Assert #tab-leaderboard does NOT have 'hidden' class
        7. Assert #tab-profile HAS 'hidden' class
        """
        # ── Step 1: Login as basic ─────────────────────────────────────────────
        login(page, "basic")

        # ── Step 2: Navigate to leaderboard tab (inside view-dashboard) ─────
        # IMPORTANT: do NOT call showView('browse') — that hides view-dashboard and
        # makes #profile-back-btn invisible (it lives inside view-dashboard's #tab-profile).
        # showTab('leaderboard') keeps view-dashboard visible and loads the lb-body cards.
        page.evaluate("showTab('leaderboard')")
        try:
            page.wait_for_selector("#lb-body .lb-card[data-addr]", timeout=15_000)
        except Exception:
            pytest.skip("No .lb-card[data-addr] found in #lb-body — Polymarket leaderboard data unavailable")

        # ── Step 3: Get first bettor address ──────────────────────────────────
        addr = page.evaluate(
            "document.querySelector('#lb-body .lb-card[data-addr]')?.getAttribute('data-addr')"
        )
        if not addr:
            pytest.skip("Could not read data-addr from first leaderboard card")

        assert addr.startswith("0x"), (
            f"Bettor address from data-addr does not start with '0x': {addr!r}"
        )

        # ── Step 4: Open profile via showProfile(addr) ────────────────────────
        page.evaluate(f"showProfile('{addr}')")

        try:
            page.wait_for_function(
                "!document.getElementById('tab-profile').classList.contains('hidden')",
                timeout=5_000,
            )
        except Exception:
            pytest.fail(
                "#tab-profile still has 'hidden' class after showProfile() was called."
            )

        # ── Step 5: Click the back button ─────────────────────────────────────
        page.click("#profile-back-btn")

        # ── Step 6: Assert #tab-leaderboard is visible ────────────────────────
        try:
            page.wait_for_function(
                "!document.getElementById('tab-leaderboard').classList.contains('hidden')",
                timeout=5_000,
            )
        except Exception:
            pytest.fail(
                "#tab-leaderboard still has 'hidden' class after clicking #profile-back-btn. "
                "showTab('leaderboard') may not be removing the 'hidden' class correctly."
            )

        # ── Step 7: Assert #tab-profile is hidden ─────────────────────────────
        profile_hidden = page.evaluate(
            "document.getElementById('tab-profile').classList.contains('hidden')"
        )
        assert profile_hidden, (
            "#tab-profile does not have 'hidden' class after navigating back to leaderboard. "
            "showTab('leaderboard') must hide the profile tab."
        )
