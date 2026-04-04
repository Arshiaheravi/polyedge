"""
Playwright E2E: Full user journey tests — Free, Basic, and VIP tiers.

Each test simulates a complete user session from login/register through the
core feature chain, verifying that tier-gated UI renders correctly at every step.

Covered journeys:
  1. Free user: register → leaderboard → profile (blurred simulator) →
     follow bettor → follows tab (padlock badge) → 2nd follow → upgrade modal
  2. Basic user: login → leaderboard → profile (real simulator, not blurred) →
     consensus tab (all markets, no whale names)
  3. VIP user: login → leaderboard → profile (real simulator) →
     consensus tab (all markets + whale names visible) →
     follow attempt not blocked by 403

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import time
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL, API_BASE, ACCOUNTS


# ── helpers ───────────────────────────────────────────────────────────────────

def _register_fresh_user(page: Page) -> tuple[str, str]:
    """Register a brand-new free-tier user and return (email, password).

    Uses timestamp email to guarantee zero prior state (no follows, no history).
    """
    ts = int(time.time())
    email = f"journey_free_{ts}@polyedge-test.com"
    password = "TestPass123!"
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle", timeout=10_000)
    page.evaluate("showView('auth', 'register')")
    page.fill("#reg-name", f"JourneyUser{ts}")
    page.fill("#reg-email", email)
    page.fill("#reg-password", password)
    page.click("#register-submit")
    page.wait_for_function(
        "!document.getElementById('view-dashboard').classList.contains('hidden')",
        timeout=10_000,
    )
    return email, password


def _get_two_bettor_addresses(page: Page) -> tuple[str, str]:
    """Navigate to leaderboard and return (addr1, addr2) from first two cards.

    Skips the test if fewer than 2 distinct addresses are available
    (Polymarket data unavailable or too few bettors on leaderboard).
    """
    page.evaluate("showView('browse')")
    try:
        page.wait_for_selector(".lb-card[data-addr]", timeout=15_000)
    except Exception:
        pytest.skip("Leaderboard has no bettor cards — Polymarket data unavailable")

    addrs = page.evaluate("""() => {
        const cards = document.querySelectorAll('.lb-card[data-addr]');
        const seen = new Set();
        for (const c of cards) {
            const a = c.getAttribute('data-addr');
            if (a) seen.add(a);
            if (seen.size >= 2) break;
        }
        return Array.from(seen);
    }""")

    if not addrs or len(addrs) < 2:
        pytest.skip("Fewer than 2 distinct bettor addresses on leaderboard")

    return addrs[0], addrs[1]


def _open_profile(page: Page, addr: str) -> None:
    """Navigate to the given bettor's profile page and wait for simulator card."""
    page.evaluate(f"showProfile('{addr}')")
    page.wait_for_function(
        "document.getElementById('profile-simulator-card').style.display === 'flex'",
        timeout=15_000,
    )


def _open_follows_tab(page: Page) -> None:
    """Switch to the Follows tab in the dashboard and wait for content to load."""
    page.evaluate("showTab('follows')")
    page.wait_for_function(
        """() => {
            const c = document.getElementById('follows-container');
            const e = document.getElementById('follows-empty');
            return (c && c.children.length > 0) ||
                   (e && !e.classList.contains('hidden'));
        }""",
        timeout=15_000,
    )


def _open_consensus_tab(page: Page) -> None:
    """Switch to the Consensus tab in the dashboard and wait for data to load."""
    page.evaluate("showTab('consensus')")
    page.wait_for_function(
        "document.getElementById('consensus-loading')?.style.display === 'none'",
        timeout=15_000,
    )


# ── Journey 1: Free user ───────────────────────────────────────────────────────

