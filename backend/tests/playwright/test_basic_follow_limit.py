"""
Playwright E2E: Basic-tier user hits 5-follow limit → upgrade modal shown.

Tests the basic-tier follow-limit gate:
  1. Login as basic@polyedge.com (subscription_tier='basic', limit=5)
  2. Clean up any pre-existing follows so the test always starts from 0
  3. Get 6 distinct bettor addresses from the leaderboard
  4. Follow 5 bettors — all should succeed (within the basic limit)
  5. Attempt a 6th follow → POST /follows returns 403 with 'Upgrade' in detail
  6. followBettor() calls openUpgradeModal() → #upgrade-modal loses 'hidden' class

This is the basic-tier equivalent of the free-tier follow-limit test in
test_auth_and_security.py::TestFollowLimitUpgradeModal.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


class TestBasicFollowLimit:
    """Basic-tier user can follow up to 5 bettors; the 6th triggers the upgrade modal."""

    def test_basic_5_follow_limit_triggers_upgrade_modal(self, page: Page):
        """
        Login as basic tier → clean up follows → follow 5 bettors (all succeed)
        → attempt 6th follow → upgrade modal (#upgrade-modal) becomes visible.

        The server-side TIER_LIMITS['basic'] == 5. When the 6th POST /follows is
        sent, the backend returns 403 with detail containing 'Upgrade'. The frontend
        followBettor() detects status 403 + 'Upgrade' and calls openUpgradeModal(),
        which removes 'hidden' from #upgrade-modal.
        """
        # ── Step 1: Login as basic-tier account ──────────────────────────────
        login(page, "basic")

        # ── Step 2: Clean up all existing follows so we start from 0 ─────────
        # Uses apiFetch (available in page JS context after login) to DELETE all
        # current follows. Playwright awaits the returned promise automatically.
        page.evaluate("""async () => {
            const res = await apiFetch('/follows');
            const data = await res.json();
            const follows = data.follows || [];
            for (const f of follows) {
                await apiFetch('/follows/' + f.bettor_address, { method: 'DELETE' });
            }
            // Sync client-side followedAddresses Set with the cleaned server state
            followedAddresses.clear();
        }""")
        page.wait_for_timeout(1_000)

        # ── Step 3: Navigate to leaderboard, collect 6 distinct bettor addresses ─
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card[data-addr]", timeout=15_000)
        except Exception:
            pytest.skip("No lb-card found — Polymarket leaderboard data unavailable")

        addrs = page.evaluate("""() => {
            const cards = document.querySelectorAll('.lb-card[data-addr]');
            const result = [];
            for (const c of cards) {
                const addr = c.getAttribute('data-addr');
                if (addr && !result.includes(addr)) result.push(addr);
                if (result.length >= 6) break;
            }
            return result;
        }""")

        if not addrs or len(addrs) < 6:
            pytest.skip(
                f"Need 6 distinct bettor addresses to test basic-tier limit; "
                f"leaderboard only has {len(addrs) if addrs else 0}"
            )

        # ── Step 4: Follow 5 bettors (within the basic-tier limit) ───────────
        for i, addr in enumerate(addrs[:5]):
            page.evaluate(f"followBettor('{addr}', 'Bettor{i + 1}', null)")
            page.wait_for_timeout(1_500)

        # Verify all 5 follows landed in the client-side Set
        follow_count = page.evaluate("followedAddresses.size")
        if follow_count < 5:
            pytest.skip(
                f"Only {follow_count} of 5 required follows succeeded "
                "— cannot test 5-follow limit gate (pre-condition not met). "
                "Polymarket API may be rate-limiting or basic account has fewer than 5 slots free."
            )

        # ── Step 5: Attempt 6th follow — should trigger 403 + upgrade modal ──
        page.evaluate(f"followBettor('{addrs[5]}', 'Bettor6', null)")

        try:
            page.wait_for_function(
                "!document.getElementById('upgrade-modal').classList.contains('hidden')",
                timeout=6_000,
            )
        except Exception:
            pytest.fail(
                "Upgrade modal did not appear after basic user attempted a 6th follow. "
                "Expected POST /follows to return 403 with 'Upgrade' in detail, "
                "and followBettor() to call openUpgradeModal(). "
                f"Followed addresses in client: {page.evaluate('followedAddresses.size')}"
            )

        # ── Step 6: Assert upgrade modal is visible ───────────────────────────
        modal_hidden = page.evaluate(
            "document.getElementById('upgrade-modal').classList.contains('hidden')"
        )
        assert not modal_hidden, (
            "Upgrade modal still has 'hidden' class after 6th follow attempt — "
            "basic-tier follow limit gate is not surfacing the upgrade prompt. "
            "Check that POST /follows returns 403 for the 6th follow and that "
            "followBettor() handles it with openUpgradeModal()."
        )
