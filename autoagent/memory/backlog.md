# Backlog

## HIGH PRIORITY — Testing

- [ ] **Leaderboard accuracy vs profile accuracy cross-check** — `test_leaderboard_vs_profile_pnl_consistent` in test_data_integrity.py verifies pnl_usd is consistent between leaderboard and profile endpoints, but does NOT check the `accuracy` field. Add a companion test that for the top bettor, if `accuracy` is non-null in the leaderboard response, the profile endpoint returns the same value (within ±0.02 tolerance). Grep: no test for accuracy cross-validation exists.

- [ ] **get_settings() lru_cache test** — Bug #9 from PROJECT.md: `get_settings()` creates a new Settings() object on every call instead of being cached with `@lru_cache`. Add `@lru_cache` to `get_settings()` in config.py AND add a unit test verifying that two calls to `get_settings()` return the same object instance (`assert get_settings() is get_settings()`). Grep: no test for settings identity/caching exists. Confirmed no test covers this path.

- [ ] **Copy simulator open-bet skip unit test** — `compute_copy_simulator` skips bets that are <7 days old and NOT in redeemed_ids (still-open bets). Add a unit test with one still-open bet (timestamp = now - 1 day, not in redeemed_ids) to confirm it is excluded from bets_analysed. Currently no unit test covers the "still open → skip" branch. Grep: no test for open-bet exclusion in compute_copy_simulator.

- [ ] **Auth /me response field audit** — verify that GET /auth/me never returns `hashed_password`, `stripe_customer_id`, or `telegram_chat_id` fields. Add an explicit assertion test in test_auth.py that fetches /auth/me and asserts none of these sensitive keys appear in the response JSON. Grep: existing `test_me_endpoint` tests check for correct fields but do not explicitly assert absence of sensitive fields.

---

## MEDIUM PRIORITY — Edge Cases & Reliability

- [ ] **Bot filtering on leaderboard** — flag or exclude Polymarket accounts with suspiciously uniform bet timing (e.g. always placing identical size bets at consistent intervals = algorithmic trader). Reduces noise in the followed-bettor list for copy-traders. Add `is_bot_suspected` flag to leaderboard normaliser. (Source: competitor research, session 143)

- [ ] **Configurable scheduler poll interval** — add `POLL_INTERVAL_SECONDS` to config.py (default 30); read in scheduler.py instead of hardcoded `30`. Allows tightening to 10s during high-traffic events without code changes. (Source: FastAPI SaaS best practices 2026, session 143)

- [ ] **Empty follows state** — Playwright: log in as new user with no follows, open Follows tab, assert empty state message shown (not crash)

---

## HIGH PRIORITY — Code Review

These tasks are a structural code review — not testing functionality, but reading the code to find bugs, security holes, and logic errors that tests might miss. Write findings as comments in a `tests/test_code_review.py` file or fix directly if small.

*(Auth review, SQL injection, CORS, tier gate completeness, scheduler correctness, Polymarket service review — all confirmed clean in code review 2026-03-26 and sessions 137–147. Removed to prevent re-auditing already-verified areas.)*

*(Dead code audit: completed session 167 — only 1 dead function found (tierBadge, 3 lines) and removed. All backend imports verified in use.)*

---

## NEW FEATURES (build AFTER all tests pass)

- [ ] **WebSocket scheduler (replace 30s REST poll)** — Replace `_poll_bets` and `_poll_vip_bets` REST polling with a Polymarket WebSocket subscription to `wss://ws-subscriptions-clob.polymarket.com/ws/markets`. As of January 2026, the 100-instrument cap on the Markets channel was removed (now supports 500 per socket), making this fully viable for PolyEdge's bettor pool. Impact: notification latency drops from ~30s to near-real-time for ALL tiers, eliminating the need for the separate VIP 5s poll job. Closes the latency gap vs PolyCop/PolyGun without any additional polling cost. (Source: docs.polymarket.com/market-data/websocket/overview, session 173)

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
