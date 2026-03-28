# Project: PolyEdge

---

## CURRENT MISSION — GUARANTEE EVERYTHING WORKS

**The agent's job is to write and run comprehensive end-to-end tests that verify every feature of PolyEdge works correctly — backend logic, frontend UI/UX, tier access controls, security, and business logic. Find bugs, fix them, then write a test to prevent regression.**

Every session must answer YES to: "Did I find and fix a real bug, or prove that a feature works exactly as a user would experience it?"

Do NOT build new features. Do NOT refactor working code. **Find broken things. Fix them. Prove they work.**

---

## Test Accounts (use these in ALL tests — do not create new ones)

| Tier | Email | Password |
|------|-------|----------|
| Free | free@polyedge.com | FreeTest123! |
| Basic | basic@polyedge.com | BasicTest123! |
| VIP | vip@polyedge.com | VipTest123! |

Login: `POST /auth/login` → use `access_token` as `Authorization: Bearer <token>`

---

## What PolyEdge Does

Tracks the top 100 most profitable Polymarket bettors, lets users follow them, and fires instant notifications when they bet. 5 premium features added in sessions 130-135:

1. **Whale Consensus** — GET /markets/consensus — Free: top 3, Basic: all markets, VIP: all + whale names
2. **Conviction Score** — notifications include bet_size / avg_bet multiplier (Basic/VIP only)
3. **Smart Entry Timing** — position cards show copy_signal (good/fair/late) — Basic/VIP only
4. **Copy Portfolio Simulator** — bettor profile shows simulated P&L — Basic/VIP; Free sees locked teaser
5. **Exit Alerts** — scheduler detects whale exits and notifies VIP users only

---

## Tech Stack

- **Backend**: Python + FastAPI + SQLAlchemy (SQLite) — `backend/`
- **Frontend**: Single HTML file SPA — `frontend/index.html`
- **Payments**: Stripe — Basic $4.99/mo (5 follows), VIP $9.99/mo (unlimited)
- **Auth**: JWT in localStorage as `pe_token`
- **Scheduler**: APScheduler polls Polymarket every 30s
- **Tests**: pytest (backend), Playwright (frontend E2E)

---

## How to Run

```bash
cd backend && py -m uvicorn app.main:app --port 8003
py -m http.server 3000 --directory frontend
```

Frontend: http://localhost:3000 | Backend: http://localhost:8003/docs

---

## Confirmed Bugs from Code Review (2026-03-26)

Full code review completed. All bugs are confirmed by reading source code, not assumptions. Fix these before running new test suites — they will cause false failures.

### CRITICAL — Fix Before Anything Else

| # | Bug | File | Line | Impact |
|---|-----|------|------|--------|
| 1 | Profile cache keyed by address only — VIP response served to free users | routes/bettors.py | 66-88 | **Paywall broken — free users get Copy Simulator for free** |
| 2 | `allow_origins=["*"]` + `allow_credentials=True` in CORS | main.py | 42-44 | Security misconfiguration; all browsers reject this combination |
| 3 | `telegram_chat_id` returned in login/register/me response | routes/auth.py | 47 | Sensitive data exposed — must never be in any API response |
| 4 | Telegram verify sets `telegram_verified=True` but never sets `telegram_chat_id`; no bot webhook exists | routes/alerts.py | 140-145 | **Telegram notifications permanently impossible even after "successful" verification** |
| 5 | Web push sends raw POST with no VAPID signing — all real browsers reject it | services/notifications.py | 68-97 | **Web push silently fails for every user, always** |

### MEDIUM — Fix Next

| # | Bug | File | Line | Impact |
|---|-----|------|------|--------|
| 6 | VIP price: CLAUDE.md says $14.99/mo, code/PROJECT.md say $9.99 | admin.py | 39 | MRR calculation wrong; pricing page inconsistent |
| 7 | `accuracy` field missing from leaderboard normaliser | services/polymarket.py | 33-48 | Frontend shows undefined; checklist item fails |
| 8 | Free user can set `web_push_enabled=True` — no tier check | routes/alerts.py | 62-106 | Users "enable" push but silently never receive anything |
| 9 | `get_settings()` not `@lru_cache` — creates new Settings() per scheduler call | config.py | — | Re-reads .env on every bet notification |
| 10 | `_last_positions` dict never purged when bettor unfollowed | services/scheduler.py | 22 | Memory grows forever as follows are added/removed |

