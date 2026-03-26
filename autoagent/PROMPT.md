# AutoAgent — Main Instructions

## BEFORE PICKING ANY TASK — IMPACT FILTER

Every task must answer YES to at least one:
1. Does it make the core product more accurate or reliable?
2. Does it bring more users or revenue?
3. Does it expand coverage or capability?

If a task is pure refactor, cleanup, or "nice to have" with no user impact → skip it, pick next.

## EVERY SESSION — READ FIRST
Read `autoagent/PROJECT.md` first for project rules, codebase conventions, git paths, and test commands. Then read `autoagent/skills/agent-patterns.md` for failure modes that kill sessions. Takes 60 seconds total. Do it before picking a task.

## EVERY SESSION — WHAT TO DO

1. Run `git diff` and `git status` first — finish any in-progress work before starting new.
   **Baseline health check**: If no in-progress work is found, run the test suite once before picking a task — verify you're starting from a known-good green state. If tests are already red, fix them before starting anything new. A broken baseline compounds into a worse session. (Source: Anthropic "Effective Harnesses for Long-Running Agents")
2. Read `autoagent/memory/current_task.md` — if it has unchecked `- [ ]` steps:
   - Run `git log --oneline -5` — if work is committed, clear current_task.md and go to step 3.
   - Run `git status --short` — if relevant files are STAGED (M/A in first column) but not committed, the previous session staged but crashed before commit. **Do NOT re-implement.** Skip directly to Step 8: run tests, fix failures, then commit the staged work.
   - Run `git status --short` — if relevant files are UNTRACKED (`??`) or modified (` M`) but match the task, the previous session wrote code but crashed before staging. **Do NOT re-implement.** Read the existing files first to assess what is already done, check off those steps, and continue from the first genuinely incomplete step.
   - If neither committed nor staged nor modified, continue from the first unchecked step.
3. If no current task, read `autoagent/memory/backlog.md` — pick the highest value unchecked task that you can complete autonomously. **Skip tasks marked "Seb action", "blocked on external input", "FEATURE MODE ONLY", or "BACKEND PENDING"** — backend-pending tasks require backend mode (PROJECT.md must say backend is allowed). Pick the next autonomous task instead. Never start a session on a task you can't finish without human input.
   **GREP-BEFORE-PICKING** (Source: Sessions 89+99 — stale backlog items burned full sessions): Before picking any task that says "add", "implement", or "build [feature]", run ONE grep for the feature's key function or class name in the relevant file (e.g. `grep -n "animateCounter\|runLandingCounters" frontend/index.html`). If found → remove the task from backlog and pick the next one. A 10-second grep prevents a 20-minute re-implementation of something already shipped.
   **EMBEDDED-GREP RULE** (Source: Sessions 170+175+177 — testing backlog items with `Grep:` lines kept being picked without re-running the grep): If the backlog item already contains a `Grep:` command in its description, run THAT exact grep before picking. It was written at task-creation time as the definitive verification — do NOT assume "returns nothing" is still true just because that's what the task says. The session that wrote the task ran the grep then; a later session may have already built the feature. Example: backlog says `Grep: grep -n "percentProfitable" tests/test_polymarket_service.py returns nothing` → run that grep NOW. If it finds a match, the test exists: remove the task, pick the next one.
   **PERIODIC TECH-DEBT CHECK** (De-Sloppify pattern) — MANDATORY, do not skip: Run `py -c "import json; d=json.load(open('autoagent/sessions.json')); print(len([s for s in d if s.get('type')=='work']))"` from project root. If that count is a multiple of 5 (e.g. 5, 10, 15, 20, ...) AND no code quality audit task exists in backlog.md → add one NOW before reading the backlog: "Code quality audit — scan last 5 work sessions' changed files for cross-file coupling, test specificity degradation, and smells introduced by agent edits." Then continue picking tasks as normal. **Do not rely on memory for the count — always run the command.** This prevents technical debt accumulation that stalls velocity after 4-6 weeks. (Source: arxiv 2511.04427 — MSR 2026 empirical study on agentic code quality degradation)
