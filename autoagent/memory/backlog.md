# Backlog

---


---

---

---

---

## HIGH PRIORITY — Quick Wins (VIP differentiators + production readiness)

- [ ] **VIP tier: reduce scheduler poll from 30s to 5s** — CLAUDE.md already promises "Priority speed" for VIP tier but scheduler polls at the same 30s interval for all tiers. Fix: add `VIP_POLL_INTERVAL_SECONDS = 5` config; scheduler runs two APScheduler jobs (5s VIP, 30s basic/free) or dynamically adjusts. Closes the competitive gap vs. PolyCop/PolyGun who claim sub-second alerts. One-line config change + minor scheduler split. (Source: Medium polybots 2026 + CLAUDE.md VIP tier description, session 153)

- [ ] **GET /health + GET /readiness endpoints** — Add `routes/health.py` with two endpoints: `/health` returns 200 immediately (liveness probe), `/readiness` checks DB connectivity (`db.execute("SELECT 1")`) and returns 200 or 503. Required before any production deployment or Docker/k8s setup. (Source: render.com FastAPI best practices 2026, session 153)

---

## MEDIUM PRIORITY — Edge Cases & Reliability

- [ ] **Rate limiting on auth routes** — add slowapi/starlette middleware to limit POST /auth/register and POST /auth/login to 10 req/min per IP; rapid brute-force attacks currently not blocked. Competitors + 2026 FastAPI best practices both flag this as production-critical. (Source: fastlaunchapi.dev 2026)

- [ ] **Bot filtering on leaderboard** — flag or exclude Polymarket accounts with suspiciously uniform bet timing (e.g. always placing identical size bets at consistent intervals = algorithmic trader). Reduces noise in the followed-bettor list for copy-traders. Add `is_bot_suspected` flag to leaderboard normaliser. (Source: competitor research, session 143)

- [ ] **Configurable scheduler poll interval** — add `POLL_INTERVAL_SECONDS` to config.py (default 30); read in scheduler.py instead of hardcoded `30`. Allows tightening to 10s during high-traffic events without code changes. (Source: FastAPI SaaS best practices 2026, session 143)

- [ ] **Empty follows state** — Playwright: log in as new user with no follows, open Follows tab, assert empty state message shown (not crash)


---

## HIGH PRIORITY — Code Review

These tasks are a structural code review — not testing functionality, but reading the code to find bugs, security holes, and logic errors that tests might miss. Write findings as comments in a `tests/test_code_review.py` file or fix directly if small.

*(Auth review, SQL injection, CORS, tier gate completeness, scheduler correctness, Polymarket service review — all confirmed clean in code review 2026-03-26 and sessions 137–147. Removed to prevent re-auditing already-verified areas.)*

- [ ] **Frontend API error handling audit** — scan `frontend/index.html` for every `catch` block and `.then(err =>` handler: verify each shows a user-visible error message (not silently swallows), and that error messages use `escapeHtml()` before `innerHTML`. Focus on: login/register failures, follow/unfollow API errors, Telegram verify errors, payment redirect failures. (Session 148: kept for audit — not yet reviewed)

- [ ] **Dead code audit** — scan `frontend/index.html` for functions defined but never called; scan `backend/app/` for imported names not referenced in their module. Remove anything genuinely unreachable. Candidate areas: frontend helper functions added in early sessions before the card-grid refactor, any `routes/*.py` imports removed during bugfixes. (Session 148: kept for audit — not yet reviewed)


---

## NEW FEATURES (build AFTER all tests pass)

- [ ] **Time-period leaderboard filter** — add time selector buttons (Today / Week / Month / All) above the leaderboard grid, pass selected period to `/bettors` endpoint which passes it to the Polymarket API (`?sortBy=profit&timeframe=weekly` etc.). Polymarket's own leaderboard has this filter — users who come from Polymarket will immediately expect it. Show who's been profitable THIS WEEK, not just all-time. TIER GATE: none (competitive baseline feature). (Source: Polymarket leaderboard research session 153)

- [ ] **Category-specific leaderboard filter** — let users filter the leaderboard by market category (crypto/politics/sports/mentions) matching Polymarket's native categories; show per-category win rate badge on bettor cards (e.g. "95% in politics"). Competitor Polymarket Analytics (Primo Data) offers this as differentiating free feature. Add category filter chips above the leaderboard grid. TIER GATE: Free/Basic/VIP (no gate — competitive baseline).

- [ ] Copy Ratio Setting — let users set a per-bettor copy ratio multiplier (0.1x, 0.25x, 0.5x, 1x) stored in BettorFollow table; show on follow cards as "Copy at 0.5x"; include copy_ratio in notification messages. TIER GATE: Basic/VIP only.

- [ ] Insider Score — 0-100 confidence score per bettor (win_rate × profit_usd × avg_conviction × bet_count / 50). Badge on leaderboard cards (green >70, yellow 40-70, gray <40). TIER GATE: badge visible to all; numeric score for Basic/VIP only.

- [ ] **Hedging position filter** — Before firing a notification, check if the bettor holds an offsetting position in the same market (YES + NO). Skip notification if offsetting positions cancel out — this is a liquidity farming position, not a directional bet. Reduces notification fatigue. Add `is_directional` flag to BetEvent. Stand.trade competitor already ships this. (Source: Polymarket copytrade-wars article, session 153)

- [ ] **SQLAlchemy production pool settings** — Set `pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600` in `database.py` before any PostgreSQL migration. `pool_pre_ping` tests connections before use and discards stale ones. Currently using SQLite defaults (single-file, no pool). (Source: zestminds.com FastAPI deployment guide, session 153)

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
