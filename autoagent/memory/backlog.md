# Backlog

---

## HIGH PRIORITY — UI/UX Tasks (doable in current UI/UX-only mode)

- [ ] Back-to-top FAB on browse leaderboard — when user scrolls >300px inside the browse `.main-content`, show a floating green ↑ button (fixed bottom-right, above mobile nav) that scrolls to top. Disappears when near top. Makes 100-item leaderboard easier to navigate.
- [ ] Animate "847+" social proof counter on hero — the hardcoded "847+" in the hero social proof `<strong>` should count up from ~800→847 via `animateCounter()` on page load (same pattern as hlstat-traders). Give it an ID e.g. `#hero-user-count`. Adds energy and implies the number is live.
- [ ] Pricing locked features upgrade nudge — add a CSS-only tooltip on `.pricing-features li.dim:hover::after` showing "Unlock with Basic →" on Free tier dim items and "VIP only →" on Basic tier dim items. `content` set via data-upgrade attribute on each `<li>`. Converts hover curiosity into upgrade intent.

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