4. If backlog is empty — check PROJECT.md for the current mission mode:
   - **DEBUG MODE**: Generate testing tasks from the All API Endpoints table in PROJECT.md. For each endpoint, check if its test file covers: happy path, auth rejection, bad input, and at least one business-rule edge case. Add any missing coverage as backlog items. Never invent feature tasks when in DEBUG MODE.
   - **FEATURE MODE**: Read the codebase, find what would add most value, add 10 tasks, pick top one
5. **Pick the right skill file** — read `autoagent/skills/INDEX.md`, find the row that matches your task type, then read ONLY that skill file. Do not read all skill files. Examples:
   - Writing a backend route → `coding.md`
   - Creating an Excel export → `xlsx.md`
   - Generating a PDF report → `pdf.md`
   - UI change → `design.md` + `playwright.md`
   - Committing code → `git.md`
   - Writing tests → `testing.md`
   - Pre-commit quality check → `audit.md`
   If no skill matches → proceed without one, then create a new skill file if you discover a reusable pattern.
6. **IMMEDIATELY write your task steps to `autoagent/memory/current_task.md`** before doing anything else:
   ```
   # Current Task: [task name]
   Steps: N total | N remaining
   - [ ] Step 1
   - [ ] Step 2
   - [ ] Step 3
   ```
   **Phase grouping for multi-domain tasks**: If the task touches 3+ distinct domains (e.g., backend route + frontend UI + tests), group steps into labeled phases instead of a flat list:
   ```
   # Current Task: [task name]
   Phase 1: Backend (2 steps) | Phase 2: Frontend (3 steps) | Phase 3: Tests (2 steps) | Remaining: 7
   ## Phase 1: Backend
   - [ ] P1.1 Add model field X
   - [ ] P1.2 Add route GET /foo
   ## Phase 2: Frontend
   - [ ] P2.1 Add tab section
   ...
   ```
   Phase grouping prevents context loss when a multi-domain task spans sessions — the phase header immediately tells the resuming agent WHERE in the task it is. (Source: Confucius Code Agent arxiv 2512.10398 — hierarchical working memory for long-context reasoning)
   **Step quality bar** (15-minute unit rule): Each step must be independently verifiable, have a single dominant risk, and have a clear done condition. If a step can't be verified in isolation → split it. (Source: ECC agentic-engineering skill)
   Update the "remaining" count as you check off steps. If remaining > 5 and context is getting long, sub-divide the rest into a continuation task rather than trying to finish everything in one window.
   **CONTEXT_SUMMARY gate**: When your context is more than half full (many tool calls made, long file reads completed), emit this block before continuing:
   ```
   CONTEXT_SUMMARY:
   - Decisions made: [bullet list]
   - Current state: [one sentence]
   - Next step: [specific next action]
   ```
   This lets the session continue cleanly from a /compact or new window.
   **Compaction timing**: Compact AFTER completing a milestone (step fully done), never DURING active debugging — compacting mid-debug loses the failure context you need to diagnose the error. (Source: ECC agentic-engineering skill)
7. Build each step. Check it off `- [x]` when done. Update the remaining count.
8. When all steps done: commit, push, update activity_log.md, clear current_task.md

## RULES-FIRST ARBITRATION
**When knowledge.md (memory) and PROMPT.md/PROJECT.md (explicit rules) conflict: explicit rules always win.** Memory records what worked in the past; explicit rules encode what SHOULD be done. A past observation cannot override a system-level directive. If knowledge.md says "do X" but PROMPT.md says "do Y", follow PROMPT.md and update knowledge.md to match.
(Source: arxiv 2603.17831 RPMS — rule-augmented memory synergy: rules-first arbitration lifted Llama 3.1 8B from 35.8% to 59.7% task success +23.9pp with no fine-tuning)

## WHEN BUILDING A FEATURE
- Check `autoagent/memory/knowledge.md` for existing patterns before reading source files
- Read only the files you need — don't explore the whole codebase
- Start coding immediately if the task is already defined — don't re-research
- Write tests alongside the feature — one test per branch minimum
- Run the test command from `autoagent/PROJECT.md`
- Fix ALL failures before committing — never commit red tests
- If a skill file exists for your task type, read it first

## SKILL_LIBRARY — progressive chaining
After each successfully completed subtask, emit a one-liner skill tag (in current_task.md or a comment):
```
SKILL: [name] — [one-sentence description of what worked]
```
On the next subtask, scan these tags before starting. If a relevant skill exists, reuse its pattern exactly instead of re-deriving it. Accumulated skill tags reduce context tokens by avoiding redundant exploration.
Examples:
- `SKILL: add-pure-function — pure function takes DataFrames in, returns dict with typed fields`
- `SKILL: wire-model-field — add field to model, grep for similar field in route, follow same wiring pattern`

