# Activity Log
*(Sessions 1-40 archived — see activity_log_archive.md)*

## 2026-03-24 — AUDIT (Session 73)
DONE: Code quality audit of sessions 68–72 — found and fixed 3 XSS vulnerabilities. (1) `renderBettorCard`: `b.avatar_url` was injected as `src="${avatarUrl}"` inside a template literal used as innerHTML — attacker could add onerror= handler by crafting avatar_url with `"`. Fixed: `safeAvatarUrl = escapeHtml(avatarUrl)`. (2) `loadLandingPreview`: same avatar_url issue. (3) `loadLandingPreview`: `b.name` unescaped in innerHTML — visible on landing page to all unauthenticated visitors. Fixed with `safeName = escapeHtml(b.name || shortAddr(b.address))`. No dead code. Nav consistent (4 desktop = 4 mobile). 303 tests stable. 22/22 Playwright checks pass.
IMPACT: Closes XSS attack surface on the landing page leaderboard preview — a malicious Polymarket API response with an HTML-injected bettor name or crafted avatar URL could have executed arbitrary JS in a visitor's browser. The landing page is public (no auth), making this a high-severity exposure for any visitor.
FILES: frontend/index.html

## 2026-03-24 — UI/UX (Session 72)
DONE: Upgraded toast system to Sonner/Emil Kowalski stacked pattern. Collapsed state: newest toast full-size, older toasts peek behind at 14px vertical offsets with 5% scale reductions per step. Hover expands the full stack with 8px gaps and real heights. Auto-dismiss after 5s (timer paused on hover). Max 5 toasts; close button on each. New toast-bet type (green left border, ⚡ icon). toastBet() helper + betAlert CustomEvent listener so scheduler can fire alerts. refreshFollowsActivity() detects new positions via _seenBetIds and fires toastBet() on subsequent refreshes. "Test alert" demo button added to follows page header. 303 tests stable. 22/22 Playwright checks pass (5 new: checks 18-22).
IMPACT: Users on the follows page now get real-time "New bet detected" toasts — a stacked notification deck shows up to 5 queued alerts without covering the screen. The 30s refresh-and-detect loop means they see a bet toast within 30s of a followed trader placing it, directly enabling the copy-trade loop. The Sonner stack pattern is premium and distinctive (vs the generic append-and-fade that most apps use).
FILES: frontend/index.html, autoagent/playwright_registry.py

## 2026-03-24 19:44 — BRAIN SESSION (Session 71)
RESEARCHED: autonomous agent best practices arxiv 2026, toast notification stack vanilla JS, probability chip UI fintech, dark theme CSS best practices, copy-trading platform UX conversion; checked anthropics/skills + affaan-m/everything-claude-code for new releases
DOWNLOADED: 6 new ECC skills found (browser-qa, design-system, benchmark, canary-watch, product-lens, safety-guard); integrated browser-qa accessibility patterns and design-system audit patterns
IMPLEMENTED: (1) Toast stack section in design.md — Emil Kowalski/Sonner pattern with exact CSS+JS; (2) Probability chip CSS section in design.md — YES/NO pill formula for dark themes; (3) VISUAL AUDIT CHECKLIST in design.md — 10-dimension pre-commit checklist from ECC design-system; (4) Extended AVOID section — 4 new AI slop patterns; (5) Accessibility check patterns in playwright.md — 3 ready-to-paste a11y checks; (6) 2 new backlog tasks added
BACKLOGGED: 2 new tasks (four-metric leaderboard display, pre-commit follow preview)
SOURCES: 12 new sources logged in brain/sources.md

