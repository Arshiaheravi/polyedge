"""
PolyEdge — Persistent Playwright check registry.
This file is cumulative: sessions ADD checks here, never subtract.
Usage: cp autoagent/playwright_registry.py autoagent/tmp_check.py → add session checks → run → cp back.
Last updated: Session 65 (empty state SVGs)
"""
import asyncio, sys
from playwright.async_api import async_playwright

BACKEND_URL = "http://localhost:8001"
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

        await browser.close()
    return checks, failures

checks, failures = asyncio.run(check())
print(f"\n  Frontend: {checks} checks, {len(failures)} failures")
for f in failures:
    print(f"  FAIL: {f}")
sys.exit(1 if failures else 0)
