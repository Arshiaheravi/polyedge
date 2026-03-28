# Activity Log
*(Sessions 1-200 archived — see activity_log_archive.md)*

## 2026-03-27 — BRAIN (Session 214)
RESEARCHED: autonomous AI agent self-improvement 2026 (arxiv 2603.24639 ERL, 2603.25697 Kitchen Loop, 2603.00680 MemPO, 2603.15421 CLAG), pytest 9.0 release notes, Playwright Python expect() assertions, FastAPI v0.135.2 (no new versions since last brain session), ECC v1.9.0 status check, anthropics/anthropic-cookbook claude_agent_sdk.
DOWNLOADED: No new skill files — ECC still at v1.9.0, no new applicable Anthropic skills.
IMPLEMENTED: (1) playwright.md — added PREFER expect() ASSERTIONS section (auto-retrying assertions vs point-in-time page.evaluate() snapshots; concrete pattern for visibility/content/count assertions with timeout). (2) testing.md — added PYTEST 9.0+ FEATURES section (subtests for runtime-generated test values, parametrize generator deprecation warning). (3) activity_log.md — archived sessions 181-200 (33→13 entries; header updated to "1-200 archived").
BACKLOGGED: No new items — PRIORITY 11 backlog already has 3 items to verify and implement.
SOURCES: 8 new sources logged (ERL, Kitchen Loop, MemPO, CLAG, Playwright expect() docs, pytest 9.0 notes, anthropic-cookbook claude_agent_sdk, FastAPI v0.135.2 re-check).

## 2026-03-27 — TESTING (Session 213)
DONE: Fixed bug in /markets/consensus — no error handling meant Polymarket API failures returned 500 instead of 502 and left the cache unset. Added try/except matching all other endpoints. Added 4 regression tests: consensus 502 response + cache-not-poisoned, consensus per-signal field contract (event_slug etc.), detect_exits inactive VIP not notified, detect_exits EXIT BetEvent stored for non-VIP followers.
IMPACT: Any future Polymarket API outage now returns a clean 502 from the consensus endpoint instead of an unhandled 500. The 4 new tests prevent silent regressions on the exit detection and consensus response contract. 503 → 507 tests passing.
FILES: backend/app/routes/markets.py, backend/tests/test_tier_gates.py, backend/tests/test_scheduler.py

## 2026-03-27 — TESTING (Session 212)
DONE: Fixed root cause of intermittent SQLite "database is locked" failures in the full test suite — switched conftest.py from file-based `test_polyedge.db` to `sqlite:///:memory:` with `StaticPool`. Result: 503 passed / 0 failed (was 452–490 passed, 6–20 failed/errored per run non-deterministically).
IMPACT: The test suite is now fully deterministic. CI/CD and future sessions can trust green = green, red = real bug. Previously, 6–20 tests would randomly fail on every run, masking real regressions and wasting diagnosis time.
FILES: backend/tests/conftest.py

## 2026-03-27 — TESTING (Session 211)
DONE: Added regression test `test_register_and_login_do_not_expose_hashed_password_or_stripe_customer_id` to test_auth.py — proves POST /auth/register and POST /auth/login never return hashed_password or stripe_customer_id in the user dict. Confirmed the other 2 PRIORITY 10 tasks (duplicate follow 409, bettor non-existent 404) were already covered by existing tests with different function names than the grep patterns expected.
IMPACT: Any future route change that accidentally adds hashed_password or stripe_customer_id to register/login responses will now fail the test suite before shipping. Closes all 3 PRIORITY 10 backlog items.
FILES: backend/tests/test_auth.py

## 2026-03-27 — TESTING (Session 210)
DONE: Code quality audit of sessions 205-209 Playwright test files (no blocking issues found; logged duplicate tab-helpers to tech_debt.md). Added 3 Playwright E2E tests for the landing page leaderboard preview: skeleton-is-replaced (regression guard), has-at-least-one-row, and data-quality-when-api-available (auto-skips on Polymarket outage). All 3 passed first run. 96→99 Playwright tests total.
IMPACT: Landing page preview table regressions are now automatically caught — any silent failure where the skeleton never loads will fail this test. Test design is resilient to Polymarket API outages by using wait_for_function (20s) and pytest.skip() for data-quality assertions when API is unavailable.
FILES: backend/tests/playwright/test_landing_leaderboard_preview.py

## 2026-03-27 — TESTING (Session 209)
DONE: Added 4 Playwright E2E tests for landing page navigation CTAs (test_landing_navigation.py) — each major CTA button now has an automated check: "View Live Leaderboard" navigates to browse view, "Log In" shows login form, "Start Free" shows register form (with animation timing fix), annual billing toggle changes price display. Also cleaned all 4 stale PRIORITY 9 backlog tasks after GREP-BEFORE-PICKING confirmed they were already implemented.
IMPACT: PROJECT.md checklist §11 "All links open correctly (no 404s)" is now covered. Landing page navigation regressions will be caught automatically. 92→96 Playwright tests. Also discovered that Polymarket /profiles API is currently returning 404 (external outage) — pre-existing tests that depend on live leaderboard data are failing intermittently.
FILES: backend/tests/playwright/test_landing_navigation.py

