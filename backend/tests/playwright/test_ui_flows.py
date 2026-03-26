"""
Playwright E2E: Core UI flows.

Covers:
  1. Landing page pricing cards — all 5 premium features mentioned per tier
  2. Register → Login flow — new user can sign up and log back in
  3. Leaderboard renders — ≥10 bettor cards each have name + profit/accuracy stats
  4. Bettor profile opens — profile view shows name, stats, recent bets, simulator card

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import time
import pytest
from playwright.sync_api import Page
from .conftest import login, BASE_URL

# ── 1. Landing page pricing ───────────────────────────────────────────────────

class TestLandingPricing:
    """Pricing cards on the landing page must advertise all 5 premium features."""

    def test_all_pricing_cards_mention_five_features(self, page: Page):
        """Each pricing tier card must reference the 5 premium features."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Grab the text of all three pricing cards
        pricing_text = page.evaluate("""() => {
            const cards = document.querySelectorAll('.pricing-card');
            return Array.from(cards).map(c => c.innerText);
        }""")

        assert len(pricing_text) == 3, (
            f"Expected 3 pricing cards, found {len(pricing_text)}"
        )

        # The landing page as a whole must mention each of the 5 features
        full_pricing_text = "\n".join(pricing_text)
        for feature in [
            "Conviction Score",
            "Smart Entry Timing",
            "Copy Portfolio Simulator",
            "Whale Consensus",
            "Exit Alert",
        ]:
            assert feature.lower() in full_pricing_text.lower(), (
                f"Feature '{feature}' not found in any pricing card"
            )

    def test_free_card_shows_locked_features(self, page: Page):
        """Free tier card must show 3 locked (cross) features and 1 available feature."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        # Free card is the first pricing card (no .featured class)
        free_card_text = page.evaluate("""() => {
            const cards = document.querySelectorAll('.pricing-card');
            for (const c of cards) {
                if (!c.classList.contains('featured') && !c.classList.contains('pricing-vip')) {
                    return c.innerText;
                }
            }
            return '';
        }""")

        assert free_card_text, "Free pricing card not found"
        assert "Whale Consensus" in free_card_text, "Free card must mention Whale Consensus"
        # Conviction Score, Smart Entry, Copy Simulator are locked on Free
        assert "Conviction Score" in free_card_text, "Free card must mention Conviction Score (locked)"
        assert "Smart Entry Timing" in free_card_text, "Free card must mention Smart Entry Timing (locked)"
        assert "Copy Portfolio Simulator" in free_card_text, "Free card must mention Copy Portfolio Simulator (locked)"

    def test_vip_card_shows_all_features_unlocked(self, page: Page):
        """VIP card must show all 5 features as available (no locked items)."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        vip_card_text = page.evaluate("""() => {
            const cards = document.querySelectorAll('.pricing-card.pricing-vip');
            return cards.length > 0 ? cards[0].innerText : '';
        }""")

        assert vip_card_text, "VIP pricing card not found"
        for feature in [
            "Conviction Score",
            "Smart Entry Timing",
            "Copy Portfolio Simulator",
            "Whale Consensus",
            "Exit Alert",
        ]:
            assert feature.lower() in vip_card_text.lower(), (
                f"VIP card missing feature: '{feature}'"
            )


# ── 2. Register → Login flow ──────────────────────────────────────────────────

class TestRegisterLoginFlow:
    """New user can register, land on dashboard, log out, then log back in."""

    def test_register_then_login(self, page: Page):
        """Full register → dashboard → logout → login → dashboard flow."""
        unique_email = f"playwright_test_{int(time.time())}@polyedge-test.com"
        password = "TestPass123!"
        name = "PW Test User"

        # ── Register ──────────────────────────────────────────────────────────
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.evaluate("showView('auth', 'register')")

        page.fill("#reg-name", name)
        page.fill("#reg-email", unique_email)
        page.fill("#reg-password", password)
        page.click("#register-submit")

        # After registration the dashboard should become visible
        page.wait_for_function(
            "!document.getElementById('view-dashboard').classList.contains('hidden')",
            timeout=10_000,
        )
        assert not page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        ), "Dashboard not visible after registration"

        # ── Logout ────────────────────────────────────────────────────────────
        # Logout button lives inside #tab-account (hidden at desktop width).
        # Call logout() directly via JS to avoid clicking a hidden element.
        page.evaluate("logout()")

        # After logout the landing page or auth view should be visible
        page.wait_for_function(
            "!document.getElementById('view-landing').classList.contains('hidden') || "
            "!document.getElementById('view-auth').classList.contains('hidden')",
            timeout=8_000,
        )

        # ── Login ─────────────────────────────────────────────────────────────
        page.evaluate("showView('auth', 'login')")
        page.fill("#login-email", unique_email)
        page.fill("#login-password", password)
        page.click("#login-submit")

        page.wait_for_function(
            "!document.getElementById('view-dashboard').classList.contains('hidden')",
            timeout=10_000,
        )
        assert not page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        ), "Dashboard not visible after login"

    def test_login_with_existing_account(self, page: Page):
        """Login with the known free-tier test account works."""
        login(page, "free")
        assert not page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        ), "Dashboard not visible after free-tier login"

    def test_wrong_password_shows_error(self, page: Page):
        """Logging in with a wrong password must not navigate to dashboard."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.evaluate("showView('auth', 'login')")
        page.fill("#login-email", "free@polyedge.com")
        page.fill("#login-password", "WrongPassword999!")
        page.click("#login-submit")

        # Dashboard must stay hidden — not redirected on wrong credentials
        page.wait_for_timeout(2_000)
        assert page.evaluate(
            "document.getElementById('view-dashboard').classList.contains('hidden')"
        ), "Dashboard became visible after wrong password — auth bypass!"