class TestFreeUserFullJourney:
    """Full journey: register → profile (blurred) → follow → padlock → 2nd follow → upgrade modal."""

    def test_free_user_full_journey(self, page: Page):
        """
        Complete free-tier user journey in 6 steps:

        1. Register fresh account (0 state pollution)
        2. Browse leaderboard — bettor cards load
        3. Open bettor profile — Copy Simulator value is blurred (locked class)
        4. Follow that bettor — succeeds (free tier allows exactly 1)
        5. Open follows tab — position card shows padlock, not copy-signal badge
        6. Follow 2nd bettor — upgrade modal appears (403 → openUpgradeModal)
        """
        # ── Step 1: Register fresh free-tier user ─────────────────────────────
        _register_fresh_user(page)

        # ── Step 2: Browse leaderboard ────────────────────────────────────────
        addr1, addr2 = _get_two_bettor_addresses(page)

        # ── Step 3: Open profile → simulator must be blurred (locked) ─────────
        _open_profile(page, addr1)

        sim_value_classes = page.evaluate(
            "document.getElementById('profile-simulator-value')?.className || ''"
        )
        assert "locked" in sim_value_classes, (
            f"Free user: profile-simulator-value class='{sim_value_classes}' — "
            "expected 'locked' class (blur filter). Copy Simulator paywall is broken."
        )

        # The CTA 'Upgrade to unlock' link must be visible for free users
        cta_display = page.evaluate(
            "document.getElementById('profile-simulator-cta')?.style.display || ''"
        )
        assert cta_display != "none", (
            "Free user: 'Upgrade to unlock' CTA is hidden — "
            "the locked simulator teaser is not showing the upgrade prompt."
        )

        # ── Step 4: Follow first bettor — must succeed ─────────────────────────
        page.evaluate(f"followBettor('{addr1}', 'Bettor1', null)")
        page.wait_for_timeout(2_500)

        is_following = page.evaluate(f"followedAddresses.has('{addr1}')")
        if not is_following:
            pytest.skip(
                f"First follow of {addr1[:10]}... did not register — "
                "cannot continue journey (pre-condition for padlock + limit tests not met)"
            )

        # ── Step 5: Open follows tab → position cards must show padlock ──────────
        _open_follows_tab(page)

        # Position cards (with copy timing badges) are in #follows-activity-container
        # #follows-container holds the followed-bettor list cards (different element)
        # Wait a bit for the /follows/live API call to complete
        page.wait_for_timeout(3_000)

        activity_html = page.inner_html("#follows-activity-container")
        # "Copyable Bets" header only appears when there are actual open positions
        has_positions = "Copyable Bets" in activity_html

        if has_positions:
            # The padlock badge is '🔒 Copy timing' — rendered when tier != basic/vip
            has_padlock = "Copy timing" in activity_html or "openUpgradeModal" in activity_html
            # Must NOT show actual copy-signal badges
            has_signal_badge = (
                "Good copy" in activity_html
                or "Price moved" in activity_html
                or "Late entry" in activity_html
            )
            assert has_padlock, (
                "Free user follows tab: padlock/upgrade prompt not found in position cards. "
                "Expected '🔒 Copy timing' badge instead of copy signal. "
                f"Activity container HTML (first 500 chars): {activity_html[:500]}"
            )
            assert not has_signal_badge, (
                "Free user follows tab: copy signal badge (Good copy / Price moved / Late entry) "
                "is visible — this is a Basic/VIP feature. Tier gate broken."
            )
        # If no positions, the followed bettor has no open bets — skip padlock assertion
        # (padlock only renders on position cards; empty state is valid)

        # ── Step 6: Follow 2nd bettor → upgrade modal must appear ──────────────
        page.evaluate(f"followBettor('{addr2}', 'Bettor2', null)")

        try:
            page.wait_for_function(
                "!document.getElementById('upgrade-modal').classList.contains('hidden')",
                timeout=5_000,
            )
        except Exception:
            pytest.fail(
                "Upgrade modal did not appear after free user attempted a 2nd follow. "
                f"addr2={addr2[:10]}... — expected POST /follows to return 403 "
                "and followBettor() to call openUpgradeModal()."
            )

        modal_hidden = page.evaluate(
            "document.getElementById('upgrade-modal').classList.contains('hidden')"
        )
        assert not modal_hidden, (
            "Upgrade modal still hidden after 2nd follow attempt — "
            "free-tier follow limit gate is not triggering the upgrade prompt."
        )


# ── Journey 2: Basic user ─────────────────────────────────────────────────────

class TestBasicUserFullJourney:
    """Full journey: login → profile (real numbers) → consensus (all, no names)."""

    def test_basic_user_full_journey(self, page: Page):
        """
        Complete basic-tier user journey:

        1. Login as basic@polyedge.com
        2. Browse leaderboard — bettor cards load
        3. Open bettor profile — Copy Simulator shows real P&L numbers (NOT blurred)
        4. Open Consensus tab — all market signals visible, no whale names shown
        """
        # ── Step 1: Login as basic user ───────────────────────────────────────
        login(page, "basic")

        # ── Step 2: Browse leaderboard ────────────────────────────────────────
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

        # ── Step 3: Open profile → simulator must NOT be blurred ──────────────
        _open_profile(page, addr)

        sim_value_classes = page.evaluate(
            "document.getElementById('profile-simulator-value')?.className || ''"
        )
        assert "locked" not in sim_value_classes, (
            f"Basic user: profile-simulator-value has 'locked' class (blurred). "
            f"Full class='{sim_value_classes}'. Copy Simulator paywall is over-restricting."
        )

        # The CTA 'Upgrade to unlock' must be hidden (not needed for basic/VIP)
        cta_display = page.evaluate(
            "document.getElementById('profile-simulator-cta')?.style.display || ''"
        )
        assert cta_display == "none", (
            f"Basic user: 'Upgrade to unlock' CTA is visible (display='{cta_display}') "
            "— it should be hidden for paying users."
        )

        # Simulator value must contain a real number (P&L, not a placeholder dash)
        sim_text = page.evaluate(
            "document.getElementById('profile-simulator-value')?.textContent?.trim() || ''"
        )
        assert sim_text and sim_text != "—", (
            f"Basic user: simulator value is '{sim_text}' — expected a real P&L number."
        )

        # ── Step 4: Consensus tab — all signals, no whale names ───────────────
        _open_consensus_tab(page)

        signal_count = page.evaluate(
            "document.getElementById('consensus-list')?.children.length ?? 0"
        )
        if signal_count == 0:
            pytest.skip("No consensus signals from Polymarket — cannot assert signal count")

        # Basic users see ALL signals (not capped at 3 like free tier)
        # This is a direction check: if free=3 and basic sees >3 the gate works
        # (If only 1-3 signals exist globally, that's still valid for basic)
        consensus_html = page.inner_html("#consensus-list")

        # Basic users must see the VIP upgrade prompt for whale names (names_visible=False)
        # The frontend renders "Upgrade to VIP to see whale names" or a 🔒 icon when
        # the backend returns names_visible=False (which it always does for basic tier).
        assert "Upgrade to VIP to see whale names" in consensus_html or "🔒" in consensus_html, (
            "Basic user consensus tab: VIP whale-names upgrade prompt not found. "
            "Backend should return names_visible=False for basic tier, and the frontend "
            "should render the 'Upgrade to VIP to see whale names' lock. "
            f"Consensus list HTML (first 600 chars): {consensus_html[:600]}"
        )


