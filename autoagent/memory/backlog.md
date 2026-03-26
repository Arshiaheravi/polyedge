# Backlog

---

## CODE QUALITY AUDIT

- [ ] **Code quality audit (Session 105)** — scan changed files from last 5 work sessions (sessions 136-140) for cross-file coupling, test specificity degradation, and smells introduced by agent edits. Check: are tests too tightly coupled to implementation details? Any circular imports? Any dead code left from bug fixes?

---

## CRITICAL BUGS — Fix First (Code Review 2026-03-26)


- [ ] **Web push is a non-functional stub** — `services/notifications.py:68-97` POSTs directly to the browser push endpoint without VAPID signing or payload encryption. Chrome/Firefox/Safari all reject unsigned pushes with 401/403. The function returns False silently — users "enable" push and never receive anything. Fix requires pywebpush library + VAPID keys. Until fixed, disable web push option in UI rather than silently failing.


- [ ] **Consensus "Could not load"** — was caused by port mismatch. Verify it now loads correctly on 8003 by running Playwright test that opens the Consensus tab and asserts market cards are visible.

---

## HIGH PRIORITY — Real-World Data Integrity Tests

These tests verify the data coming from Polymarket is real, consistent, and makes sense — not just that the API returns 200. Write as `tests/test_data_integrity.py`. Cross-validate against the live Polymarket Data API directly where possible.

- [ ] **Leaderboard data sanity** — GET /bettors: assert every bettor has a valid Ethereum address (matches `^0x[a-fA-F0-9]{40}$`); profit_usd is a number ≥ 0 for top 20; accuracy is between 0.0 and 1.0; volume_usd > 0; rank is a positive integer with no duplicates in the top 20; name is non-empty string

- [ ] **Leaderboard vs profile consistency** — pick the top 3 bettors from GET /bettors, then GET /bettors/{address} for each one; assert their profit_usd, rank, and accuracy are within 5% of what the leaderboard shows (they come from the same source — any larger discrepancy means a normalisation bug)

