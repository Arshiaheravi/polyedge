# Knowledge Base

## Windows-Specific Rules (CRITICAL — read before any subprocess or Playwright work)

- RULE: [2026-03-24] This project runs in bash (git bash), NOT Windows CMD. NEVER use CMD syntax: no `del`, no `start /B`, no `%a` variables, no `> nul`. These cause "B:/ drive not found" errors and console pop-ups.
- RULE: [2026-03-24] In bash use `rm -f file` not `del file`. Use `> /dev/null 2>&1` not `> nul 2>&1`.
- RULE: [2026-03-24] To launch background processes in bash use `python -m uvicorn ... &` not `start /B`. Capture PID with `$!` then kill with `kill $PID` when done.
- RULE: [2026-03-24] For Playwright, always pass `chromium.launch(headless=True, args=["--disable-gpu", "--no-sandbox"])` — prevents any visible browser or window.
- RULE: [2026-03-24] To kill a port in bash on Windows: `cmd /c "for /f 'tokens=5' %a in ('netstat -aon ^| findstr :PORT') do taskkill /F /PID %a" > /dev/null 2>&1` — wrap CMD-only commands inside `cmd /c "..."` when you truly need them.

---

## Project Facts (pre-seeded)

- Backend runs on port **8002** (not 8001, not 8000)
- Frontend runs on port **3000**
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
- Polymarket API rate limit: **60 requests per minute** sliding window. Cloudflare queues rather than hard-rejects. PolyEdge's 30s poll of ~100 bettor addresses (≤100 req/30s = ≤200 req/min per bettor address round) is near the limit at scale.
- **Polymarket WebSocket endpoints exist**: `/v1/ws/markets` and `/v1/ws/private` — real-time price/trade/orderbook streams up to 10 instruments. Switching from polling to WebSocket would reduce API calls and detect bets instantly instead of waiting up to 30s. Key feature for VIP tier differentiation.

## Test Infrastructure

- Tests live in `backend/tests/`
- Run with: `cd backend && py -m pytest tests/ -v`
- conftest.py: in-memory SQLite, autouse `setup_db`, `db`, `client`, `registered_user`, `auth_headers` fixtures
- autouse `clear_stripe_webhook_secret` fixture in conftest.py zeroes stripe_webhook_secret so webhook tests work (STRIPE_WEBHOOK_SECRET=whsec_REPLACE_ME in .env was causing failures)
- Test count: **296 passed** (as of 2026-03-24, session 53 — added scheduler outer exception + push subscription roundtrip tests)
- Frontend follows+alerts: **16/16 Playwright checks pass** (as of 2026-03-24, session 9)
- Frontend smoke: **7/7 Playwright checks pass** (as of 2026-03-23, session 3)

## Known Issues

- Stripe payments blocked — price IDs not configured, restricted key lacks product permissions
- Telegram notifications not configured (TELEGRAM_BOT_TOKEN = REPLACE_ME)
- No git remote configured — `git push` will fail (commits are local only)

## Session Reflexions

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
