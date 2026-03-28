# Backlog — E2E Testing Sprint

All tasks are NEW (not in done.md sessions 135–186).
Every completed task must push to https://github.com/Arshiaheravi/polyedge.git.

---

## PRIORITY 3 — Security E2E

*(All 3 tasks completed in session 207)*

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

*(All 2 tasks completed in session 205)*

---

## PRIORITY 8 — New Testing Coverage

*(All 3 tasks completed in session 206)*

---

## PRIORITY 9 — Landing Page Navigation Coverage

*(All tasks completed in session 210)*

---

## PRIORITY 10 — Coverage Gaps (generated session 210 via low-water-mark check)

- [ ] **hashed_password + stripe_customer_id never leak in API responses** — Add tests to test_auth.py or test_security.py asserting: (a) POST /auth/register response body has no `hashed_password` key, (b) POST /auth/login response body has no `hashed_password` key, (c) GET /auth/me response body has no `hashed_password` key, (d) same checks for `stripe_customer_id`. This closes section 12 "No `hashed_password`, `stripe_customer_id` ever returned." Bug #3 fixed telegram_chat_id but hashed_password+stripe_customer_id were never explicitly regression-tested.
  Grep: `grep -rn "def test.*hashed_password\|def test.*stripe_customer_id.*response" backend/tests/` should return nothing.

- [ ] **Duplicate follow returns 409** — POST /follows for an address already in the user's follows should return 409 Conflict (not 500 or silent 200). Add test to test_follows.py: follow address A once (201), follow address A again (expect 4xx). Prevents silent duplicate entries in BettorFollow table.
  Grep: `grep -rn "def test.*follow.*duplicate\|def test.*follow.*already\|def test.*double.*follow\|def test.*follow.*twice\|def test.*follow.*conflict" backend/tests/test_follows.py` should return nothing.

- [ ] **GET /bettors/{address} with non-existent address returns 404 gracefully** — Polymarket may return 404 for unknown addresses; the backend should return 404 (not 500 or hang). Add test to test_bettors.py: GET /bettors/0x0000000000000000000000000000000000000000 (zero address, never a real bettor) should return 4xx within 20s.
  Grep: `grep -rn "def test.*bettor.*not.*found\|def test.*bettors.*invalid\|def test.*profile.*404\|def test.*bettors.*nonexist" backend/tests/test_bettors.py` should return nothing.

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Min-bet-size filter per follow** — add a `min_bet_usd` field to `BettorFollow` model (default 0). Scheduler skips notifications when `bet_amount < follow.min_bet_usd`. Reduces noise from small test trades. Highest-demand competitive differentiator vs Polycule/PolycopytradBot per 2026 research. (Source: BRAIN session 203 competitor analysis — "every competing tool has min trigger amount filter")

- [ ] **Rich push notification payloads** — add `bettor_name` (truncated address), `market_title`, and a "Copy Bet" action button to VAPID web push payload body. Named notifications achieve 2× CTR vs generic "New bet detected" copy. (Source: BRAIN session 203 Pushwoosh fintech benchmark 2026 — personalization doubles CTR)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
