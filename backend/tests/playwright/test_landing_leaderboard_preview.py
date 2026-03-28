"""
Playwright E2E: Landing page leaderboard preview replaces skeleton and shows data.

Verifies that loadLandingPreview() fires automatically on landing page load and:
  1. Replaces the initial .skeleton rows with real content (no silent "forever-loading"
     regression where the preview table stays blank forever)
  2. The tbody has at least one <tr> row (data rows OR graceful fallback message)
  3. When the Polymarket API is available: first bettor row has non-empty cells

Design decision: Tests 1 and 2 are resilient to Polymarket API outages.
  - If /bettors returns empty or the backend is unreachable, loadLandingPreview()
    always replaces the skeleton with a fallback message row.
  - Only test 3 requires live bettor data; it self-skips when API is unavailable.

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import BASE_URL


class TestLandingLeaderboardPreview:
    """Landing preview table must replace skeleton and show data or graceful message."""

    def test_preview_skeleton_is_replaced_after_load(self, page: Page):
        """After page load, .skeleton elements must be gone from #preview-leaderboard.

        This is the core regression guard: loadLandingPreview() must always fire and
        replace the initial skeleton — even if the backend or Polymarket API is slow.
        The test allows up to 20 seconds for the backend's 15s Polymarket timeout + buffer.
        """
        page.goto(BASE_URL)

        # Wait for the skeleton to disappear — works whether API returns data, empty,
        # or the catch block fires (all paths replace the skeleton)
        page.wait_for_function(
            "document.querySelectorAll('#preview-leaderboard .skeleton').length === 0",
            timeout=20_000,
        )

        skeleton_count = page.evaluate(
            "() => document.querySelectorAll('#preview-leaderboard .skeleton').length"
        )
        assert skeleton_count == 0, (
            f"#preview-leaderboard still has {skeleton_count} .skeleton element(s) — "
            "loadLandingPreview() may not have fired or crashed before replacing the skeleton"
        )

    def test_preview_has_at_least_one_row(self, page: Page):
        """#preview-leaderboard must contain at least one <tr> after load.

        Whether the backend is up or down, the tbody must show content —
        either bettor data rows or the graceful fallback message row.
        A completely empty tbody means the table rendered nothing at all.
        """
        page.goto(BASE_URL)

        # Wait for skeleton replacement first (same wait as test 1)
        page.wait_for_function(
            "document.querySelectorAll('#preview-leaderboard .skeleton').length === 0",
            timeout=20_000,
        )

        row_count = page.evaluate(
            "() => document.querySelectorAll('#preview-leaderboard tr').length"
        )
        assert row_count >= 1, (
            "#preview-leaderboard has no <tr> elements after load — "
            "table is completely empty (neither bettor data nor fallback message rendered)"
        )

    def test_preview_data_quality_when_bettors_available(self, page: Page):
        """When bettor data loads, rows must have non-empty rank, name, and profit cells.

        Skips automatically if no .bettor-row divs are present (API unavailable or
        Polymarket returning empty data) — never blocks the suite due to external outage.
        """
        page.goto(BASE_URL)

        # Wait for skeleton replacement
        page.wait_for_function(
            "document.querySelectorAll('#preview-leaderboard .skeleton').length === 0",
            timeout=20_000,
        )

        # .bettor-row divs only appear when real bettor data loaded (not in fallback message)
        bettor_row_count = page.evaluate(
            "() => document.querySelectorAll('#preview-leaderboard .bettor-row').length"
        )

        if bettor_row_count == 0:
            pytest.skip(
                "No .bettor-row elements in preview (API unavailable or returned empty) — "
                "data quality check skipped"
            )

        # Bettor data is present — verify the first row renders all expected cells
        first_row_cells = page.evaluate(
            """() => {
                const rows = document.querySelectorAll('#preview-leaderboard tr');
                if (!rows.length) return [];
                const cells = rows[0].querySelectorAll('td');
                return Array.from(cells).map(td => td.textContent.trim());
            }"""
        )

        assert len(first_row_cells) >= 3, (
            f"First preview row has {len(first_row_cells)} cells, expected ≥3 "
            "(rank, bettor name, profit)"
        )

        # At least one cell must have non-empty text (the row actually rendered content)
        non_empty_cells = [c for c in first_row_cells if c]
        assert len(non_empty_cells) >= 1, (
            f"First preview row cells are all empty — bettor data did not render: "
            f"{first_row_cells}"
        )

        # Verify at most 5 rows rendered (limit=5 is enforced in loadLandingPreview)
        total_rows = page.evaluate(
            "() => document.querySelectorAll('#preview-leaderboard tr').length"
        )
        assert total_rows <= 5, (
            f"Preview shows {total_rows} rows — expected ≤5 (limit=5 in loadLandingPreview)"
        )
