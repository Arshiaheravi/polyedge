# Backlog

---

## HIGH PRIORITY — Security & Vulnerability Tests

---

## HIGH PRIORITY — Frontend Playwright Tests

- [ ] Playwright checks 111-113 — logout flow + localStorage: (111) logout() function defined in window scope, (112) clearToken() sets localStorage pe_token to null (call clearToken() in evaluate and confirm getItem returns null), (113) #back-to-top-fab element present in DOM

- [ ] Playwright checks 114-116 — follows dashboard DOM: (114) #follows-empty element exists in DOM, (115) #follows-container element exists in DOM, (116) #follows-subtitle element exists in DOM with text content

---

## HIGH PRIORITY — Backend Coverage Gaps

---

## MEDIUM PRIORITY — Business Logic Tests

---

## FEATURE MODE ONLY — Agent Infrastructure Improvements

- [ ] Plankton write-time code quality enforcement — install ruff+biome+plankton hooks via settings.json; auto-formats Python (ruff) and HTML/JS (biome) on every file edit; blocks config tampering; delegates unfixable violations to subprocesses by tier. Requires: `pip install plankton-code-quality`, hooks in settings.json. See ECC skills/plankton-code-quality/SKILL.md.

## FEATURE MODE ONLY — Competitive Intelligence (from ericaai.tech.blog + coincodecap, 2026-03-25)

- [ ] Copy-ratio per bettor follow — add `copy_ratio` column (0.1x–1x float) to `BettorFollow` model; notifications include suggested position size = whale_size × copy_ratio; lets users size bets relative to whale's stake (PolyAlertHub, ericaai 2026 production pattern)
- [ ] Min-odds + max-exposure filters — add `min_odds_threshold` and `max_exposure_usd` columns to `AlertSetting`; notification dispatch skips bets below min odds or above max exposure (prevents pings on near-certain bets or whales going all-in)
- [ ] Market-launch alerts — separate notification category for NEW markets (not just new bets); bettors who follow a whale get alerted when a new market opens that whale has bet in; competitors advertise this as a distinct feature

## FEATURE MODE ONLY — Competitive Intelligence (from awesome-prediction-market-tools, 2026-03-25)

- [ ] Discord notification channel — add Discord webhook support to alert settings (competitors: Nevua Markets, PolyAlertHub all offer Discord; VIP differentiator alongside Telegram)
- [ ] Trade size minimum filter — let users set a minimum USD trade size threshold for alerts (e.g. only notify for bets >$500); reduces notification fatigue from frequent small bets (PolyTrack, Polycool both offer this)
- [ ] "Edge Score" composite bettor metric — add a 1-10 conviction/edge score to leaderboard cards combining win rate + profit + volume; replaces Win Rate placeholder with actionable composite (future.fun Edge Score, PolyVision Copy Score both have this)
- [ ] Delayed free tier alerts — offer 15-min delayed alerts to free users as "upgrade preview" (Whale Tracker Livid model: $0 = 1-hour delay, $29/mo = real-time); shows users what they're missing

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
