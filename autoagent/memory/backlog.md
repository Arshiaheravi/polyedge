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

## PRIORITY 12 — Coverage Gaps (generated session 215 via low-water-mark check)

- [ ] **`get_current_user` HTTPException branch uncovered** — `auth.py` lines 76-77: `except HTTPException: return None` is never hit by any test. Trigger: mock `db.query` to raise `HTTPException` inside `get_current_user`, assert the protected endpoint returns 401 (not 500). Grep: `grep -r "def test_.*httpexception.*current_user\|def test_.*get_current_user.*except" backend/tests/` returns nothing.

- [ ] **`POST /payments/webhook` generic Exception → 502** — `payments.py` lines 53-54: the `except Exception` branch raises `HTTPException(status_code=502)`. Existing tests only cover the `ValueError → 400` path and success path. Add a test that patches `handle_webhook_event` to raise a generic `RuntimeError` and asserts the endpoint returns 502. Grep: `grep -r "def test_.*webhook.*502\|def test_.*webhook.*generic.*exc" backend/tests/` returns nothing.

- [ ] **Stripe webhook signature verification failure → ValueError** — `stripe_service.py` lines 75-78: when `stripe_webhook_secret` is non-empty and `Webhook.construct_event` raises `SignatureVerificationError`, `handle_webhook_event` raises `ValueError`. No test covers this. Patch `settings.stripe_webhook_secret = "real_secret"`, mock `Webhook.construct_event` to raise `SignatureVerificationError`, assert `ValueError` is raised. Grep: `grep -r "def test_.*signature.*fail\|SignatureVerification" backend/tests/` returns nothing.

---

## FEATURE MODE — Competitive Intelligence (do not implement in DEBUG mode)

- [ ] **Min-bet-size filter per follow** — add a `min_bet_usd` field to `BettorFollow` model (default 0). Scheduler skips notifications when `bet_amount < follow.min_bet_usd`. Reduces noise from small test trades. Highest-demand competitive differentiator vs Polycule/PolycopytradBot per 2026 research. (Source: BRAIN session 203 competitor analysis — "every competing tool has min trigger amount filter")

- [ ] **Rich push notification payloads** — add `bettor_name` (truncated address), `market_title`, and a "Copy Bet" action button to VAPID web push payload body. Named notifications achieve 2× CTR vs generic "New bet detected" copy. (Source: BRAIN session 203 Pushwoosh fintech benchmark 2026 — personalization doubles CTR)

- [ ] **Polystrat competitor awareness** — Polystrat (olas.network) is an autonomous AI agent that executes 4,200+ trades/month on Polymarket for users. PolyEdge's copy-notification model (human makes the copy trade decision) is differentiated from fully autonomous execution. Competitive moat: PolyEdge's notification-only model is lower risk and likely compliant where autonomous bots may not be. Consider adding a landing page differentiator: "You control the trade, AI just spots the opportunity." (Source: CoinDesk 2026-03-15 "AI agents quietly rewriting prediction market trading")

- [ ] **Mobile-first UX pass** — modern prediction market platforms (Pariflow) compete on "consumer-first" UX with one-tap execution and highly responsive mobile apps. PolyEdge currently has a mobile nav bar (session 119 confirmed working at 375px) but bettor cards and consensus signals could be more mobile-optimized. Add to FEATURE MODE sprint when mission switches.

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
