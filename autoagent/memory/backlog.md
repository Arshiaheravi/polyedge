# Backlog — E2E Testing Sprint

All tasks are NEW. None of these appear in done.md (sessions 135–186).
Every completed task must push to https://github.com/Arshiaheravi/polyedge.git.

---

## PRIORITY 1 — Full User Journey Playwright Tests

- [ ] **E2E: Free user full journey** — Playwright: register new user → browse leaderboard → click bettor → profile modal opens with Copy Simulator BLURRED (locked=true) → follow bettor → open dashboard follows tab → position card shows padlock (not copy signal badge) → try to follow 2nd bettor → upgrade modal appears. Assert each step explicitly.

- [ ] **E2E: Basic user full journey** — Playwright: log in as `basic@polyedge.com` / `BasicTest123!` → leaderboard loads → click bettor → Copy Simulator shows P&L numbers (not blurred) → follow bettor → dashboard position card shows copy signal badge (good/fair/late, NOT padlock) → open Consensus tab → all markets visible, whale_names = [] (no names shown). Assert each step.

- [ ] **E2E: VIP user full journey** — Playwright: log in as `vip@polyedge.com` / `VipTest123!` → profile page shows full Copy Simulator → dashboard position cards show copy signal badge → Consensus tab shows all markets WITH whale names visible → follow limit: can follow more than 5 bettors without 403 error. Assert each step.

- [ ] **E2E: Auth persistence** — Playwright: log in → refresh page (F5) → user is still logged in (pe_token in localStorage, username shown in UI, not redirected to landing). Assert both localStorage and visible UI state.

- [ ] **E2E: Auth expiry / bad token** — Playwright: manually set `localStorage.setItem('pe_token', 'invalid.jwt.token')` → navigate to dashboard → assert redirected to landing page (401 handled gracefully, no blank screen, no JS crash).

---

## PRIORITY 2 — Tier Gate Visual Verification (Playwright)

- [ ] **Playwright: Free tier — Copy Simulator blurred** — log in as free user → click bettor in leaderboard → assert profile modal contains `.simulator-locked` class OR blurred overlay element. Assert `locked: true` also in the raw API response `GET /bettors/{address}`.

- [ ] **Playwright: Free tier — Follow limit in UI** — log in as fresh free user (register new) → follow 1 bettor (succeeds) → attempt to follow 2nd bettor → assert upgrade modal/toast appears with "upgrade" text visible. Assert second follow returns 403 from API.

- [ ] **Playwright: Basic tier — Consensus whale names hidden** — log in as basic user → open Consensus tab → assert market cards render → assert NO whale name text visible (names_visible=false means the names array is empty, no bettor name links rendered).

- [ ] **Playwright: VIP tier — Consensus whale names visible** — log in as VIP → open Consensus tab → assert at least one market card renders with whale name text (non-empty names array rendered in DOM).

- [ ] **Playwright: Notifications settings page — tier gates** — log in as free user → navigate to Alerts tab → assert Telegram enable button is disabled or shows upgrade prompt → assert SMS option not shown. Log in as VIP → assert Telegram + web push enabled, SMS option visible.

---

## PRIORITY 3 — Security E2E

- [ ] **E2E: XSS — script tag in username** — register with name `<script>alert(1)</script>Test` → log in → navigate to account tab → assert the name is displayed as escaped text (not executed) — no alert() fires, `textContent` contains the literal `<script>` characters. Write as both Playwright test and backend test asserting response body escapes HTML.

- [ ] **E2E: JWT tamper — fetch with modified token** — backend test: create valid JWT, modify the payload (change tier to "vip"), re-sign with wrong key → send to `GET /auth/me` → assert 401 response. Then assert `GET /follows` with same token also returns 401.

- [ ] **E2E: Mass assignment — subscription_tier in register body** — backend test: POST /auth/register with body `{"email":..., "password":..., "subscription_tier": "vip"}` → assert user created with tier="free" (mass assignment blocked). Verify via GET /auth/me.

- [ ] **E2E: CORS headers in browser** — Playwright: intercept network response for any API call → assert `Access-Control-Allow-Origin` header is NOT `*` (wildcard). Assert it is either `http://localhost:3000` or absent on non-CORS requests.

- [ ] **E2E: SQL injection via login** — backend test: POST /auth/login with `{"email": "' OR '1'='1", "password": "x"}` → assert 401 (not 200, not 500). Also try `{"email": "admin@test.com'; DROP TABLE users; --", "password": "x"}` → assert 401 and users table still exists after request.

---

## PRIORITY 4 — Error State E2E

- [ ] **E2E: Polymarket API timeout → graceful frontend** — Playwright: mock `fetch` on `/bettors` to return a network error → assert leaderboard shows an error message (not blank white screen, not JS crash). The error text should be user-friendly.

- [ ] **E2E: Empty follows state** — Playwright: log in as fresh user with zero follows → open Follows tab → assert empty-state message is shown (not a blank div, not a spinner stuck forever). The empty state message must be visible and contain meaningful text.

- [ ] **E2E: Backend 503 → frontend shows error** — Playwright: intercept API response and return 503 → assert dashboard shows an error toast or message (not silent blank). Test both leaderboard and consensus tab endpoints.

- [ ] **E2E: Expired Polymarket data** — backend test: if `/bettors` returns empty list from Polymarket, assert GET /bettors returns `{"bettors": []}` with 200 (not 500). Assert frontend renders empty leaderboard gracefully.

---

## PRIORITY 5 — Cross-Endpoint Data Consistency

- [ ] **E2E: Leaderboard profit matches profile profit** — backend integration test: GET /bettors → pick top bettor address → GET /bettors/{address} → assert `pnl_usd` in leaderboard entry is within 10% of `pnl_usd` in profile response (same bettor, same data source, must be consistent).

- [ ] **E2E: Follow count matches admin stats** — backend integration test: register 2 users → each follows 1 bettor → GET /admin/stats with correct header → assert `total_follows >= 2`. Create and delete a follow → assert count updates correctly.

- [ ] **E2E: Leaderboard rank is unique and sequential** — backend test: GET /bettors?limit=20 → assert all rank values are unique integers with no gaps (1,2,3...20). No duplicate ranks, no rank=0, no missing ranks.

- [ ] **E2E: Recent bets are TRADE type only** — backend integration test: GET /bettors/{address} → assert every item in `recent_bets` has `type == "TRADE"` (no REDEEM, no MERGE transactions leaked through). Assert all bets have `side` field populated.

---

## PRIORITY 6 — Admin E2E

- [ ] **E2E: Admin stats MRR formula** — backend test: create known number of basic and VIP users → GET /admin/stats → assert `mrr_estimate == basic_count * 4.99 + vip_count * 9.99` (exact match to 2 decimal places). Currently 186 sessions in but this math was never directly asserted with real DB state.

- [ ] **E2E: Admin endpoint rejects wrong password** — backend test: GET /admin/stats with wrong x-admin-password header → 403. GET /admin/stats with no header → 403. GET /admin/stats with correct password → 200 with stats object containing `total_users`, `basic_users`, `vip_users`, `mrr_estimate` keys.

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
