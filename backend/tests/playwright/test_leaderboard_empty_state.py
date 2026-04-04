"""
Playwright E2E: Leaderboard "No data yet" empty state.

Verifies that the browse leaderboard shows "No data yet" when the API returns
a successful 200 response with an empty bettors array — as opposed to the
error state ("Could not load leaderboard") shown on API failure.

This covers the distinct empty-list success path:
  API returns {"bettors": [], "cached": false}  →  bettors.length === 0
  → container.innerHTML = '...<h3>No data yet</h3>...'

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import json
import pytest
from playwright.sync_api import Page, Route
from .conftest import BASE_URL, API_BASE


class TestLeaderboardEmptyState:
    """Verify the leaderboard shows the correct empty-list UI on a 200 with no bettors."""

    def test_leaderboard_shows_no_data_yet_when_api_returns_empty_list(self, page: Page):
        """When /bettors returns HTTP 200 with an empty bettors array, the browse
        leaderboard must show 'No data yet' — not 'Could not load leaderboard'
        (which is the error path) and not a blank div.

        Tests the `if (!bettors.length)` branch in loadBrowseLeaderboard() which sets:
          container.innerHTML = '...<h3>No data yet</h3>...'
        """
        def return_empty_bettors(route: Route) -> None:
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"bettors": [], "cached": False}),
            )

        # Intercept all /bettors requests and return an empty successful response
        page.route(f"{API_BASE}/bettors**", return_empty_bettors)

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=12_000)

        # Navigate to the public browse/leaderboard view (no login required)
        page.evaluate("showView('browse')")

        # Wait for "No data yet" to appear in the leaderboard container
        try:
            page.wait_for_function(
                """() => {
                    const body = document.getElementById('browse-leaderboard-body');
                    return body && body.textContent.includes('No data yet');
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
                f"Expected 'No data yet' when /bettors returns empty list (HTTP 200), "
                f"got: {content!r}. "
                "Check loadBrowseLeaderboard() — when bettors.length === 0, "
                "it must render the empty-state div with <h3>No data yet</h3>."
            )

        leaderboard_text = page.evaluate(
            "document.getElementById('browse-leaderboard-body').textContent.trim()"
        )
        assert "No data yet" in leaderboard_text, (
            f"Leaderboard must show 'No data yet' on empty list response, "
            f"got: {leaderboard_text[:200]!r}"
        )
        # Must NOT show the error message — this is a success path, not an error path
        assert "Could not load" not in leaderboard_text, (
            f"Empty list (200) must not trigger the error state 'Could not load', "
            f"got: {leaderboard_text[:200]!r}"
        )
        # The div must have non-trivial content (not just whitespace)
        assert len(leaderboard_text) > 5, (
            "Empty state text is unexpectedly short — leaderboard may be showing a blank div"
        )