- [ ] **Recent bets data validity** — GET /bettors/{address} for 5 different addresses; for each bet assert: amount_usd > 0; price is between 0.01 and 0.99 (a price of exactly 0 or 1 means it already resolved and shouldn't appear); outcome is "YES" or "NO"; timestamp is in the past and within the last 90 days; market_title is a non-empty string ≥ 5 chars; type == "TRADE" (no REDEEM should appear)

- [ ] **Prices are economically meaningful** — for all positions returned by GET /follows/live: avg_price must be between 0.01 and 0.99; current_price must be between 0.001 and 0.999; cur_size_usd > 0; percent_pnl is a finite number (not NaN or Infinity); cash_pnl is a finite number. A price of 0.0 or 1.0 means the market resolved — those positions should not appear as "active copyable bets"

- [ ] **Copy signal logic correctness** — for each position: if copy_value_pct ≤ 10 → copy_signal must be "good"; if 10 < copy_value_pct ≤ 30 → must be "fair"; if > 30 → must be "late". Also assert copy_value_pct = round((current_price - avg_price) / avg_price * 100, 1). Test 10 real positions and verify the math is correct.

- [ ] **Consensus signals are real** — GET /markets/consensus: assert signals is a list; each signal has whale_count ≥ 3 (the minimum threshold); avg_entry_price between 0.01 and 0.99; current_price between 0.001 and 0.999; outcome is "YES" or "NO" or a named team/candidate (non-empty); market_title is non-empty; condition_id matches `^0x[a-fA-F0-9]{64}$`; total_available is a non-negative integer

- [ ] **Copy simulator math** — GET /bettors/{address} for 5 addresses as a Basic user: assert simulated_pnl_usd is a finite float; simulated_roi_pct = simulated_pnl_usd / (bets_analysed * 100) * 100 (within rounding); bets_analysed ≥ 0 and ≤ 20; result is economically plausible — reject if |simulated_roi_pct| > 10000% (that would mean a bug, not a real return)

- [ ] **Admin stats are internally consistent** — GET /admin/stats: assert user_count ≥ 0; free_count + basic_count + vip_count == user_count; mrr_estimate == round(basic_count * 4.99 + vip_count * 9.99, 2); follow_count ≥ 0; bet_event_count ≥ 0

- [ ] **Polymarket cross-validation** — pick the #1 bettor from GET /bettors; directly call `https://data-api.polymarket.com/profiles?limit=1&sortBy=profit` and compare the top address; assert PolyEdge's #1 bettor address matches Polymarket's #1 (or is at least in Polymarket's top 5); this confirms we're not showing stale/wrong leaderboard data

- [ ] **No stale resolved markets in positions** — for all positions in GET /follows/live: if end_date is not null and end_date < today → assert that position does NOT appear (resolved markets should be excluded). A position with end_date in the past at current_price near 0 or 1 means the market resolved — copying it is pointless and misleading to users.

---

## HIGH PRIORITY — Tier Gate E2E Tests

- [ ] **Tier gate Playwright suite** — write a Playwright test file `tests/playwright/test_tier_gates.py` that:
  - Logs in as Free → checks Consensus tab shows ≤3 cards + upgrade banner; position cards show 🔒 padlock; profile simulator shows blurred teaser
  - Logs in as Basic → checks Consensus shows all cards without whale names; position cards show copy signal badge (not padlock); profile simulator shows real numbers
  - Logs in as VIP → checks Consensus shows all cards WITH whale names; position cards show copy signal badge; profile simulator shows real numbers; Exit Alerts toggle is accessible
  Use test accounts: free@polyedge.com/FreeTest123!, basic@polyedge.com/BasicTest123!, vip@polyedge.com/VipTest123!

---

## HIGH PRIORITY — Security Tests (OWASP Top 10)

- [ ] **SQL injection test** — POST /auth/login with email=`' OR '1'='1'--` and email=`admin'--`; assert 401/422, not 200. Add to `tests/test_security.py`

- [ ] **XSS test** — register with name=`<script>alert(1)</script>`, then GET /auth/me and assert name is stored as plain text (not executed); Playwright test to verify it renders escaped in UI

- [ ] **Auth bypass tests** — test tampered JWTs (wrong signature, expired, wrong user_id) all return 401; test accessing /follows, /alerts/settings, /admin/stats without token returns 401/403

- [ ] **Mass assignment test** — POST /auth/register with body including `subscription_tier: "vip"` — assert registered user has tier "free" not "vip"

- [ ] **Sensitive data test** — GET /auth/me, GET /bettors, GET /admin/stats — assert no response body contains `password`, `hashed_password`, or any hash string

---

## HIGH PRIORITY — Feature Correctness Tests

- [ ] **Copy simulator correctness** — pytest: GET /bettors/{known_address} as free → locked:true, simulated_pnl_usd:null; as basic → locked:false, simulated_pnl_usd is float, bets_analysed ≥ 0

- [ ] **Recent bets — no REDEEM** — pytest: GET /bettors/{address}/recent_bets → assert no bet has type=="REDEEM", all bets have outcome and side fields populated

- [ ] **Follow limits enforced** — pytest: login as free user, follow 1 bettor → 201; attempt 2nd follow → 403; login as basic, follow up to 5 → all 201; attempt 6th → 403

- [ ] **Admin stats** — pytest: GET /admin/stats with correct header → 200 with mrr_estimate field; wrong password → 403; no header → 403

---

## HIGH PRIORITY — Frontend UI Playwright Tests

- [ ] **Landing page pricing** — assert all 3 pricing cards contain the new features: "Conviction Score", "Smart Entry Timing", "Copy Portfolio Simulator", "Whale Consensus", "Exit Alerts"

- [ ] **Register → Login flow** — Playwright: fill register form, submit, assert redirected to dashboard; logout; login with same credentials, assert back in dashboard

- [ ] **Leaderboard renders** — Playwright: open leaderboard, assert ≥10 bettor cards visible, each has name + profit + accuracy fields

- [ ] **Bettor profile opens** — Playwright: click first bettor card, assert profile modal opens with name, stats, recent bets, copy simulator section

- [ ] **Consensus tab loads** — Playwright: log in as VIP, open Consensus tab, assert whale name is visible in at least one card

- [ ] **Back-to-top FAB** — Playwright: scroll down >300px on leaderboard, assert FAB becomes visible; click it, assert scrolled back to top

- [ ] **Mobile layout** — Playwright: set viewport to 375×812, assert mobile bottom nav is visible and all tabs navigate correctly

---

## MEDIUM PRIORITY — Edge Cases & Reliability

- [ ] **Rate limiting on auth routes** — add slowapi/starlette middleware to limit POST /auth/register and POST /auth/login to 10 req/min per IP; rapid brute-force attacks currently not blocked. Competitors + 2026 FastAPI best practices both flag this as production-critical. (Source: fastlaunchapi.dev 2026)

- [ ] **Bot filtering on leaderboard** — flag or exclude Polymarket accounts with suspiciously uniform bet timing (e.g. always placing identical size bets at consistent intervals = algorithmic trader). Reduces noise in the followed-bettor list for copy-traders. Add `is_bot_suspected` flag to leaderboard normaliser. (Source: competitor research, session 143)

- [ ] **Configurable scheduler poll interval** — add `POLL_INTERVAL_SECONDS` to config.py (default 30); read in scheduler.py instead of hardcoded `30`. Allows tightening to 10s during high-traffic events without code changes. (Source: FastAPI SaaS best practices 2026, session 143)

- [ ] **Empty follows state** — Playwright: log in as new user with no follows, open Follows tab, assert empty state message shown (not crash)

- [ ] **Polymarket timeout handling** — pytest: mock Polymarket API to return 500, assert /bettors endpoint returns graceful error not 500

- [ ] **Concurrent requests** — pytest: fire 10 simultaneous GET /bettors requests, assert all return 200 without DB errors

- [ ] **Scheduler duplicate prevention** — pytest: confirm _last_check is updated correctly so same bet is not notified twice

---

## HIGH PRIORITY — Code Review

These tasks are a structural code review — not testing functionality, but reading the code to find bugs, security holes, and logic errors that tests might miss. Write findings as comments in a `tests/test_code_review.py` file or fix directly if small.

- [ ] **Auth security review** — read `backend/app/auth.py`: verify JWT algorithm is HS256 or RS256 (not "none"); password hashing uses bcrypt or argon2 (not MD5/SHA1); `get_current_user` returns 401 (not 403) on bad token; no raw passwords logged anywhere

- [ ] **SQL injection surface** — read all route files in `backend/app/routes/`: identify every place user input is used in a DB query; confirm all go through SQLAlchemy ORM (not raw string interpolation); flag any `f"SELECT ... {user_input}"` patterns

- [ ] **Tier gate completeness** — read `follows.py`, `bettors.py`, `markets.py`: for each premium feature, verify the tier check exists on the BACKEND (not just frontend); frontend-only tier gates are security theater — the API must enforce them

- [ ] **Scheduler correctness** — read `scheduler.py`: verify `_last_check` is updated AFTER `db.commit()` (not before, or a DB failure could cause missed notifications); verify `_last_positions` is not unbounded (could grow forever as bettors are added/removed); verify exit detection handles first-run correctly (no false exits on startup)

- [ ] **Polymarket service review** — read `services/polymarket.py`: check all HTTP calls have timeouts (a hanging Polymarket call would freeze the scheduler); verify error handling won't leak raw API errors to users; check price normalization — are prices always 0-1, or can they come back as percentages (0-100)?

- [ ] **Sensitive data leakage** — search all routes for `hashed_password`, `stripe_customer_id` in response dicts; these should NEVER appear in any API response. NOTE: `telegram_chat_id` was fixed in session 137 (removed from login/register/me responses). Still need to verify `hashed_password` and `stripe_customer_id` are not leaking.

- [ ] **Frontend API error handling** — read `frontend/index.html`: for every `fetch()` call, verify there is a `.catch()` or `try/catch`; uncaught promise rejections cause silent failures; also check that expired JWT (401 response) triggers redirect to login — not a blank screen

- [ ] **Dead code and unused routes** — scan for any imported but unused modules, any route registered in main.py but not documented, any model column that is defined but never written or read; flag for removal (dead code = confusion)

---

## NEW FEATURES (build AFTER all tests pass)

- [ ] **Category-specific leaderboard filter** — let users filter the leaderboard by market category (crypto/politics/sports/mentions) matching Polymarket's native categories; show per-category win rate badge on bettor cards (e.g. "95% in politics"). Competitor Polymarket Analytics (Primo Data) offers this as differentiating free feature. Add category filter chips above the leaderboard grid. TIER GATE: Free/Basic/VIP (no gate — competitive baseline).

- [ ] Copy Ratio Setting — let users set a per-bettor copy ratio multiplier (0.1x, 0.25x, 0.5x, 1x) stored in BettorFollow table; show on follow cards as "Copy at 0.5x"; include copy_ratio in notification messages. TIER GATE: Basic/VIP only.

- [ ] Insider Score — 0-100 confidence score per bettor (win_rate × profit_usd × avg_conviction × bet_count / 50). Badge on leaderboard cards (green >70, yellow 40-70, gray <40). TIER GATE: badge visible to all; numeric score for Basic/VIP only.

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
