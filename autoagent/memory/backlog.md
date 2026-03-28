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

- [ ] **`get_bettor_profile` paginated non-list break** — polymarket.py line 279: inner paginated loop `if not isinstance(page, list): break`. Mock `httpx.AsyncClient` to return a dict response → `page` is not a list → break is hit. Verify function returns empty dict or fallback without raising.
  Grep: `grep -n "get_bettor_profile.*dict\|bettor_profile.*not.*list\|page.*not.*list" backend/tests/test_polymarket_service.py` returns nothing

- [ ] **`compute_copy_simulator` non-list activity response** — polymarket.py line 332: `if not isinstance(raw_list, list): raw_list = []`. Call `compute_copy_simulator("0xaddr")` with mock API returning `{"error": "bad"}` (dict) → raw_list reset to [] → return `{"simulated_pnl_usd": 0, "simulated_roi_pct": 0, "bets_analysed": 0}`.
  Grep: `grep -n "compute_copy_simulator.*dict\|copy_simulator.*raw_list\|compute_copy.*exception" backend/tests/test_polymarket_service.py` returns nothing

- [ ] **`_fetch_positions` empty conditionId skip** — polymarket.py line 477: `if not cid or not outcome: continue`. Mock `_fetch_positions` via `get_consensus_signals` with a position that has `conditionId=""` or missing → skipped → no signal generated.
  Grep: `grep -n "fetch_positions.*empty.*cid\|conditionId.*empty\|not.*cid.*not.*outcome" backend/tests/test_polymarket_service.py` returns nothing

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
