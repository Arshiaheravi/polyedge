# Activity Log
*(Sessions 1-140 archived — see activity_log_archive.md)*

## 2026-03-26 — TESTING (Session 175)
DONE: Added 3 regression tests covering Bug #9 (lru_cache identity), compute_copy_simulator open-bet skip branch, and GET /auth/me sensitive field absence (hashed_password, stripe_customer_id, telegram_chat_id). 472 → 475 tests.
IMPACT: test_get_settings_returns_same_instance catches if @lru_cache is accidentally removed from config.py (causes .env re-read on every scheduler invocation). test_copy_simulator_skips_still_open_bets locks in the "still-open bets excluded" contract. test_auth_me_does_not_expose_sensitive_fields guards against accidental field exposure in /auth/me.
FILES: backend/tests/test_health.py, backend/tests/test_data_integrity.py, backend/tests/test_auth.py

## 2026-03-26 — CODE QUALITY AUDIT (Session 174)
DONE: Audited files changed in sessions 167-171 (polymarket.py, test_data_integrity.py, test_follows_live.py, test_polymarket_service.py, frontend/index.html). Marcus XSS check passed — all innerHTML renders properly escape API-sourced data. Found 1 Leo smell in polymarket.py: asyncio, time, and datetime were imported inside function bodies (get_bettor_profile, compute_copy_simulator, get_consensus_signals) instead of at module level. Fixed: moved all three to module-level imports and removed two unused imports (Optional from typing, timezone from datetime). No logic changed.
IMPACT: Codebase now follows standard Python import conventions — a developer reading polymarket.py can see all dependencies at the top of the file without hunting through function bodies. Unused imports removed reduces noise.
FILES: backend/app/services/polymarket.py

## 2026-03-26 — BRAIN (Session 173)
RESEARCHED: autonomous AI agent best practices 2026, mutation testing for Python/pytest, Polymarket Data API endpoints, LLM agent memory deduplication techniques.
DOWNLOADED: Nothing — mutmut already on PyPI, no new skill files needed.
IMPLEMENTED: (1) testing.md — added MUTATION TESTING section with mutmut recipe, commands, mutation score targets, and PolyEdge-specific scoped run commands. (2) BRAIN_PROMPT.md — added explicit prohibition on background agents for STEP 2 searches (rule was in knowledge.md but not in the prompt itself — wrong location). (3) knowledge.md — added Polymarket GET /trades endpoint discovery + rate limit UNCERTAIN note.
BACKLOGGED: Nothing new — mutmut is a periodic audit tool added to testing.md for use every 20 sessions.
SOURCES: 5 new sources logged.

## 2026-03-26 — TESTING (Session 172)
DONE: Added ±10000% ROI cap to compute_copy_simulator in polymarket.py and a unit test (test_copy_simulator_extreme_price_roi_cap) with all-winning bets at price=0.01 to document and verify the cap behaviour. 471→472 tests.
IMPACT: Without the cap, a bettor who won many bets at very low entry prices (e.g. price=0.01) would show absurd ROI values on their profile simulator card — misleading users into thinking copying them is a guaranteed windfall. The cap prevents display bugs and protects user decisions.
FILES: backend/app/services/polymarket.py, backend/tests/test_data_integrity.py

## 2026-03-26 — TESTING (Session 171)
DONE: Activated the CONDITION_ID_RE regex assertion (^0x[a-fA-F0-9]{64}$) inside test_consensus_whale_count_and_price_range — the regex was defined at test_data_integrity.py:21 but never used in any assertion. Now validates that every consensus signal's condition_id is a properly-formatted 64-char hex ID.
IMPACT: Catches malformed or missing condition_ids from the Polymarket API before they reach users; ensures the condition_id field is a genuine market identifier and not an empty string or garbage value. 471 tests stable.
FILES: backend/tests/test_data_integrity.py

## 2026-03-26 — TESTING (Session 170)
DONE: Added `test_recent_bets_timestamps_within_90_days` to test_data_integrity.py — verifies that all recent bets from GET /bettors/{address} have timestamps within the past 90 days; handles both Unix float string and ISO-8601 string formats; skips gracefully when no bets available or Polymarket is unreachable. Also removed 2 stale backlog tasks (copy_value_pct and exit-alerts-VIP) whose tests already existed, and added 3 new HIGH PRIORITY testing tasks. 470→471 tests.
IMPACT: Stale Polymarket data (>90-day-old bets served as "recent") would give copy-traders wrong context — the timestamp check is a data freshness guard that catches Polymarket API caching failures.
FILES: backend/tests/test_data_integrity.py

