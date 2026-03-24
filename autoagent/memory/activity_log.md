# Activity Log
*(Sessions 1-20 archived — see activity_log_archive.md)*

## 2026-03-24 20:00 — BRAIN SESSION (Session 51)
RESEARCHED: FastAPI notification architecture 2026, Polymarket API rate limits, APScheduler vs ARQ vs Celery, pytest parametrize best practices 2026, autonomous agent memory taxonomy (arxiv 2603.07670), coding agents as long-context processors (arxiv 2603.20432), new arxiv March 2026 agent papers
DOWNLOADED: No new skill files (patterns extracted directly into existing skill files)
IMPLEMENTED: (1) pytest.param(id=...) pattern added to skills/testing.md — named IDs for parametrize produce readable failure output; (2) First actual activity_log archival executed — sessions 1-20 moved to activity_log_archive.md, main log trimmed to sessions 21-50; (3) Polymarket API rate limits added to knowledge.md as project fact
BACKLOGGED: SSE notification endpoint for browser real-time alerts; ARQ scheduler upgrade path for multi-server scaling
SOURCES: 8 new sources logged in brain/sources.md

## 2026-03-24 19:00 — TESTING (Session 50)
DONE: Added 2 backlog tests — test_poll_bets_last_check_updated_after_poll (verifies _last_check is set to check_time after a successful poll); test_delete_follow_with_multiple_follows_removes_only_correct_one (2 follows, delete one, verify other remains). Also discovered sort=accuracy and sort=volume tests already existed, so backlog item was already covered. 293→295 tests stable. Added META audit task + 3 new HIGH PRIORITY tasks to backlog.
IMPACT: _last_check update path is now locked in — a regression where the checkpoint isn't advanced would cause all bets to be re-processed on every poll. Selective delete is verified — a cascade delete regression would be caught immediately.
FILES: backend/tests/test_scheduler.py, backend/tests/test_follows.py

## 2026-03-24 18:00 — TESTING (Session 49)
DONE: Fixed flaky JWT tamper test (_tamper_token was changing padding-only bits A↔B on last base64url char, leaving HMAC identical → token verified as valid non-deterministically); added 3 backlog tests: scheduler multi-bet loop (2 bets per address → 2 BetEvents), GET /follows unknown tier returns limit=0, checkout 502 when Stripe price ID unconfigured. 290→293 tests stable.
IMPACT: Eliminates a test that randomly passed/failed depending on wall-clock time (last sig char in A-P range = same decoded bytes when flipped). Closes all 3 remaining HIGH PRIORITY backlog items.
FILES: backend/tests/test_security.py, backend/tests/test_scheduler.py, backend/tests/test_follows.py, backend/tests/test_payments.py

## 2026-03-24 10:00 — TESTING (Session 48)
DONE: Added 3 edge-case tests — get_active_positions dict response returns [], unknown subscription tier gets 403, /admin/stats full nested type contract (users/follows/bet_events/mrr_estimate types). 287→290 tests stable.
IMPACT: Closes last 3 backlog HIGH PRIORITY testing gaps. Any regression where non-list API responses crash, unknown tiers bypass the follow limit, or /admin/stats drops a nested field will now be caught immediately.
FILES: backend/tests/test_polymarket_service.py, backend/tests/test_follows.py, backend/tests/test_admin.py

## 2026-03-24 17:00 — TESTING (Session 47)
DONE: Added 6 response-contract and edge-case tests — 281→287 tests stable. Tests: login/register 7-field user_to_dict contract; bettor detail null-profile returns 200 not 404; leaderboard limit param is forwarded to service; portal works when stripe_subscription_id=None (only customer_id matters); webhook unknown event returns 200 not 502. Replenished backlog with 3 new HIGH PRIORITY tasks.
IMPACT: Locks in the full auth response contract (all 7 user fields) across register AND login, preventing silent regressions. Documents that bettor detail returns null profile (not 404) for unknown addresses. Confirms portal route only requires customer_id.
FILES: backend/tests/test_auth.py, backend/tests/test_bettors.py, backend/tests/test_payments.py

