# Activity Log
*(Sessions 1-160 archived — see activity_log_archive.md)*

## 2026-03-27 — TESTING (Session 189)
DONE: Added 3 Playwright E2E full-journey tests (test_full_journeys.py) — free/basic/VIP users each get a chained multi-step journey: register/login → leaderboard → bettor profile (blurred vs unlocked simulator) → follows tab (padlock vs signal badge) → consensus tab (capped vs all signals, no names vs whale names) → follow limit (upgrade modal for free, no 403 for VIP). 46 → 49 Playwright tests.
IMPACT: Proves the full tier-gated feature chain works end-to-end as a real user would experience it. Catches regressions in state transitions that individual unit tests miss (e.g., "user follows bettor → UI correctly shows padlock in follows tab").
FILES: backend/tests/playwright/test_full_journeys.py

## 2026-03-27 — META (Session 188)
IMPROVED: playwright.md — added FLAKY TEST HANDLING section (re-run failing tests in isolation before investigating; 3-6 Polymarket API rate-limit flakes expected in full-suite runs) and FRESH USER PATTERN section (always register timestamp-email user for follow-limit/quota tests; never reuse shared fixture accounts for state-accumulating tests).
PATTERNS FOUND: Session 187 RULE entries in knowledge.md about flaky tests and fresh user pattern had no matching guidance in playwright.md — work sessions read skill files first, not knowledge.md reflexions, so these patterns would be rediscovered each time rather than applied proactively.
PREDICTED IMPACT: Next full-journey E2E session will correctly expect and handle rate-limit flakes without wasting turns investigating pre-existing failures; follow-limit tests will use fresh users by default.

## 2026-03-27 — TESTING (Session 187)
DONE: Added 4 Playwright E2E tests in test_auth_and_security.py: (1) auth persists after page refresh — dashboard still shown, pe_token intact; (2) bad token redirect — invalid JWT cleared, landing page shown; (3) follow limit upgrade modal — fresh free user hits 403 on 2nd follow, upgrade modal fires; (4) XSS safety — script-tag username rendered via textContent, no alert fires. 42→46 Playwright tests.
IMPACT: Proves the 3 most critical user-facing security/auth flows work correctly in a real browser. Any regression in token handling, paywall follow gate, or XSS rendering will now be caught automatically.
FILES: backend/tests/playwright/test_auth_and_security.py

## 2026-03-26 — TESTING (Session 186)
DONE: Added 1 test for compute_copy_simulator API exception path — mocks httpx.ConnectError on client.get, asserts function returns {simulated_pnl_usd: 0.0, simulated_roi_pct: 0.0, bets_analysed: 0}. 499→500 tests.
IMPACT: Closes the except Exception branch (polymarket.py:333-334) that was unreachable by existing tests — a network failure during simulator fetch previously had zero test coverage.
FILES: backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 185)
DONE: Added 3 tests for conviction_score and conviction_label fields in get_recent_bets: (1) single bet → score=1.0, label=""; (2) 19 small bets + $1000 outlier → score=19.6, label="EXTREME"; (3) API ConnectError → empty list returned safely. 496→499 tests.
IMPACT: Locks in the conviction label contract (EXTREME/HIGH/empty) at the service layer — any change to the scoring thresholds in polymarket.py:431 will now immediately fail a test. Closes the last untested branch in get_recent_bets.
FILES: backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 184)
DONE: Added 3 coverage-gap tests: (1) consensus route cache hit path — pre-populates cache with fresh data, verifies get_consensus_signals is NOT called on second request; (2) JWT with no `sub` claim sent to optional-auth endpoint (/markets/consensus) — verified returns 200 with tier="free" (anonymous treatment); (3) send_telegram ConnectError — mocks httpx.AsyncClient to raise ConnectError, verifies False returned without crash.
IMPACT: Closes 3 branches that were never exercised: markets.py:29, auth.py:72-73, notifications.py:27-29. Any regression in these paths (e.g. cache skipped, exception propagated, optional auth broken) will now be caught immediately.
FILES: backend/tests/test_tier_gates.py, backend/tests/test_security.py, backend/tests/test_notifications.py

