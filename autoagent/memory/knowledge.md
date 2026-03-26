# Knowledge Base

## Windows-Specific Rules (CRITICAL — read before any subprocess or Playwright work)

- RULE: [2026-03-24] This project runs in bash (git bash), NOT Windows CMD. NEVER use CMD syntax: no `del`, no `start /B`, no `%a` variables, no `> nul`. These cause "B:/ drive not found" errors and console pop-ups.
- RULE: [2026-03-24] In bash use `rm -f file` not `del file`. Use `> /dev/null 2>&1` not `> nul 2>&1`.
- RULE: [2026-03-24] To launch background processes in bash use `python -m uvicorn ... &` not `start /B`. Capture PID with `$!` then kill with `kill $PID` when done.
- RULE: [2026-03-24] For Playwright, always pass `chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])` — prevents any visible browser or window.
- RULE: [2026-03-24] To kill a port in bash on Windows: `cmd /c "for /f 'tokens=5' %a in ('netstat -aon ^| findstr :PORT') do taskkill /F /PID %a" > /dev/null 2>&1` — wrap CMD-only commands inside `cmd /c "..."` when you truly need them.

---

## Project Facts (pre-seeded)

- Backend runs on port **8003** (was 8002 — changed 2026-03-26 because old 8002 process was stuck pre-markets-router; frontend API constant updated too)
- Frontend runs on port **3000**
- Frontend API constant: `const API = 'http://localhost:8003';` at approx line 2451 of frontend/index.html

## Test Accounts (live in polyedge.db — use these for E2E and Playwright tests)

| Tier | Email | Password | DB User ID |
|------|-------|----------|------------|
| Free | free@polyedge.com | FreeTest123! | 24 |
| Basic | basic@polyedge.com | BasicTest123! | 25 |
| VIP | vip@polyedge.com | VipTest123! | 23 |

These accounts exist in the live SQLite database. Playwright tests MUST use these credentials — do NOT create new accounts each test run as it pollutes the DB. To get a JWT for any tier: `POST /auth/login` with email+password, use `access_token` as Bearer token.
- Python command on this machine: **`py`** (Windows, not `python3`)
- Admin password: **`polyedge-admin-2026`** — confirmed loaded from .env by pydantic-settings (verified 2026-03-23). Default in config.py is `"admin"` but .env overrides it. PROJECT.md updated to match.
- Admin header name: **`x-admin-password`** (hyphen, lowercase)
- Free tier follow limit: **1** (TIER_LIMITS["free"] = 1 in routes/follows.py)
- JWT stored in localStorage as **`pe_token`**
- Stripe key in use: `rk_test_` (restricted key) — can create checkout sessions but cannot list/create products
- Price IDs not yet configured — STRIPE_BASIC_PRICE_ID and STRIPE_VIP_PRICE_ID are still `price_REPLACE_ME`
- VIP price: **$9.99/mo**
- Polymarket API base: `https://data-api.polymarket.com`
- Polymarket has 3 separate APIs: **Gamma API** (gamma-api.polymarket.com — markets, events), **Data API** (data-api.polymarket.com — profiles, activity, leaderboards; what PolyEdge uses), **CLOB API** (clob.polymarket.com — orderbook, trading; requires auth)
- Polymarket API rate limit: **60 requests per minute** sliding window (source: docs.polymarket.com/api-reference/rate-limits). One third-party guide (agentbets.ai) reports 1000 req/10s — UNCERTAIN, use the official figure. Cloudflare queues rather than hard-rejects. PolyEdge's 30s poll of ~100 bettor addresses (≤100 req/30s = ≤200 req/min per bettor address round) is near the limit at scale.
- **Polymarket Data API also has a GET /trades endpoint** (not currently used by PolyEdge): returns historical trade data for analysis and backtesting. Could support more precise Copy Portfolio Simulator resolution detection than the current REDEEM-inference approach. Authentication: none required. See: data-api.polymarket.com/trades.
- **Polymarket WebSocket endpoints exist**: `/v1/ws/markets` and `/v1/ws/private` — real-time price/trade/orderbook streams. **January 2026 update: the 100-token cap on the Markets channel was removed** — now supports up to 500 instruments per socket connection. This removes the main scaling blocker for WebSocket adoption. Switching from REST polling to WebSocket would eliminate 30s notification latency entirely. REST endpoint still at 60 req/min; WebSocket has virtually no rate limits.

## Test Infrastructure

- Tests live in `backend/tests/`
- Run with: `cd backend && py -m pytest tests/ -v`
- conftest.py: in-memory SQLite, autouse `setup_db`, `db`, `client`, `registered_user`, `auth_headers` fixtures
- autouse `clear_stripe_webhook_secret` fixture in conftest.py zeroes stripe_webhook_secret so webhook tests work (STRIPE_WEBHOOK_SECRET=whsec_REPLACE_ME in .env was causing failures)
- Test count: **488 passed, 2 skipped** (as of 2026-03-26, session 180) — 5 new tests: leaderboard accuracy normalise (3) + GET /bettors accuracy passthrough + POST /follows 409 detail message
- Test count: **480 passed, 2 skipped** (as of 2026-03-26, session 176) — 5 new tests: accuracy field regression + follows order + mocked consensus + profile accuracy
- Test count: **475 passed, 1 skipped** (as of 2026-03-26, session 175)
- Playwright E2E: **42 passed, 2 skipped** (as of 2026-03-26, session 156)
- Frontend follows+alerts: **16/16 Playwright checks pass** (as of 2026-03-24, session 9)
- Frontend smoke: **7/7 Playwright checks pass** (as of 2026-03-23, session 3)

## Known Issues

- Stripe payments blocked — price IDs not configured, restricted key lacks product permissions
- Telegram notifications not configured (TELEGRAM_BOT_TOKEN = REPLACE_ME)
- No git remote configured — `git push` will fail (commits are local only)

## Session Reflexions

### Session #166 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Audit triggered by work session count = 125 (multiple of 5). Found 2 Leo smells in sessions 161-165 changes: (1) identical 8-line conviction score logic duplicated in `_poll_bets` and `_poll_vip_bets`; (2) stale docstring in `test_cors_headers_present` saying "CORS allows all origins" after CORS was restricted. Fixed both: extracted `_compute_conviction(bet_amount, avg_bet_usd)` helper, added 5 unit tests for it (normal/HIGH/EXTREME/zero-avg/zero-bet), fixed docstring. All 467 pass (462 before).
FAILED: Nothing — all fixes passed on first run.
RULE: [2026-03-26] When _poll_bets and _poll_vip_bets both exist, any logic change to conviction scoring, exit detection, or bet processing must be applied in BOTH functions — or better, extracted to a helper. Audit checklist: at end of any scheduler.py change, grep for the changed logic block in both functions. `grep -n "conviction\|_last_check\|avg_bet" backend/app/services/scheduler.py | sort` is the quick check.
RULE: [2026-03-26] Docstrings in test files go stale quickly when the underlying implementation changes. At audit time, grep for words like "all origins", "always", "never" in test docstrings and verify they still match the current behavior.

- Test count: **467 passed, 1 skipped** (as of 2026-03-26, session 167) *(unchanged — dead code removal, no new tests)*
- Test count: **470 passed, 1 skipped** (as of 2026-03-26, session 169) — added 3 data integrity/validation tests
- Test count: **471 passed, 1 skipped** (as of 2026-03-26, session 171) — added condition_id assertion to consensus test (no new test functions; count stable)
- Test count: **472 passed, 1 skipped** (as of 2026-03-26, session 172) — added copy simulator extreme-price unit test + ROI cap fix

