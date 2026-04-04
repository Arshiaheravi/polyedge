"""
Playwright E2E: Bettor profile opens with real data for an authenticated basic user.

Tests the "click bettor → view full profile" flow:
  1. Login as basic@polyedge.com
  2. Navigate to leaderboard — wait for bettor cards to load
  3. Get first bettor's address from data-addr attribute
  4. Call showProfile(addr) — navigates to #tab-profile and starts API fetch
  5. Assert the profile address display contains the address (starts with 0x)
  6. Wait for API data to load (profile-name changes from skeleton to real text)
  7. Assert simulator card — if visible, it must NOT be locked (basic user sees real data)

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login


class TestProfileModal:
    """Basic-tier user opens a bettor profile and sees real (non-blurred) data."""

    def test_profile_shows_address_and_unlocked_simulator(self, page: Page):
        """
        Login as basic → leaderboard → showProfile(addr) → assert profile tab visible,
        address shown with 0x prefix, simulator card (if present) not locked.

        Steps:
        1. Login as basic@polyedge.com
        2. Navigate to leaderboard, wait for bettor cards
        3. Read first bettor's address from data-addr attribute
        4. Call showProfile(addr) to open the profile tab
        5. Assert #tab-profile is not hidden
        6. Assert #profile-addr-display textContent starts with '0x'
        7. Wait for profile data to load (profile-name leaves skeleton state)
        8. Assert simulator card: if displayed, #profile-simulator-value must not have 'locked' class
        """
        # ── Step 1: Login as basic ─────────────────────────────────────────────
        login(page, "basic")

        # ── Step 2: Navigate to leaderboard, wait for bettor cards ────────────
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card[data-addr]", timeout=15_000)
        except Exception:
            pytest.skip("No .lb-card[data-addr] found — Polymarket leaderboard data unavailable")

        # ── Step 3: Get first bettor address ──────────────────────────────────
        addr = page.evaluate(
            "document.querySelector('.lb-card[data-addr]')?.getAttribute('data-addr')"
        )
        if not addr:
            pytest.skip("Could not read data-addr from first leaderboard card")

        assert addr.startswith("0x"), (
            f"Bettor address from data-addr does not start with '0x': {addr!r}"
        )

        # ── Step 4: Open profile via showProfile(addr) ────────────────────────
        page.evaluate(f"showProfile('{addr}')")

        # ── Step 5: Assert #tab-profile is visible ────────────────────────────
        try:
            page.wait_for_function(
                "!document.getElementById('tab-profile').classList.contains('hidden')",
                timeout=5_000,
            )
        except Exception:
            pytest.fail(
                "#tab-profile still has 'hidden' class after showProfile() was called. "
                "showTab('profile') may not be running correctly."
            )

        # ── Step 6: Assert address displayed immediately ──────────────────────
        displayed_addr = page.evaluate(
            "document.getElementById('profile-addr-display')?.textContent?.trim()"
        )
        assert displayed_addr, (
            "#profile-addr-display is empty after showProfile() — address was not set"
        )
        assert displayed_addr.startswith("0x"), (
            f"#profile-addr-display does not start with '0x': {displayed_addr!r}"
        )
        assert displayed_addr.lower() == addr.lower(), (
            f"Profile address display shows '{displayed_addr}' but expected '{addr}'"
        )

        # ── Step 7: Wait for API data to finish loading ───────────────────────
        # renderProfileData() sets profile-name textContent — skeleton gets replaced
        # Skeleton has an inline <span class="skeleton">; real data uses textContent
        try:
            page.wait_for_function(
                """() => {
                    const el = document.getElementById('profile-name');
                    return el && !el.querySelector('.skeleton') && el.textContent.trim().length > 0;
                }""",
                timeout=15_000,
            )
        except Exception:
            pytest.fail(
                "Profile data did not load within 15s — #profile-name still shows skeleton. "
                "GET /bettors/{address} may have failed or timed out."
            )

        # ── Step 8: Simulator card check — if visible, must NOT be locked ─────
        # For basic users: if copy_simulator has data, card shows without 'locked' class
        # If bettor has no resolved bets, card stays display:none — skip assertion
        sim_card_display = page.evaluate(
            "getComputedStyle(document.getElementById('profile-simulator-card')).display"
        )

        if sim_card_display != "none":
            # Card is visible — verify it's NOT the locked (blurred) state
            sim_value_classes = page.evaluate(
                "document.getElementById('profile-simulator-value')?.className"
            )
            assert "locked" not in (sim_value_classes or ""), (
                f"Simulator card is visible but #profile-simulator-value has 'locked' class: "
                f"'{sim_value_classes}'. "
                "A basic-tier user should see real (unblurred) simulator data, not the free-tier teaser."
            )

            # The CTA 'Upgrade to unlock' must be hidden for basic users
            sim_cta_display = page.evaluate(
                "getComputedStyle(document.getElementById('profile-simulator-cta')).display"
            )
            assert sim_cta_display == "none", (
                f"Simulator upgrade CTA is visible (display={sim_cta_display!r}) for a basic user. "
                "Basic users have the simulator unlocked — the 'Upgrade to unlock' link must be hidden."
            )
        # else: no simulator data for this bettor — card is hidden, nothing to assert