## 2026-03-26 — BRAIN (Session 183)
RESEARCHED: autonomous AI agent best practices 2026, LLM agent reliability patterns, FastAPI production patterns 2026, fintech SaaS notification platform benchmarks, Polymarket copy trading competitors and features 2026.
DOWNLOADED: Nothing new — all relevant patterns already in skill files or not applicable to prompt-only agent.
IMPLEMENTED: (1) testing.md — added leaderboard cache key format rule (profit_month_50 contamination pattern from session 180) to Module-level cache isolation section. (2) activity_log.md — archived sessions 141-160 (42→22 entries; header updated to "Sessions 1-160 archived"). (3) backlog.md — added 4 competitive feature items: personalized notification body, outbound webhook channel, delayed Free-tier alerts, minimum bet size filter.
BACKLOGGED: 4 new FEATURE MODE items added to backlog.md; structured logging with request_id added to backlog.
SOURCES: 5 new sources logged.

## 2026-03-26 — TESTING (Session 182)
DONE: Added 3 coverage-gap tests: (1) PUT /alerts/settings with push_subscription as dict object — also fixed AlertSettingsUpdate.push_subscription field from Optional[str]→Optional[Any] so the isinstance(dict) branch at alerts.py:104 is reachable in Pydantic v2; (2) Telegram webhook with message present but empty text — asserts ok=True, no DB change; (3) compute_copy_simulator SELL-side trades excluded — bets_analysed=0 when all trades are SELL. 490→493 tests.
IMPACT: Closes all 3 coverage gaps identified via --cov in session 181. The model fix also means API clients can now send push subscriptions as JSON objects directly (not just pre-stringified), which is more intuitive for callers.
FILES: backend/app/routes/alerts.py, backend/tests/test_alerts.py, backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 181)
DONE: Added 2 tests covering checklist field-presence items: (1) test_follows_live_positions_include_copy_value_pct — mocks 3 positions with known copy_value_pct values (5.0, 22.5, 47.3), asserts each arrives in the route response unchanged; (2) test_bettor_detail_recent_bets_have_side_field — mocks 2 bets with side="BUY", asserts "side" key is present and non-empty on each bet. Removed stale backlog item (accuracy=0.0 boundary already tested at test_polymarket_service.py:572). Added 3 new coverage-gap tasks from automated --cov analysis. 488→490 tests.
IMPACT: Locks in the contract that copy_value_pct and side fields are not silently stripped when passing through route handlers. Previously a route refactor could drop either field and no test would catch it.
FILES: backend/tests/test_follows_live.py, backend/tests/test_bettors.py

## 2026-03-26 — TESTING (Session 180)
DONE: Added 5 tests across 3 backlog items: (1) 3 tests for _normalise_leaderboard_entry accuracy field — percentProfitable=68.5→0.685, missing key→None, explicit null→None; (2) 1 test for GET /bettors accuracy passthrough through route layer (cache-cleared to avoid stale data hit); (3) 1 test for POST /follows 409 detail message asserting response body says "Already following". 483→488 tests.
IMPACT: Locks in the contract that percentProfitable is always converted correctly in the leaderboard normaliser. The cache-clear pattern in the accuracy passthrough test prevents false passes from cached stale data. The 409 detail message test ensures users see actionable feedback, not just a raw error code.
FILES: backend/tests/test_polymarket_service.py, backend/tests/test_bettors.py, backend/tests/test_follows.py

## 2026-03-26 — CODE QUALITY AUDIT (Session 179)
DONE: Audited changed files from sessions 169-177 (polymarket.py, test_polymarket_service.py, test_bettors.py, test_data_integrity.py, test_follows.py, test_health.py, test_auth.py, frontend/index.html). No issues found: Marcus XSS check passed on all innerHTML renders; Leo scan found no dead code, no TODO comments, no duplicate logic, no print() statements; Alex check confirmed no os.getenv in services, no route imports in services. Minor note: import app.routes.bettors as bettors_mod appears inside ~15 test functions (intentional pattern for cache manipulation, not a blocking smell). No code changes needed.
IMPACT: Confirmed all code changes from sessions 169-177 are clean. The 483-test suite has zero smells introduced by the recent accuracy field additions and consensus filter tests.
FILES: none (read-only audit)

