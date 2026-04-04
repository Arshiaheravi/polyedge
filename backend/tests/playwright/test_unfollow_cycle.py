"""
Playwright E2E: Follow then unfollow cycle — bettor appears then disappears.

Tests the complete follow/unfollow lifecycle:
  1. Login as basic@polyedge.com
  2. Clean all pre-existing follows
  3. Follow first leaderboard bettor — assert address appears in #follows-container
  4. Unfollow that bettor via unfollowFromFollowsTab() JS function
  5. Assert bettor's address disappears from #follows-container
     (either container is empty or bettor card is gone)

This proves DELETE /follows/{address} wires through to the UI — any regression
that breaks the DELETE endpoint, the client-side remove logic, or the follows tab
re-render after an unfollow will cause this test to fail.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login


class TestUnfollowCycle:
    """Follow a bettor, confirm they appear, unfollow, confirm they disappear."""

    def test_follow_then_unfollow_removes_bettor_from_dashboard(self, page: Page):
        """
        Login as basic → clean follows → follow bettor → assert in #follows-container
        → unfollow → assert address is gone from #follows-container.

        Steps:
        1. Login as basic@polyedge.com
        2. Clean all existing follows
        3. Navigate to leaderboard, get first bettor address
        4. followBettor() — assert address appears in #follows-container
        5. unfollowFromFollowsTab(addr, null) via page.evaluate
        6. Wait for re-render, assert address is no longer in container HTML
        """
        # ── Step 1: Login as basic-tier account ──────────────────────────────
        login(page, "basic")

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

        # ── Step 4: Follow the bettor, assert appears in follows container ─────
        page.evaluate(f"followBettor('{addr}', 'TestBettor', null)")
        page.wait_for_timeout(2_500)

        is_following = page.evaluate(f"followedAddresses.has('{addr}')")
        if not is_following:
            pytest.skip(
                f"followBettor() did not register in followedAddresses for {addr[:10]}... "
                "— cannot test unfollow cycle (pre-condition not met)"
            )

        page.evaluate("showTab('follows')")
        try:
            page.wait_for_function(
                """() => {
                    const c = document.getElementById('follows-container');
                    return c && c.children.length > 0;
                }""",
                timeout=15_000,
            )
        except Exception:
            pytest.fail(
                "Follows tab did not render the bettor card after following. "
                "Cannot test unfollow cycle without the bettor first appearing."
            )

        container_html_before = page.inner_html("#follows-container")
        assert addr.lower() in container_html_before.lower(), (
            f"Bettor '{addr[:20]}...' not found in #follows-container after follow. "
            "Unfollow cycle pre-condition failed."
        )

        # ── Step 5: Unfollow the bettor ────────────────────────────────────────
        # unfollowFromFollowsTab(address, buttonElement) — pass null for button element
        page.evaluate(f"unfollowFromFollowsTab('{addr}', null)")
        page.wait_for_timeout(2_500)

        # ── Step 6: Assert bettor address is gone from #follows-container ──────
        # Wait for either empty state OR container to no longer contain the address
        try:
            page.wait_for_function(
                f"""() => {{
                    const c = document.getElementById('follows-container');
                    const e = document.getElementById('follows-empty');
                    const addrGone = !c || !c.innerHTML.toLowerCase().includes('{addr.lower()}');
                    const emptyShown = e && !e.classList.contains('hidden');
                    return addrGone || emptyShown;
                }}""",
                timeout=10_000,
            )
        except Exception:
            container_html_after = page.inner_html("#follows-container")
            pytest.fail(
                f"Bettor '{addr[:20]}...' still appears in #follows-container after unfollow. "
                "DELETE /follows/{address} may have failed, or the follows tab did not "
                "re-render after the delete. "
                f"Container HTML (first 400 chars): {container_html_after[:400]}"
            )

        container_html_after = page.inner_html("#follows-container")
        assert addr.lower() not in container_html_after.lower(), (
            f"Bettor '{addr[:20]}...' still in #follows-container HTML after unfollowFromFollowsTab(). "
            "The DELETE /follows/{address} endpoint or client-side follow removal is broken."
        )
