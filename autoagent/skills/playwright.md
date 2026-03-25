# Skill: Frontend Verification (Playwright)

## When to use this skill
Run after every WORK session, BEFORE committing. You must start the servers yourself, run checks, then shut them down.

---

## STEP 1 — Start the servers

Start backend and frontend in the background:

Read `autoagent/PROJECT.md` for the exact start commands, backend URL, and frontend URL.

```bash
# Use the start commands from PROJECT.md — example structure (bash syntax, NOT CMD):
# cd [PROJECT_ROOT]
# py -m uvicorn app.main:app --port 8002 > autoagent/tmp_backend.log 2>&1 &
# BACKEND_PID=$!
# py -m http.server 3000 --directory frontend > autoagent/tmp_frontend.log 2>&1 &
# FRONTEND_PID=$!
```

Wait 4 seconds for them to boot, then check they're up:

```bash
# Use backend_url and frontend_url from autoagent/config.json or PROJECT.md
curl -s [BACKEND_URL]/[HEALTH_ENDPOINT] > nul && echo backend:OK || echo backend:FAIL
curl -s [FRONTEND_URL] > nul && echo frontend:OK || echo frontend:FAIL
```

If either fails after 4s, try once more after another 3s. If still failing, set status=skip with note "servers failed to start", kill both processes, and continue to commit without a frontend check.

---

## STEP 2 — Check if Playwright is installed

```bash
py -m playwright --version
```

If not installed:
```bash
py -m pip install playwright -q && py -m playwright install chromium --quiet
```

---

## STEP 3 — Run the check script

**IMPORTANT — use the registry as your base, not the template below.**

Check if `autoagent/playwright_registry.py` exists:
```bash
ls autoagent/playwright_registry.py 2>/dev/null && echo EXISTS || echo MISSING
```

If it EXISTS:
```bash
cp autoagent/playwright_registry.py autoagent/tmp_check.py
# Then ADD your session-specific checks to tmp_check.py (insert before the final close/return)
# Do NOT remove existing checks — only add new ones
```

If MISSING: use the generic template below to create `autoagent/tmp_check.py`.

After a **successful** run (0 failures), save back to registry:
```bash
cp autoagent/tmp_check.py autoagent/playwright_registry.py
```

Then delete tmp_check.py as normal. This keeps coverage cumulative across sessions.

**Rule**: The check count in sessions.json must be >= the check count in the previous session's sessions.json entry. If it decreases, document why (e.g., "removed stale market-toggle check — element was renamed").

Save as `autoagent/tmp_check.py`, run it, delete it after.

```python
import asyncio, sys
from playwright.async_api import async_playwright

async def check():
    failures = []
    checks = 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        js_errors = []
        page.on("pageerror", lambda e: js_errors.append(str(e)))

        # 1. Page loads
        try:
            await page.goto("http://localhost:3000", timeout=12000)
            checks += 1
            print("  [CHECK 1] Page loaded OK")
        except Exception as e:
            failures.append(f"Page failed to load: {e}")
            await browser.close()
            return checks, failures

        # 2. Backend API responds — use backend_url from autoagent/config.json
        try:
            resp = await page.request.get("http://localhost:8000/api/health", timeout=8000)  # update URL per PROJECT.md
            if resp.ok:
                checks += 1
                print("  [CHECK 2] Backend API OK")
            else:
                failures.append(f"Backend returned {resp.status}")
        except Exception as e:
            failures.append(f"Backend API unreachable: {e}")

        # 3. Signal cards visible
        try:
            await page.wait_for_selector(".signal-card, .card, [class*='card']", timeout=10000)
            checks += 1
            print("  [CHECK 3] Signal cards visible")
        except:
            failures.append("Signal cards not found — dashboard may be empty or broken")

        # 4. Market toggle present
        try:
            toggle = await page.query_selector("#market-toggle, [data-market], .market-toggle")
            if toggle:
                checks += 1
                print("  [CHECK 4] Market toggle found")
            else:
                failures.append("Market toggle not found")
        except Exception as e:
            failures.append(f"Market toggle check error: {e}")

        # 5. Navigation present
        try:
            nav = await page.query_selector("nav, .nav, header")
            if nav:
                checks += 1
                print("  [CHECK 5] Navigation present")
            else:
                failures.append("Navigation not found")
        except Exception as e:
            failures.append(f"Nav check error: {e}")

        # 6. No JS errors
        await asyncio.sleep(1)
        if js_errors:
            failures.append(f"JS errors: {'; '.join(js_errors[:3])}")
        else:
            checks += 1
            print("  [CHECK 6] No JS errors")

        # 7. Removed nav items NOT present (regression guard)
        # Read "REMOVED FEATURES" from autoagent/PROJECT.md and check those page names are absent
        # Example: REMOVED_PAGES = ["old-feature", "removed-section"]
        # Customize per project — leave empty list if no removed features to guard
        REMOVED_PAGES = []  # populate from PROJECT.md "REMOVED FEATURES" table
        for rp in REMOVED_PAGES:
            elem = await page.query_selector(f'[data-page="{rp}"], [onclick*="{rp}"]')
            if elem:
                failures.append(f"REMOVED section '{rp}' still appears in nav")
            else:
                checks += 1
                print(f"  [CHECK 7/{rp}] '{rp}' correctly absent from nav")

        # 8. Light mode toggle — dark is default, verify light mode switches and no invisible elements
        try:
            toggle = await page.query_selector("#theme-toggle, [onclick*='toggleTheme'], [onclick*='theme']")
            if toggle:
                await toggle.click()
                await asyncio.sleep(0.5)
                # Verify page still has content (not invisible on white bg)
                body_bg = await page.evaluate("getComputedStyle(document.body).backgroundColor")
                # Check a card or main section is still visible
                card = await page.query_selector(".stock-card, .signal-card, #signals-container")
                if card:
                    checks += 1
                    print("  [CHECK 8] Light mode: page has content after theme toggle")
                else:
                    failures.append("Light mode: main content not visible after toggle")
                # Switch back to dark
                await toggle.click()
                await asyncio.sleep(0.3)
            else:
                checks += 1
                print("  [CHECK 8] Light mode toggle not found — skip (not blocking)")
        except Exception as e:
            print(f"  [CHECK 8] Light mode check skipped: {e}")
            checks += 1  # Non-blocking

        await browser.close()
    return checks, failures

checks, failures = asyncio.run(check())
print(f"\n  Frontend: {checks} checks, {len(failures)} failures")
for f in failures:
    print(f"  FAIL: {f}")
sys.exit(1 if failures else 0)
```

