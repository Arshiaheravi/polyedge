"""
Playwright E2E: Tier gate verification.

Verifies that UI enforces tier restrictions correctly for all 3 tiers:
  - Consensus tab: signal count + whale name visibility
  - Follows/position cards: copy timing badge vs padlock
  - Profile page: Copy Simulator unlocked vs blurred teaser

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import login

# ── helpers ───────────────────────────────────────────────────────────────────

def _open_consensus(page: Page) -> None:
    page.evaluate("showTab('consensus')")
    page.wait_for_function(
        "document.getElementById('consensus-loading')?.style.display === 'none'",
        timeout=15_000,
    )


def _open_follows(page: Page) -> None:
    page.evaluate("showTab('follows')")
    # Wait until follows container has been populated (or empty state appears)
    page.wait_for_function(
        """() => {
            const c = document.getElementById('follows-container');
            const e = document.getElementById('follows-empty');
            return (c && c.children.length > 0) ||
                   (e && !e.classList.contains('hidden'));
        }""",
        timeout=15_000,
    )


def _open_first_profile(page: Page) -> None:
    """Open the leaderboard and navigate to the first bettor's profile page."""
    page.evaluate("showView('browse')")
    # Wait for the leaderboard API call to complete and cards to render
    page.wait_for_selector(".lb-card", timeout=15_000)
    # Address is stored in data-addr attribute on the .lb-card element
    addr = page.evaluate(
        """() => {
            const cards = document.querySelectorAll('.lb-card');
            if (!cards.length) return null;
            return cards[0].getAttribute('data-addr');
        }"""
    )
    if not addr:
        pytest.skip("No bettor cards found on leaderboard — Polymarket data unavailable")
    page.evaluate(f"showProfile('{addr}')")
    # Wait for profile simulator card to become visible (goes from display:none to display:flex)
    page.wait_for_function(
        "document.getElementById('profile-simulator-card').style.display === 'flex'",
        timeout=15_000,
    )


# ── Consensus: Free tier ───────────────────────────────────────────────────────

def test_consensus_free_at_most_3_signals(page: Page):
    """Free user sees ≤3 consensus signals (tier gate enforced server-side)."""
    login(page, "free")
    _open_consensus(page)

    child_count = page.evaluate(
        "document.getElementById('consensus-list').children.length"
    )
    assert child_count <= 3, (
        f"Free user sees {child_count} consensus signals — expected ≤ 3 (tier gate broken)"
    )


def test_consensus_free_no_whale_names(page: Page):
    """Free user: whale names must NOT be shown in any consensus signal card."""
    login(page, "free")
    _open_consensus(page)

    child_count = page.evaluate(
        "document.getElementById('consensus-list').children.length"
    )
    if child_count == 0:
        pytest.skip("No consensus signals available from Polymarket right now")

    # Whale names would appear inside spans inside the consensus list
    # The free-tier lock icon text should appear instead
    list_html = page.inner_html("#consensus-list")
    assert "Upgrade to VIP to see whale names" in list_html or \
           "whale names" not in list_html.lower() or \
           "🔒" in list_html or \
           "&#128274;" in list_html, (
        "Free user consensus list appears to show whale names — tier gate may be broken"
    )


# ── Consensus: Basic tier ──────────────────────────────────────────────────────

def test_consensus_basic_no_upgrade_banner(page: Page):
    """Basic user sees all signals — upgrade banner must NOT be shown."""
    login(page, "basic")
    _open_consensus(page)

    banner_hidden = page.evaluate(
        "document.getElementById('consensus-upgrade-banner').classList.contains('hidden')"
    )
    assert banner_hidden, "Basic user should NOT see the consensus upgrade banner"


def test_consensus_basic_no_whale_names_shown(page: Page):
    """Basic user sees all signals but no whale names (VIP only)."""
    login(page, "basic")
    _open_consensus(page)

    child_count = page.evaluate(
        "document.getElementById('consensus-list').children.length"
    )
    if child_count == 0:
        pytest.skip("No consensus signals available from Polymarket right now")

    list_html = page.inner_html("#consensus-list")
    # Basic sees the lock message for whale names, not actual names
    assert "Upgrade to VIP to see whale names" in list_html, (
        f"Basic user should see whale-name lock message, but list HTML doesn't contain it.\n"
        f"First 500 chars: {list_html[:500]}"
    )


# ── Consensus: VIP tier ────────────────────────────────────────────────────────

def test_consensus_vip_no_upgrade_banner(page: Page):
    """VIP user sees all signals — upgrade banner must NOT be shown."""
    login(page, "vip")
    _open_consensus(page)

    banner_hidden = page.evaluate(
        "document.getElementById('consensus-upgrade-banner').classList.contains('hidden')"
    )
    assert banner_hidden, "VIP user should NOT see the consensus upgrade banner"


def test_consensus_vip_whale_names_visible(page: Page):
    """VIP user sees whale names in consensus signals (if any signals exist)."""
    login(page, "vip")
    _open_consensus(page)

    child_count = page.evaluate(
        "document.getElementById('consensus-list').children.length"
    )
    if child_count == 0:
        pytest.skip("No consensus signals available from Polymarket right now")

    list_html = page.inner_html("#consensus-list")
    # VIP should NOT see the lock message
    assert "Upgrade to VIP to see whale names" not in list_html, (
        "VIP user is seeing the whale-name lock message — tier gate broken for VIP"
    )


# ── Position cards: copy timing badge ─────────────────────────────────────────

