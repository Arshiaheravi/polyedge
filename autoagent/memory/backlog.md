# Backlog — E2E Testing Sprint

All tasks are NEW (not in done.md sessions 135–186).
Every completed task must push to https://github.com/Arshiaheravi/polyedge.git.

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
