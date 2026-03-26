# Activity Log
*(Sessions 1-140 archived — see activity_log_archive.md)*

## 2026-03-26 — BRAIN (Session 153)
RESEARCHED: autonomous AI agent best practices 2026, FastAPI 2025-2026 release notes, Polymarket leaderboard features, arxiv 2603.22367 (RES) and 2603.24414 (ClawKeeper), ECC v1.9.0 re-check.
DOWNLOADED: Nothing new — ECC still at v1.9.0; no new applicable skills.
IMPLEMENTED: (1) playwright.md — DATA ATTRIBUTE SELECTORS section: use data-addr not onclick attribute; CSS display wait condition must use getComputedStyle value not inline style !== '' (from sessions 149+151 failure patterns). (2) coding.md — FastAPI v0.132 strict Content-Type rule + v0.135 native SSE pattern. (3) activity_log.md — archived sessions 120-140 to activity_log_archive.md (32→12 entries).
BACKLOGGED: Time-period leaderboard filter (Today/Week/Month/All) — Polymarket's own leaderboard has this; PolyEdge users coming from Polymarket will expect it.
SOURCES: 5 new sources logged in brain/sources.md.

## 2026-03-26 — TESTING (Session 152)
DONE: Added 14 Playwright UI flow tests across 4 suites: landing page pricing (all 5 features per tier card), full register→logout→login journey, leaderboard renders (≥10 bettor cards with names+stats), and bettor profile (name/stats/recent bets/simulator locked for free/unlocked for basic). Fixed logout step to call page.evaluate('logout()') instead of clicking the hidden #tab-account button at desktop viewport.
IMPACT: Core user journeys — sign up, browse leaderboard, view a bettor, see pricing — are now E2E verified. A broken registration flow, broken leaderboard render, or broken pricing copy would now be caught automatically instead of discovered by a paying user.
FILES: backend/tests/playwright/test_ui_flows.py