## TASK ROUTING — classify before acting
Before starting any task, classify it:
- **Single-step** (rename, one-line fix, single file edit): act immediately — skip planning, skip skill reads
- **Multi-file** (new feature, new endpoint + model + frontend): write current_task.md plan first, then build
- **Open-ended** (debug with unknown cause, "find what adds value"): explore first, narrow scope, then act
This prevents wasted planning turns on trivial changes and prevents unplanned execution on complex ones.

## WHEN A TOOL CALL FAILS OR RETURNS UNEXPECTED RESULTS
Do NOT retry the same call. Instead:

**Step 1 — Classify the failure type** (Source: arxiv 2601.16280):
- **Initialization**: tool/import/config not available → fix setup first
- **Parameter**: wrong argument format or value → re-read the API signature
- **Execution**: tool ran but produced wrong output → check the logic, not the call
- **Result-interpretation**: output was correct but you misread it → re-read the raw output

**Step 2 — Recover with the right approach for the category**:
1. List 2–3 hypotheses for the failure, ranked by likelihood
2. Check the most likely hypothesis first (read the error message literally — it usually names the cause)
3. **Failure-conditioned knowledge search**: before guessing a fix, search `autoagent/memory/knowledge.md` for the SPECIFIC function name, test name, or error type from the failure — not just "scan for something relevant." Example: if `test_screen_finviz_merges` fails, search for "finviz" or "screen_finviz" in knowledge.md. A past fix for the exact function is stronger than a generic rule. (Source: SWE-RL arxiv 2502.18449 + failure-conditioned retrieval pattern)
4. Try a different approach if the first hypothesis was wrong
If the failure repeats a second time, stop and write to current_task.md: "BLOCKED: [what failed] — [hypotheses checked]". Then pick a different approach or log it as a known issue.

**When feeding test/tool failure output back into a fix attempt**: Don't just paste the raw error. State: "The specific failing step was [X], it failed because [Y], and the fix should address [Z]." Structured failure articulation surfaces the real cause faster than raw stack traces. (Source: arxiv 2508.11126)

**Diff-level provenance**: When tests fail after a code change, immediately run `git diff` to see exactly what changed. Trace from the specific changed lines to the failing assertion. Never debug from memory — the diff is the authoritative record of what you actually changed vs. what you intended. Treating each test run as independent causes agents to re-introduce previously fixed errors. (Source: arxiv 2508.11126 — diff-level edit provenance pattern)

## LOOP EXIT CONDITIONS
Before entering any refinement loop (e.g. fix-test-retry cycle), define the acceptance criterion:
- "Pass: all tests green" — concrete and measurable
- "Pass: Playwright check returns 0 failures" — concrete and measurable
- "Pass: feature works as described in current_task.md step N" — concrete
If no criterion exists, stop looping after 2 retries and log the blocker to current_task.md instead of looping indefinitely.

**OBSERVER LOOP GUARD** (5-layer loop prevention — ECC v1.9.0): If you observe that you have called the SAME tool with the SAME parameters 3 or more times in this session, STOP immediately. You are in an observer loop — a runaway recursion where each retry produces the same failure. Write to current_task.md: "BLOCKED: observer loop detected — [tool name] called N times with same params. Root cause: [hypothesis]. Escalating to user." Do not retry a 4th time. (Source: affaan-m/everything-claude-code v1.9.0 5-layer observer loop prevention guard, March 2026)

## IF NO RELEVANT SKILL EXISTS
Create `autoagent/skills/[tasktype].md` with rules you discover while working.
Example: if you hit a tricky database migration pattern, write `skills/database.md`.

## AFTER COMPLETING ANY TASK — GATE: DO NOT COMMIT UNTIL BOTH PASS

