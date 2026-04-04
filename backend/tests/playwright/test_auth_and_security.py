"""
Playwright E2E: Authentication persistence, bad-token handling, follow-limit upgrade modal,
and XSS safety.

Covers:
  1. Auth persistence across page refresh — pe_token stays, dashboard still shown after reload
  2. Bad token redirect — invalid pe_token cleared and user sent to landing on reload
  3. Follow limit upgrade modal — free user follows 1 bettor, 2nd attempt triggers upgrade modal
  4. XSS safety — username with <script> tag displayed as literal text (not executed)

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import time
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


# ── 1. Auth persistence across page refresh ───────────────────────────────────

class TestAuthPersistence:
    """Login state must survive a full page reload."""

    def test_auth_persists_after_page_refresh(self, page: Page):
        """Logging in then reloading the page must keep the user on the dashboard.

        init() re-reads pe_token from localStorage and calls /auth/me on every page load.
        If the token is valid the user is returned to the dashboard without re-entering
        credentials.
        """
        login(page, "free")

        # Baseline: user is on dashboard before reload
        assert not page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        ), "Not on dashboard after login — baseline failed before testing persistence"

        # Capture the token so we can verify it survives the reload
        token_before = page.evaluate("localStorage.getItem('pe_token')")
        assert token_before, "pe_token not found in localStorage after login"

        # Full page reload — init() re-validates the token via GET /auth/me
        page.reload()
        # Wait for either dashboard (success) or landing (failure) to become visible
        page.wait_for_function(
            "!document.getElementById('view-dashboard').classList.contains('hidden') || "
            "!document.getElementById('view-landing').classList.contains('hidden')",
            timeout=12_000,
        )

        dashboard_hidden = page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        )
        assert not dashboard_hidden, (
            "Dashboard is hidden after page refresh — auth persistence is broken. "
            "User should remain logged in when pe_token is valid in localStorage."
        )

        # Token must still be present (not cleared on valid login)
        token_after = page.evaluate("localStorage.getItem('pe_token')")
        assert token_after, "pe_token was cleared from localStorage after reload — session lost"

    def test_bad_token_redirected_to_landing(self, page: Page):
        """Placing an invalid JWT in localStorage must redirect to the landing page on reload.

        init() calls /auth/me with the bad token → 401 → clearToken() + showView('landing').
        The dashboard must stay hidden and pe_token must be removed.
        """
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Plant a clearly invalid token directly in localStorage
        page.evaluate("localStorage.setItem('pe_token', 'invalid.jwt.token')")

        # Reload — init() finds the token, sends it to /auth/me, gets 401,
        # clears the token, and falls through to showView('landing')
        page.reload()
        page.wait_for_function(
            "!document.getElementById('view-landing').classList.contains('hidden') || "
            "!document.getElementById('view-auth').classList.contains('hidden')",
            timeout=12_000,
        )

        dashboard_hidden = page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        )
        assert dashboard_hidden, (
            "Dashboard is visible after reload with a tampered JWT — "
            "authentication bypass possible!"
        )

        # Invalid token must have been cleared from storage
        token = page.evaluate("localStorage.getItem('pe_token')")
        assert not token, (
            "Invalid pe_token was NOT cleared from localStorage after 401 — "
            "stale bad token persists across sessions."
        )


# ── 2. Follow limit upgrade modal ─────────────────────────────────────────────

class TestFollowLimitUpgradeModal:
    """Free user's second follow attempt must surface the upgrade modal (server 403)."""

    def test_follow_limit_triggers_upgrade_modal(self, page: Page):
        """Register a fresh free user → follow 1 bettor (succeeds) → follow 2nd → upgrade modal.

        Free tier allows exactly 1 follow. The second POST /follows returns 403 with
        detail containing 'Upgrade'. followBettor() calls openUpgradeModal() on that 403,
        which removes 'hidden' from #upgrade-modal.
        """
        unique_email = f"follow_limit_{int(time.time())}@polyedge-test.com"
        password = "TestPass123!"
        name = "FollowLimitTester"

        # ── Register a brand-new free-tier account (0 follows guaranteed) ────
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.evaluate("showView('auth', 'register')")
        page.fill("#reg-name", name)
        page.fill("#reg-email", unique_email)
        page.fill("#reg-password", password)
        page.click("#register-submit")

        page.wait_for_function(
            "!document.getElementById('view-dashboard').classList.contains('hidden')",
            timeout=10_000,
        )

        # ── Navigate to leaderboard and grab 2 distinct bettor addresses ─────
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card", timeout=15_000)
        except Exception:
            pytest.skip("No lb-card found — Polymarket data unavailable for follow limit test")

        addrs = page.evaluate("""() => {
            const cards = document.querySelectorAll('.lb-card[data-addr]');
            const result = [];
            for (const c of cards) {
                const addr = c.getAttribute('data-addr');
                if (addr && !result.includes(addr)) result.push(addr);
                if (result.length >= 2) break;
            }
            return result;
        }""")

        if not addrs or len(addrs) < 2:
            pytest.skip("Fewer than 2 distinct bettor addresses found on leaderboard")

        addr1, addr2 = addrs[0], addrs[1]

        # ── Follow first bettor — should succeed for a fresh free user ───────
        # followBettor(address, name, btn) handles null btn gracefully
        page.evaluate(f"followBettor('{addr1}', 'Bettor1', null)")
        # Wait for the async POST /follows to complete
        page.wait_for_timeout(2_500)

        # Verify first follow registered (followedAddresses Set should contain addr1)
        is_following = page.evaluate(f"followedAddresses.has('{addr1}')")
        if not is_following:
            pytest.skip(
                f"First follow of {addr1[:10]}... did not succeed — "
                "cannot test upgrade modal (pre-condition not met)"
            )

        # ── Follow second bettor — should trigger 403 + upgrade modal ────────
        page.evaluate(f"followBettor('{addr2}', 'Bettor2', null)")

        try:
            page.wait_for_function(
                "!document.getElementById('upgrade-modal').classList.contains('hidden')",
                timeout=5_000,
            )
        except Exception:
            pytest.fail(
                "Upgrade modal did not appear after free user attempted a 2nd follow. "
                "Expected POST /follows to return 403 with 'Upgrade' in detail, "
                "and followBettor() to call openUpgradeModal()."
            )

        modal_hidden = page.evaluate(
            "document.getElementById('upgrade-modal').classList.contains('hidden')"
        )
        assert not modal_hidden, (
            "Upgrade modal still has 'hidden' class after 2nd follow attempt — "
            "follow limit gate is not triggering the upgrade prompt"
        )


