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
Source: Recurring failures sessions #48 and #57 — same bug, different call sites (polymarket_service vs scheduler)
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

## Event-driven commit reminders (instruction fade-out prevention) — implemented 2026-03-21
What: At every commit, re-display the 4 most commonly forgotten rules as a COMMIT REMINDERS block: no autoagent/ in project git add, use py not python3, project branch=main vs autoagent branch=master, clear current_task.md immediately after push. Rules re-injected at the exact decision point where they're most needed prevent instruction fade-out — the pattern where critical rules are read at session start but forgotten 30 tool calls later.
Where: PROMPT.md (STEP 3 — COMMIT REMINDERS block before step 1)
Source: arxiv 2603.05344 (OPENDEV) — event-driven system reminders counteract instruction fade-out in long sessions
Expected impact: Eliminates wrong-branch push, autoagent-in-git-add, and current_task.md not cleared — the 3 most common post-commit errors from the activity log
