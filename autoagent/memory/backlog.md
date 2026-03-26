# Backlog

---


---

---

---

---

---

---

## MEDIUM PRIORITY — Edge Cases & Reliability

- [ ] **Bot filtering on leaderboard** — flag or exclude Polymarket accounts with suspiciously uniform bet timing (e.g. always placing identical size bets at consistent intervals = algorithmic trader). Reduces noise in the followed-bettor list for copy-traders. Add `is_bot_suspected` flag to leaderboard normaliser. (Source: competitor research, session 143)

- [ ] **Configurable scheduler poll interval** — add `POLL_INTERVAL_SECONDS` to config.py (default 30); read in scheduler.py instead of hardcoded `30`. Allows tightening to 10s during high-traffic events without code changes. (Source: FastAPI SaaS best practices 2026, session 143)

- [ ] **Empty follows state** — Playwright: log in as new user with no follows, open Follows tab, assert empty state message shown (not crash)


---

## HIGH PRIORITY — Testing

- [ ] **Active positions price range validation** — `GET /follows/live` returns positions with `avg_price` and `current_price` fields; add a test to `test_data_integrity.py` that verifies both values are between 0.001–0.999 for all returned positions (price = 0 or 1 means a resolved/expired market — serving these is a data quality bug). Grep confirms: no test for this exists yet.

- [ ] **copy_signal enum validation in follows/live** — `GET /follows/live` positions include a `copy_signal` field; add a unit test verifying it is always one of `["good", "fair", "late"]` (never None, empty, or an unknown string). Add to `test_follows_live.py`. Grep confirms: no test validates the enum constraint — only the numeric threshold logic is tested.

- [ ] **Consensus signal whale_count and price range** — `GET /markets/consensus` each signal must have `whale_count >= 3` and `avg_entry_price` between 0.01–0.99. Add a data integrity test in `test_data_integrity.py` verifying these constraints on a real API call (skip gracefully if Polymarket unreachable). Grep confirms: whale_count and price range are not tested in any existing test file.

---

## HIGH PRIORITY — Code Review

These tasks are a structural code review — not testing functionality, but reading the code to find bugs, security holes, and logic errors that tests might miss. Write findings as comments in a `tests/test_code_review.py` file or fix directly if small.

*(Auth review, SQL injection, CORS, tier gate completeness, scheduler correctness, Polymarket service review — all confirmed clean in code review 2026-03-26 and sessions 137–147. Removed to prevent re-auditing already-verified areas.)*

*(Dead code audit: completed session 167 — only 1 dead function found (tierBadge, 3 lines) and removed. All backend imports verified in use.)*


---

## NEW FEATURES (build AFTER all tests pass)

- [ ] **Basket consensus alert** — when 3+ followed bettors all take the same side on the same market within a short window, fire a "basket consensus" notification (stronger signal than single-whale alert). Implementable in `scheduler.py` by aggregating positions across followed bettors per conditionId before dispatching. No new external APIs needed. (Source: phemex.com Wallet Baskets Strategy, session 163)

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