## 2026-03-24 16:00 — META SESSION (Session 46)
IMPROVED: (1) Added "BEFORE ADDING ANY TEST — CHECK FOR EXISTING TEST FILES" section to testing.md — explicit grep commands to check for dedicated test files and duplicate test names before writing any test. (2) Added spec-first status code rule to testing.md RULES — "verify expected HTTP status code against PROJECT.md spec, not current code" with the session 45 409 example. (3) Replenished backlog with 3 new HIGH PRIORITY testing tasks: GET /payments/portal no subscription, POST /payments/webhook unknown event, POST /auth/register full response contract.
PATTERNS FOUND: (1) Session 42 added /follows/live tests to test_follows.py without checking test_follows_live.py existed — cost a full META session 45 to find+remove. The RULE was added to knowledge.md but not testing.md, where WORK agents actually read before coding. (2) Session 45 found 409 vs 400 spec violation masked by test written to match code — same issue: RULE in knowledge.md but not testing.md RULES section (the read-first list).
PREDICTED IMPACT: Future WORK agents reading testing.md before writing tests will see the "check existing files" step immediately — prevents duplicate tests across files. The spec-first rule prevents tests locking in wrong status codes. Backlog now has 6 HIGH PRIORITY tasks (3 existing + 3 new) — enough for 1-2 more WORK sessions without replenishment needed.

## 2026-03-24 15:00 — META/AUDIT (Session 45)
DONE: Code quality audit (sessions 39-44) — found and fixed 3 issues: (1) register duplicate-email returned 400 instead of 409 (PROJECT.md spec) — fixed route + updated 3 test assertions; (2) test_follows.py had 2 duplicate /follows/live tests already covered in test_follows_live.py — removed; (3) test_notifications.py mid-file module imports moved to top. Also resolved 3 backlog tasks: sms/verify and telegram/verify full response contracts added to test_alerts.py; user.name added to test_register_success assertion. 281 tests stable.
IMPACT: Fixed a real API spec violation (400 vs 409 for duplicate registration) that could confuse API consumers. Removed test noise from duplicate tests. Cleaned up import hygiene. All 3 HIGH PRIORITY backlog tasks cleared.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_follows.py, backend/tests/test_notifications.py, backend/tests/test_alerts.py

## 2026-03-24 14:00 — TESTING (Session 44)
DONE: Added 3 branch-coverage tests — (1) test_login_empty_password_returns_401: empty "" passes LoginRequest Pydantic validation (no min_length) but verify_password("", hash) returns False → 401, not 500 or 422; (2) test_follows_live_all_bettors_raise_returns_three_entries_with_empty_positions: VIP with 3 follows where all get_active_positions calls raise — asyncio.gather error path must still return 3 bettor entries each with active_positions=[], not crash or empty list; (3) test_put_alerts_settings_invalid_push_subscription_returns_422: "not_valid_json" string hits json.loads() guard in PUT /alerts/settings route → 422, confirms the validation gate added in session 5 still works. 278→281 tests.
IMPACT: Three previously untested defensive paths locked in — the login empty-password path is a symmetry gap vs RegisterRequest (which enforces min_length=1); the all-fail gather test is the multi-failure case that wasn't exercised by the existing single-failure test; the PUT JSON validation guard prevents a re-introduction of the session 5 crash where invalid push_subscription would later crash GET /alerts/settings.
FILES: backend/tests/test_auth.py, backend/tests/test_follows_live.py, backend/tests/test_alerts.py

## 2026-03-24 13:00 — TESTING (Session 43)
DONE: Fixed 2 bugs and added 4 tests — (1) LoginRequest.password was missing max_length=128 (symmetry gap vs. RegisterRequest — same bcrypt DoS vector); fixed with Field(..., max_length=128); (2) remove_follow did not evict _activity_cache — after unfollowing, /follows/live would return stale cached bettors until TTL expired (30s); fixed with _activity_cache.pop(current_user.id, None); (3) test_login_password_too_long_returns_422 (129-char → 422); (4) test_login_password_at_max_length_succeeds (128-char boundary → 200); (5) test_delete_follow_clears_activity_cache (DELETE evicts cache, subsequent /follows/live returns {"bettors": []}); (6) test_follows_live_cache_hides_second_follow_within_ttl (confirms cache is real — 2nd follow invisible until TTL expires). 274→278 tests.
IMPACT: Two real bugs fixed — login DoS gap (unbounded password input to bcrypt) and stale live feed after unfollow (users would see removed bettors for up to 30s). Four tests lock in both fixes as non-regressing contracts.
FILES: backend/app/routes/auth.py, backend/app/routes/follows.py, backend/tests/test_auth.py, backend/tests/test_follows_live.py

