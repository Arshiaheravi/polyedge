# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Win Rate computation — session 75 added the Win Rate slot in the 2x2 leaderboard grid but it shows "—"; compute win rate from activity data in `polymarket.py` (profitable bets / total bets from the last 20 activity records), expose as `win_rate_pct` in bettor profile API response, and render it in the card. **Note: backend change required (polymarket.py) — skip in UI/UX-only mode; pick this when backend mode resumes**
- [ ] Auth form UX tightening — (1) add focus ring on the currently active input field (highlight the input border with --accent on :focus); (2) add show/hide animation when switching between Login and Register tabs (fade + translateY); (3) on mobile, the modal should be full-screen (100vh) not a floating card; (4) add a divider "or" with horizontal rules between the form submit and a future social login slot (pure UI placeholder, no backend needed)
- [ ] Leaderboard card progressive disclosure — clicking anywhere on .lb-card except the follow button expands it via CSS max-height transition to reveal: last 2 recent market titles (from leaderboard data if available, else "Recent markets loading..."), and a "View profile →" link. Collapsed state: existing 4-metric grid only. Use CSS max-height: 0 → max-height: 200px with overflow:hidden and a chevron indicator that rotates on expand.


---

## MEDIUM PRIORITY

- [ ] Hero live counter animations — implement countUp() on the 3 hero stats strip (animate from 0 to final value on page load using requestAnimationFrame); add number ticker that increments one of the live stats every 8s to signal real-time activity. Pure CSS/JS, no backend needed. Pattern already in design.md ANIMATION RULES.
- [ ] Nav/header improvements — add active state to nav links, smooth scroll behavior, add a subtle top progress bar on page load
- [ ] Trust signals section — add "Built on real Polymarket data" text badge near leaderboard header; show live total bet count (fetch from `/admin/stats` if available or derive from leaderboard data). **Note**: "How it works 3-step section" was completed in session 84 — do NOT re-implement it.
- [ ] Color-coded profit/loss — verify consistency: sessions 75/80/83 added green/red profit badges on leaderboard cards, profile hero, and follow cards. Check that the follows activity grid (renderPositionItem) also colors P&L correctly. If already done everywhere, remove this item.
- [ ] Pre-commit follow preview — on the LEADERBOARD follow button (not profile page — that already has it from session 80): before confirming follow, show a tooltip or inline preview "You'll be notified within 30s when [Name] bets". Profile page already has this; leaderboard cards do not yet.
- [ ] WebSocket real-time notifications — replace the 30s APScheduler polling loop with Polymarket's WebSocket endpoints (`/v1/ws/markets`, `/v1/ws/private`) for instant bet detection. Key VIP tier differentiator — reduces detection latency from ~30s to ~1s. Backend change: scheduler.py. **Note: backend change required — skip in UI/UX-only mode.**

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
