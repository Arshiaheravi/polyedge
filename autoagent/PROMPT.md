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
3. If no current task, read `autoagent/memory/backlog.md` — pick the highest value unchecked task that you can complete autonomously. **Skip tasks marked "Seb action", "blocked on external input", or "FEATURE MODE ONLY"** — the first two require human action, the last requires feature mode. Pick the next autonomous task instead. Never start a session on a task you can't finish without human input.
   **PERIODIC TECH-DEBT CHECK** (De-Sloppify pattern): Check `autoagent/sessions.json` — count sessions where `type == "work"`. If that count is a multiple of 5 (e.g. 5, 10, 15, 20, ...), add a META task to the backlog first: "Code quality audit — scan last 5 work sessions' changed files for cross-file coupling, test specificity degradation, and smells introduced by agent edits." Then continue picking tasks as normal. This prevents technical debt accumulation that stalls velocity after 4-6 weeks. (Source: arxiv 2511.04427 — MSR 2026 empirical study on agentic code quality degradation)
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
Fix anything found BEFORE running tests. This catches a class of bugs that tests miss.
Skip only if: zero Python code was changed this session.

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
   Then append one line to `autoagent/memory/done.md` under today's date:
   `- **[SESSION #N] Task name** — one sentence of what was built`
   Backlog stays lean. done.md is the permanent record.

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
   - FAILED: what broke or required retry, and why
   - RULE: one concrete rule learned (even if nothing failed — confirm what worked)
   **CRITICAL: APPEND rules, never overwrite existing ones. Each new rule gets a date. Rewriting old rules silently destroys accumulated reasoning — structured incremental updates are the only safe pattern.**
   This is mandatory, not optional. Skipping it loses the learning from every session.
9. Update `autoagent/memory/knowledge.md` test suite history table with new test count

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