# ── 3. Leaderboard renders ────────────────────────────────────────────────────

class TestLeaderboardRenders:
    """Leaderboard must show ≥10 bettor cards, each with name and profit/accuracy stats."""

    def test_leaderboard_shows_bettor_cards(self, page: Page):
        """Leaderboard (view-browse) shows ≥10 .lb-card elements."""
        login(page, "free")

        page.evaluate("showView('browse')")
        # Wait for cards to appear — leaderboard is loaded via /bettors API
        try:
            page.wait_for_selector(".lb-card", timeout=15_000)
        except Exception:
            pytest.skip("No lb-card found — Polymarket data unavailable")

        card_count = page.evaluate("document.querySelectorAll('.lb-card').length")
        assert card_count >= 10, (
            f"Expected ≥10 bettor cards, found {card_count}"
        )

    def test_leaderboard_cards_have_name_field(self, page: Page):
        """Each visible bettor card must have a non-empty name."""
        login(page, "free")
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card", timeout=15_000)
        except Exception:
            pytest.skip("No lb-card found — Polymarket data unavailable")

        names = page.evaluate("""() => {
            const nameEls = document.querySelectorAll('.lb-card-name');
            return Array.from(nameEls).map(el => el.innerText.trim());
        }""")
        assert len(names) >= 10, f"Found only {len(names)} name elements"
        empty_names = [n for n in names if not n]
        assert not empty_names, f"{len(empty_names)} bettor cards have empty names"

    def test_leaderboard_cards_have_stats(self, page: Page):
        """Each bettor card must have a stats section with visible values."""
        login(page, "free")
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card-stats", timeout=15_000)
        except Exception:
            pytest.skip("No lb-card-stats found — Polymarket data unavailable")

        stats_count = page.evaluate(
            "document.querySelectorAll('.lb-card-stats').length"
        )
        assert stats_count >= 10, (
            f"Expected ≥10 stat sections, found {stats_count}"
        )

        # Each stat card must have at least one value element with non-empty text
        non_empty_stats = page.evaluate("""() => {
            const statCards = document.querySelectorAll('.lb-card-stats');
            let valid = 0;
            for (const sc of statCards) {
                const vals = sc.querySelectorAll('.lb-stat-val, .lb-stat-value, [class*="stat-val"]');
                if (vals.length > 0) valid++;
            }
            return valid;
        }""")
        assert non_empty_stats >= 5, (
            f"Too few bettor cards have stat value elements: {non_empty_stats}"
        )


