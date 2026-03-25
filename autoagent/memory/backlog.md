# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Pricing section uplift — elevate the Basic card (translateY(-8px), 2px accent glow border, "Most Popular" badge), add a feature comparison list per card, add "Cancel anytime · No credit card for Free" trust line under the CTAs
- [ ] Follows tab dashboard feel — add a summary row at the top (total followed, active bets in last 24h, P&L indicator), style the bettor cards on the follows page with a richer layout matching the leaderboard card quality
- [ ] Win Rate computation — session 75 added the Win Rate slot in the 2x2 leaderboard grid but it shows "—"; compute win rate from activity data in `polymarket.py` (profitable bets / total bets from the last 20 activity records), expose as `win_rate_pct` in bettor profile API response, and render it in the card. **Note: backend change required (polymarket.py) — skip in UI/UX-only mode; pick this when backend mode resumes**

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