## 2026-03-26 — META (Session 178)
IMPROVED: (1) meta/PROMPT.md — fixed reflexion gap check: replaced grep ... | tail -1 (physically-last line) with grep -oE ... | sort -n | tail -1 (numerically highest session number). Old command always returned #167 (last appended) even when sessions 169-177 had reflexions prepended above it. (2) PROMPT.md — added EMBEDDED-GREP RULE: if a backlog item contains a Grep: command, re-run THAT exact grep before picking. (3) backlog.md — added code quality audit task (work sessions = 135, multiple of 5, no audit in backlog).
PATTERNS FOUND: (a) Reflexion gap check gave false alarm of 11 missing sessions because knowledge.md is not in session-number order. (b) Testing backlog items with embedded Grep: lines were picked without re-running those greps across sessions 170, 175, 177 — three distinct sessions wasted turns. (c) Work session count 135 hit a multiple-of-5 milestone with no audit in backlog.
PREDICTED IMPACT: Reflexion gap check will correctly report the highest-numbered session. Work sessions will re-run embedded greps before picking testing tasks.

## 2026-03-26 — TESTING (Session 177)
DONE: Added 3 tests: (1) get_consensus_signals filters resolved markets — mocked 5 whales with curPrice=0.98 asserts 0 signals (the > 0.95 guard works); (2) GET /bettors/{address} profile dict includes accuracy key — confirms the field passes through the route, not just _normalise_profile; (3) GET /auth/me does NOT include accuracy — user account data must not leak bettor metrics. Removed stale backlog task 1 (accuracy regression tests already existed from session 176). Added 3 new HIGH PRIORITY testing tasks. 480 → 483 tests.
IMPACT: Test (1) locks in the resolved-market filter contract in a deterministic mocked test (no live API). Test (2) is a contract test that would catch the accuracy field being accidentally stripped in the route layer. Test (3) confirms the auth/me response boundary — bettor metrics should never appear in user account responses.
FILES: backend/tests/test_polymarket_service.py, backend/tests/test_bettors.py

## 2026-03-26 — TESTING (Session 176)
DONE: Added accuracy field to bettor profile endpoint (_normalise_profile was missing it; leaderboard already had it). Added 5 new tests: leaderboard vs profile accuracy cross-check, follows list order (newest-first, deterministic via DB timestamp offsets), mocked get_consensus_signals (5 whales, whale_count=5 assertion), and 3 unit tests locking in _normalise_profile accuracy field conversion. 475 → 480 tests.
IMPACT: Free users and premium users now get consistent accuracy data across leaderboard and profile pages. Follows list order test prevents silent regression of the DESC sort. Mocked consensus test provides CI-safe deterministic coverage of the signal grouping logic (all live API tests skip on timeout).
FILES: backend/app/services/polymarket.py, backend/tests/test_data_integrity.py, backend/tests/test_follows.py, backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 175)
DONE: Added 3 regression tests covering Bug #9 (lru_cache identity), compute_copy_simulator open-bet skip branch, and GET /auth/me sensitive field absence (hashed_password, stripe_customer_id, telegram_chat_id). 472 → 475 tests.
IMPACT: test_get_settings_returns_same_instance catches if @lru_cache is accidentally removed from config.py (causes .env re-read on every scheduler invocation). test_copy_simulator_skips_still_open_bets locks in the "still-open bets excluded" contract. test_auth_me_does_not_expose_sensitive_fields guards against accidental field exposure in /auth/me.
FILES: backend/tests/test_health.py, backend/tests/test_data_integrity.py, backend/tests/test_auth.py

## 2026-03-26 — CODE QUALITY AUDIT (Session 174)
DONE: Audited files changed in sessions 167-171 (polymarket.py, test_data_integrity.py, test_follows_live.py, test_polymarket_service.py, frontend/index.html). Marcus XSS check passed — all innerHTML renders properly escape API-sourced data. Found 1 Leo smell in polymarket.py: asyncio, time, and datetime were imported inside function bodies instead of at module level. Fixed: moved all three to module-level imports and removed two unused imports (Optional from typing, timezone from datetime). No logic changed.
IMPACT: Codebase now follows standard Python import conventions. Unused imports removed reduces noise.
FILES: backend/app/services/polymarket.py