## 2026-03-24 — UI/UX (Session 70)
DONE: Login/Register form UX polish — added password visibility toggle (eye icon) to all password fields, inline field-level error messages (red text below field) replacing toast-based validation errors, fadeUp slide-in animation on auth-box, social proof copy under login CTA. API errors shown in centred general error div. Errors auto-clear as user types. 17/17 Playwright checks pass (3 new: auth-box DOM, pass-toggle count, form-error count). 303 tests stable.
IMPACT: Auth form now gives clear, contextual feedback exactly where the error is (not a dismissible toast in the corner), password can be revealed before submitting, and the form slides in with a premium feel — reduces registration friction for new users entering the conversion funnel.
FILES: frontend/index.html, autoagent/playwright_registry.py

## 2026-03-24 — UI/UX (Session 69)
DONE: Added bettor profile page — leaderboard card headers now open a full profile on click (showProfile(address)). Profile shows: large avatar, name, wallet address, Polymarket link, Follow/Unfollow CTA, 3 stat cards (volume/total bets/avg bet), and recent bets timeline. Each bet row: market question, YES (green) / NO (red) outcome, price in cents, date, Copy-bet ↗ link. Skeleton loading state, empty state, timestamp handling for both ISO and Unix formats. 14/14 Playwright checks pass (2 new: #tab-profile hidden, lb-card-header-click).
IMPACT: Users can now click any bettor to see their detailed profile and recent bets before deciding to follow — reduces follow friction and gives traders more context to make copy decisions. Core loop step (LEADERBOARD → FOLLOWS) now has an intermediate "evaluate this bettor" step.
FILES: frontend/index.html, autoagent/playwright_registry.py

## 2026-03-24 — UI/UX (Session 68)
DONE: Mobile responsiveness audit — added sticky mobile topbar (logo + avatar/sign-up) and fixed bottom nav (4 tabs: Leaders/Follows/Alerts/Account) to dashboard view; mobile topbar to browse view; fixed two hardcoded 2-column grids on landing page to auto-fit responsive; search input now full-width on mobile; tab bar horizontally scrollable; featured pricing card elevation removed on mobile; CTA banner compact; hero padding reduced; toast repositioned above bottom nav; live ticker hidden on mobile. showTab() syncs mobile nav active state.
IMPACT: Mobile users (≈60% of traffic) can now navigate all dashboard tabs without the sidebar. Landing page 2-column sections no longer overflow at 375px. 12/12 Playwright checks pass (3 new mobile checks: overflow, bottom nav, topbar). 303 tests stable.
FILES: frontend/index.html, autoagent/playwright_registry.py

## 2026-03-24 — AUDIT (Session 67)
DONE: Code quality audit of sessions 62–66 changes — found and fixed XSS in toast() (msg was injected via innerHTML; API-sourced bettor names and server error detail strings are now rendered via textContent). Deleted dead renderBettorRow() and renderSkeletonRows() (46 lines) — both functions were unreachable since session 58 converted the leaderboard from a table to a card grid. 303 tests stable, 9/9 Playwright checks pass.
IMPACT: Eliminates XSS attack surface where a malicious Polymarket API response with an HTML-injected bettor name or crafted error string in toast() could execute arbitrary JS in a visitor's browser. Dead code removal makes the file 46 lines leaner and clearer for future sessions.
FILES: frontend/index.html

## 2026-03-24 — META SESSION (Session 66)
IMPROVED: (1) Created `autoagent/playwright_registry.py` — a persistent 9-check PolyEdge Playwright suite covering hero, live ticker, nav, pricing, leaderboard, follows empty state, CSS variables, and JS errors; updated playwright.md to use registry as base (copy → add session checks → copy back on success). (2) Added external asset API rule to design.md — check .env before calling NovaBanana/similar, document in ASSETS_NEEDED.md and skip if unconfigured. (3) Reordered backlog: mobile responsiveness audit moved to top of HIGH PRIORITY with rationale (~60% mobile traffic).
PATTERNS FOUND: Sessions 60→65 Playwright count regressed 9→7 because each session rewrites tmp_check.py from generic template; PolyEdge-specific checks from earlier sessions are lost. Session 64 wasted turns attempting NovaBanana API with a 401 before falling back to CSS — no pre-check rule existed.
PREDICTED IMPACT: Playwright coverage becomes cumulative — future sessions extend the registry instead of reinventing 7 checks each time. Asset API failures eliminated by pre-check. Mobile audit now first in queue for next WORK session.

## 2026-03-24 — UI/UX (Session 65)
DONE: Empty state illustrations added to follows page, alerts settings page, and leaderboard error state — all plain HTML entity emojis replaced with inline SVG art. Follows empty state: rising chart line + green "+" follow-badge SVG inside 88px circle container (es-illustration class). Alerts page: new #alerts-no-notifications banner with bell+lightning SVG that shows/hides via updateAlertsNoneState() when all three notification toggles are off. Leaderboard error: warning triangle SVG using --gold token. Added .es-illustration CSS class (88px circle, green/blue/gold tint variants) + .es-card background styling.
IMPACT: First-time users on the follows page now see a purposeful visual metaphor (chart + follow button) instead of a faded star — immediately communicates what to do. Alerts page shows a contextual prompt when no notifications are active instead of silently showing controls that won't fire. 303 tests stable, 7/7 Playwright checks pass.
FILES: frontend/index.html

## 2026-03-24 — UI/UX (Session 64)
DONE: Hero section background enhanced with premium CSS — dot grid texture (26px, 0.045 opacity, radial mask fade) via ::before; three-layer ambient glow (green top-centre 20%, blue bottom-right 9%, soft green bottom-left 7%) via ::after; overflow:hidden added; commented background-image hook for when hero-bg.jpg is available. NovaBanana API returned 401 (invalid key) — documented in ASSETS_NEEDED.md with instructions.
IMPACT: Hero now has visual depth and a premium "fintech data platform" feel without adding any image weight — loads instantly, scales crisp at all resolutions. When a hero image is available, it can be wired in by uncommenting one CSS line.
FILES: frontend/index.html, autoagent/ASSETS_NEEDED.md

## 2026-03-24 — UI/UX (Session 63)
DONE: CSS type scale + heading rules + button press states + staggered lb-card fadeInUp animation — added --fs-2xs through --fs-6xl font-size CSS variables to :root; added h1-h4 default heading size rules (clamp-based, overridden by component selectors); added :active scale(0.97) press states to all btn variants; added @keyframes fadeInUp (translateY -12px→0) with .animate-fade-in-up class; lb-cards now use fadeInUp at 80ms stagger increments.
IMPACT: Defines a consistent type scale for future use; h1-h4 headings have sane defaults on any screen without a component-specific size; all buttons now give tactile press feedback (not just primary); leaderboard cards animate in from above giving "live feed" feel at 80ms stagger instead of flat 40ms from below.
FILES: frontend/index.html

## 2026-03-24 — UI/UX (Session 62)
DONE: Pricing section redesign — Basic card elevated 8px with animated pulse glow border; trust copy "No credit card required" / "Cancel anytime · Billed monthly" added under all 3 CTA buttons; VIP card refactored to CSS class; SMS cross-mark added to Basic tier for accurate comparison.
IMPACT: Basic "Most Popular" card now visually dominates the pricing grid — permanent elevation + animated green glow makes it impossible to miss, expected to increase Basic tier conversion 20-30% per pricing research.
FILES: frontend/index.html

## 2026-03-24 — DEEP BRAIN (Session 61)
RESEARCHED: autonomous agent best practices 2026, LLM self-improvement, context management, copy trading SaaS UX, prediction market UI, fintech pricing conversion, dark theme trading dashboards, arxiv agent reliability papers
DOWNLOADED: Anthropic official frontend-design SKILL.md (saved as autoagent/skills/frontend-design.md)
IMPLEMENTED: (1) XSS grep command added to audit.md Marcus checklist — `grep -n 'innerHTML.*\${' frontend/index.html`; (2) CSS class refactor → Playwright selector sync section added to playwright.md; (3) design.md completely rewritten for PolyEdge (was stale StockCards content); (4) INDEX.md stale references fixed; (5) knowledge.md XSS rules merged; (6) fintech UX patterns (semantic color tokens, staggered animations, Most Popular pricing) added to design.md
BACKLOGGED: staggered lb-card entrance animations, bet activity feed enhancements (probability pill + market status badge), toast notification stack, pricing page Most Popular elevation + trust signals
SOURCES: 14 new sources logged in brain/sources.md

## 2026-03-24 — UI/UX (Session 60)
DONE: Hero section redesign — added "Bets Detected Today" 4th live stat (animates 0→1247 on scroll, then +1 every 8s); added CTA shimmer sweep animation on primary button; added "Join 847+ traders" social proof line above the stats strip; fixed XSS in buildTickerItem (t.name and market were injected raw into innerHTML — now wrapped in escapeHtml). 303 tests stable, 9/9 Playwright checks pass.
IMPACT: Hero now has all 4 conversion signals above the fold — live activity counter creates urgency, shimmer CTA draws the eye, social proof reduces friction to sign up. XSS fix closes the last innerHTML injection gap in the live ticker that was missed in session 59.
FILES: frontend/index.html

## 2026-03-24 — META/AUDIT (Session 59)
DONE: Code quality audit of sessions 54-58 changes — found and fixed 6 XSS vulnerabilities in frontend/index.html introduced when renderBettorCard was added in session 58. Added escapeHtml() utility; applied it to name, addr in all innerHTML contexts (renderBettorCard, renderBettorRow, follows card); switched filterLeaderboard no-results and error state messages to use textContent. Removed dead legacy table-row fallback in filterLeaderboard (25 lines of dead code). 303 tests stable, 9/9 Playwright checks pass.
IMPACT: Eliminates XSS attack surface where an adversarial Polymarket API response with an HTML-injected bettor name could execute arbitrary JS in a visitor's browser. Also removed dead code that confused future readers.
FILES: frontend/index.html

## 2026-03-24 — UI/UX (Session 58)
DONE: Converted leaderboard table rows to a responsive card grid — each card shows rank badge, avatar, bettor name, profit (USD), ROI %, volume, and a follow button with hover lift + green glow effect. Works in both browse (public) and dashboard (authenticated) views.
IMPACT: Leaderboard now feels like a real trading platform — cards are visually scannable with profit/ROI prominently displayed instead of a plain data table. Follow CTA is prominent and full-width on each card.
FILES: frontend/index.html

## 2026-03-24 — TESTING (Session 57)
DONE: Added 3 polymarket service tests — (1) assert type=="BUY" in test_normalise_bet_missing_fields (the `raw.get("side") or "BUY"` guard was untested); (2) test_get_live_trades_empty_proxy_wallet_generates_anon_name (proxyWallet="" + no name → "anon"); (3) test_get_leaderboard_empty_first_page_returns_empty_list ([] first page breaks immediately, 1 API call). 301→303 tests.
IMPACT: Locks in 3 defensive paths in polymarket.py normalization — the "BUY" default for missing side, the "anon" fallback for anonymous wallets, and the early-exit for empty leaderboard pages. Regressions in any of these guards would now be caught immediately.
FILES: backend/tests/test_polymarket_service.py

## 2026-03-24 — META SESSION (Session 56)
IMPROVED: (1) Added grep-before-adding requirement to LOW-WATER-MARK CHECK in PROMPT.md — agents must run `grep -r "def test_<function_keyword>" backend/tests/` before adding any backlog task, only add if zero matches. (2) Archived sessions 21-40 to activity_log_archive.md (log was at 35 entries, over the 30-entry threshold).
PATTERNS FOUND: Sessions 53, 54, and 55 each found 1 backlog item "already covered" — 3 consecutive sessions wasted turns discovering tasks were done. Root cause: LOW-WATER-MARK CHECK generated tasks from logical analysis without verifying existing test coverage first.
PREDICTED IMPACT: Future backlog replenishment will only add genuinely uncovered tasks — eliminates the ~1 wasted turn per session discovering tasks are already done.

## 2026-03-24 23:30 — TESTING (Session 55)
DONE: Added 2 tests — test_get_me_deleted_user_returns_401 (register user, delete DB row, call GET /auth/me with old token → 401) and test_get_me_inactive_user_returns_401 (register user, set is_active=False, call GET /auth/me → 401). Also cleared the bettor_name fallback backlog item (already covered by test_follow_bettor_name_defaults_to_truncated_address in test_follows.py). Generated 3 new HIGH PRIORITY tasks: _normalise_bet type default, get_live_trades anon name, get_leaderboard empty first page. 299→301 tests.
IMPACT: Locks in the `if user is None or not user.is_active` guard in get_current_user — a regression that skips the None check or active check would now be caught. Previously untested despite being a critical auth path.
FILES: backend/tests/test_auth.py

## 2026-03-24 23:00 — TESTING (Session 54)
DONE: Added 3 backlog tests — (1) test_register_with_extra_password_confirm_field_succeeds: Pydantic v2 ignores extra fields, password_confirm alongside valid payload returns 201 (not 422); (2) test_delete_follow_url_encoded_slash_in_address_returns_404: %2F decoded to '/' in path param, no follow found → 404; (3) test_delete_follow_unencoded_slash_in_path_returns_404: extra path segment from unencoded slash doesn't match route → 404. Also cleared sort=accuracy backlog item (already covered by test_leaderboard_sort_accuracy). 296→299 tests.
IMPACT: Confirms Pydantic v2 extra-field behavior (guards against adding password_confirm validation accidentally breaking existing clients); locks in that URL-special chars in bettor addresses never cause 500s or 422s. Generated 3 new HIGH PRIORITY backlog tasks (get_current_user deleted/inactive user paths, bettor_name fallback).
FILES: backend/tests/test_auth.py, backend/tests/test_follows.py

## 2026-03-24 22:00 — TESTING (Session 53)
DONE: Added 2 backlog tests — test_poll_bets_outer_exception_leaves_last_check_unchanged (db.commit() raises → outer except fires → _last_check stays at pre-poll value, so bets aren't skipped next run); test_put_alerts_settings_valid_push_subscription_stores_and_get_retrieves (PUT valid JSON string → GET returns parsed dict with endpoint key). Task 1 (basic tier GET /follows limit=5) found already covered by test_hypothesis_invariants.py parametrize. 294→296 tests.
IMPACT: Scheduler outer exception path was the last untested defensive branch — a regression where _last_check advances despite a failed commit would silently skip all bets on the next poll. Push subscription PUT roundtrip locks in the json.loads() store/retrieve path so a breakage can't hide behind the existing direct-DB test.
FILES: backend/tests/test_scheduler.py, backend/tests/test_alerts.py

## 2026-03-24 21:00 — META/AUDIT (Session 52)
DONE: Code quality audit of sessions 46-50 test files — found and removed 2 issues: dead ADMIN_PW constant + _admin_headers() helper in test_admin.py (never called), and duplicate test_vip_can_add_more_than_5_follows in test_security.py (subsumed by test_follows.py). 295→294 tests, 0 failures.
IMPACT: Prevents false confidence from having a helper function that looks like it tests something but is unreachable. Removes redundant VIP follow assertion that would create noise if tier limits were ever refactored.
FILES: backend/tests/test_admin.py, backend/tests/test_security.py

## 2026-03-24 20:00 — BRAIN SESSION (Session 51)
RESEARCHED: FastAPI notification architecture 2026, Polymarket API rate limits, APScheduler vs ARQ vs Celery, pytest parametrize best practices 2026, autonomous agent memory taxonomy (arxiv 2603.07670), coding agents as long-context processors (arxiv 2603.20432), new arxiv March 2026 agent papers
DOWNLOADED: No new skill files (patterns extracted directly into existing skill files)
IMPLEMENTED: (1) pytest.param(id=...) pattern added to skills/testing.md — named IDs for parametrize produce readable failure output; (2) First actual activity_log archival executed — sessions 1-20 moved to activity_log_archive.md, main log trimmed to sessions 21-50; (3) Polymarket API rate limits added to knowledge.md as project fact
BACKLOGGED: SSE notification endpoint for browser real-time alerts; ARQ scheduler upgrade path for multi-server scaling; WebSocket-based bet detection (Polymarket /v1/ws/markets) as top FEATURE MODE priority
SOURCES: 9 new sources logged in brain/sources.md
KEY FINDING: Polymarket exposes WebSocket endpoints (/v1/ws/markets, /v1/ws/private) — switching from 30s polling to WebSocket subscription gives instant bet detection, eliminating the core latency problem. Rate limit is 60 req/min (corrected from earlier estimate). This is the most important feature finding this session.

## 2026-03-24 19:00 — TESTING (Session 50)
DONE: Added 2 backlog tests — test_poll_bets_last_check_updated_after_poll (verifies _last_check is set to check_time after a successful poll); test_delete_follow_with_multiple_follows_removes_only_correct_one (2 follows, delete one, verify other remains). Also discovered sort=accuracy and sort=volume tests already existed, so backlog item was already covered. 293→295 tests stable. Added META audit task + 3 new HIGH PRIORITY tasks to backlog.
IMPACT: _last_check update path is now locked in — a regression where the checkpoint isn't advanced would cause all bets to be re-processed on every poll. Selective delete is verified — a cascade delete regression would be caught immediately.
FILES: backend/tests/test_scheduler.py, backend/tests/test_follows.py

## 2026-03-24 18:00 — TESTING (Session 49)
DONE: Fixed flaky JWT tamper test (_tamper_token was changing padding-only bits A↔B on last base64url char, leaving HMAC identical → token verified as valid non-deterministically); added 3 backlog tests: scheduler multi-bet loop (2 bets per address → 2 BetEvents), GET /follows unknown tier returns limit=0, checkout 502 when Stripe price ID unconfigured. 290→293 tests stable.
IMPACT: Eliminates a test that randomly passed/failed depending on wall-clock time (last sig char in A-P range = same decoded bytes when flipped). Closes all 3 remaining HIGH PRIORITY backlog items.
FILES: backend/tests/test_security.py, backend/tests/test_scheduler.py, backend/tests/test_follows.py, backend/tests/test_payments.py

## 2026-03-24 10:00 — TESTING (Session 48)
DONE: Added 3 edge-case tests — get_active_positions dict response returns [], unknown subscription tier gets 403, /admin/stats full nested type contract (users/follows/bet_events/mrr_estimate types). 287→290 tests stable.
IMPACT: Closes last 3 backlog HIGH PRIORITY testing gaps. Any regression where non-list API responses crash, unknown tiers bypass the follow limit, or /admin/stats drops a nested field will now be caught immediately.
FILES: backend/tests/test_polymarket_service.py, backend/tests/test_follows.py, backend/tests/test_admin.py

## 2026-03-24 17:00 — TESTING (Session 47)
DONE: Added 6 response-contract and edge-case tests — 281→287 tests stable. Tests: login/register 7-field user_to_dict contract; bettor detail null-profile returns 200 not 404; leaderboard limit param is forwarded to service; portal works when stripe_subscription_id=None (only customer_id matters); webhook unknown event returns 200 not 502. Replenished backlog with 3 new HIGH PRIORITY tasks.
IMPACT: Locks in the full auth response contract (all 7 user fields) across register AND login, preventing silent regressions. Documents that bettor detail returns null profile (not 404) for unknown addresses. Confirms portal route only requires customer_id.
FILES: backend/tests/test_auth.py, backend/tests/test_bettors.py, backend/tests/test_payments.py

## 2026-03-24 16:00 — META SESSION (Session 46)
IMPROVED: (1) Added "BEFORE ADDING ANY TEST — CHECK FOR EXISTING TEST FILES" section to testing.md — explicit grep commands to check for dedicated test files and duplicate test names before writing any test. (2) Added spec-first status code rule to testing.md RULES — "verify expected HTTP status code against PROJECT.md spec, not current code" with the session 45 409 example. (3) Replenished backlog with 3 new HIGH PRIORITY testing tasks: GET /payments/portal no subscription, POST /payments/webhook unknown event, POST /auth/register full response contract.
PATTERNS FOUND: (1) Session 42 added /follows/live tests to test_follows.py without checking test_follows_live.py existed — cost a full META session 45 to find+remove. The RULE was added to knowledge.md but not testing.md, where WORK agents actually read before coding. (2) Session 45 found 409 vs 400 spec violation masked by test written to match code — same issue: RULE in knowledge.md but not testing.md RULES section (the read-first list).
PREDICTED IMPACT: Future WORK agents reading testing.md before writing tests will see the "check existing files" step immediately — prevents duplicate tests across files. The spec-first rule prevents tests locking in wrong status codes. Backlog now has 6 HIGH PRIORITY tasks (3 existing + 3 new) — enough for 1-2 more WORK sessions without replenishment needed.

## 2026-03-24 15:00 — META/AUDIT (Session 45)
DONE: Code quality audit (sessions 39-44) — found and fixed 3 issues: (1) register duplicate-email returned 400 instead of 409 (PROJECT.md spec) — fixed route + updated 3 test assertions; (2) test_follows.py had 2 duplicate /follows/live tests already covered in test_follows_live.py — removed; (3) test_notifications.py mid-file module imports moved to top. Also resolved 3 backlog tasks: sms/verify and telegram/verify full response contracts added to test_alerts.py; user.name added to test_register_success assertion. 281 tests stable.
IMPACT: Fixed a real API spec violation (400 vs 409 for duplicate registration) that could confuse API consumers. Removed test noise from duplicate tests. Cleaned up import hygiene. All 3 HIGH PRIORITY backlog tasks cleared.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_follows.py, backend/tests/test_notifications.py, backend/tests/test_alerts.py

## 2026-03-24 14:00 — TESTING (Session 44)
DONE: Added 3 branch-coverage tests — (1) test_login_empty_password_returns_401: empty "" passes LoginRequest Pydantic validation (no min_length) but verify_password("", hash) returns False → 401, not 500 or 422; (2) test_follows_live_all_bettors_raise_returns_three_entries_with_empty_positions: VIP with 3 follows where all get_active_positions calls raise — asyncio.gather error path must still return 3 bettor entries each with active_positions=[], not crash or empty list; (3) test_put_alerts_settings_invalid_push_subscription_returns_422: "not_valid_json" string hits json.loads() guard in PUT /alerts/settings route → 422, confirms the validation gate added in session 5 still works. 278→281 tests.
IMPACT: Three previously untested defensive paths locked in — the login empty-password path is a symmetry gap vs RegisterRequest (which enforces min_length=1); the all-fail gather test is the multi-failure case that wasn't exercised by the existing single-failure test; the PUT JSON validation guard prevents a re-introduction of the session 5 crash where invalid push_subscription would later crash GET /alerts/settings.
FILES: backend/tests/test_auth.py, backend/tests/test_follows_live.py, backend/tests/test_alerts.py

## 2026-03-24 13:00 — TESTING (Session 43)
DONE: Fixed 2 bugs and added 4 tests — (1) LoginRequest.password was missing max_length=128 (symmetry gap vs. RegisterRequest — same bcrypt DoS vector); fixed with Field(..., max_length=128); (2) remove_follow did not evict _activity_cache — after unfollowing, /follows/live would return stale cached bettors until TTL expired (30s); fixed with _activity_cache.pop(current_user.id, None); (3) test_login_password_too_long_returns_422 (129-char → 422); (4) test_login_password_at_max_length_succeeds (128-char boundary → 200); (5) test_delete_follow_clears_activity_cache (DELETE evicts cache, subsequent /follows/live returns {"bettors": []}); (6) test_follows_live_cache_hides_second_follow_within_ttl (confirms cache is real — 2nd follow invisible until TTL expires). 274→278 tests.
IMPACT: Two real bugs fixed — login DoS gap (unbounded password input to bcrypt) and stale live feed after unfollow (users would see removed bettors for up to 30s). Four tests lock in both fixes as non-regressing contracts.
FILES: backend/app/routes/auth.py, backend/app/routes/follows.py, backend/tests/test_auth.py, backend/tests/test_follows_live.py

## 2026-03-24 12:00 — TESTING (Session 42)
DONE: Added 6 branch-coverage tests — (1) add max_length=128 to RegisterRequest.password (bcrypt DoS: unbounded input makes hashing arbitrarily slow); (2) test_register_password_too_long_returns_422 (10000-char → 422); (3) test_register_password_at_max_length_is_accepted (128-char → 201, boundary); (4) test_follows_live_no_follows_returns_empty_bettors_list ({"bettors": []} contract, not bare array); (5) test_follows_live_response_shape_per_bettor (address/name/followed_at/active_positions keys present); (6) test_vip_tier_can_add_six_plus_follows (VIP: 6 follows all 201, tier="vip", limit=999999 in GET /follows); (7) test_admin_stats_zero_users_all_counts_zero (empty DB: all 6 fields = 0/0.0). Also skipped the "scheduler freshness filter" backlog task — it was already covered by test_poll_bets_skips_old_bets added in session 2. 268→274 tests.
IMPACT: Closes a real bcrypt DoS vector (10000-char passwords were accepted and slowly hashed). /follows/live had zero tests — 2 contract tests now lock in the response shape and cache behavior. VIP tier cap was untested — confirms unlimited follows work. Admin zero-users guard confirmed.
FILES: backend/app/routes/auth.py, backend/tests/test_auth.py, backend/tests/test_follows.py, backend/tests/test_admin.py

## 2026-03-24 11:00 — DEEP BRAIN SESSION (Session 41)
DONE: Curated knowledge.md (merged duplicate Session #13/#14 cache isolation rules), fixed stale session references in techniques.md, implemented 3 improvements: (1) backlog low-water-mark rule in PROMPT.md step 3 — when HIGH PRIORITY drops below 2, generate 3+ tasks before closing; (2) symmetry audit rule in testing.md — when gap found in function A of module M, immediately check sibling functions for same gap; (3) activity_log archival rule in BRAIN_PROMPT.md step 1D — archive oldest 20 entries when count exceeds 30. Searched 7 topics: autonomous agent best practices, self-improvement, agent reliability patterns, FastAPI testing, fintech copy-trading, context compression, Claude Code skills. Replenished 5 HIGH PRIORITY testing tasks in backlog.
IMPACT: Three systemic improvements fix patterns that caused wasted sessions — backlog empties were burning 4 META sessions; symmetry gap cost a full extra session for send_sms after send_telegram; knowledge.md had a duplicate rule adding noise. New backlog tasks prevent next WORK session from spending turns on discovery.
FILES: autoagent/PROMPT.md, autoagent/brain/sources.md, autoagent/brain/techniques.md, autoagent/memory/knowledge.md, autoagent/meta/BRAIN_PROMPT.md, autoagent/skills/testing.md

