# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Leaderboard four-metric display — surface PnL%, win rate, volume, and follower count per card (OKX/copy-trading research: these are the 4 data points users act on); add "confidence horizon" label ("90-day history") next to win rate to reduce perceived risk
- [ ] Notification/alerts settings page redesign — replace raw form with toggle switches, add status indicators (connected/disconnected) for Telegram and web push, add a "Test notification" button
- [ ] Loading skeleton screens — replace any spinner with skeleton placeholder cards while data loads (leaderboard, follows list)

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
