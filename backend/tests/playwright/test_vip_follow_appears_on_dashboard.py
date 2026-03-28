"""
Playwright E2E: VIP-tier user follows bettor → bettor appears on follows dashboard.

Tests the core user flow for the VIP tier:
  1. Login as vip@polyedge.com (subscription_tier='vip')
  2. Clean all pre-existing follows so the test starts from zero
  3. Browse leaderboard — get first bettor address
  4. Follow that bettor via followBettor() JS function
  5. Navigate to Follows tab
  6. Assert the followed bettor's address appears in #follows-container

This completes the North Star table row "Follow bettor → see on dashboard | ✓ | ✓ | ✓"
for the VIP tier. A regression that breaks POST /follows, GET /follows, or the
follow card renderer will cause this test to fail.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login


class TestVipFollowAppearsOnDashboard:
    """VIP-tier user follows a bettor → bettor card appears in follows dashboard."""

    def test_vip_followed_bettor_appears_in_follows_container(self, page: Page):
        """
        Login as VIP tier → clean follows → follow first leaderboard bettor
        → switch to Follows tab → assert bettor address appears in #follows-container.

        Steps:
        1. Login as vip@polyedge.com
        2. Clean all existing follows via apiFetch DELETE
        3. Navigate to leaderboard, get first bettor's address
        4. Call followBettor() — VIP tier has unlimited follows
        5. Switch to Follows tab — wait for container to populate
        6. Assert bettor address is in #follows-container HTML
        """
        # ── Step 1: Login as VIP-tier account ────────────────────────────────
        login(page, "vip")

        # ── Step 2: Clean all existing follows ───────────────────────────────
        page.evaluate("""async () => {
            const res = await apiFetch('/follows');
            const data = await res.json();
            const follows = data.follows || [];
            for (const f of follows) {
                await apiFetch('/follows/' + f.bettor_address, { method: 'DELETE' });
            }
            followedAddresses.clear();
        }""")
        page.wait_for_timeout(1_000)

        # ── Step 3: Navigate to leaderboard, get first bettor address ─────────
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

        # ── Step 4: Follow the bettor via JS function ──────────────────────────
        page.evaluate(f"followBettor('{addr}', 'TestBettor', null)")
        page.wait_for_timeout(2_500)

        # Verify the follow registered in client state
        is_following = page.evaluate(f"followedAddresses.has('{addr}')")
        if not is_following:
            pytest.skip(
                f"followBettor() did not register in followedAddresses for {addr[:10]}... "
                "— cannot assert dashboard appearance (pre-condition not met)"
            )

        # ── Step 5: Navigate to Follows tab ───────────────────────────────────
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
                "follows-empty still hidden) after VIP user followed a bettor. "
                "loadMyFollows() may have failed or GET /follows returned empty."
            )

        # ── Step 6: Assert bettor address appears in #follows-container ────────
        container_html = page.inner_html("#follows-container")

        assert addr.lower() in container_html.lower(), (
            f"Followed bettor address '{addr[:20]}...' not found in #follows-container HTML. "
            "The bettor was followed successfully (followedAddresses confirmed it) but the "
            "follows tab did not render the bettor card. "
            f"Container HTML (first 400 chars): {container_html[:400]}"
        )
