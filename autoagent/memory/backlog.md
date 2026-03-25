# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Win Rate computation — session 75 added the Win Rate slot in the 2x2 leaderboard grid but it shows "—"; compute win rate from activity data in `polymarket.py` (profitable bets / total bets from the last 20 activity records), expose as `win_rate_pct` in bettor profile API response, and render it in the card. **Note: backend change required (polymarket.py) — skip in UI/UX-only mode; pick this when backend mode resumes**
- [ ] Hero live counter animations — implement countUp() on the 3 hero stats strip (animate from 0 to final value on page load using requestAnimationFrame); add number ticker that increments one of the live stats every 8s to signal real-time activity. Pure CSS/JS, no backend needed. Pattern already in design.md ANIMATION RULES.
- [ ] Pre-commit follow preview on leaderboard cards — on the leaderboard card follow button (not profile page — profile already has this from session 80): show a tooltip or popover "You'll be notified within 30s when [Name] bets" before confirming follow. Collapsed by default, appears on hover or focus of the follow button.
- [ ] Playwright screenshot gallery — capture screenshots of all 7 major screens (landing, leaderboard, profile, follows, alerts/settings, pricing, auth form) and save to `autoagent/reports/screenshots/`. Required by NORTH_STAR.md. Add 7 Playwright checks that each screen renders without JS errors and save PNG files.


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