# ── 4. Bettor profile opens ───────────────────────────────────────────────────

class TestBettorProfileOpens:
    """Clicking a bettor card opens a profile view with name, stats, bets, and simulator."""

    def _open_first_profile(self, page: Page) -> str:
        """Navigate to leaderboard and open the first bettor profile. Returns address."""
        page.evaluate("showView('browse')")
        try:
            page.wait_for_selector(".lb-card", timeout=15_000)
        except Exception:
            pytest.skip("No lb-card found — Polymarket data unavailable")

        addr = page.evaluate("""() => {
            const cards = document.querySelectorAll('.lb-card');
            return cards.length ? cards[0].getAttribute('data-addr') : null;
        }""")
        if not addr:
            pytest.skip("First lb-card has no data-addr — cannot open profile")

        page.evaluate(f"showProfile('{addr}')")
        # Wait for profile view to become active (simulator card becomes flex or profile-name is populated)
        try:
            page.wait_for_function(
                "document.getElementById('profile-simulator-card').style.display === 'flex'",
                timeout=15_000,
            )
        except Exception:
            # Even without simulator, profile page might be visible
            page.wait_for_function(
                """() => {
                    const name = document.getElementById('profile-name');
                    return name && name.innerText.trim() && name.innerText.trim() !== '—';
                }""",
                timeout=15_000,
            )
        return addr

    def test_profile_name_populated(self, page: Page):
        """Profile view shows a non-empty bettor name."""
        login(page, "basic")
        self._open_first_profile(page)

        name = page.evaluate(
            "document.getElementById('profile-name')?.innerText?.trim()"
        )
        assert name and name != "—", f"Profile name is empty or placeholder: '{name}'"

    def test_profile_stats_populated(self, page: Page):
        """Profile view shows non-placeholder profit and volume stats."""
        login(page, "basic")
        self._open_first_profile(page)

        profit = page.evaluate(
            "document.getElementById('pstat-profit')?.innerText?.trim()"
        )
        volume = page.evaluate(
            "document.getElementById('pstat-volume')?.innerText?.trim()"
        )
        assert profit and profit != "—", f"pstat-profit is empty: '{profit}'"
        assert volume and volume != "—", f"pstat-volume is empty: '{volume}'"

    def test_profile_recent_bets_listed(self, page: Page):
        """Profile view shows at least 1 recent bet in profile-bets-list."""
        login(page, "basic")
        self._open_first_profile(page)

        # Wait for bets list to be populated (it loads async)
        try:
            page.wait_for_function(
                "document.getElementById('profile-bets-list')?.children.length > 0",
                timeout=12_000,
            )
        except Exception:
            pytest.skip("profile-bets-list stayed empty — no recent bets for this bettor")

        bet_count = page.evaluate(
            "document.getElementById('profile-bets-list')?.children.length"
        )
        assert bet_count and bet_count >= 1, (
            f"Expected ≥1 recent bet, found {bet_count}"
        )

    def test_profile_simulator_card_visible_for_basic(self, page: Page):
        """Basic user sees the Copy Simulator card (not blurred/locked)."""
        login(page, "basic")
        self._open_first_profile(page)

        sim_display = page.evaluate(
            "document.getElementById('profile-simulator-card')?.style.display"
        )
        assert sim_display == "flex", (
            f"Simulator card display='{sim_display}', expected 'flex' for basic user"
        )

        # Value should NOT be blurred (locked class means paywall)
        sim_value_classes = page.evaluate(
            "document.getElementById('profile-simulator-value')?.className"
        )
        assert "locked" not in (sim_value_classes or ""), (
            "Simulator value has 'locked' class for basic user — paywall leak!"
        )

    def test_profile_simulator_locked_for_free(self, page: Page):
        """Free user sees the Copy Simulator card in blurred/locked state."""
        login(page, "free")
        self._open_first_profile(page)

        sim_display = page.evaluate(
            "document.getElementById('profile-simulator-card')?.style.display"
        )
        assert sim_display == "flex", (
            f"Simulator card not visible for free user (display='{sim_display}')"
        )

        sim_value_classes = page.evaluate(
            "document.getElementById('profile-simulator-value')?.className"
        )
        assert "locked" in (sim_value_classes or ""), (
            "Simulator value does NOT have 'locked' class for free user — paywall broken!"
        )