## 2026-03-26 — BRAIN (Session 173)
RESEARCHED: autonomous AI agent best practices 2026, mutation testing for Python/pytest, Polymarket Data API endpoints, LLM agent memory deduplication techniques.
DOWNLOADED: Nothing — mutmut already on PyPI, no new skill files needed.
IMPLEMENTED: (1) testing.md — added MUTATION TESTING section with mutmut recipe, commands, mutation score targets, and PolyEdge-specific scoped run commands. (2) BRAIN_PROMPT.md — added explicit prohibition on background agents for STEP 2 searches. (3) knowledge.md — added Polymarket GET /trades endpoint discovery + rate limit UNCERTAIN note.
BACKLOGGED: Nothing new — mutmut is a periodic audit tool added to testing.md for use every 20 sessions.
SOURCES: 5 new sources logged.

## 2026-03-26 — TESTING (Session 172)
DONE: Added +-10000% ROI cap to compute_copy_simulator in polymarket.py and a unit test (test_copy_simulator_extreme_price_roi_cap) with all-winning bets at price=0.01 to document and verify the cap behaviour. 471→472 tests.
IMPACT: Without the cap, a bettor who won many bets at very low entry prices (e.g. price=0.01) would show absurd ROI values on their profile simulator card — misleading users into thinking copying them is a guaranteed windfall.
FILES: backend/app/services/polymarket.py, backend/tests/test_data_integrity.py

## 2026-03-26 — TESTING (Session 171)
DONE: Activated the CONDITION_ID_RE regex assertion (^0x[a-fA-F0-9]{64}$) inside test_consensus_whale_count_and_price_range — the regex was defined at test_data_integrity.py:21 but never used in any assertion. Now validates that every consensus signal's condition_id is a properly-formatted 64-char hex ID.
IMPACT: Catches malformed or missing condition_ids from the Polymarket API before they reach users. 471 tests stable.
FILES: backend/tests/test_data_integrity.py

## 2026-03-26 — TESTING (Session 170)
DONE: Added test_recent_bets_timestamps_within_90_days to test_data_integrity.py — verifies that all recent bets from GET /bettors/{address} have timestamps within the past 90 days; handles both Unix float string and ISO-8601 string formats; skips gracefully when no bets available or Polymarket is unreachable. Also removed 2 stale backlog tasks (copy_value_pct and exit-alerts-VIP) whose tests already existed, and added 3 new HIGH PRIORITY testing tasks. 470→471 tests.
IMPACT: Stale Polymarket data (>90-day-old bets served as recent) would give copy-traders wrong context — the timestamp check is a data freshness guard.
FILES: backend/tests/test_data_integrity.py

## 2026-03-26 14:00 — TESTING (Session 169)
DONE: Fixed get_active_positions to filter positions with cur_price < 0.001 or > 0.999 (resolved/expired markets leaking as copyable), and added 3 regression tests: (1) price range filter verified with mock data including price=0 and price=1 positions, (2) copy_signal enum always in {good, fair, late}, (3) consensus signals have whale_count>=3 and avg_entry_price in 0.01-0.99. Fixed 2 existing tests that had no curPrice in fixtures (now filtered out by the new guard). 467→470 tests.
IMPACT: Users no longer see resolved markets in their copy-trading dashboard.
FILES: backend/app/services/polymarket.py, backend/tests/test_data_integrity.py, backend/tests/test_follows_live.py, backend/tests/test_polymarket_service.py

## 2026-03-26 — META (Session 168)
IMPROVED: (1) knowledge.md — added reflexion entries for sessions 156-167 (12 missing reflexions) and updated test suite history table. (2) backlog.md — removed empty section clutter at top, reordered to put HIGH PRIORITY Testing before MEDIUM PRIORITY Edge Cases. (3) meta/PROMPT.md — added reflexion gap check to STEP 1.
PATTERNS FOUND: (a) Reflexion entries for sessions 156-167 were completely absent from knowledge.md — 12 sessions of accumulated rules were missing. (b) Backlog ordering had MEDIUM PRIORITY section before HIGH PRIORITY sections. (c) Test suite history table was 25 sessions stale.
PREDICTED IMPACT: Future META sessions will catch reflexion gaps early. Work sessions will pick HIGH PRIORITY testing tasks before medium ones.

## 2026-03-26 — CODE REVIEW (Session 167)
DONE: Dead code audit — scanned all JS function definitions in frontend/index.html and all imports in backend/app/. Found and removed 1 dead function: tierBadge(tier) (3 lines, generated a tier badge HTML string but was never called from any code path or HTML attribute). All other suspects confirmed live. All backend imports verified in use. 467 tests stable.
IMPACT: Codebase is slightly cleaner; tierBadge was producing a string that was never rendered anywhere.
FILES: frontend/index.html

