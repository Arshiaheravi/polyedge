# Brain — Implemented Techniques

## Reflexion verbal self-feedback — implemented 2026-03-17
What: After each session, write ACCOMPLISHED/FAILED/DIFFERENT/RULE instead of numeric scores
Where: PROMPT.md activity_log format
Source: Shinn et al. NeurIPS 2023
Expected impact: knowledge capture improves, rules extracted from failures

## Context U-curve structuring — implemented 2026-03-17
What: Critical rules at TOP of prompt, final checklist at BOTTOM — middle gets less attention
Where: PROMPT.md structure
Source: Liu et al. 2023 (Lost in the Middle)
Expected impact: rule-following rate ~50%→~80%

## FAST-FORWARD MODE — implemented 2026-03-19
What: If task already has defined steps, skip research phase and start coding immediately
Where: PROMPT.md (WHEN BUILDING A FEATURE section)
Source: Direct observation — engineer was spending 20-25 turns on re-research
Expected impact: task completion rate ~40%→~75%

## Dynamic replanning — implemented 2026-03-19
What: After a mid-task failure, re-read remaining steps and ask if failure invalidates future steps
Where: PROMPT.md
Source: arxiv 2503.09572v3 (PLAN-AND-ACT)
Expected impact: cascading mid-task failures → 0

## Tail truncation for memory injection — implemented 2026-03-19
What: Inject only last N chars of memory files — prompt stays fixed size forever
Where: run.py build_prompt()
Source: LLMLingua + direct observation of context growth
Expected impact: token exhaustion → 0%, prompt always ~2700 tokens

## Self-critique gate — implemented 2026-03-19
What: Before running tests, re-read the 3 most-changed functions and ask: (a) matches intent? (b) edge cases missed? (c) all return values wired through?
Where: PROMPT.md (STEP 0, before STEP 1 tests)
Source: LangChain State of Agent Engineering 2026 (write→critique→test→validate cycle)
Expected impact: Catches wiring bugs and intent drift that tests can't detect; reduces retry loops from test failures

## ACE incremental append rule — implemented 2026-03-19
What: Never overwrite existing knowledge.md rules — always append with date. Structured incremental updates prevent knowledge erosion.
Where: PROMPT.md (session logging section, knowledge.md update instruction)
Source: arxiv 2510.04618 (Agentic Context Engineering)
Expected impact: Accumulated rules stay intact across sessions; historical reasoning preserved

## Context budget tracking — implemented 2026-03-19
What: Write "Steps: N total | N remaining" header in current_task.md, updated each step. If remaining > 5 and context is long, sub-divide into a continuation task.
Where: PROMPT.md (current_task.md format)
Source: Anthropic context engineering article + Google BATS (budget awareness improves completion)
Expected impact: Prevents context exhaustion mid-task; agent self-regulates instead of getting truncated

## Few-shot format anchoring — implemented 2026-03-19
What: Add a CORRECT and WRONG concrete example directly adjacent to the activity_log format template in PROMPT.md. Examples narrow the output space and prevent format drift more reliably than rules alone.
Where: PROMPT.md (activity_log format section)
Source: comet.com/site/blog/few-shot-prompting — "examples narrow the space of plausible outputs"
Expected impact: Eliminates recurring activity_log format failures (Output tail: pattern, bold titles, raw CLI text) — format compliance from ~60% → ~95%

## Test-first specification — implemented 2026-03-19
What: Before writing feature code, write in plain English what the 3 tests will verify (happy path, edge case, guard condition). This is the acceptance criteria. If all 3 pass, the feature is done.
Where: skills/testing.md (TEST-FIRST SPECIFICATION section)
Source: anthropic.com/engineering/demystifying-evals-for-ai-agents — "evals as specifications, not validation"
Expected impact: Catches scope drift before code is locked in; reduces retry loops from misunderstood requirements

## Task routing / difficulty classifier — implemented 2026-03-19
What: Before acting, classify request as single-step (act directly), multi-file (plan first), or open-ended (explore first). Skip planning turns on trivial tasks; enforce planning on complex ones.
Where: PROMPT.md (TASK ROUTING section, after WHEN BUILDING A FEATURE)
Source: arxiv.org/abs/2502.09601 (CoT-Valve) + anthropic.com/research/building-effective-agents
Expected impact: Fewer wasted planning turns on simple edits; fewer unplanned executions on complex features

## Hypothesis-ranked error recovery — implemented 2026-03-19
What: When a tool call fails, list 2-3 hypotheses ranked by likelihood, check the most likely one first, try a different approach rather than retrying the same call. Stop after 2 retries and log the blocker.
Where: PROMPT.md (WHEN A TOOL CALL FAILS section)
Source: Latent.Space / 2024 in Agents
Expected impact: Eliminates infinite retry loops; blocked states get logged instead of looping indefinitely

## Loop exit conditions — implemented 2026-03-19
What: Before entering any refinement loop (fix-test-retry), define the acceptance criterion explicitly. Stop after 2 retries if no concrete criterion exists.
Where: PROMPT.md (LOOP EXIT CONDITIONS section)
Source: anthropic.com/research/building-effective-agents (evaluator-optimizer pattern)
Expected impact: Prevents indefinite test-fix-retry spirals that exhaust context windows

