# Skill: Virtual Senior Dev Team Audit

**When to use**: After every WORK session, before committing. Read this file and run each team member's checklist against the files changed this session. Fix all issues found. Issues too large to fix now → append one line to `autoagent/memory/tech_debt.md`.

**How to use**:
1. Get changed files: read `autoagent/memory/project_root.md` for the project path, then `git -C "[PROJECT_ROOT]" diff --name-only HEAD` (or use staged diff if pre-commit)
2. For each team member below: re-read the changed files through that lens and ask "Would this person approve this PR?"
3. Fix every issue immediately unless it's too large (>30 min)
4. Never commit with a known Marcus (security) failure — those are always blocking
5. Log deferred issues to `autoagent/memory/tech_debt.md`: `[DATE] [FILE] [TEAM MEMBER] — [issue description]`

---

## TEAM MEMBER 1 — Alex, Staff Backend Engineer (10 years Python/FastAPI)

Mandate: the backend must be bulletproof, consistent, and scalable.

**Checklist**:
- [ ] Every new route follows: routes/ imports services/, services/ imports nothing from routes/ — one-way dependency only
- [ ] No logic in routes — routes call service functions, services do the work
- [ ] Every external network call (third-party APIs, webhooks, scrapers) is wrapped in try/except with a logged warning and graceful fallback — never crashes the endpoint
- [ ] No N+1 DB queries — batch queries where multiple rows are needed
- [ ] No blocking I/O on the async event loop — use `run_in_executor` for all sync calls
- [ ] All new Pydantic models have `model_config` set correctly
- [ ] New DB models auto-create on `create_app()` startup — never require manual migration
- [ ] Config variables go in `config.py` with a default — never raw `os.getenv()` scattered in routes
- [ ] API responses always snake_case — no camelCase in JSON responses
- [ ] New endpoints added to `app.py` via `app.include_router()`

---

## TEAM MEMBER 2 — Sarah, Senior Frontend Engineer (8 years JS/CSS)

Mandate: the UI must be polished, consistent, and never leave the user confused.

**Checklist**:
- [ ] Frontend files follow project structure from `autoagent/PROJECT.md` — no new separate files unless the project pattern allows it
- [ ] Every API call has: loading state (spinner or skeleton), success state, error state with user-friendly message
- [ ] New UI elements use existing CSS variables and design patterns — no one-off inline styles
- [ ] Theme/dark mode consistent with existing color variables defined in the project
- [ ] Mobile-first: every new element visible and functional at 375px, 768px, 1280px
- [ ] No `console.error` left in production code
- [ ] New interactive elements have hover states and `cursor:pointer`
- [ ] Loading skeletons shown immediately — never a blank white flash

---

## TEAM MEMBER 3 — Marcus, Application Security Engineer (OWASP certified)

Mandate: zero security regressions. One vuln ships = company trust destroyed.

**BLOCKING — never commit with a Marcus failure.**

**Checklist**:
- [ ] No hardcoded secrets, API keys, passwords, or tokens anywhere in source files
- [ ] All user-supplied input rendered via `textContent` or escaped — never `innerHTML` with user data (XSS)
- [ ] All DB queries use SQLAlchemy ORM or parameterized statements — never f-string SQL (injection)
- [ ] No IDOR: every DB query that returns user data filters by `current_user.id` — users cannot access other users' data
- [ ] Admin routes check password/JWT — never accessible unauthenticated
- [ ] JWT secret is from `settings.jwt_secret_key` — never hardcoded
- [ ] Sensitive data (passwords, API keys, card numbers) never appear in log output
- [ ] CORS settings not widened beyond what's in config
- [ ] HTTP error responses use generic messages — no stack traces, DB error strings, or file paths in 4xx/5xx JSON. `{"detail": "Internal server error"}` not `{"detail": "sqlalchemy.exc.NoResultFound: ..."}`

---

## TEAM MEMBER 4 — Priya, Senior UX Engineer + Product Designer (fintech specialist)

Mandate: every user interaction must feel intentional, clear, and trustworthy — especially for financial data.

**Checklist**:
- [ ] Every new feature has an empty state design (what does the page look like with zero data?)
- [ ] Every destructive action (cancel subscription, delete watchlist) has a confirmation step
- [ ] Error messages are human-readable — "Could not load signals — try refreshing" not "500 Internal Server Error"
- [ ] Success actions have a visible confirmation (toast, green badge, updated number)
- [ ] Free-tier paywalls are respectful — show value first, then the lock. Never hide content without explaining why.
- [ ] New pages have a clear page title and one primary action per screen
- [ ] Core UI components maintain consistent anatomy — check `autoagent/PROJECT.md` for the UI component spec
- [ ] No layout shift when data loads — reserve space with skeletons before content arrives

---

## TEAM MEMBER 5 — Jordan, Growth Engineer + Performance Marketer

Mandate: every feature must either acquire users, retain users, or convert free→paid.

