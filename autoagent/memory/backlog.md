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

## PRIORITY 9 — Unfixed Bugs + Real-World Data Integrity

- [ ] **Fix + test Bug #9** — `get_settings()` in `config.py` is not `@lru_cache` — creates a new `Settings()` on every call. Add `@lru_cache` decorator, write 1 test asserting `get_settings() is get_settings()` (same object returned twice).
  Grep: `grep -n "lru_cache" backend/app/config.py` should return nothing.

- [ ] **Fix + test Bug #10** — `_last_positions` dict in `scheduler.py` never purged when a bettor is unfollowed. Grows forever as follows are added/removed. Fix: in the DELETE /follows route (or scheduler poll loop), remove the address key from `_last_positions`. Write 1 unit test: follow bettor → unfollow → assert address not in `_last_positions`.
  Grep: `grep -n "_last_positions" backend/app/services/scheduler.py returns nothing except the initial assignment` — confirm no purge logic exists.

- [ ] **Fix + test Bug #12** — `_consensusLoaded` flag in `frontend/index.html` is set once and never cleared, causing stale consensus data within the same session. Fix: reset `_consensusLoaded = false` at the top of `loadConsensusSignals()` before the early-return check, or clear it on tab switch. Write 1 Playwright test: call `loadConsensusSignals()` twice, assert it fires the API a second time (or check `_consensusLoaded` resets).
  Grep: `grep -n "_consensusLoaded" frontend/index.html` to see current state.

- [ ] **Real-World Data Integrity: bettor address format** — Playwright test that calls GET /bettors (live), asserts every returned address matches `^0x[a-fA-F0-9]{40}$` regex. Catches any normalisation bug that corrupts addresses.
  Grep: `grep -rn "0x.*fA-F0-9.*40" backend/tests/` should return nothing.

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Min-bet-size filter per follow** — add a `min_bet_usd` field to `BettorFollow` model (default 0). Scheduler skips notifications when `bet_amount < follow.min_bet_usd`. Reduces noise from small test trades. Highest-demand competitive differentiator vs Polycule/PolycopytradBot per 2026 research. (Source: BRAIN session 203 competitor analysis — "every competing tool has min trigger amount filter")

- [ ] **Rich push notification payloads** — add `bettor_name` (truncated address), `market_title`, and a "Copy Bet" action button to VAPID web push payload body. Named notifications achieve 2× CTR vs generic "New bet detected" copy. (Source: BRAIN session 203 Pushwoosh fintech benchmark 2026 — personalization doubles CTR)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
