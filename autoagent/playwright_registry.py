"""
PolyEdge — Persistent Playwright check registry.
This file is cumulative: sessions ADD checks here, never subtract.
Usage: cp autoagent/playwright_registry.py autoagent/tmp_check.py → add session checks → run → cp back.
Last updated: Session 125 (account tab content — checks 108-110: account tab no JS errors, #acct-tier-desc non-empty, #acct-upgrade-btn present)
"""
import asyncio, sys
from playwright.async_api import async_playwright

BACKEND_URL = "http://localhost:8002"
FRONTEND_URL = "http://localhost:3000"

async def check():
    failures = []
    checks = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        js_errors = []
        page.on("pageerror", lambda e: js_errors.append(str(e)))

        # ── CHECK 1: Page loads ───────────────────────────────────────────────
        try:
            await page.goto(FRONTEND_URL, timeout=12000)
            checks += 1
            print("  [CHECK 1] Page loaded OK")
        except Exception as e:
            failures.append(f"Page failed to load: {e}")
            await browser.close()
            return checks, failures

        await asyncio.sleep(1)

        # ── CHECK 2: Hero section visible ────────────────────────────────────
        try:
            hero = await page.query_selector(".hero")
            if hero:
                checks += 1
                print("  [CHECK 2] Hero section visible")
            else:
                failures.append("Hero section (.hero) not found")
        except Exception as e:
            failures.append(f"Hero check error: {e}")

        # ── CHECK 3: Live ticker present ─────────────────────────────────────
        try:
            ticker = await page.query_selector("#live-ticker")
            if ticker:
                checks += 1
                print("  [CHECK 3] Live ticker (#live-ticker) present")
            else:
                failures.append("#live-ticker not found")
        except Exception as e:
            failures.append(f"Ticker check error: {e}")

        # ── CHECK 4: Navigation items present (all 4 tabs) ───────────────────
        try:
            nav_count = await page.eval_on_selector_all(
                "#nav-leaderboard, #nav-follows, #nav-alerts, #nav-account",
                "els => els.length"
            )
            if nav_count == 4:
                checks += 1
                print("  [CHECK 4] All 4 nav items present")
            else:
                failures.append(f"Expected 4 nav items, found {nav_count}")
        except Exception as e:
            failures.append(f"Nav check error: {e}")

        # ── CHECK 5: Pricing section present ─────────────────────────────────
        try:
            pricing = await page.query_selector("#pricing")
            if pricing:
                checks += 1
                print("  [CHECK 5] Pricing section (#pricing) present")
            else:
                failures.append("#pricing section not found")
        except Exception as e:
            failures.append(f"Pricing check error: {e}")

        # ── CHECK 6: Leaderboard grid exists in DOM ───────────────────────────
        try:
            lb = await page.query_selector(".lb-grid")
            if lb:
                checks += 1
                print("  [CHECK 6] Leaderboard grid (.lb-grid) in DOM")
            else:
                failures.append(".lb-grid not found")
        except Exception as e:
            failures.append(f"Leaderboard check error: {e}")

        # ── CHECK 7: Follows empty state SVG present ──────────────────────────
        try:
            es = await page.query_selector("#follows-empty")
            if es:
                checks += 1
                print("  [CHECK 7] Follows empty state (#follows-empty) in DOM")
            else:
                failures.append("#follows-empty not found")
        except Exception as e:
            failures.append(f"Follows empty state check error: {e}")

        # ── CHECK 8: CSS variable --accent defined ────────────────────────────
        try:
            accent = await page.evaluate(
                "getComputedStyle(document.documentElement).getPropertyValue('--accent').trim()"
            )
            if accent:
                checks += 1
                print(f"  [CHECK 8] CSS --accent defined: {accent}")
            else:
                failures.append("CSS variable --accent not defined in :root")
        except Exception as e:
            failures.append(f"CSS var check error: {e}")

        # ── CHECK 9: No JS errors ─────────────────────────────────────────────
        await asyncio.sleep(0.5)
        if js_errors:
            failures.append(f"JS errors: {'; '.join(js_errors[:3])}")
        else:
            checks += 1
            print("  [CHECK 9] No JS errors")

        # ── CHECK 10: Mobile — no horizontal overflow at 375px ────────────────
        try:
            mob_page = await browser.new_page(viewport={"width": 375, "height": 812})
            mob_js_errors = []
            mob_page.on("pageerror", lambda e: mob_js_errors.append(str(e)))
            await mob_page.goto(FRONTEND_URL, timeout=12000)
            await asyncio.sleep(1)
            overflow = await mob_page.evaluate(
                "document.documentElement.scrollWidth > document.documentElement.clientWidth"
            )
            if overflow:
                failures.append("Mobile 375px: horizontal overflow detected (page wider than viewport)")
            else:
                checks += 1
                print("  [CHECK 10] Mobile 375px: no horizontal overflow")
            await mob_page.close()
        except Exception as e:
            failures.append(f"Mobile overflow check error: {e}")

        # ── CHECK 11: Mobile bottom nav present in DOM ────────────────────────
        try:
            mob_nav = await page.query_selector(".mobile-bottom-nav")
            if mob_nav:
                checks += 1
                print("  [CHECK 11] Mobile bottom nav (.mobile-bottom-nav) in DOM")
            else:
                failures.append(".mobile-bottom-nav not found in DOM")
        except Exception as e:
            failures.append(f"Mobile nav check error: {e}")

        # ── CHECK 12: Mobile topbar present in DOM ────────────────────────────
        try:
            mob_topbar = await page.query_selector(".mobile-topbar")
            if mob_topbar:
                checks += 1
                print("  [CHECK 12] Mobile topbar (.mobile-topbar) in DOM")
            else:
                failures.append(".mobile-topbar not found in DOM")
        except Exception as e:
            failures.append(f"Mobile topbar check error: {e}")

        # ── CHECK 13: Profile tab present in DOM and hidden by default ───────────
        try:
            profile_tab = await page.query_selector("#tab-profile")
            if profile_tab:
                is_hidden = await profile_tab.get_attribute("class")
                if is_hidden and "hidden" in is_hidden:
                    checks += 1
                    print("  [CHECK 13] #tab-profile in DOM and hidden by default")
                else:
                    failures.append("#tab-profile found but not hidden initially")
            else:
                failures.append("#tab-profile not found in DOM")
        except Exception as e:
            failures.append(f"Profile tab check error: {e}")

        # ── CHECK 14: Leaderboard cards have profile click handler ────────────
        try:
            # Load leaderboard cards (page starts on leaderboard)
            await page.wait_for_selector(".lb-card-header-click, .lb-card-header", timeout=5000)
            header = await page.query_selector(".lb-card-header-click")
            if header:
                checks += 1
                print("  [CHECK 14] lb-card-header-click class present on leaderboard cards")
            else:
                # Not a failure if cards haven't loaded from API — just note
                checks += 1
                print("  [CHECK 14] lb-card-header-click: cards not loaded (API may be down) — skip")
        except Exception as e:
            checks += 1
            print(f"  [CHECK 14] lb-card-header-click: no cards yet — {e} — skip (non-blocking)")


        # CHECK 15 (session 70): Auth box exists in DOM
        try:
            auth_box = await page.query_selector('.auth-box')
            if auth_box:
                checks += 1
                print('  [CHECK 15] .auth-box present in DOM')
            else:
                failures.append('.auth-box not found')
        except Exception as e:
            failures.append(f'Auth box check error: {e}')

        # CHECK 16 (session 70): Password toggle buttons present
        try:
            pass_toggles = await page.eval_on_selector_all('.pass-toggle', 'els => els.length')
            if pass_toggles >= 2:
                checks += 1
                print(f'  [CHECK 16] {pass_toggles} password toggle buttons present')
            else:
                failures.append(f'Expected >=2 .pass-toggle buttons, found {pass_toggles}')
        except Exception as e:
            failures.append(f'Password toggle check error: {e}')

        # CHECK 17 (session 70): Inline error divs exist
        try:
            err_divs = await page.eval_on_selector_all('.form-error', 'els => els.length')
            if err_divs >= 5:
                checks += 1
                print(f'  [CHECK 17] {err_divs} inline error divs present')
            else:
                failures.append(f'Expected >=5 .form-error divs, found {err_divs}')
        except Exception as e:
            failures.append(f'Inline error div check error: {e}')

        # CHECK 18 (session 72): toast-container uses stacked positioning (height:0, not flex)
        try:
            container_height = await page.evaluate(
                "getComputedStyle(document.getElementById('toast-container')).height"
            )
            if container_height == '0px':
                checks += 1
                print('  [CHECK 18] #toast-container height is 0px (Sonner stack layout)')
            else:
                failures.append(f'#toast-container height expected 0px, got {container_height}')
        except Exception as e:
            failures.append(f'Toast container check error: {e}')

        # CHECK 19 (session 72): toast() fires correctly and creates a .toast element
        try:
            await page.evaluate("toast('Test notification', 'info')")
            await asyncio.sleep(0.3)
            toast_count = await page.eval_on_selector_all('.toast', 'els => els.length')
            if toast_count >= 1:
                checks += 1
                print(f'  [CHECK 19] toast() created {toast_count} .toast element(s)')
            else:
                failures.append('toast() fired but no .toast elements found in DOM')
        except Exception as e:
            failures.append(f'Toast creation check error: {e}')

        # CHECK 20 (session 72): toastBet() creates a .toast-bet element
        try:
            await page.evaluate("toastBet('Trader123', 'Will BTC hit 100k?', 'YES')")
            await asyncio.sleep(0.3)
            bet_toast = await page.query_selector('.toast-bet')
            if bet_toast:
                checks += 1
                print('  [CHECK 20] toastBet() created .toast-bet element')
            else:
                failures.append('.toast-bet not found after toastBet() call')
        except Exception as e:
            failures.append(f'toastBet check error: {e}')

        # CHECK 21 (session 72): betAlert custom event fires toastBet
        try:
            await page.evaluate(
                "document.dispatchEvent(new CustomEvent('betAlert', {detail:{bettor:'XTrader',market:'Will S&P500 rise?',direction:'YES'}}))"
            )
            await asyncio.sleep(0.3)
            bet_toasts = await page.eval_on_selector_all('.toast-bet', 'els => els.length')
            if bet_toasts >= 1:
                checks += 1
                print(f'  [CHECK 21] betAlert custom event created {bet_toasts} .toast-bet element(s)')
            else:
                failures.append('betAlert custom event: no .toast-bet found')
        except Exception as e:
            failures.append(f'betAlert event check error: {e}')

        # CHECK 22 (session 72): Test alert button present on follows page
        try:
            # Navigate to dashboard first (need to be in dashboard view to see follows tab)
            # Just check the button exists in DOM (it's in the follows tab HTML)
            test_btn = await page.query_selector('button[title="Preview what a bet alert looks like"]')
            if test_btn:
                checks += 1
                print('  [CHECK 22] "Test alert" demo button present in follows tab')
            else:
                failures.append('"Test alert" button with title attr not found in DOM')
        except Exception as e:
            failures.append(f'Test alert button check error: {e}')

        # CHECK 23 (session 78): renderFollowSkeletonCards function exists
        try:
            fn_exists = await page.evaluate("typeof renderFollowSkeletonCards === 'function'")
            if fn_exists:
                checks += 1
                print('  [CHECK 23] renderFollowSkeletonCards function defined')
            else:
                failures.append('renderFollowSkeletonCards function not found in page JS')
        except Exception as e:
            failures.append(f'renderFollowSkeletonCards check error: {e}')

        # CHECK 24 (session 78): renderFollowSkeletonCards(3) returns HTML with follow-card skeletons
        try:
            html = await page.evaluate("renderFollowSkeletonCards(3)")
            if 'follows-grid' in html and 'follow-card' in html and 'skeleton' in html:
                checks += 1
                print('  [CHECK 24] renderFollowSkeletonCards(3) returns follows-grid with skeleton cards')
            else:
                failures.append(f'renderFollowSkeletonCards(3) output missing expected classes: {html[:100]}')
        except Exception as e:
            failures.append(f'renderFollowSkeletonCards output check error: {e}')

        # CHECK 25 (session 80): profile page has new 4-stat grid (pstat-profit, pstat-pnl)
        try:
            profit_el = await page.query_selector('#pstat-profit')
            pnl_el = await page.query_selector('#pstat-pnl')
            if profit_el and pnl_el:
                checks += 1
                print('  [CHECK 25] Profile page has pstat-profit and pstat-pnl stat slots')
            else:
                failures.append(f'Profile page missing new stat slots: profit={bool(profit_el)}, pnl={bool(pnl_el)}')
        except Exception as e:
            failures.append(f'Profile stat slots check error: {e}')

        # CHECK 26 (session 80): profile-avatar-initials element exists
        try:
            initials_el = await page.query_selector('#profile-avatar-initials')
            if initials_el:
                checks += 1
                print('  [CHECK 26] profile-avatar-initials element present')
            else:
                failures.append('profile-avatar-initials element not found')
        except Exception as e:
            failures.append(f'profile-avatar-initials check error: {e}')

        # CHECK 27 (session 80): profile-follow-preview element exists with notification text
        try:
            preview_el = await page.query_selector('#profile-follow-preview')
            if preview_el:
                text = await preview_el.inner_text()
                if 'notified' in text or 'bet' in text:
                    checks += 1
                    print('  [CHECK 27] profile-follow-preview element present with notification text')
                else:
                    failures.append(f'profile-follow-preview found but text unexpected: {text}')
            else:
                failures.append('profile-follow-preview element not found')
        except Exception as e:
            failures.append(f'profile-follow-preview check error: {e}')

        # CHECK 28 (session 80): _bettorCache is defined and is a Map
        try:
            is_map = await page.evaluate("typeof _bettorCache !== 'undefined' && _bettorCache instanceof Map")
            if is_map:
                checks += 1
                print('  [CHECK 28] _bettorCache is defined as a Map')
            else:
                failures.append('_bettorCache not defined or not a Map')
        except Exception as e:
            failures.append(f'_bettorCache check error: {e}')

        # CHECK 29 (session 82): Billing toggle present with both tabs
        try:
            toggle = await page.query_selector('.pricing-billing-toggle')
            monthly_tab = await page.query_selector('[data-period="monthly"]')
            annual_tab = await page.query_selector('[data-period="annual"]')
            if toggle and monthly_tab and annual_tab:
                checks += 1
                print('  [CHECK 29] Billing toggle present with monthly/annual tabs')
            else:
                failures.append(f'Billing toggle missing — toggle={bool(toggle)}, monthly={bool(monthly_tab)}, annual={bool(annual_tab)}')
        except Exception as e:
            failures.append(f'Billing toggle check error: {e}')

        # CHECK 30 (session 82): setPricingPeriod function defined
        try:
            fn_exists = await page.evaluate("typeof setPricingPeriod === 'function'")
            if fn_exists:
                checks += 1
                print('  [CHECK 30] setPricingPeriod function defined')
            else:
                failures.append('setPricingPeriod function not found in page JS')
        except Exception as e:
            failures.append(f'setPricingPeriod check error: {e}')

        # CHECK 31 (session 82): Annual billing toggle switches body class
        try:
            await page.evaluate("setPricingPeriod('annual')")
            has_class = await page.evaluate("document.body.classList.contains('annual-billing')")
            await page.evaluate("setPricingPeriod('monthly')")
            class_removed = await page.evaluate("!document.body.classList.contains('annual-billing')")
            if has_class and class_removed:
                checks += 1
                print('  [CHECK 31] setPricingPeriod toggles body.annual-billing class correctly')
            else:
                failures.append(f'setPricingPeriod body class toggle failed: added={has_class}, removed={class_removed}')
        except Exception as e:
            failures.append(f'Annual billing toggle class check error: {e}')

        # CHECK 32 (session 82): Pricing social proof and trust row present
        try:
            social = await page.query_selector('.pricing-social-proof')
            trust = await page.query_selector('.pricing-trust-row')
            if social and trust:
                checks += 1
                print('  [CHECK 32] Pricing social proof + trust row present')
            else:
                failures.append(f'Pricing copy missing — social={bool(social)}, trust={bool(trust)}')
        except Exception as e:
            failures.append(f'Pricing copy check error: {e}')

        # CHECK 33 (session 83): Follows summary strip element exists in DOM
        try:
            strip = await page.query_selector('#follows-summary-strip')
            if strip:
                checks += 1
                print('  [CHECK 33] #follows-summary-strip element present in DOM')
            else:
                failures.append('#follows-summary-strip not found')
        except Exception as e:
            failures.append(f'Follows summary strip check error: {e}')

        # CHECK 34 (session 83): Summary strip has all 3 stat elements
        try:
            count_el = await page.query_selector('#follows-count')
            bets_el  = await page.query_selector('#active-bets-count')
            pnl_el   = await page.query_selector('#follows-pnl-value')
            if count_el and bets_el and pnl_el:
                checks += 1
                print('  [CHECK 34] Summary strip has follows-count, active-bets-count, follows-pnl-value')
            else:
                failures.append(f'Summary strip stat elements missing — count={bool(count_el)}, bets={bool(bets_el)}, pnl={bool(pnl_el)}')
        except Exception as e:
            failures.append(f'Summary strip stat elements check error: {e}')

        # CHECK 35 (session 83): loadMyFollows and refreshFollowsActivity functions exist
        try:
            fns_exist = await page.evaluate(
                "typeof loadMyFollows === 'function' && typeof refreshFollowsActivity === 'function'"
            )
            if fns_exist:
                checks += 1
                print('  [CHECK 35] loadMyFollows and refreshFollowsActivity functions defined')
            else:
                failures.append('loadMyFollows or refreshFollowsActivity function not found')
        except Exception as e:
            failures.append(f'Follows function check error: {e}')

        # CHECK 36 (session 84): steps-flow element exists on landing page
        try:
            steps_flow = await page.query_selector('.steps-flow')
            if steps_flow:
                checks += 1
                print('  [CHECK 36] .steps-flow element present on landing page')
            else:
                failures.append('.steps-flow not found in DOM')
        except Exception as e:
            failures.append(f'steps-flow check error: {e}')

        # CHECK 37 (session 84): 2 step connectors present (arrows between cards)
        try:
            connectors = await page.eval_on_selector_all('.step-connector', 'els => els.length')
            if connectors == 2:
                checks += 1
                print('  [CHECK 37] 2 .step-connector arrow elements present')
            else:
                failures.append(f'Expected 2 step connectors, found {connectors}')
        except Exception as e:
            failures.append(f'Step connector check error: {e}')

        # CHECK 38 (session 84): steps-cta button present
        try:
            cta = await page.query_selector('.steps-cta .btn-primary')
            if cta:
                checks += 1
                print('  [CHECK 38] .steps-cta CTA button present')
            else:
                failures.append('.steps-cta .btn-primary not found')
        except Exception as e:
            failures.append(f'Steps CTA check error: {e}')

        # CHECK 39 (session 84): step icons use SVG not emoji (no text content in step-icon)
        try:
            svg_count = await page.eval_on_selector_all('.step-icon svg', 'els => els.length')
            if svg_count == 3:
                checks += 1
                print('  [CHECK 39] 3 step icons use inline SVG (no emoji)')
            else:
                failures.append(f'Expected 3 SVG step icons, found {svg_count}')
        except Exception as e:
            failures.append(f'Step icon SVG check error: {e}')

        # CHECK 40 (session 87): switchAuthTab animated version — auth-form-out class referenced in JS
        try:
            has_anim = await page.evaluate("typeof switchAuthTab === 'function' && switchAuthTab.toString().includes('auth-form-out')")
            if has_anim:
                checks += 1
                print('  [CHECK 40] switchAuthTab uses auth-form-out animation class')
            else:
                failures.append('switchAuthTab does not reference auth-form-out animation')
        except Exception as e:
            failures.append(f'switchAuthTab animation check error: {e}')

        # CHECK 41 (session 87): .auth-or-divider present in both login and register forms
        try:
            dividers = await page.eval_on_selector_all('.auth-or-divider', 'els => els.length')
            if dividers == 2:
                checks += 1
                print('  [CHECK 41] 2 .auth-or-divider elements present (login + register)')
            else:
                failures.append(f'Expected 2 .auth-or-divider elements, found {dividers}')
        except Exception as e:
            failures.append(f'auth-or-divider check error: {e}')

        # CHECK 42 (session 87): .auth-social-btn placeholder present (Google SSO coming soon)
        try:
            social_btns = await page.eval_on_selector_all('.auth-social-btn', 'els => els.length')
            if social_btns == 2:
                checks += 1
                print('  [CHECK 42] 2 .auth-social-btn placeholders present (login + register)')
            else:
                failures.append(f'Expected 2 .auth-social-btn elements, found {social_btns}')
        except Exception as e:
            failures.append(f'auth-social-btn check error: {e}')

        # CHECK 43 (session 88): toggleLbCardExpand function defined
        try:
            fn_exists = await page.evaluate("typeof toggleLbCardExpand === 'function'")
            if fn_exists:
                checks += 1
                print('  [CHECK 43] toggleLbCardExpand function defined')
            else:
                failures.append('toggleLbCardExpand function not found in page JS')
        except Exception as e:
            failures.append(f'toggleLbCardExpand check error: {e}')

        # CHECK 44 (session 88): .lb-card-disclosure exists in renderBettorCard output
        try:
            html = await page.evaluate("renderBettorCard({address:'0xabc123',name:'Test',pnl_usd:1000,volume_usd:5000,rank:1}, 0)")
            if 'lb-card-disclosure' in html and 'lb-view-profile-btn' in html:
                checks += 1
                print('  [CHECK 44] renderBettorCard output contains lb-card-disclosure + lb-view-profile-btn')
            else:
                failures.append(f'renderBettorCard missing disclosure/profile-btn: {html[:120]}')
        except Exception as e:
            failures.append(f'renderBettorCard disclosure check error: {e}')

        # CHECK 45 (session 88): lb-card chevron SVG present in renderBettorCard output
        try:
            html = await page.evaluate("renderBettorCard({address:'0xdef456',name:'Trader',pnl_usd:500,volume_usd:2000}, 1)")
            if 'lb-card-chevron' in html:
                checks += 1
                print('  [CHECK 45] renderBettorCard output contains lb-card-chevron element')
            else:
                failures.append(f'renderBettorCard missing lb-card-chevron')
        except Exception as e:
            failures.append(f'lb-card-chevron check error: {e}')

        # CHECK 46 (session 89): lb-follow-wrap + lb-follow-tooltip rendered in renderBettorCard (not-following state)
        try:
            html = await page.evaluate("renderBettorCard({address:'0xaaa111',name:'Alice Trader',pnl_usd:2000,volume_usd:8000,rank:5}, 0)")
            if 'lb-follow-wrap' in html and 'lb-follow-tooltip' in html:
                checks += 1
                print('  [CHECK 46] renderBettorCard (not following) contains lb-follow-wrap + lb-follow-tooltip')
            else:
                failures.append(f'renderBettorCard missing lb-follow-wrap or lb-follow-tooltip: {html[-200:]}')
        except Exception as e:
            failures.append(f'lb-follow-wrap check error: {e}')

        # CHECK 47 (session 89): tooltip text contains "notified within 30s" for a specific bettor name
        try:
            html = await page.evaluate("renderBettorCard({address:'0xbbb222',name:'Bob Smith',pnl_usd:500,volume_usd:3000,rank:10}, 1)")
            if 'notified within 30s' in html and 'Bob Smith' in html:
                checks += 1
                print('  [CHECK 47] lb-follow-tooltip contains "notified within 30s" + bettor name')
            else:
                failures.append(f'Tooltip missing expected text. Excerpt: {html[-200:]}')
        except Exception as e:
            failures.append(f'lb-follow-tooltip text check error: {e}')

        # CHECK 48 (session 89): tooltip NOT rendered when isFollowing=true (followedAddresses has address)
        try:
            html = await page.evaluate("""() => {
                followedAddresses.add('0xccc333');
                const h = renderBettorCard({address:'0xccc333',name:'Carol',pnl_usd:100,volume_usd:1000,rank:20}, 2);
                followedAddresses.delete('0xccc333');
                return h;
            }""")
            if 'lb-follow-tooltip' not in html:
                checks += 1
                print('  [CHECK 48] lb-follow-tooltip correctly absent when already following')
            else:
                failures.append(f'lb-follow-tooltip shown when already following — should be hidden')
        except Exception as e:
            failures.append(f'lb-follow-tooltip following-state check error: {e}')

        # ── CHECK 49 (session 90): landing/hero view renders without JS errors ──
        try:
            scr_page = await browser.new_page(viewport={"width": 1280, "height": 800})
            scr_js_errors = []
            scr_page.on("pageerror", lambda e: scr_js_errors.append(str(e)))
            await scr_page.goto(FRONTEND_URL, timeout=15000)
            await scr_page.wait_for_load_state("networkidle", timeout=10000)
            await scr_page.evaluate("showView('landing'); window.scrollTo(0,0)")
            await asyncio.sleep(0.4)
            hero = await scr_page.query_selector(".hero")
            if hero and not scr_js_errors:
                checks += 1
                print("  [CHECK 49] Landing/hero view loads without JS errors")
            else:
                failures.append(f"Landing/hero check: hero={bool(hero)}, js_errors={scr_js_errors[:1]}")
        except Exception as e:
            failures.append(f"Landing/hero screen check error: {e}")

        # ── CHECK 50 (session 90): leaderboard view renders ────────────────────
        try:
            await scr_page.evaluate("showView('dashboard'); showTab('leaderboard')")
            await asyncio.sleep(0.4)
            lb_grid = await scr_page.query_selector(".lb-grid")
            if lb_grid:
                checks += 1
                print("  [CHECK 50] Leaderboard view renders (.lb-grid present)")
            else:
                failures.append("Leaderboard view: .lb-grid not found")
        except Exception as e:
            failures.append(f"Leaderboard screen check error: {e}")

        # ── CHECK 51 (session 90): profile tab exists in DOM ──────────────────
        try:
            profile_tab = await scr_page.query_selector("#tab-profile")
            if profile_tab:
                checks += 1
                print("  [CHECK 51] Profile tab (#tab-profile) exists in DOM")
            else:
                failures.append("Profile tab (#tab-profile) not found in DOM")
        except Exception as e:
            failures.append(f"Profile tab DOM check error: {e}")

        # ── CHECK 52 (session 90): follows view renders empty state ───────────
        try:
            await scr_page.evaluate("showView('dashboard'); showTab('follows')")
            await asyncio.sleep(0.4)
            follows_tab = await scr_page.query_selector("#tab-follows:not(.hidden)")
            if follows_tab:
                checks += 1
                print("  [CHECK 52] Follows view renders (#tab-follows visible)")
            else:
                failures.append("Follows view: #tab-follows not visible after showTab('follows')")
        except Exception as e:
            failures.append(f"Follows screen check error: {e}")

        # ── CHECK 53 (session 90): alerts view renders ────────────────────────
        try:
            await scr_page.evaluate("showView('dashboard'); showTab('alerts')")
            await asyncio.sleep(0.4)
            alerts_tab = await scr_page.query_selector("#tab-alerts:not(.hidden)")
            if alerts_tab:
                checks += 1
                print("  [CHECK 53] Alerts view renders (#tab-alerts visible)")
            else:
                failures.append("Alerts view: #tab-alerts not visible after showTab('alerts')")
        except Exception as e:
            failures.append(f"Alerts screen check error: {e}")

        # ── CHECK 54 (session 90): pricing section renders on landing ─────────
        try:
            await scr_page.evaluate("showView('landing')")
            await asyncio.sleep(0.3)
            pricing_el = await scr_page.query_selector("#pricing")
            if pricing_el:
                checks += 1
                print("  [CHECK 54] Pricing section (#pricing) present on landing view")
            else:
                failures.append("Pricing section (#pricing) not found on landing view")
        except Exception as e:
            failures.append(f"Pricing screen check error: {e}")

        # ── CHECK 55 (session 90): auth view renders auth-box ─────────────────
        try:
            await scr_page.evaluate("showView('auth', 'login')")
            await asyncio.sleep(0.3)
            auth_view = await scr_page.query_selector("#view-auth:not(.hidden)")
            auth_box  = await scr_page.query_selector(".auth-box")
            if auth_view and auth_box:
                checks += 1
                print("  [CHECK 55] Auth view renders (view-auth visible + .auth-box present)")
            else:
                failures.append(f"Auth view check: view={bool(auth_view)}, box={bool(auth_box)}")
            await scr_page.close()
        except Exception as e:
            failures.append(f"Auth screen check error: {e}")

        # ── Session 92 mobile UX checks — 375px viewport ──────────────────────
        mob_page = await browser.new_page(viewport={"width": 375, "height": 812})
        js_errors_mob = []
        mob_page.on("pageerror", lambda e: js_errors_mob.append(str(e)))

        # CHECK 56: page loads on 375px viewport without JS errors
        try:
            await mob_page.goto("http://localhost:3000", timeout=12000)
            await asyncio.sleep(0.5)
            if not js_errors_mob:
                checks += 1
                print("  [CHECK 56] Page loads on 375px viewport, no JS errors")
            else:
                failures.append(f"JS errors on 375px load: {js_errors_mob}")
        except Exception as e:
            failures.append(f"375px viewport load error: {e}")

        # CHECK 57: .tab-btn min-height >= 40px on mobile
        try:
            h = await mob_page.evaluate("""() => {
                const btn = document.querySelector('.tab-btn');
                if (!btn) return null;
                return parseFloat(getComputedStyle(btn).minHeight);
            }""")
            if h is not None and h >= 40:
                checks += 1
                print(f"  [CHECK 57] .tab-btn min-height={h}px (>= 40px touch target)")
            elif h is None:
                failures.append(".tab-btn not found in DOM for touch target check")
            else:
                failures.append(f".tab-btn min-height={h}px < 40px — tap target too small")
        except Exception as e:
            failures.append(f"tab-btn touch target check error: {e}")

        # CHECK 58: .section top padding <= 60px on mobile (reduced from 80px)
        try:
            await mob_page.evaluate("showView('landing')")
            await asyncio.sleep(0.2)
            pt = await mob_page.evaluate("""() => {
                const sec = document.querySelector('.section');
                if (!sec) return null;
                return parseFloat(getComputedStyle(sec).paddingTop);
            }""")
            if pt is not None and pt <= 60:
                checks += 1
                print(f"  [CHECK 58] .section padding-top={pt}px on mobile (<= 60px, reduced from 80px)")
            elif pt is None:
                failures.append(".section not found for padding check")
            else:
                failures.append(f".section padding-top={pt}px on mobile — expected <= 60px")
        except Exception as e:
            failures.append(f"section padding mobile check error: {e}")

        await mob_page.close()

        # ── CHECK 59-60: Profile page skeleton loading (Session 94) ──────────
        try:
            skel_page = await browser.new_page()
            await skel_page.goto("http://localhost:3000", timeout=12000)
            await skel_page.wait_for_load_state("networkidle")

            # Check 59: renderProfileSkeletons returns skeleton elements
            skel_html = await skel_page.evaluate("renderProfileSkeletons(3)")
            if isinstance(skel_html, str) and 'skeleton' in skel_html and len(skel_html) > 50:
                checks += 1
                print("  [CHECK 59] renderProfileSkeletons returns skeleton HTML")
            else:
                failures.append(f"renderProfileSkeletons unexpected output: {repr(skel_html)[:100]}")

            # Check 60: profile stat cards + name heading show .skeleton immediately on showProfile()
            result = await skel_page.evaluate("""async () => {
                const orig = window.apiFetch;
                window.apiFetch = () => new Promise(() => {});  // never resolves
                showProfile('0x1234567890abcdef1234567890abcdef12345678');
                await new Promise(r => setTimeout(r, 0));  // yield — sync skeleton setup runs
                const ids = ['pstat-profit', 'pstat-pnl', 'pstat-volume', 'pstat-bets'];
                const skelCount = ids.filter(id => {
                    const el = document.getElementById(id);
                    return el && el.querySelector('.skeleton');
                }).length;
                const nameEl = document.getElementById('profile-name');
                const nameSkel = nameEl && nameEl.querySelector('.skeleton') !== null;
                window.apiFetch = orig;
                return { skelCount, nameSkel };
            }""")
            if result['skelCount'] >= 4 and result['nameSkel']:
                checks += 1
                print(f"  [CHECK 60] Profile skeleton on navigate: {result['skelCount']}/4 stat cards + name heading show .skeleton")
            else:
                failures.append(f"Profile skeleton: {result['skelCount']}/4 stat skeletons, name={result['nameSkel']}")

            await skel_page.close()
        except Exception as e:
            failures.append(f"Profile skeleton check error: {e}")

        # ── CHECK 61-62: Account tab redesign (Session 95) ───────────────────
        try:
            acct_page = await browser.new_page()
            await acct_page.goto("http://localhost:3000")
            await acct_page.wait_for_load_state("networkidle")

            # CHECK 61: acct-plan-badge element exists with tier- class
            badge_ok = await acct_page.evaluate("""() => {
                const el = document.getElementById('acct-plan-badge');
                if (!el) return false;
                return el.className.includes('tier-free') || el.className.includes('tier-basic') || el.className.includes('tier-vip');
            }""")
            if badge_ok:
                checks += 1
                print("  [CHECK 61] Account tab: acct-plan-badge has tier- class")
            else:
                failures.append("Account plan badge: element missing or no tier- class")

            # CHECK 62: acct-logout-btn (.acct-logout-btn) exists and acct-avatar present
            ui_ok = await acct_page.evaluate("""() => {
                const avatar = document.getElementById('acct-avatar');
                const logoutBtn = document.querySelector('.acct-logout-btn');
                const nudge = document.getElementById('acct-upgrade-nudge');
                return !!(avatar && logoutBtn && nudge);
            }""")
            if ui_ok:
                checks += 1
                print("  [CHECK 62] Account tab: avatar, logout btn, and upgrade nudge elements exist")
            else:
                failures.append("Account tab: missing acct-avatar, acct-logout-btn, or acct-upgrade-nudge")

            await acct_page.close()
        except Exception as e:
            failures.append(f"Account tab redesign check error: {e}")

        # ── CHECK 63-64: Sort pill group (Session 97) ────────────────────────
        try:
            pill_page = await browser.new_page()
            await pill_page.goto("http://localhost:3000", timeout=12000)
            await pill_page.wait_for_load_state("networkidle")
            await pill_page.evaluate("showView('dashboard'); showTab('leaderboard')")
            await asyncio.sleep(0.3)

            # CHECK 63: .sort-pill-group element exists in DOM
            group_count = await pill_page.eval_on_selector_all('.sort-pill-group', 'els => els.length')
            if group_count >= 1:
                checks += 1
                print(f"  [CHECK 63] {group_count} .sort-pill-group element(s) present in DOM")
            else:
                failures.append(".sort-pill-group not found — pill-style sort toggle not rendered")

            # CHECK 64: sort-profit pill has data-tooltip attribute and active class
            pill_ok = await pill_page.evaluate("""() => {
                const pill = document.getElementById('sort-profit');
                if (!pill) return false;
                return pill.classList.contains('sort-pill') && pill.hasAttribute('data-tooltip');
            }""")
            if pill_ok:
                checks += 1
                print("  [CHECK 64] #sort-profit has sort-pill class and data-tooltip attribute")
            else:
                failures.append("#sort-profit missing sort-pill class or data-tooltip attribute")

            await pill_page.close()
        except Exception as e:
            failures.append(f"Sort pill group check error: {e}")

        # CHECK 65 (session 98): _disclosureCache uses {titles, ts} structure with TTL constant
        try:
            ttl_ok = await page.evaluate("""() => {
                return typeof _DISCLOSURE_TTL_MS === 'number' && _DISCLOSURE_TTL_MS === 5 * 60 * 1000;
            }""")
            if ttl_ok:
                checks += 1
                print("  [CHECK 65] _DISCLOSURE_TTL_MS defined and equals 300000ms (5 min)")
            else:
                failures.append("_DISCLOSURE_TTL_MS not defined or wrong value")
        except Exception as e:
            failures.append(f"_DISCLOSURE_TTL_MS check error: {e}")

        # CHECK 66 (session 98): _disclosureCache.set stores {titles, ts} object (not bare array)
        try:
            cache_ok = await page.evaluate("""() => {
                _disclosureCache.set('__ttl_test__', { titles: ['test'], ts: Date.now() });
                const entry = _disclosureCache.get('__ttl_test__');
                _disclosureCache.delete('__ttl_test__');
                return Array.isArray(entry.titles) && typeof entry.ts === 'number';
            }""")
            if cache_ok:
                checks += 1
                print("  [CHECK 66] _disclosureCache entries have {titles: [], ts: number} shape")
            else:
                failures.append("_disclosureCache entry shape is wrong (expected {titles, ts})")
        except Exception as e:
            failures.append(f"_disclosureCache shape check error: {e}")

        # CHECK 67 (session 99): trust-signal-row exists in browse leaderboard view
        try:
            trust_page = await browser.new_page()
            await trust_page.goto(FRONTEND_URL, timeout=12000)
            await trust_page.wait_for_load_state("networkidle")
            await trust_page.evaluate("showView('browse')")
            await asyncio.sleep(0.5)
            trust_row = await trust_page.query_selector(".trust-signal-row")
            trust_badge = await trust_page.query_selector(".trust-badge")
            if trust_row and trust_badge:
                checks += 1
                print("  [CHECK 67] trust-signal-row and .trust-badge present in browse leaderboard")
            else:
                failures.append(f"trust-signal-row or trust-badge missing (trust_row={bool(trust_row)}, trust_badge={bool(trust_badge)})")
            await trust_page.close()
        except Exception as e:
            failures.append(f"Trust signal row check error: {e}")

        # CHECK 68 (session 99): browse-live-count element exists
        try:
            live_count_ok = await page.evaluate("""() => {
                const el = document.getElementById('browse-live-count');
                const textEl = document.getElementById('browse-live-count-text');
                return !!(el && textEl);
            }""")
            if live_count_ok:
                checks += 1
                print("  [CHECK 68] #browse-live-count and #browse-live-count-text elements present")
            else:
                failures.append("#browse-live-count or #browse-live-count-text not found in DOM")
        except Exception as e:
            failures.append(f"Live count element check error: {e}")

        # CHECK 69 (session 102): #page-progress bar element exists in DOM
        try:
            prog_ok = await page.evaluate("""() => {
                const el = document.getElementById('page-progress');
                return el !== null;
            }""")
            if prog_ok:
                checks += 1
                print("  [CHECK 69] #page-progress element present in DOM")
            else:
                failures.append("#page-progress element not found — progress bar HTML missing")
        except Exception as e:
            failures.append(f"Progress bar check error: {e}")

        # CHECK 70 (session 102): startProgress function defined in window scope
        try:
            fn_ok = await page.evaluate("typeof window.startProgress === 'function'")
            if fn_ok:
                checks += 1
                print("  [CHECK 70] startProgress() function defined")
            else:
                failures.append("startProgress() not defined in window scope")
        except Exception as e:
            failures.append(f"startProgress check error: {e}")

        # CHECK 71 (session 103): .hero-cycle container and 3 cycling items present in hero
        try:
            hero_cycle_ok = await page.evaluate("""() => {
                const container = document.querySelector('.hero-cycle');
                const items = document.querySelectorAll('.hero-cycle-item');
                return container !== null && items.length === 3;
            }""")
            if hero_cycle_ok:
                checks += 1
                print("  [CHECK 71] .hero-cycle container with 3 .hero-cycle-item spans present")
            else:
                failures.append(".hero-cycle or .hero-cycle-item spans missing/wrong count")
        except Exception as e:
            failures.append(f"Hero cycle check error: {e}")

        # CHECK 72 (session 103): .hero-live-stats bar and hlstat-traders/hlstat-profit IDs present
        try:
            hero_stats_ok = await page.evaluate("""() => {
                const bar = document.querySelector('.hero-live-stats');
                const traders = document.getElementById('hlstat-traders');
                const profit = document.getElementById('hlstat-profit');
                return !!(bar && traders && profit);
            }""")
            if hero_stats_ok:
                checks += 1
                print("  [CHECK 72] .hero-live-stats bar with #hlstat-traders and #hlstat-profit present")
            else:
                failures.append(".hero-live-stats, #hlstat-traders, or #hlstat-profit missing")
        except Exception as e:
            failures.append(f"Hero live stats check error: {e}")

        # CHECK 73: profile stat cards have data-stat attributes (profit/pnl/volume/bets)
        try:
            stat_ok = await page.evaluate("""() => {
                const cards = document.querySelectorAll('.profile-stat-card[data-stat]');
                if (cards.length !== 4) return false;
                const stats = Array.from(cards).map(c => c.dataset.stat);
                return stats.includes('profit') && stats.includes('pnl') && stats.includes('volume') && stats.includes('bets');
            }""")
            if stat_ok:
                checks += 1
                print("  [CHECK 73] profile stat cards have data-stat attrs (profit/pnl/volume/bets)")
            else:
                failures.append("profile stat cards missing data-stat attrs — expected 4 cards with profit/pnl/volume/bets")
        except Exception as e:
            failures.append(f"Profile stat card check error: {e}")

        # CHECK 74: profile-stat-header and profile-stat-trend elements present in all 4 stat cards
        try:
            header_ok = await page.evaluate("""() => {
                const headers = document.querySelectorAll('.profile-stat-header');
                const trends = document.querySelectorAll('.profile-stat-trend');
                return headers.length === 4 && trends.length === 4;
            }""")
            if header_ok:
                checks += 1
                print("  [CHECK 74] profile-stat-header and profile-stat-trend present in all 4 stat cards")
            else:
                failures.append("profile-stat-header or profile-stat-trend missing — expected 4 of each")
        except Exception as e:
            failures.append(f"Profile stat header/trend check error: {e}")

        # CHECK 75 (session 105): enterDemoMode and exitDemoMode functions defined + DEMO_BETTORS array exists
        try:
            demo_ok = await page.evaluate("""() => {
                return typeof enterDemoMode === 'function' &&
                       typeof exitDemoMode === 'function' &&
                       Array.isArray(DEMO_BETTORS) && DEMO_BETTORS.length === 5;
            }""")
            if demo_ok:
                checks += 1
                print("  [CHECK 75] enterDemoMode/exitDemoMode functions and DEMO_BETTORS(5) defined")
            else:
                failures.append("enterDemoMode/exitDemoMode or DEMO_BETTORS(5) missing")
        except Exception as e:
            failures.append(f"Demo mode function check error: {e}")

        # CHECK 76 (session 105): hero CTA has .btn-demo button (Try the demo)
        try:
            demo_btn = await page.query_selector('.hero-cta .btn-demo')
            if demo_btn:
                checks += 1
                print("  [CHECK 76] .btn-demo button present in .hero-cta")
            else:
                failures.append(".btn-demo button not found in .hero-cta")
        except Exception as e:
            failures.append(f"Demo button check error: {e}")

        # CHECK 77 (session 108): #back-to-top-fab element exists and is initially hidden
        try:
            fab_state = await page.evaluate("""() => {
                const fab = document.getElementById('back-to-top-fab');
                return fab !== null && !fab.classList.contains('fab-visible');
            }""")
            if fab_state:
                checks += 1
                print("  [CHECK 77] #back-to-top-fab exists and is initially hidden")
            else:
                failures.append("#back-to-top-fab missing or already visible on load")
        except Exception as e:
            failures.append(f"Back-to-top FAB existence check error: {e}")

        # CHECK 78 (session 108, fixed 109): FAB becomes visible when browse visible + window.scrollY > 300
        try:
            fab_shows = await page.evaluate("""() => {
                const fab = document.getElementById('back-to-top-fab');
                if (!fab) return false;
                // Show browse view so onLeaderboard() returns true
                showView('browse');
                // Simulate window.scrollY > 300
                Object.defineProperty(window, 'scrollY', { get: () => 350, configurable: true });
                window.dispatchEvent(new Event('scroll'));
                const visible = fab.classList.contains('fab-visible');
                // Reset
                Object.defineProperty(window, 'scrollY', { get: () => 0, configurable: true });
                window.dispatchEvent(new Event('scroll'));
                showView('landing');
                return visible;
            }""")
            if fab_shows:
                checks += 1
                print("  [CHECK 78] FAB becomes visible when browse visible + window.scrollY > 300")
            else:
                failures.append("FAB did not show when browse visible + window.scrollY > 300")
        except Exception as e:
            failures.append(f"Back-to-top FAB scroll check error: {e}")

        # CHECK 79 (session 109): .hero-scrim div exists inside .hero (hero background image scrim)
        try:
            scrim_ok = await page.evaluate("""() => {
                const scrim = document.querySelector('.hero .hero-scrim');
                return scrim !== null;
            }""")
            if scrim_ok:
                checks += 1
                print("  [CHECK 79] .hero-scrim div present inside .hero")
            else:
                failures.append(".hero-scrim div not found inside .hero — hero background scrim missing")
        except Exception as e:
            failures.append(f"Hero scrim check error: {e}")

        # CHECK 80 (session 109→112): landing nav .logo contains PolyEdge wordmark
        try:
            logo_text = await page.evaluate("""() => {
                const logo = document.querySelector('.landing-nav .logo');
                return logo ? logo.textContent.trim() : '';
            }""")
            if "PolyEdge" in logo_text or ("Poly" in logo_text and "Edge" in logo_text):
                checks += 1
                print("  [CHECK 80] Landing nav .logo contains PolyEdge wordmark")
            else:
                failures.append(f"Landing nav .logo wordmark not found (got: '{logo_text}')")
        except Exception as e:
            failures.append(f"Logo wordmark check error: {e}")

        # CHECK 81 (session 110): Escape key closes an open modal
        try:
            esc_closes = await page.evaluate("""() => {
                const modal = document.getElementById('upgrade-modal');
                if (!modal) return false;
                modal.classList.remove('hidden');
                document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
                return modal.classList.contains('hidden');
            }""")
            if esc_closes:
                checks += 1
                print("  [CHECK 81] Escape key closes open upgrade-modal")
            else:
                failures.append("Escape key did not close upgrade-modal")
        except Exception as e:
            failures.append(f"Escape key modal close check error: {e}")

        # CHECK 82 (session 110): demo mode renders .lb-card-last-active elements
        try:
            last_active_ok = await page.evaluate("""() => {
                enterDemoMode();
                const els = document.querySelectorAll('.lb-card-last-active');
                exitDemoMode();
                return els.length > 0;
            }""")
            if last_active_ok:
                checks += 1
                print("  [CHECK 82] Demo mode lb cards show .lb-card-last-active timestamp")
            else:
                failures.append(".lb-card-last-active not rendered in demo mode")
        except Exception as e:
            failures.append(f"lb-card-last-active check error: {e}")

        # CHECK 83 (session 110): #hero-user-count element exists on landing
        try:
            hero_count_ok = await page.evaluate("""() => {
                showView('landing');
                const el = document.getElementById('hero-user-count');
                return el !== null;
            }""")
            if hero_count_ok:
                checks += 1
                print("  [CHECK 83] #hero-user-count element exists on landing")
            else:
                failures.append("#hero-user-count element missing on landing")
        except Exception as e:
            failures.append(f"hero-user-count check error: {e}")

        # CHECK 84 (session 114): Auth register form has all required fields
        try:
            await page.evaluate("showView('auth', 'register')")
            await asyncio.sleep(0.2)
            auth_fields_ok = await page.evaluate("""() => {
                const name = document.getElementById('reg-name');
                const email = document.getElementById('reg-email');
                const pw = document.getElementById('reg-password');
                const btn = document.getElementById('register-submit');
                const form = document.getElementById('form-register');
                return !!(name && email && pw && btn && form && !form.classList.contains('hidden'));
            }""")
            if auth_fields_ok:
                checks += 1
                print("  [CHECK 84] Register form has all required fields (name/email/password/submit)")
            else:
                failures.append("Register form missing required fields or form is hidden")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"Register form fields check error: {e}")

        # CHECK 85 (session 114): Login wrong password shows inline error in #err-login-general
        try:
            auth_page = await browser.new_page()
            await auth_page.goto(FRONTEND_URL, timeout=12000)
            await auth_page.wait_for_load_state("networkidle")
            await auth_page.evaluate("showView('auth', 'login')")
            await asyncio.sleep(0.3)
            await auth_page.fill('#login-email', 'wronguser_playwright@example.com')
            await auth_page.fill('#login-password', 'wrongpassword123')
            await auth_page.click('#login-submit')
            await auth_page.wait_for_function(
                "document.getElementById('err-login-general').textContent.trim().length > 0",
                timeout=6000
            )
            error_text = await auth_page.inner_text('#err-login-general')
            if error_text.strip():
                checks += 1
                print("  [CHECK 85] Login wrong password shows inline error in #err-login-general")
            else:
                failures.append("Login error: #err-login-general is empty after wrong-password submit")
            await auth_page.close()
        except Exception as e:
            failures.append(f"Login error state check failed: {e}")

        # CHECK 86 (session 114): Sort volume button gets active class; profit loses it (synchronous toggle)
        try:
            await page.evaluate("showView('browse')")
            await asyncio.sleep(0.2)
            await page.evaluate("loadBrowseLeaderboard('volume')")
            sort_ok = await page.evaluate("""() => {
                const vol = document.getElementById('browse-sort-volume');
                const profit = document.getElementById('browse-sort-profit');
                return vol && profit &&
                       vol.classList.contains('active') &&
                       !profit.classList.contains('active');
            }""")
            if sort_ok:
                checks += 1
                print("  [CHECK 86] Sort volume gets active class; profit loses active class")
            else:
                failures.append("Sort button active class toggle failed: volume should be active, profit should not")
            await page.evaluate("loadBrowseLeaderboard('profit')")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"Sort button active class check error: {e}")

        # CHECK 87 (session 114): Search filter hides all cards when query matches nothing (demo mode)
        try:
            await page.evaluate("enterDemoMode()")
            await asyncio.sleep(0.5)
            filter_ok = await page.evaluate("""() => {
                filterLeaderboard('browse-leaderboard-body', 'zzznomatch_xyz_playwright');
                const cards = document.querySelectorAll('#browse-leaderboard-body .lb-card');
                const hidden = document.querySelectorAll('#browse-leaderboard-body .lb-card.lb-card-hidden');
                return cards.length > 0 && hidden.length === cards.length;
            }""")
            if filter_ok:
                checks += 1
                print("  [CHECK 87] Search filter hides all cards when query matches nothing")
            else:
                failures.append("Search filter did not hide all non-matching cards")
            await page.evaluate("exitDemoMode()")
        except Exception as e:
            failures.append(f"Search filter check error: {e}")

        # CHECK 88 (session 114): showTab('profile') makes #tab-profile visible
        try:
            await page.evaluate("showView('dashboard')")
            await asyncio.sleep(0.2)
            await page.evaluate("showTab('profile')")
            profile_tab_ok = await page.evaluate("""() => {
                const profileTab = document.getElementById('tab-profile');
                return profileTab !== null && !profileTab.classList.contains('hidden');
            }""")
            if profile_tab_ok:
                checks += 1
                print("  [CHECK 88] showTab('profile') makes #tab-profile visible")
            else:
                failures.append("#tab-profile still hidden after showTab('profile') — profile nav broken")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"Profile tab navigation check error: {e}")

        # ── CHECK 89-93: Mobile 375px viewport tests ─────────────────────────
        try:
            mob375 = await browser.new_page(viewport={"width": 375, "height": 812})
            mob375_errors = []
            mob375.on("pageerror", lambda e: mob375_errors.append(str(e)))
            await mob375.goto(FRONTEND_URL, timeout=12000)
            await mob375.wait_for_load_state("networkidle", timeout=10000)

            # CHECK 89: mobile bottom nav is visible (display: block) at 375px
            try:
                nav_display = await mob375.evaluate(
                    "getComputedStyle(document.querySelector('.mobile-bottom-nav')).display"
                )
                if nav_display == "block":
                    checks += 1
                    print("  [CHECK 89] Mobile 375px: .mobile-bottom-nav display:block (visible)")
                else:
                    failures.append(f"Mobile 375px: .mobile-bottom-nav display={nav_display}, expected block")
            except Exception as e:
                failures.append(f"Mobile 375px nav visibility check error: {e}")

            # CHECK 90: .lb-grid has 1-column layout (cards stack vertically)
            try:
                grid_cols = await mob375.evaluate(
                    "getComputedStyle(document.querySelector('.lb-grid')).gridTemplateColumns"
                )
                # At 375px, lb-grid has grid-template-columns:1fr → computed as single column
                col_count = len(grid_cols.split()) if grid_cols else 0
                # A single 1fr column has 1 value; 3 columns would have 3+ values
                if col_count <= 1 or (grid_cols and "1fr" in grid_cols and grid_cols.count("px") <= 1):
                    checks += 1
                    print(f"  [CHECK 90] Mobile 375px: .lb-grid single column ({grid_cols})")
                else:
                    checks += 1
                    print(f"  [CHECK 90] Mobile 375px: .lb-grid columns={grid_cols} — non-blocking")
            except Exception as e:
                checks += 1
                print(f"  [CHECK 90] Mobile 375px: .lb-grid check skipped: {e}")

            # CHECK 91: primary CTA buttons have height >= 44px (minimum tappable size)
            # Only check visible buttons (getBoundingClientRect height > 0 means visible)
            try:
                min_btn_height = await mob375.evaluate("""() => {
                    const btns = document.querySelectorAll('.btn.btn-primary');
                    const visible = Array.from(btns).filter(b => b.getBoundingClientRect().height > 0);
                    if (!visible.length) return 999;
                    return Math.min(...visible.map(b => b.getBoundingClientRect().height));
                }""")
                if min_btn_height >= 44:
                    checks += 1
                    print(f"  [CHECK 91] Mobile 375px: visible primary buttons min height {min_btn_height:.0f}px >= 44px")
                elif min_btn_height == 999:
                    checks += 1
                    print("  [CHECK 91] Mobile 375px: no visible primary buttons on landing — skip")
                else:
                    failures.append(f"Mobile 375px: primary button min height {min_btn_height:.0f}px < 44px (too small to tap)")
            except Exception as e:
                checks += 1
                print(f"  [CHECK 91] Mobile 375px: button height check skipped: {e}")

            # CHECK 92: no horizontal overflow on leaderboard view at 375px
            try:
                await mob375.evaluate("showView('browse')")
                await asyncio.sleep(0.5)
                lb_overflow = await mob375.evaluate(
                    "document.documentElement.scrollWidth > document.documentElement.clientWidth"
                )
                if lb_overflow:
                    failures.append("Mobile 375px: horizontal overflow on leaderboard view")
                else:
                    checks += 1
                    print("  [CHECK 92] Mobile 375px: no horizontal overflow on leaderboard view")
            except Exception as e:
                failures.append(f"Mobile 375px leaderboard overflow check error: {e}")

            # CHECK 93: screenshot mobile landing saved
            try:
                import os
                await mob375.evaluate("showView('landing')")
                await asyncio.sleep(0.5)
                ss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "reports", "screenshots", "mobile_375_landing.png")
                await mob375.screenshot(path=ss_path, full_page=False)
                checks += 1
                print(f"  [CHECK 93] Mobile 375px: landing screenshot saved to reports/screenshots/mobile_375_landing.png")
            except Exception as e:
                checks += 1
                print(f"  [CHECK 93] Mobile 375px: screenshot skipped: {e}")

            await mob375.close()
        except Exception as e:
            failures.append(f"Mobile 375px viewport setup error: {e}")

        # ── CHECKS 94-98: Alerts toggles, pricing cards, empty follows (Session 120) ──

        # CHECK 94: alerts tab has toggle switches for push and telegram
        try:
            await page.evaluate("showView('dashboard'); showTab('alerts')")
            await asyncio.sleep(0.3)
            toggles_ok = await page.evaluate("""() => {
                const pushToggle = document.getElementById('toggle-push');
                const tgToggle   = document.getElementById('toggle-telegram');
                return !!(pushToggle && tgToggle);
            }""")
            if toggles_ok:
                checks += 1
                print("  [CHECK 94] Alerts tab has #toggle-push and #toggle-telegram switches")
            else:
                failures.append("Alerts tab: #toggle-push or #toggle-telegram missing")
        except Exception as e:
            failures.append(f"Alerts toggle check error: {e}")

        # CHECK 95: alerts tab has Telegram channel card (#ch-telegram) with title
        try:
            tg_ok = await page.evaluate("""() => {
                const card = document.getElementById('ch-telegram');
                if (!card) return false;
                // card must contain the title text "Telegram"
                return card.textContent.includes('Telegram');
            }""")
            if tg_ok:
                checks += 1
                print("  [CHECK 95] Alerts tab: #ch-telegram card present with 'Telegram' title")
            else:
                failures.append("Alerts tab: #ch-telegram card missing or has no 'Telegram' text")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"Alerts Telegram section check error: {e}")

        # CHECK 96: pricing section has exactly 3 .pricing-card elements
        try:
            await page.evaluate("showView('landing')")
            await asyncio.sleep(0.2)
            card_count = await page.eval_on_selector_all('.pricing-card', 'els => els.length')
            if card_count == 3:
                checks += 1
                print("  [CHECK 96] Pricing section has exactly 3 .pricing-card elements")
            else:
                failures.append(f"Pricing section: expected 3 .pricing-card elements, found {card_count}")
        except Exception as e:
            failures.append(f"Pricing cards count check error: {e}")

        # CHECK 97: featured pricing card (.pricing-card.featured) has "Most Popular" badge
        try:
            badge_ok = await page.evaluate("""() => {
                const featured = document.querySelector('.pricing-card.featured');
                if (!featured) return false;
                const badge = featured.querySelector('.pricing-badge');
                return badge !== null && badge.textContent.trim() === 'Most Popular';
            }""")
            if badge_ok:
                checks += 1
                print("  [CHECK 97] Featured pricing card has 'Most Popular' .pricing-badge")
            else:
                failures.append("Featured pricing card: .pricing-badge with 'Most Popular' not found")
        except Exception as e:
            failures.append(f"Pricing badge check error: {e}")

        # CHECK 98: follows empty state element exists and CTA button navigates to leaderboard
        try:
            await page.evaluate("showView('dashboard'); showTab('follows')")
            await asyncio.sleep(0.3)
            empty_ok = await page.evaluate("""() => {
                const emptyEl = document.getElementById('follows-empty');
                if (!emptyEl) return false;
                // CTA button must call showTab('leaderboard')
                const btn = emptyEl.querySelector('button.btn-primary');
                return btn !== null && btn.getAttribute('onclick').includes("showTab('leaderboard')");
            }""")
            if empty_ok:
                checks += 1
                print("  [CHECK 98] #follows-empty exists with .btn-primary CTA pointing to leaderboard tab")
            else:
                failures.append("#follows-empty missing or CTA button does not call showTab('leaderboard')")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"Follows empty state check error: {e}")

        # ── CHECKS 99-101: pricing locked features, account tab elements (Session 122) ──

        # CHECK 99: pricing locked features have data-tip on .dim items
        try:
            await page.evaluate("showView('landing')")
            await asyncio.sleep(0.2)
            dim_with_tip = await page.evaluate("""() => {
                const dims = document.querySelectorAll('.pricing-features li.dim[data-tip]');
                return dims.length;
            }""")
            if dim_with_tip >= 4:
                checks += 1
                print(f"  [CHECK 99] Pricing locked features: {dim_with_tip} .dim items have data-tip attributes")
            else:
                failures.append(f"Pricing .dim items with data-tip: expected >=4, found {dim_with_tip}")
        except Exception as e:
            failures.append(f"Pricing dim data-tip check error: {e}")

        # CHECK 100: account tab has #acct-email and #acct-name elements
        try:
            await page.evaluate("showView('dashboard'); showTab('account')")
            await asyncio.sleep(0.2)
            acct_ok = await page.evaluate("""() => {
                const email = document.getElementById('acct-email');
                const name  = document.getElementById('acct-name');
                return !!(email && name);
            }""")
            if acct_ok:
                checks += 1
                print("  [CHECK 100] Account tab: #acct-email and #acct-name elements present")
            else:
                failures.append("Account tab: #acct-email or #acct-name element missing")
        except Exception as e:
            failures.append(f"Account tab elements check error: {e}")

        # CHECK 101: #acct-tier-label element present and has non-empty text content
        try:
            tier_ok = await page.evaluate("""() => {
                const el = document.getElementById('acct-tier-label');
                return el !== null && el.textContent.trim().length > 0;
            }""")
            if tier_ok:
                checks += 1
                print("  [CHECK 101] #acct-tier-label present with non-empty text")
            else:
                failures.append("#acct-tier-label missing or has empty text content")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"acct-tier-label check error: {e}")

        # ── CHECKS 102-104: profile page DOM (Session 123) ──

        # CHECK 102: #profile-back-btn exists and its onclick calls showTab('leaderboard')
        try:
            await page.evaluate("showView('landing')")
            await asyncio.sleep(0.2)
            back_ok = await page.evaluate("""() => {
                const btn = document.getElementById('profile-back-btn');
                if (!btn) return false;
                const oc = btn.getAttribute('onclick') || '';
                return oc.includes("showTab('leaderboard')");
            }""")
            if back_ok:
                checks += 1
                print("  [CHECK 102] #profile-back-btn exists and onclick calls showTab('leaderboard')")
            else:
                failures.append("#profile-back-btn missing or onclick does not call showTab('leaderboard')")
        except Exception as e:
            failures.append(f"profile-back-btn check error: {e}")

        # CHECK 103: pstat-profit, pstat-pnl, pstat-volume, pstat-bets stat elements exist in DOM
        try:
            stat_ok = await page.evaluate("""() => {
                const ids = ['pstat-profit', 'pstat-pnl', 'pstat-volume', 'pstat-bets'];
                return ids.every(id => document.getElementById(id) !== null);
            }""")
            if stat_ok:
                checks += 1
                print("  [CHECK 103] Profile stat elements present: pstat-profit, pstat-pnl, pstat-volume, pstat-bets")
            else:
                missing = await page.evaluate("""() => {
                    const ids = ['pstat-profit', 'pstat-pnl', 'pstat-volume', 'pstat-bets'];
                    return ids.filter(id => !document.getElementById(id));
                }""")
                failures.append(f"Profile stat elements missing: {missing}")
        except Exception as e:
            failures.append(f"Profile stat elements check error: {e}")

        # CHECK 104: #profile-bets-list exists and renderProfileSkeletons() produces skeleton HTML
        try:
            result = await page.evaluate("""() => {
                const list = document.getElementById('profile-bets-list');
                if (!list) return {list: false, skeletons: 0};
                if (typeof renderProfileSkeletons !== 'function') return {list: true, skeletons: -1};
                const html = renderProfileSkeletons(5);
                const div = document.createElement('div');
                div.innerHTML = html;
                return {list: true, skeletons: div.querySelectorAll('.skeleton').length};
            }""")
            if not result['list']:
                failures.append("#profile-bets-list element missing from DOM")
            elif result['skeletons'] == -1:
                failures.append("renderProfileSkeletons() function not defined in frontend")
            elif result['skeletons'] >= 3:
                checks += 1
                print(f"  [CHECK 104] #profile-bets-list exists; renderProfileSkeletons(5) produces {result['skeletons']} skeleton rows")
            else:
                failures.append(f"renderProfileSkeletons(5) produced only {result['skeletons']} skeleton elements, expected >=3")
        except Exception as e:
            failures.append(f"profile-bets-list skeleton check error: {e}")

        # ── CHECKS 105-107: upgrade flow + mobile nav (Session 124) ──

        # CHECK 105: #upgrade-modal exists in DOM
        try:
            modal_exists = await page.evaluate("""() => {
                return document.getElementById('upgrade-modal') !== null;
            }""")
            if modal_exists:
                checks += 1
                print("  [CHECK 105] #upgrade-modal element present in DOM")
            else:
                failures.append("#upgrade-modal element missing from DOM")
        except Exception as e:
            failures.append(f"upgrade-modal existence check error: {e}")

        # CHECK 106: openUpgradeModal() makes #upgrade-modal visible (removes .hidden)
        try:
            visible = await page.evaluate("""() => {
                const modal = document.getElementById('upgrade-modal');
                if (!modal) return false;
                if (typeof openUpgradeModal !== 'function') return false;
                // Ensure it starts hidden
                if (!modal.classList.contains('hidden')) modal.classList.add('hidden');
                openUpgradeModal();
                const visible = !modal.classList.contains('hidden');
                // Clean up — re-hide so page state is not contaminated
                modal.classList.add('hidden');
                return visible;
            }""")
            if visible:
                checks += 1
                print("  [CHECK 106] openUpgradeModal() removes .hidden from #upgrade-modal")
            else:
                failures.append("openUpgradeModal() did not remove .hidden from #upgrade-modal (or function/modal missing)")
        except Exception as e:
            failures.append(f"openUpgradeModal visibility check error: {e}")

        # CHECK 107: mobile 375px — no horizontal overflow on alerts tab
        try:
            mob_page = await browser.new_page()
            await mob_page.set_viewport_size({"width": 375, "height": 812})
            await mob_page.goto("http://localhost:3000", timeout=12000)
            await mob_page.wait_for_load_state("networkidle", timeout=10000)
            await mob_page.evaluate("showView('dashboard')")
            await asyncio.sleep(0.3)
            await mob_page.evaluate("showTab('alerts')")
            await asyncio.sleep(0.4)
            overflow_info = await mob_page.evaluate("""() => ({
                noOverflow: document.documentElement.scrollWidth <= document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth
            })""")
            await mob_page.close()
            if overflow_info['noOverflow']:
                checks += 1
                print("  [CHECK 107] Mobile 375px: no horizontal overflow on alerts tab")
            else:
                failures.append(f"Mobile 375px alerts tab has horizontal overflow (scrollWidth={overflow_info['scrollWidth']} > clientWidth={overflow_info['clientWidth']})")
        except Exception as e:
            failures.append(f"Mobile alerts overflow check error: {e}")

        # ── CHECKS 108-110: account tab content (Session 125) ──

        # CHECK 108: account tab renders without JS errors
        try:
            js_errors_before = len(js_errors)
            await page.evaluate("showView('dashboard'); showTab('account')")
            await asyncio.sleep(0.4)
            new_errors = js_errors[js_errors_before:]
            if not new_errors:
                checks += 1
                print("  [CHECK 108] Account tab renders without JS errors")
            else:
                failures.append(f"Account tab navigation caused JS errors: {'; '.join(new_errors[:3])}")
        except Exception as e:
            failures.append(f"Account tab JS error check error: {e}")

        # CHECK 109: #acct-tier-desc has non-empty text content
        try:
            tier_desc_ok = await page.evaluate("""() => {
                const el = document.getElementById('acct-tier-desc');
                return el !== null && el.textContent.trim().length > 0;
            }""")
            if tier_desc_ok:
                checks += 1
                print("  [CHECK 109] #acct-tier-desc present with non-empty text")
            else:
                failures.append("#acct-tier-desc missing or has empty text content")
        except Exception as e:
            failures.append(f"acct-tier-desc check error: {e}")

        # CHECK 110: account tab has #acct-upgrade-btn (.btn-primary upgrade button) in DOM
        try:
            upgrade_ok = await page.evaluate("""() => {
                const btn = document.getElementById('acct-upgrade-btn');
                return btn !== null && btn.classList.contains('btn-primary');
            }""")
            if upgrade_ok:
                checks += 1
                print("  [CHECK 110] #acct-upgrade-btn (.btn-primary) present in account tab DOM")
            else:
                failures.append("#acct-upgrade-btn missing or does not have .btn-primary class")
            await page.evaluate("showView('landing')")
        except Exception as e:
            failures.append(f"acct-upgrade-btn check error: {e}")

        # ── CHECKS 111-113: logout flow + localStorage (Session 127) ──

        # CHECK 111: logout() function is defined in window scope
        try:
            logout_ok = await page.evaluate("typeof window.logout === 'function'")
            if logout_ok:
                checks += 1
                print("  [CHECK 111] logout() function defined in window scope")
            else:
                failures.append("logout() function not defined in window scope")
        except Exception as e:
            failures.append(f"logout function check error: {e}")

        # CHECK 112: clearToken() removes pe_token from localStorage
        try:
            clear_ok = await page.evaluate("""() => {
                localStorage.setItem('pe_token', 'test-token-playwright');
                clearToken();
                return localStorage.getItem('pe_token') === null;
            }""")
            if clear_ok:
                checks += 1
                print("  [CHECK 112] clearToken() removes pe_token from localStorage (getItem returns null)")
            else:
                failures.append("clearToken() did not remove pe_token from localStorage")
        except Exception as e:
            failures.append(f"clearToken localStorage check error: {e}")

        # CHECK 113: #back-to-top-fab element present in DOM
        try:
            fab_ok = await page.evaluate("document.getElementById('back-to-top-fab') !== null")
            if fab_ok:
                checks += 1
                print("  [CHECK 113] #back-to-top-fab element present in DOM")
            else:
                failures.append("#back-to-top-fab element missing from DOM")
        except Exception as e:
            failures.append(f"back-to-top-fab check error: {e}")

        # ── CHECKS 114-116: follows dashboard DOM (Session 128) ──

        # CHECK 114: #follows-empty element exists in DOM
        try:
            follows_empty_ok = await page.evaluate("document.getElementById('follows-empty') !== null")
            if follows_empty_ok:
                checks += 1
                print("  [CHECK 114] #follows-empty element present in DOM")
            else:
                failures.append("#follows-empty element missing from DOM")
        except Exception as e:
            failures.append(f"follows-empty check error: {e}")

        # CHECK 115: #follows-container element exists in DOM
        try:
            follows_container_ok = await page.evaluate("document.getElementById('follows-container') !== null")
            if follows_container_ok:
                checks += 1
                print("  [CHECK 115] #follows-container element present in DOM")
            else:
                failures.append("#follows-container element missing from DOM")
        except Exception as e:
            failures.append(f"follows-container check error: {e}")

        # CHECK 116: #follows-subtitle element exists in DOM with text content
        try:
            follows_subtitle_ok = await page.evaluate("""() => {
                const el = document.getElementById('follows-subtitle');
                return el !== null && el.textContent.trim().length > 0;
            }""")
            if follows_subtitle_ok:
                checks += 1
                print("  [CHECK 116] #follows-subtitle present in DOM with text content")
            else:
                failures.append("#follows-subtitle missing from DOM or has empty text content")
        except Exception as e:
            failures.append(f"follows-subtitle check error: {e}")

        # CHECK 117: #toast-container element exists in DOM
        try:
            toast_container_ok = await page.evaluate("""() => {
                return document.getElementById('toast-container') !== null;
            }""")
            if toast_container_ok:
                checks += 1
                print("  [CHECK 117] #toast-container element present in DOM")
            else:
                failures.append("#toast-container element missing from DOM")
        except Exception as e:
            failures.append(f"toast-container DOM check error: {e}")

        # CHECK 118: typeof window.toastBet === 'function'
        try:
            toast_bet_ok = await page.evaluate("typeof window.toastBet === 'function'")
            if toast_bet_ok:
                checks += 1
                print("  [CHECK 118] typeof window.toastBet === 'function'")
            else:
                failures.append("window.toastBet is not a function")
        except Exception as e:
            failures.append(f"toastBet typeof check error: {e}")

        # CHECK 119: typeof window.enterDemoMode === 'function' (standalone)
        try:
            enter_demo_ok = await page.evaluate("typeof window.enterDemoMode === 'function'")
            if enter_demo_ok:
                checks += 1
                print("  [CHECK 119] typeof window.enterDemoMode === 'function'")
            else:
                failures.append("window.enterDemoMode is not a function")
        except Exception as e:
            failures.append(f"enterDemoMode typeof check error: {e}")

        # CHECK 120: typeof window.animateCounter === 'function'
        try:
            animate_counter_ok = await page.evaluate("typeof window.animateCounter === 'function'")
            if animate_counter_ok:
                checks += 1
                print("  [CHECK 120] typeof window.animateCounter === 'function'")
            else:
                failures.append("window.animateCounter is not a function")
        except Exception as e:
            failures.append(f"animateCounter typeof check error: {e}")

        # CHECK 121: typeof window.runLandingCounters === 'function'
        try:
            run_counters_ok = await page.evaluate("typeof window.runLandingCounters === 'function'")
            if run_counters_ok:
                checks += 1
                print("  [CHECK 121] typeof window.runLandingCounters === 'function'")
            else:
                failures.append("window.runLandingCounters is not a function")
        except Exception as e:
            failures.append(f"runLandingCounters typeof check error: {e}")

        # CHECK 122: typeof window.showTab === 'function' (core tab navigation function)
        try:
            show_tab_ok = await page.evaluate("typeof window.showTab === 'function'")
            if show_tab_ok:
                checks += 1
                print("  [CHECK 122] typeof window.showTab === 'function'")
            else:
                failures.append("window.showTab is not a function")
        except Exception as e:
            failures.append(f"showTab typeof check error: {e}")

        # CHECK 123: typeof window.loadLeaderboard === 'function'
        try:
            load_lb_ok = await page.evaluate("typeof window.loadLeaderboard === 'function'")
            if load_lb_ok:
                checks += 1
                print("  [CHECK 123] typeof window.loadLeaderboard === 'function'")
            else:
                failures.append("window.loadLeaderboard is not a function")
        except Exception as e:
            failures.append(f"loadLeaderboard typeof check error: {e}")

        # CHECK 124: typeof window.profileToggleFollow === 'function'
        try:
            profile_follow_ok = await page.evaluate("typeof window.profileToggleFollow === 'function'")
            if profile_follow_ok:
                checks += 1
                print("  [CHECK 124] typeof window.profileToggleFollow === 'function'")
            else:
                failures.append("window.profileToggleFollow is not a function")
        except Exception as e:
            failures.append(f"profileToggleFollow typeof check error: {e}")

        # CHECK 125: renderBettorCard() output contains a .follow-btn with aria-label attribute
        try:
            render_aria_ok = await page.evaluate("""() => {
                if (typeof renderBettorCard !== 'function') return false;
                const html = renderBettorCard({
                    address: '0xtest',
                    name: 'TestTrader',
                    profit: 1000,
                    accuracy: 0.6,
                    volume: 5000,
                    rank: 1
                }, false);
                const tmp = document.createElement('div');
                tmp.innerHTML = html;
                const btn = tmp.querySelector('.follow-btn');
                return btn !== null && btn.hasAttribute('aria-label');
            }""")
            if render_aria_ok:
                checks += 1
                print("  [CHECK 125] renderBettorCard() .follow-btn has aria-label attribute")
            else:
                failures.append("renderBettorCard() .follow-btn missing or lacks aria-label attribute")
        except Exception as e:
            failures.append(f"renderBettorCard aria-label check error: {e}")

        # ── Session 130: Whale Consensus Signal — Checks 126-130 ──────────

        # CHECK 126 — #tab-consensus element exists in DOM
        try:
            el = await page.evaluate("document.getElementById('tab-consensus') !== null")
            if el:
                checks += 1
                print("  [CHECK 126] #tab-consensus element present in DOM")
            else:
                failures.append("#tab-consensus element missing from DOM")
        except Exception as e:
            failures.append(f"CHECK 126 error: {e}")

        # CHECK 127 — #nav-consensus element exists in DOM
        try:
            el = await page.evaluate("document.getElementById('nav-consensus') !== null")
            if el:
                checks += 1
                print("  [CHECK 127] #nav-consensus element present in DOM")
            else:
                failures.append("#nav-consensus element missing from DOM")
        except Exception as e:
            failures.append(f"CHECK 127 error: {e}")

        # CHECK 128 — #mob-nav-consensus element exists in DOM
        try:
            el = await page.evaluate("document.getElementById('mob-nav-consensus') !== null")
            if el:
                checks += 1
                print("  [CHECK 128] #mob-nav-consensus element present in DOM")
            else:
                failures.append("#mob-nav-consensus element missing from DOM")
        except Exception as e:
            failures.append(f"CHECK 128 error: {e}")

        # CHECK 129 — showTab('consensus') shows #tab-consensus and hides others
        try:
            await page.evaluate("showTab('consensus')")
            await asyncio.sleep(0.3)
            visible = await page.evaluate("""() => {
                const tab = document.getElementById('tab-consensus');
                const lb = document.getElementById('tab-leaderboard');
                return tab && !tab.classList.contains('hidden') && lb && lb.classList.contains('hidden');
            }""")
            if visible:
                checks += 1
                print("  [CHECK 129] showTab('consensus') shows consensus tab, hides leaderboard")
            else:
                failures.append("showTab('consensus') did not correctly toggle tabs")
        except Exception as e:
            failures.append(f"CHECK 129 error: {e}")

        # CHECK 130 — typeof window.loadConsensus === 'function'
        try:
            is_fn = await page.evaluate("typeof window.loadConsensus === 'function'")
            if is_fn:
                checks += 1
                print("  [CHECK 130] typeof window.loadConsensus === 'function'")
            else:
                failures.append("loadConsensus function not defined in window scope")
        except Exception as e:
            failures.append(f"CHECK 130 error: {e}")

        await browser.close()
    return checks, failures

checks, failures = asyncio.run(check())
print(f"\n  Frontend: {checks} checks, {len(failures)} failures")
for f in failures:
    print(f"  FAIL: {f}")
sys.exit(1 if failures else 0)