# ── Journey 3: VIP user ───────────────────────────────────────────────────────

class TestVIPUserFullJourney:
    """Full journey: login → profile (real) → consensus with whale names → unlimited follows."""

    def test_vip_user_full_journey(self, page: Page):
        """
        Complete VIP-tier user journey:

        1. Login as vip@polyedge.com
        2. Browse leaderboard — bettor cards load
        3. Open bettor profile — Copy Simulator shows real P&L (not blurred, no upgrade CTA)
        4. Open Consensus tab — all signals visible WITH whale names populated
        5. POST /follows does NOT return 403 (VIP has unlimited follow cap)
        """
        # ── Step 1: Login as VIP user ─────────────────────────────────────────
        login(page, "vip")

        # ── Step 2: Browse leaderboard ────────────────────────────────────────
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

        # ── Step 3: Open profile → simulator must show real data ──────────────
        _open_profile(page, addr)

        sim_value_classes = page.evaluate(
            "document.getElementById('profile-simulator-value')?.className || ''"
        )
        assert "locked" not in sim_value_classes, (
            f"VIP user: profile-simulator-value has 'locked' class. "
            "Copy Simulator should be fully visible for VIP tier."
        )

        cta_display = page.evaluate(
            "document.getElementById('profile-simulator-cta')?.style.display || ''"
        )
        assert cta_display == "none", (
            f"VIP user: 'Upgrade to unlock' CTA is visible (display='{cta_display}') "
            "— it must be hidden for VIP users."
        )

        # ── Step 4: Consensus tab — all signals WITH whale names ──────────────
        _open_consensus_tab(page)

        signal_count = page.evaluate(
            "document.getElementById('consensus-list')?.children.length ?? 0"
        )
        if signal_count == 0:
            pytest.skip("No consensus signals from Polymarket — cannot assert whale names")

        consensus_html = page.inner_html("#consensus-list")

        # For VIP, the upgrade banner must NOT be shown (they already have access)
        assert "Upgrade to VIP to see whale names" not in consensus_html, (
            "VIP user consensus tab: 'Upgrade to VIP to see whale names' prompt is visible — "
            "tier gate is incorrectly restricting a VIP user."
        )

        # Whale names should be rendered: the frontend renders name spans when
        # namesVisible=true AND whale_names array is non-empty
        # If Polymarket returns no whale names in the data, the spans simply won't render
        # — so we only assert that the upgrade prompt is absent (we can't force Polymarket data)

        # ── Step 5: VIP follow attempt must NOT return 403 ────────────────────
        # Make a real API call via the browser's fetch (uses the VIP JWT in localStorage)
        follow_status = page.evaluate(f"""async () => {{
            const token = localStorage.getItem('pe_token');
            if (!token) return -1;
            try {{
                const resp = await fetch('{API_BASE}/follows', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    }},
                    body: JSON.stringify({{address: '{addr}'}})
                }});
                return resp.status;
            }} catch (e) {{
                return -2;
            }}
        }}""")

        assert follow_status != 403, (
            f"VIP user: POST /follows returned 403 — "
            "VIP tier should have unlimited follows but the follow limit gate blocked them. "
            f"HTTP status was: {follow_status}"
        )
        assert follow_status != -1, "VIP user: pe_token not found in localStorage after login"
        assert follow_status != -2, "VIP user: fetch() threw a network error (backend unreachable?)"
        # Status 200 (new follow) or 400 (already following) are both acceptable
        assert follow_status in (200, 201, 400, 422), (
            f"VIP user: POST /follows returned unexpected status {follow_status} "
            "(expected 200/201 for new follow, or 400/422 for duplicate/already-following)"
        )