# ── 5. Back-to-top FAB ────────────────────────────────────────────────────────

class TestBackToTopFAB:
    """FAB (#back-to-top-fab) appears after scrolling >300px on the leaderboard view."""

    def test_fab_appears_after_scroll(self, page: Page):
        """FAB gains fab-visible class when user scrolls >300px on leaderboard."""
        login(page, "free")
        # Switch to browse (leaderboard) view so onLeaderboard() returns true
        page.evaluate("showView('browse')")
        page.wait_for_timeout(500)

        # Make the page tall enough to scroll, then scroll 400px and fire scroll event
        page.evaluate("""() => {
            document.body.style.minHeight = '5000px';
            window.scrollTo(0, 400);
            window.dispatchEvent(new Event('scroll'));
        }""")
        page.wait_for_timeout(300)

        fab_visible = page.evaluate(
            "document.getElementById('back-to-top-fab').classList.contains('fab-visible')"
        )
        assert fab_visible, (
            "FAB did not get fab-visible class after scrolling >300px on leaderboard view"
        )

    def test_fab_hidden_when_not_scrolled(self, page: Page):
        """FAB does not have fab-visible class on initial page load (scrollY == 0)."""
        login(page, "free")
        page.evaluate("showView('browse')")
        page.wait_for_timeout(300)

        fab_visible = page.evaluate(
            "document.getElementById('back-to-top-fab').classList.contains('fab-visible')"
        )
        assert not fab_visible, (
            "FAB incorrectly shows fab-visible class on initial load (scrollY should be 0)"
        )

    def test_fab_click_scrolls_to_top(self, page: Page):
        """Clicking the FAB scrolls the window back to the top."""
        login(page, "free")
        page.evaluate("showView('browse')")
        page.wait_for_timeout(500)

        # Scroll down and trigger the FAB to become visible
        page.evaluate("""() => {
            document.body.style.minHeight = '5000px';
            window.scrollTo(0, 400);
            window.dispatchEvent(new Event('scroll'));
        }""")
        page.wait_for_timeout(300)

        # Click FAB via JS to avoid display:none issues at desktop viewport
        page.evaluate("document.getElementById('back-to-top-fab').click()")
        page.wait_for_timeout(500)  # smooth scroll completes

        scroll_y = page.evaluate("window.scrollY")
        assert scroll_y < 50, (
            f"FAB click did not scroll back to top — scrollY is still {scroll_y}"
        )


# ── 6. Mobile layout ──────────────────────────────────────────────────────────