# ── 3. XSS safety — username with script tag ──────────────────────────────────

class TestXSSUsernameSafety:
    """Username containing HTML/script tags must be rendered as literal text, never executed."""

    def test_script_tag_in_username_not_executed(self, page: Page):
        """Register with name containing <script>alert('xss')</script>.

        The frontend uses textContent (not innerHTML) to render the account name and
        sidebar name. If this test passes: the script tag is never executed as JavaScript.
        If it fails: the <script> tag was inserted into the DOM and ran (XSS).
        """
        xss_name = "<script>alert('xss')</script>XSSTest"
        unique_email = f"xss_test_{int(time.time())}@polyedge-test.com"
        password = "TestPass123!"

        # Install a dialog handler BEFORE any interaction — catches alert() if fired
        dialog_fired = {"fired": False, "message": ""}

        def on_dialog(dialog):
            dialog_fired["fired"] = True
            dialog_fired["message"] = dialog.message
            dialog.dismiss()

        page.on("dialog", on_dialog)

        # ── Register with the XSS payload as the display name ─────────────────
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.evaluate("showView('auth', 'register')")
        page.fill("#reg-name", xss_name)
        page.fill("#reg-email", unique_email)
        page.fill("#reg-password", password)
        page.click("#register-submit")

        page.wait_for_function(
            "!document.getElementById('view-dashboard').classList.contains('hidden')",
            timeout=10_000,
        )

        # ── Navigate to account tab where #acct-name is rendered ──────────────
        page.evaluate("showTab('account')")
        page.wait_for_timeout(800)  # renderAccount() is synchronous but let paint complete

        # PRIMARY ASSERTION: no browser dialog/alert was triggered
        # If the <script> tag had been executed, alert('xss') would have fired a dialog
        assert not dialog_fired["fired"], (
            f"A browser dialog fired during XSS test! Message: '{dialog_fired['message']}'. "
            "The <script> tag in the username was EXECUTED — innerHTML used instead of textContent!"
        )

        # SECONDARY: the account name element must display the user's name as text
        acct_name_text = page.evaluate(
            "document.getElementById('acct-name')?.textContent?.trim()"
        )
        assert acct_name_text, (
            "Account name element (#acct-name) is empty — registration may have stripped the name"
        )

        # The rendered text must contain the safe part of the name
        assert "XSSTest" in acct_name_text, (
            f"Expected 'XSSTest' in #acct-name textContent, got: '{acct_name_text}'. "
            "Name may have been incorrectly sanitized or not stored."
        )

        # The <script> tag must appear as LITERAL text (not parsed as a DOM element)
        # textContent returns text nodes only — a parsed <script> would NOT appear here
        # but innerHTML would include its outer HTML
        script_as_dom_element = page.evaluate(
            "document.getElementById('acct-name')?.querySelector('script') !== null"
        )
        assert not script_as_dom_element, (
            "A <script> element was found as a child of #acct-name — "
            "the name was rendered via innerHTML and a script tag was injected into the DOM!"
        )
