# Backlog — E2E Testing Sprint

All tasks are NEW (not in done.md sessions 135–186).
Every completed task must push to https://github.com/Arshiaheravi/polyedge.git.

---

## PRIORITY 1 — Full User Journey Playwright Tests

- [ ] **E2E: Free user full journey** — Playwright: register new user → browse leaderboard → click bettor → profile modal opens with Copy Simulator BLURRED (locked=true) → follow bettor → open dashboard follows tab → position card shows padlock (not copy signal badge) → try to follow 2nd bettor → upgrade modal appears. Assert each step explicitly.

- [ ] **E2E: Basic user full journey** — Playwright: log in as `basic@polyedge.com` / `BasicTest123!` → leaderboard loads → click bettor → Copy Simulator shows P&L numbers (not blurred) → follow bettor → dashboard position card shows copy signal badge (good/fair/late, NOT padlock) → open Consensus tab → all markets visible, whale_names = [] (no names shown). Assert each step.

- [ ] **E2E: VIP user full journey** — Playwright: log in as `vip@polyedge.com` / `VipTest123!` → profile page shows full Copy Simulator → dashboard position cards show copy signal badge → Consensus tab shows all markets WITH whale names visible → follow limit: can follow more than 5 bettors without 403 error. Assert each step.

---

## PRIORITY 2 — Tier Gate Visual Verification (Playwright)

- [ ] **Playwright: Notifications settings page — tier gates** — log in as free user → navigate to Alerts tab → assert Telegram enable button is disabled or shows upgrade prompt → assert SMS option not shown. Log in as VIP → assert Telegram + web push enabled, SMS option visible.

---

## PRIORITY 3 — Security E2E

- [ ] **E2E: CORS headers in browser** — Playwright: intercept network response for any API call → assert `Access-Control-Allow-Origin` header is NOT `*` (wildcard). Assert it is either `http://localhost:3000` or absent on non-CORS requests.

---

## PRIORITY 4 — Error State E2E

- [ ] **E2E: Polymarket API timeout → graceful frontend** — Playwright: mock `fetch` on `/bettors` to return a network error → assert leaderboard shows an error message (not blank white screen, not JS crash). The error text should be user-friendly.

- [ ] **E2E: Empty follows state** — Playwright: log in as fresh user with zero follows → open Follows tab → assert empty-state message is shown (not a blank div, not a spinner stuck forever). The empty state message must be visible and contain meaningful text.

- [ ] **E2E: Backend 503 → frontend shows error** — Playwright: intercept API response and return 503 → assert dashboard shows an error toast or message (not silent blank). Test both leaderboard and consensus tab endpoints.

- [ ] **E2E: Expired Polymarket data** — backend test: if `/bettors` returns empty list from Polymarket, assert GET /bettors returns `{"bettors": []}` with 200 (not 500). Assert frontend renders empty leaderboard gracefully.

---

## PRIORITY 5 — Cross-Endpoint Data Consistency

- [ ] **E2E: Follow count matches admin stats** — backend integration test: register 2 users → each follows 1 bettor → GET /admin/stats with correct header → assert `total_follows >= 2`. Create and delete a follow → assert count updates correctly.

---

## PRIORITY 6 — Admin E2E

- [ ] **E2E: Admin endpoint rejects wrong password** — backend test: GET /admin/stats with wrong x-admin-password header → 403. GET /admin/stats with no header → 403. GET /admin/stats with correct password → 200 with stats object containing `total_users`, `basic_users`, `vip_users`, `mrr_estimate` keys.

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