### MINOR

| # | Bug | File | Impact |
|---|-----|------|--------|
| 11 | Register returns 409 (correct!) but checklist/tests written expecting 400 | routes/auth.py | Tests assert wrong status code |
| 12 | `_consensusLoaded` flag set once, never cleared — stale data within same session | frontend/index.html | Consensus never re-fetches after initial load |
| 13 | Leaderboard cache dict initialized with dead string key `"bettors"` | routes/bettors.py | 13 | Code smell; no functional impact but misleading |

### Confirmed Working (Code Review — Do NOT Re-Test These)

- JWT algorithm is HS256 ✓
- bcrypt password hashing ✓
- `get_current_user` returns 401 (not 403) on bad token ✓
- All Polymarket HTTP calls have explicit 15s timeout ✓
- `_last_check` updated AFTER `db.commit()` (correct order) ✓
- Exit detection first-run correctly records state without firing false exits ✓
- Duplicate notification prevention via DB check + timestamp ✓
- Consensus tier gate enforced server-side (free=3, basic=all, VIP=all+names) ✓
- Follow limits enforced server-side (free=1, basic=5, VIP=999999) ✓
- Copy signal thresholds correct (≤10%=good, ≤30%=fair, >30%=late) ✓
- No raw SQL string interpolation found — all queries via SQLAlchemy ORM ✓

---

## WHAT TO TEST — Comprehensive Checklist

### 1. Auth & Registration
- [ ] Register with valid data → JWT returned, user in DB
- [ ] Register duplicate email → **409** error (Conflict), clear message — NOTE: code returns 409 not 400; tests must assert 409
- [ ] Login valid → JWT, correct tier in response
- [ ] Login wrong password → 401
- [ ] Protected endpoints without token → 401
- [ ] JWT expiry behaviour

### 1a. Real-World Data Integrity (EQUALLY IMPORTANT — fake/wrong data destroys user trust)

These checks verify the data is real, consistent, and economically meaningful — not just that endpoints return 200.

- [ ] Every bettor address matches `^0x[a-fA-F0-9]{40}$`
- [ ] Leaderboard profit_usd ≥ 0 for all top 20; accuracy between 0.0–1.0; no duplicate ranks
- [ ] Cross-check: leaderboard profit/rank for top 3 bettors matches their profile endpoint (within 5%)
- [ ] Recent bets: all type == "TRADE", price between 0.01–0.99, amount_usd > 0, timestamp in past ≤ 90 days
- [ ] Active positions: avg_price and current_price both between 0.001–0.999 (not 0 or 1 = resolved market)
- [ ] copy_value_pct math correct: `round((current_price - avg_price) / avg_price * 100, 1)`; copy_signal matches
- [ ] Consensus signals: whale_count ≥ 3, prices in range, condition_id is valid 64-char hex
- [ ] Copy simulator: |simulated_roi_pct| ≤ 10000% (sanity cap), math checks out
- [ ] Admin stats: free+basic+vip == total users; mrr == basic*4.99 + vip*9.99
- [ ] Cross-validate #1 leaderboard bettor against live Polymarket Data API directly

### 2. Tier Access Controls (MOST IMPORTANT — bugs found here)
- [ ] Free user: GET /markets/consensus returns ≤3 signals, whale_names = []
- [ ] Basic user: GET /markets/consensus returns all signals, whale_names = []
- [ ] VIP user: GET /markets/consensus returns all signals, whale_names populated
- [ ] Free user: /follows/live returns tier:"free", position cards show 🔒 copy timing padlock in UI
- [ ] Basic user: /follows/live returns tier:"basic", position cards show copy signal badge
- [ ] VIP user: /follows/live returns tier:"vip", position cards show copy signal badge (NOT padlock)
- [ ] Free user: GET /bettors/{address} returns locked:true copy simulator — **BUG #1: profile cache bypasses this gate; fix cache key to include tier**
- [ ] Basic user: GET /bettors/{address} returns full copy simulator
- [ ] VIP user: profile page shows full copy simulator
- [ ] Exit alerts only sent to VIP users in scheduler

