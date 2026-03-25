# Backlog

---

## HIGH PRIORITY — UI/UX Tasks (doable in current UI/UX-only mode)

*(all previous tasks completed in sessions 109-110 — generating new tasks)*

- [ ] Bettor profile page visual upgrade — (1) add animated sparkline SVG under profit stat (fake data for now); (2) add "Copy Address" button next to wallet address with clipboard feedback; (3) add bet history row color coding (green row for YES bets, red for NO bets); (4) add a "Performance" section with win/loss ratio bar
- [ ] Landing page testimonials section upgrade — (1) replace plain testimonial cards with carousel/slider (auto-scroll every 5s, pause on hover); (2) add star rating display (⭐⭐⭐⭐⭐) to each testimonial; (3) add avatar placeholder circle to each testimonial card
- [ ] Mobile follow flow friction reduction — (1) on mobile, tapping a bettor card opens a bottom sheet (slide-up panel) with profile preview + Follow CTA instead of navigating away; (2) after following, show a ✓ confetti micro-animation for 0.8s; (3) add swipe-to-unfollow gesture on follows list items

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
