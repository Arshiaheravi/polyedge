# Activity Log

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