## 2026-03-27 — META (Session 208)
IMPROVED: playwright.md — added VERIFY API RESPONSE SHAPE section (curl endpoint before asserting on field names; FastAPI required Header → 422 not 403). testing.md — added FastAPI Header() 422 pattern under PolyEdge-specific section. backlog.md — added PRIORITY 9 with 4 new bug-fix/data-integrity tasks (Bug #9 lru_cache, Bug #10 _last_positions purge, Bug #12 _consensusLoaded reset, bettor address regex Playwright test).
PATTERNS FOUND: Session 207 failed on admin Playwright test because it asserted wrong nested key names (flat vs nested) and expected 403 for missing FastAPI required Header (actually 422). Both rules were in knowledge.md reflexion only — not in the skill files where they fire at write-time.
PREDICTED IMPACT: Next Playwright test writing session will find the "curl first" rule in playwright.md before writing assertions, preventing another test-fix cycle. The 4 new backlog tasks extend the testing sprint by 4+ sessions targeting real outstanding bugs.

## 2026-03-27 — TESTING (Session 207)
DONE: Fixed BUG #8 (free-tier web push gate missing in toggleWebPush) and added 8 Playwright E2E tests across 3 new files — logout clears pe_token from localStorage and shows landing view; free user calling toggleWebPush() sees the upgrade modal (toggle stays OFF); admin /admin/stats mrr_estimate math matches basic*4.99+vip*9.99, tier counts sum to total, missing header returns 4xx.
IMPACT: BUG #8 paywall hole closed — free users can no longer bypass push tier gate. Three auth/security/admin flows now have automated E2E coverage. 84→92 Playwright tests total.
FILES: frontend/index.html, backend/tests/playwright/test_logout_clears_token.py, backend/tests/playwright/test_free_push_upgrade_modal.py, backend/tests/playwright/test_admin_mrr_math.py

## 2026-03-27 — TESTING (Session 206)
DONE: Added 9 Playwright E2E tests across 3 new files — account tab shows "Free" badge (tier-free class) and visible upgrade button for free users; leaderboard period filter defaults to #period-month active and correctly moves active state to #period-week/#period-all after switch (cards still render); guide tab becomes visible after showTab('guide') with an h1 heading and visible content blocks.
IMPACT: Proves the account settings tab correctly renders tier status, the period filter toggle does not crash or lose state, and the guide tab is not blank for authenticated users. 75→84 Playwright tests total.
FILES: backend/tests/playwright/test_account_tab_tier_badge.py, backend/tests/playwright/test_period_filter.py, backend/tests/playwright/test_guide_tab.py

## 2026-03-27 — TESTING (Session 205)
DONE: Added 6 Playwright E2E tests — 3 for alerts tab toggle presence (basic-tier user opens Alerts tab, asserts #toggle-push and #toggle-telegram exist and have non-zero size) and 3 for leaderboard sort toggle (initial #sort-profit is active, switching to volume moves active class to #sort-volume, cards still render after sort switch).
IMPACT: Proves the Alerts settings tab correctly renders both notification toggles for authenticated users, and that the leaderboard sort mechanism does not crash or blank the UI on sort change. 69→75 Playwright tests.
FILES: backend/tests/playwright/test_alerts_tab_toggles.py, backend/tests/playwright/test_leaderboard_sort_toggle.py

## 2026-03-27 — TESTING (Session 204)
DONE: Code quality audit of sessions 195-202 Playwright test files — removed duplicate API_BASE definition from test_cors_headers.py (now imported from conftest), replaced hardcoded localhost:8003 URL in test_full_journeys.py page.evaluate() string with the conftest API_BASE constant, and updated tech_debt.md with 6 brittle wait_for_timeout locations across 5 test files.
IMPACT: A future backend port change now requires editing only conftest.py instead of hunting across multiple test files. The audit also documented all wait_for_timeout brittle waits as known deferred debt.
FILES: backend/tests/playwright/test_cors_headers.py, backend/tests/playwright/test_full_journeys.py, autoagent/memory/tech_debt.md

## 2026-03-27 — BRAIN (Session 203)
RESEARCHED: autonomous AI agent best practices 2026, LLM agent memory management (A-MEM, ACE, AgentHER), FastAPI v0.135 features, Polymarket copy trading competitors (Polycule, Stand, PolycopytradBot), fintech push notification benchmarks (Pushwoosh 2026), GitHub repos (anthropics/skills webapp-testing, ECC v1.9.0).
DOWNLOADED: webapp-testing SKILL.md from anthropics/skills (content integrated into playwright.md VIEW CONTEXT RULES section).
IMPLEMENTED: (1) playwright.md — VIEW CONTEXT RULES FOR PROFILE NAVIGATION section (session 202 showProfile()/view-browse bug); (2) PROMPT.md — Zettelkasten cross-link rule in reflexion writing (A-MEM arxiv 2502.12110); (3) backlog.md — code quality audit task (155 work sessions = multiple of 5) + min-bet-size filter + rich push notification features.
BACKLOGGED: code quality audit, min-bet-size filter per follow, rich push notification payloads.
SOURCES: 9 new sources logged.

## 2026-03-27 — TESTING (Session 202)
DONE: Added Playwright E2E test proving the profile back-button returns to the leaderboard tab — basic user opens a bettor profile via showProfile(), then clicks #profile-back-btn, and the test asserts #tab-leaderboard loses its hidden class and #tab-profile gains it.
IMPACT: Proves the full profile→leaderboard back navigation wires correctly. Also uncovered that showProfile() is view-context-dependent — calling it from showView('browse') makes #profile-back-btn invisible to Playwright since the button lives inside view-dashboard.
FILES: backend/tests/playwright/test_profile_back_button.py

## 2026-03-27 — TESTING (Session 201)
DONE: Added Playwright E2E test proving basic-tier user can open a bettor profile via showProfile(), the #tab-profile becomes visible, #profile-addr-display contains the 0x-prefixed address, and the copy simulator card (if shown) is not blurred/locked.
IMPACT: Proves the full "click bettor → view profile" flow works end-to-end for authenticated basic users. Any regression breaking showProfile(), the bettors/{address} API, or the tier-gated simulator rendering will be caught automatically.
FILES: backend/tests/playwright/test_profile_modal.py
