"""
Playwright E2E: Error state and empty state tests.

Verifies that the frontend handles API failures and empty data gracefully:
  1. Leaderboard shows "Could not load leaderboard" on network abort (not blank screen)
  2. Leaderboard shows "Could not load leaderboard" on HTTP 503 (not silent blank)
  3. Consensus tab shows fallback message on API error (not infinite spinner)
  4. Empty follows state shows "No traders followed yet" for a fresh user (not blank div)

Covers backlog items:
  - E2E: Polymarket API timeout → graceful frontend
  - E2E: Backend 503 → frontend shows error (leaderboard + consensus)
  - E2E: Empty follows state

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import time
import pytest
from playwright.sync_api import Page, Route
from .conftest import login, BASE_URL

API_BASE = "http://localhost:8003"


class TestApiErrorGracefulHandling:
    """Verify the frontend shows user-friendly error messages when the API fails.

    These tests intercept network requests at the browser level (route interception)
    to simulate failures that real users would experience during outages.
    """

    def test_browse_leaderboard_network_abort_shows_error_message(self, page: Page):
        """When /bettors request is aborted (network timeout / connection refused),
        the browse leaderboard must show 'Could not load leaderboard' — not a blank
        screen, infinite spinner, or uncaught JS exception.

        Tests the catch(e) handler in loadBrowseLeaderboard() which sets:
          container.innerHTML = '...<h3>Could not load leaderboard</h3>...'
        """
        # Intercept all /bettors requests on this page and abort them
        page.route(
            f"{API_BASE}/bettors**",
            lambda route: route.abort("failed"),
        )

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=12_000)

        # Navigate to public browse view (no login required)
        page.evaluate("showView('browse')")

        # Wait for error state to appear in the browse leaderboard container
        try:
            page.wait_for_function(
                """() => {
                    const body = document.getElementById('browse-leaderboard-body');
                    return body && body.textContent.includes('Could not load');
                }""",
                timeout=10_000,
            )
        except Exception:
            content = page.evaluate(
                """document.getElementById('browse-leaderboard-body')
                   ? document.getElementById('browse-leaderboard-body').textContent.trim().slice(0, 200)
                   : 'element-not-found'"""
            )
            pytest.fail(
                f"Expected 'Could not load leaderboard' after network abort, "
                f"got: {content!r}. "
                "Check loadBrowseLeaderboard() catch handler in index.html."
            )

        error_text = page.evaluate(
            "document.getElementById('browse-leaderboard-body').textContent.trim()"
        )
        assert "Could not load" in error_text, (
            f"Leaderboard must show 'Could not load' on network abort, got: {error_text[:200]!r}"
        )
        # Confirm it's not a blank screen — text must be non-trivially long
        assert len(error_text) > 5, (
            "Error state text is unexpectedly short — leaderboard may be showing a blank div"
        )

    def test_browse_leaderboard_503_response_shows_error_message(self, page: Page):
        """When /bettors returns HTTP 503, the browse leaderboard must show an error
        state with 'Could not load leaderboard' — not a blank div or frozen spinner.

        503 is not-ok, so loadBrowseLeaderboard() throws 'Failed to load leaderboard'
        and the catch handler renders the error state.
        """
        def return_503(route: Route) -> None:
            route.fulfill(
                status=503,
                content_type="application/json",
                body='{"detail": "Service Unavailable"}',
            )

        page.route(f"{API_BASE}/bettors**", return_503)

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=12_000)

        page.evaluate("showView('browse')")

        try:
            page.wait_for_function(
                """() => {
                    const body = document.getElementById('browse-leaderboard-body');
                    return body && body.textContent.includes('Could not load');
                }""",
                timeout=10_000,
            )
        except Exception:
            content = page.evaluate(
                """document.getElementById('browse-leaderboard-body')
                   ? document.getElementById('browse-leaderboard-body').textContent.trim().slice(0, 200)
                   : 'element-not-found'"""
            )
            pytest.fail(
                f"Expected 'Could not load leaderboard' after HTTP 503, got: {content!r}. "
                "A 503 response is not-ok and must trigger the catch handler."
            )

        error_text = page.evaluate(
            "document.getElementById('browse-leaderboard-body').textContent.trim()"
        )
        assert "Could not load" in error_text, (
            f"Leaderboard 503 must show error message, got: {error_text[:200]!r}"
        )

    def test_consensus_api_error_shows_fallback_message(self, page: Page):
        """When /markets/consensus fails (network abort), the Consensus tab must show
        'Could not load consensus signals. Try again later.' — not blank or stuck loading.

        Tests the catch(e) handler in loadConsensus() which sets:
          listEl.innerHTML = '<div>Could not load consensus signals. Try again later.</div>'
        """
        # Intercept only consensus requests — auth and other calls work normally
        page.route(
            f"{API_BASE}/markets/consensus**",
            lambda route: route.abort("failed"),
        )

        login(page, "free")

        # Navigate to Consensus tab (triggers loadConsensus())
        page.evaluate("showTab('consensus')")

        # Wait for the loading indicator to disappear and error text to appear
        try:
            page.wait_for_function(
                """() => {
                    const listEl = document.getElementById('consensus-list');
                    if (!listEl) return false;
                    return listEl.textContent.includes('Could not load');
                }""",
                timeout=10_000,
            )
        except Exception:
            list_content = page.evaluate(
                """document.getElementById('consensus-list')
                   ? document.getElementById('consensus-list').textContent.trim().slice(0, 200)
                   : 'element-not-found'"""
            )
            loading_visible = page.evaluate(
                """(() => {
                    const el = document.getElementById('consensus-loading');
                    return el ? el.style.display !== 'none' : false;
                })()"""
            )
            pytest.fail(
                f"Expected 'Could not load consensus signals' after API abort, "
                f"got: {list_content!r}. "
                f"Loading spinner still visible: {loading_visible}. "
                "Check loadConsensus() catch handler in index.html."
            )

        consensus_text = page.evaluate(
            "document.getElementById('consensus-list').textContent.trim()"
        )
        assert "Could not load" in consensus_text, (
            f"Consensus tab must show fallback on API error, got: {consensus_text[:200]!r}"
        )
        # Loading spinner must be gone (not stuck forever)
        loading_visible = page.evaluate(
            """(() => {
                const el = document.getElementById('consensus-loading');
                return el ? el.style.display !== 'none' : false;
            })()"""
        )
        assert not loading_visible, (
            "Consensus loading spinner is still showing after API error — "
            "the catch handler must hide it."
        )


class TestEmptyStateHandling:
    """Verify the frontend shows correct empty states when there is no data to display."""

    def test_empty_follows_state_shows_message_for_new_user(self, page: Page):
        """A freshly-registered user with zero follows must see the empty-state UI on
        the Follows tab — not a blank div, not a spinner that never resolves.

        The empty state (#follows-empty) is revealed when:
          follows = [] → emptyEl.classList.remove('hidden')

        Visible text: h3 = "No traders followed yet"
        """
        ts = int(time.time())
        email = f"error_state_{ts}@polyedge-test.com"
        password = "TestPass123!"

        # Register a brand-new user — guaranteed 0 follows
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.evaluate("showView('auth', 'register')")
        page.fill("#reg-name", f"ErrorStateUser{ts}")
        page.fill("#reg-email", email)
        page.fill("#reg-password", password)
        page.click("#register-submit")
        page.wait_for_function(
            "!document.getElementById('view-dashboard').classList.contains('hidden')",
            timeout=10_000,
        )

        # Navigate to Follows tab — triggers loadMyFollows()
        page.evaluate("showTab('follows')")

        # Wait for empty state to appear (hidden class removed)
        try:
            page.wait_for_function(
                """() => {
                    const emptyEl = document.getElementById('follows-empty');
                    return emptyEl && !emptyEl.classList.contains('hidden');
                }""",
                timeout=10_000,
            )
        except Exception:
            classes = page.evaluate(
                """document.getElementById('follows-empty')
                   ? document.getElementById('follows-empty').className
                   : 'element-not-found'"""
            )
            pytest.fail(
                f"Expected #follows-empty to be visible for a fresh user with 0 follows, "
                f"got classes: {classes!r}. "
                "Check loadMyFollows() — when follows.length === 0, emptyEl.classList.remove('hidden')"
            )

        # Verify the message is meaningful (not blank)
        empty_text = page.evaluate(
            "document.getElementById('follows-empty').textContent.trim()"
        )
        assert "No traders followed yet" in empty_text, (
            f"Follows empty state must say 'No traders followed yet', got: {empty_text[:200]!r}"
        )
        # Confirm the message contains a call to action (not just h3 title)
        assert "Browse" in empty_text or "leaderboard" in empty_text.lower(), (
            f"Follows empty state must contain a call-to-action to browse the leaderboard, "
            f"got: {empty_text[:200]!r}"
        )
