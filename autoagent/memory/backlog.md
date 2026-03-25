# Backlog

---

## HIGH PRIORITY — UI/UX Tasks (doable in current UI/UX-only mode)

- [ ] Leaderboard sort controls upgrade — the 3 sort buttons (Profit / Win Rate / Volume) currently have basic active states; upgrade with: pill-style toggle group (one visible active pill), smooth 0.2s transition, tooltip on hover explaining what each metric means (e.g. "Total USD profit on Polymarket"), and a subtle count badge showing how many bettors qualify.
- [ ] _disclosureCache TTL fix — leaderboard card disclosure cache never expires; add a TTL key alongside each entry (`{titles, ts: Date.now()}`) and re-fetch if older than 5 minutes. Pure frontend JS change in `_loadDisclosureMarkets`. See tech_debt.md.
- [ ] Nav/header improvements — add active state to nav links, smooth scroll behavior, add a subtle top progress bar on page load
- [ ] Trust signals section — add "Built on real Polymarket data" text badge near leaderboard header; show live total bet count (fetch from `/admin/stats` if available or derive from leaderboard data). **Note**: "How it works 3-step section" was completed in session 84 — do NOT re-implement it.
- [ ] Color-coded profit/loss — verify renderPositionItem (follows activity grid) colors P&L correctly. Sessions 75/80/83 added green/red badges on leaderboard, profile, and follow cards. If renderPositionItem already applies color, remove this item.

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