### 3. Follows & Follow Limits
- [ ] Free: can follow 1, follow attempt #2 → 403 with upgrade message
- [ ] Basic: can follow up to 5
- [ ] VIP: unlimited follows
- [ ] DELETE /follows/{address} removes follow
- [ ] GET /follows returns correct list

### 4. Whale Consensus (GET /markets/consensus)
- [ ] Returns 200 with signals array
- [ ] Each signal has: market_title, outcome, whale_count ≥ 3, avg_entry_price, current_price
- [ ] tier and names_visible fields correct per user tier
- [ ] Unauthenticated: returns free-tier response (top 3, no names)

### 5. Smart Entry Timing (GET /follows/live)
- [ ] Returns copy_signal field on each position: "good", "fair", or "late"
- [ ] Returns copy_value_pct field (number)
- [ ] Frontend renders green badge for "good", amber for "fair", red for "late"
- [ ] Frontend renders 🔒 padlock for free users (NOT the signal badge)

### 6. Copy Portfolio Simulator (GET /bettors/{address})
- [ ] Returns simulated_copy_pnl object for authenticated users
- [ ] Basic/VIP: simulated_pnl_usd is a number, locked = false
- [ ] Free user: locked = true, simulated_pnl_usd = null
- [ ] Frontend profile page renders simulator card for Basic/VIP
- [ ] Frontend profile page renders blurred locked teaser for Free

### 7. Leaderboard & Bettor Profiles
- [ ] GET /bettors returns list with profit, accuracy, rank fields — **BUG #7: accuracy field currently missing from normaliser**
- [ ] GET /bettors/{address} returns profile + recent_bets (TRADE type only, no REDEEM)
- [ ] Recent bets all have outcome and side fields populated
- [ ] rank and pnl_usd match leaderboard values

### 8. Alerts & Notifications
- [ ] GET /alerts/settings returns current settings
- [ ] PUT /alerts/settings updates web_push_enabled, telegram_enabled — **BUG #5: web push is stub (no VAPID signing); BUG #8: free user can set web_push=True with no tier check**
- [ ] Telegram link flow: start → get code → verify — **BUG #4: verify sets verified=True but never sets telegram_chat_id; notifications can never send**
- [ ] Free user cannot enable notifications (no follow limit bypass)

### 9. Admin Endpoint
- [ ] GET /admin/stats with correct header returns stats + mrr_estimate
- [ ] GET /admin/stats without header → 403
- [ ] GET /admin/stats wrong password → 403

### 10. Security — OWASP Top 10
- [ ] SQL injection: try `' OR '1'='1` in login email field
- [ ] XSS: register with `<script>alert(1)</script>` as name, verify it's escaped in UI
- [ ] Auth bypass: try accessing /follows with tampered JWT
- [ ] Mass assignment: try POSTing subscription_tier in register body
- [ ] Rate limiting: rapid fire 20 login attempts — should not crash
- [ ] CORS: verify only expected origins are allowed — **BUG #2: currently `["*"]` + credentials=True — fix to explicit origin list**
- [ ] Sensitive data: ensure password hash never appears in any API response — **BUG #3: `telegram_chat_id` currently leaks in auth responses**

### 11. Frontend UI/UX (Playwright)
- [ ] Landing page loads, pricing cards show all 5 new features per tier
- [ ] Register flow works end-to-end
- [ ] Login flow works, user stays logged in after refresh
- [ ] Leaderboard renders bettor cards with rank, profit, accuracy
- [ ] Clicking bettor opens profile modal/page
- [ ] Profile shows Copy Simulator (locked for free, unlocked for basic/vip)
- [ ] Dashboard Consensus tab loads and shows market cards
- [ ] Dashboard Follows tab shows position cards with correct copy timing badge
- [ ] Upgrade prompt appears for free user trying locked features
- [ ] Back-to-top FAB appears when scrolled >300px
- [ ] Mobile nav bar visible on narrow viewport
- [ ] All links open correctly (no 404s)

