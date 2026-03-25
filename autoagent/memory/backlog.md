# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Win Rate computation — session 75 added the Win Rate slot in the 2x2 leaderboard grid but it shows "—"; compute win rate from activity data in `polymarket.py` (profitable bets / total bets from the last 20 activity records), expose as `win_rate_pct` in bettor profile API response, and render it in the card. **Note: backend change required (polymarket.py) — skip in UI/UX-only mode; pick this when backend mode resumes**
- [ ] Account tab redesign (logged-in state) — when a user is logged in, `renderAccount()` currently shows minimal info; upgrade it to show: user avatar/initials, username, current plan badge (Free/Basic/VIP with color), plan upgrade CTA if on Free, and a styled logout button. Frontend-only change to `renderAccount()`.
- [ ] Leaderboard sort controls upgrade — the 3 sort buttons (Profit / Win Rate / Volume) currently have basic active states; upgrade with: pill-style toggle group (one visible active pill), smooth 0.2s transition, tooltip on hover explaining what each metric means (e.g. "Total USD profit on Polymarket"), and a subtle count badge showing how many bettors qualify.


- [ ] Empowerment-framed bet notification copy — change Telegram/push alert message from "0xABCD placed a bet on [Market]" to "Top bettor you follow just moved on [Market] — 68% win rate this month". Frame the alert as an edge, not a data dump. Change in `services/notifications.py` dispatch_bet_notification(). **Backend change required.**
- [ ] @lru_cache on get_settings() — add `@functools.lru_cache()` decorator to `get_settings()` in `backend/app/config.py` so Pydantic reads the .env file exactly once at startup rather than on every request. 2-line change, zero risk.
- [ ] Per-bettor notification budget — add `max_alerts_per_bettor_per_day` column to AlertSetting model (default: unlimited). Scheduler checks this before firing notification — if user already received N alerts from bettor X today, skip. Prevents one prolific bettor spamming the notification feed.

---

## MEDIUM PRIORITY

- [ ] Nav/header improvements — add active state to nav links, smooth scroll behavior, add a subtle top progress bar on page load
- [ ] Trust signals section — add "Built on real Polymarket data" text badge near leaderboard header; show live total bet count (fetch from `/admin/stats` if available or derive from leaderboard data). **Note**: "How it works 3-step section" was completed in session 84 — do NOT re-implement it.
- [ ] Color-coded profit/loss — verify consistency: sessions 75/80/83 added green/red profit badges on leaderboard cards, profile hero, and follow cards. Check that the follows activity grid (renderPositionItem) also colors P&L correctly. If already done everywhere, remove this item.
- [ ] WebSocket real-time notifications — replace the 30s APScheduler polling loop with Polymarket's WebSocket endpoints (`/v1/ws/markets`, `/v1/ws/private`) for instant bet detection. Key VIP tier differentiator — reduces detection latency from ~30s to ~1s. Backend change: scheduler.py. **Note: backend change required — skip in UI/UX-only mode.**

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
