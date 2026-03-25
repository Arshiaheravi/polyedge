# Backlog

---

## HIGH PRIORITY — Security & Vulnerability Tests

- [ ] SQL injection tests — try `' OR '1'='1`, `; DROP TABLE users; --` in email/address/name fields on register, login, follows, bettors endpoints — assert 4xx returned, never 500, DB intact after
- [ ] XSS payload tests — inject `<script>alert(1)</script>` and `"><img src=x onerror=alert(1)>` into name field on register, market_question stored in BetEvent — assert stored safely (escaped), never executed
- [ ] Auth bypass tests — call every protected endpoint with: no token, wrong token, token from deleted user, token with tampered payload, token with modified tier claim — all must return 401 or 403
- [ ] Tier enforcement bypass — create free user, manually craft POST /follows requests to exceed limit=1 — assert 403 on 2nd follow regardless of request manipulation

---

## HIGH PRIORITY — Frontend Playwright Tests

- [ ] Full register → login → follow flow — Playwright: open http://localhost:3000, click Sign Up, fill form, submit, assert redirected to dashboard, assert leaderboard loads with bettor cards, click Follow on first bettor, assert follow confirmed
- [ ] Login error states — Playwright: try wrong password → assert inline error shown (not alert box), try empty fields → assert validation error, assert no redirect on failure
- [ ] Leaderboard interactions — Playwright: assert bettor cards render, click sort buttons and assert order changes, type in search box and assert filtering works, scroll to bottom and assert back-to-top FAB appears
- [ ] Profile page flow — Playwright: click View Profile on any bettor card, assert profile page loads with name + stats + recent bets, assert recent bets show outcome (Yes/No) not empty, click Back and assert return to leaderboard

---

## HIGH PRIORITY — Backend Coverage Gaps

- [ ] GET /follows/live — test with VIP user following 3 bettors where get_active_positions raises for all 3 — assert still returns 3 entries with empty active_positions, not a 500
- [ ] Admin MRR formula — assert `basic_users * 4.99 + vip_users * 9.99` (not old 14.99 formula), test with 2 basic + 3 VIP users

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
