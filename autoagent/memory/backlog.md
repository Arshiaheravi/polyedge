# Backlog — E2E Testing Sprint

All tasks are NEW (not in done.md sessions 135–186).
Every completed task must push to https://github.com/Arshiaheravi/polyedge.git.

---

## PRIORITY 3 — Security E2E

## PRIORITY 4 — Error State E2E

*(All 4 error state tasks completed in session 194)*

---

## PRIORITY 5 — Cross-Endpoint Data Consistency

*(Covered by existing test_admin.py::test_admin_stats_follows_total_reflects_actual_follows)*

---

## PRIORITY 6 — Admin E2E

*(Covered by existing test_admin.py — no_header→403, wrong_password→403, correct→200+keys)*

---

## PRIORITY 7 — High-Value Gaps (added session 194, LOW-WATER-MARK fill)

- [ ] **Playwright: follow bettor → bettor appears on follows dashboard** — basic user registers fresh, follows bettor from leaderboard via `POST /follows`, navigates to follows tab, asserts the followed bettor's address appears in `#follows-container`. Proves "Follow bettor → see on dashboard" end-to-end in a real browser. Grep: `grep -r "def test_.*follow.*appear" backend/tests/playwright/` returns nothing.

- [ ] **Playwright: leaderboard "No data yet" shown when API returns empty list** — route intercept returns `{"bettors": [], "cached": false}` with 200 → browse view shows "No data yet" text (not "Could not load", not blank). This covers the empty-list success path distinct from error states. Grep: `grep -r "No data yet" backend/tests/playwright/` returns nothing.

- [ ] **Backend: copy_value_pct math is correct** — unit test in test_follows_live.py: mock position with avg_price=0.40, current_price=0.50 → assert copy_value_pct == 25.0; avg_price=0.20, current_price=0.30 → assert copy_value_pct == 50.0. Current tests pass the field through but never verify the formula. Grep: `grep -r "copy_value_pct.*formula\|avg_price.*current_price" backend/tests/` returns nothing.

---

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