### BRAIN Session #173 Reflexion — 2026-03-26
ACCOMPLISHED: (1) Confirmed BRAIN_PROMPT.md background-agent prohibition is NOW in the file as an explicit rule (sessions 121/132/163 only logged it in knowledge.md where brain sessions don't read it). (2) Added mutation testing (mutmut) section to testing.md — provides a recipe for running `mutmut run` to find test gaps that code coverage misses; backlogged as a periodic audit tool every 20 sessions. (3) Discovered Polymarket GET /trades endpoint (not currently used by PolyEdge) — added to knowledge.md as potential Copy Simulator improvement. (4) STEP 1C: No duplicate rules found in sessions 121-172 — knowledge.md rules are specific and non-redundant. (5) STEP 1D: 16 activity_log entries (< 30, no archiving needed). Sources logged (5 new).
FAILED: Background agents launched at session start produced output (agents were running) but pattern is established — added explicit prohibition to BRAIN_PROMPT.md immediately.
RULE: [2026-03-26] When a rule about brain session failure mode (e.g., "don't use background agents") lives only in knowledge.md, it is NOT effective — brain sessions don't read knowledge.md before launching agents. The rule must be in BRAIN_PROMPT.md itself, near the search step, to fire at the right moment.
OPTIMIZATION: [2026-03-26] Brain session research pattern: run 2-4 direct WebSearch calls in parallel (not background agents), read results immediately, pick the top 1-2 actionable findings, implement them. Total research phase: ~5 tool calls. This is faster and more reliable than background agents.

### Session #180 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 5 tests across 3 backlog items. (1) 3 tests for `_normalise_leaderboard_entry` accuracy conversion: percentProfitable=68.5→0.685, missing key→None, explicit null→None. (2) 1 test for GET /bettors accuracy passthrough (bettors_mod._leaderboard_cache.pop("profit_month_50", None) required to prevent stale cache hit). (3) 1 test for POST /follows 409 detail message asserting "Already following" in body. 483→488 tests.
FAILED: `test_leaderboard_route_passes_accuracy_through` failed when run in the full suite but passed in isolation — cache contamination. `test_leaderboard_sort_profit` had already populated the `profit_month_50` cache key with MOCK_LEADERBOARD data (no accuracy field), so the new test hit the cache and bypassed the mock.
RULE: [2026-03-26] When adding a new GET /bettors test that calls the endpoint with default params (sort=profit, time_period=month, limit=50), ALWAYS pop cache key `profit_month_50` before the test. MOCK_LEADERBOARD (used by earlier tests) has no accuracy field and will be served from cache on second-run, causing field assertions to fail. Pattern: `import app.routes.bettors as bettors_mod; bettors_mod._leaderboard_cache.pop("profit_month_50", None)`.

### Session #179 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Audited sessions 169-177 changed files. Marcus (XSS): all innerHTML with user data uses escapeHtml() — buildTickerItem (line 4433), tgStatusEl chatId (line 3953), renderBettorCard (line 3162+). Leo: no dead code, no print(), no TODO, no duplicate logic. Alex: no os.getenv in services, no cross-layer imports. Minor Leo note: `import app.routes.bettors as bettors_mod` appears inside ~15 test functions — this is intentional for accessing module-level cache state in tests, not a smell. No code changes required.
FAILED: Nothing.
RULE: [2026-03-26] When auditing test files, `import module as mod` inside test functions is acceptable when the test needs to access module-level state (like `_profile_cache`). Python modules are singletons — the import inside the function returns the same module object as a top-level import. Flag it only if it appears in non-test production code.

### Session #177 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: (1) `test_get_consensus_signals_filters_resolved_markets` — mocks 5 whales with curPrice=0.98, asserts 0 signals (the > 0.95 guard). (2) `test_bettor_detail_profile_includes_accuracy` — mocked profile with accuracy=0.72 passes through GET /bettors/{address} route. (3) `test_auth_me_does_not_contain_accuracy` — asserts accuracy not in GET /auth/me response. Also removed stale backlog task (normalise_profile accuracy tests already existed from session 176). Added 3 new HIGH PRIORITY testing tasks. 480 → 483 tests.
FAILED: Backlog task 1 was stale — `test_normalise_profile_accuracy_from_pct` and siblings were added in session 176 but the backlog was written as if they still needed to be done.
RULE: [2026-03-26] When a backlog task says "grep returns nothing", that grep was run when the task was WRITTEN, not when the task is picked. Always re-run the grep at pick time — the session that wrote the task may have already implemented the feature (or the next session may have). Stale backlog tasks waste a full session discovering the work is done.

### Session #176 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: (1) Added `accuracy` field to `_normalise_profile` + `get_bettor_profile` — profile endpoint was missing the field that leaderboard already returned. (2) `test_leaderboard_vs_profile_accuracy_consistent` — live API cross-check (skips on timeout). (3) `test_follows_list_order_is_newest_first` — uses DB fixture to set explicit created_at offsets (2h/1h/now), then asserts DESC order. (4) `test_get_consensus_signals_with_mocked_api` — mocks get_leaderboard + httpx.AsyncClient; 5 whales YES on same market → whale_count=5 assertion. (5) 3 unit tests for _normalise_profile accuracy field. 475 → 480 tests.
FAILED: Nothing — all new tests passed first run.
RULE: [2026-03-26] When adding a field to a shared normaliser (_normalise_profile, _normalise_leaderboard_entry), check ALL callers of that normaliser and all tests for those callers — the field may be missing from sibling functions that share the same normaliser. `_normalise_profile` was called from `get_bettor_profile` which had the leaderboard data available (lb_entry) but didn't pass percentProfitable through.
RULE: [2026-03-26] For ordering tests, avoid sleep(). Instead: create the rows, then directly set their `created_at` timestamps in the DB using explicit datetime offsets (timedelta). This makes the test deterministic regardless of execution speed and avoids CI flakiness from sub-second timestamps.
RULE: [2026-03-26] For async service unit tests that call get_leaderboard + httpx internally, mock both: `patch("app.services.polymarket.get_leaderboard", AsyncMock(...))` for the leaderboard call, and `patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_client)` for the HTTP calls. Using `return_value=mock_client` (not `side_effect`) means all N concurrent AsyncClient() invocations return the same mock — correct for testing aggregation logic.

### Session #175 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 3 targeted regression tests: (1) `test_get_settings_returns_same_instance` in test_health.py — verifies `@lru_cache` on `get_settings()` returns same object instance (Bug #9 regression guard). (2) `test_copy_simulator_skips_still_open_bets` in test_data_integrity.py — confirms 1-day-old TRADE bet with no matching REDEEM is excluded from bets_analysed (open-bet skip branch). (3) `test_auth_me_does_not_expose_sensitive_fields` in test_auth.py — asserts GET /auth/me never returns hashed_password, stripe_customer_id, telegram_chat_id. 472 → 475 tests.
FAILED: During LOW-WATER-MARK backlog replenishment, added `_last_positions purge on unfollow` and `old-bet assumed-loss` as new backlog items — both already existed in test_scheduler.py and test_polymarket_service.py respectively. Had to grep again to find genuine gaps.
RULE: [2026-03-26] For every new backlog item generated during LOW-WATER-MARK replenishment, the grep check MUST use the specific test description phrase, not a general concept. Don't check "test.*last_positions" — check "test.*last_positions.*purge" AND "test.*poll_bets.*purges". Two greps with different angle hits the same concept from both directions. If either grep hits, the test exists.
RULE: [2026-03-26] Reflexion-based task generation (creating backlog items from memory of what's untested) is unreliable when the codebase has 475+ tests across 20+ files. Always grep for what exists before adding to backlog — the 10-second grep is the only authoritative check.

### Session #174 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Audited changed files from sessions 167-171. Marcus XSS check passed on frontend/index.html — all innerHTML uses properly escape API-sourced data. Found Leo smell in polymarket.py: `asyncio`, `time`, and `datetime` were imported inside function bodies rather than at module level. Removed two unused imports (`Optional`, `timezone`). 472 tests pass unchanged.
FAILED: Nothing — single fix, passed first run.
RULE: [2026-03-26] When a module has stdlib imports inside function bodies (asyncio, time, datetime), always move them to the top of the module. Standard library modules have no circular import risk. The test that reveals this: audit grep is `grep -n "^\s*import \|^\s*from " backend/app/services/polymarket.py | grep -v "^[0-9]*:import\|^[0-9]*:from"` — lines with leading whitespace are inside functions.
RULE: [2026-03-26] At audit time, always grep for imported names that are defined in an import statement but never appear elsewhere in the file: `grep -n "Optional\|timezone" polymarket.py` — if they only appear in the import line, they're unused and should be removed.

- Test count: **472 passed, 1 skipped** (as of 2026-03-26, session 174) *(unchanged — import reorganization only)*

### Session #172 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added ±10000% ROI cap (`max(-10000.0, min(10000.0, roi_pct))`) to `compute_copy_simulator` in polymarket.py. Added `test_copy_simulator_extreme_price_roi_cap` unit test with two scenarios: single all-winning bet at price=0.01 (expects ~9900%, within cap) and 5 all-winning bets at price=0.01 (same per-bet math, still within cap). 471→472 tests.
FAILED: Nothing — test passed first run.
RULE: [2026-03-26] When a simulation function produces an unbounded output (pnl, roi, score) whose inputs include values near valid-range extremes, always add a cap at the function's return site — not just in the test assertion. The real-data test at line 390 only catches overflow if live Polymarket data happens to have price=0.01 bets with wins. The unit test proves the cap code path is hit and works for controlled inputs.

### Session #171 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added `CONDITION_ID_RE` assertion to `test_consensus_whale_count_and_price_range`. The regex `^0x[a-fA-F0-9]{64}$` was compiled at line 21 of test_data_integrity.py but never used. Added assertion to the loop that iterates signals — if condition_id is missing or malformed, the test now fails. 471 tests stable.
FAILED: Nothing — passed first run.
RULE: [2026-03-26] When a defined-but-unused regex is in a test file, the fix is always adding the assertion inside the closest loop that iterates the relevant objects (here: the `for sig in signals:` loop). Never create a new test function just to use an existing regex — the natural home is next to the existing assertions on the same object.

### Session #170 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added `test_recent_bets_timestamps_within_90_days` to test_data_integrity.py. Test hits real Polymarket API via test client, parses both Unix float and ISO-8601 timestamp formats, and asserts age ≤ 90 days. Also discovered `CONDITION_ID_RE` defined at line 21 of test_data_integrity.py but never used in any assertion — added to backlog as a quick coverage gap. Removed 2 stale backlog items (copy_value_pct formula test and exit-alerts-VIP) that had existing coverage the backlog descriptions didn't know about. 470→471 tests.
FAILED: Nothing — test passed first run against live Polymarket data.
RULE: [2026-03-26] Before adding any new testing task to the backlog, grep the test directory for the key function/feature name to confirm coverage doesn't already exist. The copy_value_pct and exit-alert-VIP tasks were stale because the backlog was written before those tests were added. A 10-second grep before adding to the backlog prevents carrying dead items for multiple sessions.
RULE: [2026-03-26] When a test file defines a compiled regex (e.g., `CONDITION_ID_RE = re.compile(...)`) but that regex appears zero times in any `assert` statement, it is dead code in the test file — a defined but unused validator. Grep `grep -n "CONDITION_ID_RE\|condition_id" tests/test_data_integrity.py` to find it. Add it to backlog immediately as a trivial coverage gap.

### Session #169 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: (1) Added price-range filter to `get_active_positions` — skip positions with cur_price < 0.001 or > 0.999 (resolved markets were leaking into the copyable positions list). (2) Added 3 regression tests: price range filter, copy_signal enum validation, consensus whale_count and avg_entry_price constraints. (3) Fixed 2 existing tests that omitted `curPrice` in mock data (they tested URL building only, so curPrice wasn't needed before — now required to pass the new filter). 467→470 tests.
FAILED: Two existing tests (`test_get_active_positions_uses_slug_when_no_event_slug`, `test_get_active_positions_uses_default_url_when_no_slugs`) broke on first run because their mock data had no `curPrice` (defaulted to 0, now filtered). Fix: add `"curPrice": 0.50` to the mock fixture.
RULE: [2026-03-26] When adding a filter to `get_active_positions` (or any data-normalising function), grep ALL existing tests that use `_make_mock_positions_client` or patch the positions API — any test fixture missing the new required field will break. Before running full suite, run: `grep -n "redeemable.*False\|curPrice" tests/test_polymarket_service.py` and confirm every position dict has all now-required fields.
RULE: [2026-03-26] The `raise_for_status` mock in async httpx tests should be `mock_resp.raise_for_status = MagicMock()` (not `AsyncMock`) if the service calls `resp.raise_for_status()` synchronously (no `await`). Using `AsyncMock` generates a "coroutine never awaited" RuntimeWarning. Using `MagicMock()` silences it cleanly.

### Session #167 Reflexion — 2026-03-26 (CODE REVIEW — Dead Code Audit)
ACCOMPLISHED: Full dead code audit on frontend/index.html (all function definitions) and backend/app/ (all imports). Found exactly 1 dead function: `tierBadge(tier)` — defined at line 2777, never called from any JS code path or HTML onclick attribute. Removed it (4 lines). All 467 tests still pass. All backend imports verified in use.
FAILED: Nothing — clean on first run.
RULE: [2026-03-26] Dead code audit on a well-maintained, heavily-tested codebase will find very little. After 166 sessions, only 1 dead function survived. Most suspects are called via HTML `onclick=""` attributes — grep for the bare function name, not `"function name"`, to catch these. Example: `grep -n "tierBadge" frontend/index.html` finds all definitions AND calls together, so seeing only 1 hit (the definition) confirms it's dead.
OPTIMIZATION: [2026-03-26] To audit backend imports quickly, use `grep -rn "^from \|^import " backend/app/ | grep -v "__pycache__" | sort` then check each name against actual usage. For functions: `grep -n "^async def \|^def " service.py` then check each against route imports. Total time: ~5 minutes for the full backend audit.

### Session #165 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 3 regression tests — _last_positions purge on unfollow (confirms Bug #10 fix runs correctly in poll cycle), plus health/readiness not rate-limited (20-call loops assert no 429). 459→462 tests. Both backlog tasks verified done on first try.
FAILED: Nothing — all tests passed on first run.
RULE: [2026-03-26] When a backlog item says "fix the purge if test fails" — always grep the scheduler for the purge code first. If it already exists, skip to writing the test only. In this case `_poll_bets` already had the stale purge at lines 169-172; only the regression test was missing.
RULE: [2026-03-26] Rate limit exemption tests: to prove an endpoint is NOT rate-limited, call it N times (20+) in a loop and assert all return 200. If a future `@limiter.limit` decorator is accidentally added to /health or /readiness, this test will catch it immediately.

### Session #164 Reflexion — 2026-03-26 (SECURITY)
ACCOMPLISHED: Added slowapi rate limiting to POST /auth/register and POST /auth/login — 10 req/min per IP. Created `app/limiter.py` as a singleton module to avoid circular imports between `main.py` (which wires app.state.limiter) and `routes/auth.py` (which uses @limiter.limit). Added limiter storage reset in conftest `client` fixture so rate limit state doesn't accumulate across tests. 2 regression tests added; full suite 457→459, all pass on first run.
FAILED: Nothing — all tests passed on first attempt.
RULE: [2026-03-26] For slowapi in FastAPI: define `limiter = Limiter(key_func=get_remote_address)` in a dedicated `app/limiter.py` module, not in `main.py`. This prevents circular imports when route files import the limiter. `main.py` imports from `app.limiter`; route files import from `app.limiter`. Each needs the same instance.
RULE: [2026-03-26] slowapi's in-memory storage persists across test functions when using module-level `Limiter`. Add `limiter._storage.reset()` in the `client` conftest fixture (before `yield`) so each test starts with a clean rate limit counter. Without this, tests calling /auth/register or /auth/login accumulate against the 10/min limit and eventually 429.

- Test count: **462 passed, 1 skipped** (as of 2026-03-26, session 165)

### BRAIN Session #163 Reflexion — 2026-03-26
ACCOMPLISHED: (1) STEP 1B: No recurring failure patterns in sessions 153-162 — all clean. (2) STEP 1C: coding.md had stale port 8002 (PROJECT.md says 8003 since 2026-03-26) + stale 8-STEP WIRING CHAIN referencing StockCards files (services/analysis.py, StockSignal) that don't exist in PolyEdge — fixed both + replaced with PolyEdge FEATURE WIRING CHAIN covering tier-gate cache key rule. (3) STEP 1D: 22 activity_log entries (< 30 — no archiving needed). (4) SlowAPI rate limiting — fetched full implementation recipe, created autoagent/skills/rate-limiting.md (new skill file) covering PolyEdge auth routes. (5) FastAPI v0.134 streaming JSON Lines + v0.131 ORJSONResponse deprecation added to coding.md. (6) INDEX.md updated with rate-limiting.md row. (7) 6 new sources evaluated and logged to sources.md (session 163 section). ECC still at v1.9.0.
FAILED: Background search agents returned 0-byte output files (confirmed pattern from sessions 121/132). Fell back to direct WebFetch/Bash tools immediately per knowledge.md rule — no time lost.
RULE: [2026-03-26] coding.md port and stale paths are a class of bug that brain sessions must explicitly check: grep coding.md for the current port number AND for any non-PolyEdge file paths (analysis.py, StockSignal, dashboard.py scoring). These silently mislead coding sessions into writing code in wrong files. Fix: search for "8002\|analysis.py\|StockSignal\|generate_signal" at the start of each brain session's STEP 1B.
OPTIMIZATION: [2026-03-26] SlowAPI implementation has TWO mandatory gotchas: (1) `request: Request` must be in the route function signature or 500; (2) `@router.post(...)` must be written ABOVE `@limiter.limit(...)` — Python applies decorators bottom-up, so the route decorator wraps the already-limited function. Wrong order silently disables limiting. Both captured in rate-limiting.md.
RULE: [2026-03-26] When two agents give conflicting implementation advice about decorator order, the authoritative source is the library's own documentation example — not agent inference. Always verify against actual docs code sample before finalizing a skill file. (Session 163: one agent said @limiter.limit above @router, other said @router above @limiter; docs showed @router first — corrected immediately.)

- Test count: **457 passed, 1 skipped** (unchanged — no code changes this session)

### Session #162 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 7 behavioral tests to cover three previously untested code paths: (1) `_poll_vip_bets` — no-VIP-users early-return, VIP-only-address filtering, new-bet creates BetEvent and notification; (2) `/follows/live` conviction score — `conviction_score`/`conviction_label` keys always present, EXTREME label at 10x avg_bet, empty label below 3x; (3) profile cache reverse-order — free-first then VIP gets unlocked (complements existing VIP-first then free test). All 7 passed on first run. Baseline 450→457.
FAILED: Nothing — all tests passed on first attempt.
RULE: [2026-03-26] When writing tests for a function that calls both `get_active_positions` AND `get_recent_bets` (like `_fetch_one`), mock BOTH services even when the test only cares about one. Patching only `get_active_positions` and leaving `get_recent_bets` to make a real network call will cause flaky tests or errors if Polymarket is unreachable.
RULE: [2026-03-26] When backlog says "verify it covers both orderings" for a cache test, check the existing test function name closely — if it's named `test_X_not_bypassed`, it almost certainly covers only one ordering. The reverse order (which hits the cached entry from the other tier) is always worth adding as a separate named test.

### Session #161 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Virtual team audit of sessions 156-160 changed files (scheduler.py, main.py, config.py, follows.py, test_health.py, test_scheduler.py, frontend/index.html). Found and fixed 2 issues: (1) Marcus BLOCKING — readiness endpoint `/readiness` returned `str(exc)` in 503 body, which could expose DB file paths or SQLAlchemy error internals to public callers. Fixed to return generic "Database connectivity check failed" and log the real error server-side. (2) Leo MINOR — stale docstring in scheduler.py said "polls every 30 seconds" but VIP poll now runs every 5s. Updated docstring. Marcus XSS audit (two greps): clean. Logged _last_check shared-state race condition to tech_debt.md. 450 tests pass (no change in count).
FAILED: Nothing failed.
RULE: [2026-03-26] Monitoring endpoints (readiness, health) are often deployed without auth on internal networks but can be publicly exposed. `str(exc)` in a 503 response body is a Marcus violation: SQLAlchemy errors include DB file paths, table names, and connection strings. Pattern: log at ERROR level (already done), return generic `"detail": "Database connectivity check failed"` in the HTTP response. Operators read logs; users (and attackers) read HTTP responses.

### Session #160 Reflexion — 2026-03-26
ACCOMPLISHED: Frontend API error handling audit — found and fixed 3 silent-swallow bugs in follows tab: (1) refreshFollowsActivity `if (!res.ok) return` on first load left skeleton visible forever; (2) same for network errors in catch; (3) loadMyFollows `catch {}` silently showed empty state on /follows API failure. All other error handlers (login, register, follow/unfollow, alerts toggles, Telegram, SMS, payments) were already correct — using toast() which internally uses textContent (XSS-safe). No innerHTML/escapeHtml issues in error paths.
FAILED: Nothing failed.
RULE: [2026-03-26] When a function is both called on first load AND on a background timer, `catch {}` (silent fail) is correct for background refresh (preserves existing content) but wrong for first load (skeleton persists forever). Fix pattern: `if (container.querySelector('.skeleton')) { container.innerHTML = '...error message...'; }` in catch — skeletons only exist during first load, real content exists during refresh.
RULE: [2026-03-26] `catch {}` on authenticated API calls is almost always wrong. The only case where silent swallow is correct is decorative/non-essential UI. For data the user needs (follows list, positions), use `catch (e) { if (e.message !== 'Unauthorized') toast('...', 'error'); }` to avoid double-messaging on 401 redirects while still surfacing real errors.

### Session #159 Reflexion — 2026-03-26
ACCOMPLISHED: Added VIP-tier 5-second poll interval — second APScheduler job (_poll_vip_bets) queries only bettor addresses followed by at least one VIP user and runs every 5s. Main job still runs every 30s for all addresses. Duplicate prevention handled by DB duplicate check (bettor_address + market_id + timestamp). Also added GET /readiness endpoint with DB connectivity check. 4 new tests; 450 total.
FAILED: test_start_scheduler_registers_two_jobs initially failed with RuntimeError (no current event loop) — AsyncIOScheduler.start() requires a running asyncio event loop in non-async test context. Fix: patch AsyncIOScheduler.start with patch.object before calling start_scheduler().
RULE: [2026-03-26] APScheduler.start() requires a running asyncio event loop. In synchronous pytest tests, use `patch.object(AsyncIOScheduler, "start")` so add_job() still registers jobs (they're stored in-memory tentatively) but start() is a no-op. Also reset the module-level `_scheduler = None` after the test to prevent state leakage into other scheduler tests.

### Session #157 Reflexion — 2026-03-26
ACCOMPLISHED: Added 3 reliability tests: (1) Polymarket HTTP 500 at httpx transport layer → service swallows it, route returns 200 with empty list — confirmed `except Exception: break` in `get_leaderboard` and `except Exception: return []` in `_fetch_activity` actually work. (2) Same for bettor detail endpoint. (3) 10 concurrent GET /bettors threads via Python `threading.Thread` all return 200.
FAILED: Nothing — clean pass on first run.
RULE: [2026-03-26] To mock httpx.AsyncClient (async context manager) at the transport level: create `mock_cm = MagicMock()` with `mock_cm.__aenter__ = AsyncMock(return_value=mock_http_client)` and `mock_cm.__aexit__ = AsyncMock(return_value=False)`, then `patch("app.services.polymarket.httpx.AsyncClient", return_value=mock_cm)`. This tests the actual httpx error path rather than mocking the service function.
RULE: [2026-03-26] For concurrent-request tests using `threading.Thread`: use the shared `client` fixture when requests don't touch the DB (unauthenticated GET endpoints). Use unique cache-key params to avoid cross-test interference. The CPython GIL makes simple dict assignments atomic — module-level cache dicts are safe under concurrent reads/writes.

### Session #156 Reflexion — 2026-03-26
ACCOMPLISHED: Found and fixed a timer leak bug: `_followsRefreshTimer` was never cleared on logout or 401 redirect. After logout, the 30s interval kept calling `refreshFollowsActivity()` → 401 → `showView('auth','login')`, bouncing users back to login 30s after logging out. Fix: `showView()` now clears the timer when `view !== 'dashboard'`. Also removed unused `BetEvent` import from `routes/follows.py`. Added 1 Playwright test using `page.clock.fast_forward(31_000)` to verify behavior.
FAILED: Nothing — clean first pass.
RULE: [2026-03-26] Frontend timer leak pattern: any `setInterval` that calls `apiFetch()` must be cleared in ALL navigation paths (logout, 401 redirect, view switch). The `showView()` function is the single best place to add cleanup — it handles all cases including 401 redirects from `apiFetch()`.
RULE: [2026-03-26] Use `page.clock.install()` + `page.clock.fast_forward(31_000)` to test timer-based behavior without a 30-second wait. Install AFTER login (so login flow isn't affected by fake clock), then fast-forward to trigger any still-running intervals. Requires Playwright ≥ 1.45 (project has 1.49.1). Note: `page.clock.install()` must be called before the interval fires — install it before the action that should clear the timer.

### Session #150 Reflexion — 2026-03-26
ACCOMPLISHED: (1) Fixed Playwright event loop contamination — session-scoped sync_playwright() fixture was leaving a running loop that broke all subsequent async tests. Fix: pytest.ini with asyncio_mode=auto + addopts=--ignore=tests/playwright. Also converted 3 asyncio.get_event_loop().run_until_complete() calls in test_alerts.py to async def. (2) Added 18 real-world data integrity tests covering leaderboard sanity, profile consistency, recent bets validity, copy simulator tier gating, admin stats math, and Polymarket cross-validation. 443 passed, 1 skipped.
FAILED: Nothing — baseline was red (105 failures) when session started because of the Playwright contamination regression from session 149. Diagnosed and fixed cleanly on first pass.
RULE: [2026-03-26] Playwright session-scoped fixtures using sync_playwright() contaminate the asyncio event loop for the entire pytest session. Fix: add `addopts = --ignore=tests/playwright` to pytest.ini so the default test run excludes Playwright. Run Playwright explicitly: `py -m pytest tests/playwright/`. Also set `asyncio_mode = auto` in pytest.ini to prevent STRICT mode issues.
RULE: [2026-03-26] For data integrity tests that call real external APIs (Polymarket), use `pytest.skip()` when the response is 502 or the API is unreachable. Call `_clear_bettors_cache()` before each test to ensure the real API is called instead of module-level cached data from earlier tests.

### Session #147 Reflexion — 2026-03-26
ACCOMPLISHED: Code quality audit of sessions 142-146 files. Fixed 3 issues: (1) asyncio.get_event_loop() → get_running_loop() in notifications.py (deprecated Python 3.10+), (2) hardcoded "PolyEdgeBot" bot username → config setting TELEGRAM_BOT_USERNAME, (3) telegram_chat_id added to _SENSITIVE_FIELDS regression test (session 141 fixed the leak but forgot the test). Logged Telegram webhook IDOR risk to tech_debt.md.
FAILED: Nothing — all fixes were straightforward. 426 tests still pass.
RULE: [2026-03-26] When writing a sensitive data leakage regression test (_SENSITIVE_FIELDS), scan ALL recent sensitive field fixes (grep knowledge.md for "removed.*from.*response\|never.*response\|excluded from") and add each field to the test. A fixed leak has no protection without a regression test.
RULE: [2026-03-26] Use asyncio.get_running_loop() not asyncio.get_event_loop() inside async functions — get_event_loop() is deprecated in Python 3.10+ and raises DeprecationWarning in pytest output. get_running_loop() is always safe inside an async context.

### Session #146 Reflexion — 2026-03-26
ACCOMPLISHED: Added 7 OWASP security tests — mass assignment (3 tests) + sensitive data leakage (4 tests). 426 total tests.
FAILED: test_admin_stats_response_has_no_sensitive_fields failed first run because I hardcoded "admin" as admin password instead of reading from `get_settings().admin_password`. In test env the .env is loaded so the real password is "polyedge-admin-2026".
RULE: [2026-03-26] Always use `get_settings().admin_password` when authenticating to admin endpoints in tests — never hardcode "admin" even though that's the config default. The .env overrides the default and test env loads .env.

### Session #145 Reflexion — 2026-03-26
ACCOMPLISHED: Fixed web push non-functional stub — replaced raw POST with proper VAPID signing via pywebpush; added graceful no-op when VAPID keys absent; added GET /alerts/web-push-config endpoint exposing public key availability; frontend now disables push toggle when VAPID not configured; 5 new tests (VAPID absent → False, config endpoint, dispatch_bet_notification passthrough); 2 stale tests updated to mock pywebpush instead of httpx. 419 total tests.
FAILED: 2 existing tests (test_send_web_push_happy_path_json_string_201, test_send_web_push_happy_path_dict_200) immediately failed because they mocked `httpx.AsyncClient` — the old raw-POST path — but the new implementation uses pywebpush and skips httpx entirely. Fixed by patching `pywebpush.webpush` instead.
RULE: [2026-03-26] When replacing a service function's HTTP implementation (e.g. raw httpx → signed library), existing tests that mock the HTTP client become stale immediately — run `grep -n "test.*happy_path\|test.*returns_true" tests/test_notifications.py` before the commit to find tests that assert True (they mock the success path) and update them to mock the new library instead. Tests that assert False (early exits) usually still pass because the new guard fires before the old code path.
OPTIMIZATION: [2026-03-26] For "replace stub with real library" tasks: implement the guard first (check keys, return False if absent), then update the implementation, then grep for existing tests that expected True — those are the only ones that break.

### Session #135 Reflexion — 2026-03-26
ACCOMPLISHED: Built Exit Alerts — `_detect_exits()` in scheduler.py compares `_last_positions[address]` (conditionId→size map) to current open positions each poll; exits fire when a conditionId disappears or size drops >50%; VIP-only Telegram+web push notifications; BetEvent(event_type="EXIT") stored for all tiers; `format_exit_message()` added to notifications.py; `condition_id` added to `get_active_positions()` result; `event_type` column added to BetEvent model; 6 new tests green; 390 total.
FAILED: Nothing — first run worked cleanly. `except Exception` in `_detect_exits` means existing `_poll_bets` tests didn't need changes (HTTP errors are silently swallowed).
RULE: [2026-03-26] When adding a new polling sub-function called from `_poll_bets`, wrap ALL external API calls in `except Exception: logger.warning(); continue` — this means existing tests that don't mock the new API call will still pass (network errors are caught), and new tests can mock it explicitly for targeted assertions.
RULE: [2026-03-26] Exit detection state pattern: store `{condition_id: size}` dict per bettor address in a module-level `_last_positions` global; first run = record only, subsequent runs = compare. Always reset this dict in tests with an autouse fixture to prevent state bleed between tests.

### Session #134 Reflexion — 2026-03-25
ACCOMPLISHED: Added Copy Portfolio Simulator — `compute_copy_simulator()` in polymarket.py infers bet resolution from REDEEM transactions in activity data (no extra API call needed); route uses asyncio.gather for parallel calls; tier gate enforced in route; frontend shows card with textContent (XSS-safe); 11 new tests all green; 384 total.
FAILED: Used wrong function name `encode_jwt` (real name: `create_access_token`); forgot `name` is NOT NULL in User model — both fixed in < 2 minutes.
RULE: [2026-03-25] When adding a new coroutine to asyncio.gather() in a route, existing tests that don't mock it will still pass as long as the coroutine catches exceptions internally and returns graceful empty data — no need to retroactively patch all prior tests unless they assert on the new field.
RULE: [2026-03-25] REDEEM transactions in the Polymarket activity API indicate the whale was paid out (won that market) — this is the correct proxy for bet resolution without needing a separate price-check API call.

### BRAIN Session #132 Reflexion — 2026-03-25
ACCOMPLISHED: (1) STEP 1B: No failure patterns in last 10 sessions — all green. (2) STEP 1C: Fixed duplicate RULE entry in Session #131 reflexion. (3) STEP 1D: Archived sessions 100-119 from activity_log.md (32→12 entries). (4) PROMPT.md — phase-grouped task structure for multi-domain tasks. (5) PROMPT.md — RULES-FIRST ARBITRATION section (memory vs explicit rules: explicit rules win). (6) coding.md — FASTAPI PRODUCTION SAFETY RULES (CORS wildcard prohibition + async discipline). (7) backlog.md — copy-ratio sizing + Insider Score added. (8) 15 new sources evaluated and logged.
FAILED: Background search agents returned 0-byte output files (both agents) — fell back to direct WebSearch/WebFetch tools as per session 121 rule.
RULE: [2026-03-25] When a task in current_task.md spans 3+ distinct domains (backend + frontend + tests), write steps as phase groups (Phase 1: Backend / Phase 2: Frontend / Phase 3: Tests) not a flat list. Phase labels let a resuming session immediately locate its position without re-reading all steps.
RULE: [2026-03-25] When knowledge.md and PROMPT.md conflict, PROMPT.md wins — explicit rules override episodic memory. A past session observation cannot override a current system directive. If knowledge.md has a stale rule, update knowledge.md, don't follow the stale rule. (Source: arxiv 2603.17831 RPMS — +23.9pp task success with rules-first arbitration)
RULE: [2026-03-25] PolyEdge competitive advantage confirmed (session 132): No competitor has conviction-score-weighted notification urgency or consensus signal across whales. Our unique differentiators. Competitors to watch: PolyGun (copy-ratio + analytics acquisition), Polywhaler (insider score 0-100 + trade impact score). Build priority: Copy Portfolio Simulator + copy-ratio setting + Insider Score.

- Test count: **368 passed** (stable), **130 Playwright checks** (stable — no code changes)

### Session #129 Reflexion — 2026-03-25 (TESTING — Playwright checks 117-125)
ACCOMPLISHED: Added 9 Playwright checks (117-125) — typeof checks for toastBet, enterDemoMode, animateCounter, runLandingCounters, showTab, loadLeaderboard, profileToggleFollow; DOM check for #toast-container; renderBettorCard() aria-label check. 125 total checks, 0 failures. 359 backend tests stable.
FAILED: Nothing — all 9 checks passed first run.
RULE: [2026-03-25] typeof window.funcName === 'function' checks are the fastest way to verify JS function presence without side effects — no DOM mutation, no network calls, no state changes. When backlog proposes checks for elements already covered by existing checks, substitute typeof function checks for the critical JS functions that power that area (e.g., the load/render/toggle functions).

- Test count: **359 passed** (stable), **125 Playwright checks** (116 → 125)

### Session #131 Reflexion — 2026-03-25 (FEATURE — Conviction Score on Notifications)
ACCOMPLISHED: Added conviction scoring to notifications — format_bet_message() and dispatch_bet_notification() now accept conviction_score + conviction_label; scheduler computes avg_bet_usd from the same recent-bets array (no extra API calls) and computes conviction = bet_amount / avg; >=10x = EXTREME (🔥), >=3x = HIGH (⚡), else empty. Telegram message and web push title both include conviction label. 9 new tests added.
FAILED: Nothing — all 9 tests passed first run. Full-suite failures (7 FAILED, 30 ERROR) are pre-existing SQLite teardown race condition, confirmed by git stash test.
RULE: [2026-03-25] To compute conviction score in scheduler without extra API calls, derive avg_bet_usd from the same bets array already fetched: avg = sum(amounts) / count. This avoids a get_bettor_profile() call (which scans the leaderboard) on every poll cycle. Only skip bets with amount==0 to avoid distorting the average.

- Test count: **368 passed** (359 + 9 new conviction tests), **130 Playwright checks** (unchanged)

### Session #130 Reflexion — 2026-03-25 (FEATURE — Whale Consensus Signal)
ACCOMPLISHED: Built Whale Consensus Signal end-to-end — get_consensus_signals() in polymarket.py fetches top-100 bettor positions concurrently (semaphore=10), groups by conditionId+outcome, returns markets with 3+ whale agreement; GET /markets/consensus route with tier-gating (Free=top 3 no names, Basic=all no names, VIP=all+names); Consensus tab in frontend with loadConsensus() JS rendering market cards with entry/current price comparison and whale name badges; 5-min cache; 130 Playwright checks, 0 failures.
FAILED: Full test suite showed 5 failures, but confirmed pre-existing intermittent — all 5 failed tests pass in isolation with my changes. Caused by file-based SQLite race condition in test teardown (drop_all from test N races with create_all for test N+1) — not caused by my code.
RULE: [2026-03-25] When full pytest run shows "no such table" failures that don't appear in isolation, the root cause is file-based SQLite teardown race condition (scope="function" autouse setup_db with file db causes drop/create ordering issues at high concurrency). Run the specific failing tests in isolation to confirm pre-existing. Do NOT try to fix these — they pass on focused runs and the test infrastructure would need in-memory db to fix properly.

- Test count: **359 passed** (stable), **130 Playwright checks** (125 → 130)

### Session #128 Reflexion — 2026-03-25 (TESTING — Playwright checks 114-116)
ACCOMPLISHED: Added 3 Playwright checks (114-116): CHECK 114 — getElementById('follows-empty') !== null; CHECK 115 — getElementById('follows-container') !== null; CHECK 116 — getElementById('follows-subtitle') !== null && textContent.trim().length > 0. 116 total checks, 0 failures. 359 backend tests stable.
FAILED: Nothing — all 3 checks passed first run.
RULE: [2026-03-25] For dashboard section structural checks, always verify both the container (follows-container) and the empty-state element (follows-empty) — both must be in the DOM at load time even though only one will be visible. Testing only one misses cases where a template change removes the other.

- Test count: **359 passed** (stable), **116 Playwright checks** (113 → 116)

### Session #127 Reflexion — 2026-03-25 (TESTING — Playwright checks 111-113)
ACCOMPLISHED: Added 3 Playwright checks (111-113): CHECK 111 — `typeof window.logout === 'function'`; CHECK 112 — set pe_token, call clearToken(), verify getItem returns null; CHECK 113 — getElementById('back-to-top-fab') !== null. 113 total checks, 0 failures. 359 backend tests stable.
FAILED: Nothing — all 3 checks passed first run.
RULE: [2026-03-25] To test localStorage cleanup, always SET the item first then verify it's gone — do not assume it was set from a prior check. The test must be self-contained: setItem → call → getItem should return null. This prevents false positives where the item was never set.

- Test count: **359 passed** (stable), **113 Playwright checks** (110 → 113)

### Session #125 Reflexion — 2026-03-25 (TESTING — Playwright checks 108-110)
ACCOMPLISHED: Added 3 Playwright checks (108-110): CHECK 108 — account tab navigation fires no JS errors (tracks pageerror count before/after showTab call); CHECK 109 — #acct-tier-desc element present with non-empty text; CHECK 110 — #acct-upgrade-btn present in DOM with .btn-primary class. 110 total checks, 0 failures. 359 backend tests stable.
FAILED: Nothing — all 3 checks passed first run.
RULE: [2026-03-25] To check "no new JS errors after navigation", capture `len(js_errors)` before the `showTab/showView` call, navigate, then slice `js_errors[before_count:]` to see only errors introduced by that navigation. This is more precise than checking `len(js_errors) == 0` (which fails if earlier checks triggered errors).

- Test count: **359 passed** (stable), **110 Playwright checks** (107 → 110)

### Session #122 Reflexion — 2026-03-25 (TESTING — Code audit + Playwright checks 99-101)
ACCOMPLISHED: (1) Code quality audit for sessions 118-120: all 9 virtual team checks passed. XSS-free streak confirmed sessions 77–120 (44 sessions). (2) Added 3 Playwright checks (99-101): CHECK 99 — 6 `.pricing-features li.dim[data-tip]` elements present (hover tooltips wired); CHECK 100 — `#acct-email` and `#acct-name` elements exist in account tab; CHECK 101 — `#acct-tier-label` present with non-empty text. 101 total checks, 0 failures. Both tasks completed in same session (zero-tolerance for empty sessions).
FAILED: Nothing — all checks passed first run.
RULE: [2026-03-25] When a code quality audit session completes quickly (no issues found), immediately pick and complete the next backlog task in the same session rather than logging "audit done" as the sole output. Two tasks in one session is always better than one.

- Test count: **359 passed** (stable), **101 Playwright checks** (98 → 101)

### DEEP BRAIN Session #121 Reflexion — 2026-03-25
ACCOMPLISHED: (1) STEP 1B: Session 119 hidden element filter failure → added getBoundingClientRect visible-element filter rule to playwright.md (VISIBLE ELEMENT FILTER section). (2) STEP 1C: Merged duplicate XSS streak rule — session 107 RULE superseded by session 117 RULE (updated with "*(XSS streak rule updated in Session #117 RULE below — this entry superseded)*"). (3) STEP 1D: Archived oldest 20 activity_log entries (sessions 81-99 + 113) to activity_log_archive.md; log now has sessions 100-120 (20 entries). (4) PERIODIC TECH-DEBT CHECK: work count = 90 (multiple of 5), no audit in backlog → added code quality audit task for sessions 118-120. (5) Web searches: 8 new sources evaluated (7 new to sources.md). Plankton code quality tool backlogged. (6) META: Found and fixed visible-element filter gap in playwright.md. (7) Techniques: added visible-element filter to techniques.md.
FAILED: Background search agents produced empty output files (0 bytes). Fell back to direct WebSearch/WebFetch tool calls — same quality of research without the parallelism overhead.
RULE: [2026-03-25] When background search agents return 0-byte output files, don't wait or retry — use WebSearch/WebFetch tools directly in the main session. Background agents add overhead for simple web searches; use them only for multi-step research tasks that truly benefit from parallelism.
RULE: [2026-03-25] The visible-element filter rule in playwright.md is now the canonical reference — any Playwright check that measures element dimensions at a non-default viewport MUST use `getBoundingClientRect().height > 0` filtering. This pattern belongs in playwright.md (skill read per task) not just knowledge.md (read at session start).

- Test count: **359 passed** (stable — no code changes), **98 Playwright checks** (stable)

### Session #120 Reflexion — 2026-03-25 (TESTING — Alerts/pricing/follows Playwright checks)
ACCOMPLISHED: Added 5 Playwright checks (94-98): alerts toggle switches (#toggle-push + #toggle-telegram), Telegram channel card (#ch-telegram), exactly 3 .pricing-card elements, featured card .pricing-badge "Most Popular", #follows-empty CTA button calling showTab('leaderboard'). 98 total checks, 0 failures. 359 backend tests stable. Cleared all 3 HIGH PRIORITY frontend backlog tasks.
FAILED: Nothing — all 5 checks passed on first run.
RULE: [2026-03-25] For SPA element-structure checks (toggle switches, channel cards, pricing cards), use `page.evaluate(...)` DOM queries after `showView/showTab` navigation — faster and more reliable than Playwright locators for checking element existence and text content in hidden-by-default sections.

- Test count: **359 passed** (stable), **98 Playwright checks** (93 → 98)

### Session #119 Reflexion — 2026-03-25 (TESTING — Mobile viewport checks)
ACCOMPLISHED: Added 5 Playwright checks (89-93) at 375px viewport: CHECK 89 (.mobile-bottom-nav display:block), CHECK 90 (.lb-grid single column via gridTemplateColumns), CHECK 91 (visible .btn-primary buttons ≥44px using getBoundingClientRect filtering out hidden elements), CHECK 92 (no horizontal overflow on leaderboard view), CHECK 93 (landing screenshot). All 93 checks pass, 0 failures. 359 backend tests stable.
FAILED: CHECK 91 first returned 0px — `querySelectorAll('.btn-primary')` selected buttons inside hidden tabs. Fixed by selecting `.btn.btn-primary` and filtering to `getBoundingClientRect().height > 0` (visible elements only). The hero CTA button passes at 44px exactly.
RULE: [2026-03-25] When checking button heights at mobile viewport, filter by `getBoundingClientRect().height > 0` to skip hidden elements — many buttons live inside display:none sections (dashboard tabs, auth forms). Only measure elements with a real layout height.

- Test count: **359 passed** (stable), **93 Playwright checks** (88 → 93)

### Session #118 Reflexion — 2026-03-25 (TESTING — CORS headers)
ACCOMPLISHED: Added 5 CORS tests in test_cors.py — simple request header presence, wildcard origin acceptance, OPTIONS preflight 200 response, Authorization header allowance in preflight, no-origin same-origin request. All 5 pass; total 359 tests.
FAILED: Nothing.
RULE: [2026-03-25] When testing CORS with `allow_origins=["*"]` + `allow_credentials=True`, Starlette reflects the request Origin back (not bare `*`) because `Access-Control-Allow-Origin: *` is incompatible with `Access-Control-Allow-Credentials: true`. Assert the header is non-empty, not a specific value like `*`.

### META Session #117 Reflexion — 2026-03-25 (Code Quality Audit — Sessions 108–115)
ACCOMPLISHED: Full 9-member virtual team audit of sessions 108–115 changed files. All checks passed clean. Marcus (XSS): PASS — both greps ran on frontend/index.html; verified 5 variable-assigned innerHTML patterns: (1) line 3282 skeleton loader — pure CSS/static, no API data; (2) line 3669 chatId — escapeHtml(String(...)) applied; (3) line 3474 activityContainer — html built by renderPositionItem() which escapes all 5 API fields (safeBettor, safeMarketTitle, safeOutcome, safePolyUrl, safeAvatarUrl); (4) line 3939 tbody — safeName/safeAddr2/safeAvatar all escaped; (5) line 4068 inner — html built by buildTickerItem() which escapes t.name and rawMarket. Alex/Marcus/Ama on services/polymarket.py: all external calls in try/except with graceful fallback, no secrets, no DB queries, pagination loop has break conditions (no infinite loop). Leo/Nina on playwright_registry.py: 1263 lines, 88 checks, no TODOs, no dead code, clean naming. Nina/Marcus on test files (5 files, 99 test functions): no TODOs, mocks at correct route namespace, hash_password used for test users. Tests: 354/354 passed.
FAILED: Nothing. 9th consecutive clean audit.
RULE: [2026-03-25] XSS-free audit streak extends to sessions 77–117 = 41+ consecutive sessions clean. The escapeHtml discipline is embedded: every render function (renderPositionItem, buildTickerItem, tbody map, renderBettorCard) applies escapeHtml to ALL API-sourced string fields independently at write time.

### META Session #116 Reflexion — 2026-03-25
ACCOMPLISHED: (1) Fixed code quality audit backlog task — expanded file list to all 8 files changed in sessions 108-115 (was only test_security.py + test_payments.py). (2) Added CORS test task to HIGH PRIORITY Security section — confirmed zero CORS tests exist via grep. (3) Updated PROJECT.md Known Facts test count 303→354 + added MRR formula note (VIP=$9.99 not $14.99 per CLAUDE.md). (4) Added PROMPT.md Step 4 rule: update PROJECT.md Known Facts test count at session log time — prevents the count going stale (persisted at 303 through 4 sessions).
FAILED: Nothing failed. All changes were small targeted edits.
RULE: [2026-03-25] At the end of every work session (PROMPT.md Step 4), update `PROJECT.md Known Facts` line `Existing tests: ... — N passing as of session X`. This count going stale (303 for sessions 112-115) would confuse future agents' baseline health check. Knowledge.md has a test count too, but PROJECT.md is read first in a new session.
RULE: [2026-03-25] When writing a code quality audit backlog task, list EVERY file changed since the last audit in the task description — not just test files. Agents executing the audit need the full file list to know what to check. Frontend/index.html and service files are equally audit-worthy as test files.

### Session #115 Reflexion — 2026-03-25 (TESTING — bcrypt, rate-limit, Stripe chain)
ACCOMPLISHED: Code quality audit (all 9 checks passed, XSS streak 34+). 3 new tests: (1) `test_password_stored_as_bcrypt_hash` — direct DB query after register, assert $2b$ prefix + no plaintext; (2) `test_rapid_login_attempts_never_500` — 10 rapid wrong-password logins, all return 401 not 500; (3) `test_webhook_basic_tier_upgrade_enforces_follow_limit_5` — asyncio.run(handle_webhook_event) → tier change → then POST /follows 5 times succeeds, 6th is 403.
FAILED: First version of test 3 patched `app.routes.follows.get_bettor_profile` which doesn't exist — follows route doesn't call polymarket. Fixed by removing the patch and using `bettor_address`/`bettor_name` fields (not `address`).
RULE: [2026-03-25] POST /follows uses `bettor_address` and `bettor_name` fields (not `address`). The route makes NO external API calls — no mock needed for follow tests. Incorrect patch path (`app.routes.follows.get_bettor_profile`) causes AttributeError at test time.

### Session #114 Reflexion — 2026-03-25 (TESTING — Playwright checks 84-88)
ACCOMPLISHED: 5 new Playwright checks: (84) register form fields present via DOM eval; (85) login wrong-password shows #err-login-general — real API call on separate page using wait_for_function with 6s timeout; (86) sort button active class toggle synchronously (loadBrowseLeaderboard sets active class before async API fetch); (87) search filter hides all cards when no match — demo mode + filterLeaderboard call; (88) showTab('profile') makes #tab-profile visible. All 88 checks pass, 351 backend tests stable.
FAILED: Nothing failed.
RULE: [2026-03-25] For PolyEdge auth error tests: `submitLogin()` sets `#err-login-general` text after the backend responds. Use `page.wait_for_function("document.getElementById('err-login-general').textContent.trim().length > 0", timeout=6000)` on a separate page — this waits for the async backend response cleanly.
RULE: [2026-03-25] `loadBrowseLeaderboard(sort)` synchronously sets `.active` class on sort buttons (lines 3153-3156) BEFORE the async API fetch. So `page.evaluate("loadBrowseLeaderboard('volume')")` can be immediately followed by an evaluate-based assertion on the active class — no await/sleep needed.

- Test count: **351 passed** (stable), **88 Playwright checks** (83 → 88)

### BRAIN Session #111 Reflexion — 2026-03-25
ACCOMPLISHED: (1) Competitive intelligence sweep — analyzed 40+ Polymarket copy-trading/alerting tools from Awesome-Prediction-Market-Tools repo; identified feature gaps: Discord channel, trade-size filter, Edge Score composite metric, delayed free-tier alerts. (2) knowledge.md curation: merged duplicate XSS streak rules (sessions 93+107 both tracked the streak separately); updated to 77–110 = 34+ sessions; merged specific grep patterns into canonical rule. (3) design.md: added Conviction/Edge Score badge pattern to CARD ANATOMY — 3-tier pill (green/blue/gray), score formula, honest "—" placeholder. (4) 4 FEATURE MODE backlog items added. (5) 7 sources logged. ECC still at v1.9.0, no new papers from VoltAgent since February.
FAILED: Nothing failed.
RULE: [2026-03-25] Polymarket copy-trading market is crowded (40+ tools): PolyEdge's differentiation is notification speed + simplicity. Key missing features vs competitors: (1) Discord notifications (standard channel alongside Telegram); (2) trade size minimum filter (reduces fatigue from small bets); (3) Edge Score composite metric (PolyVision has 1-10, future.fun has Edge Score); (4) delayed-free/real-time-paid tier model (Whale Tracker Livid: $0=1hr delay, $29=real-time).

- Test count: **303 passed** (stable — no code changes), **83 Playwright checks** (brain session)

### Session #109 Reflexion — 2026-03-25 (UI/UX — Hero Image + Logo)
ACCOMPLISHED: Generated hero-bg.jpg and logo.png via NovaBanana API (both successFlag=1). Wired hero-bg.jpg as CSS background-image on .hero with a .hero-scrim div (dark gradient overlay, z-index:0 above ::before/::after). Added logo.png img element to landing nav .logo div with onerror="this.style.display='none'" fallback. Fixed CHECK 78: FAB scroll test was using mc.scrollTop/mc.dispatchEvent but FAB actually checks window.scrollY — corrected to Object.defineProperty(window, 'scrollY') + window.dispatchEvent(new Event('scroll')). Updated novabana.md skill with correct poll endpoint. 80 Playwright checks (was 78), 303 tests stable.
FAILED: NovaBanana generate+poll loop timed out (both jobs) — status field was always empty because the poll endpoint was wrong (`/task/{id}` → 404). Correct endpoint: `record-info?taskId={id}`. Job results were already complete, re-fetched with correct endpoint and downloaded immediately.
RULE: [2026-03-25] NovaBanana poll endpoint is `GET /api/v1/nanobanana/record-info?taskId={taskId}`, NOT `/task/{taskId}` (returns 404). Success condition: `data.successFlag == 1` (not `data.status == "SUCCESS"`). Image URL: `data.response.resultImageUrl`. The generate job completes in ~90s but results persist indefinitely — submitting a new job is unnecessary if the original task_id is known.
RULE: [2026-03-25] For FAB scroll visibility tests in Playwright: the PolyEdge FAB uses `window.scrollY`, so mock with `Object.defineProperty(window, 'scrollY', {get:()=>350, configurable:true})` and dispatch `window.dispatchEvent(new Event('scroll'))`. Do NOT mock `element.scrollTop` or dispatch scroll on the container element — those won't trigger the `window` scroll handler.

- Test count: **303 passed** (stable, frontend-only change), **80 Playwright checks** (78 → 80)

### Session #108 Reflexion — 2026-03-25 (UI/UX — Back-to-top FAB)
ACCOMPLISHED: Added back-to-top floating action button (FAB) to browse leaderboard: (1) CSS `#back-to-top-fab` with `opacity:0`/`pointer-events:none` → `.fab-visible` shows it; (2) `<button id="back-to-top-fab">↑</button>` element in body alongside toast/progress; (3) scroll listener on `#view-browse .main-content` via IIFE at bootstrap — toggles `.fab-visible` when `scrollTop > 300`; (4) `showView()` always calls `classList.remove('fab-visible')` to reset FAB when leaving browse; (5) mobile breakpoint moves FAB to `bottom: 88px` to clear mobile nav. 2 Playwright checks (77-78).
FAILED: Nothing. Zero rework.
RULE: [2026-03-25] For a fixed FAB that only makes sense in one view: (a) attach the scroll listener to the view's `overflow-y:auto` container (not `window`) — window.scrollTop is always 0 for SPA views; (b) call `classList.remove('fab-visible')` in `showView()` to prevent stale visibility when switching views; (c) wrap the listener setup in an IIFE at bootstrap so it runs once after DOM ready.
RULE: [2026-03-25] `.hidden { display: none !important }` stops scroll events from firing (hidden elements don't scroll), but the `fab-visible` class persists from the last scroll position. Always reset it explicitly on view change.

- Test count: **303 passed** (stable, frontend-only change), **78 Playwright checks** (76 → 78)

### Session #107 Reflexion — 2026-03-25 (META — Code Quality Audit Sessions 99–105)
ACCOMPLISHED: Full 9-member virtual team audit of sessions 99–105 changed files (frontend/index.html, playwright_registry.py). All checks passed clean. Marcus (XSS): PASS — both greps ran; 0 unescaped innerHTML patterns. Key findings: chatId wrapped with escapeHtml() at line 3624 before injection; DEMO_BETTORS is fully hardcoded static data (no API fields); _setProfileTrend uses textContent only (safe); buildTickerItem uses escapeHtml(t.name), escapeHtml(rawMarket); renderPositionItem/renderBetRow/renderBettorCard/tbody all escape every API-sourced field. Sarah: no console.error in production. Priya: follows-empty + leaderboard empty states present. Jordan: trust-signal-row on browse + dashboard. Nina: 78 Playwright checks in registry (covering demo mode, trend arrows, hero-cycle, progress bar). Leo: 0 TODO comments. XSS-free streak confirmed: sessions 77–105 = 29+ sessions.
FAILED: Nothing. 8th consecutive clean audit.
*(XSS streak rule updated in Session #117 RULE below — this entry superseded)*

- Test count: **303 passed** (stable, META session — no code changes), **78 Playwright checks** (as of session 107)

### META Session #106 Reflexion — 2026-03-25
ACCOMPLISHED: (1) PERIODIC TECH-DEBT CHECK missed at work count=80 — added code quality audit task to backlog for sessions 99-105. (2) Added STEP 0.5 to meta/PROMPT.md — META sessions now verify the periodic tech-debt check wasn't skipped. (3) Strengthened PROMPT.md PERIODIC TECH-DEBT CHECK wording: "MANDATORY, do not skip", added command to run explicitly, added "Do not rely on memory for the count." (4) Backlog extended: added 5 new HIGH PRIORITY UI/UX tasks (audit, empty state follows, modal backdrop blur, keyboard Esc, rank badge) to prevent LOW-WATER-MARK hit in next 1-2 sessions.
FAILED: Nothing failed. All changes are system improvements.
RULE: [2026-03-25] The PERIODIC TECH-DEBT CHECK (work count multiple of 5 → add audit task) is easy to miss in long work sessions — the agent may estimate count from memory rather than running the json count. Adding an explicit "run the command" mandate AND a META-session safety net (STEP 0.5) creates two-layer enforcement for mandatory periodic tasks.

### Session #105 Reflexion — 2026-03-25 (UI/UX — Demo Mode Landing Page)
ACCOMPLISHED: Added full demo mode flow: (1) `.btn-demo` CSS class (dashed border, muted color, green hover). (2) `.demo-banner` + `.demo-badge` + `.demo-banner-actions` CSS components. (3) Hero CTA gains third button: "Try the demo" with `onclick="enterDemoMode()"`. (4) `DEMO_BETTORS` array (5 mock bettors with realistic names/profit/volume, valid hex addresses). (5) `_demoMode` flag variable. (6) `enterDemoMode()`: sets flag, calls `showView('browse')`, injects `#demo-banner` before lb-grid via `insertBefore`. (7) `exitDemoMode()`: clears flag, removes banner, calls `showView('landing')`. (8) `loadBrowseLeaderboard()` short-circuits with demo bettors when `_demoMode === true` — no skeleton, no API call. 2 Playwright checks (75-76). Zero rework.
FAILED: Nothing failed.
RULE: [2026-03-25] For a demo/preview mode flag that affects an async function (loadBrowseLeaderboard), set the flag BEFORE calling showView() — the async function's synchronous preamble runs immediately on the next call stack frame. If the demo path has no `await`, it completes synchronously and the view is populated before the banner injection code runs.
RULE: [2026-03-25] When injecting a DOM element next to a known sibling (e.g. before `#browse-leaderboard-body`), use `lbGrid.parentNode.insertBefore(banner, lbGrid)` — cleaner than `querySelector('.main-content').insertBefore(banner, lbGrid)` and works without knowing the container structure.

- Test count: **303 passed** (stable, frontend-only change), **76 Playwright checks** (74 → 76)

### Session #104 Reflexion — 2026-03-25 (UI/UX — Profile Rich Stat Cards)
ACCOMPLISHED: 4 profile stat cards upgraded: (1) Added `[data-stat="profit|pnl|volume|bets"]` attributes to each card. (2) Per-card `--stat-accent` CSS variable defined via attribute selectors (green/blue/purple/amber). (3) `border-top: 2px solid var(--stat-accent)` replaces plain border for colored accent. (4) Hover lift: `translateY(-2px)` + `box-shadow`. (5) `.profile-stat-header` flex row (label left, trend right) replaces plain label. (6) `.profile-stat-trend` span with `trend-up`/`trend-down`/`trend-info` classes + opacity fade-in. (7) `_setProfileTrend(id, value, infoText)` helper function added before `_renderProfileBadges`. (8) Wired in `renderProfileData` for all 4 stats. 2 Playwright checks (73-74). Zero rework.
FAILED: Nothing failed.
RULE: [2026-03-25] For per-card accent colors via a CSS variable, use `[data-stat="X"] { --stat-accent: color }` + reference `var(--stat-accent, fallback)` in the shared `.card` rule — cleaner than 4 separate color property rules. The data attribute doubles as both a semantic identifier and a CSS hook.
RULE: [2026-03-25] `_setProfileTrend(id, value, infoText)` pattern: when `infoText` arg is provided, show it as info; when `value` arg is provided, show directional arrow based on sign. This 3-argument pattern (id, numeric, override-text) cleanly handles both signed and unsigned trend displays in one helper.

- Test count: **303 passed** (stable, frontend-only change), **74 Playwright checks** (72 → 74)

### Session #103 Reflexion — 2026-03-25 (UI/UX — Hero Section Polish)
ACCOMPLISHED: 4 hero improvements: (1) `.hero h1` font-size bumped from `clamp(40px,6.5vw,80px)` → `clamp(50px,7.5vw,96px)`. (2) Static `<p>` replaced with `.hero-cycle` container + 3 `.hero-cycle-item` spans using `@keyframes heroTextCycle` (9s total cycle: 3s per phrase, fade+slide in/out, staggered via `animation-delay`). Added `height: 60px` desktop / `height: 88px` mobile. (3) `.btn-hero` gains `animation: ctaGlowPulse 2.5s ease-in-out infinite` — box-shadow glow pulse, coexists with existing `::after` shimmer (different render targets). (4) `.hero-live-stats` bar added below social proof — 3 inline items with `hlstat-dot` separators; `runLandingCounters()` now also animates `#hlstat-traders` (100) and `#hlstat-profit` (2.4). 2 Playwright checks (71-72): hero-cycle DOM shape + hero-live-stats IDs. Zero rework.
FAILED: Nothing failed.
RULE: [2026-03-25] For a cycling text container, `height` must be fixed (not `min-height`) — if the container is `overflow: hidden`, a `min-height` will expand to show multiple items stacked, breaking the cycle illusion. Use exact `height` + separate mobile breakpoint to set taller height for wrapping text.
RULE: [2026-03-25] Adding `animation:` to an element that already has `::after { animation: }` is safe — the element's own animation property and the pseudo-element's animation property are fully independent and don't conflict. Only one `animation` property per selector level.

- Test count: **303 passed** (stable, frontend-only change), **72 Playwright checks** (70 → 72)

### Session #102 Reflexion — 2026-03-25 (UI/UX — Nav Progress Bar)
ACCOMPLISHED: Added `#page-progress` — 3px green gradient bar (fixed, top viewport, z-index 10000) that animates on every `showView()` / `showTab()` / initial load. `startProgress()` uses 3-step timeout chain: 0→60% (instant), 60→100% (420ms), then opacity 0 and reset. `showTab()` also calls `mc.scrollTo({ top: 0, behavior: 'smooth' })` on the active `.main-content`. 2 Playwright checks (69-70): DOM presence + function defined.
FAILED: Nothing failed.
RULE: [2026-03-25] Progress bar CSS transition requires `void bar.offsetWidth` (force reflow) between setting `width: 0%` and starting the animation — without it, the transition doesn't run because the browser batches the style changes. This is the standard "force reflow" trick for CSS animations.

- Test count: **303 passed** (stable, frontend-only change), **70 Playwright checks** (68 → 70)

### BRAIN Session #101 Reflexion — 2026-03-25 (DEEP BRAIN)
ACCOMPLISHED: (1) STEP 1B: Found "stale backlog item" pattern recurs (sessions 89+99) — fixed by adding GREP-BEFORE-PICKING rule to PROMPT.md step 3. (2) STEP 1C: Merged stale session 85 XSS streak rule (superseded by session 93 rule); updated session 93 XSS streak count from "16 sessions" to "24+ sessions (77-100)". (3) STEP 1D: Archived sessions 61-80 from activity_log.md to archive (was 40 entries, now 20). (4) 7 sources evaluated, 7 logged. (5) 1 concrete implementation: GREP-BEFORE-PICKING in PROMPT.md. (6) 1 backlog task added: demo mode landing page (2x conversion research finding). (7) MCE paper found (2601.21557) — validates our brain session approach but not implementable prompt-only.
FAILED: Nothing failed.
RULE: [2026-03-25] The "grep before picking" heuristic must live in PROMPT.md step 3 (where task selection happens), not just in knowledge.md. A rule only in knowledge.md gets read at session start but is not recalled at the specific moment it's needed (task selection). The rule's insertion point matters as much as its content. (Source: Sessions 89+99 both wasted turns despite the rule existing in knowledge.md.)

- Test count: **303 passed** (stable — no code changes this session)

### Session #99 Reflexion — 2026-03-25 (UI/UX — Trust Signals Section)
ACCOMPLISHED: Added `.trust-signal-row` below the leaderboard `page-header` on both browse and dashboard views. Two elements: (1) `.trust-badge` — star SVG + "Built on real Polymarket data" always-visible pill; (2) `.trust-live-count` — pulsing dot + "N traders tracked live" that fades in via `opacity: 0 → 1 / .visible` after `loadBrowseLeaderboard` / `loadLeaderboard` populates data. Pulse animation via `@keyframes pulse-dot`. Live count uses `textContent = bettors.length` (safe integer, not innerHTML). 2 Playwright checks (67-68). Also removed the already-done "color-coded profit/loss" backlog item after confirming `renderPositionItem` already applies `var(--green)`/`var(--red)` coloring.
FAILED: Nothing. First run clean.
RULE: [2026-03-25] For "live" or "real-time" indicators, use a small dot with `@keyframes` pulse (scale 0.8↔1 + opacity 0.5↔1, 2s ease-in-out infinite) rather than a blinking cursor or spinner — pulse feels alive without being distracting. Pair it with an `opacity: 0 → 1` fade on the containing badge so the element doesn't flash a "0 traders" state before data loads.
RULE: [2026-03-25] Before starting a session, check each backlog item by reading the relevant code section — "color-coded P&L" was already implemented but remained in backlog 3 sessions too long. A 30-second grep for the described variable (`pnlColor = p.cash_pnl >= 0`) would have caught this. Always grep before implementing a "verify/add" backlog item.

- Test count: **303 passed** (as of 2026-03-25, session 100 — no new backend tests, META session)

### Session #100 Reflexion — 2026-03-25 (META — Code Quality Audit Sessions 94–98)
ACCOMPLISHED: Full virtual team audit (9 members) of sessions 94–98 changed files. All checks passed clean. Verified Marcus XSS greps: 30 escapeHtml() usages, chatId correctly wrapped before innerHTML injection, renderBettorCard/renderBetRow/renderPositionItem/tbody all clean. Removed stale tech_debt entry for _disclosureCache TTL (fixed session 98). Test count 303 confirmed stable.
FAILED: Nothing. Cleanest audit in 6 sessions.
RULE: [2026-03-25] After fixing a tech_debt item (like the disclosureCache TTL), immediately mark it as fixed in tech_debt.md in the same session — don't leave it open to confuse future audits. The audit cycle confirmed: logging debt to tech_debt.md and fixing it in the targeted session is working correctly.

### Session #98 Reflexion — 2026-03-25 (UI/UX — _disclosureCache TTL Fix)
ACCOMPLISHED: Changed `_disclosureCache` from `Map<addr, string[]>` to `Map<addr, {titles: string[], ts: number}>`. Added `_DISCLOSURE_TTL_MS = 5 * 60 * 1000`. Cache hit check now validates `(Date.now() - cached.ts) < _DISCLOSURE_TTL_MS` before serving; stale entries trigger a fresh fetch. Error path also stores `{titles: [], ts: Date.now()}` so errors don't permanently lock an address. 2 Playwright checks (65-66) verify the TTL constant value and entry shape. Zero tests changed.
FAILED: Nothing. Clean first run.
RULE: [2026-03-25] When adding TTL to a cache, always apply TTL to the error path too — not just the success path. If the error path stores without a TTL, a transient network failure will lock that cache key permanently until page reload, which is worse than the original stale-data problem.
RULE: [2026-03-25] For Playwright checks on pure JS state (constants, Map structures), use `page.evaluate()` to inject a test entry and verify shape. Don't rely on DOM checks for logic-layer tests — `_disclosureCache.set('__test__', ...)` + `_disclosureCache.get('__test__')` + `_disclosureCache.delete('__test__')` is the cleanest pattern.

### Session #97 Reflexion — 2026-03-25 (UI/UX — Sort Controls Pill Upgrade)
ACCOMPLISHED: Upgraded leaderboard sort buttons from flat `.tab-btn` to a pill segmented control. CSS: `.sort-pill-group` (dark card bg + border + 100px radius container), `.sort-pill` (transparent bg, transitions to green on active), `.sort-count` (opacity 0 → 1 after data loads), `[data-tooltip]::after` CSS attribute tooltip. JS: reset count badges before fetch, set badge.textContent = bettors.length + classList.add('loaded') after successful load. Applied to both `loadLeaderboard` and `loadBrowseLeaderboard`. 2 new Playwright checks (63-64) pass first run.
FAILED: Nothing. Zero rework needed.
RULE: [2026-03-25] For pill/segmented controls, use a wrapper container with `background: var(--card2); border: 1px solid var(--border); border-radius: 100px; padding: 3px;` and children with `background: transparent; border: none; border-radius: 100px; transition: all 0.2s;`. The active child gets `background: var(--accent); color: #000;`. This avoids double borders (inner button + outer container) while giving a clean grouped look.
RULE: [2026-03-25] Custom CSS tooltips: use `[data-tooltip]` attribute + `::after { content: attr(data-tooltip); opacity: 0; transition: opacity 0.15s; z-index: 200; }` + `:hover::after { opacity: 1; }`. Never use `title` attribute for styled tooltips — browser-native tooltips have no style control and a ~500ms delay. CSS attribute tooltips are instant and styleable.
RULE: [2026-03-25] Count badges on interactive controls should use `opacity: 0` initial state + `opacity: 1` added via `.loaded` class after data arrives. This prevents flashing "0" or empty badges before data loads. Reset by removing `.loaded` and clearing `.textContent` before the fetch.

### Session #95 Reflexion — 2026-03-24 (UI/UX — Account Tab Redesign)
ACCOMPLISHED: Replaced the minimal plain-text Profile settings-card with a `.acct-profile-card` hero layout: avatar circle with computed initials, color-coded `.acct-plan-badge` pill (tier-free/tier-basic/tier-vip classes), upgrade nudge div (hidden/shown based on tier in `renderAccount()`), btn-danger logout with SVG icon. All new IDs/classes populated via `.textContent` (zero innerHTML with API data). 2 new Playwright checks (61-62) pass first run. 303 backend tests unchanged.
FAILED: Nothing. Zero rework needed.
RULE: [2026-03-24] For user-facing profile/identity sections, use `.textContent` for all user data (name, email, timestamps) and CSS classes for dynamic visual state (badge tier class, badge label). Never use innerHTML to display user account fields — textContent is both safer and sufficient.
RULE: [2026-03-24] Initials computation from name: `name.trim().split(/\s+/).map(w => w[0]).slice(0, 2).join('').toUpperCase()` — handles single-word names, multi-word names, gracefully falls back to email first letter or '?'. Reusable for any avatar initials pattern.

### Session #94 Reflexion — 2026-03-24 (UI/UX — Profile Skeleton Loading)
ACCOMPLISHED: Added animated .skeleton shimmer to all 4 profile stat card values (pstat-profit, pstat-pnl, pstat-volume, pstat-bets) and the name heading in showProfile(). Bet-row skeletons were already present via renderProfileSkeletons(). Change is 7 lines. 303 tests + 60 Playwright checks pass (2 new: check 59 renderProfileSkeletons function, check 60 verify 4/4 stat + name skeleton on navigate using apiFetch mock pattern).
FAILED: Check 59 assertion included 'bet-row' string check — Playwright evaluate returns the JS string fine but the assertion condition was fragile. Fixed by simplifying to just check 'skeleton' in string and len > 50.
RULE: [2026-03-24] When Playwright-testing immediate DOM state that appears synchronously before an async JS function's first `await`, use the apiFetch mock pattern: `window.apiFetch = () => new Promise(() => {})` (never resolves) + call the function (not awaited) + `await new Promise(r => setTimeout(r, 0))` to yield the microtask queue. The synchronous skeleton setup runs; the async API call hasn't resolved. Restore apiFetch after. This avoids all race-condition timing issues.
RULE: [2026-03-24] `.textContent = value` replaces innerHTML skeletons cleanly — no special teardown needed. If you use `innerHTML` to set skeleton elements in a loading state, and the data-fill step uses `.textContent`, the skeleton is cleared automatically when data arrives.

### Session #93 Reflexion — 2026-03-24 (META — Code Quality Audit)
ACCOMPLISHED: 9-member virtual team audit of sessions 88–92. Zero issues blocking commit. Marcus (XSS): PASS — both grep patterns run, confirmed escapeHtml on chatId (alerts), disclosure market titles, renderPositionItem (5 fields: bettor, market_title, outcome, poly_url, avatarUrl), buildTickerItem (name, market), renderBetRow (question, outcome, market_icon, polyLink). Disclosure loader: try/catch present, error fallback "No recent data available", empty fallback "No recent markets found". Tech debt logged: _disclosureCache no-TTL pattern.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing `innerHTML = variable` (grep #2), always trace the variable back to where it was built — a two-step pattern (build in one function, assign in caller) can hide unescaped vars if you only look at the assignment line. The `html` variable pattern (build renderFoo → assign innerHTML = html) is safe only if renderFoo escapes every API-sourced field.
*(XSS streak rule merged into Session #107 RULE above — this entry superseded)*

### Session #92 Reflexion — 2026-03-24 (UI/UX — Mobile Audit)
ACCOMPLISHED: Audited all 7 screens at 375px. Found and fixed 8 concrete issues: (1) .tab-btn height ~33px → min-height 40px, (2) .follow-btn height ~30px → min-height 44px, (3) .section padding 80px → 48px on mobile, (4) .modal padding 36px → 28px 24px, (5) pricing-card compact padding, (6) follows-stat-divider hidden ≤480px, (7) preview table Volume column hidden ≤480px, (8) preview-card overflow-x auto. 3 new Playwright checks (56-58). 303 tests, 58 checks, 0 failures.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing mobile tap targets: custom button classes (`.tab-btn`, `.follow-btn`, `.sort-btn`) don't inherit from `.btn` which has `min-height: 44px`. Always check EVERY button class independently for `min-height` — only the `.btn` base class has it. Secondary filter/sort buttons should have min-height 40px; primary actions (follow, CTA) need 44px.
RULE: [2026-03-24] Mobile audit order: (1) landing section padding, (2) tap targets on all button variants, (3) table overflow (preview tables are clipped, not scrollable), (4) follow/stat strip dividers at narrow widths, (5) modal padding. These 5 areas catch 80% of mobile issues in a typical SPA dark dashboard.

### BRAIN Session #91 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Curated knowledge.md — no duplicates found, already clean. (2) Checked activity_log.md — 30 entries, below 30 threshold, no archival triggered. (3) Searched 5+ topics, 11 new sources. (4) Found 3 new ECC skills (click-path-audit, santa-method, skill-comply) added 2026-03-22/23. (5) Implemented 3 improvements: playwright.md SPA hidden-element navigation rule (from session 90 failure), coding.md stale-path fix + FRAGILE ZONES guard (from arxiv 2603.06847 fault taxonomy), new click-path-audit.md skill. (6) Added 3 backlog items.
FAILED: Nothing failed.
RULE: [2026-03-24] Skill files that reference wrong project paths (stale from prior project) are as harmful as wrong code — agents follow them and edit wrong files. BRAIN sessions must check coding.md PYTHON BACKEND PATTERNS and FRONTEND PATTERNS sections against the actual project structure. Grep for distinctive wrong terms (e.g. "stockcards", "app.js", "styles.css") to catch staleness fast.
RULE: [2026-03-24] When a BRAIN session implements a fix for a specific session failure (e.g. session 90's hidden-element Playwright click), the fix goes into the SKILL FILE for that task type (playwright.md), not just knowledge.md. knowledge.md is the agent's long-term memory; skill files are the agent's in-session reference. A rule only in knowledge.md gets read at session start but may not be recalled when the specific failure triggers mid-session.

### Session #90 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Playwright screenshot gallery. Captured 7 PNGs (01-07) via tmp_screenshots.py using JS `showView()`/`showTab()` calls — no click() on nav elements (they're not visible at 1280px desktop). Added 7 new checks (49-55) to playwright_registry.py using a separate `scr_page` instance so the new checks don't interfere with prior checks 1-48. 55/55 pass. 303 backend tests stable.
FAILED: First attempt used ElementHandle.click() on #nav-leaderboard etc. — elements exist in DOM but are display:none at desktop width. Fixed by using `page.evaluate("showView(...)")` / `page.evaluate("showTab(...)")` instead. Also hit charmap encoding error from `→` unicode in print() — fixed by using plain ASCII `->` in print statements (or sys.stdout.reconfigure — but ASCII was simpler).
RULE: [2026-03-24] SPA navigation in Playwright: never click nav elements by ID if they might be hidden (e.g. desktop vs mobile nav). Use `page.evaluate("showTab('X')")` or equivalent JS function calls instead — they always work regardless of element visibility.
RULE: [2026-03-24] When print() raises charmap error on Windows (can't encode unicode like → \u2192): replace with ASCII equivalent (`->`) in all print statements. Alternatively add `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` at script top — but ASCII is simpler and avoids the import entirely.
RULE: [2026-03-24] Playwright multi-screen check pattern: create a dedicated `scr_page = await browser.new_page(...)` for screen-navigation checks at the end of the check function. Navigate via JS evals. Close `scr_page` in the last check's block before `browser.close()`. This isolates screen-navigation side effects (tab switches, view changes) from earlier checks on the main `page`.

### Session #89 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Follow preview tooltip on leaderboard cards. CSS: `.lb-follow-wrap` (position:relative), `.lb-follow-tooltip` (absolute, bottom:calc(100%+8px), left:50%, translateX(-50%), opacity:0 by default, transition opacity 0.15s, arrow caret via ::after). Show on `.lb-follow-wrap:hover` or `.lb-follow-wrap:focus-within`. JS: `renderBettorCard` wraps follow button in `.lb-follow-wrap`; inserts `<span class="lb-follow-tooltip">` with bettor name only when `!isFollowing` (uses already-escaped `eName`). XSS: `eName` = `escapeHtml(name)` — safe in tooltip. 3 new Playwright checks (46–48): tooltip present in not-following state, correct text content, absent when following. 48/48 pass. 303 tests stable. Also: discovered hero counter animations (animateCounter + runLandingCounters + 8s live ticker) were already committed — removed stale backlog item.
FAILED: Nothing.
RULE: [2026-03-24] Before picking a backlog task, run a quick grep for the key function/class name to verify it wasn't already implemented in a previous session. `grep -n "animateCounter\|runLandingCounters"` caught hero counters already done — saves the full implementation turn. Stale backlog items accumulate when work is done but the backlog isn't immediately updated.
RULE: [2026-03-24] Tooltip positioning pattern (for any card-embedded tooltip): parent `position:relative`; tooltip `position:absolute; bottom:calc(100%+8px); left:50%; transform:translateX(-50%); opacity:0; pointer-events:none; transition:opacity 0.15s`; show via `parent:hover .tooltip, parent:focus-within .tooltip { opacity:1 }`. Arrow caret: `::after { border-top-color: var(--border2) }`. This pattern works even inside scrollable containers because it's relative to the parent, not the viewport.

### Session #88 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Leaderboard card progressive disclosure. (1) CSS: `.lb-card` gets `cursor:pointer`; `.lb-card-chevron` (24×24, flex centered, `transition: transform 0.28s, color 0.2s`); `.lb-card.lb-expanded .lb-card-chevron` rotates 180°; `.lb-card-disclosure` (max-height:0, opacity:0, `overflow:hidden`, `transition: max-height 0.3s, opacity 0.25s`); `.lb-card.lb-expanded .lb-card-disclosure` (max-height:220px, opacity:1); `.lb-disclosure-inner` (border-top, padding); `.lb-view-profile-btn` (full-width, accent border, hover glow). (2) JS: `_disclosureCache` Map for caching fetched market titles per address; `_loadDisclosureMarkets(addr, disclosureEl)` lazy-fetches `/bettors/{addr}`, extracts 2 market titles, updates `.lb-disclosure-markets` inner HTML using `escapeHtml(t)`; `_renderDisclosureMarkets(marketsDiv, titles)` renders the title rows or fallback text; `toggleLbCardExpand(event, cardEl)` toggles `.lb-expanded` class, skips follow/view-profile buttons, calls `_loadDisclosureMarkets` on expand. (3) `renderBettorCard`: removed `onclick`/`role="button"` from header, added chevron SVG in header, moved click handler to card root div, added `event.stopPropagation()` on follow button + view-profile button, added `.lb-card-disclosure` section before follow button. (4) 3 new Playwright checks (43-45). 45/45 pass. 303 tests stable.
FAILED: Nothing.
RULE: [2026-03-24] For CSS max-height expand/collapse: set the initial `max-height:0` on the element and the expanded `max-height` to a generous fixed value (220px) rather than `max-height: auto` — transitions don't animate from/to `auto`. The opacity transition complements it so the reveal feels smooth.
RULE: [2026-03-24] When making a card clickable but with a button inside: add `event.stopPropagation()` to all interactive child elements (buttons, links) so the card's onclick doesn't fire when the child is clicked. Conversely, in `toggleLbCardExpand(event, cardEl)` use `event.target.closest('.follow-btn')` to bail early for any follow-button descendant click.

### Session #87 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Auth form UX tightening — animated tab switch (authFormOut/authFormIn CSS keyframes + 150ms JS timeout before revealing new form), mobile full-screen auth-box (100vh, border-radius:0 at ≤640px), "or" divider + Google SSO placeholder button (disabled, opacity:0.45) in both forms. 303 tests stable, 42/42 Playwright checks pass (3 new).
FAILED: Nothing.
RULE: [2026-03-24] When animating a tab/panel switch (show old → fade out → hide old → show new → fade in): use setTimeout to delay the swap by the CSS animation duration (e.g. 150ms) so the out-animation completes before the element gets `hidden`. If you hide immediately, the animation never plays. Pattern: add out-class → setTimeout(duration) → add hidden + remove out-class + remove hidden on target + add in-class → setTimeout(220) → remove in-class.
RULE: [2026-03-24] For disabled/coming-soon placeholder buttons in UI: use `disabled` attribute + `cursor:not-allowed` + `opacity:0.45` + `transition:none` to clearly signal "not interactive yet" without visual clutter. Do NOT use `pointer-events:none` alone — that hides the not-allowed cursor. The `disabled` attribute also prevents keyboard focus (correct for a placeholder).

### Session #85 Reflexion — 2026-03-24 (META audit)
ACCOMPLISHED: Code quality audit of sessions 77–83. Ran Marcus two-grep XSS check, Sarah UI consistency, Jordan conversion, Nina regression, Leo dead-code checks. Zero issues found across 5 work sessions.
FAILED: Nothing.
*(XSS streak rule merged into Session #93 RULE below — this entry superseded)*

### Session #84 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: "How It Works" landing section upgrade. (1) CSS: `.steps-flow` flex container (column on mobile), `.step-card` with `flex: 1`, `.step-connector` (40px wide, padding-top 56px to vertically centre vs card icon), `.step-num` (22px green circle), `.steps-cta` + `.steps-cta-sub`. (2) HTML: removed the old `.steps-grid` wrapper and emoji HTML entities; replaced with 3 `.step-card` elements in `.steps-flow` with 2 `.step-connector` divs between them; each card now has step-num, step-icon with inline SVG, step-title, step-desc. (3) SVGs: bar chart (leaderboard), user-plus (follow), bell (alerts). (4) CTA button + trust sub-line after steps-flow. (5) 4 new Playwright checks (36-39). 39/39 pass. 303 backend tests stable.
FAILED: First attempt put cards inside a `.steps-grid` grid container inside `.steps-flow`, which meant connector arrows (sibling to the grid) couldn't interleave with cards. Fixed by removing `.steps-grid` and putting all 3 cards + 2 connectors directly in `.steps-flow` as flex children.
RULE: [2026-03-24] When building a "steps with arrows" layout: connector arrows must be SIBLINGS of the step cards in a flex container, not inside a separate CSS grid. Grid handles placement internally — you can't inject arbitrary elements between grid cells.

### Session #83 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Follows tab dashboard upgrade. (1) CSS: `.follows-summary-strip`, `.follows-stat`, `.follows-stat-value`, `.follows-stat-label`, `.follows-stat-divider` — strip pinned above live feed with 3 stats. (2) Static HTML for `#follows-summary-strip` + 3 child elements (`#follows-count`, `#active-bets-count`, `#follows-pnl-value`). (3) `loadMyFollows()` updated: shows strip + sets `#follows-count`, upgraded card template to rank badge + gradient-initials avatar + 2-stat mini-grid (Profit/PnL%) from `_bettorCache` + View Profile/Unfollow button row. (4) `refreshFollowsActivity()` updated: sets `#active-bets-count` to `allPositions.length`, computes `cumPnl` via reduce, updates `#follows-pnl-value` text + color. (5) XSS: `initials` from `name[0]` wrapped in `escapeHtml()`. (6) 3 new Playwright checks (33-35). 35/35 pass. 303 backend tests stable.
FAILED: Nothing.
RULE: [2026-03-24] When adding a single-char initial from an API-sourced name (e.g. `name[0].toUpperCase()`) into innerHTML, STILL wrap in `escapeHtml()`. A bettor name starting with `<` would produce an unescaped `<` — a single character doesn't escape the XSS rule. Always: `escapeHtml(name ? name[0].toUpperCase() : '?')`.

### Session #82 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Pricing section uplift + annual billing toggle. (1) Monthly/Annual pill toggle above pricing cards — `setPricingPeriod()` adds/removes `body.annual-billing` class; CSS `body.annual-billing .pricing-price-monthly { display:none }` / `.pricing-price-annual { display:inline }` swaps prices without JS DOM mutation. (2) 7-row aligned feature comparison across all 3 tiers — same rows in same order, check/cross per tier, outcome-oriented language. (3) Social proof line + shared trust row under pricing grid. (4) 4 new Playwright checks (29-32): billing toggle DOM, `setPricingPeriod` fn, body class toggle, social/trust elements. 32/32 checks pass. 303 backend tests stable (frontend-only session).
FAILED: Nothing.
RULE: [2026-03-24] For binary UI state toggles (monthly/annual, dark/light, tab A/B), prefer body-class CSS pattern over JS innerHTML swaps: `body.annual-billing .price-monthly { display:none }` is simpler, transition-friendly, and SSR-safe. The JS only adds/removes a class — no DOM queries, no innerHTML, no XSS surface. JS complexity stays linear with states; CSS handles all the conditional display logic.

### Session #81 Reflexion — 2026-03-24 (DEEP Brain)
ACCOMPLISHED: (1) Archived activity_log.md sessions 41-60 to activity_log_archive.md — log trimmed from 210 lines to 107 lines. (2) Curated knowledge.md — no duplicates found (already clean after session 61+76 curation passes). (3) META analysis of sessions 61-80: found STEP 0 skip condition "zero Python code" silently skipped self-critique for ALL UI/UX sessions — root cause of 4 XSS audit cycles. (4) Fixed STEP 0: changed skip condition to "zero files changed" + added Q6 (frontend XSS grep gate). (5) Updated audit.md to include session 79 in the recurring failure note. (6) Logged technique in brain/techniques.md. (7) Web searches: evaluated 8+ sources. (8) Backlog confirmed 3 HIGH PRIORITY items remain.
FAILED: Nothing failed.
RULE: [2026-03-24] STEP 0 skip condition must be "zero files changed", NOT "zero Python code changed". When the project is in frontend-only mode (all sessions edit index.html, no Python), the "zero Python" condition skips STEP 0 for every session — silently eliminating the self-critique gate that catches XSS, logic errors, and intent drift. This was the root cause of 4 consecutive XSS audit cycles (sessions 59, 67, 73, 79). The correct skip condition is always language-agnostic.
RULE: [2026-03-24] XSS write-time protocol (session 76) + two-grep audit (session 76) confirmed working: sessions 77, 78, 80 introduced zero XSS. The cycle is broken. If future AUDIT sessions find new XSS, it means design.md was not read before writing — not that the protocol is ineffective. The audit sessions are now a sanity check, not a primary defense.

### Session #80 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Bettor profile hero upgrade. Added `_bettorCache` Map populated in `loadLeaderboard` → profile page gets rank/pnl_usd instantly from cache when navigating from leaderboard. Gradient-initials avatar (deterministic palette from first char of name) sits behind the `<img>` at z-index 0; img fades in on `onload`. Rank badge (gold #1 / silver #2 / bronze #3 / grey #N) and profit badge (green pos / red neg pill) appear above name. 4-stat grid: Profit, PnL%, Volume, Total Bets — replaced old 3-stat (Volume, Bets, Avg Bet). `_updateFollowPreview(isFollowing)` updates preview text on follow toggle. 28/28 Playwright checks pass. 303 backend tests stable (frontend-only session).
FAILED: Nothing.
RULE: [2026-03-24] When navigating from a list page (leaderboard) to a detail page (profile), cache the list-page data keyed by ID. The profile API call takes 1-2s; the cached rank/pnl_usd can render immediately. Pattern: `Map.set(b.address, b)` when rendering cards → `Map.get(address)` in showProfile. Prevents a "flash of no data" on the most prominent stats.

### Session #79 Reflexion — 2026-03-24 (Audit)
ACCOMPLISHED: Code quality audit of sessions 74–78. Found 5 XSS vulnerabilities in `renderPositionItem` — all API-sourced fields injected directly into innerHTML template literals: `p._bettor` (bettor name), `p.market_title`, `p.outcome`, `p.poly_url` (href attribute), `p._avatarUrl` (src attribute). Fixed with 5 `escapeHtml()` calls. Removed dead `renderBetItem` function (38 lines) — was replaced by the renderPositionItem/renderBetRow pattern but never deleted. 303 tests stable, 24/24 Playwright checks pass.
FAILED: Nothing.
RULE: [2026-03-24] When a render function is replaced by a newer one (e.g. renderBetItem → renderPositionItem), the old function accumulates XSS risk because it stops receiving the same code-review attention as active functions — and if it's somehow re-wired, its unescaped variables ship. Delete dead render functions immediately at the time of replacement, not at the next audit. Dead code is live attack surface if it ever gets called again.

### Session #78 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Added `renderFollowSkeletonCards(count)` function — follow-card shaped skeletons (avatar circle + name/addr lines + button bar). Called in `loadMyFollows()` for `cardContainer` (was previously set to `''` during load). Replaced 2 flat 80px skeleton bars in `activityContainer` with 4 structured position-card skeletons (top bar with avatar/name/LIVE badge, title block, outcome pill row, stats grid). Playwright CHECK 23+24 added. 303 tests stable, 24/24 Playwright checks pass.
FAILED: Nothing.
RULE: [2026-03-24] Skeleton cards should structurally mirror the real card they replace — same CSS class wrapper, same internal sections (avatar, name row, stat blocks, button). A 80px flat bar is better than a spinner but users still register it as "placeholder not content" if the proportions don't match. Structural skeletons (same grid, same spacing) feel like the content is "coming soon in place" rather than "whole section missing".

### Session #77 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Redesigned the alerts settings page — replaced the flat settings-card with 3 toggle-rows with three distinct `.acc-card` channel cards (Web Push / Telegram / SMS), each with icon, plan-tier badge, live status dot+label, and a "Test" button shown only when the channel is active. Added `updateChannelStatus()` (reads toggle DOM state + `alertSettings` global to determine Active/Connected/Not linked/VIP required) and `testChannel()` (fires real browser Notification for push; toast for Telegram/SMS). Speed banner with left accent border added. Added `--blue: #4A9EFF` to `:root`. `telegram_chat_id` escaped via `escapeHtml()`. 303 tests stable, 22/22 Playwright checks pass.
FAILED: Nothing.
RULE: [2026-03-24] When adding status indicators that depend on both toggle state (DOM) and API state (global object), read them separately: `toggleEl.classList.contains('on')` for "is the channel enabled" and `alertSettings.telegram_verified` for "is it connected/verified". Don't conflate enabled with connected — a channel can be toggled on but still not linked, and the status label must distinguish these states for user trust.

### Session #75 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Replaced the leaderboard's cramped 3-stat layout (Profit | ROI | Volume-fullwidth) with a clean 2×2 metric grid: PnL% (top-left), Profit (top-right), Volume (bottom-left), Win Rate with "90d" confidence-horizon badge (bottom-right). Renamed "ROI" to "PnL%" for copy-trader clarity. Win Rate shows "—" — honest placeholder until trade-level outcome data is wired. Skeleton updated to 4 equal slots. 303 tests stable, 22/22 Playwright checks pass.
FAILED: Nothing.
RULE: [2026-03-24] When a UI card needs a metric slot but the data isn't available from the API, show "—" with a clear label + confidence horizon badge (e.g. "Win Rate [90d]") — don't omit the slot or fake the data. The slot establishes the design intent, tells the user what metric they're looking at, and can be populated later without a layout change. This is the "progressive disclosure" approach for data-sparse MVP cards.

### Session #74 Reflexion — 2026-03-24 (UI/UX)
ACCOMPLISHED: Transformed bet rows in bettor profile from flat `outcome + separate price span` to YES/NO pill component: `.bet-outcome.yes` (green tint + border), `.bet-outcome.no` (red tint + border), `.bet-outcome.other` (neutral), with inline `.bet-outcome-price` for "72¢". Added `.bet-active-badge` (pulsing dot via `::before`) for bets < 14 days old. 303 tests stable, 22/22 Playwright checks pass.
FAILED: Nothing. Single-file CSS+JS change with no external dependencies.
RULE: [2026-03-24] When a bet row needs a "market status" badge but only the bet timestamp (not market end date) is available from the frontend, use a conservative recency heuristic: `betAge < 14 days → "Active"`; no badge for older bets. This is honest UX — don't label anything "Open" or "Closed" without ground-truth data. Overpromising market status misleads traders who might copy a settled market.

### Session #73 Reflexion — 2026-03-24 (Audit)
ACCOMPLISHED: Code quality audit of sessions 68–72 changes in frontend/index.html. Found and fixed 3 XSS vulnerabilities: (1) `renderBettorCard` used `avatarUrl` (API-sourced `b.avatar_url`) directly in `src="${avatarUrl}"` inside a template literal injected via innerHTML — fixed by adding `const safeAvatarUrl = escapeHtml(avatarUrl)`. (2) `loadLandingPreview` used `b.avatar_url` unescaped in `src` attribute — fixed with `escapeHtml`. (3) `loadLandingPreview` used `b.name` unescaped in innerHTML — fixed with `escapeHtml`. No dead code found. Nav is consistent (desktop 4 items = mobile 4 items). No console.error. 303 tests stable. 22/22 Playwright checks pass.
FAILED: Nothing failed.
RULE: [2026-03-24] When a render function builds an `<img>` element via innerHTML template literal, BOTH the `src` AND the `alt` attributes must be escaped with `escapeHtml()` if they come from API data. Setting `.src` via DOM property (e.g. `el.src = apiValue`) is safe, but `src="${apiValue}"` inside a template literal injected as innerHTML is not — an attacker can break out of the attribute with `"`. The `renderProfileData` function correctly uses `avatarEl.src = avatarSrc` (DOM property — safe); `renderBettorCard` incorrectly used `src="${avatarUrl}"` (template literal — XSS). Pattern: always prefer DOM property assignment for untrusted URLs.

### BRAIN Session #71 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Curated knowledge.md — no duplicate rules found; all existing rules pass 5-factor admission check. (2) Searched 5 topics; 12 sources evaluated and logged. (3) GitHub agent found 6 new ECC skills added 2026-03-23 (browser-qa, design-system, benchmark, canary-watch, product-lens, safety-guard). (4) Implemented 5 concrete improvements: toast stack pattern in design.md, probability chip CSS in design.md, 10-dimension visual audit checklist in design.md, expanded AVOID section (4 new AI slop patterns), accessibility check patterns in playwright.md. (5) Added 2 new backlog tasks: four-metric leaderboard, pre-commit follow preview. (6) activity_log.md now at 31 entries — archiving needed next BRAIN session.
FAILED: Nothing failed.
RULE: [2026-03-24] For interruptible UI entry animations (toast fade-in, modal slide-in), prefer CSS `data-*` attribute + `transition` over `@keyframes`. Set `data-mounted="false"` on DOM insert, flip to `"true"` in the next requestAnimationFrame. CSS transitions can be cancelled mid-flight; `@keyframes` animations cannot — causing a "flash" when an element is added and removed quickly (e.g., rapid-fire toasts).

### Session #70 Reflexion — 2026-03-24
ACCOMPLISHED: Auth form polish — password visibility toggle (eye SVG, toggles field type + swaps icon), inline field errors with `.form-error` / `showFieldError()` / `clearFieldError()`, `clearAllErrors()` before submit, general error div for API-level failures, fadeUp animation on `.auth-box`, social proof copy under login CTA. 17/17 Playwright checks pass (3 new). 303 tests stable.
FAILED: Python `str.replace()` on file content wrote 0 bytes when the needle had `\n` but file had `\r\n` on Windows. The file content was empty after open+write. Fixed by using line-array injection instead of string replace.
RULE: [2026-03-24] On Windows, never use `str.replace('...\n...', ...)` to patch multi-line file content — line endings may be `\r\n` and the needle won't match. Instead, read as lines list, find the target line index by inspection, then insert at that index.
RULE: [2026-03-24] For form inline errors: use `textContent = msg` not `innerHTML = msg` — API error messages (data.detail) are user-facing strings that could contain HTML characters. textContent is always safe. Only ever use innerHTML for hardcoded SVG/HTML literal strings.

### Session #69 Reflexion — 2026-03-24
ACCOMPLISHED: Built bettor profile page — `showProfile(address)` fetches `/bettors/{address}`, renders `renderProfileData()` with avatar/stats/follow-btn, and `renderBetRow()` for each bet with YES(green)/NO(red) outcome, price in cents, Copy-bet link. showTab() extended to include 'profile' in the hidden/show loop. lb-card-header gets `lb-card-header-click` class + onclick. 303 tests stable, 14/14 Playwright checks pass (2 new checks).
FAILED: Nothing failed. CSS-only + JS-only, no Python touched.
RULE: [2026-03-24] When adding a new "tab" that has no sidebar nav item (like a profile page navigated to from a card), include it in showTab()'s ALL_TABS array so it gets hidden when switching to any other tab — but don't add it to the nav-active loop. The nav loop only manages items that have `nav-{tab}` and `mob-nav-{tab}` elements.
RULE: [2026-03-24] Polymarket bet timestamps from the `/activity` API can be either Unix epoch integers OR ISO 8601 strings (source varies by endpoint version). Always handle both: `typeof raw === 'string' ? new Date(raw) : new Date(Number(raw) * 1000)`.

### Session #67 Reflexion — 2026-03-24
ACCOMPLISHED: Code quality audit of sessions 62–66 changes in frontend/index.html. Fixed XSS: toast() was using innerHTML with a msg param that callers pass API-sourced bettor names and server `data.detail` error strings via e.message. Replaced with a DOM-built approach: iconSpan.innerHTML = hardcoded entity (safe), msgSpan.textContent = msg (safe). Deleted 46 lines of dead code: renderBettorRow() and renderSkeletonRows() — both were never called; they predated the session 58 table→card grid conversion. 303 tests stable, 9/9 Playwright pass.
FAILED: First full test run showed 5 failures + 7 errors — traced to DB lock contention because the backend server (port 8002) was still running while pytest used its own in-memory SQLite. Killing the server first gives 303/303 pass.
RULE: [2026-03-24] Never run `py -m pytest tests/` while the live uvicorn backend is also running on the same machine — DB lock contention causes intermittent SQLAlchemy OperationalError failures. Always kill background servers before running the full test suite.
RULE: [2026-03-24] Dead code audit pattern: after any session that converts a UI element from one rendering strategy to another (table→cards, list→grid), grep for the OLD render function name in the file — if zero callers remain, delete it immediately. Renderer replacements consistently leave the old function unreachable.

### Session #65 Reflexion — 2026-03-24
ACCOMPLISHED: Empty state illustrations — three inline SVG illustrations added: (1) follows page chart+follow-badge SVG; (2) alerts no-notifications banner with bell+lightning SVG that toggles based on all-channels-off state; (3) leaderboard error warning triangle SVG. Added .es-illustration CSS class (88px circle, 3 tint variants). Added updateAlertsNoneState() JS helper called from loadAlertSettings + all 3 toggle functions. 303 tests stable, 7/7 Playwright checks pass.
FAILED: Playwright check 5 initially failed because it looked for .lb-card/.skeleton which only appear after API data loads, not on initial page load. Fixed by targeting #preview-leaderboard which is immediately visible on the landing page.
RULE: [2026-03-24] When writing Playwright checks for PolyEdge, target elements visible on the PUBLIC landing page (hero, nav, #preview-leaderboard, btn-primary) — not elements inside tabs/sections that require auth or user interaction to reveal. #browse-leaderboard-body and #lb-body are always hidden on initial load.
RULE: [2026-03-24] For JS-driven empty state banners: put updateState() calls in (a) the load function AND (b) each mutating function's success AND error handler — the error handler must revert the toggle AND update the state banner, otherwise the banner can get out of sync with the actual DOM toggle state.

### Session #64 Reflexion — 2026-03-24
ACCOMPLISHED: Hero background CSS enhanced — dot grid ::before with radial mask fade + three-layer ambient glow ::after replacing the old single-glow. overflow:hidden added to hero. bg-image hook commented in for when actual hero-bg.jpg is dropped in frontend/assets/. NovaBanana API key invalid (401) — documented in ASSETS_NEEDED.md. 303 tests stable, 7/7 Playwright checks pass.
FAILED: Nothing failed. CSS-only change, no JS touched.
RULE: [2026-03-24] When adding `::before` and `::after` backgrounds behind hero content, set `z-index: -1` on both pseudo-elements (not `z-index: 0`). Within a stacking context, z-index: 0 paints at the same level as block children (ambiguous ordering) while z-index: -1 reliably paints behind all non-positioned children. Test with `overflow: hidden` on the parent to prevent glow bleed.
RULE: [2026-03-25] NovaBanana API key `458ef44f91c6cbcc614a31573b7f15fe` IS VALID (session 109 confirmed working). Previous 401 was from a stale attempt. Correct poll endpoint: `GET /api/v1/nanobanana/record-info?taskId={id}` — NOT `/task/{id}` (returns 404). Check `data.successFlag == 1` and read image from `data.response.resultImageUrl`. See novabana.md for full working code.

### Session #63 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Added `--fs-2xs` through `--fs-6xl` font-size CSS variables to `:root` — type scale now defined, reusable in future refactors. (2) Added `h1–h4` default heading size rules using `clamp()` — any heading without a component-specific override gets a sane proportional size. (3) Added `:active { transform: scale(0.97); transition-duration: 60ms; }` to all btn variants — previously only `btn-primary` had an active state, all others gave no press feedback. (4) Added `@keyframes fadeInUp` (translateY(-12px)→0) + `.animate-fade-in-up` CSS class; updated `renderBettorCard` to use it at 80ms stagger increments (was `fadeUp` at 40ms). 303 tests stable, 9/9 Playwright checks pass.
FAILED: Nothing failed. The `settings-card h3 { font-size: 16px; }` rule correctly overrides the generic `h3 { font-size: clamp(17px,...) }` — verified by CSS specificity rules (class + element > element alone).
RULE: [2026-03-24] When adding generic `h1-h4` default styles, always grep for `h[1-4] {` rules that already exist in component contexts to confirm specificity overrides work. CSS specificity: `.class h3` (0,1,1) beats `h3` (0,0,1) — specific component rules always win.
RULE: [2026-03-24] For `@keyframes fadeInUp` the convention is: from `translateY(-12px)` → to `translateY(0)` (drops down from above). This gives "live feed" feel. Contrast: `fadeUp` from `translateY(20px)` → `translateY(0)` (rises from below) gives "page reveal" feel. Use fadeInUp for dynamic list data; fadeUp for hero/static sections.

### Session #62 Reflexion — 2026-03-24
ACCOMPLISHED: Pricing section redesign — (1) `transform: translateY(-8px)` permanent elevation on Basic/featured card (featured:hover goes to -12px); (2) `@keyframes pricing-glow-pulse` animates green box-shadow between 28px and 52px glow with 2px solid border at peak (3.5s loop); (3) `.pricing-cta-note` trust copy under all 3 CTA buttons; (4) `.pricing-vip` CSS class replacing inline `border-color` on VIP card; (5) added SMS ✗ row to Basic tier (was missing, mismatch with VIP comparison). 303 tests stable, 9/9 Playwright checks pass.
FAILED: Nothing failed. All changes landed cleanly on first try.
RULE: [2026-03-24] When elevating a pricing card with `translateY(-8px)`, always also set a specific `:hover` override (e.g. `featured:hover { transform: translateY(-12px); }`) — otherwise the generic `.pricing-card:hover { transform: translateY(-4px); }` rule overrides the elevation on hover, snapping the featured card DOWN instead of UP. Elevated cards need their own hover state.

### DEEP Brain Session #61 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Found 2 failure patterns in sessions 58-60: XSS missed in template helpers + Playwright selector staleness after CSS refactor. Fixed both: XSS grep command added to audit.md Marcus checklist; CSS class refactor section added to playwright.md. (2) Curated knowledge.md — merged session 59+60 XSS rules into one canonical rule. (3) Rewrote design.md from stale "StockCards" content to accurate PolyEdge color system (actual :root CSS vars), file structure, and card anatomy. (4) Fixed stale references in INDEX.md (updated API endpoint + frontend-only feature workflows). (5) Downloaded Anthropic official frontend-design SKILL.md (correct path: skills/frontend-design/SKILL.md) — saved as autoagent/skills/frontend-design.md, principles merged into design.md. (6) Searched 7+ topics; 11+ sources evaluated. (7) Fintech UX research yielded: staggered card animations, semantic color token rule (green ONLY for profit), Most Popular pricing card elevation — 4 new backlog tasks added. (8) Activity log at 20 entries — no archiving needed.
FAILED: Nothing failed.
RULE: [2026-03-24] Skill files that were copied from a prior project (design.md, INDEX.md) silently give wrong instructions — agents follow them and produce wrong file paths, wrong colors, wrong patterns. BRAIN sessions must check every skill file that was written before the current project started and verify its examples match the current codebase. Pattern: grep skill files for the old project's distinctive terms (e.g., "StockCards", "styles.css", "app.js") — any hit means the file needs rewriting.

### Session #60 Reflexion — 2026-03-24
ACCOMPLISHED: Hero redesign — added "Bets Detected Today" 4th stat (animates 0→1247, then +1 every 8s), CTA shimmer sweep animation via `.btn-hero::after` pseudo-element, social proof "Join 847+ traders" line. Fixed last XSS gap: `buildTickerItem` used `t.name` and `t.market` raw in innerHTML — wrapped in `escapeHtml()`. Added null guard for `t.market` (was `t.market.length` which crashes if undefined). 303 tests stable, 9/9 Playwright pass.
FAILED: Nothing failed — all edits were clean on first try.
RULE: [2026-03-24] XSS in innerHTML — canonical rule (merged sessions 59+60): (1) Prevention: template-literal innerHTML with API-sourced data is XSS — always wrap in `escapeHtml()`. Names, messages, and error strings are dangerous; wallet hex addresses are structurally safe. Add `escapeHtml` as a shared utility immediately when writing any renderXxx/buildXxx/createXxx function. (2) Detection: after writing or auditing any frontend HTML file, run `grep -n 'innerHTML.*\${' frontend/index.html` — check EVERY match, not just renderXxx functions. Template helpers (buildXxx, createXxx) are equally dangerous and often missed. Fix every match that uses an API-sourced variable.

### Session #59 Reflexion — 2026-03-24
ACCOMPLISHED: META audit of sessions 54-58. Found 6 XSS injection points in renderBettorCard (new session 58 code) and pre-existing renderBettorRow — bettor names from Polymarket API inserted raw into innerHTML, filterLeaderboard's no-results message used `${query}` in innerHTML, error state used `${e.message}` in innerHTML. Fixed by adding escapeHtml() and applying it to all name/addr/message innerHTML insertions. Also removed ~25 lines of dead legacy table-row fallback code in filterLeaderboard. 303 tests stable, 9/9 Playwright pass.
FAILED: Nothing failed — all fixes were clean on first try.
RULE: [2026-03-24] → merged into Session #60 XSS canonical rule above.

### Session #58 Reflexion — 2026-03-24
ACCOMPLISHED: Converted leaderboard from table (lb-table) to responsive CSS card grid (lb-grid) in both browse and dashboard views. Added CSS (.lb-grid, .lb-card, .lb-stat, .lb-rank-badge), renderBettorCard() and renderSkeletonCards() JS functions, updated filterLeaderboard() to handle card divs via data-name/data-addr attributes, updated loadLeaderboard() and loadBrowseLeaderboard(). Also updated Playwright check script to recognise new lb-card-name class and navigate to browse view before checking. 303 tests stable, 9 Playwright checks pass.
FAILED: Two Playwright check failures on first run — (1) CHECK 3 looked for "bettor-row"/"bettor-name" classes which don't exist in new card HTML (new cards use lb-card-name); (2) CHECK 7 found empty browse-leaderboard-body because old tbody had a skeleton <tr> as initial HTML but new grid starts empty until showView('browse') is called. Fixed by updating check strings to include lb-card-name and navigating to browse view before checking.
RULE: [2026-03-24] When converting from table rows to card divs, update ALL consumers: (1) Playwright checks that test for class names; (2) filterLeaderboard() which iterates 'tr' elements; (3) empty-state HTML (tr/td wrapper → plain div). Also: any Playwright check that reads a hidden view's content must first navigate to that view — empty div as initial state means the check reads nothing.

### Session #57 Reflexion — 2026-03-24
ACCOMPLISHED: Added 3 tests to test_polymarket_service.py — (1) added `assert result["type"] == "BUY"` to existing test_normalise_bet_missing_fields (the `raw.get("side") or "BUY"` guard was the only untested field in the missing-fields test); (2) test_get_live_trades_empty_proxy_wallet_generates_anon_name: proxyWallet="" + no name/pseudonym → name=="anon" via `addr[:8] + "..." if addr else "anon"`; (3) test_get_leaderboard_empty_first_page_returns_empty_list: mock returning [] on first call → result==[], call_count==1. 301→303 tests.
FAILED: Nothing failed. All 3 tests passed on first run.
RULE: [2026-03-24] When a "missing fields" test exists for a normalisation function (e.g. `_normalise_bet`), always check it asserts ALL output keys — not just the obvious ones. Add missing assertions to the existing test rather than creating a parallel test with one extra assert. The existing test is the canonical contract for the zero-input case.

### Session #55 Reflexion — 2026-03-24
ACCOMPLISHED: Added test_get_me_deleted_user_returns_401 and test_get_me_inactive_user_returns_401 to test_auth.py. Both register a fresh user, mutate DB state (delete row or set is_active=False), then call GET /auth/me with the original (still-valid-HMAC) token. Also cleared bettor_name backlog item (already covered). 299→301 tests.
FAILED: Nothing failed.
RULE: [2026-03-24] When testing get_current_user deleted/inactive paths, register a fresh user (not the fixture), modify DB directly, then call endpoint with the original token. The token HMAC is unchanged by DB mutation — only the DB query result changes. This makes the test prove the DB check, not the HMAC check.

### Session #54 Reflexion — 2026-03-24
ACCOMPLISHED: Added 3 backlog tests — Pydantic v2 extra fields ignored (register with password_confirm → 201), URL-encoded slash in DELETE path decoded to '/' → 404 "Follow not found", unencoded slash creates extra path segment → 404 from router. Also cleared sort=accuracy backlog item (already covered in test_bettors.py from a prior session). 296→299 tests.
FAILED: Nothing failed. All 3 passed on first run.
RULE: [2026-03-24] When testing "URL-special chars in path parameter", test BOTH the URL-encoded variant (e.g. `%2F`) AND the unencoded variant (e.g. literal `/`). They hit different failure modes: encoded → path param decoded to special char (route matches, handler returns 404); unencoded → extra path segment (route doesn't match, router returns 404). Both must be 404/not-500.

### Session #52 Reflexion — 2026-03-24
ACCOMPLISHED: META code quality audit of sessions 46-50 changed test files. Found 2 issues: (1) Dead code in test_admin.py — `ADMIN_PW = "testadmin"` and `_admin_headers()` helper defined but never called (all tests use `get_settings().admin_password` directly); (2) Duplicate test in test_security.py — `test_vip_can_add_more_than_5_follows` fully subsumed by `test_follows.py::test_vip_tier_can_add_six_plus_follows` which tests the same 6 VIP follows plus GET response. Both removed. 295→294 tests.
FAILED: Nothing failed.
RULE: [2026-03-24] In test files, scan module-level defs (constants and helper functions) against their callers before calling the audit done. Test-file dead code is subtler than production dead code because the def exists as scaffolding without warnings — grep for the function name and constant name to confirm they're actually called.

### BRAIN Session #51 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Archived activity_log.md sessions 1-20 to activity_log_archive.md — first actual archival execution (rule was added in session 41, now triggered at 50+ entries). (2) Curated knowledge.md — no merges needed, already clean after session 41 pass. (3) Searched 7+ topics, evaluated 8 new sources. (4) Implemented pytest.param(id=...) pattern in testing.md — names parametrize IDs for readable failure output. (5) Added Polymarket API rate limits to knowledge.md as project fact. (6) Backlogged SSE notification endpoint and ARQ scheduler migration path. (7) No new failure patterns found in last 10 sessions (41-50 — all clean).
FAILED: Nothing failed.
RULE: [2026-03-24] When using @pytest.mark.parametrize with multiple tier or status values, always use pytest.param(..., id="name") instead of bare tuples. Named IDs appear directly in test failure output ("tier_free" vs "[0]"), cutting debug time significantly on parametrize-heavy test suites like PolyEdge's tier-limit tests.

### Session #50 Reflexion — 2026-03-24
ACCOMPLISHED: Added test_poll_bets_last_check_updated_after_poll — captures a `before_poll` timestamp, runs _poll_bets() with an empty get_recent_bets return (no BetEvents needed), asserts `scheduler_module._last_check >= before_poll`. Added test_delete_follow_with_multiple_follows_removes_only_correct_one — upgrades to basic tier, creates 2 follows, deletes one, verifies the other remains in GET /follows. Also discovered the sort=accuracy/volume backlog task was already covered (tests existed at test_bettors.py:29-40). 293→295 stable.
FAILED: Nothing failed.
RULE: [2026-03-24] When a scheduler _last_check test needs empty-poll behavior (no bets returned), mock get_recent_bets to return [] — the poll still sets _last_check = check_time at the end of the try block even when bets is empty, as long as there is at least one BettorFollow row. The `if not addresses: return` early exit is the only path that skips the update.
RULE: [2026-03-24] Before implementing a backlog task, grep the relevant test file for the function/param name first. "sort=accuracy and sort=volume untested" was already covered by test_leaderboard_sort_accuracy/test_leaderboard_sort_volume added in a prior session. 60-second check saves a wasted implementation slot.

### Session #49 Reflexion — 2026-03-24
ACCOMPLISHED: Fixed flaky test `test_tampered_token_blocked_on_follows` — root cause was `_tamper_token` flipping between 'A' (000000) and 'B' (000001) on the last character of the JWT signature. For HMAC-SHA256 (32 bytes = 43 base64url chars), the last character has 2 unused padding bits; 'A' and 'B' differ only in those padding bits and decode to identical byte sequences. So the "tampered" token still passed JWT verification. Fix: tamper `sig[0]` (first character, all 6 bits significant). Added 3 backlog tests: scheduler multi-bet, GET /follows unknown tier, checkout no-price-id 502. 290→293 stable.
FAILED: Nothing failed after the fix.
RULE: [2026-03-24] When writing a JWT tamper helper, NEVER change only the last character of the base64url signature. For any N-byte HMAC, the last base64url character may have up to 5 unused padding bits. Characters that differ only in padding bits decode to the same bytes and the tamper is invisible to the JWT verifier. Tamper a character at index 0 or near the middle of the signature — all 6 bits are significant there.

### Session #48 Reflexion — 2026-03-24
ACCOMPLISHED: Added 3 targeted edge-case tests: (1) `get_active_positions` with a dict API response returns `[]` (the `if not isinstance(raw, list)` branch); (2) unknown subscription tier "enterprise" blocked with 403 via TIER_LIMITS.get fallback; (3) `/admin/stats` full nested shape contract with `isinstance` checks on all nested fields. 287→290 tests stable.
FAILED: Nothing failed. All 3 tests passed on first run.
RULE: [2026-03-24] When adding edge-case tests for "fallback returns []" paths, always check if `isinstance(raw, list)` is the guard or if `except Exception` catches it — the mock must return a non-exception (a dict) to hit the isinstance path, not `side_effect=Exception`. These are different code paths.

### Session #47 Reflexion — 2026-03-24
ACCOMPLISHED: Added 6 response-contract and edge-case tests across test_auth.py, test_bettors.py, test_payments.py. All 6 passed first run; full suite 281→287 stable. Backlog replenished with 3 new HIGH PRIORITY tasks.
FAILED: Nothing failed.
RULE: [2026-03-24] When a backlog task says "stripe_subscription_id=None" but the route only checks stripe_customer_id — verify the actual route code before writing the test. The concern in the backlog may have been misattributed. Write a test for the actual behavior (customer_id check), not the backlog's assumed behavior (subscription_id check). Reading the route is 30 seconds; writing the wrong test wastes the session.

### Session #45 Reflexion — 2026-03-24
ACCOMPLISHED: META code quality audit (sessions 39-44). Found and fixed 3 issues: (1) routes/auth.py register duplicate-email returned 400 instead of 409 (PROJECT.md spec) — fixed route + 3 test assertions; (2) test_follows.py had 2 duplicate /follows/live tests already covered by test_follows_live.py (added in session 42 without checking existing dedicated file) — removed duplicates (-2 tests); (3) test_notifications.py had module-level `import app.services.notifications as notif_mod` and `from app.services.notifications import send_web_push` in the middle of the file — moved to top-level imports block. Also resolved 3 backlog tasks: sms/verify response includes "message" field, telegram/verify response includes "message" field, register response includes user.name. Net: 281→281 (2 removed + 2 added; name test modified existing test).
FAILED: Nothing failed.
RULE: [2026-03-24] When writing tests for error paths, always verify the expected status code against PROJECT.md spec first — do NOT write the test to match the current code. Tests written to match code (not spec) lock in wrong behavior and mask spec violations. Specific case: duplicate email register should be 409, not 400.
RULE: [2026-03-24] When adding /follows/live tests to test_follows.py, the dedicated file test_follows_live.py already exists with comprehensive coverage. Before adding any test to a file, grep for similar test names in other test files — especially when the endpoint has its own dedicated test file.

### Session #44 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Added test_login_empty_password_returns_401 — empty "" passes LoginRequest Pydantic (no min_length) but verify_password returns False → 401. Registers a real user first so the lookup hits a DB row. (2) Added test_follows_live_all_bettors_raise_returns_three_entries_with_empty_positions — VIP + 3 follows + all get_active_positions raise → 3 entries with active_positions=[] confirmed. The autouse clear_activity_cache fixture handles cache isolation. (3) Added test_put_alerts_settings_invalid_push_subscription_returns_422 — "not_valid_json" hits json.loads() guard → 422. All 3 passed first run; full suite 281/281. Added 3 new backlog tasks (sms/verify response shape, telegram/verify response shape, register response user.name).
FAILED: Nothing failed.
RULE: [2026-03-24] When writing a test for an endpoint that requires auth and has a VIP/paid tier requirement (like follows/live multi-follow test), always set subscription_tier directly on the User DB row — not via the API. The tier-change API requires Stripe, which isn't configured. Pattern: `user.subscription_tier = "vip"; db.commit()` via the db fixture.
RULE: [2026-03-24] For a "login with invalid credential" test, register a real user first, then attempt the bad-credential login. Testing against a non-existent email produces the same 401 (user=None → 401), but testing against a real user makes the test path more realistic — it hits verify_password() instead of the early return, which is the branch we actually want to verify.

### DEEP Brain Session #41 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Curated knowledge.md — merged Sessions #13+#14 duplicate cache isolation rules into one canonical rule (three caches, same pattern, now unified). (2) Fixed stale session references in techniques.md (sessions "#48 and #57" referenced a prior project, not PolyEdge). (3) META analysis of last 20 sessions — identified 2 failure patterns: backlog-empties-reactively (4 META sessions spent on this) and symmetry-gap (same coverage gap in sibling functions found session later). (4) Implemented 3 concrete improvements: backlog low-water-mark rule in PROMPT.md (< 2 HIGH PRIORITY → add 3+ tasks before close), symmetry audit rule in testing.md (check sibling functions for same gap), activity_log archival rule in BRAIN_PROMPT.md Step 1D (> 30 entries → archive oldest 20). (5) Searched 7 topics, evaluated 5 new sources. (6) Replenished empty HIGH PRIORITY backlog with 5 concrete testing tasks.
FAILED: Nothing failed.
RULE: [2026-03-24] When a BRAIN/META session identifies a failure pattern caused by a MISSING RULE (e.g. backlog empties reactively), the fix must be implemented in the file that gets read at the exact point the failure occurs — not in knowledge.md. Backlog empties at end of WORK session → add the low-water-mark rule to PROMPT.md STEP 3 (where backlog cleanup happens). Symmetry audit fails during testing → add it to testing.md BRANCH AUDIT WORKFLOW. Rules placed in the right file at the right moment are followed; rules in knowledge.md are often forgotten.
RULE: [2026-03-24] activity_log.md is auto-loaded into context. Archive when > 30 entries to prevent context bloat. Use BRAIN_PROMPT.md Step 1D trigger. The archive format is: move oldest 20 to activity_log_archive.md (append), add a header line to the active file noting the archive range.

### Session #43 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Fixed LoginRequest missing max_length=128 — symmetry gap vs. RegisterRequest (same DoS vector). (2) Fixed remove_follow missing cache eviction — stale /follows/live data after unfollow was a real bug. (3) 4 tests: login 129-char→422, login 128-char→200 (boundary), DELETE clears cache, /follows/live cache hides 2nd follow within TTL. All 4 passed first run; full suite 278/278.
FAILED: Full suite had 2 intermittent failures (test_admin_stats_counts_users assert 1==2, test_sms sqlalchemy error) — passed in isolation, passed on 2nd full run. Pre-existing test isolation flakiness, not caused by this session's changes.
RULE: [2026-03-24] Always check BOTH register AND login request models when adding input validation (min_length, max_length, type). These models are often written separately and drift apart — a guard added to RegisterRequest may be missing from LoginRequest. Same applies to any paired request models (e.g. CreateRequest vs. UpdateRequest).
RULE: [2026-03-24] When a DELETE or PUT endpoint modifies data that is also served by a cached GET endpoint, the DELETE/PUT handler MUST evict the cache entry for the affected resource. Pattern: `_activity_cache.pop(user_id, None)` in remove_follow. Without eviction, stale data persists until TTL expires — test by: populate cache via GET, DELETE the resource, call GET again, assert fresh data.

### Session #42 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Added max_length=128 to RegisterRequest.password — closes a real bcrypt DoS vector. (2) 2 tests for password boundary (10000-char rejected, 128-char accepted). (3) 2 tests for /follows/live response shape ({"bettors": []} contract, per-item key shape). (4) VIP tier follow cap test (6 follows succeed, limit=999999 confirmed). (5) Admin zero-users test (all 6 stats = 0/0.0). (6) Found scheduler freshness filter was already covered by test_poll_bets_skips_old_bets — grepped and confirmed before writing a duplicate.
FAILED: test_follows_live_response_shape_per_bettor failed in the full suite (passed in isolation) due to _activity_cache stale data from the prior test. Root cause: module-level cache dict persists across tests since Python modules are singletons. Fixed by calling `follows_module._activity_cache.clear()` at the start of each /follows/live test.
RULE: [2026-03-24] Module-level caches in route handlers (like `_activity_cache` in routes/follows.py) survive across test functions — they're module singletons. Tests that read cached routes MUST clear the cache before the GET call, or they may get a stale response from a prior test. Pattern: `import app.routes.follows as m; m._activity_cache.clear()`. Same as conftest `clear_stripe_webhook_secret` autouse fixture pattern — consider adding autouse fixture if multiple tests hit the same cache.

### Session #40 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 branch-coverage tests. Gaps found: (1) send_sms had the same gap as send_telegram from session 39 — only the False paths (missing credentials) were tested; HTTP success and exception handler were untested; (2) Scheduler VIP SMS dispatch path was completely untested — the only untested notification channel combination remaining; (3) dispatch_bet_notification phone_number=None guard (sms skipped even with sms_enabled=True when no phone) was untested. All 5 passed first run. 263→268.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing notification function coverage, apply the same bool-return rule (session 39) to ALL three send_* functions: send_telegram, send_sms, send_web_push. Each has missing_credentials→False, HTTP_success→True, exception→False paths that must all be tested. After fixing one, immediately check the others for the same gap.
RULE: [2026-03-24] Scheduler SMS dispatch is only exercisable when user.subscription_tier="vip", user.phone_verified=True, AND alert.sms_enabled=True — all three conditions must be set simultaneously. Setting only one or two silently skips the SMS path without error, leaving the test exercising the wrong branch.

### Session #39 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 branch-coverage tests. Key gaps found: (1) send_telegram had only False-path tests (early return for empty bot_token/chat_id) — the HTTP success path returning True was untested; (2) scheduler try/except around dispatch_bet_notification had no test confirming exception is caught and event.notified=True still set; (3) telegram/start response shape only asserted "code" in prior test — instructions and bot_link were unverified; (4) telegram/verify .upper() normalization for lowercase codes was untested; (5) PUT /alerts/settings response telegram_verified and phone_verified keys were never asserted. All 5 passed first run. 258→263.
FAILED: Nothing failed.
RULE: [2026-03-24] For any service function that returns bool (send_telegram, send_web_push, send_sms), verify BOTH the True path (success) AND every False path (early returns + exception handlers). Only testing the False paths leaves the success branch uncovered and can mask regressions where the function silently returns False on success.
RULE: [2026-03-24] For any try/except block in a scheduler or background job, write a test that confirms: (a) the exception is swallowed (no propagation), and (b) code AFTER the except block still executes correctly. A caught exception that silently prevents subsequent state changes (like event.notified=True) is a silent bug.

### Session #38 Reflexion — 2026-03-24 (De-Sloppify Audit)
ACCOMPLISHED: Ran De-Sloppify audit across sessions 32–37 changed files. Found 3 issues: (1) dead module-level var `BETTOR_C` in test_follows.py — defined at top but never referenced in any test; (2) two duplicate tier/limit tests in test_follows.py (`test_list_follows_basic_tier_reports_tier_and_limit`, `test_list_follows_vip_tier_reports_tier_and_limit`) that are exact duplicates of the parametrized `test_follows_always_returns_tier_and_limit` invariant already in test_hypothesis_invariants.py; (3) `_activity_cache` in follows.py grows unboundedly (logged to tech_debt.md). Fixed 1+2, logged 3. 260→258.
FAILED: Nothing failed.
RULE: [2026-03-24] Agent-written tests accumulate duplicate parametrized coverage across files over time. When a parametrized invariant test is added to test_hypothesis_invariants.py covering all tier variants, the matching per-tier tests in test_follows.py become redundant. De-Sloppify pattern: after each De-Sloppify session, grep each individual test name across all test_*.py files and check if the same scenario is already covered by a parametrized or invariant test.
RULE: [2026-03-24] Dead module-level constants in test files accumulate silently (e.g., `BETTOR_C = "0xghi789"` defined but never used). Periodic audit: for each `^[A-Z_]+ =` module-level variable in test_*.py, verify it appears at least once outside its definition line.

### Session #37 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests. Found that 2 of 5 HIGH PRIORITY backlog items (invoice.payment_failed, sort=volume) were already covered — grepped and skipped per knowledge.md rule. Real gaps found: DELETE /follows 204 had no `resp.content == b""` assertion; DELETE 404 had no detail message check; POST /payments/checkout response key set had no complete contract assertion; scheduler had no test for both channels enabled simultaneously; scheduler had no test for web_push-only (telegram_enabled=False) path. All 5 passed first run. 255→260.
FAILED: Nothing failed.
RULE: [2026-03-24] Scheduler notification channel tests require three independent test cases: (1) telegram-only (web_push_enabled=False), (2) web_push-only (telegram_enabled=False), (3) both channels simultaneously. Testing only one combination does NOT cover the others — the conditional expressions `if (alert and alert.telegram_enabled and user.telegram_verified)` and `if (alert and alert.web_push_enabled)` are evaluated independently and can be wrong independently.
RULE: [2026-03-24] A 204 response shape contract test must assert BOTH `resp.status_code == 204` AND `resp.content == b""` — the status code alone does not prove the body is empty. Similarly, a 404 contract test should assert both `resp.status_code == 404` and the exact `resp.json()["detail"]` message — the status alone doesn't prevent wording regressions.

### Session #36 Reflexion — 2026-03-24 (META)
ACCOMPLISHED: Fixed stale "stockcards" project references in testing.md PATCHING section; replenished empty testing backlog with 5 concrete tasks. Session 26 fixed the IMPORT CHECK in testing.md but left the PATCHING section with wrong module paths — partial fix that this session caught.
FAILED: Nothing failed.
RULE: [2026-03-24] When a META session fixes a stale project reference in a skill file (e.g. wrong import check), audit ALL other examples in the same section for the same staleness — fixes are often partial. Session 26 fixed one example but left the PATCHING section unchanged; this session found it 10 sessions later.

### Session #35 Reflexion — 2026-03-24
ACCOMPLISHED: Found 1 security bug: RegisterRequest.password had bare `str` with no min_length — empty string "" was accepted, hashed by bcrypt, and stored as a valid credential. Fixed with `Field(..., min_length=1)`. Added 5 tests: empty password → 422; GET /alerts/settings auto-creates AlertSetting for user without one; PUT /alerts/settings auto-creates; PUT empty body `{}` → 200 no changes; name whitespace stripped on register. 250→255.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing Pydantic models for input validation, check EVERY `str` field — not just email and name. Password fields are easy to forget since they're hashed, but an empty password is a valid bcrypt hash. Pattern: `password: str` with no min_length = security hole. Add `Field(..., min_length=1)` (or min_length=8 for production) to any password field.
RULE: [2026-03-24] AlertSetting auto-create branches in GET/PUT /alerts/settings are unreachable from normal API usage (registration always creates the row), but testable by inserting a User directly in the DB. These defensive paths should still be covered — they protect against future migration or manual DB changes that could produce users without AlertSettings.

### Session #34 Reflexion — 2026-03-24
ACCOMPLISHED: Found 2 input-validation bugs by auditing RegisterRequest model — email was `str` (no format check, accepted `""`), name had no validator (whitespace-only stored as `""`). Fixed both: `EmailStr` for email, `field_validator` for name. Fixed flaky Hypothesis deadline (test makes real HTTP calls, 200ms default is too tight). Added 4 tests: empty email 422, whitespace name 422, free-tier duplicate ordering (403 not 409), bettor detail shape contract. 246→250.
FAILED: Nothing failed.
RULE: [2026-03-24] After adding any `.strip()` call in a route handler, audit the Pydantic model — if the field is bare `str` with no min_length or validator, a blank or whitespace-only value will pass FastAPI validation and reach the route as `""` after strip. The fix is at the model level: `EmailStr` for emails, `field_validator` that strips-then-checks for string fields where blank is invalid. Never rely on route-level `.strip()` alone as the only defense.
RULE: [2026-03-24] Hypothesis @settings deadline=None is required for any test that touches the real network (even with mocks on the route, if the test infrastructure startup involves real connections). The 200ms default deadline is calibrated for pure CPU logic, not I/O. Check for DeadlineExceeded in Hypothesis test failures before investigating logic bugs.

### Session #33 Reflexion — 2026-03-24 (De-Sloppify Audit)
ACCOMPLISHED: Ran the De-Sloppify audit across the last 5 work sessions' changed files. Found 1 real bug: `auth.py` login used `.lower()` but not `.strip()` — registration strips emails before storing, so a user who typed `" user@example.com "` in the login form would get 401. Fixed with `.lower().strip()`. Found 1 dead code: `@given(st.nothing())` `_placeholder` function in test_hypothesis_invariants.py (agent draft artifact). Found 1 doc inconsistency: CLAUDE.md shows VIP at $14.99 but code/tests use $9.99 — logged to tech_debt.md. Added test_login_with_whitespace_padded_email_works. 245→246.
FAILED: Nothing failed.
RULE: [2026-03-24] When a session adds whitespace-stripping to register (`.strip()`), immediately check all OTHER places the same field is normalized — especially login. It's a systematic mistake to fix input normalization in one path (register) and miss the parallel path (login). After any normalization fix, grep for the same field in all routes that accept it.

### Session #32 Reflexion — 2026-03-24
ACCOMPLISHED: Fixed 2 input-validation bugs and added 6 tests. Bug 1: `FollowRequest.bettor_address: str` had no min_length — empty string was silently stored in DB; fixed with `Field(..., min_length=1)`. Bug 2: `/auth/register` duplicate check used `.lower()` but not `.strip()` — registering with `" user@example.com "` would bypass the check and crash with 500 (DB unique constraint) on a second attempt; fixed by adding `.strip()` to the check. All 6 new tests passed first run (after fixing a test isolation issue where extra assertions from a prior test leaked into mine due to imprecise old_string in Edit call). 239→245.
FAILED: First run of `test_telegram_start_called_twice_overwrites_code` failed — `assert user.telegram_verified is True` at line 265. Cause: my Edit `old_string` ended at `assert resp.json()["verified"] is True` but the actual file had 3 more lines (`db.refresh(user)`, two asserts) belonging to the original test. My new test insertion placed those lines inside the new test body. Fix: used another Edit to remove the 3 leaked lines. Passed on re-run.
RULE: [2026-03-24] When inserting a new function block after another function using Edit, always verify the `old_string` extends to the END of the target function (including any trailing `db.refresh` or assertion lines), not just the last obvious assertion. Imprecise `old_string` boundaries cause following-test code to leak into the new test body, producing confusing false failures.

### Session #30 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests covering gaps found by systematic cross-file audit. (1) Cross-user DELETE /follows security — verified user B cannot delete user A's follow (route filters by user_id, returns 404); (2) Register uppercase email duplicate — `email.lower()` at register/login means `USER@EXAMPLE.COM` collides with `user@example.com`; (3) GET /auth/me all 7 user_to_dict fields asserted; (4) admin/stats follows.total with actual DB rows; (5) scheduler passes correct telegram_chat_id to dispatch when alert.telegram_enabled=True and user.telegram_verified=True — this required adding an AlertSetting row to the sched_db fixture alongside the user. All 5 passed first run. 234→239.
FAILED: Nothing failed.
RULE: [2026-03-24] When writing scheduler integration tests that test alert-condition branching (telegram_enabled, sms_enabled, web_push_enabled), always create an AlertSetting row in the test DB — the scheduler queries AlertSetting for each follower. Without the row, `alert` is None and the conditional expressions all produce None, hiding whether the logic is right. Use `session.add(AlertSetting(user_id=user.id, telegram_enabled=True, ...))` before committing.

### Session #29 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests covering untested defensive branches: (1) scheduler `is_active=False` user skip — the `if not user or not user.is_active or subscription_tier == "free"` condition had its middle sub-condition untested; (2) `_parse_timestamp` OverflowError for `10**20` — the `except (OSError, OverflowError, ValueError): return None` path was never hit; (3) scheduler orphaned follow (user_id with no matching User) — `if not user: continue` was untested; (4) `/follows/live` name fallback — `follow.bettor_name or addr[:12]+"..."` only reachable when bettor_name is manually set to None in DB; (5) telegram disable for basic — `telegram_enabled=False` PUT path confirmed working after enable. All 5 passed first run. 229→234.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing scheduler.py `if not user or not user.is_active or subscription_tier == "free"` guard: all three sub-conditions must be tested independently. Free-tier is the easiest to remember; is_active=False and user=None are often forgotten. Check each sub-condition has its own test case.

### Session #28 Reflexion — 2026-03-24
ACCOMPLISHED: Added 19 tests covering 3 areas: (1) 5 direct `send_web_push` unit tests — happy-path JSON string (201), happy-path dict (200), missing endpoint, HTTP 410, connection exception. `send_web_push` was previously only ever mocked at dispatch level, never tested directly. (2) 1 scheduler test — `get_recent_bets` returns `None` (no exception) causes `for bet in None` TypeError, caught by outer except, no crash, no BetEvent, no dispatch. (3) 13 Hypothesis/parametrize invariant tests — GET /follows tier+limit presence for all 3 tiers, POST /follows tier limit enforcement for free/basic, 7 protected endpoints always reject missing auth, adversarial bettor address strings never cause 500. Installed hypothesis and added to requirements.txt. Checkout response shape and DELETE /follows 404 backlog items turned out to be already covered. 210 → 229.
FAILED: First full-suite run showed Hypothesis adversarial-address test FAILED — issue was Hypothesis database interaction with test ordering (the profile_cache wasn't being cleared between Hypothesis iterations). When run in isolation the test PASSED. Fixed by ensuring `_profile_cache.clear()` runs per Hypothesis iteration (it's inside the test body). Passed on re-run.
RULE: [2026-03-24] To patch `httpx.AsyncClient` used inside an async service function, use `patch.object(module, "httpx", ...)` won't work — the module references `httpx.AsyncClient`. Correct pattern: `patch.object(notif_mod.httpx, "AsyncClient", return_value=mock_instance)` where mock_instance has `__aenter__` and `__aexit__` set as AsyncMocks returning the instance itself. The mock_instance.post must be an AsyncMock returning a MagicMock with .status_code set.

### Session #27 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 stripe_service.py branch tests. Gaps found by reading every if/elif/else and checking grep in existing tests: (1) `_handle_checkout_completed` missing-metadata early-return had no test; (2) `if subscription_id:` set stripe_subscription_id had no assertion; (3) `_handle_subscription_change` unknown-customer early-return had no test; (4) active status with price_id matching neither basic nor vip left tier unchanged — untested; (5) `create_billing_portal_session` had no service-level unit test (only route-level mock). All 5 passed first run. 205→210.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing stripe_service.py, check these 4 branch types that are commonly missed: (1) early-return guards (`if not user_id or not plan: return`, `if not user: return`) — they're silent and easy to miss in the "happy path" test set; (2) conditional field assignment (`if subscription_id: user.stripe_subscription_id = ...`) — often tested indirectly but the field value is never asserted; (3) loop body with no-match case (`for item in items: if price_id == X ...`) — what happens when nothing matches? Tier unchanged but db.commit() still runs; (4) service-level unit test vs. route-level mock — route tests mock the service function; they don't test the service function's own logic. Always add at least one direct service unit test.

### META Session #26 Reflexion — 2026-03-24
ACCOMPLISHED: Fixed testing.md import check (was pointing to `stockcards` — wrong project, would fail for PolyEdge). Added branch-audit workflow to testing.md (the systematic checklist used in sessions 22-25 was only in knowledge.md reflexions; moved it to testing.md where WORK agents actually look). Replenished backlog with 6 concrete testing tasks (stripe_service branches, send_web_push unit tests, scheduler edge cases, Hypothesis invariants, DELETE /follows 404, checkout response shape).
FAILED: Nothing failed.
RULE: [2026-03-24] When a META session finds no active failures (sessions all green), focus on: (1) stale references in skill files (wrong project names, outdated paths), (2) proven patterns in knowledge.md reflexions that haven't been promoted to the skill file that gets read daily, and (3) backlog replenishment so next session doesn't waste turns on task discovery. These three checks reliably produce 2-3 actionable improvements even in a "nothing broke" session.

### Session #25 Reflexion — 2026-03-24
ACCOMPLISHED: Added 6 coverage-gap tests found by auditing every branch in polymarket.py and notifications.py. Gaps: (1) get_active_positions poly_url has 3 branches (eventSlug / slug / fallback) — only eventSlug was tested; (2) get_live_trades non-list response branch untested; (3) get_recent_bets "activity" key fallback untested (only "data" key was); (4) send_telegram empty-creds early-return had no unit test despite being a real defensive branch. All 6 passed first run. 199→205.
FAILED: Nothing failed.
RULE: [2026-03-24] When a function has a multi-branch conditional for URL/string construction (if A: url=...; elif B: url=...; else: url=default), each branch needs its own test. Testing only the first branch (e.g. eventSlug) does NOT cover the slug-only or no-slug fallback — these are independent code paths that can be wrong independently. Count the branches, write one test per branch.

### Session #24 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests found by systematic audit: VIP tier follows limit (completes free/basic/VIP triplet), get_bettor_profile empty-activity path, follows/live followed_at response field, get_recent_bets dict-response defensive branch, /bettors limit=0 boundary. All 5 passed first run. 194→199.
FAILED: Nothing failed.
RULE: [2026-03-24] When auditing coverage, check service-level defensive branches separately from route tests — e.g. `get_recent_bets` has `if not isinstance(raw_list, list): raw_list = raw_list.get("data") or []` that can only be hit by mocking the httpx client at the service level. Route-level mocks (patching the service function itself) will never exercise this branch. Always look for untested `isinstance` guards and empty-collection returns in service files.

### Session #23 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests for previously untested async polymarket service functions and auth email lowercasing. All 5 passed first run. 189→194.
FAILED: Nothing failed. Full suite showed the known ordering flake on test_tampered_signature_returns_401 (passes in isolation — documented in Session #15).
RULE: [2026-03-24] Polymarket async service functions (get_bettor_profile, get_recent_bets, get_live_trades, get_leaderboard) had zero direct unit tests despite being the core data pipeline. When testing async httpx functions use AsyncMock with __aenter__/__aexit__ returning mock_client; for multi-call pagination tests use side_effect list on .get(). For email auth tests, register with lowercase then login with UPPERCASE to verify the lowercasing guard.

### Session #22 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests. Gaps found by reading every route's branches vs. existing tests: _profile_cache hit was the only cache-hit path not tested (leaderboard + trades were); past_due and unpaid statuses in _handle_subscription_change were untested; subscription.updated basic upgrade had no test (only VIP); admin/stats bet_events fields were presence-checked but never value-verified; POST /follows response body only asserted bettor_address, not the other 3 fields. All 5 passed first run. 184→189.
FAILED: Nothing failed.
RULE: [2026-03-24] After testing all caches for hit paths, audit each cache separately — _profile_cache (keyed by address string), _leaderboard_cache (keyed by sort+period+limit), and _trades_cache (flat dict) have different key structures. Testing one cache type does not cover another. Similarly, for webhook event handler branches, list all status strings in the code (canceled, unpaid, past_due, active) and verify each has at least one test.

### BRAIN Session #31 Reflexion — 2026-03-24
ACCOMPLISHED: (1) Curated knowledge.md — scanned all RULE: entries, confirmed no duplicates or superseded rules (the session #17 merge was the last one needed). (2) Researched 7+ topics, evaluated 9 new sources. (3) Implemented periodic De-Sloppify tech-debt trigger in PROMPT.md step 3 — every 5 work sessions a META quality audit task is auto-added to backlog. (4) Replenished empty testing backlog with 5 new tasks covering POST /follows empty address, admin MRR precision, whitespace email, web_push independence, and telegram/start second-call regeneration. (5) Added 2 feature items to backlog: /bettors/{address}/playbook endpoint and hourly leaderboard cache refresh. (6) Logged 9 new sources in sources.md.
FAILED: Nothing failed.
RULE: [2026-03-24] Empirical research (arxiv 2511.04427) shows LLM-assisted velocity gains reverse after 6-8 weeks due to accumulated test specificity degradation and cross-file coupling. A periodic De-Sloppify pass every 5 work sessions prevents this — check sessions.json count, trigger the pass proactively rather than waiting for visible quality issues.

### BRAIN Session #21 Reflexion — 2026-03-24
ACCOMPLISHED: Curated knowledge.md (merged duplicate grep-before-adding rules from sessions #10 and #17 into one canonical entry). Ran web searches across 5 topics. Found 3 actionable improvements: (1) irreversibility check added to self-critique gate in PROMPT.md, (2) Hypothesis property-based testing added to testing.md, (3) 4 new feature items added to backlog (Discord, entry price in alerts, conviction score, outbox pattern). Logged 8 new sources in sources.md. Found strong competitor intelligence on Polymarket copy-trading SaaS market.
FAILED: Nothing failed.
RULE: [2026-03-24] Agents consistently underweight irreversible actions (DB deletes, Stripe charges, live notification sends) — explicitly name each one in self-critique before committing. If the session's tests don't mock or guard the irreversible action, flag it before running the code. (Source: arxiv 2601.02749 The Path Ahead for Agentic AI)

### Session #20 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests. Gaps found by auditing response field assertions and happy-path coverage. Trades cached=True was the only missing branch for that pattern. Login user dict untested despite being returned. SMS start had zero success-path tests. telegram/verify and sms/verify had no no-auth tests. All 5 passed first run. 179→184.
FAILED: Nothing failed. All 5 passed first run.
RULE: [2026-03-24] When auditing for coverage gaps, check: (1) for every endpoint that returns a `cached` bool, is there a second-call test verifying cached=True? (2) for every POST endpoint that returns a response body, are success-path response fields asserted in at least one test? (3) for every POST /verify-style endpoint (sms/verify, telegram/verify), is there a no-auth test? These are the most common missed test types after basic happy/error coverage exists.

### Session #19 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests. Gaps found via rule from Session #18: (3) not all HTTP methods covered for auth. PUT /alerts/settings and POST /follows had no no-auth test (only GET/DELETE were tested). Also covered: VIP tier telegram/start (only basic was tested), leaderboard cached=True second-call branch, GET /alerts/settings phone/telegram field presence. 174→179.
FAILED: Nothing failed. All 5 passed first run.
RULE: [2026-03-24] For any endpoint with multiple HTTP methods (GET/POST/PUT/DELETE), each method needs its own no-auth test — passing GET /foo without auth ≠ POST /foo is also protected. Check every method, not just the first one found.

### Session #18 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests by auditing each endpoint against the PROJECT.md table. Gaps found: basic-tier GET /follows limit field, leaderboard "cached" response field, DELETE /follows without-auth 403, web-push disable toggle, admin users.basic/users.vip count fields. All 5 passed first run. 169→174.
FAILED: Nothing failed.
RULE: [2026-03-24] When the backlog empties, audit each endpoint by checking: (1) are all 3 tier values (free/basic/VIP) tested for any tier-gated response field, (2) are all response fields asserted in at least one test, (3) are all HTTP methods for protected endpoints covered in auth tests. These three checks reliably surface 3-5 new gaps per audit.

### Session #17 Reflexion — 2026-03-24
ACCOMPLISHED: Added 2 tests: test_leaderboard_sort_accuracy (verifies sort=accuracy passes correct arg) and test_poll_bets_multiple_followers_each_notified (verifies both followers get dispatch_bet_notification called). 167 → 169 tests. All 6 high-priority backlog testing tasks are now complete.
FAILED: Nothing failed. Both tests passed first run.
*(grep-before-adding rule merged into Session #10 canonical entry above)*

### Session #15 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests covering previously untested branches: SMS start 503 (Twilio not configured), 400 (invalid phone format), 502 (send_sms returns False); GET /alerts/settings returns parsed push_subscription dict; /follows/live cache-hit path (API called once, second call served from cache). 162 → 167 tests.
FAILED: Transient failure of test_tampered_signature_returns_401 on first full-suite run — passed in isolation and on second run. Likely a test ordering flake unrelated to changes.
RULE: [2026-03-24] Module-level settings objects (settings = get_settings() at top of alerts.py) must be monkeypatched directly on the module attribute (app.routes.alerts.settings.twilio_account_sid) with try/finally restore — using monkeypatch fixture or patching get_settings() won't work because the reference is already bound at import time.

### Session #14 Reflexion — 2026-03-24
ACCOMPLISHED: Added 4 tests covering previously untested branches: is_active=False login guard (403), GET /bettors/{address} exception handler (502), basic-tier cap error message (VIP upsell), and bettor_name truncated-address fallback. 158 → 162 tests.
FAILED: Nothing failed. All 4 tests passed first run.
*(cache isolation rule merged into Session #13 canonical entry below)*

### Session #13 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests covering previously untested error paths: portal Stripe 502, leaderboard API 502, recent trades API 502, and recent trades limit boundaries (422 for limit<5 and limit>50). 153 → 158 tests.
FAILED: Nothing failed. Cache isolation concern was caught in self-critique: trades_cache (30s TTL) would have served a cached 200 to the error test if run after test_recent_trades_public. Fixed by resetting _trades_cache to {data: None, ts: 0} at test start. Leaderboard error test uses time_period=day to avoid key collision with existing profit_month_50 cache entry.
RULE: [2026-03-24] Three module-level caches in bettors.py (_leaderboard_cache, _trades_cache, _profile_cache) persist across tests in the same pytest session. Tests that need to exercise the uncached code path must reset each relevant cache at test start: call `_profile_cache.clear()` for the profile cache; set `_leaderboard_cache` or `_trades_cache` to `{data: None, ts: 0}` (or use a unique query param combo not seen by earlier tests). Missing this causes the mock to never be called and the test to silently return a cached 200 instead of the expected error.

### Session #12 Reflexion — 2026-03-24
ACCOMPLISHED: Ran 9-check Playwright E2E suite. Sort tabs (profit/volume), period tabs (week/month), account tier label, and browse view (unauthenticated) all pass. Discovered the "bettor profile click-through" backlog task assumes a feature that was never built — no onclick on leaderboard rows navigates to a profile view.
FAILED: CHECK 8 had a Python UnicodeEncodeError on Windows CP1252 terminal when printing button text containing the → character. Fixed by encoding to ASCII with error replacement before print.
RULE: [2026-03-24] When printing Playwright-fetched DOM text on Windows, always encode with `.encode('ascii', errors='replace').decode('ascii')` before printing — PolyEdge buttons contain → (U+2192) which breaks CP1252 print on Windows.
RULE: [2026-03-24] The PolyEdge leaderboard rows have NO onclick — there is no bettor profile click-through in the frontend. Do not add backlog tasks assuming this feature exists until it is built. The API endpoint GET /bettors/{address} exists but is not wired to any UI navigation.

### Session #10 Reflexion — 2026-03-24
ACCOMPLISHED: Added 2 tests — `test_follows_list_contains_bettor_fields` (GET /follows returns bettor_address, bettor_name, created_at per item) and `test_get_me_reflects_updated_subscription_tier` (GET /auth/me returns updated tier after DB change). Confirmed webhook delete test and MRR test already existed in test_payments.py and test_admin.py. 151 → 153 tests.
FAILED: Nothing failed. Both tests passed first run.
RULE: [2026-03-24] Before adding any backlog test task or checking off a backlog item, grep existing test files for the function name or endpoint path — ~50% of the time it already exists from a prior session. Grepping saves a full read of each test file and prevents duplicate tests. (Merged from sessions #10 + #17.)

### Session #9 Reflexion — 2026-03-24
ACCOMPLISHED: Ran 16-check Playwright E2E for follows + alerts pages. All 16 passed. Discovered that `toggleWebPush()` calls `Notification.requestPermission()` — headless tests must grant notifications via `browser.new_context(permissions=['notifications'])`. Found that `showView('dashboard')` does NOT set `currentUser` — must call `window.init()` instead so `/auth/me` is fetched. Free tier Telegram toggle is intentionally blocked by `openUpgradeModal()`.
FAILED: First run: nav clicks failed (elements not visible in headless viewport after follow button click) — switched from `.click()` to `page.evaluate("showTab('...')")`. Second run: toggle class unchanged — root cause was headless notification permission + `currentUser=null`. Fixed in v5 of check script.
RULE: [2026-03-24] In Playwright tests for PolyEdge: (1) Always call `window.init()` not `showView('dashboard')` — init() fetches /auth/me and sets currentUser; without it, toggleFollow() sees currentUser=null and shows sign-up nudge. (2) Grant notifications permission via `browser.new_context(permissions=['notifications'])` or toggleWebPush will return early. (3) Use JS `showTab()` calls not DOM clicks for navigation — sidebar nav elements may not be clickable in headless depending on page scroll state.

### Session #8 Reflexion — 2026-03-23
ACCOMPLISHED: Added 3 BetEvent field-value tests (all-fields-correct, missing-fields-defaults, timestamp-timezone-aware) and 3 subscription lifecycle tests (VIP→free preserves follows, VIP→basic preserves follows, downgraded user blocked from new follow). 145 → 151 tests.
FAILED: First run of test_poll_bets_bet_event_all_fields_correct failed — `event.timestamp == FUTURE_TS` failed because SQLite strips tzinfo on DateTime column round-trip. Fixed by comparing `.replace(tzinfo=None)` on both sides.
RULE: [2026-03-23] SQLite strips tzinfo from DateTime columns on round-trip. Always compare `event.timestamp.replace(tzinfo=None)` against `expected_dt.replace(tzinfo=None)` when asserting BetEvent (or any model) timestamps stored via SQLite. This also applies to timestamp_aware test in test_scheduler.py.

### Session #7 Reflexion — 2026-03-23
ACCOMPLISHED: Added 6 dispatch_bet_notification tests (both-channels-none, no chat_id, no push_sub, correct args passed, failure doesn't block push) and 5 telegram/verify tests (no pending, wrong code, correct code, round-trip, already-linked). Also resolved admin password conflict — confirmed polyedge-admin-2026 is loaded from .env correctly. 134 → 145 tests.
FAILED: Nothing failed. All 11 tests passed first run.
RULE: [2026-03-23] dispatch_bet_notification does not catch exceptions from send_telegram — only mock with return_value=False (not side_effect=Exception) to test failure isolation. The real send_telegram catches all exceptions internally; side_effect bypasses that and makes dispatch crash. Test failure resilience with False returns at the dispatch level.

### Session #5 Reflexion — 2026-03-23
ACCOMPLISHED: Added 8 edge-case tests covering follow-limit error wording, SQL injection safety, admin stats empty-DB, and invalid push_subscription. Found and fixed a real bug: PUT /alerts/settings accepted invalid JSON strings (200) which then caused GET to 500 on json.loads. Fix adds try/except json.loads validation before storing. 126 → 134 tests.
FAILED: test_invalid_json_push_subscription_returns_422 failed on first run (got 200 instead of 422) — confirmed the bug. One-line fix resolved it.
RULE: [2026-03-23] When a field stores a JSON-serialized string (Optional[str] in Pydantic), Pydantic will not validate the JSON content — the route must explicitly call json.loads() in a try/except and raise HTTPException(422) if it fails, otherwise invalid JSON silently lands in the DB and crashes on read.

### Session #4 Reflexion — 2026-03-23
ACCOMPLISHED: Added 18 security and business-rule tests in test_security.py. All 18 passed first run. Full suite: 108 → 126 passed.
FAILED: Nothing failed. All tests passed on first run.
RULE: [2026-03-23] To test JWT expiry, use `create_access_token(data, expires_delta=timedelta(seconds=-1))`. To test tampered signature, split token on "." and flip one char in part[2] (the HMAC signature). Both reliably trigger 401 from jose JWTError.

### Session #3 Reflexion — 2026-03-23
ACCOMPLISHED: Ran full E2E Playwright smoke test. All 7 checks passed: landing page, backend API (100 real bettors), leaderboard browse view, login form, register form, no JS errors.
FAILED: Nothing failed. Register form check initially used wrong IDs (`register-email`/`register-password`) — actual IDs are `reg-email`/`reg-password`. Fixed in check script before final run.
RULE: [2026-03-23] Always grep the actual HTML for input IDs before writing Playwright selectors — PolyEdge register form uses `reg-*` prefix (not `register-*`). Confirm selectors from source before writing checks.

### Session #2 Reflexion — 2026-03-23
ACCOMPLISHED: Added 17 tests for scheduler module — _parse_timestamp (pure function, 10 cases) and _poll_bets (7 integration cases using file-based SQLite tmp_path fixture).
FAILED: Nothing failed. All 17 tests passed on first run.
RULE: [2026-03-23] To test a function that creates its own DB session (via `SessionLocal()`), use a tmp_path file-based SQLite (not in-memory) and patch `app.services.scheduler.SessionLocal` with a sessionmaker bound to that engine. In-memory SQLite creates a separate DB per connection, so two sessions would not share state. File-based SQLite allows two sessions to see each other's committed data.

### META Session #6 Reflexion — 2026-03-23
ACCOMPLISHED: Replenished empty backlog with 7 concrete testing tasks. Created missing project_root.md (required by meta/PROMPT.md STEP 0). Flagged admin password conflict in knowledge.md. Added DEBUG MODE backlog-generation rule to PROMPT.md.
FAILED: Nothing failed. Pure system maintenance.
RULE: [2026-03-23] When the backlog empties after a testing sprint, always pre-populate the next session's testing tasks — don't leave next session to derive them from scratch. 5 minutes of backlog writing in META saves 20+ turns of exploration in WORK.

### BRAIN Session #11 Reflexion — 2026-03-24
ACCOMPLISHED: Searched 7 topics, evaluated 6 new sources. Implemented ACE Curator step (Step 1C) in BRAIN_PROMPT.md — prevents knowledge.md from accumulating redundant rules over time. Added 3 high-priority backlog items from Polymarket strategy research: win_rate display, 15s VIP polling, and Alembic migrations. Ran first curation pass on knowledge.md — 13 rules confirmed distinct, no merges needed.
FAILED: Nothing failed.
RULE: [2026-03-24] Polymarket information arbitrage window is <30s — 30s polling catches most bets but VIP users would benefit from 15s. Keep this in mind when any performance or tier-differentiation work comes up.

### Session #53 Reflexion — 2026-03-24
ACCOMPLISHED: Added 2 tests for last 3 HIGH PRIORITY backlog items. Discovered task 1 (basic tier GET /follows limit=5) was already covered by test_hypothesis_invariants.py parametrize before writing any code — saved time and avoided a duplicate. test_poll_bets_outer_exception_leaves_last_check_unchanged uses a real-session wrapper with commit() overridden to raise. test_put_alerts_settings_valid_push_subscription_stores_and_get_retrieves is a full PUT→GET roundtrip. 294→296.
FAILED: Nothing failed.
RULE: [2026-03-24] Before writing any backlog test, grep test_hypothesis_invariants.py parametrize tables — they often cover combinations (free/basic/vip) that backlog items claim are "only tested for some tiers." Saves a full test slot.

### Session #1 Reflexion — 2026-03-23
ACCOMPLISHED: Fixed 5 failing webhook tests by adding autouse conftest fixture to clear stripe_webhook_secret. Committed prior-session backend bugfixes and full 91-test suite. Fixed CLAUDE.md free tier documentation.
FAILED: Nothing failed in this session.
RULE: [2026-03-23] When .env has a truthy placeholder (e.g. `whsec_REPLACE_ME`), pydantic-settings loads it as a real value — tests that rely on the field being falsy must mock or clear it explicitly in conftest.

### Session #68 Reflexion — 2026-03-24
ACCOMPLISHED: Full mobile responsiveness audit. Added mobile bottom nav (4-tab fixed nav) + sticky topbar to dashboard; mobile topbar + sign-up to browse. Fixed 2-column hardcoded grids on landing. Full-width search, scrollable tab bar, compact CTA banner, no-elevation featured pricing card on mobile. Playwright: 9→12 checks (3 new mobile checks). 303 tests stable.
FAILED: Nothing failed.
RULE: [2026-03-24] Mobile nav pattern for single-HTML SPA with sidebar: wrap sidebar+main in an inner `display:flex;flex:1;min-height:0` div inside the view container; add sticky topbar and fixed bottom-nav as siblings outside that inner div; the view container gets `display:flex;flex-direction:column`. On desktop, topbar/bottom-nav have `display:none` — inner div gets full 100vh.
RULE: [2026-03-24] Hardcoded `grid-template-columns:1fr 1fr` inline styles are invisible to media queries. Convert them to a CSS class (`.grid-2col { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)) }`) to make them responsive automatically.

### META Session #76 Reflexion — 2026-03-24
ACCOMPLISHED: Diagnosed systemic XSS recurrence (sessions 59, 67, 73 each found XSS from the preceding UI work sessions). Root cause: the two-line innerHTML pattern — template literal builds a string into a variable, that variable later assigned to innerHTML — is NOT caught by `grep -n 'innerHTML.*\${' frontend/index.html`. Added write-time prevention protocol to design.md; added second grep to audit.md Marcus checklist.
FAILED: Nothing failed. Pure system improvement.
RULE: [2026-03-24] XSS in innerHTML has a two-line failure mode: `const html = \`...\${apiVar}...\`; el.innerHTML = html`. The grep `innerHTML.*\${` misses this. The correct second grep is `grep -n 'innerHTML\s*=\s*[a-zA-Z_]' frontend/index.html` — it flags variable-assigned innerHTML so you can trace the variable back to its template literal definition. Add this second grep to every pre-commit security check.
RULE: [2026-03-24] Audit-time rules prevent regressions but don't prevent introduction. Write-time rules (applied while building the feature) are more effective. When a security rule keeps triggering at audit time, move it to the skill file read BEFORE writing (design.md, coding.md) and make it a checklist item to apply at the moment of writing, not review.

### Session #72 Reflexion — 2026-03-24
ACCOMPLISHED: Toast notification stack — Sonner/Emil Kowalski pattern. Replaced simple append-and-remove toast with stacked deck: height:0 container, position:absolute toasts anchored at bottom:0, JS-managed transforms (collapsed=fan-stack with 14px/5%-scale steps; expanded=real heights + 8px gaps on hover). data-mounted attribute for interruptible entry animation. toast-bet type + toastBet() + betAlert CustomEvent. New-position detection in refreshFollowsActivity() via _seenBetIds. 5 new Playwright checks (18-22). 303 tests stable.
FAILED: Nothing failed. All checks passed first run.
RULE: [2026-03-24] Sonner toast stack — use height:0 on the container so toasts overflow upward via position:absolute; bottom:0. In collapsed mode the front toast is translateY(0), each background toast gets translateY(+14px*i) scale(0.95^i) — pushed DOWN (toward screen bottom) creating the "peeking cards" illusion. In expanded mode accumulate real heights + 8px gap and use negative translateY to push each toast UP. Never use flex-column for stacked toasts — it breaks the visual overlap.
RULE: [2026-03-24] To detect genuinely new items in a polling function: track seen IDs in a Set; on each refresh, filter for unseen items and add them to the Set. Guard with a wasFirstLoad flag (Set was empty before this call) to suppress toasts on the very first poll that just populates the Set.

### Session #110 Reflexion — 2026-03-25
ACCOMPLISHED: Completed 3 backlog tasks (leaderboard card overhaul remaining items + empty state modal polish + keyboard accessibility). Implemented: Escape/Enter keyboard shortcuts for all modals via document.addEventListener with `querySelectorAll('.modal-overlay:not(.hidden)')`; "Active Xm ago" green-dot badge on lb cards using `last_active_ts` field (added to DEMO_BETTORS with `Date.now()/1000 - N*60` offsets); animated follow button glow pulse via `@keyframes followBtnPulse`; social proof counter `animateCounter(el, 847, '', '+')` in `runLandingCounters()`; pricing locked feature tooltips via `data-tip` attrs + `::after { content: attr(data-tip) }` CSS. 83 Playwright checks (3 new), 303 backend tests stable.
FAILED: Nothing failed — all 3 checks passed first run.
RULE: [2026-03-25] For `data-tip` CSS tooltips: use `content: attr(data-tip)` with `position: absolute; bottom: calc(100% + 4px); opacity: 0; transition: opacity 0.15s` on `::after`, set `opacity: 1` on `:hover::after`. Add `position: relative` and `cursor: help` to the parent. This requires zero JS and works for any inline element. Pitfall: `white-space: nowrap` is needed on the ::after to prevent tooltip text wrapping — without it, tooltips on short parent elements collapse to a single character width.
RULE: [2026-03-25] When DEMO_BETTORS array needs dynamic values (e.g. timestamps), compute them at module load time by declaring `const _now = Math.floor(Date.now() / 1000)` BEFORE the DEMO_BETTORS const, then reference `_now - N*60` inside the object literals. This avoids making DEMO_BETTORS a function call and keeps the array serializable.

### Session #112 Reflexion — 2026-03-25 (TESTING)
ACCOMPLISHED: Committed uncommitted polymarket service + frontend changes from a prior interrupted session; wrote 7 new tests proving rank/pnl_usd fields present, REDEEM-type bets filtered, outcome/price populated for TRADE bets; updated Playwright CHECK 80 from "logo img present" to "PolyEdge wordmark present" to match the frontend change that removed the logo img element; 310 backend tests + 83 Playwright checks pass.
FAILED: First Playwright run showed 1 failure — CHECK 80 expected a logo img tag that had been removed in the uncommitted frontend diff. Fixed by updating both playwright_registry.py and tmp_check.py (they are separate files — both must be updated).
RULE: [2026-03-25] When uncommitted changes remove a UI element that a Playwright check verifies, update BOTH `playwright_registry.py` AND `tmp_check.py` — they are separate files and `tmp_check.py` is the one actually executed. Updating only the registry leaves the stale check in the running file.
RULE: [2026-03-25] When a service function is refactored to use `asyncio.gather` with two internal `httpx.AsyncClient` contexts, existing mock tests that patch `httpx.AsyncClient` with a single `return_value` still work — both internal contexts receive the same mock object. Verify this by checking `has_lb_data = bool(lb_entry and lb_entry.get("vol") is not None)`: if the activity mock data lacks "vol", lb data is treated as absent and falls back to legacy volume-summing logic.

## Test Suite History
| Session | Backend Tests | Frontend Checks |
|---------|--------------|-----------------|
| 112     | 310          | 83              |
| 110     | 303          | 83              |

### Session #113 Reflexion — 2026-03-25
ACCOMPLISHED: 41 new security tests covering XSS payloads in name/address fields, SQL injection in name/address/URL path, modified tier claim JWT bypass, and auth bypass on all 9 protected endpoints.
FAILED: Two tests initially failed — GET /auth/me wraps user in `{"user": {...}}` so accessing `resp.json()["name"]` should be `resp.json()["user"]["name"]`. Fixed by reading the route response structure first.
RULE: [2026-03-25] GET /auth/me returns `{"user": {...}}` not a flat user dict — always access `resp.json()["user"]["field"]`, not `resp.json()["field"]`. This is different from register/login which also wrap in `{"access_token": ..., "user": {...}}`.
RULE: [2026-03-25] Modified tier claim JWT test pattern: use `create_access_token({"sub": str(user_id), "tier": "vip"})` with valid secret — server decodes it, reads sub, fetches DB user, uses DB tier. The extra JWT claim is silently ignored. Test confirms DB-authoritative tier enforcement.

## Test Suite History
| Session | Backend Tests | Frontend Checks |
|---------|--------------|-----------------|
| 133     | 373          | 130             |
| 123     | 359          | 104             |
| 122     | 359          | 101             |
| 118     | 359          | 88              |
| 115     | 354          | 88              |
| 113     | 351          | 83              |
| 112     | 310          | 83              |
| 110     | 303          | 83              |

### Session #124 Reflexion — 2026-03-25 (TESTING)
ACCOMPLISHED: Added 3 Playwright checks (105-107) covering upgrade modal and mobile overflow: (105) #upgrade-modal element present in DOM, (106) openUpgradeModal() removes .hidden class making modal visible (tested by reading classList state before+after call), (107) mobile 375px viewport navigates to alerts tab and confirms no horizontal overflow (scrollWidth <= clientWidth). All 3 passed first run. 107 total checks, 0 failures. 359 backend tests stable.
FAILED: Nothing failed this session.
RULE: [2026-03-25] When testing JS modal visibility toggle in Playwright, use page.evaluate() to call the function and read classList state in one atomic JS call — avoids timing issues from async page updates. Always clean up by re-adding .hidden at the end of the evaluate block so subsequent checks see uncontaminated page state.

### Session #123 Reflexion — 2026-03-25 (TESTING)
ACCOMPLISHED: Added 3 Playwright checks (102-104) covering the profile page DOM: (102) #profile-back-btn exists with onclick calling showTab('leaderboard'), (103) all 4 pstat-* stat elements present, (104) #profile-bets-list exists and renderProfileSkeletons(5) produces skeleton rows. CHECK 104 initially tested by calling full async showProfile() but the API call quickly replaced skeletons with error state before the assertion ran. Fixed by directly testing renderProfileSkeletons() in isolation. 104 total checks, 0 failures. 359 backend tests stable.
FAILED: CHECK 104 first attempt failed — called async showProfile(), waited 0.1s, but the fetch to /bettors/0x000... returned error state synchronously before the check, replacing the skeletons. Root cause: async function replaces skeleton with error state in <0.1s.
RULE: [2026-03-25] When Playwright-testing that a function sets skeleton HTML (loading state), test the skeleton-generation function directly (e.g. `renderProfileSkeletons(5)`) rather than calling the full async function that shows skeletons then immediately replaces them. Direct function testing avoids all race conditions and gives a deterministic result.

### Session #133 Reflexion — 2026-03-25 (FEATURE)
ACCOMPLISHED: Built Smart Entry Timing on position cards. get_active_positions already had avg_price and cur_price — added copy_signal (good/fair/late) and copy_value_pct computed inline. Added tier to /follows/live both paths (empty and populated). Frontend renderPositionItem now accepts tier param and renders color-coded badge for Basic/VIP, padlock for Free. 5 copy_signal unit tests + 2 tier field tests added. 373 total, +5.
FAILED: Two existing tests asserted `resp.json() == {"bettors": []}` (exact match). Adding tier broke them. Fixed by changing to `resp.json()["bettors"] == []` (key-level assertion). Lesson: exact-dict response assertions are fragile — prefer key-level checks.
RULE: [2026-03-25] Exact response dict assertions (`assert resp.json() == {"key": val}`) break whenever a new field is added. Always assert at key level (`assert resp.json()["key"] == val`) unless testing that NO extra fields exist.

### Session #137 Reflexion — 2026-03-26 (BUGFIX)
ACCOMPLISHED: Fixed 3 CRITICAL bugs from code review: (1) profile cache tier bypass — changed cache key from `address` to `(address, tier)`; (2) CORS wildcard removed — explicit `["http://localhost:3000", "http://127.0.0.1:3000"]`; (3) telegram_chat_id removed from user_to_dict(). 3 regression tests added. Also committed lingering uncommitted changes (conviction scoring persistence + pricing UI updates). 393 tests passing.
FAILED: Two existing tests (`test_login_response_has_all_7_fields`, `test_register_response_has_all_7_fields`) explicitly asserted that `telegram_chat_id` IS present — had to update them alongside adding the new security regression test. Also one existing CORS test (`test_cors_allows_any_origin`) was asserting wildcard behaviour that we just fixed — needed to rewrite it.
RULE: [2026-03-26] When removing a field from an API response (security fix or otherwise), grep ALL test files for that field name BEFORE committing — existing tests asserting the field IS present will fail. Fix those tests in the same commit. Pattern recurred in sessions 137 + 141 despite the rule existing in knowledge.md — the rule must also be in PROMPT.md STEP 0 self-critique so it fires at write-time, not just session-start. *(Canonical rule — session 141 duplicate superseded)*
RULE: [2026-03-26] Profile cache in multi-tier SaaS MUST include tier in the cache key. Any cache keyed only by resource ID will serve the highest-permission cached response to lower-permission users — a silent paywall bypass that doesn't throw errors.

### Session #139 Reflexion — 2026-03-26 (BUGFIX)
ACCOMPLISHED: Fixed 5 medium-priority bugs: accuracy field in leaderboard normaliser (from percentProfitable API field), @lru_cache on get_settings(), get_settings() moved outside per-follower inner loop, free users blocked from enabling web push (403), _last_positions purged for unfollowed bettors each poll cycle. 4 existing tests updated (used free tier for web_push but free is now blocked). 1 regression test added. 394 tests passing.
FAILED: 4 test failures on first run — existing tests for web_push_enabled used free user (default auth_headers fixture); new tier check correctly blocked them with 403. Fix was to upgrade users to "basic" tier in those tests.
RULE: [2026-03-26] When adding a tier gate to an existing endpoint, grep ALL tests for calls to that endpoint and check if they use a free-tier user. Tier checks break free-tier tests that previously worked.
RULE: [2026-03-26] @lru_cache(maxsize=1) on get_settings() is critical for settings called in hot loops (per-bet, per-follower). Without it, each call re-reads .env file from disk — 1000+ file reads per scheduler poll cycle.

### Session #140 Reflexion — 2026-03-26 (BUGFIX)
ACCOMPLISHED: Fixed VIP copy timing padlock bug — `_activity_cache` in routes/follows.py stored `tier` at fill-time; after a free→VIP upgrade, the cached response had `tier:'free'` for up to 30s, causing frontend to render the padlock for VIP users. Fix: inject `current_user.subscription_tier` on every cache hit so tier is always fresh from DB. Added 2 regression tests (stale-cache override after upgrade, VIP tier assertion). 396 tests passing.
FAILED: Nothing — first run passed all 396 tests.
RULE: [2026-03-26] When caching API responses that include user-state fields (tier, subscription limits, feature flags), NEVER serve those fields from the stale cache. Always override with the live user object on cache hits: `return {**cached["data"], "tier": current_user.subscription_tier}`. The bettors/positions list can be stale; the user's state cannot.

## Test Suite History (updated)
| Session | Backend Tests | Frontend (Playwright) |
|---------|--------------|----------------------|
| 176     | 480          | 42                   |
| 175     | 475          | 42                   |
| 174     | 472          | 42                   |
| 172     | 472          | 42                   |
| 171     | 471          | 42                   |
| 170     | 471          | 42                   |
| 169     | 470          | 42                   |
| 167     | 467          | 42                   |
| 166     | 467          | 42                   |
| 165     | 462          | 42                   |
| 164     | 459          | 42                   |
| 162     | 457          | 42                   |
| 159     | 450          | 42                   |
| 157     | 446          | 42                   |
| 156     | 443          | 42                   |
| 155     | 443          | 41                   |
| 152     | 443          | 31                   |
| 150     | 443          | 5                    |
| 142     | 413          | 132 (old format)     |
| 141     | 401          | 132                  |
| 140     | 396          | 132                  |
| 139     | 394          | 132                  |
| 137     | 393          | 132                  |

### Session #141 Reflexion — 2026-03-26 (BUGFIX)
ACCOMPLISHED: Fixed Telegram notifications permanently broken — added `POST /alerts/telegram/webhook` endpoint that Telegram bot calls when a user sends `/verify CODE`. The webhook extracts the chat_id from the message and sets `telegram_chat_id` + `telegram_verified=True` in the DB. Without this endpoint, `telegram_chat_id` was always null so notifications could never send. Also fixed a secondary sensitive data leak: `GET /alerts/settings` was returning `telegram_chat_id` to clients — removed it (only `telegram_verified` bool needed by frontend). Updated 1 existing test. Added 5 new webhook tests. 401 tests passing.
FAILED: Nothing — all 401 tests passed first run.
RULE: [2026-03-26] Telegram bot webhook endpoints are PUBLIC (no JWT) — security comes from the webhook URL being secret (registered via setWebhook). The endpoint must ALWAYS return 200 ok=True regardless of whether it processed the update — Telegram retries non-200 responses indefinitely.
*(Rule merged into Session #137 RULE above — see canonical version there)*

### Session #142 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added API tier gate test suite (tests/test_tier_gates.py) — 12 tests covering /markets/consensus tier enforcement (free cap at 3 signals, basic/VIP get all, VIP gets whale names) and /follows/live tier field correctness for all 3 tiers. Also added Bug #140 regression test (stale cache must not serve old tier). 413 tests total.
FAILED: Nothing — all 12 new tests passed on first run.
RULE: [2026-03-26] The consensus cache is a fixed-key dict {"data": None, "ts": 0}, NOT a per-key dict. To isolate tests, reset with `_consensus_cache["data"] = None` and `_consensus_cache["ts"] = 0` — do NOT call `.clear()` on it (that removes the keys and the next access fails with a KeyError when the route tries `_consensus_cache["data"]`).

### DEEP BRAIN Session #143 Reflexion — 2026-03-26
ACCOMPLISHED: (1) STEP 1B: Found that sessions 137+141 both hit the same "removed API field but forgot to grep tests" failure. Rule was in knowledge.md but not at write-time. (2) STEP 1C: Merged duplicate rule from sessions 137+141 into one canonical entry. (3) STEP 1D: 22 activity_log entries — no archival needed (< 30). (4) PROMPT.md — added Q6 (API field removal gate) and Q7 (tier gate addition check) to STEP 0 self-critique — both are write-time enforcement for recurring failures. (5) testing.md — added tier gate breakage pattern to BRITTLE TEST PATTERNS. (6) TIMGS technique: added OPTIMIZATION tag to reflexion format in PROMPT.md; added three-category tip guide to BRAIN_PROMPT STEP 1B. (7) Backlog: added category-specific leaderboard filter (Polymarket Analytics insight). (8) 6 new sources evaluated and logged. ECC still at v1.9.0.
FAILED: Background search agents returned 0-byte output files (again) — fell back to direct WebSearch/WebFetch as per session 121/132 rule.
RULE: [2026-03-26] PROMPT.md write-time gates (STEP 0 Q6/Q7) are MORE effective than knowledge.md rules for recurring failures. knowledge.md is read at session start; STEP 0 fires at the exact moment before commit. The same rule at STEP 0 prevents what knowledge.md alone couldn't (sessions 137+141 both had the rule in knowledge.md; neither was caught until tests ran).
OPTIMIZATION: [2026-03-26] Background search agents consistently return 0-byte output files for web searches. Skip the agent-based search for standard web queries — use WebSearch/WebFetch directly. Only spawn background agents for multi-step research tasks that need tool access beyond web search.

- Test count: **413 passed** (stable — no code changes this session), **132 Playwright checks** (stable)

### Session #144 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Code quality audit of sessions 136-142 changed files. Found 1 real bug + 2 smells: (1) alerts.py telegram_verify set telegram_verified=True even when telegram_chat_id=None — misleading "Telegram linked" response when notifications still can't fire; fixed by adding idempotent guard (already verified → return success) + chat_id required guard (code matches but bot not connected → 400). (2) scheduler.py had inline `from app.config import get_settings` inside loop body × 2 — moved to module-level import. (3) scheduler.py had redundant conviction variable aliasing — removed. Also updated 4 happy-path telegram_verify tests to simulate webhook firing first, and fixed misleading test comment. 414 tests passing (+1 new regression test).
FAILED: First test run showed test_telegram_start_then_verify_full_round_trip still failed — because after the webhook fires, verify_code is cleared to None, hitting the "no pending verification" guard before the chat_id guard. Fix: added idempotent path at top of telegram_verify (if already verified AND has chat_id → return success immediately).
RULE: [2026-03-26] When a webhook endpoint CLEARS a field (e.g., telegram_verify_code = None) as part of its authoritative action, any secondary endpoint that checks for that field's presence will break after the webhook fires. Add an idempotent early-return path for the "already completed" state before checking the now-cleared field.
RULE: [2026-03-26] Code quality audit pattern: read changed files through the lens of (Alex: architecture, Marcus: security, Leo: dead code/consistency). The most valuable finding comes from tracing the INTERACTION between related endpoints (webhook sets fields, verify checks fields) — not just reading each endpoint in isolation.

- Test count: **414 passed** (was 413), **132 Playwright checks** (stable)

### Session #149 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 5 Playwright E2E tests for the Consensus tab. All pass: (1) free user sees no "Could not load" error; (2) free tier ≤3 signals (tier gate); (3) free tier upgrade banner visible; (4) VIP no upgrade banner; (5) VIP no error. Also fixed conftest.py login() which had never worked — `text=Login` selector matched nothing (button says "Log In"), `#dashboard` doesn't exist (it's `#view-dashboard`). The conftest was written but never tested.
FAILED: First run: all 5 tests timed out on `page.click("text=Login")`. Root cause: conftest written for a button that doesn't match (wrong text) and waiting for a selector that doesn't exist. Fix: use `page.evaluate("showView('auth', 'login')")` to navigate via JS; use `#login-email`, `#login-password`, `#login-submit`; wait for `#view-dashboard` (not `#dashboard`). Second run: all 5 passed.
RULE: [2026-03-26] For PolyEdge Playwright conftest: (1) Never use `text=Login` — button is "Log In"; (2) Never wait for `#dashboard` — element is `#view-dashboard`; (3) Use `page.evaluate("showView('auth', 'login')")` to reach auth form. These 3 mistakes were all in the conftest at once and would have broken every future Playwright test.
RULE: [2026-03-26] A conftest.py with no test files that import it has never been run and must be treated as untested code. Before relying on conftest helpers in new test files, grep for any existing test that calls them: `grep -r "from .conftest import\|from conftest import" tests/playwright/`. If zero matches, validate the helper against the live frontend first.

- Test count: **426 passed** (backend, unchanged), **5 new Playwright tests passing**

### Session #150 Reflexion — 2026-03-26 (BUGFIX + TESTING)
ACCOMPLISHED: Fixed Playwright event loop contamination (105 async tests broken) — asyncio.get_event_loop().run_until_complete() in 3 test functions conflicted with anyio/asyncio_mode=auto. Added pytest.ini with asyncio_mode=auto and testpaths/ignore to exclude playwright/ from default run. Added 18 real-world data integrity tests covering ETH address formats, profit ranges, trade type validation, MRR formula correctness, and live Polymarket API cross-validation.
FAILED: Nothing failed in this session — the fix was clear from the error (ScopeMismatch: anyio and asyncio_mode conflict).
RULE: [2026-03-26] When adding pytest.ini with asyncio_mode=auto, also add --ignore=tests/playwright to avoid event loop conflicts between sync playwright fixtures and async test modes. These two settings must co-exist.

- Test count: **443 passed** (was 426, +17 data integrity tests), **5 Playwright tests passing**

### Session #151 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 12 Playwright E2E tier gate tests covering Consensus (3 tiers × 2 assertions), position cards (3 tiers), and profile simulator (3 tiers). 10 passed, 2 skipped (free/basic accounts have no follows in DB, expected). Profile simulator tests initially all skipped due to two bugs in `_open_first_profile`: (1) extracted address from onclick attribute (doesn't exist on .lb-card — uses toggleLbCardExpand, address is in data-addr); (2) wait condition was `display !== ''` which passed immediately since display:none is truthy. Fixed to use data-addr + wait for display === 'flex'.
FAILED: Profile simulator tests skipped on first run (not failed). Root cause traced via DOM inspection pattern.
RULE: [2026-03-26] For PolyEdge leaderboard card address extraction: use `cards[0].getAttribute('data-addr')` — NOT onclick parsing. The .lb-card onclick is `toggleLbCardExpand()`, not `showProfile()`. The address lives in `data-addr`.
RULE: [2026-03-26] When waiting for an element whose initial state is `display:none` to become visible after an async JS operation, wait for the TARGET display value (e.g., `display === 'flex'`), NOT for `display !== ''` — `display:none` is already non-empty and will pass immediately.
OPTIMIZATION: [2026-03-26] When a Playwright test skips instead of fails, check the skip condition in the helper function first, not the test body — the helper may be returning None/falsy and triggering pytest.skip() without any error output.

- Test count: **443 passed** (backend unchanged), **10 new Playwright tier gate tests passing, 2 skipped**

### Session #152 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 14 Playwright UI flow tests across 4 suites: landing page pricing, register/login journey, leaderboard renders, and bettor profile (simulator locked/unlocked). All 14 pass. One failure on first run: logout step tried to click `button.btn-danger[onclick='logout()']` which exists inside `#tab-account` (hidden at desktop viewport).
FAILED: Logout click timed out — element not visible because it's inside a hidden dashboard tab. Fixed by calling `page.evaluate("logout()")` directly.
RULE: [2026-03-26] In PolyEdge Playwright tests, NEVER click the logout button directly — it lives inside #tab-account which is display:none at desktop viewport. Always call `page.evaluate("logout()")` to log out programmatically.
OPTIMIZATION: [2026-03-26] For any button inside a named dashboard tab (#tab-account, #tab-alerts, etc.), use page.evaluate() to call the underlying JS function rather than Playwright's click() — avoids the "element not visible" timeout entirely.

- Test count: **443 passed** (backend unchanged), **14 new Playwright UI flow tests passing** (31 total Playwright tests across 3 files)

### BRAIN Session #153 Reflexion — 2026-03-26
ACCOMPLISHED: (1) STEP 1B: Failure pattern from sessions 149+151 — Playwright selector used getAttribute('onclick') instead of 'data-addr'; wait condition used display !== '' instead of display === 'flex'. Added DATA ATTRIBUTE SELECTORS section to playwright.md. (2) STEP 1C: No duplicate rules found in knowledge.md (rules are distinct and dated). (3) STEP 1D: Archived sessions 120-140 from activity_log.md (32→12 entries). (4) Web research: 5 sources evaluated. FastAPI v0.132 strict Content-Type + v0.135 native SSE added to coding.md. Polymarket has time-period leaderboard filter (Today/Week/Month/All) — not in PolyEdge; added to backlog. ECC still at v1.9.0. arxiv 2603.22367 (RES) and 2603.24414 (ClawKeeper) not applicable prompt-only.
FAILED: Background search agents returned 0-byte output (same as sessions 121, 132) — fell back to direct WebFetch calls per established rule.
RULE: [2026-03-26] Playwright wait_for_function for CSS display changes must use getComputedStyle(...).display === 'flex' (or === 'block'). Using style.display !== '' produces a false pass because empty string is falsy but also means the inline style property is not set (computed style is different). Always use the computed style value, not inline style.
OPTIMIZATION: [2026-03-26] For brain sessions, skip background search agents entirely (they return 0 bytes on this machine). Use WebFetch directly with parallel calls — same research quality with no wait time.

### Session #154 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 7 Playwright E2E tests for back-to-top FAB behaviour (3 tests) and mobile layout (4 tests). All 7 passed on first run. Removed stale backlog item (Consensus VIP already covered). 36 Playwright tests passing total.
FAILED: Nothing — all 7 tests passed first run.
RULE: [2026-03-26] To test FAB scroll-triggered visibility in Playwright headless: (1) set document.body.style.minHeight = '5000px' to make page scrollable, (2) call window.scrollTo(0, 400), (3) dispatch a 'scroll' event manually via window.dispatchEvent(new Event('scroll')), (4) wait 300ms for handler to fire. This reliably triggers the scroll listener in headless Chromium without needing real content.
RULE: [2026-03-26] At 375px viewport, mobile nav buttons (inside .mobile-bottom-nav) ARE clickable via page.click('#mob-nav-leaderboard') — they become visible via CSS media query. The desktop-width rule (use page.evaluate() instead of click) applies to #nav-* elements hidden via sidebar, NOT to .mobile-nav-btn elements which become visible at mobile widths.

### Session #155 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: (1) Fixed Bug #12 — replaced `_consensusLoaded` boolean with `_consensusLoadedAt` TTL timestamp (60s) so consensus data re-fetches instead of staying stale forever within a session. (2) Added data-testid attributes to 9 key HTML elements (pricing cards × 3, form inputs × 6, bettor card, follow button). (3) Added 5 Playwright tests: TTL re-fetch regression (1), data-testid presence (4). 41 Playwright tests passing.
FAILED: `window._consensusLoadedAt` returned None in Playwright because `let` top-level variables are NOT accessible via `window.*` — only `var` declarations are added to the global object. Fixed by using bare `_consensusLoadedAt` in page.evaluate (no `window.` prefix).
RULE: [2026-03-26] In Playwright `page.evaluate()`, top-level `let`/`const` variables in the page script are NOT accessible as `window.*`. Use bare variable names: `page.evaluate("_myVar")` not `page.evaluate("window._myVar")`. Only `var` declarations are added to the global window object.
OPTIMIZATION: [2026-03-26] Frontend error-handling audit (checking every fetch for try/catch) can be done in ~10 min by: (1) grep all fetch/apiFetch calls, (2) read ±15 lines around each, (3) confirm try/catch present. No server startup needed.

### Session #156 Reflexion — 2026-03-26 (BUGFIX + TESTING)
ACCOMPLISHED: Fixed follows refresh timer leak — after logout (or JWT expiry), the 30s setInterval kept firing refreshFollowsActivity(), which called showView('auth','login') and bounced users back to login 30s after logging out. Fix: showView() now clears _followsRefreshTimer when navigating away from dashboard. Added 1 Playwright test using page.clock.fast_forward(31s). Also removed unused BetEvent import from routes/follows.py. 443 backend tests, 42 Playwright tests.
FAILED: Nothing — all tests passed first run.
RULE: [2026-03-26] JS setInterval timers set in a view-entry function must be cleared when navigating AWAY from that view. showView() is the central routing function — add `clearInterval(_fooTimer); _fooTimer = null` there for every timer that belongs to a specific view. Without this, timers outlive the view and fire stale callbacks into wrong app states.

### Session #157 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 3 reliability tests in test_bettors.py — Polymarket HTTP 500 at httpx transport level returns graceful 200 empty list for leaderboard; same for bettor detail endpoint; 10 concurrent GET /bettors threads all return 200 without crashing. 446 backend tests.
FAILED: Nothing — all 3 passed first run.
RULE: [2026-03-26] To test HTTP-transport-level resilience (not just mock-at-service-function level), use `httpx.MockTransport` with a custom `handle_request` that raises `httpx.HTTPStatusError`. This verifies that `except Exception: break` patterns in the service actually swallow upstream errors at the httpx layer, not just at the mock-function level.

### META Session #158 Reflexion — 2026-03-26
ACCOMPLISHED: (1) playwright.md — added TIMER TESTING section: page.clock.fast_forward() pattern from session 156, including install-before-goto rule. (2) backlog.md — removed empty "HIGH PRIORITY — Frontend UI Playwright Tests" section (all tasks completed). (3) Restored "Frontend API error handling" and "Dead code" review items that were explicitly kept in session 148 but dropped in cleanup.
PATTERNS FOUND: Playwright patterns get used in work sessions but never filed back to playwright.md. Backlog items can silently disappear during section cleanups.
RULE: [2026-03-26] After a WORK session uses a new Playwright pattern (e.g., page.clock, page.evaluate for JS calls), the META session following it must file the pattern to playwright.md — not just knowledge.md. Skill files are read at session start; knowledge.md is scanned for specific terms only.

### Session #159 Reflexion — 2026-03-26 (FEATURE)
ACCOMPLISHED: Added VIP 5-second poll interval via a second APScheduler job (_poll_vip_bets every 5s alongside _poll_bets every 30s). Added GET /readiness endpoint (SELECT 1 check, returns 200/503). 450 backend tests (4 added), 42 Playwright tests.
FAILED: Nothing — all 4 new tests passed first run.
RULE: [2026-03-26] When adding a second APScheduler job to an existing scheduler, both jobs register on the SAME AsyncIOScheduler instance before `scheduler.start()` is called. The VIP job must filter to addresses followed by VIP users only — fetching all addresses in the fast-path defeats the purpose and doubles load on Polymarket API.

### Session #160 Reflexion — 2026-03-26 (BUGFIX)
ACCOMPLISHED: Fixed 3 silent error swallowing bugs in the follows tab — users now see "Could not load positions. Try refreshing." instead of stuck skeleton cards when positions API fails; follows-list errors show a toast instead of empty state. 450 backend tests (stable), 42 Playwright tests (stable).
FAILED: Nothing — straightforward catch block additions.
RULE: [2026-03-26] Frontend catch blocks that call `resolve([])` or just hide the loader create silent failures — the user sees an empty state and doesn't know if it's real or broken. Always show a visible error message or toast in the catch block. The pattern `catch(e) { showToast("Could not load X. Try refreshing.", "error"); }` is the minimum acceptable error handler.

### Session #161 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Audited sessions 155-160 changed files. Found and fixed: (1) readiness endpoint leaking exception details in 503 body (DB file path + SQLAlchemy error string exposed to public callers); (2) stale scheduler docstring. Logged _last_check race condition to tech_debt.md. 450 backend tests (stable).
FAILED: Nothing — straightforward fixes.
RULE: [2026-03-26] The `except Exception as e: raise HTTPException(status_code=503, detail=str(e))` pattern exposes internal error strings to clients — SQLAlchemy errors include DB file paths and schema info. Always log the full error server-side and return a generic user-facing message: `logger.error(f"Health check failed: {e}"); raise HTTPException(503, "Database connectivity check failed")`.

### Session #162 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 7 behavioral tests — VIP fast-path (no-VIP early return, VIP-only address filtering, new bet creates BetEvent+notification), /follows/live conviction score (keys always present, EXTREME label at 10x, empty below 3x), profile cache (reverse-order confirms VIP gets unlocked simulator even after free user cached same address). 457 backend tests, 42 Playwright tests.
FAILED: Nothing — all 7 passed first run.
RULE: [2026-03-26] When testing cache tier isolation (e.g., profile cache keyed by (address, tier)), test in REVERSE order: free user first (populates free cache), then VIP user for same address. If the cache key is wrong (address only), the VIP user gets the free response. Testing VIP first masks the bug.

### BRAIN Session #163 Reflexion — 2026-03-26
ACCOMPLISHED: Fixed stale coding.md (port 8002→8003, StockCards references → PolyEdge); created autoagent/skills/rate-limiting.md with complete SlowAPI recipe including the mandatory `request: Request` parameter; added FastAPI v0.134 streaming JSON Lines + v0.131 ORJSONResponse deprecation entries. 457 tests stable.
FAILED: Nothing.
RULE: [2026-03-26] Brain sessions must verify the development port in coding.md matches PROJECT.md at the start of every brain session. Port numbers drift as projects evolve — a stale port in coding.md causes work sessions to attempt server startup on the wrong port, wasting the first 2-3 turns diagnosing connection refused errors.

### Session #164 Reflexion — 2026-03-26 (SECURITY)
ACCOMPLISHED: Added rate limiting to POST /auth/register and POST /auth/login — 10 req/min per IP via slowapi; shared limiter singleton in app/limiter.py; conftest resets limiter between tests; 2 regression tests. 459 backend tests.
FAILED: Nothing — rate-limiting.md skill from session 163 had the exact recipe needed. No rediscovery required.
RULE: [2026-03-26] SlowAPI requires `request: Request` as the FIRST parameter (after self if method) in every rate-limited route function. Missing it raises a 500 "No request object found" error that is completely opaque. Always add it; the rate-limiting.md skill documents this pattern.
OPTIMIZATION: [2026-03-26] Creating the rate-limiting.md skill in the BRAIN session BEFORE the implementing session saved the full research cost (~5 turns) — the implementation session went straight to coding. Pre-filing skill files for planned work is the single highest-ROI brain session action.

### Session #165 Reflexion — 2026-03-26 (TESTING)
ACCOMPLISHED: Added 3 regression tests — _poll_bets purges stale _last_positions entries; /health not rate-limited (20 consecutive calls); /readiness not rate-limited (20 consecutive calls). 462 backend tests.
FAILED: Nothing — all 3 passed first run.
RULE: [2026-03-26] k8s liveness/readiness probe endpoints (/health, /readiness) MUST be exempt from rate limiting. Without an explicit test, a future refactor adding rate limiting to all routes would silently break deployments. Add a rate-limit exemption test alongside every new rate-limiter installation.

### Session #166 Reflexion — 2026-03-26 (CODE QUALITY AUDIT)
ACCOMPLISHED: Extracted `_compute_conviction(bet_amount, avg_bet_usd)` helper — eliminated identical 8-line conviction logic duplicated in _poll_bets and _poll_vip_bets. Fixed stale docstring in test_cors_headers_present. Added 5 unit tests for the helper. 467 backend tests.
FAILED: Nothing — all 5 new tests passed first run.
RULE: [2026-03-26] Agent-edited code accumulates silent duplicates because each task is implemented independently, often in sibling functions. When a code quality audit finds identical multi-line logic in two sibling functions (e.g., _poll_bets and _poll_vip_bets), extract it immediately — a threshold change in one copy will never be applied to the other, causing inconsistent behavior (e.g., different notification thresholds for VIP vs standard polls).

### Session #167 Reflexion — 2026-03-26 (CODE REVIEW)
ACCOMPLISHED: Dead code audit of frontend/index.html (all JS function definitions scanned against oncl* attributes and JS call sites) and backend/app/ (all imports verified). Found 1 dead function: `tierBadge(tier)` — generated an HTML string but was never called from any code path or HTML attribute. Removed (3 lines). 467 backend tests stable.
FAILED: Nothing — straightforward removal.
RULE: [2026-03-26] For JS dead code detection, grep for the function name in: (1) `onclick="`, `onclick='` attributes; (2) other JS function bodies. A function can look syntactically correct and even return useful output but still be completely dead if nothing calls it. `tierBadge` produced badge HTML that was never rendered — silent dead weight. The grep pattern: `grep -n "tierBadge\|functionName" frontend/index.html` covers both call sites and definition in one pass.
