# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Win Rate computation — session 75 added the Win Rate slot in the 2x2 leaderboard grid but it shows "—"; compute win rate from activity data in `polymarket.py` (profitable bets / total bets from the last 20 activity records), expose as `win_rate_pct` in bettor profile API response, and render it in the card. **Note: backend change required (polymarket.py) — skip in UI/UX-only mode; pick this when backend mode resumes**
- [ ] Playwright screenshot gallery — capture screenshots of all 7 major screens (landing, leaderboard, profile, follows, alerts/settings, pricing, auth form) and save to `autoagent/reports/screenshots/`. Required by NORTH_STAR.md. Add 7 Playwright checks that each screen renders without JS errors and save PNG files.
- [ ] Mobile UX audit — test all 7 screens at 375px width: check text truncation, button tap targets (min 44px), card layout, bottom nav accessibility, and any horizontal overflow. Fix any issues found.


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