**Checklist**:
- [ ] Every Pro/Elite feature visible to free users with a locked overlay and upgrade CTA — free users should always know what they're missing
- [ ] New pages that could rank on Google have `<title>`, `<meta name="description">`, and JSON-LD structured data
- [ ] Track Record / verified returns always visible above the fold on landing — this is the #1 conversion driver
- [ ] Email alerts include the product logo, key summary, and a CTA back to the app — every email is a re-engagement touchpoint
- [ ] New features that could be shared (signal cards, trade results) have a share/copy button
- [ ] Upgrade modal shown after free user hits any gated feature — never a 403, always a conversion opportunity
- [ ] Any new metric tracked (win rate, avg return, # signals) shown publicly on the landing page if it makes the product look good

---

## TEAM MEMBER 6 — Chen, Financial Analyst + Compliance Officer (Canadian securities)

Mandate: no legal exposure. The product must never cross applicable regulatory lines (financial advice, privacy, consumer protection).

**Checklist**:
- [ ] No copy promises specific outcomes or guaranteed results — check project's legal/compliance notes in `autoagent/PROJECT.md`
- [ ] Required disclaimers are present on regulated features (read `autoagent/PROJECT.md` for what applies to this project)
- [ ] No new features that take irreversible actions (trades, charges, sends) without explicit user consent and confirmation
- [ ] Stats and metrics displayed with sample size where relevant: "65% (n=42)" not just "65%"

---

## TEAM MEMBER 7 — Ama, Staff DevOps + Reliability Engineer

Mandate: the system must stay up, stay fast, and never silently fail.

**Checklist**:
- [ ] No new endpoint exceeds 2s response time on warm cache — check with `curl -o /dev/null -s -w "%{time_total}" [BACKEND_URL]/api/...` (read backend_url from `autoagent/PROJECT.md`)
- [ ] New background jobs use APScheduler (already in codebase) — never raw threads or bare asyncio tasks
- [ ] All background jobs have error logging — silent failures are invisible failures
- [ ] New DB queries hit indexed columns — no full table scans on large tables
- [ ] Cache TTL set appropriately: market data 5min, user data 1min, static data 1hr
- [ ] No infinite loops or unbounded retries in background jobs
- [ ] New yfinance/external calls respect rate limits — use batch endpoints, not individual calls in loops

---

## TEAM MEMBER 8 — Leo, Senior Technical Writer + Code Consistency Enforcer

Mandate: the codebase must be readable and consistent — a new developer should understand any file in 5 minutes.

**Checklist**:
- [ ] No dead code left behind — removed features fully deleted, not commented out
- [ ] No duplicate logic — if the same calculation appears twice, it's in a shared service function
- [ ] Function names are verbs: `calculate_rsi()`, `get_screened_tickers()`, `send_play_alert()` — not `rsi()` or `tickers()`
- [ ] New files follow existing naming convention: routes use noun (dashboard.py, admin.py), services use noun (analysis.py, signals.py)
- [ ] No TODO comments left in committed code — either fix it or add to tech_debt.md
- [ ] `CLAUDE.md` updated if any new architectural pattern, convention, or file structure was introduced this session

---

---

## TEAM MEMBER 9 — Nina, QA Engineer + Accessibility Specialist

Mandate: every change must be regression-tested against what already works. No feature should silently break something else. No removed feature should reappear.

**Checklist**:
- [ ] **Removed features stay removed**: Check `autoagent/PROJECT.md` "REMOVED FEATURES" list — none of those sections, nav links, or JS functions reappear in any changed file
- [ ] **Light mode + dark mode**: Any element with a dark background (`rgba(15,23,42`, `#0d1117`, `#161b22`) must have a `[data-theme="light"]` override if it lives in a user-facing section
- [ ] **Navigation consistency**: Nav items in desktop nav and mobile nav must match — if a page exists, it's in both; if a page is removed, it's gone from both
- [ ] **Logic accuracy gate**: If any core calculation or scoring function was changed, run the project's test suite (see `autoagent/PROJECT.md` for the test command) and verify all critical tests pass.
- [ ] **No partial implementations**: Every frontend UI element that calls an API must have a corresponding working endpoint. No buttons that 404, no tabs that show empty state because the route wasn't wired.
- [ ] **Pricing accuracy**: The pricing modal in `index.html` must accurately reflect what the backend actually enforces (tier limits, market access). If you change backend tier logic, update the pricing modal too.
- [ ] **Console clean**: After any frontend change, the Playwright check (playwright.md) must report zero JS errors. Warnings are okay, errors are not.
- [ ] **Feature explanations**: Any complex feature (pattern detection, score breakdown, market regime) must have a tooltip, info icon, or explanatory text visible to the user. If you add a chip or metric, add its explanation too.

---

## Quick reference — which checklist for which change type

| Change type | Must check |
|-------------|-----------|
| New FastAPI route | Alex (architecture), Marcus (security), Priya (UX empty states) |
| New DB model | Alex (migration), Ama (indexes + background jobs) |
| New frontend component | Sarah (UI consistency), Priya (UX), Jordan (conversion), Nina (light mode + regression) |
| New scoring function | Alex (data flow), Leo (naming), Nina (golden set gate), test coverage in testing.md |
| New external API call | Alex (try/except), Ama (rate limits + caching) |
| New paywall / gated feature | Jordan (upgrade CTA), Chen (compliance), Marcus (IDOR), Nina (pricing accuracy) |
| New config variable | Alex (config.py), Leo (naming) |
| Any change involving user data | Marcus (security) — always blocking |
| Removing a feature | Leo (dead code fully deleted), Nina (removed features list updated in PROJECT.md) |
| Changing tier logic | Nina (pricing accuracy), Jordan (upgrade CTAs still work) |
