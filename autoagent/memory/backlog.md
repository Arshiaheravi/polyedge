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

*(All 3 tasks completed in session 232 — unpaid downgrade mutation, JWT sub-claim identity mutation, Stripe checkout metadata user_id mutation; 541→544 tests)*

---

## PRIORITY 24 — Mutation Tests: Alerts + Bettors + Notifications

*(All 3 tasks already covered by existing tests — verified session 233 via grep. No new tests needed: test_web_push_blocked_for_free_tier + test_enable_web_push kill the alerts mutation; test_profile_cache_tier_gate_not_bypassed kills the bettors cache mutation; test_detect_exits_only_notifies_vip kills the notifications VIP mutation.)*

---

## PRIORITY 25 — Mutation Tests: copy_signal boundaries + conviction null

*(All 3 tasks completed in session 233 — copy_signal exact 10.0% boundary ("good"), exact 30.0% boundary ("fair"), and /follows/live conviction_score null when no recent bets; 544→547 tests)*

---

## PRIORITY 26 — Mutation Tests: scheduler ts boundary + follows conviction HIGH + consensus exact-3

**Context**: Manual mutation analysis — 3 surviving mutants found during session 233 low-water-mark check.

*(All 3 tasks completed in session 233 — ts exact boundary, conviction HIGH at 3.0, consensus exact-3-whale; 547→550 tests)*

---

## PRIORITY 27 — Code Quality Audit (generated session 235 — work session count hit 180)

*(Completed session 235 — audit clean: no TODO/dead code/secrets; minor Leo pattern: two nested _fail_commit helpers in test_scheduler.py are slightly different implementations, not blocking; Nina gate: all tier fixtures correct)*

---

## PRIORITY 21 — Coverage Gaps (generated session 227 via low-water-mark check — 99% total, 4 missed lines in database.py only)

*(All 3 tasks completed in session 228 — database.py now 100% covered; Stripe webhook unhandled event was already covered)*

---

## PRIORITY 16 — Coverage Gaps (generated session 221 via coverage report — 98% total, 24 missed lines)

*(All 3 tasks completed in session 222)*

---

## PRIORITY 28 — Playwright Tier Gate Gaps (generated session 235 via low-water-mark check)

*(All 3 tasks completed in session 235+236 — basic tier notifications not gated (session 235), Basic/VIP badge + upgrade button tests (session 236); 101→107 Playwright tests)*

---

## PRIORITY 29 — Playwright Account Tab Label + Billing Button

*(All 3 tasks completed in session 237 — tier-label text, billing button visibility, upgrade-nudge hidden state for Basic and VIP; 107→113 Playwright tests)*

---

## PRIORITY 30 — Playwright Account Tab Free-Tier Complements + Tier Description

*(All 3 tasks completed in session 238 — free billing hidden, free nudge visible, tier-desc text for all 3 tiers; 113→118 Playwright tests)*

---

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **WebSocket scheduler migration** — replace REST poll-every-30s in `services/scheduler.py` with Polymarket `/v1/ws/markets` WebSocket subscription. January 2026 update removed the 100-instrument cap (now 500/socket), removing the main scaling blocker. March 2026 Polymarket rule changes (taker bot unviable, <100ms execution window standard) make real-time detection (30s → <1s) the primary competitive differentiator vs PolyAlertHub. Architecture: `_start_ws_listener()` subscribes at startup; on trade event, call `dispatch_bet_notification()` directly; keep REST poll as fallback on WS disconnect. (Source: PolyEdge knowledge.md + quicknode.com 2026 + coincodecap 2026)

- [ ] **Min-bet-size filter per follow** — add a `min_bet_usd` field to `BettorFollow` model (default 0). Scheduler skips notifications when `bet_amount < follow.min_bet_usd`. Reduces noise from small test trades. Highest-demand competitive differentiator vs Polycule/PolycopytradBot per 2026 research. (Source: BRAIN session 203 competitor analysis — "every competing tool has min trigger amount filter")

- [ ] **Rich push notification payloads** — add `bettor_name` (truncated address), `market_title`, and a "Copy Bet" action button to VAPID web push payload body. Named notifications achieve 2× CTR vs generic "New bet detected" copy. (Source: BRAIN session 203 Pushwoosh fintech benchmark 2026 — personalization doubles CTR)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

- [ ] **Wallet basket / topic-based follow groups** — allow users to follow a group of wallets filtered by topic (e.g., "geopolitics basket: 5 top traders"). Fire signal only when 80%+ of basket members enter the same side within a tight time window. Requires a new `BettorBasket` model + basket scheduler logic. Competitors (Phemex Wallet Baskets, March 2026) are moving to this paradigm — it is a meaningfully different product from single-bettor follow. (Source: BRAIN session 234 Phemex/Polymarket competitive research)

- [ ] **Account-cluster tracking** — top Polymarket traders use multi-wallet strategies to obscure positions. Allow users to link multiple addresses under one "trader identity" (a BettorCluster model). Notifications fire when ANY address in the cluster places a bet. This addresses the multi-wallet evasion problem and would differentiate PolyEdge vs simpler copy bots that track single addresses only. (Source: BRAIN session 234 Polymarket COPYTRADE WARS competitive analysis)

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
