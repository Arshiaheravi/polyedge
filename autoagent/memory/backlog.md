# Backlog

---

## HIGH PRIORITY — UI/UX Tasks

- [ ] Pricing section redesign — 3 cards (Free / Basic / VIP), highlight Basic as "Most Popular" with a badge, show feature checklist per tier, add a subtle animated border on the recommended plan, make upgrade CTA buttons prominent
- [ ] Global CSS variables & typography overhaul — define consistent color palette (:root CSS vars), upgrade font stack to Inter or similar system font, set heading scale (h1-h4), ensure 8px spacing grid is consistent across all sections
- [ ] Animations & micro-interactions — add smooth fade-in on page load, hover lift on all cards, button press feedback (scale down), smooth section transitions; use CSS transitions only (no heavy JS animation libs)
- [ ] Generate hero background image using Nano Banana API and wire into hero section with CSS fallback gradient
- [ ] Empty state illustrations — add helpful illustrated empty states for: no follows yet, no alerts configured, leaderboard loading; use CSS-generated or Nano Banana API
- [ ] Mobile responsiveness audit — test every screen at 375px width, fix any horizontal overflow, ensure nav/header works on mobile, make cards stack vertically, make buttons full-width on mobile
- [ ] Bettor profile page — add click-through from leaderboard cards to a profile page showing bettor stats, recent bets timeline, and a prominent Follow/Unfollow CTA
- [ ] Login/Register modal polish — clean up form design, add smooth open/close animation, add password visibility toggle, improve error message styling (red inline, not alert box)

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