## Skill Library INDEX — implemented 2026-03-19
What: Populated skills/INDEX.md with a quick-reference table (task type → skill file → key workflow) plus proven common task workflows (add scoring function, add endpoint, add frontend feature, fix test).
Where: autoagent/skills/INDEX.md
Source: Latent.Space / 2024 in Agents — skill library +22.5% task success from reusing proven decompositions
Expected impact: Agent finds relevant skill file in one read instead of guessing or skipping

## CONTEXT_SUMMARY gate at half-full context — implemented 2026-03-20
What: When context is more than half full, emit a structured CONTEXT_SUMMARY block (decisions, current state, next step) before continuing. Allows clean resume from /compact or new session.
Where: PROMPT.md (current_task.md format section, step 6)
Source: code.claude.com/docs/en/best-practices
Expected impact: Prevents silent context truncation mid-task; session can always be resumed from the summary

## Self-check block before chaining output — implemented 2026-03-20
What: Before any output that feeds into the next step, verify (1) format matches, (2) no uncertain claims, (3) no contradictions with earlier state. Mark uncertain items with `UNCERTAIN:`.
Where: PROMPT.md (STEP 0 — Self-critique section)
Source: promptbuilder.cc/blog/claude-prompt-engineering-best-practices-2026
Expected impact: Catches format drift and uncertain claims before they propagate into subsequent tool calls

## SKILL_LIBRARY progressive chaining — implemented 2026-03-20
What: After each successful subtask, emit a SKILL: tag (name + one-sentence description). On next subtask, scan accumulated tags and reuse matching patterns instead of re-deriving them.
Where: PROMPT.md (SKILL_LIBRARY section, after WHEN BUILDING A FEATURE)
Source: arxiv 2512.17102 (SAGE): 59% fewer tokens, 26% fewer interaction steps on chained tasks
Expected impact: Faster subtask execution in multi-step features; avoids redundant exploration of known patterns

## Tool output validation before chaining — implemented 2026-03-20
What: Before using the result of any tool call as input to the next step, verify it's what you expected. Confirm file writes by reading back, confirm tests by checking exit code, confirm routes by grepping.
Where: PROMPT.md (STEP 0 — Self-critique section, tool output validation block)
Source: claude-code-best-practices training knowledge (general reliability pattern)
Expected impact: Prevents silent propagation of bad tool outputs through multi-step plans; surfaces failures at the step where they occur instead of several steps later

## Intra-function import patching rule (expanded) — implemented 2026-03-20
What: When ANY function (not just routes, also scheduler/service) uses `from module import func` inside the body, patch at `module.func`. The calling module never holds a reference to `func`.
Where: skills/testing.md (PATCHING section — added "Intra-function imports" subsection)
Source: Recurring pattern in scheduler and service tests — same bug hits different call sites (polymarket_service vs scheduler)
Expected impact: Eliminates the most repeated test failure class across 2+ sessions

## Float formatting assertion safety — implemented 2026-03-20
What: `:.0f` rounds halves up (112.51 → "113"). Test assertions for formatted numbers must use the post-rounded value or an invariant substring.
Where: skills/testing.md + knowledge.md (appended rule)
Source: Session #57 test failure — asserted "112" in subject, actual was "113"
Expected impact: Eliminates one-off format assertion failures in email subject line tests

## Global-plan consistency check in self-critique — implemented 2026-03-20
What: In STEP 0 self-critique, add question 4: "Does what I just built invalidate any remaining steps?" A mid-task discovery can make a future step wrong; catching it at critique time is cheaper than at test time.
Where: PROMPT.md (STEP 0 self-critique, question 4)
Source: arxiv 2512.03549 (PARC Self-Reflective Coding Agent) — 2-level reflection: local + global
Expected impact: Catches plan invalidation before executing stale steps; prevents downstream confusion

## Typed tool-failure taxonomy (4 categories) — implemented 2026-03-20
What: Classify failures as initialization/parameter/execution/result-interpretation before attempting recovery. Each category implies a different fix strategy.
Where: PROMPT.md (WHEN A TOOL CALL FAILS — Step 1 classification)
Source: arxiv 2601.16280 (Tool Invocation Reliability Diagnostic Framework)
Expected impact: Faster root-cause identification; prevents applying wrong fix category to a failure

## Few-shot success-pattern anchoring in recovery — implemented 2026-03-20
What: Before guessing a fix for a failure, scan knowledge.md for a matching RULE from past successes. Prior successful recovery is stronger evidence than a hypothesis.
Where: PROMPT.md (WHEN A TOOL CALL FAILS — Step 2, item 3)
Source: arxiv 2502.18449 (SWE-RL) — score candidates by similarity to known-good patterns
Expected impact: Faster convergence on correct fix; leverages accumulated session rules directly

## Verification report format (STEP 2.5) — implemented 2026-03-20
What: Before committing, emit a structured PASS/FAIL report: Import check / Tests / Frontend / Audit (Marcus) / READY TO COMMIT. Makes the gate state explicit and prevents silent "commit anyway" without confirming all checks passed.
Where: PROMPT.md (STEP 2.5, between frontend check and commit)
Source: github.com/affaan-m/everything-claude-code/skills/verification-loop/SKILL.md
Expected impact: No more ambiguous "tests passed, committing" without explicit gate confirmation — each check is named and its status is stated