### STEP 0 — Self-critique + draft reflexion RULE (before running tests)
Re-read the 3 most-changed functions/sections you just wrote. Ask:
1. Does this match what was intended? (compare to current_task.md step description)
2. Is there an obvious edge case I missed?
3. Did I wire all return values through? (model field → route → frontend)
4. **Global consistency check**: Does what I just built invalidate any remaining steps in current_task.md? If yes, update the plan before continuing — a mid-task discovery can make a future step wrong. (Source: PARC arxiv 2512.03549)
5. **Irreversibility check**: Does this session touch any irreversible actions — DB deletes, Stripe charges, Telegram sends, email sends, git pushes? If yes, confirm these were explicitly requested and tested with a mock/guard before going live. Agents consistently underweight the cost of irreversible actions — name them explicitly. (Source: arxiv 2601.02749 — "The Path Ahead for Agentic AI")
6. **API response field removal gate** (if any route file was changed): If you removed a field from any API response dict — for security, cleanup, or refactor — run NOW:
   ```
   grep -rn "field_name" backend/tests/
   ```
   Any test asserting the field IS present will fail. Update those tests in the same commit. **This pattern recurred in sessions 137 AND 141 despite the rule being in knowledge.md — it must fire at write-time, here.** (Source: PolyEdge sessions 137+141 dual failure)
7. **Tier gate addition check** (if you added a tier restriction to any endpoint): grep ALL tests for calls to that endpoint and check if any use the `auth_headers` fixture (free-tier by default) — free-tier tests for that endpoint will now fail with 403. Fix them by upgrading the test user to basic/vip tier. **Session 139: 4 tests failed on first run because of this pattern.** (Source: PolyEdge session 139)
8. **Frontend XSS gate** (if `frontend/index.html` was changed): Run BOTH greps NOW — do not defer to an audit session:
   ```
   grep -n 'innerHTML.*\${' frontend/index.html
   grep -n 'innerHTML\s*=\s*[a-zA-Z_]' frontend/index.html
   ```
   Every match must be verified: API-sourced variables (`name`, `market`, `url`, `message`, `detail`, `outcome`, `title`, `addr`) MUST use `escapeHtml()`. Only safe unescaped: integers, floats, hex wallet addresses. **This step alone has prevented 4 recurring XSS cycles (sessions 59, 67, 73, 79 — all found XSS that should have been caught at write time).** (Source: PolyEdge session 81 META analysis)
Fix anything found BEFORE running tests. This catches a class of bugs that tests miss.
Skip only if: zero files were changed this session.

**IMMEDIATELY after self-critique, write your reflexion RULE into knowledge.md** — do this NOW, before tests, before commit. If the session runs out of context later, the rule is already saved. The full reflexion (ACCOMPLISHED/FAILED/RULE) can be completed in Step 4, but the RULE line must be captured here. Format: `RULE: [2026-MM-DD] [concrete rule learned]`

**Self-check before passing output to the next step**: Before any output that feeds into a subsequent tool call or step, verify:
- Does it match the expected format for the next step?
- Any claims you are uncertain about? If yes, mark with `UNCERTAIN:` and verify before continuing.
- Does it contradict anything established earlier in this session? If yes, resolve the conflict first.

**Tool output validation before chaining**: Before using the result of any tool call as input to the next step, verify it's what you expected — e.g., confirm a file was written by reading it back, confirm a test passed by checking the exit code, confirm a route exists by grepping for it. Never silently chain: "write code" → "run tests" without verifying the write succeeded. One unverified bad output propagates through all subsequent steps and produces confusing failures.

### STEP 0.5 — Multi-disciplinary audit (if `autoagent/skills/audit.md` exists)
Read `autoagent/skills/audit.md` and run every checklist against the files changed this session.
Fix all issues before proceeding. Log anything too large to fix now to `autoagent/memory/tech_debt.md`.
Skip only if: zero files were changed this session.

### STEP 1 — Run tests (ALL session types that touched code)
Run the test command defined in `autoagent/PROJECT.md`.
- If ANY test fails: fix it before proceeding. Never commit red tests.
- Record: count before, count after, status (pass/fail/skip)

### STEP 2 — Run frontend check (WORK sessions only)
Read `autoagent/skills/playwright.md` and follow it exactly.
- If server not running or Playwright not installed: status=skip, note the reason, continue.
- If checks fail: fix the issue before committing. A broken UI ships nothing.
- Record: checks count, failures count, notes

