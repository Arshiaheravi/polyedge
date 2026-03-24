# Backlog

---

## HIGH PRIORITY — Testing tasks (DEBUG MODE)

*(replenish when empty — see DEBUG MODE rules in PROMPT.md)*

- [ ] GET /follows for basic tier reports limit=5 in response — TIER_LIMITS["basic"]=5 branch in the list endpoint; only free (limit=1) and VIP (limit=999999) GET responses are explicitly tested; add: upgrade user to basic, GET /follows, assert tier="basic" and limit=5
- [ ] Scheduler outer exception path leaves _last_check unchanged — mock db.commit() to raise so the outer `except Exception as exc: logger.error(...)` handler fires; verify scheduler_module._last_check is still datetime(2000,1,1) (not updated); this ensures a failed poll doesn't skip bets on the next run
- [ ] PUT /alerts/settings with valid JSON push_subscription stores and GET retrieves it — the PUT success path for non-None push_subscription; PUT {"push_subscription": '{"endpoint":"https://ex.com","keys":{"auth":"a","p256dh":"b"}}'}, then GET and assert push_subscription is a dict with "endpoint" key; guards against the json.loads() path breaking silently


---

## FEATURE MODE ONLY — skip in DEBUG MODE

- [ ] Switch scheduler from polling to Polymarket WebSocket (/v1/ws/markets or /v1/ws/private) for real-time bet detection — current 30s poll misses the <30s information arbitrage window; WebSocket pushes trade events instantly; eliminates polling entirely; critical for VIP tier's "fastest alerts" promise (Source: docs.polymarket.com WebSocket docs 2026)
- [ ] Add win_rate and total_trades fields to bettor leaderboard display — whale-following research confirms users need "50+ trades + 60%+ win rate" to make smart follow decisions; Polymarket API /profiles endpoint returns this data, just not surfaced in UI
- [ ] Reduce scheduler polling to 15s for VIP tier — information arbitrage window on Polymarket is <30s; current 30s polling misses the fastest edge; VIP users pay for speed, this justifies the tier price
- [ ] Add Alembic migration setup — current `Base.metadata.create_all()` destroys schema history; Alembic enables zero-downtime column additions and PostgreSQL migration path when scaling; add `alembic init`, create initial migration from existing models
- [ ] Add Discord webhook notification channel — competitor analysis (Polycop) shows users explicitly request Discord alongside Telegram; add `discord_webhook_url` to AlertSetting model and `send_discord()` to notifications.py; VIP tier feature
- [ ] Show entry price in bet notifications — competitor analysis (stand.trade) shows cost-basis visibility is top user request; include entry price and implied probability in Telegram/push notification body
- [ ] Add "conviction score" to bettor profiles — compute ratio of directional-only bets vs. offsetting Yes/No pairs from activity data; surfaces whether a bettor has conviction or is farming liquidity rewards; unique differentiator not offered by any competitor
- [ ] Add outbox pattern for reliable notification dispatch — currently scheduler fires notifications inline; write bet events to an `outbox` DB table atomically, then dispatch from a relay loop; prevents missed notifications on partial failure (Source: async-database-access-patterns 2026)
- [ ] Add GET /bettors/{address}/playbook endpoint — returns latest open positions as copy-ready instructions (market, side, entry size); competitor analysis shows this is top UX gap vs. stand.trade and Polycop; FEATURE MODE ONLY
- [ ] Add hourly leaderboard cache refresh via second APScheduler job — current /bettors makes a live Polymarket API call on every request; competitors refresh rankings hourly and serve from cache; add scheduler job every 60min to refresh top-100 into a DB-backed cache (Source: HolyPoly competitor analysis 2026)
- [ ] Add Server-Sent Events (SSE) endpoint for real-time bet notifications in browser — current web push uses VAPID which requires browser permission; SSE via `/events/user/{id}` is simpler and doesn't require push permission; yield events from an in-process queue; clients subscribe and get instant bet alerts (Source: medium.com FastAPI SSE patterns 2026)
- [ ] Migrate scheduler to ARQ + Redis if scaling beyond single server — APScheduler is fine for single-server; ARQ (asyncio-native) with Redis broker handles multi-worker deployments without forking; drop-in replacement for APScheduler periodic jobs (Source: davidmuraya.com ARQ vs APScheduler FastAPI 2026)

---

## MEDIUM PRIORITY — Frontend E2E: remaining pages

- [ ] Playwright: bettor profile page — NOTE: no click-through exists yet in the frontend (leaderboard rows have no onclick). This task requires first building the UI navigation to /bettors/{address}, THEN adding the Playwright check. Skip until the feature is built.

---

## LOW PRIORITY — Blocked on external input

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) so payments work end-to-end — requires Seb to update .env
- [ ] Set up git remote so commits can be pushed — requires Seb to create remote repo
- [ ] Configure TELEGRAM_BOT_TOKEN so live Telegram notifications work — requires Seb to create a bot via @BotFather