## 2026-03-24 12:00 — TESTING (Session 42)
DONE: Added 6 branch-coverage tests — (1) add max_length=128 to RegisterRequest.password (bcrypt DoS: unbounded input makes hashing arbitrarily slow); (2) test_register_password_too_long_returns_422 (10000-char → 422); (3) test_register_password_at_max_length_is_accepted (128-char → 201, boundary); (4) test_follows_live_no_follows_returns_empty_bettors_list ({"bettors": []} contract, not bare array); (5) test_follows_live_response_shape_per_bettor (address/name/followed_at/active_positions keys present); (6) test_vip_tier_can_add_six_plus_follows (VIP: 6 follows all 201, tier="vip", limit=999999 in GET /follows); (7) test_admin_stats_zero_users_all_counts_zero (empty DB: all 6 fields = 0/0.0). Also skipped the "scheduler freshness filter" backlog task — it was already covered by test_poll_bets_skips_old_bets added in session 2. 268→274 tests.
IMPACT: Closes a real bcrypt DoS vector (10000-char passwords were accepted and slowly hashed). /follows/live had zero tests — 2 contract tests now lock in the response shape and cache behavior. VIP tier cap was untested — confirms unlimited follows work. Admin zero-users guard confirmed.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_follows.py, backend/tests/test_admin.py

