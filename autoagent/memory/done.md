# Done

## 2026-03-24
- **[SESSION #22] 5 coverage-gap tests — bettor cache hit, past_due downgrade, sub.updated basic, bet_events admin count, POST /follows body** — closed last untested branches in bettors profile cache, stripe webhook downgrade/upgrade paths, admin bet_events count, and follows response shape; 184→189 tests.
- **[SESSION #19] 5 coverage-gap tests — auth gaps, VIP telegram, cache hit, alert fields** — PUT /alerts and POST /follows auth tested (403), VIP telegram/start confirmed, leaderboard cached=True second call verified, alert settings phone/telegram fields checked; 174→179 tests.
- **[SESSION #17] sort=accuracy + multi-follower notify tests** — 2 new tests: GET /bettors sort=accuracy passes correct arg to service; scheduler notifies all N followers of same bettor; 167 → 169 tests.
- **[SESSION #13] Error-path + boundary tests** — 5 new tests: portal Stripe 502, leaderboard API 502, trades API 502, trades limit 422 (low/high); 153 → 158 tests.
- **[SESSION #12] Playwright E2E — leaderboard sort tabs + account tab + browse view** — 9-check Playwright suite; all pass; confirms sort/period toggles update active class + re-render data, account tab shows correct tier label, public browse view loads bettors without login.
- **[SESSION #10] Field-coverage tests** — 2 new tests: GET /follows returns bettor_address/bettor_name/created_at; GET /auth/me reflects updated tier; 151 → 153 tests.
- **[SESSION #9] Playwright E2E — follows + alerts pages** — 16-check Playwright verification; all pass; confirmed follow flow (currentUser must be loaded via init()), free tier limit UI, alert toggles, settings persist after reload.

## 2026-03-23
- **[SESSION #8] BetEvent field verification + subscription lifecycle tests** — 6 new tests: 3 verify BetEvent fields (market_question, outcome, amount_usd, timestamp) are stored correctly; 3 document downgrade behavior (follows preserved, new adds blocked); test count 145 → 151.


- **[SESSION #7] Notification dispatch + Telegram verify tests** — 11 new tests; full dispatch_bet_notification and telegram/verify flow covered; admin password confirmed; test count 134 → 145.
- **[SESSION #5] Edge-case tests + push_subscription bug fix** — 8 new tests; fixed silent acceptance of invalid JSON (now returns 422); test count 126 → 134.
- **[SESSION #4] Security + business-rule tests** — 18 new tests: JWT tamper/expiry, VIP unlimited follows, input validation, unfollow-refollow; test count 108 → 126.
- **[SESSION #3] E2E frontend smoke test** — Ran Playwright against live servers; all 7 checks pass (landing, leaderboard 100 bettors, login form, register form, no JS errors).
- **[SESSION #2] Scheduler + BetEvent test suite** — 17 new tests covering _parse_timestamp and _poll_bets; test count 91 → 108.
- **[SESSION #1] Fix 5 failing webhook tests** — Added autouse conftest fixture clearing STRIPE_WEBHOOK_SECRET so webhook tests work; committed prior-session backend bugfixes (polymarket API, follows live, notifications) and full 91-test E2E suite; fixed CLAUDE.md free tier docs.
- **[SESSION #14] 4 coverage-gap tests** — disabled login, bettor_detail 502, basic tier message, bettor_name default
- **[SESSION #15] 5 coverage-gap tests** — SMS 503/400/502 paths, alert settings push_subscription parsing, follows/live cache hit; 162→167 tests