## Alpaca API retry pattern + alpaca-py — implemented 2026-03-20
What: Exponential backoff on 503/504 (`2**attempt` sleep), immediate re-raise on 401/403, `get_open_position` before sell. Use `alpaca-py` SDK not deprecated `alpaca-trade-api`.
Where: skills/coding.md (EXTERNAL API ERROR HANDLING section)
Source: alpaca.markets/learn/how-to-fix-common-trading-api-errors + alpaca.markets/sdks/python
Expected impact: Prevents silent order failures and Alpaca 401 retry loops in auto-trader

## Gunicorn multi-worker production startup — implemented 2026-03-20
What: Use `gunicorn -k uvicorn.workers.UvicornWorker -w 4` instead of plain `uvicorn` for production. Process fault isolation + CPU parallelism at zero code cost.
Where: skills/coding.md (PRODUCTION STARTUP section)
Source: fastlaunchapi.dev/blog/fastapi-best-practices-production-2026
Expected impact: `/api/dashboard` screener resilient under concurrent users; process crash doesn't kill all workers

## Structured failure articulation — implemented 2026-03-20
What: When feeding test/tool failure back into a fix, state "specific failing step + why + what fix should address" — not raw stack trace. Surfaces the actual cause faster than pasting error output.
Where: PROMPT.md (WHEN A TOOL CALL FAILS section)
Source: arxiv 2508.11126 (AI Agentic Programming Survey)
Expected impact: Faster root-cause identification in fix-test-retry cycles; fewer misdiagnosed hypotheses

## Phase-grouped task structure for multi-domain tasks — implemented 2026-03-25
What: When a task touches 3+ distinct domains (backend + frontend + tests), group steps into labeled phases in current_task.md (Phase 1: Backend / Phase 2: Frontend / Phase 3: Tests) instead of a flat numbered list. The phase header tells a resuming agent WHERE in the task it is without re-reading all steps.
Where: PROMPT.md (step 6 — current_task.md format section, Phase grouping rule)
Source: arxiv 2512.10398 (Confucius Code Agent) — hierarchical working memory for long-context reasoning; persistent note-taking for cross-session task continuity
Expected impact: Multi-domain tasks that span sessions resume faster — agent immediately knows it's in Phase 2 (Frontend) without re-reading the entire plan; reduces re-exploration at session resumption

## FastAPI production safety rules (CORS wildcard prohibition + async discipline) — implemented 2026-03-25
What: (1) Never use `allow_origins=["*"]` in CORS config — use explicit origin list only. (2) `async def` route handlers must never contain blocking I/O (no time.sleep, no sync DB calls) — these stall the uvicorn event loop.
Where: autoagent/skills/coding.md (FASTAPI PRODUCTION SAFETY RULES section)
Source: fastlaunchapi.dev/blog/fastapi-best-practices-production-2026; dev.to/thesius_code production-ready FastAPI 2026
Expected impact: Prevents silent CORS security regression (wildcard) and event-loop starvation bugs introduced by sync calls in async routes — two bugs invisible at dev time that cause production failures

## Visible-element filter for mobile Playwright checks — implemented 2026-03-25
What: When checking element dimensions (height, width) at mobile viewport, filter by getBoundingClientRect().height > 0 to skip elements in display:none sections. Also use element+class selector (`.btn.btn-primary`) not just class (`.btn-primary`) to avoid matching links styled as buttons.
Where: autoagent/skills/playwright.md (VISIBLE ELEMENT FILTER section)
Source: Session #119 failure — querySelectorAll('.btn-primary') returned 0px for buttons inside hidden dashboard tabs
Expected impact: Eliminates false-zero results in mobile viewport height checks; CHECK 91-style failures won't recur

## AAA pattern + one-assert-per-test — implemented 2026-03-20
What: Tests follow Arrange-Act-Assert structure (3 blocks, blank line between). One behavior per test so failures are pinpointed.
Where: skills/testing.md (TEST STRUCTURE section from ECC TDD skill)
Source: github.com/affaan-m/everything-claude-code/skills/tdd-workflow/SKILL.md
Expected impact: Cleaner test failures; easier to diagnose which assertion triggered

## Marcus error-message non-disclosure check — implemented 2026-03-20
What: HTTP error responses must use generic messages — no stack traces, DB error strings, or file paths exposed in 4xx/5xx JSON.
Where: skills/audit.md (Marcus checklist, last item)
Source: github.com/affaan-m/everything-claude-code/skills/security-review/SKILL.md
Expected impact: Prevents accidental information leakage in error responses

## Recent-session skimming before skill updates — implemented 2026-03-19
What: In BRAIN sessions, before searching the web, skim last 10 activity_log entries for failure patterns. Anchors research to real failures instead of hypotheticals.
Where: meta/BRAIN_PROMPT.md (STEP 1B)
Source: arxiv 2508.07407 (Self-Evolving AI Agents) — experience replay: evolve from real interaction data, not abstract principles
Expected impact: Brain sessions improve the agent on its actual bottlenecks instead of theoretical issues

