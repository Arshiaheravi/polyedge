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

*(All 3 tasks completed or confirmed already covered in session 211)*

## PRIORITY 11 — Coverage Gaps (generated session 213 via low-water-mark check)

*(All 3 tasks completed or confirmed already covered in session 215)*

## PRIORITY 11.5 — Code Quality Audit

*(Completed session 217)*

---

## PRIORITY 12 — Coverage Gaps (generated session 215 via low-water-mark check)

*(All 3 tasks completed in session 216)*

---

## PRIORITY 13 — Coverage Gaps (generated session 217 via low-water-mark check + coverage report)

*(All 3 tasks completed or confirmed already covered in session 218)*

---

## PRIORITY 14 — Coverage Gaps (generated session 218 via low-water-mark check)

*(All 3 tasks completed in session 220)*

---

## PRIORITY 15 — Coverage Gaps (generated session 220 via low-water-mark check + coverage report)

*(All 3 tasks completed in session 221)*

---

## PRIORITY 17 — Coverage Gaps (generated session 222 via coverage report — 98% total, 21 missed lines)

*(All 3 tasks completed in session 223)*

---

## PRIORITY 16.5 — Code Quality Audit (generated session 222 — work session count hit 170)

*(Completed session 223 — audit clean, no issues found)*

---

## PRIORITY 18 — Coverage Gaps (generated session 223 via coverage report — 99% total, 16 missed lines)

*(All 3 tasks completed in session 225 — NOTE: task 3 was actually _fetch_positions inside get_consensus_signals, not get_active_positions; backlog description had wrong function name but correct line numbers)*

---

## PRIORITY 19 — Coverage Gaps (generated session 225 via coverage report — 99% total, 11 missed lines in polymarket.py)

*(All 3 tasks completed in session 226)*

---

## PRIORITY 20 — Coverage Gaps (generated session 226 via coverage report — 99% total, 4 missed lines in polymarket.py)

*(All 2 tasks completed in session 227 — polymarket.py now 100% covered)*

---

## PRIORITY 21.5 — Code Quality Audit (generated session 228 — work session count hit 175)

*(Completed session 230 — one Leo smell fixed: removed redundant autouse-duplicate _last_check assignment; all other checks clean)*

---

## PRIORITY 22 — Mutation Tests

*(All 3 tasks completed in session 231 — 3 surviving mutants identified via manual analysis and killed: signals[:2] in markets.py, tier==free branch in follows.py, <= vs < at 50% boundary in scheduler.py; 538→541 tests)*

---

## PRIORITY 23 — Mutation Tests: Payments + Auth (generated session 231 — low-water-mark, all PRIORITY 22 done)

**Context**: Manual mutation analysis approach (mutmut incompatible with Windows py env). For each file: read the critical branching logic, identify mutations that change behavior, check whether existing tests assert the specific boundary, write tests for gaps.

- [ ] **Mutation test — routes/payments.py Stripe tier assignment** — Read the Stripe webhook handler in routes/payments.py. Key mutations: `subscription_tier = "basic"` → `"vip"` (or vice versa), `customer_id` comparison logic. Check if existing tests assert the EXACT tier assigned after each webhook event type (checkout.completed, subscription.deleted). A mutant swapping "basic"/"vip" would give wrong access.
  Grep: `grep -n "def test.*webhook\|subscription_tier.*basic\|subscription_tier.*vip" backend/tests/test_payments.py` — check if exact tier values are asserted post-webhook.

- [ ] **Mutation test — routes/auth.py JWT claims and password verify** — Key mutations: `str(user.id)` → `str(user.email)` in JWT sub claim (users get wrong identity), `verify_password` return value inversion (auth bypass), `expire` delta changed. Check if existing tests assert the token's sub claim decodes to the correct user ID. A sub-claim mutation would let any user impersonate any other.
  Grep: `grep -n "def test.*jwt\|def test.*token\|sub.*user.id\|decode" backend/tests/test_auth.py` — check if JWT sub is asserted.

- [ ] **Mutation test — services/stripe_service.py customer/tier mapping** — Read the Stripe service. Key mutations: `stripe_customer_id` assignment (customer mapped to wrong user), tier string literals in upgrade paths. Check if tests assert `user.stripe_customer_id == expected_id` after customer creation, and that tier upgrades use the exact expected string.
  Grep: `grep -n "stripe_customer_id\|subscription_tier" backend/tests/test_stripe_service.py` — check exact assertion values.

---

## PRIORITY 21 — Coverage Gaps (generated session 227 via low-water-mark check — 99% total, 4 missed lines in database.py only)

*(All 3 tasks completed in session 228 — database.py now 100% covered; Stripe webhook unhandled event was already covered)*

---

## PRIORITY 16 — Coverage Gaps (generated session 221 via coverage report — 98% total, 24 missed lines)

*(All 3 tasks completed in session 222)*

---

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **WebSocket scheduler migration** — replace REST poll-every-30s in `services/scheduler.py` with Polymarket `/v1/ws/markets` WebSocket subscription. January 2026 update removed the 100-instrument cap (now 500/socket), removing the main scaling blocker. March 2026 Polymarket rule changes (taker bot unviable, <100ms execution window standard) make real-time detection (30s → <1s) the primary competitive differentiator vs PolyAlertHub. Architecture: `_start_ws_listener()` subscribes at startup; on trade event, call `dispatch_bet_notification()` directly; keep REST poll as fallback on WS disconnect. (Source: PolyEdge knowledge.md + quicknode.com 2026 + coincodecap 2026)

- [ ] **Min-bet-size filter per follow** — add a `min_bet_usd` field to `BettorFollow` model (default 0). Scheduler skips notifications when `bet_amount < follow.min_bet_usd`. Reduces noise from small test trades. Highest-demand competitive differentiator vs Polycule/PolycopytradBot per 2026 research. (Source: BRAIN session 203 competitor analysis — "every competing tool has min trigger amount filter")

- [ ] **Rich push notification payloads** — add `bettor_name` (truncated address), `market_title`, and a "Copy Bet" action button to VAPID web push payload body. Named notifications achieve 2× CTR vs generic "New bet detected" copy. (Source: BRAIN session 203 Pushwoosh fintech benchmark 2026 — personalization doubles CTR)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
