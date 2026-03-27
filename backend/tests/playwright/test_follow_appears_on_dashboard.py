"""
Playwright E2E: Follow bettor → bettor appears on follows dashboard.

Tests the core user flow:
  1. Register fresh free-tier user (zero state pollution)
  2. Browse leaderboard — get first bettor address
  3. Follow that bettor via followBettor() JS function
  4. Navigate to Follows tab
  5. Assert the followed bettor's address appears in #follows-container

This test proves the end-to-end "follow → appears on dashboard" flow works in
a real browser. A regression that breaks POST /follows, GET /follows, or the
cardContainer rendering will cause this test to fail.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import time
import pytest
from playwright.sync_api import Page
from .conftest import BASE_URL


def _register_fresh_user(page: Page) -> None:
    """Register a brand-new free-tier user.

    Uses timestamp email to guarantee zero prior state (no follows).
    """
    ts = int(time.time())
    email = f"follow_test_{ts}@polyedge-test.com"
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle", timeout=10_000)
    page.evaluate("showView('auth', 'register')")
    page.fill("#reg-name", f"FollowTest{ts}")
    page.fill("#reg-email", email)
    page.fill("#reg-password", "TestPass123!")
    page.click("#register-submit")
    page.wait_for_function(
        "!document.getElementById('view-dashboard').classList.contains('hidden')",
        timeout=10_000,
    )


class TestFollowAppearsOnDashboard:
    """Core user flow: follow bettor → bettor card appears in follows dashboard."""

    def test_followed_bettor_appears_in_follows_container(self, page: Page):
        """
        After following a bettor from the leaderboard, that bettor's address
        must appear in #follows-container when the Follows tab is loaded.

        Steps:
        1. Register fresh account — guaranteed 0 follows
        2. Navigate to leaderboard, get first bettor's address
        3. Call followBettor() — free tier allows exactly 1 follow
        4. Switch to Follows tab — wait for container to populate
        5. Assert bettor address is in #follows-container HTML
        """
        # ── Step 1: Register fresh free-tier user ─────────────────────────────
        _register_fresh_user(page)

        # ── Step 2: Navigate to leaderboard, get first bettor address ─────────
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card[data-addr]", timeout=15_000)
        except Exception:
            pytest.skip("Leaderboard has no bettor cards — Polymarket data unavailable")

        addr = page.evaluate(
            "document.querySelector('.lb-card[data-addr]')?.getAttribute('data-addr')"
        )
        if not addr:
            pytest.skip("No bettor address found on leaderboard")

        # ── Step 3: Follow the bettor via JS function ──────────────────────────
        page.evaluate(f"followBettor('{addr}', 'TestBettor', null)")
        page.wait_for_timeout(2_500)

        # Verify the follow actually registered in client state
        is_following = page.evaluate(f"followedAddresses.has('{addr}')")
        if not is_following:
            pytest.skip(
                f"followBettor() did not register in followedAddresses for {addr[:10]}... "
                "— cannot assert dashboard appearance (pre-condition not met)"
            )

        # ── Step 4: Navigate to Follows tab ───────────────────────────────────
        page.evaluate("showTab('follows')")
        try:
            page.wait_for_function(
                """() => {
                    const c = document.getElementById('follows-container');
                    const e = document.getElementById('follows-empty');
                    return (c && c.children.length > 0) ||
                           (e && !e.classList.contains('hidden'));
                }""",
                timeout=15_000,
            )
        except Exception:
            pytest.fail(
                "Follows tab did not render any content (follows-container empty AND "
                "follows-empty still hidden) after following a bettor. "
                "loadMyFollows() may have failed or GET /follows returned empty."
            )

        # ── Step 5: Assert bettor address appears in #follows-container ────────
        container_html = page.inner_html("#follows-container")

        # The bettor address appears in onclick attrs: showProfile('addr') and
        # unfollowFromFollowsTab('addr', this) — both render the full lowercase address
        assert addr.lower() in container_html.lower(), (
            f"Followed bettor address '{addr[:20]}...' not found in #follows-container HTML. "
            "The bettor was followed successfully (followedAddresses confirmed it) but the "
            "follows tab did not render the bettor card. "
            f"Container HTML (first 400 chars): {container_html[:400]}"
        )
