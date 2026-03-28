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

## PRIORITY 7 — High-Value Gaps

- [ ] **Playwright: basic user hits 5-follow limit → upgrade modal shown** — register a fresh basic-tier user, follow 5 bettors (all succeed), attempt a 6th follow → server returns 403 → upgrade modal (#upgrade-modal) becomes visible. This is the basic-tier equivalent of the free-tier follow-limit test in test_auth_and_security.py. Grep: `grep -r "def test.*basic.*follow.*limit\|5.*follow.*basic" backend/tests/playwright/` returns nothing.

- [ ] **Playwright: basic user follows bettor → appears on follows dashboard** — login as basic, follow first leaderboard bettor, navigate to Follows tab, assert bettor address appears in #follows-container. Same flow as session 195 (free user) but for basic tier. Grep: `grep -r "def test.*basic.*follow.*dashboard" backend/tests/playwright/` returns nothing.

- [ ] **Playwright: VIP user follows bettor → appears on follows dashboard** — login as VIP, follow first leaderboard bettor, navigate to Follows tab, assert bettor address appears. Completes the North Star table row "Follow bettor → see on dashboard | ✓ | ✓ | ✓". Grep: `grep -r "def test.*vip.*follow.*dashboard" backend/tests/playwright/` returns nothing.

---

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
