"""
Playwright E2E test: Consensus tab — regression for port-mismatch "Could not load" bug.

Before the fix, the frontend used port 8002 while the backend runs on 8003;
every consensus fetch silently failed and users always saw the error state.
These tests confirm the tab loads real data at port 8003.
"""
import pytest
from playwright.sync_api import Page
from .conftest import login

# ── helpers ──────────────────────────────────────────────────────────────────

def _open_consensus(page: Page) -> None:
    """Navigate to the Consensus tab (nav items are display:none at desktop viewport)."""
    page.evaluate("showTab('consensus')")


def _wait_consensus_loaded(page: Page, timeout: int = 15_000) -> None:
    """Wait until the consensus loading spinner is hidden (both success and error paths hide it)."""
    page.wait_for_function(
        "document.getElementById('consensus-loading')?.style.display === 'none'",
        timeout=timeout,
    )


# ── tests ─────────────────────────────────────────────────────────────────────

def test_consensus_tab_no_error_for_free_user(page: Page):
    """
    CRITICAL regression: free user's Consensus tab must not show
    'Could not load consensus signals' after the port-8003 fix.
    """
    login(page, "free")
    _open_consensus(page)
    _wait_consensus_loaded(page)

    list_html = page.inner_html("#consensus-list")
    assert "Could not load consensus signals" not in list_html, (
        f"Consensus tab still shows the error message — port fix may not have taken effect.\n"
        f"List HTML (first 300 chars): {list_html[:300]}"
    )


def test_consensus_free_tier_sees_at_most_three_signals(page: Page):
    """Free tier: server returns ≤ 3 signals (tier gate enforced server-side)."""
    login(page, "free")
    _open_consensus(page)
    _wait_consensus_loaded(page)

    # Count direct child elements of #consensus-list (each is one signal card)
    child_count = page.evaluate(
        "document.getElementById('consensus-list').children.length"
    )
    assert child_count <= 3, (
        f"Free user sees {child_count} consensus signals — expected ≤ 3 (tier gate broken)"
    )


def test_consensus_free_tier_upgrade_banner_present(page: Page):
    """Free user with ≥1 signal shown: upgrade banner should be visible."""
    login(page, "free")
    _open_consensus(page)
    _wait_consensus_loaded(page)

    child_count = page.evaluate(
        "document.getElementById('consensus-list').children.length"
    )
    if child_count == 0:
        pytest.skip("No consensus signals available from Polymarket right now")

    # If signals exist, the upgrade banner must be shown (free tier has limited access)
    banner_hidden = page.evaluate(
        "document.getElementById('consensus-upgrade-banner').classList.contains('hidden')"
    )
    assert not banner_hidden, (
        "Upgrade banner should be visible for free users when more signals are available"
    )


def test_consensus_ttl_re_fetches_after_reset(page: Page):
    """
    Bug #12 regression: _consensusLoadedAt must be a TTL timestamp, not a permanent flag.
    After resetting _consensusLoadedAt to 0, navigating away and back must re-fetch data.
    """
    login(page, "free")
    _open_consensus(page)
    _wait_consensus_loaded(page)

    # Confirm initial load recorded a timestamp (let vars are not on window — use direct access)
    loaded_at = page.evaluate("_consensusLoadedAt")
    assert loaded_at is not None and loaded_at > 0, (
        f"_consensusLoadedAt should be > 0 after first load, got: {loaded_at}"
    )

    # Reset the TTL to force re-fetch on next tab visit
    page.evaluate("_consensusLoadedAt = 0")

    # Navigate away then back
    page.evaluate("showTab('leaderboard')")
    page.evaluate("showTab('consensus')")
    _wait_consensus_loaded(page)

    # Should have a new timestamp — confirming re-fetch happened
    new_loaded_at = page.evaluate("_consensusLoadedAt")
    assert new_loaded_at is not None and new_loaded_at > 0, (
        f"_consensusLoadedAt should be > 0 after TTL reset + re-visit; "
        "re-fetch did not happen (Bug #12 regression)"
    )


def test_consensus_vip_no_upgrade_banner(page: Page):
    """VIP user sees all signals — upgrade banner must NOT be shown."""
    login(page, "vip")
    _open_consensus(page)
    _wait_consensus_loaded(page)

    # VIP gets all signals, so total_available == signals.length → banner stays hidden
    banner_hidden = page.evaluate(
        "document.getElementById('consensus-upgrade-banner').classList.contains('hidden')"
    )
    assert banner_hidden, "VIP user should NOT see the upgrade banner"


def test_consensus_tab_no_error_for_vip_user(page: Page):
    """VIP user Consensus tab also must not show the error state."""
    login(page, "vip")
    _open_consensus(page)
    _wait_consensus_loaded(page)

    list_html = page.inner_html("#consensus-list")
    assert "Could not load consensus signals" not in list_html, (
        f"VIP Consensus tab shows error. List HTML: {list_html[:300]}"
    )
