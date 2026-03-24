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

## Test Infrastructure

- Tests live in `backend/tests/`
- Run with: `cd backend && py -m pytest tests/ -v`
- conftest.py: in-memory SQLite, autouse `setup_db`, `db`, `client`, `registered_user`, `auth_headers` fixtures
- autouse `clear_stripe_webhook_secret` fixture in conftest.py zeroes stripe_webhook_secret so webhook tests work (STRIPE_WEBHOOK_SECRET=whsec_REPLACE_ME in .env was causing failures)
- Test count: **194 passed** (as of 2026-03-24, session 23 added 5 coverage-gap tests)
- Frontend follows+alerts: **16/16 Playwright checks pass** (as of 2026-03-24, session 9)
- Frontend smoke: **7/7 Playwright checks pass** (as of 2026-03-23, session 3)

## Known Issues

- Stripe payments blocked — price IDs not configured, restricted key lacks product permissions
- Telegram notifications not configured (TELEGRAM_BOT_TOKEN = REPLACE_ME)
- No git remote configured — `git push` will fail (commits are local only)

## Session Reflexions

### Session #23 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests for previously untested async polymarket service functions and auth email lowercasing. All 5 passed first run. 189→194.
FAILED: Nothing failed. Full suite showed the known ordering flake on test_tampered_signature_returns_401 (passes in isolation — documented in Session #15).
RULE: [2026-03-24] Polymarket async service functions (get_bettor_profile, get_recent_bets, get_live_trades, get_leaderboard) had zero direct unit tests despite being the core data pipeline. When testing async httpx functions use AsyncMock with __aenter__/__aexit__ returning mock_client; for multi-call pagination tests use side_effect list on .get(). For email auth tests, register with lowercase then login with UPPERCASE to verify the lowercasing guard.

### Session #22 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 coverage-gap tests. Gaps found by reading every route's branches vs. existing tests: _profile_cache hit was the only cache-hit path not tested (leaderboard + trades were); past_due and unpaid statuses in _handle_subscription_change were untested; subscription.updated basic upgrade had no test (only VIP); admin/stats bet_events fields were presence-checked but never value-verified; POST /follows response body only asserted bettor_address, not the other 3 fields. All 5 passed first run. 184→189.
FAILED: Nothing failed.
RULE: [2026-03-24] After testing all caches for hit paths, audit each cache separately — _profile_cache (keyed by address string), _leaderboard_cache (keyed by sort+period+limit), and _trades_cache (flat dict) have different key structures. Testing one cache type does not cover another. Similarly, for webhook event handler branches, list all status strings in the code (canceled, unpaid, past_due, active) and verify each has at least one test.

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
RULE: [2026-03-24] GET /bettors/{address} has a module-level _profile_cache dict — must call `_profile_cache.clear()` at test start to force the uncached code path, same pattern as _trades_cache. Missing this causes the mock to never be called.

### Session #13 Reflexion — 2026-03-24
ACCOMPLISHED: Added 5 tests covering previously untested error paths: portal Stripe 502, leaderboard API 502, recent trades API 502, and recent trades limit boundaries (422 for limit<5 and limit>50). 153 → 158 tests.
FAILED: Nothing failed. Cache isolation concern was caught in self-critique: trades_cache (30s TTL) would have served a cached 200 to the error test if run after test_recent_trades_public. Fixed by resetting _trades_cache to {data: None, ts: 0} at test start. Leaderboard error test uses time_period=day to avoid key collision with existing profit_month_50 cache entry.
RULE: [2026-03-24] Module-level caches in bettors.py (_leaderboard_cache, _trades_cache) persist across tests in the same pytest session. Tests that need to exercise the uncached path must either (a) use a unique query param combo not seen by earlier tests, or (b) directly reset the cache dict to {data: None, ts: 0} at the start of the test. Missing this causes the mock to never be called and the test to return 200 instead of the expected error.

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

### Session #1 Reflexion — 2026-03-23
ACCOMPLISHED: Fixed 5 failing webhook tests by adding autouse conftest fixture to clear stripe_webhook_secret. Committed prior-session backend bugfixes and full 91-test suite. Fixed CLAUDE.md free tier documentation.
FAILED: Nothing failed in this session.
RULE: [2026-03-23] When .env has a truthy placeholder (e.g. `whsec_REPLACE_ME`), pydantic-settings loads it as a real value — tests that rely on the field being falsy must mock or clear it explicitly in conftest.