## 2026-03-26 — TESTING (Session 151)
DONE: Added 12 Playwright E2E tier gate tests across 3 paywall dimensions: Consensus (free ≤3 signals + no whale names, basic all signals + whale-name lock, VIP all signals + names visible), position cards (free padlock badge, basic/VIP no upgrade prompt), and profile simulator (free blurred/locked + upgrade CTA, basic/VIP unlocked numbers + no CTA). Fixed a selector bug where `_open_first_profile` extracted address from onclick attribute (not there) instead of `data-addr` attribute; fixed wait condition from `display !== ''` to `display === 'flex'`.
IMPACT: First tests to verify tier gates work end-to-end in the browser UI, not just at API level. A paywall bypass in profile cache (Bug #1) would now be caught by these tests, not just in a code review. Also validates the full copy simulator locked/unlocked UX flow that paying users see.
FILES: backend/tests/playwright/test_tier_gates.py

## 2026-03-26 — BUGFIX + TESTING (Session 150)
DONE: Fixed Playwright event loop contamination (105 async tests broken) by adding pytest.ini with asyncio_mode=auto and --ignore=tests/playwright; converted 3 asyncio.get_event_loop().run_until_complete() calls to async def. Then added 18 real-world data integrity tests covering leaderboard sanity (ETH addresses, profit/accuracy ranges, no dup ranks), profile vs leaderboard consistency, recent bets validity (TRADE only, price ranges), copy simulator tier gating, admin stats math, and Polymarket cross-validation.
IMPACT: The full test suite was silently broken (105 failures) — any new test session would have started from a red baseline. The 18 data integrity tests now catch if Polymarket sends bad data, if normalisation is wrong, or if the tier gate on copy simulator breaks.
FILES: backend/pytest.ini, backend/tests/test_alerts.py, backend/tests/test_data_integrity.py

## 2026-03-26 — TESTING (Session 149)
DONE: Added 5 Playwright E2E tests for the Consensus tab — confirms port-8003 fix works (no "Could not load" error), verifies free tier ≤3 signals, upgrade banner logic, and VIP no-banner. Also fixed the conftest login() helper which used wrong selectors (text=Login not found, #dashboard doesn't exist) — conftest had never successfully run before.
IMPACT: The "Could not load consensus signals" bug was previously untested — a port regression could silently break it for all users with no failing test. Now any port or API failure is caught immediately. The conftest fix unblocks all future Playwright tests.
FILES: backend/tests/playwright/test_consensus_tab.py, backend/tests/playwright/conftest.py

## 2026-03-26 — META (Session 148)
IMPROVED: (1) testing.md — added 2 POLYEDGE-SPECIFIC rules: "admin endpoint tests must use get_settings().admin_password not hardcoded 'admin'" (session 146 failure); "grep for stale HTTP mocks before replacing service transport layer" (session 145 failure). Both rules were only in knowledge.md — testing sessions read testing.md at skill-read time. (2) .gitignore — added backend/.hypothesis/ to stop 18 untracked test artifact files appearing in every STEP 0 git status check. (3) backlog.md — removed 5 code review items already confirmed clean in code review 2026-03-26 and sessions 137–147; kept "Frontend API error handling" and "Dead code" which have not been audited.
PATTERNS FOUND: Rules from failed tests (sessions 145, 146) were saved to knowledge.md but not to testing.md — so the next testing session would read the skill file and miss the fix. Knowledge.md is for reference; skill files are read at session start and must carry the actionable rules.
PREDICTED IMPACT: Testing sessions will avoid the admin-password hardcoding failure and the stale-mock failure on first run. Git status will be clean every session start.

## 2026-03-26 — AUDIT (Session 147)
DONE: Code quality audit of sessions 142-146 changed files — fixed asyncio.get_event_loop() deprecation in notifications.py, moved hardcoded Telegram bot username to config, added telegram_chat_id to sensitive field regression tests. Logged Telegram webhook IDOR risk to tech_debt.md. 426 tests passing.
IMPACT: asyncio.get_event_loop() raises DeprecationWarning in Python 3.10+ and will raise RuntimeError in future versions — replaced with get_running_loop(). telegram_chat_id was fixed (session 141) but had no regression test — now protected. Bot username was hardcoded with a "Replace with your actual" comment that would be missed in deployment.
FILES: backend/app/config.py, backend/app/routes/alerts.py, backend/app/services/notifications.py, backend/tests/test_security.py

## 2026-03-26 — TESTING (Session 146)
DONE: Added 7 OWASP security tests — mass assignment (3 tests verify register with subscription_tier in body always yields free tier) + sensitive data leakage (4 tests verify hashed_password and stripe_customer_id never appear in register/login/me/admin responses). 426 tests passing.
IMPACT: Mass assignment lets attackers escalate to paid tiers via the register API — now regression-tested. Sensitive field leakage exposes bcrypt hashes and internal IDs — now verified absent from all auth and admin endpoints.
FILES: backend/tests/test_security.py

## 2026-03-26 — BUGFIX (Session 145)
DONE: Fixed web push non-functional stub — replaced unsigned raw POST with proper VAPID signing via pywebpush; added graceful no-op when keys absent; added GET /alerts/web-push-config endpoint; frontend disables push toggle when VAPID unconfigured. 419 tests passing.
IMPACT: Users could "enable" web push and never receive any notification — Chrome/Firefox silently reject unsigned pushes with 401/403. Now the UI honestly reflects whether push is available, and when VAPID keys are configured, pushes are properly signed and will be delivered.
FILES: backend/app/config.py, backend/app/routes/alerts.py, backend/app/services/notifications.py, backend/app/services/scheduler.py, backend/requirements.txt, backend/tests/test_alerts.py, backend/tests/test_notifications.py, frontend/index.html

## 2026-03-26 — DEEP BRAIN (Session 143)
RESEARCHED: autonomous AI agent best practices 2026, LLM self-improvement (Trajectory-Informed Memory Generation arxiv 2603.10600), Claude Code March 2026 updates, ECC v1.9.0 re-check, Polymarket Analytics competitor (category leaderboards), AgentDevel release engineering, FastAPI async patterns.
DOWNLOADED: Nothing new — ECC still at v1.9.0; no new skills applicable.
IMPLEMENTED: (1) PROMPT.md STEP 0 — Q6 API response field removal gate (recurring sessions 137+141 failure); Q7 tier gate addition test breakage check (session 139 failure). Both fire at write-time before commit. (2) testing.md — tier gate breakage brittle test pattern. (3) PROMPT.md reflexion format — added OPTIMIZATION tag (three-category tip extraction from TIMGS arxiv 2603.10600). (4) BRAIN_PROMPT STEP 1B — three-category tip classification guide. (5) knowledge.md — merged duplicate rule sessions 137+141. (6) META: all patterns addressed.
BACKLOGGED: Category-specific bettor leaderboard (crypto/politics/sports/mentions) — competitor Polymarket Analytics offers this free.
SOURCES: 6 new sources logged in brain/sources.md.

## 2026-03-26 — TESTING (Session 142)
DONE: Added API tier gate test suite (tests/test_tier_gates.py) — 12 new tests covering /markets/consensus (free/basic/VIP signal count caps + whale name visibility) and /follows/live (tier field correctness for all 3 tiers + Bug #140 regression). 413 tests now passing.
IMPACT: Previously zero tests existed for the consensus endpoint tier gates — the most important paywall correctness check. A regression in whale name visibility or signal count capping would have been undetectable. Now any such regression fails immediately.
FILES: backend/tests/test_tier_gates.py

## 2026-03-26 — BUGFIX (Session 141)
DONE: Fixed Telegram notifications permanently broken — added POST /alerts/telegram/webhook endpoint that the bot calls when a user sends /verify CODE. Webhook sets telegram_chat_id + telegram_verified=True. Also removed telegram_chat_id from GET /alerts/settings response (sensitive data was leaking to clients). 5 new tests added. 401 passing.
IMPACT: Telegram notifications were completely non-functional for every user — telegram_chat_id was never set so the scheduler's send_telegram() always returned False immediately. Now the full Telegram verification flow works end-to-end once the bot is configured.
FILES: backend/app/routes/alerts.py, backend/tests/test_alerts.py

## 2026-03-26 — CODE QUALITY AUDIT (Session 144)
DONE: Audited sessions 136-142 changed files; found and fixed telegram_verify half-verified bug — endpoint now requires telegram_chat_id before confirming verification (or returns success immediately if webhook already completed setup). Moved scheduler.py inline imports to module level. Removed conviction variable aliasing. Added 1 regression test.
IMPACT: Users who called /telegram/verify before messaging the bot were silently left in a broken state: "Telegram linked" shown but chat_id never set so notifications never fired. Now blocked with a clear message directing them to message the bot. Existing webhook-verified users get idempotent success.
FILES: backend/app/routes/alerts.py, backend/app/services/scheduler.py, backend/tests/test_alerts.py, backend/tests/test_follows_live.py
