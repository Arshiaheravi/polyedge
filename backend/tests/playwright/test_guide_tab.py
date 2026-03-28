"""
Playwright E2E: Guide tab renders content for authenticated users.

Verifies that a basic-tier user navigating to the Guide tab sees:
  - #tab-guide loses its 'hidden' class (tab becomes visible)
  - A heading (h1) with content is present inside the guide tab
  - At least one paragraph or content block is rendered (not a blank tab)

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL


def _open_guide_tab(page: Page) -> None:
    """Navigate to the Guide tab using JS (nav elements are display:none at desktop)."""
    page.evaluate("showTab('guide')")
    page.wait_for_function(
        "!document.getElementById('tab-guide').classList.contains('hidden')",
        timeout=8_000,
    )


class TestGuideTab:
    """Guide tab must render content for authenticated users."""

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_guide_tab_becomes_visible(self, page: Page):
        """#tab-guide must lose the 'hidden' class after showTab('guide') is called."""
        login(page, "basic")
        _open_guide_tab(page)

        is_hidden = page.evaluate(
            "() => document.getElementById('tab-guide').classList.contains('hidden')"
        )
        assert not is_hidden, (
            "#tab-guide still has 'hidden' class after showTab('guide') — tab did not become visible"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_guide_tab_has_heading(self, page: Page):
        """#tab-guide must contain an h1 heading with non-empty text."""
        login(page, "basic")
        _open_guide_tab(page)

        heading_text = page.evaluate(
            """() => {
                const h1 = document.querySelector('#tab-guide h1');
                return h1 ? h1.textContent.trim() : null;
            }"""
        )
        assert heading_text is not None, (
            "No <h1> found inside #tab-guide — guide tab may be empty or not rendering"
        )
        assert len(heading_text) > 0, (
            "Guide tab h1 heading is empty"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_guide_tab_has_content_blocks(self, page: Page):
        """#tab-guide must contain at least one content block (div/p) with non-zero size."""
        login(page, "basic")
        _open_guide_tab(page)

        # Count visible content children inside the guide tab
        visible_children = page.evaluate(
            """() => {
                const tab = document.getElementById('tab-guide');
                if (!tab) return 0;
                const children = tab.querySelectorAll('div, p, section, article');
                return Array.from(children).filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                }).length;
            }"""
        )
        assert visible_children > 0, (
            "No visible content blocks found inside #tab-guide — guide tab appears blank"
        )