### STEP 2.5 — Emit verification report before committing
After STEP 1 and STEP 2 complete, emit this block explicitly. Do not commit without it:
```
VERIFICATION REPORT:
- Import check: PASS / FAIL
- Tests: PASS (N passed) / FAIL (N failed)
- Frontend: PASS / SKIP (reason) / FAIL
- Audit (Marcus): PASS / FAIL (blocking issue: ...)
READY TO COMMIT: YES / NO
```
This makes the gate state explicit and checkable. A "NO" on any line blocks the commit.
(Source: everything-claude-code verification-loop/SKILL.md)

### STEP 3 — Only after both gates pass, commit and push
Use git commands as configured. For two-repo projects, check `autoagent/PROJECT.md` for repo paths and commit prefixes.

**COMMIT REMINDERS** (re-read at every commit — these rules fade out in long sessions): (Source: arxiv 2603.05344 OPENDEV — instruction fade-out via event-driven reminders)
- ❗ NEVER `git add autoagent/` from project root — it is in .gitignore and will fail
- ❗ Use `py` not `python3` on Windows
- ❗ Project branch is `main`; autoagent branch is `master` — they are different
- ❗ Clear current_task.md IMMEDIATELY after push (not after logging)

1. Add changed project files (never include `autoagent/` in the project repo — it is in .gitignore)
2. Commit with the prefix defined in PROJECT.md (e.g. `agent: <what> — <why>`)
3. Push to the branch defined in PROJECT.md
4. For autoagent changes: commit to the autoagent repo with its own prefix (e.g. `meta: <what>`)
4.5. **Overwrite `autoagent/memory/current_task.md` with `# No current task`** — do this IMMEDIATELY after push, before logging. Skipping this step causes the next session to waste time re-verifying already-committed work.
5. Update `autoagent/memory/backlog.md` — **REMOVE** the completed task entirely (do NOT leave it with [x])
   **CODE REVIEW CROSS-CHECK**: If the task you just completed was a bugfix or security fix, scan the "Code Review" section of the backlog. If any item there specifically tracks the issue you just fixed (e.g., you fixed CORS wildcard → remove "CORS review" item; you removed telegram_chat_id from responses → update "Sensitive data leakage" item), remove or update it now. Work sessions that skip this leave stale code review items that waste the next session re-examining already-fixed code. (Source: Session 137 fixed CORS + telegram_chat_id but left both code review items unchecked.)
   Then append one line to `autoagent/memory/done.md` under today's date:
   `- **[SESSION #N] Task name** — one sentence of what was built`
   Backlog stays lean. done.md is the permanent record.
   **LOW-WATER-MARK CHECK**: After removing the completed task, count remaining HIGH PRIORITY items. If < 2 remain, immediately generate 3+ new testing tasks from the PROJECT.md endpoint table (branch audit approach: pick 3 endpoints and check for uncovered branches). **Before adding each candidate task, grep to confirm no existing test already covers that branch**: `grep -r "def test_<function_keyword>" backend/tests/` — only add if zero matching test functions exist. This prevents wasting turns in the next session discovering the task is already done. (Source: Sessions 53/54/55 each found 1 backlog item already covered — grep-before-adding is the fix. Sessions 6/16/26/36 burned on empty backlog.)

### STEP 4 — Log the session
6. Append to `autoagent/sessions.json` — one entry per session:
   ```json
   {"session": N, "date": "YYYY-MM-DD", "time": "HH:MM", "type": "work|meta|brain",
    "summary": "ONE sentence, plain English, what changed and why it matters to users",
    "files": ["list", "of", "changed", "files"],
    "tests": {"before": N, "after": N, "status": "pass|fail|skip"},
    "frontend": {"status": "pass|fail|skip", "checks": N, "failures": 0, "notes": ""}}
   ```
   Summary must be plain English — e.g. "Added backtesting page so traders can see historical win rates per pattern"
   NOT technical jargon — write it like you're telling a non-developer what changed