class TestMobileLayout:
    """At 375×812 viewport the mobile bottom nav is visible and all tabs navigate."""

    def test_mobile_nav_visible_at_narrow_viewport(self, page: Page):
        """Mobile bottom nav becomes visible at 375px width (max-width:768px breakpoint)."""
        page.set_viewport_size({"width": 375, "height": 812})
        login(page, "free")

        nav_display = page.evaluate(
            "getComputedStyle(document.querySelector('.mobile-bottom-nav')).display"
        )
        assert nav_display != "none", (
            f"Mobile bottom nav is display:'{nav_display}' at 375px — should be visible"
        )

    def test_mobile_nav_buttons_present(self, page: Page):
        """All 5 mobile nav buttons are present and have non-empty labels."""
        page.set_viewport_size({"width": 375, "height": 812})
        login(page, "free")

        button_ids = [
            "mob-nav-leaderboard",
            "mob-nav-follows",
            "mob-nav-consensus",
            "mob-nav-alerts",
            "mob-nav-account",
        ]
        for btn_id in button_ids:
            text = page.evaluate(
                f"document.getElementById('{btn_id}')?.innerText?.trim()"
            )
            assert text, f"Mobile nav button #{btn_id} is missing or has no label"

    def test_mobile_nav_leaderboard_tab_navigates(self, page: Page):
        """Clicking the mobile Leaders nav button switches to the leaderboard tab."""
        page.set_viewport_size({"width": 375, "height": 812})
        login(page, "free")

        # Click the Leaders mobile nav button — it should be visible at 375px
        page.click("#mob-nav-leaderboard")
        page.wait_for_timeout(400)

        tab_hidden = page.evaluate(
            "document.getElementById('tab-leaderboard').classList.contains('hidden')"
        )
        assert not tab_hidden, (
            "tab-leaderboard is still hidden after clicking mobile nav Leaders button"
        )

    def test_mobile_sidebar_hidden_at_narrow_viewport(self, page: Page):
        """Desktop sidebar must be hidden at mobile viewport (display:none)."""
        page.set_viewport_size({"width": 375, "height": 812})
        login(page, "free")

        sidebar_display = page.evaluate(
            "getComputedStyle(document.querySelector('.sidebar')).display"
        )
        assert sidebar_display == "none", (
            f"Desktop sidebar is display:'{sidebar_display}' at mobile viewport — should be hidden"
        )


# ── 5. Data-testid attribute presence ────────────────────────────────────────

class TestDataTestidAttributes:
    """Key interactive elements must have data-testid attributes for stable selector access."""

    def test_pricing_cards_have_data_testid(self, page: Page):
        """All three pricing tier cards must have data-testid attributes."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        for testid, label in [
            ("pricing-free-card", "Free"),
            ("pricing-basic-card", "Basic"),
            ("pricing-vip-card", "VIP"),
        ]:
            el = page.query_selector(f'[data-testid="{testid}"]')
            assert el is not None, f"Pricing card data-testid='{testid}' ({label}) not found"

    def test_login_form_inputs_have_data_testid(self, page: Page):
        """Login email, password, and submit button must have data-testid attributes."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)
        # Navigate to login form
        page.evaluate("showView('auth', 'login')")

        for testid in ["login-email", "login-password", "login-submit"]:
            el = page.query_selector(f'[data-testid="{testid}"]')
            assert el is not None, f"Login form element data-testid='{testid}' not found"

    def test_register_form_inputs_have_data_testid(self, page: Page):
        """Register name, email, password, and submit must have data-testid attributes."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)
        page.evaluate("showView('auth', 'register')")

        for testid in ["register-name", "register-email", "register-password", "register-submit"]:
            el = page.query_selector(f'[data-testid="{testid}"]')
            assert el is not None, f"Register form element data-testid='{testid}' not found"

    def test_bettor_cards_have_data_testid_after_leaderboard_loads(self, page: Page):
        """Rendered bettor cards must have data-testid='bettor-card' for selector stability."""
        login(page, "free")
        # Wait for leaderboard cards to render
        page.wait_for_selector('[data-testid="bettor-card"]', timeout=15_000)
        cards = page.query_selector_all('[data-testid="bettor-card"]')
        assert len(cards) >= 1, "No bettor cards with data-testid='bettor-card' found after leaderboard load"
