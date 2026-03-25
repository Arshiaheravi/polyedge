# Backlog

---

## HIGH PRIORITY — Security & Vulnerability Tests

---

## HIGH PRIORITY — Frontend Playwright Tests

- [ ] Mobile viewport tests — Playwright at 375px: assert landing page no horizontal scroll, assert nav renders correctly, assert bettor cards stack vertically, assert buttons >= 44px height, screenshot each screen
- [ ] Alerts/settings page — Playwright: login, navigate to Alerts tab, assert toggle switches present, assert Telegram section visible, assert no JS errors on page
- [ ] Pricing section — Playwright: scroll to pricing on landing, assert 3 pricing cards visible, assert Basic card has "Most Popular" badge, hover locked features and assert tooltip appears
- [ ] Empty follows state — Playwright: login as new user with no follows, navigate to My Follows, assert empty state card shown with CTA button, assert clicking CTA navigates to leaderboard

---

## HIGH PRIORITY — Backend Coverage Gaps

---

## MEDIUM PRIORITY — Business Logic Tests

---

## FEATURE MODE ONLY — Competitive Intelligence (from awesome-prediction-market-tools, 2026-03-25)

- [ ] Discord notification channel — add Discord webhook support to alert settings (competitors: Nevua Markets, PolyAlertHub all offer Discord; VIP differentiator alongside Telegram)
- [ ] Trade size minimum filter — let users set a minimum USD trade size threshold for alerts (e.g. only notify for bets >$500); reduces notification fatigue from frequent small bets (PolyTrack, Polycool both offer this)
- [ ] "Edge Score" composite bettor metric — add a 1-10 conviction/edge score to leaderboard cards combining win rate + profit + volume; replaces Win Rate placeholder with actionable composite (future.fun Edge Score, PolyVision Copy Score both have this)
- [ ] Delayed free tier alerts — offer 15-min delayed alerts to free users as "upgrade preview" (Whale Tracker Livid model: $0 = 1-hour delay, $29/mo = real-time); shows users what they're missing

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