## 2026-03-26 14:00 — TESTING (Session 169)
DONE: Fixed get_active_positions to filter positions with cur_price < 0.001 or > 0.999 (resolved/expired markets leaking as "copyable"), and added 3 regression tests: (1) price range filter verified with mock data including price=0 and price=1 positions, (2) copy_signal enum always in {good, fair, late}, (3) consensus signals have whale_count>=3 and avg_entry_price in 0.01-0.99. Fixed 2 existing tests that had no curPrice in fixtures (now filtered out by the new guard). 467→470 tests.
IMPACT: Users no longer see resolved markets in their copy-trading dashboard. The price range filter catches both "data missing" (price=0) and "YES settled" (price=1) cases. Tests prove the filter and document the contract.
FILES: backend/app/services/polymarket.py, backend/tests/test_data_integrity.py, backend/tests/test_follows_live.py, backend/tests/test_polymarket_service.py

## 2026-03-26 — META (Session 168)
IMPROVED: (1) knowledge.md — added reflexion entries for sessions 156-167 (12 missing reflexions) and updated test suite history table (was stale at session 142/413 tests, now current through session 167/467 tests). (2) backlog.md — removed empty section clutter at top (14 lines of orphaned `---` separators), reordered to put HIGH PRIORITY Testing before MEDIUM PRIORITY Edge Cases. (3) meta/PROMPT.md — added reflexion gap check to STEP 1: grep for last reflexion session number and flag if 3+ sessions are missing, with instructions to write them from activity_log data.
PATTERNS FOUND: (a) Reflexion entries for sessions 156-167 were completely absent from knowledge.md — 12 sessions of accumulated rules were missing. Most sessions had no failures so the reflexion was likely skipped as "nothing to document" — but the RULE line is always required even for clean sessions. (b) Backlog ordering had MEDIUM PRIORITY section before HIGH PRIORITY sections — work sessions pick the top item and would reach medium tasks before high ones. (c) Test suite history table was 25 sessions stale.
PREDICTED IMPACT: Future META sessions will catch reflexion gaps early via the gap check. Work sessions will pick HIGH PRIORITY testing tasks before medium ones. Knowledge.md now has the full learning chain including timer leak, VIP poll, rate limiting, and dead code audit patterns.

## 2026-03-26 — CODE REVIEW (Session 167)
DONE: Dead code audit — scanned all JS function definitions in frontend/index.html and all imports in backend/app/. Found and removed 1 dead function: `tierBadge(tier)` (3 lines, generated a tier badge HTML string but was never called from any code path or HTML attribute). All other suspects confirmed live (enterDemoMode, toggleSms, daysUntil, etc. all called from onclick attributes). All backend imports verified in use. 467 tests stable.
IMPACT: Codebase is slightly cleaner; tierBadge was producing a string that was never rendered anywhere — a silent dead weight. Audit confirmed the codebase has very little true dead code after 166 sessions of iterative agent editing.
FILES: frontend/index.html

## 2026-03-26 — CODE QUALITY AUDIT (Session 166)
DONE: Extracted `_compute_conviction(bet_amount, avg_bet_usd)` helper into scheduler.py — eliminated the identical 8-line conviction score logic that was duplicated in `_poll_bets` and `_poll_vip_bets`. Fixed stale docstring in `test_cors_headers_present`. Added 5 unit tests for `_compute_conviction` covering normal/HIGH/EXTREME/zero-avg/zero-bet cases. 462→467 tests passing.
IMPACT: Conviction score thresholds now live in one place — a future threshold change (e.g. raising EXTREME from 10x to 15x) only requires editing one function instead of two, eliminating the risk of inconsistent notification behavior between VIP-fast-path and standard poll.
FILES: backend/app/services/scheduler.py, backend/tests/test_scheduler.py, backend/tests/test_health.py

