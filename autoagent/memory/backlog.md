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

- [ ] **`_poll_vip_bets` skips old bets** — scheduler.py line 337: `if ts and ts <= _last_check: continue`. VIP user + follow + bet with timestamp before `_last_check` → BetEvent not created and `get_recent_bets` called but no event row. Mirror of `test_poll_bets_skips_old_bets` for VIP path.
  Grep: `grep -n "poll_vip_bets.*skip.*old\|vip.*old.*bet\|skips_old.*vip" backend/tests/test_scheduler.py` returns nothing

- [ ] **`_poll_vip_bets` outer exception handler** — scheduler.py lines 417-418: `except Exception as exc: logger.error("VIP poll_bets error: %s", exc); db.rollback()`. Patch `db.commit` inside `_poll_vip_bets` to raise, assert the function doesn't crash and the except branch fires.
  Grep: `grep -n "poll_vip_bets.*outer.*except\|vip.*rollback\|poll_vip.*error.*handler" backend/tests/test_scheduler.py` returns nothing

- [ ] **`get_live_trades` exception handler** — polymarket.py lines 104-105: `except Exception: trades = []`. Mock `client.get` to raise `httpx.ConnectError`, call `get_live_trades()`, assert result is `[]` without raising. Mirror of `test_get_recent_bets_api_exception_returns_empty_list` for the live-trades path.
  Grep: `grep -n "get_live_trades.*exception\|live_trades.*error\|live_trades.*raises" backend/tests/test_polymarket_service.py` returns nothing

---

## PRIORITY 16.5 — Code Quality Audit (generated session 222 — work session count hit 170)

- [ ] **Code quality audit** — scan last 5 work sessions' changed files (test_scheduler.py, test_notifications.py, test_alerts.py) for cross-file coupling, test specificity degradation, and smells introduced by agent edits.

---

## PRIORITY 16 — Coverage Gaps (generated session 221 via coverage report — 98% total, 24 missed lines)

*(All 3 tasks completed in session 222)*

---

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Min-bet-size filter per follow** — add a `min_bet_usd` field to `BettorFollow` model (default 0). Scheduler skips notifications when `bet_amount < follow.min_bet_usd`. Reduces noise from small test trades. Highest-demand competitive differentiator vs Polycule/PolycopytradBot per 2026 research. (Source: BRAIN session 203 competitor analysis — "every competing tool has min trigger amount filter")

- [ ] **Rich push notification payloads** — add `bettor_name` (truncated address), `market_title`, and a "Copy Bet" action button to VAPID web push payload body. Named notifications achieve 2× CTR vs generic "New bet detected" copy. (Source: BRAIN session 203 Pushwoosh fintech benchmark 2026 — personalization doubles CTR)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
