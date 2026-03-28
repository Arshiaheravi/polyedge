# Activity Log
*(Sessions 1-180 archived — see activity_log_archive.md)*

## 2026-03-27 — TESTING (Session 207)
DONE: Fixed BUG #8 (free-tier web push gate missing in toggleWebPush) and added 8 Playwright E2E tests across 3 new files — logout clears pe_token from localStorage and shows landing view; free user calling toggleWebPush() sees the upgrade modal (toggle stays OFF); admin /admin/stats mrr_estimate math matches basic*4.99+vip*9.99, tier counts sum to total, missing header returns 4xx.
IMPACT: BUG #8 paywall hole closed — free users can no longer bypass push tier gate. Three auth/security/admin flows now have automated E2E coverage. 84→92 Playwright tests total.
FILES: frontend/index.html, backend/tests/playwright/test_logout_clears_token.py, backend/tests/playwright/test_free_push_upgrade_modal.py, backend/tests/playwright/test_admin_mrr_math.py

## 2026-03-27 — TESTING (Session 206)
DONE: Added 9 Playwright E2E tests across 3 new files — account tab shows "Free" badge (tier-free class) and visible upgrade button for free users; leaderboard period filter defaults to #period-month active and correctly moves active state to #period-week/#period-all after switch (cards still render); guide tab becomes visible after showTab('guide') with an h1 heading and visible content blocks.
IMPACT: Proves the account settings tab correctly renders tier status, the period filter toggle does not crash or lose state, and the guide tab is not blank for authenticated users. 75→84 Playwright tests total.
FILES: backend/tests/playwright/test_account_tab_tier_badge.py, backend/tests/playwright/test_period_filter.py, backend/tests/playwright/test_guide_tab.py