### 12. Code Review (Read Code, Find Bugs Before They Hit Users)
- [ ] Auth: JWT algorithm is HS256/RS256, never "none"; bcrypt/argon2 used for passwords; no raw passwords logged
- [ ] SQL injection surface: all user inputs go through SQLAlchemy ORM, zero raw string interpolation in queries
- [ ] Tier gate completeness: every premium feature (Consensus, Copy Timing, Simulator, Exit Alerts) is enforced on the BACKEND, not just in frontend JS
- [ ] Scheduler `_last_check` is updated AFTER `db.commit()` (not before — a rollback would cause missed bets)
- [ ] Polymarket HTTP calls all have explicit timeouts; API errors don't leak raw stack traces to users
- [ ] CORS config: no `*` wildcard allowed; verify `allow_origins` list in main.py
- [ ] No `hashed_password`, `stripe_customer_id`, or `telegram_chat_id` ever returned in any API response body
- [ ] Every `fetch()` in index.html has error handling; 401 responses redirect to login (no silent blank screens)
- [ ] No dead imports, unregistered routes, or unused model columns

### 13. Business Logic
- [ ] MRR calculation in /admin/stats: basic_count*4.99 + vip_count*9.99
- [ ] Subscription tier upgrades persist in DB after Stripe webhook
- [ ] Scheduler updates _last_check after each poll
- [ ] Scheduler does not fire duplicate notifications for same bet

---

## Agent Technical Config

### Test Commands
```
cd backend && py -m pytest tests/ -q          # backend unit tests
cd backend && py -m pytest tests/ -q -x       # stop on first failure
```

### Playwright Tests
```
cd backend && py -m pytest tests/playwright/ -q   # if playwright tests exist
```

### Python Command
`py` (Windows, not python3)

### Git Repos
- **Project repo**: `git -C "c:/Users/arshi/OneDrive/Desktop/PolyEdge"` — Branch: `main` — Prefix: `agent`
- **AutoAgent repo**: `git -C "c:/Users/arshi/OneDrive/Desktop/PolyEdge/autoagent"` — Branch: `master` — Prefix: `meta`
- NEVER run `git add autoagent/` from project root

### Known Facts
- Backend port: **8003** (updated 2026-03-26 — old 8002 processes stuck)
- Frontend API: `const API = 'http://localhost:8003'` in frontend/index.html
- Admin password: **`polyedge-admin-2026`**
- Free=1 follow, Basic=5, VIP=unlimited
- MRR: `basic * 4.99 + vip * 9.99`
- Stripe/Telegram not configured — feature-gate gracefully
- `py` not `python3` on Windows
- Frontend is ONE file: `frontend/index.html`
- 541 backend tests passing (2 skipped), 99 Playwright E2E tests passing (6 consensus tab + 12 tier gates + 24 UI flows + 4 auth/security + 3 full journeys + 4 notifications tier gates + 4 CORS headers + 4 error states + 1 follow-appears-on-dashboard + 1 leaderboard-empty-state + 1 basic-follow-limit + 1 basic-follow-dashboard + 1 vip-follow-dashboard + 1 unfollow-cycle + 1 profile-modal + 1 profile-back-button + 3 alerts-tab-toggles + 3 leaderboard-sort-toggle + 3 account-tab-tier-badge + 3 period-filter + 3 guide-tab + 3 logout-clears-token + 2 free-push-upgrade-modal + 3 admin-mrr-math + 4 landing-navigation + 3 landing-leaderboard-preview; 2 skipped — no follows for free/basic) as of session 231. NOTE: 10 tests fail intermittently when Polymarket /profiles API is down (external dependency — unrelated to code)
- pytest.ini excludes tests/playwright/ from default run (use `py -m pytest tests/playwright/` separately)
