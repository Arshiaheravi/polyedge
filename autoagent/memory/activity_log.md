# Activity Log

## 2026-03-24 — BRAIN SESSION (Session 31)
RESEARCHED: autonomous AI agent planning 2026 (arxiv), LLM memory management 2026, FastAPI testing patterns 2026, Polymarket copy-trading competitor features (HolyPoly), everything-claude-code new skills (autonomous-loops, eval-harness), agentic coding multi-file reliability (MSR 2026 arxiv 2511.04427)
DOWNLOADED: autonomous-loops/SKILL.md and eval-harness/SKILL.md from everything-claude-code (evaluated, De-Sloppify concept extracted)
IMPLEMENTED: (1) Periodic De-Sloppify tech-debt trigger added to PROMPT.md step 3 — every 5 work sessions auto-adds a META code-quality audit task to backlog; addresses empirical finding that agentic velocity reverses after 6-8 weeks without quality checks. (2) Replenished empty testing backlog with 5 new edge-case tests (POST /follows empty address, MRR decimal precision, whitespace email, web_push independence, telegram/start regeneration).
BACKLOGGED: playbook endpoint for bettors, hourly leaderboard cache refresh (FEATURE MODE ONLY); A-MEM linked memory (requires infrastructure); FSM planning (overkill for current complexity)
SOURCES: 9 new sources logged in brain/sources.md
CURATED: Scanned all knowledge.md RULE: entries — no duplicates or superseded rules found (already clean from session 21 curation)

## 2026-03-24 — TESTING (Session 30)
DONE: Added 5 branch-coverage tests found by systematic audit — (1) DELETE /follows/{address} by a different user returns 404 (cross-user security invariant), (2) POST /auth/register with uppercase duplicate email returns 400 (email normalization), (3) GET /auth/me returns all 7 expected fields from user_to_dict (response contract), (4) admin/stats follows.total reflects actual BettorFollow count (data accuracy), (5) scheduler dispatches with correct telegram_chat_id when user has telegram_enabled=True and telegram_verified=True (notification arg passing). 234→239 tests.
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
PREDICTED IMPACT: Next WORK session starts with 6 ready test tasks instead of spending turns on task discovery. The branch-audit checklist in testing.md will cut the "find gaps" phase from ~5 turns to 1 read.

