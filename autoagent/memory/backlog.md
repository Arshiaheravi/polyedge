# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] **[META] Code quality audit** — scan last 5 work sessions' changed files (sessions 79–83) for cross-file coupling, test specificity degradation, and smells introduced by agent edits. (Added: 65 work sessions = multiple of 5)
- [ ] Win Rate computation — session 75 added the Win Rate slot in the 2x2 leaderboard grid but it shows "—"; compute win rate from activity data in `polymarket.py` (profitable bets / total bets from the last 20 activity records), expose as `win_rate_pct` in bettor profile API response, and render it in the card. **Note: backend change required (polymarket.py) — skip in UI/UX-only mode; pick this when backend mode resumes**
- [ ] Auth form UX tightening — (1) add focus ring on the currently active input field (highlight the input border with --accent on :focus); (2) add show/hide animation when switching between Login and Register tabs (fade + translateY); (3) on mobile, the modal should be full-screen (100vh) not a floating card; (4) add a divider "or" with horizontal rules between the form submit and a future social login slot (pure UI placeholder, no backend needed)
- [ ] Leaderboard card progressive disclosure — clicking anywhere on .lb-card except the follow button expands it via CSS max-height transition to reveal: last 2 recent market titles (from leaderboard data if available, else "Recent markets loading..."), and a "View profile →" link. Collapsed state: existing 4-metric grid only. Use CSS max-height: 0 → max-height: 200px with overflow:hidden and a chevron indicator that rotates on expand.


---

## MEDIUM PRIORITY

- [ ] Nav/header improvements — add active state to nav links, smooth scroll behavior, add a subtle top progress bar on page load
- [ ] Trust signals section — add "Built on real Polymarket data", show live bet count ticker, add a "How it works" 3-step section with icons
- [ ] Color-coded profit/loss — green for positive P&L, red for negative, consistent across all cards and tables
- [ ] Pre-commit follow preview — before confirming follow, show inline preview: "You will be notified within 30s when [Bettor Name] places a bet"; one-CTA enrollment flow; reduces follow abandonment

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