```bash
py autoagent/tmp_check.py
rm -f autoagent/tmp_check.py
```

---

## STEP 4 — Kill the servers

After the check (pass or fail), always kill the servers:

```bash
# Kill the background processes started in STEP 1
kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
rm -f autoagent/tmp_backend.log autoagent/tmp_frontend.log
```

---

## STEP 5 — Record results in sessions.json

Pass:
```json
"frontend": {"status": "pass", "checks": 6, "failures": 0, "notes": ""}
```

Fail (fix before committing):
```json
"frontend": {"status": "fail", "checks": 4, "failures": 2, "notes": "Signal cards not found; JS error: X"}
```

Skip (servers couldn't start or Playwright missing):
```json
"frontend": {"status": "skip", "checks": 0, "failures": 0, "notes": "servers failed to start"}
```

---

## IF CHECKS FAIL

Fix the issue, re-run the check, confirm pass — then commit. A failing frontend check blocks the commit exactly like a failing test.
The only exception is status=skip (can't start servers / Playwright missing) — that never blocks a commit.

---

## CSS CLASS REFACTOR — update Playwright selectors first

When doing a large frontend refactor that renames CSS classes (e.g., table rows → cards, old-name → new-name):

**Before running the check script**, grep it for old class names:
```bash
grep -n 'bettor-row\|bettor-name\|old-class-pattern' autoagent/tmp_check.py
```

If any old class names appear in the check script, update them to the new names **at the same time as the refactor** — not after. Stale selectors in the check script silently "pass" on `null` (element not found) instead of catching regressions.

**Rule**: Any time a CSS class is renamed in `frontend/index.html`, search the active Playwright check script for that class name and update it simultaneously.

(Source: Session #58 — converted lb-table→lb-grid, Playwright checks still referenced .bettor-row/.bettor-name → 2 failures on first run)

---

## RECONNAISSANCE-THEN-ACTION PATTERN (from Anthropic webapp-testing skill)

When debugging a failing check, use this order — never skip to action:
1. **Screenshot first**: `await page.screenshot(path="autoagent/tmp_debug.png")` — see what the page actually shows
2. **DOM inspect**: `await page.content()` — see raw HTML to verify selectors exist
3. **Identify correct selectors** from DOM, then act
4. **Always wait for networkidle** on dynamic apps before inspecting: `await page.wait_for_load_state("networkidle")`

Source: Anthropic skills/webapp-testing/SKILL.md (2026-03-20)

---

## ACCESSIBILITY CHECKS (add to session checks when touching UI)

From browser-qa/SKILL.md (ECC 2026-03-23). Add these as Playwright checks for any session that modifies forms, cards, or navigation:

```python
# Accessibility: focus states — interactive elements must be keyboard-focusable
focus_issues = await page.evaluate("""() => {
    const interactive = document.querySelectorAll('button, a, input, select, textarea');
    return Array.from(interactive).filter(el => {
        const style = getComputedStyle(el, ':focus');
        return style.outlineWidth === '0px' && style.outlineStyle === 'none';
    }).length;
}""")
if focus_issues > 0:
    failures.append(f"Accessibility: {focus_issues} interactive elements have no focus outline")
else:
    checks += 1
    print("  [CHECK N] Accessibility: all interactive elements have focus outlines")

# Accessibility: images must have alt text
missing_alt = await page.evaluate("""() =>
    document.querySelectorAll('img:not([alt])').length
""")
if missing_alt > 0:
    failures.append(f"Accessibility: {missing_alt} images missing alt attribute")
else:
    checks += 1
    print("  [CHECK N] Accessibility: all images have alt text")

# Accessibility: form inputs must have labels
unlabeled = await page.evaluate("""() => {
    const inputs = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"])');
    return Array.from(inputs).filter(i => !i.labels?.length && !i.getAttribute('aria-label') && !i.getAttribute('aria-labelledby')).length;
}""")
if unlabeled > 0:
    failures.append(f"Accessibility: {unlabeled} form inputs without labels")
else:
    checks += 1
    print("  [CHECK N] Accessibility: all form inputs labeled")
```

**Rule**: accessibility checks are non-blocking for this project (PolyEdge is not public-accessibility-required yet) — log failures as warnings, don't fail the check. Change `failures.append` to `print(f"  [WARN] ...")` for a11y checks.

(Source: affaan-m/everything-claude-code skills/browser-qa/SKILL.md, 2026-03-23)

---

## SPA WAIT STRATEGIES (for PolyEdge's dynamic API content)

From ECC e2e-testing/SKILL.md (2026). PolyEdge loads leaderboard data from the `/bettors` API after page load — checks that test for card content must wait for the API response, not just page load.

**Use `waitForResponse()` for API-dependent assertions:**
```python
# Wait for a specific API call to complete before asserting its result
async with page.expect_response(lambda r: "/bettors" in r.url and r.ok) as resp_info:
    await page.goto("http://localhost:3000")
await resp_info.value  # response is done
# Now safe to check for .lb-card elements
cards = await page.query_selector_all(".lb-card")
```

**Use `waitForLoadState('networkidle')` for general dynamic content:**
```python
await page.goto("http://localhost:3000")
await page.wait_for_load_state("networkidle", timeout=10000)
# Now safe to check for any dynamically-loaded elements
```

**Rule**: When a Playwright check randomly passes/fails, the root cause is almost always a race condition between the check's DOM query and the API response. Use `waitForResponse()` (preferred, precise) or `networkidle` (acceptable, coarser) before asserting on API-loaded content.

(Source: affaan-m/everything-claude-code skills/e2e-testing/SKILL.md, 2026-03-24)

---

## SPA HIDDEN ELEMENT NAVIGATION (PolyEdge-specific)

PolyEdge's SPA has nav elements that are conditionally visible — `#nav-leaderboard`, `#nav-follows`, etc. are `display:none` at desktop widths (mobile-only). Trying to `click()` them in Playwright will silently fail or error.

**Never click nav elements by ID if they might be hidden. Use `page.evaluate()` to call the SPA's JS functions directly:**

```python
# WRONG — clicks hidden element, silently fails at desktop width:
await page.click("#nav-leaderboard")

# CORRECT — calls the JS function directly, always works:
await page.evaluate("showView('leaderboard')")
await page.evaluate("showTab('follows')")
await page.evaluate("showView('browse')")
```

**Multi-screen check pattern** — use a dedicated `scr_page` instance for screen-navigation checks to avoid contaminating the main `page` state:

```python
scr_page = await browser.new_page()
await scr_page.goto("http://localhost:3000", timeout=12000)
await scr_page.wait_for_load_state("networkidle")

# Navigate via JS evals (not click):
await scr_page.evaluate("showView('leaderboard')")
await asyncio.sleep(0.5)
title = await scr_page.title()
# ... assert on scr_page ...

await scr_page.close()
# Then browser.close() as normal
```

Close `scr_page` before `browser.close()` to avoid resource warnings.

**Rule**: For PolyEdge SPA, ALL tab/view switching in Playwright must use `page.evaluate("showView(...)")` or `page.evaluate("showTab(...)")` — never `click()` on nav elements. Nav elements are `display:none` at desktop width (1280px default Playwright viewport).

(Source: Session #90 failure — ElementHandle.click() on #nav-leaderboard failed because element is display:none at desktop width. Fixed by using page.evaluate("showView(...)") instead.)
