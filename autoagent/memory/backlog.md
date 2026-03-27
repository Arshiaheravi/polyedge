# Backlog — E2E Testing Sprint

All tasks are NEW (not in done.md sessions 135–186).
Every completed task must push to https://github.com/Arshiaheravi/polyedge.git.

---

## PRIORITY 3 — Security E2E

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

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Dead assertion sweep** — run `grep -rn "or True" backend/tests/` and verify zero matches. If any found, fix. Also run `grep -rn "assert True$\|assert 1$" backend/tests/` — these are always-pass assertions. (Source: session 192 code quality audit found `assert ... or True` masking a tier gate failure for 3 sessions.)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
