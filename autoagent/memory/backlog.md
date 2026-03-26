# Backlog

## HIGH PRIORITY — Testing

- [ ] **GET /markets/consensus: cache hit path (markets.py:30)** — every existing test clears `_consensus_cache` before calling the endpoint, so the cache-hit branch (`signals = _consensus_cache["data"]`) is never exercised. Add test: pre-populate `_consensus_cache["data"]` with known signals and set `_consensus_cache["ts"]` to `time.time()` (fresh), mock `get_consensus_signals` to assert it is NOT called, verify the route returns the pre-populated data. Grep: `grep -rn "def test.*consensus.*cache.*hit\|_consensus_cache.*time" backend/tests/` returns nothing.

- [ ] **get_current_user_optional: JWT with no sub claim → returns None (auth.py:72-73)** — the path where `payload.get("sub")` is None is not covered. Add test: craft a JWT with no `sub` field (use `jwt.encode({"role": "ghost"}, SECRET, "HS256")`), call GET /markets/consensus with it as Bearer token, verify response is 200 and `tier == "free"` (treated as anonymous). Grep: `grep -rn "def test.*optional.*no.sub\|sub.*None.*optional\|no.*sub.*claim" backend/tests/` returns nothing.

- [ ] **send_telegram_message: HTTP exception path returns False (notifications.py:27-29)** — the exception handler returning `False` and logging the warning is not covered. Add test: mock `httpx.AsyncClient` to raise `httpx.ConnectError`, call `send_telegram_message("bot_token", "chat_123", "hello")` directly, assert result is `False`. Grep: `grep -rn "def test.*telegram.*fail\|ConnectError.*telegram\|send_telegram.*exception" backend/tests/` returns nothing.


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

- [ ] **Personalized notification body** — embed the bettor's leaderboard rank + the user's first name in every notification message (e.g. "Hey Alex — #7 ranked whale just bet $5,000 on [market]"). Requires one DB query per alert for the bettor's rank. Industry benchmarks show named notifications get 2x CTR vs generic. TIER GATE: Basic/VIP. (Source: pushwoosh.com fintech push benchmarks, session 183)

- [ ] **Outbound webhook notification channel** — add `webhook_url` field to `AlertSetting`; in `dispatch_bet_notification()` fire an HTTP POST with the bet payload to the user's webhook URL (Zapier/Slack/custom scripts). No competitor at the free/basic tier offers this. Implementable: `httpx.post(webhook_url, json=payload)` in notifications.py. TIER GATE: VIP only (power user feature). (Source: defiprime.com Polymarket ecosystem guide, session 183)

- [ ] **Delayed alerts for Free tier** — store notification in a queue when created; dispatch to Free-tier users after 10 minutes, Basic after 1 minute, VIP immediately (already polling at 5s). Creates concrete upgrade incentive — users experience the 10-minute lag before seeing the opportunity close. APScheduler supports delayed job scheduling natively. (Source: signals.coincodecap.com top Polymarket alert bots 2026, session 183)

- [ ] **Minimum bet size filter in AlertSetting** — add `min_bet_usd` field (default 0) to `AlertSetting`; in scheduler, skip `dispatch_bet_notification()` if `bet.amount_usd < user.alert_settings.min_bet_usd`. UI: slider or input on alerts settings page. Reduces noise for users who only want to know about large conviction bets. TIER GATE: Basic/VIP. (Source: pushwoosh.com behavioral segmentation research, session 183)

- [ ] Copy Ratio Setting — let users set a per-bettor copy ratio multiplier (0.1x, 0.25x, 0.5x, 1x) stored in BettorFollow table; show on follow cards as "Copy at 0.5x"; include copy_ratio in notification messages. TIER GATE: Basic/VIP only.

- [ ] Insider Score — 0-100 confidence score per bettor (win_rate × profit_usd × avg_conviction × bet_count / 50). Badge on leaderboard cards (green >70, yellow 40-70, gray <40). TIER GATE: badge visible to all; numeric score for Basic/VIP only.

- [ ] **Hedging position filter** — Before firing a notification, check if the bettor holds an offsetting position in the same market (YES + NO). Skip notification if offsetting positions cancel out — this is a liquidity farming position, not a directional bet. Reduces notification fatigue. Add `is_directional` flag to BetEvent. Stand.trade competitor already ships this. (Source: Polymarket copytrade-wars article, session 153)

- [ ] **SQLAlchemy production pool settings** — Set `pool_size=10, max_overflow=20, pool_pre_ping=True, pool_recycle=3600` in `database.py` before any PostgreSQL migration. `pool_pre_ping` tests connections before use and discards stale ones. Currently using SQLite defaults (single-file, no pool). (Source: zestminds.com FastAPI deployment guide, session 153)

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