## 2026-03-24 — TESTING (Session 25)
DONE: Added 6 coverage-gap tests — get_active_positions slug-only poly_url branch (no eventSlug, uses slug), get_active_positions no-slug fallback ("https://polymarket.com"), get_live_trades non-list API response returns [], get_recent_bets dict response with "activity" key, send_telegram returns False when bot_token empty, send_telegram returns False when chat_id empty. 199→205 tests.
IMPACT: Closes the two untested poly_url construction branches in get_active_positions (the eventSlug path was already tested; slug-only and no-slug weren't); confirms get_live_trades defensive non-list handling; confirms get_recent_bets "activity" key fallback; and locks in the early-return guards in send_telegram that prevent sending to unconfigured/invalid recipients.
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

## 2026-03-24 — TESTING (Session 20)
DONE: Added 5 coverage-gap tests — trades endpoint cached=True second-call branch, login response user dict fields, SMS start happy path (first success test for that endpoint), telegram/verify no-auth 403, sms/verify no-auth 403. 179→184 tests.
IMPACT: Closes the SMS start happy path (was only error paths before); locks in the trades cached=True contract matching the leaderboard pattern; two more auth gaps closed for verify endpoints.
FILES: backend/tests/test_bettors.py, backend/tests/test_auth.py, backend/tests/test_alerts.py

## 2026-03-24 — TESTING (Session 19)
DONE: Added 5 coverage-gap tests — PUT /alerts/settings auth gap, POST /follows auth gap, VIP telegram/start, leaderboard cache-hit returns cached=True, GET /alerts/settings response includes phone/telegram fields. 174→179 tests.
IMPACT: Closes the last HTTP-method auth gaps (PUT and POST were untested for missing auth); confirms VIP tier can initiate telegram linking; validates the leaderboard cache True branch that was previously only tested as False.
FILES: backend/tests/test_alerts.py, backend/tests/test_follows.py, backend/tests/test_bettors.py

## 2026-03-24 — TESTING (Session 18)
DONE: Added 5 coverage-gap tests — basic-tier GET /follows (tier+limit fields), leaderboard "cached" field, DELETE /follows without auth (403), web-push disable toggle, admin stats basic/vip user counts. 169→174 tests.
IMPACT: Three tier slots (free/basic/VIP) for GET /follows limit are now all tested; DELETE auth gap closed; cached field contract locked in for the leaderboard response.
FILES: backend/tests/test_follows.py, backend/tests/test_bettors.py, backend/tests/test_alerts.py, backend/tests/test_admin.py

## 2026-03-24 — TESTING (Session 17)
DONE: Added 2 coverage-gap tests — GET /bettors sort=accuracy passes correct arg to service; scheduler dispatches to all N followers of same bettor. 167→169 tests.
IMPACT: sort=accuracy was the only sort param without a test; multi-follower notification path is the core revenue mechanic (more followers → more upgrades) and was untested.
FILES: backend/tests/test_bettors.py, backend/tests/test_scheduler.py

## 2026-03-24 — META SESSION (Session 16)
IMPROVED: (1) Added PolyEdge-specific cache isolation and module settings monkeypatch patterns to skills/testing.md. (2) Replenished backlog with 6 concrete testing tasks. (3) Relabeled feature backlog items as "FEATURE MODE ONLY". (4) Added "FEATURE MODE ONLY" to skip list in PROMPT.md step 3.
PATTERNS FOUND: Sessions 13-15 repeatedly hit module-level cache isolation (_trades_cache, _profile_cache) and module-level settings binding issues — both documented in knowledge.md but absent from testing.md where WORK agents actually look. Backlog was empty of test tasks, forcing next session to derive them from PROJECT.md.
PREDICTED IMPACT: WORK agents will find cache isolation and settings monkeypatch patterns before they fail; next WORK session starts with 6 ready testing tasks instead of spending turns on task discovery; DEBUG MODE agents won't accidentally pick feature tasks.

## 2026-03-24 — TESTING (Session 15)
DONE: Added 5 coverage-gap tests — SMS start 503/400/502 error paths, GET /alerts/settings returns parsed push_subscription dict, /follows/live cache-hit path. 162→167 tests.
IMPACT: Four previously untested SMS error branches now verified (Twilio unconfigured, bad phone format, send failure); alert settings push_subscription parsing confirmed; follows live cache behaviour locked in.
FILES: backend/tests/test_alerts.py, backend/tests/test_follows_live.py

## 2026-03-24 — TESTING (Session 14)
DONE: Added 4 coverage-gap tests — disabled account login (403), bettor_detail 502 on API failure, basic tier limit error message with VIP upsell, and bettor_name truncated-address default. 158→162 tests.
IMPACT: Four previously uncovered code branches now tested: the is_active=False login guard, the bettors/{address} exception handler, the non-free tier cap message, and the bettor_name fallback logic.
FILES: backend/tests/test_auth.py, backend/tests/test_bettors.py, backend/tests/test_follows.py

## 2026-03-24 — TESTING (Session 13)
DONE: Added 5 error-path + boundary tests — portal Stripe 502, leaderboard API 502, recent trades API 502, and recent trades limit boundaries (422 for limit<5 and limit>50). 153→158 tests.
IMPACT: These were untested exception branches in payments and bettors routes — a real Stripe or Polymarket outage would have hit uncovered code paths.
FILES: backend/tests/test_bettors.py, backend/tests/test_payments.py

## 2026-03-24 — TESTING (Session 12)
DONE: Ran 9-check Playwright E2E suite covering leaderboard sort tabs, period tabs, account tab, and browse view. All 9 passed. Discovered that bettor profile click-through does not exist in the frontend — backlog task updated to reflect reality.
IMPACT: Confirms leaderboard sort/period toggles work correctly, account tier label renders for authenticated users, and the public browse view loads real bettor data without a login.
FILES: No project files changed (Playwright-only session)

## 2026-03-24 — BRAIN SESSION (Session 11)
RESEARCHED: autonomous AI agent best practices 2026, LLM self-improvement, AI coding agent reliability (arxiv), agentic context management, FastAPI production 2026, Polymarket trading strategies and copytrading competitive advantage
DOWNLOADED: No new skill files (all repos already covered in sources.md)
IMPLEMENTED: ACE Curator step added to BRAIN_PROMPT.md (Step 1C) — each brain session now scans knowledge.md for duplicate/superseded rules and merges them; first curation pass confirmed 13 rules are distinct
BACKLOGGED: 3 high-priority PolyEdge features — win_rate display on leaderboard, 15s VIP polling interval, Alembic migration setup
SOURCES: 6 new sources logged in brain/sources.md

## 2026-03-24 05:00 — TESTING (Session 10)
DONE: Added 2 field-coverage tests — GET /follows verified to return bettor_address, bettor_name, created_at per array item; GET /auth/me verified to reflect updated subscription_tier. Confirmed webhook delete + MRR tests already existed. Test count: 151 → 153.
IMPACT: Closes the last 4 uncovered backend edge cases from backlog. Response shape for /follows is now contract-tested — any future regression that strips bettor_name will be caught.
FILES: backend/tests/test_follows.py, backend/tests/test_auth.py

## 2026-03-24 04:30 — TESTING (Session 9)
DONE: Ran 16-check Playwright E2E for follows + alerts pages. All 16 passed. Confirmed: follows tab subtitle correct, follow button works for logged-in users, free tier limit enforced at UI level, alerts toggles visible, web push toggle changes state (with notification permission), Telegram toggle correctly blocked on free tier, alert settings persist after page reload.
IMPACT: Every critical follow and alerts UI flow is now verified E2E — any regression in follow counting, tier enforcement, or notification settings will be caught.
FILES: autoagent/tmp_check.py (run-only, deleted after)

## 2026-03-23 — TESTING (Session 8)
DONE: Added 6 tests: 3 BetEvent field-value tests (market_question, outcome, amount_usd, timestamp stored correctly + partial-fields defaults + timestamp tzinfo) and 3 subscription lifecycle tests documenting that follows are NOT auto-removed on downgrade. Test count: 145 → 151.
IMPACT: Confirmed BetEvent stores all 6 required fields with correct values; documented and enforced the downgrade invariant (follows persist after tier change).
FILES: backend/tests/test_scheduler.py, backend/tests/test_stripe_service.py

## 2026-03-23 — TESTING (Session 7)
DONE: Added 11 tests covering dispatch_bet_notification edge cases (6 tests) and the full /alerts/telegram/verify flow (5 tests). Resolved admin password conflict — confirmed `polyedge-admin-2026` loads correctly from .env. Test count: 134 → 145.
IMPACT: Notification dispatch logic and Telegram linking flow are now fully covered — any regression in the core "follow bettor → get notified" loop will be caught immediately.
FILES: backend/tests/test_notifications.py, backend/tests/test_alerts.py, autoagent/PROJECT.md, autoagent/memory/knowledge.md

## 2026-03-23 — META SESSION (Session 6)
DONE: Replenished empty backlog with 7 concrete testing tasks (notifications, Telegram flow, admin password fix, BetEvent fields, subscription lifecycle, frontend E2E). Created missing project_root.md. Added DEBUG MODE backlog rule to PROMPT.md. Flagged admin password conflict in knowledge.md.
IMPACT: Next WORK session starts with a clear task list instead of wasting turns on task discovery. Missing project_root.md would have broken every future META session at STEP 0.
FILES: autoagent/memory/backlog.md, autoagent/memory/project_root.md, autoagent/memory/knowledge.md, autoagent/PROMPT.md, autoagent/memory/activity_log.md
NOTE: STEP 4 commit skipped — autoagent has no git repo initialized (no .git in autoagent/). Memory changes are persisted on filesystem only. To fix: run `git init` in autoagent/ and set a remote. Memory files are gitignored by autoagent/.gitignore (design intent), but PROMPT.md and skills/ can be committed once a repo exists.

## 2026-03-23 — BUG FIX + TESTING (Session 5)
DONE: Added 8 edge-case tests and fixed a bug where invalid JSON in push_subscription was silently accepted (200) then crashed GET with 500. Route now validates JSON and returns 422. Test count: 126 → 134.
IMPACT: Prevents server crash when a browser sends a malformed push_subscription string; error message wording confirmed to guide users toward upgrade; SQL injection and empty-DB scenarios confirmed safe.
FILES: backend/tests/test_edge_cases.py, backend/app/routes/alerts.py

## 2026-03-23 — TESTING (Session 4)
DONE: Added 18 security and business-rule tests covering JWT tampering/expiry/missing-sub (6 tests), VIP unlimited follows (3 tests), register/login input validation (6 tests), unfollow-then-refollow (1 test), unknown bettor address graceful handling (2 tests). Test count: 108 → 126.
IMPACT: Confirms auth cannot be bypassed with tampered tokens; VIP tier correctly allows unlimited follows; input validation rejects malformed requests; re-follow works after unfollow.
FILES: backend/tests/test_security.py

## 2026-03-23 — TESTING (Session 3)
DONE: Ran full E2E Playwright smoke test against live servers — all 7 checks pass: landing page visible, backend /bettors returns 100 real bettors, browse/leaderboard view opens, login form fields present, register form fields present, zero JS errors.
IMPACT: Every core user-facing flow confirmed working end-to-end against real backend. Frontend SPA is healthy.
FILES: autoagent/tmp_check.py (temp, deleted after run)

## 2026-03-23 — TESTING (Session 2)
DONE: Added 17 scheduler tests covering _parse_timestamp (10 cases) and _poll_bets (7 cases: no-follows, new bet saved, old bet skipped, duplicate skipped, free-tier no-notification, basic-tier notified, API error continues). Test count: 91 → 108.
IMPACT: The scheduler is the core revenue-driving loop (detects bets → fires notifications → users upgrade). Zero tests existed before; now all critical branches are verified.
FILES: backend/tests/test_scheduler.py

## 2026-03-23 — BUG FIX
DONE: Fixed 5 failing webhook tests — added autouse conftest fixture that clears STRIPE_WEBHOOK_SECRET for all tests, so tests using sig_header="" don't trigger real Stripe signature verification.
IMPACT: Test suite now fully green (91 passed, 0 failed). Also committed prior-session backend bugfixes (polymarket API, follows live endpoint, notifications) and the full E2E test suite.
FILES: backend/tests/conftest.py, backend/app/config.py, backend/app/main.py, backend/app/models.py, backend/app/routes/admin.py, backend/app/routes/alerts.py, backend/app/routes/bettors.py, backend/app/routes/follows.py, backend/app/services/notifications.py, backend/app/services/polymarket.py, backend/app/services/scheduler.py, backend/requirements.txt, frontend/index.html, run.sh, backend/tests/ (12 test files)