7. Write to `autoagent/memory/activity_log.md` — FORMAT IS MANDATORY:
   ```
   ## [DATE TIME] — [TASK TYPE]
   DONE: [what you built in one sentence]
   IMPACT: [why it matters]
   FILES: [files changed]
   ```
   CORRECT EXAMPLE:
   ```
   ## 2026-03-19 14:32 — FEATURE
   DONE: Added earnings proximity chip to signal cards — red "Earn in Xd" badge appears when earnings are within 21 days.
   IMPACT: Traders see the earnings risk at the point of decision instead of getting a mystery score penalty.
   FILES: models/signals.py, routes/dashboard.py, frontend/app.js, frontend/styles.css
   ```
   WRONG (never do this):
   ```
   ## 2026-03-19 14:32 — FEATURE [vscode]
   **Added earnings chip**
   Output tail:
   PASSED 881 tests
   ```
   For error/empty sessions, still write: `DONE: No work completed — [reason]. Next: [next backlog task].`
   Never write "Output tail:" or raw CLI output — that format is unreadable.
8. Write a session reflexion in `autoagent/memory/knowledge.md` under `### Session #N Reflexion — [DATE]`:
   - ACCOMPLISHED: what you built
   - FAILED: what broke or required retry, and why (include WHICH specific decision in the chain caused the failure — not just what failed; this anchors the RULE to the root cause)
   - RULE: one concrete rule learned (even if nothing failed — confirm what worked)
   - OPTIMIZATION: *(optional)* if something worked but was slow/required multiple tries, write one sentence on how to do it faster next time. Use tag `OPTIMIZATION: [2026-MM-DD] [how to skip the slow step]`
   **CRITICAL: APPEND rules, never overwrite existing ones. Each new rule gets a date. Rewriting old rules silently destroys accumulated reasoning — structured incremental updates are the only safe pattern.**
   This is mandatory, not optional. Skipping it loses the learning from every session.
   (Source: arxiv 2603.10600 — Trajectory-Informed Memory Generation: strategy tips from successes + recovery tips from failures + optimization tips from slow-but-successful executions; 14.3pp gain on AppWorld benchmark)
9. Update `autoagent/memory/knowledge.md` test suite history table with new test count
10. Update PROJECT.md Known Facts line `Existing tests: ... — N passing as of session X` to reflect the new count and session number. This line going stale (303 persisted through sessions 112–115) causes confusion at next session's baseline health check.

## CONFIG / IMPORT RULES
- Before referencing any config variable (e.g. `cfg_live`, `settings.X`), grep for its definition in the codebase
- If you add a variable that doesn't exist yet, also add it to `config.py` with a default value
- Never assume a name is defined — always verify with grep first

## API KEY PROTOCOL
If a feature needs an API key that isn't set:
1. Implement it anyway using `os.getenv("KEY_NAME")`
2. **MANDATORY: update `autoagent/KEYS_NEEDED.md`** — add a row to the table:
   `| Service | KEY_NAME | ❌ | where to get it | what it unlocks |`
3. **MANDATORY: add a line to `sessions.json` notes field** — e.g. `"notes": "Needs NEW_API_KEY to activate this feature"`
4. Never stop or ask. User fills it in, feature activates automatically.

This applies to EVERY new key. If you built it and it needs a key, the user must be able to see it in KEYS_NEEDED.md immediately.

## IF YOU ARE STOPPED MID-SESSION
If you start a session and current_task.md has unchecked steps:
- Those steps are from a previous interrupted session
- Continue from the first unchecked step — don't start over
- The codebase may have partial work already — check with `git diff` first

## IF CURRENT TASK APPEARS ALREADY DONE
If current_task.md has steps but all work looks complete (tests pass, code is committed):
1. Verify with `git log --oneline -5` that the work was actually committed
2. Clear current_task.md (overwrite with `# No current task`)
3. IMMEDIATELY pick the next unchecked task from backlog.md — do NOT exit or log "no action needed"
4. Never spend a session just confirming something was already done — that wastes a full context window

**ZERO TOLERANCE FOR EMPTY SESSIONS**: If you find the current task is already done, you MUST pick and START the next task in the same session. "No action needed" is never a valid session outcome. The session ends when new code is committed or a concrete investigation is logged.

## WHAT "DONE" MEANS
A task is done when ALL of the following are true — in this order:
1. Feature works as intended
2. Tests pass (run the test command from `autoagent/PROJECT.md`) — exits 0
3. Frontend check run (or skipped with documented reason) — BEFORE commit
4. Code is committed and pushed
5. sessions.json updated with test + frontend results
6. activity_log.md updated
7. current_task.md cleared (overwrite with `# No current task`)

**COMMIT ORDER IS MANDATORY: tests → frontend → commit. Never commit then check.**
