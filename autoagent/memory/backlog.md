# Backlog

---

## HIGH PRIORITY — UI/UX Tasks (doable in current UI/UX-only mode)

- [ ] Nav/header improvements — add active state to nav links, smooth scroll behavior, add a subtle top progress bar on page load
- [ ] Hero section polish — improve landing page hero: bigger headline, animated value-prop subtext, pulsing CTA button, and a live stat counter (e.g. "100 traders tracked · $2M+ profit tracked")
- [ ] Bettor profile rich stats — replace the 4 plain stat cards on the profile page with gradient-border cards that have micro-sparklines or trend arrows (up/down since last week)
- [ ] Demo mode landing page — add a "Try the demo" CTA on the hero that loads a pre-populated leaderboard with 5 anonymized demo bettors (client-side mock data, zero backend) so visitors can experience the UI before registering. Research shows interactive demos convert 2x better than static screenshots (aimers.io CRO 2026)

---

## BACKEND PENDING (blocked — current mission is UI/UX-only; pick when backend mode resumes)

- [ ] Win Rate computation — compute from activity data in `polymarket.py` (profitable bets / total bets from last 20 records), expose as `win_rate_pct` in bettor profile API, render in the 2×2 leaderboard card slot currently showing "—".
- [ ] Empowerment-framed bet notification copy — change `dispatch_bet_notification()` in `services/notifications.py` from "0xABCD placed a bet on [Market]" to "Top bettor you follow just moved on [Market] — 68% win rate this month".
- [ ] @lru_cache on get_settings() — add `@functools.lru_cache()` to `get_settings()` in `backend/app/config.py`. 2-line change, zero risk.
- [ ] Per-bettor notification budget — add `max_alerts_per_bettor_per_day` to `AlertSetting` model; scheduler skips if daily limit reached per bettor.
- [ ] WebSocket real-time notifications — replace 30s APScheduler polling with Polymarket's `/v1/ws/markets` WebSocket. Reduces detection latency from ~30s to ~1s; key VIP differentiator. Change in `scheduler.py`.

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