## Session baseline health check — implemented 2026-03-21
What: Before picking any task, run the test suite once to verify starting from a known-good green state. If tests are already red, fix them before starting new work. Prevents compounding failures on top of a broken baseline.
Where: PROMPT.md (EVERY SESSION — WHAT TO DO, step 1)
Source: anthropic.com/engineering/effective-harnesses-for-long-running-agents
Expected impact: Eliminates class of bugs where a session starts on broken code and produces confusing failures that mix prior and new breakage

## Brittle Test Cascade failure mode — implemented 2026-03-21
What: Before adding a new loop pass or list element, grep for hard-coded iteration counts in tests (call_count == N). Also grep for fake/stub objects when adding model fields. Both fail immediately and silently.
Where: skills/agent-patterns.md (Failure Mode #7), skills/testing.md (BRITTLE TEST PATTERNS section)
Source: Session #77-78 recurring failures (FakeSignal missing sector attr; call_count == 2 broke on 3rd pass)
Expected impact: Eliminates the most common test failure class in feature-extension sessions

## Co-locating related fields in same batch query — implemented 2026-03-21
What: When adding a new field that uses the same underlying DB query data as an existing field, compute both in the same loop iteration to avoid a second query. Ask "do I already have this data in scope?" before writing a new query.
Where: skills/performance.md (item #0 in performance killers list)
Source: Session #73 RULE — score_velocity used same DailyScore history as score_history
Expected impact: Prevents accidental N+2 queries when adding correlated fields

## 8-step scoring wiring chain — implemented 2026-03-21
What: Full checklist of all 8 layers for a new scoring dimension: pure function → dashboard.py call → generate_signal() param → signature → scoring logic → score_breakdown → StockSignal constructor → model field + frontend badge. Missing any layer silently produces wrong scores.
Where: skills/coding.md (8-STEP WIRING CHAIN section)
Source: Session #71 RULE — confirmed all 8 steps required
Expected impact: Eliminates silent scoring bugs from missed wiring layers

## 15-minute unit rule for task steps — implemented 2026-03-21
What: Each step in current_task.md must be: (1) independently verifiable, (2) single dominant risk, (3) clear done condition. Steps that don't meet all 3 must be split further. This forces granular, testable work units.
Where: PROMPT.md (step 6 — current_task.md format, step quality bar)
Source: github.com/affaan-m/everything-claude-code/skills/agentic-engineering/SKILL.md
Expected impact: Prevents vague steps like "implement feature" that are hard to track progress on

## Meta-prompt analysis in BRAIN sessions — implemented 2026-03-21
What: For each failure pattern found in activity_log, explicitly ask "which rule in PROMPT.md should have prevented this?" If the rule doesn't exist → create it. If it exists but was ignored → make it more prominent (move earlier, add example).
Where: meta/BRAIN_PROMPT.md (STEP 1B — after skimming failures)
Source: Meta-prompting research (intuitionlabs.ai) — LLMs consistently produce better prompts than human engineers when critiquing their own prompts
Expected impact: META and BRAIN sessions produce more targeted rule improvements instead of general refinements

## Diff-level edit provenance for debugging — implemented 2026-03-21
What: When tests fail after a code change, immediately run `git diff` to trace from specific changed lines to the failing assertion. Never debug from memory of what you changed.
Where: PROMPT.md (WHEN A TOOL CALL FAILS — recovery section, after structured failure articulation)
Source: arxiv 2508.11126 (AI Agentic Programming Survey) — diff-level provenance prevents re-introducing previously fixed errors
Expected impact: Faster root-cause identification; eliminates guessing when the failure is in a function that was recently modified

## Failure-conditioned knowledge search — implemented 2026-03-21
What: When a test fails, search knowledge.md for the SPECIFIC function name, test name, or error type from the failure — not a general "scan for relevant rules." A past fix for the exact function is stronger evidence than a generic rule.
Where: PROMPT.md (WHEN A TOOL CALL FAILS — step 2, item 3 — enhanced SWE-RL rule)
Source: arxiv 2508.11126 + SWE-RL arxiv 2502.18449 — failure-conditioned retrieval surfaces exact past fixes
Expected impact: Faster convergence on correct fix for recurring failures in the same codebase functions

## Milestone-based compaction timing — implemented 2026-03-21
What: Use /compact or CONTEXT_SUMMARY AFTER a step is fully done, never in the middle of active debugging. Compacting mid-debug loses the failure context needed to diagnose the error.
Where: PROMPT.md (CONTEXT_SUMMARY gate section, step 6)
Source: github.com/affaan-m/everything-claude-code/skills/agentic-engineering/SKILL.md
Expected impact: Prevents lost debugging context when /compact is triggered at wrong time in fix cycles

## Irreversibility check in self-critique gate — implemented 2026-03-24
What: Added Q5 to STEP 0 self-critique: "Does this session touch irreversible actions (DB deletes, Stripe charges, Telegram sends)? Name them explicitly and confirm they're mocked/guarded."
Where: autoagent/PROMPT.md (STEP 0 self-critique, question 5)
Source: arxiv 2601.02749 (The Path Ahead for Agentic AI) — agents consistently underweight cost of irreversible actions
Expected impact: Prevents accidentally firing live Telegram/Stripe/email calls in sessions that only intend to test them

## Hypothesis property-based testing pattern — implemented 2026-03-24
What: Added a new section to testing.md documenting Hypothesis property-based testing for PolyEdge invariants (auth always 401, tier limits never exceeded, cached field always present). Includes concrete PolyEdge example patterns.
Where: autoagent/skills/testing.md (PROPERTY-BASED TESTING section)
Source: dasroot.net Python Agent Testing Best Practices 2026 — 72% of deployed LLM agents show non-deterministic behavior; invariant testing is more reliable for auth/validation paths
Expected impact: Future testing sessions can use Hypothesis to generate adversarial inputs for auth and tier-limit routes instead of only writing example-based tests

## ACE Curator step in BRAIN sessions — implemented 2026-03-24
What: Each BRAIN session, scan knowledge.md for duplicate or superseded RULE: entries. Merge duplicates into one canonical rule (best wording + most recent date). Remove rules contradicted by newer ones.
Where: meta/BRAIN_PROMPT.md (Step 1C, added between Step 1B and Step 2)
Source: softmaxdata.com — ACE ICLR 2026 paper; Generate→Reflect→Curate loop prevents context collapse from redundant knowledge entries
Expected impact: knowledge.md stays compact and authoritative instead of growing into a 100+ rule fragmented log; rules that overlap stop confusing the agent

## Periodic De-Sloppify tech-debt trigger — implemented 2026-03-24
What: Every 5 work sessions, automatically add a META code-quality audit task to the backlog — scan changed files for cross-file coupling and test specificity degradation introduced by agent edits. Triggered in PROMPT.md step 3 by counting work sessions in sessions.json.
Where: PROMPT.md (EVERY SESSION — WHAT TO DO, step 3 — PERIODIC TECH-DEBT CHECK block)
Source: arxiv 2511.04427 (MSR 2026) + everything-claude-code autonomous-loops De-Sloppify pattern
Expected impact: Prevents technical debt accumulation that empirically reverses velocity gains after 6-8 weeks; ensures each 5-session block ends with a quality pass

## Activity log archival (active context compression) — implemented 2026-03-24
What: BRAIN sessions check activity_log.md entry count. If > 30 entries, archive oldest 20 to activity_log_archive.md. Keeps the auto-loaded context file from growing unbounded.
Where: meta/BRAIN_PROMPT.md (Step 1D, added between Step 1C and Step 2)
Source: arxiv 2601.07190 (Active Context Compression) — 22.7% token reduction with autonomous context pruning, identical accuracy
Expected impact: Prevents activity_log.md from exceeding context window limits as session count grows beyond 50-100

## Backlog low-water-mark check — implemented 2026-03-24
What: After removing a completed task from backlog.md (Step 3 of post-task logging), count remaining HIGH PRIORITY items. If < 2, immediately generate 3+ new testing tasks before closing.
Where: PROMPT.md (STEP 3 commit section, after the backlog cleanup instruction)
Source: Observed pattern — 4 META sessions spent replenishing empty backlog (sessions 6/16/26/36); WORK sessions could self-replenish instead
Expected impact: Eliminates reactive backlog replenishment; next session starts with tasks ready instead of spending context on discovery

## Symmetry audit rule in testing — implemented 2026-03-24
What: When a coverage gap is found in function A of module M, immediately audit all analogous functions in M for the same gap type. Do NOT move to the next module until the full symmetry check is done.
Where: autoagent/skills/testing.md (BRANCH AUDIT WORKFLOW — checklist, SYMMETRY AUDIT RULE block)
Source: Session #39-40 pattern — send_telegram had missing True-return path; same gap existed in send_sms but wasn't caught in the same session
Expected impact: Prevents spending a full additional session finding the same gap in a sibling function

## A-MAC five-factor memory admission control — implemented 2026-03-24
What: Added 5-factor checklist to BRAIN_PROMPT.md Step 1C (curation step): future utility, factual confidence, semantic novelty, temporal recency, content type priority. BRAIN sessions now score each rule against these 5 factors to decide keep/merge/drop — not just "check for duplicates."
Where: meta/BRAIN_PROMPT.md (Step 1C, added 5-factor block after existing merge/supersede checks)
Source: arxiv 2603.04549 (A-MAC, ICLR 2026 Workshop MemAgent)
Expected impact: knowledge.md stays compact and signal-dense; old one-time-fix rules get aged out instead of accumulating indefinitely

## Anthropic frontend-design skill download + design.md rewrite — implemented 2026-03-24 (session 61)
What: Downloaded official Anthropic frontend-design SKILL.md (correct path: skills/frontend-design/SKILL.md). Extracted: bold aesthetic direction framework (Purpose/Tone/Constraints/Differentiation), background depth patterns (gradient meshes, noise textures, grain overlays), motion hierarchy (one orchestrated load > scattered micro-interactions). Also rewrote design.md from stale StockCards content to accurate PolyEdge color system (actual :root CSS vars), file structure (single index.html), and card anatomy.
Where: autoagent/skills/frontend-design.md (new), autoagent/skills/design.md (complete rewrite)
Source: https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md
Expected impact: Future UI/UX sessions read an accurate design.md with real CSS variables instead of wrong values from a prior project; frontend-design.md provides inspirational design framework for PolyEdge's current FEATURE MODE

## XSS grep command in Marcus audit checklist — implemented 2026-03-24 (session 61)
What: Added `grep -n 'innerHTML.*\${' frontend/index.html` command to Marcus security checklist in audit.md. After sessions 59+60 each found missed XSS injections in different function types (renderXxx vs buildXxx template helpers), the grep command catches ALL innerHTML template literals in one sweep rather than relying on a category-based mental search.
Where: autoagent/skills/audit.md (Marcus checklist, XSS line)
Source: Sessions 59+60 failure pattern — 2 consecutive sessions needed to fully fix XSS because pattern-based inspection missed non-renderXxx functions
Expected impact: A single pre-commit grep catches all innerHTML injection points at once; eliminates the "missed one template helper" pattern that caused session 61 to need a follow-up XSS fix

## CSS class refactor → Playwright selector sync — implemented 2026-03-24 (session 61)
What: Added "CSS CLASS REFACTOR" section to playwright.md: when renaming CSS classes in a large refactor, grep the check script for old class names before running it. Old class selectors in check scripts silently "pass" on null (element not found) instead of catching regressions.
Where: autoagent/skills/playwright.md (new section before RECONNAISSANCE pattern)
Source: Session 58 failure — converted lb-table→lb-grid; Playwright checks referenced .bettor-row/.bettor-name → 2 first-run failures
Expected impact: Eliminates first-run Playwright failures after CSS class refactors; agent updates check script at the same time as the refactor

## design.md + INDEX.md stale reference cleanup — implemented 2026-03-24 (session 61)
What: Removed stale references to the previous "StockCards" project from design.md (rewrote entire file for PolyEdge) and INDEX.md (updated frontend-only feature workflow, API endpoint workflow, scoring function workflow to reference PolyEdge's actual files: backend/app/routes/, frontend/index.html).
Where: autoagent/skills/design.md, autoagent/skills/INDEX.md
Source: Session 61 META audit — design.md referenced styles.css/app.js/PLAY signals/DECK blue which don't exist in PolyEdge; INDEX.md referenced src/stockcards/routes/ which is wrong
Expected impact: Future UI/UX sessions read correct file paths and color variables on first read; eliminates risk of editing wrong files

## pytest.param() named IDs for parametrized tests — implemented 2026-03-24
What: Use `pytest.param("free", 1, id="tier_free")` instead of bare tuples in @pytest.mark.parametrize. Named IDs appear in failure output as "FAILED test_follows[tier_free]" instead of unreadable "FAILED test_follows[0]". Makes parametrize-heavy test suites 3x faster to debug.
Where: skills/testing.md (PARAMETRIZE BEST PRACTICES section, added before IMPORT CHECK)
Source: rednafi.com/python/pytest-param — pytest best practices 2026
Expected impact: Future testing sessions write more debuggable parametrized tests for tier and response-shape invariants

## Activity log archival (first actual archival) — implemented 2026-03-24
What: Archived sessions 1-20 from activity_log.md to activity_log_archive.md. Trimmed main log to 30 entries (sessions 21-50). Rule was implemented in session 41; first archival executed in session 51 (BRAIN).
Where: autoagent/memory/activity_log.md, autoagent/memory/activity_log_archive.md (new)
Source: arxiv 2601.07190 (Active Context Compression)
Expected impact: activity_log.md stays under 10000 tokens; auto-loaded context doesn't bloat over time

## Accessibility check patterns in playwright.md — implemented 2026-03-24 (session 71)
What: Added 3 accessibility Playwright checks to playwright.md (focus outlines on interactive elements, alt text on images, labels on form inputs), adapted from browser-qa/SKILL.md. Marked as non-blocking warnings for PolyEdge (not public-a11y-required yet).
Where: autoagent/skills/playwright.md (ACCESSIBILITY CHECKS section)
Source: affaan-m/everything-claude-code skills/browser-qa/SKILL.md (2026-03-23)
Expected impact: Future sessions adding forms or nav items have a ready-to-paste a11y check pattern; prevents invisible form inputs and unnavigable keyboards from shipping silently

## 10-dimension visual audit checklist in design.md — implemented 2026-03-24 (session 71)
What: Added VISUAL AUDIT CHECKLIST section to design.md with 10 pass/fail dimensions (color, typography, spacing, consistency, responsive, animation, a11y, density, empty states, loading states). Also extended AVOID section with 4 new AI slop patterns from ECC design-system Mode 3 (purposeless glass morphism, rounded data tables, excessive scroll animations, heavy shadows on dark).
Where: autoagent/skills/design.md (VISUAL AUDIT CHECKLIST + AVOID sections)
Source: affaan-m/everything-claude-code skills/design-system/SKILL.md Mode 2 + Mode 3 (2026-03-23)
Expected impact: Future UI sessions have a concrete pre-commit checklist instead of subjective quality review; AI slop list now covers 10 anti-patterns vs 6 previously

## Toast stack implementation pattern in design.md — implemented 2026-03-24 (session 71)
What: Added concrete vanilla JS + CSS implementation pattern for a stacked toast notification system to design.md. Includes the collapsed state scale formula (scale - 0.05 * index), height-accumulation expand pattern, and data-mounted interruptible entry animation — all ready to copy directly into index.html for the backlog "toast notification stack" task.
Where: autoagent/skills/design.md (TOAST NOTIFICATION STACK section)
Source: emilkowal.ski/ui/building-a-toast-component (Sonner/Emil Kowalski pattern)
Expected impact: The backlog toast task can be implemented without research turns — the pattern is pre-resolved and concrete

## Probability chip CSS pattern in design.md — implemented 2026-03-24 (session 71)
What: Added concrete CSS for YES/NO outcome pills on bet rows (dark-tinted bg + bright border + bright text formula for dark themes). Includes HTML structure pattern (direction + price in one atomic pill) and mobile touch-target note.
Where: autoagent/skills/design.md (PROBABILITY CHIP section)
Source: 2026 fintech dark-mode research; badges-vs-chips UI pattern analysis
Expected impact: The backlog bet-activity-feed enhancement task can copy the pill CSS directly — no research needed

## Observer loop guard (5-layer runaway prevention) — implemented 2026-03-24 (session 81)
What: Added "OBSERVER LOOP GUARD" to LOOP EXIT CONDITIONS section in PROMPT.md. If the same tool is called with the same params 3+ times, the agent STOPS and writes BLOCKED to current_task.md — no 4th retry. Prevents runaway loops that exhaust context windows on genuinely broken environments.
Where: PROMPT.md (LOOP EXIT CONDITIONS section, after the 2-retry stop rule)
Source: affaan-m/everything-claude-code v1.9.0 — 5-layer loop prevention guard (March 2026)
Expected impact: Eliminates runaway tool-call loops that silently exhaust context; converts silent failure into explicit BLOCKED log.

## SPA wait strategies in Playwright (waitForResponse pattern) — implemented 2026-03-24 (session 81)
What: Added "SPA WAIT STRATEGIES" section to playwright.md with `waitForResponse()` (precise, waits for specific API call) and `networkidle` (coarser) patterns for PolyEdge's API-loaded content. Includes working Python code snippet.
Where: autoagent/skills/playwright.md (new section at end)
Source: affaan-m/everything-claude-code skills/e2e-testing/SKILL.md (v1.9.0, March 2026)
Expected impact: Eliminates intermittent Playwright race conditions where checks pass/fail randomly because they don't wait for the /bettors API response before asserting on leaderboard cards.

## 2026 SaaS pricing page CRO patterns — implemented 2026-03-24 (session 81)
What: Added outcomes-over-features rule (+34% conversion), explicit checkmark/X comparisons (-31% support inquiries), social proof on pricing page (+15-25%), and mobile stack note (2.3x better) to the "Pricing page" section of design.md.
Where: autoagent/skills/design.md (Pricing page section, expanded with InfluenceFlow 2026 research)
Source: InfluenceFlow SaaS Pricing Page Best Practices 2026; Aimers CRO Trends 2026
Expected impact: Next WORK session on pricing section uplift has concrete 2026 research-backed copy and layout rules without needing its own research phase.

## Follows tab dashboard feel pattern — implemented 2026-03-24 (session 81)
What: Added "FOLLOWS TAB DASHBOARD FEEL" section to design.md with a concrete summary strip HTML/CSS pattern (total follows, active bets 24h, cumulative P&L) and rules for when to show/hide it.
Where: autoagent/skills/design.md (new section)
Source: Backlog task analysis + copy-trading UX research
Expected impact: Next WORK session on follows tab can copy the summary strip pattern directly without design research.

## STEP 0 skip condition fix + frontend XSS gate — implemented 2026-03-24 (session 81)
What: Changed STEP 0 self-critique skip condition from "zero Python code changed" to "zero files changed" so it runs for frontend-only sessions. Added Q6 (frontend XSS gate) that requires running both audit.md greps inline in STEP 0 whenever frontend/index.html is changed.
Where: PROMPT.md (STEP 0 self-critique, skip condition + Q6)
Source: Session 81 META analysis — STEP 0 was silently skipped for ALL UI/UX sessions (no Python touched). XSS audit cycle (sessions 59→67→73→79) happened because STEP 0.5's audit.md wasn't always run either. Moving the grep to STEP 0 Q6 makes it impossible to miss.
Expected impact: XSS introduced in UI/UX sessions is caught by the author session (not 3-4 sessions later by a dedicated AUDIT session). Breaks the recurring 4-session XSS cycle permanently.

## SPA hidden-element navigation rule in playwright.md — implemented 2026-03-24 (session 91)
What: Added "SPA HIDDEN ELEMENT NAVIGATION" section to playwright.md. Never click PolyEdge nav elements by ID (display:none at desktop). Always use `page.evaluate("showView(...)")` or `page.evaluate("showTab(...)")`. Also added multi-screen check pattern with isolated `scr_page` instance.
Where: autoagent/skills/playwright.md (new section at end, after SPA WAIT STRATEGIES)
Source: Session #90 failure — ElementHandle.click() on #nav-leaderboard failed silently at 1280px desktop viewport
Expected impact: Eliminates first-run Playwright failures after any SPA navigation change; agents don't waste a retry discovering hidden-element click failures

## coding.md stale-path cleanup + fragile zones guard — implemented 2026-03-24 (session 91)
What: (1) Fixed PYTHON BACKEND PATTERNS and FRONTEND PATTERNS sections — removed stale StockCards paths (src/stockcards/routes/, frontend/app.js, frontend/styles.css); replaced with correct PolyEdge paths (backend/app/routes/, frontend/index.html, port 8002). (2) Added FRAGILE ZONES section: when editing auth.py, scheduler.py, or polymarket.py, double-check the interface contract (JWT payload shape, datetime tz-awareness, normalised field names).
Where: autoagent/skills/coding.md (PYTHON BACKEND PATTERNS, FRONTEND PATTERNS, AFTER WRITING CODE sections)
Source: (1) SWE-Skills-Bench arxiv 2603.15401 — stale project-specific paths in skills files actively degrade agent performance; (2) arxiv 2603.06847 Fault Taxonomy — top propagation paths in agentic codebases are auth/datetime/API-normalization interface mismatches
Expected impact: Future WORK sessions read correct file paths on first try; agents double-check JWT/scheduler/polymarket interfaces before committing changes that could silently break all auth or all bet detection

## click-path-audit.md skill (vanilla JS) — implemented 2026-03-24 (session 91)
What: Created new skill file `autoagent/skills/click-path-audit.md` — PolyEdge-specific adaptation of ECC click-path-audit. Documents PolyEdge's 5 global state variables, 4 common cancellation patterns (toggle+reload race, follow+cache stale, tab switch+pending fetch, disclosure cache invalidation), and a structured audit output format. Added to INDEX.md.
Where: autoagent/skills/click-path-audit.md (new file), autoagent/skills/INDEX.md
Source: affaan-m/everything-claude-code skills/click-path-audit (2026-03-22) — 54 state-interaction bugs found in one session using this method in original React/Zustand repo
Expected impact: Future debugging sessions for "button does nothing" UI bugs have a systematic trace method instead of ad-hoc guessing

## Event-driven commit reminders (instruction fade-out prevention) — implemented 2026-03-21
What: At every commit, re-display the 4 most commonly forgotten rules as a COMMIT REMINDERS block: no autoagent/ in project git add, use py not python3, project branch=main vs autoagent branch=master, clear current_task.md immediately after push. Rules re-injected at the exact decision point where they're most needed prevent instruction fade-out — the pattern where critical rules are read at session start but forgotten 30 tool calls later.
Where: PROMPT.md (STEP 3 — COMMIT REMINDERS block before step 1)
Source: arxiv 2603.05344 (OPENDEV) — event-driven system reminders counteract instruction fade-out in long sessions
Expected impact: Eliminates wrong-branch push, autoagent-in-git-add, and current_task.md not cleared — the 3 most common post-commit errors from the activity log

## Grep-before-picking rule — implemented 2026-03-25
What: Before picking any "add/implement/build" backlog task, run a one-line grep for the feature's key function/class name in the relevant file. If found, remove the task from backlog and pick next.
Where: PROMPT.md (EVERY SESSION — WHAT TO DO, step 3 — GREP-BEFORE-PICKING block)
Source: Sessions 89+99 — "animateCounter" and "color-coded P&L" were already implemented but remained in backlog, wasting a full implementation turn each time
Expected impact: Eliminates the "stale backlog item" waste (2+ occurrences in sessions 89-99); 10-second grep saves 20-minute re-implementation

## Edge Score design pattern + competitive intelligence backlog — implemented 2026-03-25 (session 111 BRAIN)
What: (1) Added "Conviction / Edge Score badge" design pattern to design.md CARD ANATOMY section — 3-tier pill (green/blue/gray), score derivation formula, honest "—" placeholder until win_rate data available. (2) Added 4 competitive intelligence backlog items: Discord channel, trade-size filter, Edge Score, delayed-free-tier alerts.
Where: autoagent/skills/design.md (CARD ANATOMY section), autoagent/memory/backlog.md (FEATURE MODE ONLY section)
Source: github.com/aarora4/Awesome-Prediction-Market-Tools (40+ competitors); coindesk.com/tech/2026/03/15/ai-agents-are-quietly-rewriting-prediction-market-trading
Expected impact: Next feature-mode leaderboard session has a concrete design spec for the Edge Score badge without research; competitive intelligence backlog prevents feature drift relative to market

## knowledge.md curation — XSS streak rule merge (session 111 BRAIN)
What: Merged duplicate XSS streak rules (line 67 session 107 vs line 156 session 93). Updated to reflect sessions 77–110 = 34+ sessions. Merged the specific grep patterns (`innerHTML.*\${` AND `innerHTML\s*=\s*[a-zA-Z_]`) from the older rule into the newer one. Marked old entry as superseded.
Where: autoagent/memory/knowledge.md (Session #107 Reflexion section)
Source: BRAIN_PROMPT.md Step 1C curation + A-MAC 5-factor admission control
Expected impact: Removes one duplicate rule that could confuse agents seeing two different streak counts for the same invariant
