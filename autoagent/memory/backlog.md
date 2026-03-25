# Backlog

---

## HIGH PRIORITY — Code Quality

- [ ] Code quality audit — scan last 5 work sessions' changed files for cross-file coupling, test specificity degradation, and smells introduced by agent edits (sessions 108–113: frontend/index.html, playwright_registry.py, backend/tests/test_bettors.py, backend/tests/test_polymarket_service.py)

---

## HIGH PRIORITY — Security & Vulnerability Tests

- [ ] Password bcrypt hash storage — POST /auth/register, then query DB: verify User.hashed_password starts with `$2b$` and does NOT contain the plaintext password (proves bcrypt is used, never plaintext)
- [ ] Rate limiting: 10 rapid login attempts in a loop — none should return 500 (server must be stable under repeated auth requests even without rate limit enforcement)

---

## HIGH PRIORITY — Frontend Playwright Tests

---

## HIGH PRIORITY — Backend Coverage Gaps

- [ ] Stripe webhook basic-tier upgrade — simulate `checkout.session.completed` with metadata `{plan: "basic"}`, assert user tier changes free → basic and follow limit becomes 5


---

## MEDIUM PRIORITY — Frontend Playwright (More Screens)

- [ ] Mobile viewport tests — Playwright at 375px: assert landing page no horizontal scroll, assert nav renders correctly, assert bettor cards stack vertically, assert buttons >= 44px height, screenshot each screen
- [ ] Alerts/settings page — Playwright: login, navigate to Alerts tab, assert toggle switches present, assert Telegram section visible, assert no JS errors on page
- [ ] Pricing section — Playwright: scroll to pricing on landing, assert 3 pricing cards visible, assert Basic card has "Most Popular" badge, hover locked features and assert tooltip appears
- [ ] Empty follows state — Playwright: login as new user with no follows, navigate to My Follows, assert empty state card shown with CTA button, assert clicking CTA navigates to leaderboard

---

## MEDIUM PRIORITY — Business Logic Tests

- [ ] Subscription tier upgrade flow — simulate Stripe webhook `checkout.session.completed` event with valid payload, assert user tier upgraded from free → basic, assert follow limit now 5
- [ ] Subscription downgrade — simulate `customer.subscription.deleted` webhook, assert tier reverts to free, assert follow limit back to 1
- [ ] Notification gating — create free tier user with alert settings enabled, trigger bet notification, assert notification NOT sent (free tier blocked)
- [ ] JWT expiry — generate token with exp=1 second, wait 2 seconds, call /auth/me, assert 401 returned

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