## 2026-03-26 — CODE QUALITY AUDIT (Session 166)
DONE: Extracted _compute_conviction(bet_amount, avg_bet_usd) helper into scheduler.py — eliminated the identical 8-line conviction score logic that was duplicated in _poll_bets and _poll_vip_bets. Fixed stale docstring in test_cors_headers_present. Added 5 unit tests for _compute_conviction covering normal/HIGH/EXTREME/zero-avg/zero-bet cases. 462→467 tests passing.
IMPACT: Conviction score thresholds now live in one place — a future threshold change only requires editing one function instead of two.
FILES: backend/app/services/scheduler.py, backend/tests/test_scheduler.py, backend/tests/test_health.py

## 2026-03-26 — TESTING (Session 165)
DONE: Added 3 regression tests — test_poll_bets_purges_stale_last_positions: verifies _poll_bets cleans up _last_positions entries for bettors no longer followed (Bug #10 regression coverage); test_health_not_rate_limited: 20 consecutive calls to GET /health all return 200; test_readiness_not_rate_limited: 20 consecutive calls to GET /readiness all return 200. 459→462 tests passing.
IMPACT: Memory leak from unfollowed bettors is now regression-tested. k8s liveness/readiness probes are confirmed to never get 429-blocked.
FILES: backend/tests/test_scheduler.py, backend/tests/test_health.py

## 2026-03-26 — SECURITY (Session 164)
DONE: Added rate limiting to POST /auth/register and POST /auth/login — 10 req/min per IP via slowapi; shared limiter singleton in app/limiter.py; conftest resets limiter storage between tests; 2 regression tests added (459 total).
IMPACT: Brute-force password attacks and mass account creation are now blocked at the server layer. The 11th request in a burst returns 429 Too Many Requests automatically.
FILES: backend/requirements.txt, backend/app/limiter.py, backend/app/main.py, backend/app/routes/auth.py, backend/tests/conftest.py, backend/tests/test_auth.py

## 2026-03-26 — BRAIN (Session 163)
DONE: Fixed stale coding.md (port 8002→8003, StockCards 8-STEP CHAIN→PolyEdge FEATURE WIRING CHAIN with tier-gate cache key rule); created autoagent/skills/rate-limiting.md with complete SlowAPI recipe for auth routes; added FastAPI v0.134 streaming JSON Lines + v0.131 ORJSONResponse deprecation to coding.md; added rate-limiting row to INDEX.md; logged 6 new sources.
IMPACT: Coding sessions will no longer be misled by wrong port (8002) or non-existent PolyEdge file paths. Rate limiting implementation now has a ready-to-use recipe.
FILES: autoagent/skills/coding.md, autoagent/skills/rate-limiting.md, autoagent/skills/INDEX.md, autoagent/brain/sources.md, autoagent/brain/techniques.md, autoagent/memory/knowledge.md

## 2026-03-26 — TESTING (Session 162)
DONE: Added 7 behavioral tests across 3 files — (1) _poll_vip_bets: no-VIP-users early return, VIP-only-addresses filtering, and new-bet creates BetEvent+notification; (2) /follows/live conviction score: keys always present, EXTREME label at 10x avg_bet, empty label below 3x; (3) profile cache: reverse-order test confirms VIP gets unlocked simulator even after free user cached same address.
IMPACT: Three previously untested code paths now have regression coverage — a broken VIP fast-path, a missing conviction field, or a cache key regression would now be caught automatically.
FILES: backend/tests/test_scheduler.py, backend/tests/test_follows_live.py, backend/tests/test_bettors.py

## 2026-03-26 — CODE QUALITY AUDIT (Session 161)
DONE: Audited last 5 sessions changed files; found and fixed readiness endpoint leaking exception details in 503 body and stale scheduler docstring. Logged _last_check race condition to tech_debt.md.
IMPACT: Readiness endpoint no longer exposes DB file paths or SQLAlchemy error strings to public callers — internal error is logged server-side while users see a generic message.
FILES: backend/app/main.py, backend/app/services/scheduler.py, backend/tests/test_health.py