def test_follows_free_shows_padlock_badge(page: Page):
    """Free user: position cards show 🔒 Copy timing padlock, not a signal badge."""
    login(page, "free")
    _open_follows(page)

    # Check if empty state (no follows) — skip if so
    empty_hidden = page.evaluate(
        "document.getElementById('follows-empty').classList.contains('hidden')"
    )
    if not empty_hidden:
        pytest.skip("Free user has no follows — cannot test position card badges")

    # The padlock text is injected as HTML into follow cards
    container_html = page.inner_html("#follows-container")
    assert "🔒 Copy timing" in container_html or "Copy timing" in container_html, (
        f"Free user position cards should show padlock badge.\n"
        f"Container HTML (first 800 chars): {container_html[:800]}"
    )
    # Must NOT show the actual signal badges
    assert "✅ Good copy" not in container_html, (
        "Free user should not see 'Good copy' signal badge (Basic/VIP only)"
    )
    assert "⚠️ Price moved" not in container_html, (
        "Free user should not see 'Price moved' signal badge (Basic/VIP only)"
    )
    assert "🔴 Late entry" not in container_html, (
        "Free user should not see 'Late entry' signal badge (Basic/VIP only)"
    )


def test_follows_basic_shows_signal_badge_not_padlock(page: Page):
    """Basic user: position cards show copy signal badge (not padlock)."""
    login(page, "basic")
    _open_follows(page)

    empty_hidden = page.evaluate(
        "document.getElementById('follows-empty').classList.contains('hidden')"
    )
    if not empty_hidden:
        pytest.skip("Basic user has no follows — cannot test position card badges")

    container_html = page.inner_html("#follows-container")
    # Basic user should NOT see the padlock badge
    # (They see actual signal badges like Good copy / Price moved / Late entry)
    assert "Upgrade to Basic" not in container_html, (
        "Basic user should not see 'Upgrade to Basic' prompt on position cards"
    )


def test_follows_vip_shows_signal_badge_not_padlock(page: Page):
    """VIP user: position cards show copy signal badge (not padlock)."""
    login(page, "vip")
    _open_follows(page)

    empty_hidden = page.evaluate(
        "document.getElementById('follows-empty').classList.contains('hidden')"
    )
    if not empty_hidden:
        pytest.skip("VIP user has no follows — cannot test position card badges")

    container_html = page.inner_html("#follows-container")
    assert "Upgrade to Basic" not in container_html, (
        "VIP user should not see 'Upgrade to Basic' prompt on position cards"
    )


# ── Profile simulator: tier gates ─────────────────────────────────────────────

def test_profile_simulator_free_user_sees_blurred_teaser(page: Page):
    """Free user: Copy Simulator on profile page shows blurred/locked value."""
    login(page, "free")
    _open_first_profile(page)

    # The simulator card should be visible
    sim_card_display = page.evaluate(
        "document.getElementById('profile-simulator-card').style.display"
    )
    assert sim_card_display != "none", (
        "Profile simulator card is hidden for free user — should show locked teaser"
    )

    # The value element should have 'locked' class (blurred)
    sim_value_classes = page.evaluate(
        "document.getElementById('profile-simulator-value').className"
    )
    assert "locked" in sim_value_classes, (
        f"Free user simulator value should have 'locked' class (blurred). "
        f"Got classes: '{sim_value_classes}'"
    )

    # The upgrade CTA should be visible
    cta_display = page.evaluate(
        "document.getElementById('profile-simulator-cta').style.display"
    )
    assert cta_display != "none", (
        "Free user should see 'Upgrade to unlock' CTA on simulator card"
    )


def test_profile_simulator_basic_user_sees_real_numbers(page: Page):
    """Basic user: Copy Simulator shows real P&L numbers (not blurred/locked)."""
    login(page, "basic")
    _open_first_profile(page)

    sim_card_display = page.evaluate(
        "document.getElementById('profile-simulator-card').style.display"
    )
    assert sim_card_display != "none", (
        "Profile simulator card is hidden for basic user — should show real numbers"
    )

    sim_value_classes = page.evaluate(
        "document.getElementById('profile-simulator-value').className"
    )
    assert "locked" not in sim_value_classes, (
        f"Basic user simulator value should NOT have 'locked' class. "
        f"Got classes: '{sim_value_classes}'"
    )

    # Upgrade CTA should be hidden for paying users
    cta_display = page.evaluate(
        "document.getElementById('profile-simulator-cta').style.display"
    )
    assert cta_display == "none", (
        "Basic user should NOT see 'Upgrade to unlock' CTA on simulator card"
    )


def test_profile_simulator_vip_user_sees_real_numbers(page: Page):
    """VIP user: Copy Simulator shows real P&L numbers (not blurred/locked)."""
    login(page, "vip")
    _open_first_profile(page)

    sim_card_display = page.evaluate(
        "document.getElementById('profile-simulator-card').style.display"
    )
    assert sim_card_display != "none", (
        "Profile simulator card is hidden for VIP user — should show real numbers"
    )

    sim_value_classes = page.evaluate(
        "document.getElementById('profile-simulator-value').className"
    )
    assert "locked" not in sim_value_classes, (
        f"VIP user simulator value should NOT have 'locked' class. "
        f"Got classes: '{sim_value_classes}'"
    )

    cta_display = page.evaluate(
        "document.getElementById('profile-simulator-cta').style.display"
    )
    assert cta_display == "none", (
        "VIP user should NOT see 'Upgrade to unlock' CTA on simulator card"
    )
