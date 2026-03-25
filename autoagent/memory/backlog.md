# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Toast notification stack — vanilla JS custom event dispatcher; push trade alert toasts from bottom-right; stack with 8px gap, auto-dismiss after 5s; use for "New bet detected" events on follows page
- [ ] Bet activity feed enhancements — add probability pill (YES 72¢ green / NO 28¢ red) to each bet row in bettor profile; add market status badge (Open/Closed/Resolved) using CSS date comparison; helps user judge if trade is still copyable

---

## MEDIUM PRIORITY

- [ ] Notification/alerts settings page redesign — replace raw form with toggle switches, add status indicators (connected/disconnected) for Telegram and web push, add a "Test notification" button
- [ ] Nav/header improvements — add active state to nav links, smooth scroll behavior, add a subtle top progress bar on page load
- [ ] Loading skeleton screens — replace any spinner with skeleton placeholder cards while data loads (leaderboard, follows list)
- [ ] Trust signals section — add "Built on real Polymarket data", show live bet count ticker, add a "How it works" 3-step section with icons
- [ ] Color-coded profit/loss — green for positive P&L, red for negative, consistent across all cards and tables

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