## 2026-03-27 — TESTING (Session 205)
DONE: Added 6 Playwright E2E tests — 3 for alerts tab toggle presence (basic-tier user opens Alerts tab, asserts #toggle-push and #toggle-telegram exist and have non-zero size) and 3 for leaderboard sort toggle (initial #sort-profit is active, switching to volume moves active class to #sort-volume, cards still render after sort switch).
IMPACT: Proves the Alerts settings tab correctly renders both notification toggles for authenticated users, and that the leaderboard sort mechanism does not crash or blank the UI on sort change. 69→75 Playwright tests.
FILES: backend/tests/playwright/test_alerts_tab_toggles.py, backend/tests/playwright/test_leaderboard_sort_toggle.py

## 2026-03-27 — TESTING (Session 204)
DONE: Code quality audit of sessions 195-202 Playwright test files — removed duplicate API_BASE definition from test_cors_headers.py (now imported from conftest), replaced hardcoded localhost:8003 URL in test_full_journeys.py page.evaluate() string with the conftest API_BASE constant, and updated tech_debt.md with 6 brittle wait_for_timeout locations across 5 test files.
IMPACT: A future backend port change now requires editing only conftest.py instead of hunting across multiple test files. The audit also documented all wait_for_timeout brittle waits as known deferred debt.
FILES: backend/tests/playwright/test_cors_headers.py, backend/tests/playwright/test_full_journeys.py, autoagent/memory/tech_debt.md

## 2026-03-27 — BRAIN (Session 203)
RESEARCHED: autonomous AI agent best practices 2026, LLM agent memory management (A-MEM, ACE, AgentHER), FastAPI v0.135 features, Polymarket copy trading competitors (Polycule, Stand, PolycopytradBot), fintech push notification benchmarks (Pushwoosh 2026), GitHub repos (anthropics/skills webapp-testing, ECC v1.9.0).
DOWNLOADED: webapp-testing SKILL.md from anthropics/skills (content integrated into playwright.md VIEW CONTEXT RULES section).
IMPLEMENTED: (1) playwright.md — VIEW CONTEXT RULES FOR PROFILE NAVIGATION section (session 202 showProfile()/view-browse bug); (2) PROMPT.md — Zettelkasten cross-link rule in reflexion writing (A-MEM arxiv 2502.12110); (3) backlog.md — code quality audit task (155 work sessions = multiple of 5) + min-bet-size filter + rich push notification features.
BACKLOGGED: code quality audit, min-bet-size filter per follow, rich push notification payloads.
SOURCES: 9 new sources logged.

## 2026-03-27 — TESTING (Session 202)
DONE: Added Playwright E2E test proving the profile back-button returns to the leaderboard tab — basic user opens a bettor profile via showProfile(), then clicks #profile-back-btn, and the test asserts #tab-leaderboard loses its hidden class and #tab-profile gains it.
IMPACT: Proves the full profile→leaderboard back navigation wires correctly. Also uncovered that showProfile() is view-context-dependent — calling it from showView('browse') makes #profile-back-btn invisible to Playwright since the button lives inside view-dashboard.
FILES: backend/tests/playwright/test_profile_back_button.py

## 2026-03-27 — TESTING (Session 201)
DONE: Added Playwright E2E test proving basic-tier user can open a bettor profile via showProfile(), the #tab-profile becomes visible, #profile-addr-display contains the 0x-prefixed address, and the copy simulator card (if shown) is not blurred/locked.
IMPACT: Proves the full "click bettor → view profile" flow works end-to-end for authenticated basic users. Any regression breaking showProfile(), the bettors/{address} API, or the tier-gated simulator rendering will be caught automatically.
FILES: backend/tests/playwright/test_profile_modal.py

## 2026-03-27 — TESTING (Session 200)
DONE: Added 3 Playwright E2E tests completing the North Star "follow bettor → see on dashboard" coverage for all 3 tiers, plus the unfollow cycle. Basic and VIP login, clean follows, follow a bettor, assert address in #follows-container. Unfollow cycle: follow → assert present → unfollow → assert gone.
IMPACT: The North Star table row "Follow bettor → see on dashboard" is now fully proven for Free (session 195), Basic, and VIP tiers. The unfollow cycle proves DELETE /follows/{address} wires through to the UI end-to-end. 64→67 Playwright tests.
FILES: backend/tests/playwright/test_basic_follow_appears_on_dashboard.py, backend/tests/playwright/test_vip_follow_appears_on_dashboard.py, backend/tests/playwright/test_unfollow_cycle.py

## 2026-03-27 — TESTING (Session 199)
DONE: Code quality audit of last 5 sessions' Playwright test files. Fixed API_BASE duplication — constant moved to conftest.py and imported in 2 test files. Logged duplicate registration helper pattern and brittle wait_for_timeout calls to tech_debt.md.
IMPACT: Eliminates hardcoded backend URL scattered across test files — future port changes require editing only conftest.py.
FILES: backend/tests/playwright/conftest.py, backend/tests/playwright/test_error_states.py, backend/tests/playwright/test_leaderboard_empty_state.py

## 2026-03-27 — META (Session 198)
IMPROVED: playwright.md — added SHARED ACCOUNT CLEANUP section (page.evaluate batch-delete pattern for shared tier accounts) and Windows DB lock note to FLAKY TEST HANDLING. backlog.md — added 3 new testing tasks (unfollow cycle, profile modal, login form validation) to prevent backlog exhaustion after 2-3 more sessions.
PATTERNS FOUND: (1) Session 197 RULE about cleaning shared-account follows via page.evaluate had no matching section in playwright.md — would be re-discovered. (2) Session 190 RULE about Windows DB lock before isolated playwright runs also absent from playwright.md. (3) Backlog had only 2 priority items + 1 audit item; after 2-3 sessions it would be empty (low-water-mark rule generates 3 items at commit time but that's too late if sessions run fast).
PREDICTED IMPACT: Next session adding a basic/VIP tier follow-limit test will find the cleanup pattern in playwright.md immediately. The 3 new backlog items (unfollow, profile modal, login validation) extend the testing sprint by 3 sessions.

## 2026-03-27 — TESTING (Session 197)
DONE: Added Playwright E2E test for basic-tier 5-follow-limit gate — logs in as basic@polyedge.com, cleans all existing follows, follows 5 bettors (all succeed), attempts 6th → server returns 403 → upgrade modal (#upgrade-modal) becomes visible.
IMPACT: Proves the basic-tier follow limit enforces correctly at the browser level. Any regression that breaks the 403 response or openUpgradeModal() call will be caught automatically.
FILES: backend/tests/playwright/test_basic_follow_limit.py

## 2026-03-27 — TESTING (Session 196)
DONE: Added 2 backend tests for exact copy_value_pct formula math and 1 Playwright test for leaderboard "No data yet" empty state on successful empty API response.
IMPACT: Formula tests prove the exact arithmetic is correct (not just approximate), catching any rounding or operator-precedence bugs in the copy timing signal. Playwright test proves the distinct empty-list success path (distinct from network error) renders correctly.
FILES: backend/tests/test_polymarket_service.py, backend/tests/playwright/test_leaderboard_empty_state.py

## 2026-03-27 — TESTING (Session 195)
DONE: Added Playwright E2E test — fresh user follows first leaderboard bettor, navigates to Follows tab, asserts the bettor's address appears in #follows-container.
IMPACT: Proves the core "follow → see on dashboard" user flow works end-to-end in a real browser. Any regression breaking POST /follows, GET /follows, or the follow card renderer will now be caught automatically.
FILES: backend/tests/playwright/test_follow_appears_on_dashboard.py

## 2026-03-27 — TESTING (Session 194)
DONE: Added 4 Playwright E2E error state tests — network abort on /bettors shows "Could not load leaderboard", HTTP 503 on /bettors shows same error state, /markets/consensus abort shows "Could not load consensus signals", fresh user with zero follows sees "No traders followed yet" empty state. 57→61 Playwright tests.
IMPACT: Proves the frontend handles all major API failure modes gracefully — any regression that introduces blank screens, infinite spinners, or silent failures on API errors will now be caught automatically.
FILES: backend/tests/playwright/test_error_states.py

## 2026-03-27 — BRAIN (Session 193)
RESEARCHED: autonomous AI agent best practices 2026, agentic coding test quality (arxiv 2603.17973 TDAD, arxiv 2603.13724), FastAPI production patterns, prediction market copy trading competitors (Polystrat), ECC v1.9.0 status check.
DOWNLOADED: Nothing new — ECC still at v1.9.0, no applicable new skills.
IMPLEMENTED: (1) activity_log.md — archived sessions 161-180 (32->12 entries; header updated to "Sessions 1-180 archived"). (2) knowledge.md — curated test suite history table: removed duplicate "500 backend" entries for sessions 189-191 (all same count). (3) testing.md — added TARGETED PRE-COMMIT VERIFICATION section (TDAD pattern: grep for test files covering changed module, run those first) + DEAD ASSERTION GUARD section (grep for "or True" in assertions). (4) backlog.md — added dead assertion sweep task, Polystrat competitor context note, mobile-first UX pass item.
BACKLOGGED: 3 new items: dead assertion sweep, Polystrat competitor context, mobile-first UX pass.
SOURCES: 5 new sources logged.

## 2026-03-27 — AUDIT (Session 192)
DONE: Code quality audit of last 5 work sessions' changed test files — fixed dead assertion (assert ... or True, always passes) in test_full_journeys.py with real assertion, and replaced blocking time.sleep(0.5) with page.wait_for_timeout(500) in test_notifications_tier_gates.py.
IMPACT: Dead assertion was masking a potentially broken tier gate (basic user seeing whale names without VIP lock). Sleep fix removes a blocking Python call inside Playwright tests.
FILES: backend/tests/playwright/test_full_journeys.py, backend/tests/playwright/test_notifications_tier_gates.py

## 2026-03-27 — TESTING (Session 191)
DONE: Added 4 Playwright E2E CORS header tests — browser-level verification that API responses never return wildcard CORS origin, correct localhost:3000 origin is reflected, preflight OPTIONS succeeds, and untrusted origins are rejected. 53 → 57 Playwright tests.
IMPACT: Proves the CORS security fix (Bug #2) works from a real browser's perspective — any regression that accidentally re-introduces wildcard CORS will now be caught in the Playwright suite before reaching users.
FILES: backend/tests/playwright/test_cors_headers.py

## 2026-03-27 — TESTING (Session 190)
DONE: Added 4 Playwright E2E tests for Alerts tab tier gates — free user Telegram toggle fires upgrade modal, free user SMS label shows "VIP required" and SMS toggle fires upgrade modal, VIP user SMS label shows "Not verified" (no gate), VIP Telegram toggle is not blocked. 49 → 53 Playwright tests.
IMPACT: Proves the notification channel tier restrictions work correctly in the browser — any regression that accidentally lets free users enable Telegram or blocks VIP users from SMS will now be caught automatically.
FILES: backend/tests/playwright/test_notifications_tier_gates.py

## 2026-03-27 — TESTING (Session 189)
DONE: Added 3 Playwright E2E full-journey tests (test_full_journeys.py) — free/basic/VIP users each get a chained multi-step journey: register/login → leaderboard → bettor profile (blurred vs unlocked simulator) → follows tab (padlock vs signal badge) → consensus tab (capped vs all signals, no names vs whale names) → follow limit (upgrade modal for free, no 403 for VIP). 46 → 49 Playwright tests.
IMPACT: Proves the full tier-gated feature chain works end-to-end as a real user would experience it. Catches regressions in state transitions that individual unit tests miss.
FILES: backend/tests/playwright/test_full_journeys.py

## 2026-03-27 — META (Session 188)
IMPROVED: playwright.md — added FLAKY TEST HANDLING section (re-run failing tests in isolation before investigating; 3-6 Polymarket API rate-limit flakes expected in full-suite runs) and FRESH USER PATTERN section (always register timestamp-email user for follow-limit/quota tests; never reuse shared fixture accounts for state-accumulating tests).
PATTERNS FOUND: Session 187 RULE entries in knowledge.md about flaky tests and fresh user pattern had no matching guidance in playwright.md — work sessions read skill files first, not knowledge.md reflexions, so these patterns would be rediscovered each time rather than applied proactively.
PREDICTED IMPACT: Next full-journey E2E session will correctly expect and handle rate-limit flakes without wasting turns investigating pre-existing failures; follow-limit tests will use fresh users by default.

## 2026-03-27 — TESTING (Session 187)
DONE: Added 4 Playwright E2E tests in test_auth_and_security.py: (1) auth persists after page refresh — dashboard still shown, pe_token intact; (2) bad token redirect — invalid JWT cleared, landing page shown; (3) follow limit upgrade modal — fresh free user hits 403 on 2nd follow, upgrade modal fires; (4) XSS safety — script-tag username rendered via textContent, no alert fires. 42→46 Playwright tests.
IMPACT: Proves the 3 most critical user-facing security/auth flows work correctly in a real browser.
FILES: backend/tests/playwright/test_auth_and_security.py

## 2026-03-26 — TESTING (Session 186)
DONE: Added 1 test for compute_copy_simulator API exception path — mocks httpx.ConnectError on client.get, asserts function returns {simulated_pnl_usd: 0.0, simulated_roi_pct: 0.0, bets_analysed: 0}. 499→500 tests.
IMPACT: Closes the except Exception branch (polymarket.py:333-334) that was unreachable by existing tests.
FILES: backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 185)
DONE: Added 3 tests for conviction_score and conviction_label fields in get_recent_bets: (1) single bet → score=1.0, label=""; (2) 19 small bets + $1000 outlier → score=19.6, label="EXTREME"; (3) API ConnectError → empty list returned safely. 496→499 tests.
IMPACT: Locks in the conviction label contract (EXTREME/HIGH/empty) at the service layer.
FILES: backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 184)
DONE: Added 3 coverage-gap tests: (1) consensus route cache hit path — pre-populates cache with fresh data, verifies get_consensus_signals is NOT called on second request; (2) JWT with no `sub` claim sent to optional-auth endpoint (/markets/consensus) — verified returns 200 with tier="free" (anonymous treatment); (3) send_telegram ConnectError — mocks httpx.AsyncClient to raise ConnectError, verifies False returned without crash.
IMPACT: Closes 3 branches that were never exercised: markets.py:29, auth.py:72-73, notifications.py:27-29.
FILES: backend/tests/test_tier_gates.py, backend/tests/test_security.py, backend/tests/test_notifications.py

## 2026-03-26 — BRAIN (Session 183)
RESEARCHED: autonomous AI agent best practices 2026, LLM agent reliability patterns, FastAPI production patterns 2026, fintech SaaS notification platform benchmarks, Polymarket copy trading competitors and features 2026.
DOWNLOADED: Nothing new — all relevant patterns already in skill files or not applicable to prompt-only agent.
IMPLEMENTED: (1) testing.md — added leaderboard cache key format rule (profit_month_50 contamination pattern from session 180) to Module-level cache isolation section. (2) activity_log.md — archived sessions 141-160 (42->22 entries; header updated to "Sessions 1-160 archived"). (3) backlog.md — added 4 competitive feature items: personalized notification body, outbound webhook channel, delayed Free-tier alerts, minimum bet size filter.
BACKLOGGED: 4 new FEATURE MODE items added to backlog.md; structured logging with request_id added to backlog.
SOURCES: 5 new sources logged.

## 2026-03-26 — TESTING (Session 182)
DONE: Added 3 coverage-gap tests: (1) PUT /alerts/settings with push_subscription as dict object — also fixed AlertSettingsUpdate.push_subscription field from Optional[str]->Optional[Any] so the isinstance(dict) branch at alerts.py:104 is reachable in Pydantic v2; (2) Telegram webhook with message present but empty text — asserts ok=True, no DB change; (3) compute_copy_simulator SELL-side trades excluded — bets_analysed=0 when all trades are SELL. 490→493 tests.
IMPACT: Closes all 3 coverage gaps identified via --cov in session 181.
FILES: backend/app/routes/alerts.py, backend/tests/test_alerts.py, backend/tests/test_polymarket_service.py

## 2026-03-26 — TESTING (Session 181)
DONE: Added 2 tests covering checklist field-presence items: (1) test_follows_live_positions_include_copy_value_pct — mocks 3 positions with known copy_value_pct values, asserts each arrives in route response unchanged; (2) test_bettor_detail_recent_bets_have_side_field — mocks 2 bets with side="BUY", asserts "side" key is present and non-empty. Removed stale backlog item. Added 3 new coverage-gap tasks from --cov analysis. 488→490 tests.
IMPACT: Locks in the contract that copy_value_pct and side fields are not silently stripped when passing through route handlers.
FILES: backend/tests/test_follows_live.py, backend/tests/test_bettors.py