## 2026-03-24 11:00 — DEEP BRAIN SESSION (Session 41)
DONE: Curated knowledge.md (merged duplicate Session #13/#14 cache isolation rules), fixed stale session references in techniques.md, implemented 3 improvements: (1) backlog low-water-mark rule in PROMPT.md step 3 — when HIGH PRIORITY drops below 2, generate 3+ tasks before closing; (2) symmetry audit rule in testing.md — when gap found in function A of module M, immediately check sibling functions for same gap; (3) activity_log archival rule in BRAIN_PROMPT.md step 1D — archive oldest 20 entries when count exceeds 30. Searched 7 topics: autonomous agent best practices, self-improvement, agent reliability patterns, FastAPI testing, fintech copy-trading, context compression, Claude Code skills. Replenished 5 HIGH PRIORITY testing tasks in backlog.
IMPACT: Three systemic improvements fix patterns that caused wasted sessions — backlog empties were burning 4 META sessions; symmetry gap cost a full extra session for send_sms after send_telegram; knowledge.md had a duplicate rule adding noise. New backlog tasks prevent next WORK session from spending turns on discovery.
FILES: autoagent/PROMPT.md, autoagent/brain/sources.md, autoagent/brain/techniques.md, autoagent/memory/knowledge.md, autoagent/meta/BRAIN_PROMPT.md, autoagent/skills/testing.md

## 2026-03-24 10:00 — TESTING (Session 40)
DONE: Added 5 branch-coverage tests — (1) send_sms returns False when any credential is empty (early-return guard); (2) send_sms returns True when Twilio HTTP succeeds (the only success path, was untested); (3) send_sms returns False on HTTP exception (exception handler path); (4) scheduler passes phone_number and sms_enabled=True to dispatch_bet_notification for VIP user with phone_verified=True and sms_enabled=True (SMS dispatch path was fully untested); (5) dispatch_bet_notification does NOT call send_sms when phone_number=None even with sms_enabled=True and VIP tier (phone_number guard). 263→268 tests.
IMPACT: Closes all three send_sms branches (same gap as send_telegram had in session 39 — only False paths were tested). The scheduler SMS dispatch path is the last untested notification channel combination — now all four combinations (telegram-only, web_push-only, both, SMS for VIP) are locked in. The phone_number=None guard prevents a regression where dispatch silently tries to SMS without a phone number.
FILES: backend/tests/test_notifications.py, backend/tests/test_scheduler.py

## 2026-03-24 09:00 — TESTING (Session 39)
DONE: Added 5 branch-coverage tests — (1) send_telegram returns True when HTTP call succeeds (only the early-return False paths were tested before); (2) scheduler dispatch exception is caught and loop continues, event.notified=True still set (the try/except around dispatch_bet_notification was untested); (3) POST /alerts/telegram/start response shape includes all 3 keys: code, instructions, bot_link (only code was asserted); (4) POST /alerts/telegram/verify accepts lowercase code via .upper() normalization; (5) PUT /alerts/settings response shape includes telegram_verified and phone_verified fields. 258→263 tests.
IMPACT: Five previously untested branches now locked in — send_telegram success path, scheduler resilience to notification failures, and three response shape contracts. The scheduler dispatch exception test is particularly important: confirms that a single user's notification failure never prevents other users from receiving notifications or the event from being marked notified.
FILES: backend/tests/test_notifications.py, backend/tests/test_scheduler.py, backend/tests/test_alerts.py

## 2026-03-24 — DE-SLOPPIFY AUDIT (Session 38)
DONE: Ran De-Sloppify audit across sessions 32–37 changed files — found and fixed 3 issues: (1) dead module-level constant BETTOR_C in test_follows.py never used in any test; (2) test_list_follows_basic_tier_reports_tier_and_limit and test_list_follows_vip_tier_reports_tier_and_limit were exact duplicates of the parametrized test_follows_always_returns_tier_and_limit invariant in test_hypothesis_invariants.py; (3) _activity_cache in routes/follows.py grows unboundedly (no eviction, logged to tech_debt.md). 260→258 tests.
IMPACT: Removes test duplication that will accumulate into noise — when both parametrized invariants AND individual tests exist for the same logic, the individual tests create false confidence that branches are "double-covered" while actually reducing the signal-to-noise ratio for test failures. Dead vars are micro-clutter that slows down future readers.
FILES: backend/tests/test_follows.py

## 2026-03-24 07:00 — TESTING (Session 37)
DONE: Added 5 contract and dispatch tests — (1) DELETE /follows 204 response body is empty bytes; (2) DELETE /follows 404 detail is exactly "Follow not found"; (3) POST /payments/checkout response key set is exactly {"checkout_url"}; (4) Scheduler: user with BOTH telegram_enabled AND web_push_enabled fires both channels simultaneously (dispatch gets both telegram_chat_id and push_subscription_json set); (5) Scheduler: web_push-only path (telegram_enabled=False) sets push_subscription_json but telegram_chat_id=None. Two backlog items (invoice.payment_failed, sort=volume) were already covered by prior sessions — grepped and skipped. 255→260 tests.
IMPACT: Response shape contracts for DELETE and checkout are now locked in — any future change that adds unexpected keys or returns wrong body will be caught. Dual-channel scheduler dispatch was the only remaining untested notification path; now all single and combined channel combinations are covered.
FILES: backend/tests/test_follows.py, backend/tests/test_payments.py, backend/tests/test_scheduler.py

## 2026-03-24 06:00 — META SESSION (Session 36)
IMPROVED: (1) Fixed stale "stockcards" project references in skills/testing.md PATCHING section — replaced with PolyEdge-specific app.* module paths; any WORK agent following the old examples literally would use wrong patch targets and waste turns diagnosing failures. (2) Replenished empty HIGH PRIORITY testing backlog with 5 concrete tasks: Stripe invoice.payment_failed event, GET /bettors sort=volume, DELETE /follows response shape, POST /payments/checkout response shape, scheduler dual-channel dispatch (telegram + web_push simultaneously).
PATTERNS FOUND: (1) Session 26 fixed the IMPORT CHECK in testing.md but left the PATCHING section with stale stockcards.* references — partial fix pattern. (2) Backlog HIGH PRIORITY section is empty after sessions 32-35 cleared all prior tasks — same replenishment pattern as sessions 6, 16, and 26.
PREDICTED IMPACT: Next WORK session starts with 5 ready testing tasks instead of spending turns on task discovery. Any agent following the patching section will now use correct PolyEdge module paths.

## 2026-03-24 05:00 — BUG FIX + TESTING (Session 35)
DONE: Fixed empty password security bug and added 5 tests — (1) RegisterRequest.password had no min_length: empty string "" was accepted, hashed, and stored, allowing anyone to log in with an empty password; fixed with Field(min_length=1); (2) GET /alerts/settings auto-creates AlertSetting for user with no row (path untested since registration always creates one); (3) PUT /alerts/settings auto-creates AlertSetting for user with no row; (4) PUT /alerts/settings with empty body {} returns 200 with no field changes (all Optional fields stay None); (5) POST /auth/register with name "  Alice  " stores as "Alice" (verifies route-level name.strip() works). 250→255 tests.
IMPACT: Empty password was a real security hole — bcrypt hash of "" is a valid credential anyone could use. Three previously untested defensive branches in alerts.py now locked in.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_alerts.py

## 2026-03-24 03:35 — BUG FIX + TESTING (Session 34)
DONE: Fixed 2 input-validation bugs and added 5 tests — (1) POST /auth/register accepted empty email (field was `str`, no validation) — changed to `EmailStr`; (2) POST /auth/register accepted whitespace-only name (stored as "" after `.strip()`) — added `field_validator` that strips then rejects blank; (3) fixed Hypothesis `test_bettor_address_never_causes_500` deadline failure (340ms > 200ms default) by adding `deadline=None`; (4) added ordering test for free-tier duplicate: count check fires before duplicate check → 403 not 409; (5) added bettor detail response shape contract: both `profile` and `recent_bets` keys always present. 246→250 tests.
IMPACT: Two silent data-corruption paths closed — registering with empty email or blank name created garbage User rows with no error. Hypothesis test now stable (was flaky on slow machines). Two invariants locked in by contract tests.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_bettors.py, backend/tests/test_follows.py, backend/tests/test_hypothesis_invariants.py

## 2026-03-24 — DE-SLOPPIFY AUDIT (Session 33)
DONE: Audited last 5 work sessions' changed files for coupling, test specificity, and agent smells — found 1 real bug, 1 dead code, 1 doc inconsistency. Fixed login email strip bug (auth.py line 73 was .lower() only, not .lower().strip()); removed dead @given(st.nothing()) _placeholder from test_hypothesis_invariants.py; added test_login_with_whitespace_padded_email_works. 245→246 tests.
IMPACT: Login with whitespace-padded email now works correctly (was returning 401). Dead placeholder test removed. VIP price mismatch (CLAUDE.md=$14.99 vs code=$9.99) logged to tech_debt.md.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_hypothesis_invariants.py

## 2026-03-24 03:05 — TESTING + BUG FIX (Session 32)
DONE: Fixed 2 bugs and added 6 tests — (1) FollowRequest.bettor_address now has min_length=1 (empty string was silently stored in DB), (2) /auth/register duplicate check now strips whitespace (padded email bypassed check and crashed with 500 on second attempt), (3-6) tests: empty address → 422, MRR 3 basic + 2 VIP decimal precision (not integer-rounded), whitespace email strips + deduplicates, login works after whitespace-padded registration, web_push_enabled independent of push_subscription, telegram/start second call overwrites code (old code invalid). 239→245 tests.
IMPACT: Two silent data-corruption/crash paths closed — empty bettor_address would create garbage rows; whitespace email would cause a 500 on duplicate registration attempts. All 5 backlog edge-case tasks completed.
FILES: backend/app/routes/follows.py, backend/app/routes/auth.py, backend/tests/test_follows.py, backend/tests/test_admin.py, backend/tests/test_auth.py, backend/tests/test_alerts.py

## 2026-03-24 — BRAIN SESSION (Session 31)
RESEARCHED: autonomous AI agent planning 2026 (arxiv), LLM memory management 2026, FastAPI testing patterns 2026, Polymarket copy-trading competitor features (HolyPoly), everything-claude-code new skills (autonomous-loops, eval-harness), agentic coding multi-file reliability (MSR 2026 arxiv 2511.04427)
DOWNLOADED: autonomous-loops/SKILL.md and eval-harness/SKILL.md from everything-claude-code (evaluated, De-Sloppify concept extracted)
IMPLEMENTED: (1) Periodic De-Sloppify tech-debt trigger added to PROMPT.md step 3 — every 5 work sessions auto-adds a META code-quality audit task to backlog; addresses empirical finding that agentic velocity reverses after 6-8 weeks without quality checks. (2) Replenished empty testing backlog with 5 new edge-case tests (POST /follows empty address, MRR decimal precision, whitespace email, web_push independence, telegram/start regeneration).
BACKLOGGED: playbook endpoint for bettors, hourly leaderboard cache refresh (FEATURE MODE ONLY); A-MEM linked memory (requires infrastructure); FSM planning (overkill for current complexity)
SOURCES: 9 new sources logged in brain/sources.md
CURATED: Scanned all knowledge.md RULE: entries — no duplicates or superseded rules found (already clean from session 21 curation)

## 2026-03-24 — TESTING (Session 30)
DONE: Added 5 branch-coverage tests found by systematic cross-file audit. (1) Cross-user DELETE /follows security — verified user B cannot delete user A's follow (route filters by user_id, returns 404); (2) Register uppercase email duplicate — `email.lower()` at register/login means `USER@EXAMPLE.COM` collides with `user@example.com`; (3) GET /auth/me all 7 user_to_dict fields asserted; (4) admin/stats follows.total with actual DB rows; (5) scheduler passes correct telegram_chat_id to dispatch when alert.telegram_enabled=True and user.telegram_verified=True. 234→239 tests.
IMPACT: Closes a cross-user security gap (users cannot delete each other's follows), confirms email normalization is consistent between register and login, locks in the /auth/me response shape contract, verifies admin observability data is correct for follows, and confirms the scheduler correctly passes Telegram credentials to the notification dispatcher.
FILES: backend/tests/test_follows.py, backend/tests/test_auth.py, backend/tests/test_admin.py, backend/tests/test_scheduler.py

## 2026-03-24 — TESTING (Session 29)
DONE: Added 5 branch-coverage tests found by systematic branch audit — (1) scheduler skips inactive users (is_active=False), (2) _parse_timestamp returns None for too-large int (OverflowError), (3) scheduler skips orphaned BettorFollow where user_id has no matching User row, (4) /follows/live returns addr[:12]+"..." when bettor_name is None in DB, (5) PUT /alerts/settings telegram_enabled=False (disable path) for basic user. 229→234 tests.
IMPACT: Closes 5 untested defensive branches — inactive user, parse_ts overflow, orphaned follow, and name fallback were all silent skip/fallback paths that could mask regressions; telegram disable is a real user action (enable→disable toggle) not previously verified.
FILES: backend/tests/test_scheduler.py, backend/tests/test_follows_live.py, backend/tests/test_alerts.py

## 2026-03-24 — TESTING (Session 28)
DONE: Added 19 tests — 5 direct send_web_push unit tests (JSON string 201, dict 200, no endpoint, HTTP 410, connection exception), 1 scheduler test (API returns None handled gracefully), 13 Hypothesis/parametrize invariant tests (GET /follows tier+limit for all 3 tiers, POST /follows tier enforcement for free/basic, 7 protected endpoints reject missing auth, adversarial bettor address strings never cause 500). Installed hypothesis and added to requirements.txt. 210→229 tests.
IMPACT: send_web_push was previously only mocked at dispatch level — all 5 branches now covered directly. Scheduler None-return path was a latent crash risk. Hypothesis invariants now guard the 3 hardest-to-break business rules against adversarial inputs automatically.
FILES: backend/tests/test_notifications.py, backend/tests/test_scheduler.py, backend/tests/test_hypothesis_invariants.py, backend/requirements.txt

## 2026-03-24 — TESTING (Session 27)
DONE: Added 5 stripe_service.py branch tests — checkout with missing metadata early-returns without error, checkout saves stripe_subscription_id to user, subscription change with unknown customer_id early-returns without error, active subscription with unrecognized price_id leaves user tier unchanged, create_billing_portal_session direct unit test (happy path). 205→210 tests.
IMPACT: Closes every untested explicit early-return guard and conditional branch in stripe_service.py — missing metadata, unknown customer, and unrecognized price_id were all defensive paths that could silently produce wrong state without a test catching it. stripe_subscription_id save was a data-persistence path never verified.
FILES: backend/tests/test_stripe_service.py

## 2026-03-24 — META SESSION (Session 26)
IMPROVED: (1) Fixed testing.md IMPORT CHECK — was pointing to `src.stockcards.app` (wrong project), now points to `app.main` (correct for PolyEdge). (2) Added BRANCH AUDIT WORKFLOW section to testing.md — the systematic checklist used successfully in sessions 22-25 was buried in knowledge.md reflexions; promoted to testing.md where WORK agents actually read before coding. (3) Replenished backlog with 6 concrete testing tasks covering stripe_service branches, send_web_push unit tests, scheduler edge cases, Hypothesis invariants, DELETE 404 edge case, and checkout response shape.
PATTERNS FOUND: Sessions 22-25 were all green (no failures) but used the same branch-audit methodology each time without it being documented in the skill file. Any session could have derived it from reflexions, but that wastes context and is unreliable. The testing.md import check was a stale reference that would break any future session following it literally.
PREDICTED IMPACT: Next WORK session starts with 6 ready testing tasks instead of spending turns on task discovery. The branch-audit checklist in testing.md will cut the "find gaps" phase from ~5 turns to 1 read.

## 2026-03-24 — TESTING (Session 25)
DONE: Added 6 coverage-gap tests — get_active_positions slug-only poly_url branch (no eventSlug, uses slug), get_active_positions no-slug fallback ("https://polymarket.com"), get_live_trades non-list API response returns [], get_recent_bets dict response with "activity" key, send_telegram returns False when bot_token empty, send_telegram returns False when chat_id empty. 199→205 tests.
IMPACT: Closes the two untested poly_url construction branches in get_active_positions; confirms get_live_trades defensive non-list handling; confirms get_recent_bets "activity" key fallback; and locks in the early-return guards in send_telegram that prevent sending to unconfigured/invalid recipients.
FILES: backend/tests/test_polymarket_service.py, backend/tests/test_notifications.py

## 2026-03-24 — TESTING (Session 24)
DONE: Added 5 coverage-gap tests — VIP tier GET /follows limit=999999 (completes tier triplet), get_bettor_profile empty-activity returns address-only profile with zeros, GET /follows/live response includes followed_at field, get_recent_bets dict response with data key extracts bets correctly, GET /bettors limit=0 returns 422 at minimum boundary. 194→199 tests.
IMPACT: Closes the last uncovered tier slot in follows tier/limit tests (free/basic were done, VIP wasn't); verifies the empty-activity defensive path in the bettor profile service; locks in the follows/live response shape contract; confirms the get_recent_bets dict-response fallback that prevents data loss on unexpected API format changes.
FILES: backend/tests/test_follows.py, backend/tests/test_follows_live.py, backend/tests/test_polymarket_service.py, backend/tests/test_bettors.py

## 2026-03-24 — TESTING (Session 23)
DONE: Added 5 coverage-gap tests — get_bettor_profile normalised profile (name/volume/avg_bet from activity), get_recent_bets normalised list (market_id/amount_usd/type), get_live_trades normalised trades (name/market/side/amount_usd), get_leaderboard pagination (2 API calls when first page is full), login email case-insensitivity (UPPER@EMAIL.COM matches lowercase user). 189→194 tests.
IMPACT: Covers all four core async Polymarket service functions that were previously untested — these power bettor profile pages, live ticker, and leaderboard; email case test confirms login UX doesn't confuse users who type uppercase.
FILES: backend/tests/test_polymarket_service.py, backend/tests/test_auth.py

## 2026-03-24 — TESTING (Session 22)
DONE: Added 5 coverage-gap tests — bettor_detail cache-hit path (second call served from _profile_cache), past_due subscription status downgrades VIP→free, subscription.updated active status upgrades free→basic, admin/stats bet_events.total+notified verified with real BetEvent rows, POST /follows response body includes id+bettor_name+created_at. 184→189 tests.
IMPACT: Closes the last uncovered branches in bettor profile caching (a hot path), confirms two billing downgrade/upgrade scenarios not previously tested (past_due and sub.updated→basic), and locks in the admin observability query and the POST /follows contract.
FILES: backend/tests/test_bettors.py, backend/tests/test_stripe_service.py, backend/tests/test_admin.py, backend/tests/test_follows.py

## 2026-03-24 — BRAIN SESSION (Session 21)
RESEARCHED: autonomous AI agent best practices 2026, LLM pytest testing patterns, FastAPI async patterns, agentic instruction-following reliability (arxiv), Polymarket copy-trading competitors
DOWNLOADED: No new skill files (patterns extracted directly into existing skill files)
IMPLEMENTED: (1) Irreversibility check (Q5) added to PROMPT.md self-critique gate — agents must name all irreversible actions before committing; (2) Hypothesis property-based testing section added to skills/testing.md with PolyEdge-specific invariant examples; (3) 4 new feature backlog items: Discord webhook channel, entry price in notifications, conviction score, outbox pattern for reliable dispatch
BACKLOGGED: Discord, entry price, conviction score, outbox pattern (all FEATURE MODE ONLY)
SOURCES: 8 new sources logged in brain/sources.md
CURATED: Merged duplicate grep-before-adding rules (sessions #10 and #17) into one canonical entry in knowledge.md