## 2026-03-26 — TESTING (Session 165)
DONE: Added 3 regression tests — (1) `test_poll_bets_purges_stale_last_positions`: verifies `_poll_bets` cleans up `_last_positions` entries for bettors no longer followed (Bug #10 regression coverage); (2) `test_health_not_rate_limited`: 20 consecutive calls to GET /health all return 200; (3) `test_readiness_not_rate_limited`: 20 consecutive calls to GET /readiness all return 200. 459→462 tests passing.
IMPACT: Memory leak from unfollowed bettors is now regression-tested. k8s liveness/readiness probes are confirmed to never get 429-blocked — without this test, a future rate limiter change could silently break deployments.
FILES: backend/tests/test_scheduler.py, backend/tests/test_health.py

## 2026-03-26 — SECURITY (Session 164)
DONE: Added rate limiting to POST /auth/register and POST /auth/login — 10 req/min per IP via slowapi; shared limiter singleton in app/limiter.py; conftest resets limiter storage between tests; 2 regression tests added (459 total).
IMPACT: Brute-force password attacks and mass account creation are now blocked at the server layer. The 11th request in a burst returns 429 Too Many Requests automatically.
FILES: backend/requirements.txt, backend/app/limiter.py, backend/app/main.py, backend/app/routes/auth.py, backend/tests/conftest.py, backend/tests/test_auth.py

## 2026-03-26 — BRAIN (Session 163)
DONE: Fixed stale coding.md (port 8002→8003, StockCards 8-STEP CHAIN→PolyEdge FEATURE WIRING CHAIN with tier-gate cache key rule); created autoagent/skills/rate-limiting.md with complete SlowAPI recipe for auth routes; added FastAPI v0.134 streaming JSON Lines + v0.131 ORJSONResponse deprecation to coding.md; added rate-limiting row to INDEX.md; logged 6 new sources.
IMPACT: Coding sessions will no longer be misled by wrong port (8002) or non-existent PolyEdge file paths (analysis.py, StockSignal). Rate limiting implementation now has a ready-to-use recipe so the implementing session won't need to rediscover the mandatory `request: Request` param that causes 500 errors.
FILES: autoagent/skills/coding.md, autoagent/skills/rate-limiting.md, autoagent/skills/INDEX.md, autoagent/brain/sources.md, autoagent/brain/techniques.md, autoagent/memory/knowledge.md

## 2026-03-26 — TESTING (Session 162)
DONE: Added 7 behavioral tests across 3 files — (1) _poll_vip_bets: no-VIP-users early return, VIP-only-addresses filtering, and new-bet creates BetEvent+notification; (2) /follows/live conviction score: keys always present, EXTREME label at 10x avg_bet, empty label below 3x; (3) profile cache: reverse-order test confirms VIP gets unlocked simulator even after free user cached same address.
IMPACT: Three previously untested code paths now have regression coverage — a broken VIP fast-path, a missing conviction field, or a cache key regression would now be caught automatically instead of shipping silently broken to users.
FILES: backend/tests/test_scheduler.py, backend/tests/test_follows_live.py, backend/tests/test_bettors.py

## 2026-03-26 — CODE QUALITY AUDIT (Session 161)
DONE: Audited last 5 sessions' changed files; found and fixed readiness endpoint leaking exception details in 503 body and stale scheduler docstring. Logged _last_check race condition to tech_debt.md.
IMPACT: Readiness endpoint no longer exposes DB file paths or SQLAlchemy error strings to public callers — internal error is logged server-side while users see a generic "Database connectivity check failed" message.
FILES: backend/app/main.py, backend/app/services/scheduler.py, backend/tests/test_health.py

## 2026-03-26 — BUGFIX (Session 160)
DONE: Fixed 3 silent error swallowing bugs in the follows tab — users now see "Could not load positions. Try refreshing." instead of stuck skeleton cards when the positions API fails on first load; follows-list errors show a toast instead of a misleading empty state.
IMPACT: Users no longer see infinite loading skeletons when the API is slow or returns an error on the follows tab. Reliable error feedback replaces silent failures that made the app look broken.
FILES: frontend/index.html

## 2026-03-26 14:00 — FEATURE (Session 159)
DONE: Added VIP-tier 5-second poll interval (vs 30s for all tiers) — scheduler now runs two APScheduler jobs: _poll_vip_bets every 5s for addresses followed by VIP users, _poll_bets every 30s for all addresses. Also added GET /readiness endpoint that checks DB connectivity (SELECT 1) and returns 200/503 for production deployments. 4 new tests added (450 total).
IMPACT: VIP users receive bet notifications up to 6x faster, closing the competitive gap vs PolyCop/PolyGun. The readiness probe enables safe k8s/Docker deployments with proper health gating.
FILES: backend/app/config.py, backend/app/services/scheduler.py, backend/app/main.py, backend/tests/test_health.py, backend/tests/test_scheduler.py

## 2026-03-26 — META (Session 158)
IMPROVED: (1) playwright.md — added TIMER TESTING section: page.clock.fast_forward() pattern used in session 156 but never documented; includes install-before-goto rule and when-to-use guidance. (2) backlog.md — removed empty "HIGH PRIORITY — Frontend UI Playwright Tests" section header (all tasks completed sessions 149–157, empty section was confusing). (3) backlog.md — restored "Frontend API error handling" and "Dead code" code review items that were explicitly kept in session 148 but silently dropped in subsequent backlog cleanups.
PATTERNS FOUND: (a) Useful Playwright patterns (page.clock) get used in work sessions but never filed back to playwright.md — only enters knowledge.md at best. (b) Backlog items can silently disappear when sections get cleaned up; session 148 META kept two items but they were gone by session 157.
PREDICTED IMPACT: Timer-based Playwright tests won't require rediscovery next session. Two pending code review tasks will be picked up instead of forgotten.

## 2026-03-26 — TESTING (Session 157)
DONE: Added 3 new reliability tests in test_bettors.py — (1) Polymarket HTTP 500 at httpx transport level returns graceful 200 empty list (leaderboard), (2) same for bettor detail endpoint, (3) 10 concurrent GET /bettors threads using Python threading all return 200 without crashing. Also removed 3 already-covered items from backlog (timeout handling, concurrent requests, scheduler duplicate prevention — all already tested).
IMPACT: First tests that verify Polymarket 500 resilience at the HTTP layer (not just the mock-at-service-function level). Proves the service's `except Exception: break` pattern actually swallows upstream errors correctly. Concurrent test confirms the module-level cache dict handles concurrent writes safely via CPython GIL.
FILES: backend/tests/test_bettors.py

## 2026-03-26 — BUGFIX + TESTING (Session 156)
DONE: Fixed follows refresh timer leak — after logout (or JWT expiry), the 30s setInterval kept firing refreshFollowsActivity(), which got 401 and called showView('auth','login'), redirecting users back to the login page 30 seconds after logging out. Fix: showView() now clears _followsRefreshTimer when navigating away from dashboard. Also removed unused BetEvent import from routes/follows.py. Added 1 Playwright test using page.clock.fast_forward(31s) to verify the timer is cleared on logout.
IMPACT: Users no longer get silently bounced back to the login page 30 seconds after logging out. The dead import cleanup prevents future confusion about what follows.py uses.
FILES: frontend/index.html, backend/app/routes/follows.py, backend/tests/playwright/test_ui_flows.py

## 2026-03-26 — TESTING (Session 154)
DONE: Added 7 Playwright E2E tests: back-to-top FAB (appears after scrolling >300px on leaderboard, hidden on load, resets scroll on click) and mobile layout (bottom nav visible at 375px, all 5 nav buttons present, leaderboard tab navigates, desktop sidebar hidden at mobile viewport). Also removed stale Consensus-VIP backlog item already covered by test_tier_gates.py.
IMPACT: FAB and mobile nav are now regression-tested — a broken scroll-to-top or hidden mobile nav would be caught automatically instead of discovered by a user on a phone.
FILES: backend/tests/playwright/test_ui_flows.py

## 2026-03-26 — BRAIN (Session 153)
RESEARCHED: autonomous AI agent best practices 2026, FastAPI 2025-2026 release notes, Polymarket leaderboard + copytrade-wars competitor research, arxiv 2603.22367/2603.24414/2601.11653, Playwright best practices 2026, ECC v1.9.0 re-check, prediction market bot competitive landscape.
DOWNLOADED: Nothing new — ECC still at v1.9.0; no new applicable Python/FastAPI skills.
IMPLEMENTED: (1) playwright.md — DATA ATTRIBUTE SELECTORS section: use data-addr not onclick; CSS display wait condition must use getComputedStyle().display === 'flex' not style.display !== ''. (2) coding.md — FastAPI v0.132 strict Content-Type rule + v0.135 native SSE pattern. (3) activity_log.md — archived sessions 120-140 (32→12 entries).
BACKLOGGED: (1) VIP poll 30s→5s — closes gap vs PolyCop/PolyGun; fulfills CLAUDE.md "Priority speed" VIP promise. (2) /health + /readiness endpoints — production readiness. (3) data-testid on index.html — selector stability. (4) Time-period leaderboard filter. (5) Hedging position filter (stand.trade competitor feature). (6) SQLAlchemy production pool settings.
SOURCES: 12 new sources logged in brain/sources.md.

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

## 2026-03-26 — TESTING (Session 155)
DONE: Fixed Bug #12 — replaced _consensusLoaded boolean (never cleared) with 60-second TTL timestamp so consensus data re-fetches after 60s instead of showing stale prices for the whole session. Added data-testid attributes to 9 key HTML elements (pricing cards, login/register form inputs, bettor cards, follow button). Added 5 Playwright tests: TTL re-fetch regression + data-testid presence checks.
IMPACT: Users on the Consensus tab no longer see stale whale data for the entire session. Playwright selectors are now stable against CSS class changes — data-testid won't break if a designer renames a class.
FILES: frontend/index.html, backend/tests/playwright/test_consensus_tab.py, backend/tests/playwright/test_ui_flows.py
