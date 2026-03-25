# Backlog

---

## HIGH PRIORITY — Security & Vulnerability Tests

---

## HIGH PRIORITY — Code Quality Audit (MANDATORY — work count hit 90, multiple of 5)

- [ ] Code quality audit — sessions 118–120 changed files: `backend/tests/test_cors.py`, `autoagent/playwright_registry.py` (checks 89-98). Run all 9 virtual team checks: Marcus (XSS greps on index.html), Sarah (no console.error, CSS vars), Priya (empty states), Jordan (trust signals), Nina (Playwright check count ≥98, no removed features), Leo (no TODO/FIXME), Alex (try/except on external calls), Ama (secrets not logged), Marcus (error message non-disclosure). Confirm XSS-free streak extends to sessions 77–120.

## HIGH PRIORITY — Frontend Playwright Tests

- [ ] Playwright CHECK 99-101 — (a) pricing locked features have `data-tip` attributes on `.dim` items, (b) account tab has `#acct-email` and `#acct-name` elements, (c) `#acct-tier-label` element present and has non-empty text content

---

## HIGH PRIORITY — Backend Coverage Gaps

---

## MEDIUM PRIORITY — Business Logic Tests

---

## FEATURE MODE ONLY — Agent Infrastructure Improvements

- [ ] Plankton write-time code quality enforcement — install ruff+biome+plankton hooks via settings.json; auto-formats Python (ruff) and HTML/JS (biome) on every file edit; blocks config tampering; delegates unfixable violations to subprocesses by tier. Requires: `pip install plankton-code-quality`, hooks in settings.json. See ECC skills/plankton-code-quality/SKILL.md.

## FEATURE MODE ONLY — Competitive Intelligence (from awesome-prediction-market-tools, 2026-03-25)

- [ ] Discord notification channel — add Discord webhook support to alert settings (competitors: Nevua Markets, PolyAlertHub all offer Discord; VIP differentiator alongside Telegram)
- [ ] Trade size minimum filter — let users set a minimum USD trade size threshold for alerts (e.g. only notify for bets >$500); reduces notification fatigue from frequent small bets (PolyTrack, Polycool both offer this)
- [ ] "Edge Score" composite bettor metric — add a 1-10 conviction/edge score to leaderboard cards combining win rate + profit + volume; replaces Win Rate placeholder with actionable composite (future.fun Edge Score, PolyVision Copy Score both have this)
- [ ] Delayed free tier alerts — offer 15-min delayed alerts to free users as "upgrade preview" (Whale Tracker Livid model: $0 = 1-hour delay, $29/mo = real-time); shows users what they're missing

---

## BLOCKED — Needs User Action

- [ ] Configure real Stripe price IDs (STRIPE_BASIC_PRICE_ID, STRIPE_VIP_PRICE_ID) — requires user to update backend/.env
- [ ] Configure TELEGRAM_BOT_TOKEN — requires user to create bot via @BotFather
