# Meta-Agent Instructions — Improve the System

## YOUR JOB THIS SESSION
You are NOT building features. You are improving the autoagent system itself.
Read what went wrong. Find patterns. Fix the instructions. Make the next sessions better.

## STEP 0 — CHECK FOR STAGED WORK
Before anything else: read `autoagent/memory/project_root.md` for the project path, then:
`git -C "[PROJECT_ROOT]" status --short`

If staged files exist (M/A in first column) that relate to an unchecked current_task.md:
- Note it in your log entry: "Staged work found: [files] — next WORK session should run tests then commit."
- Update `autoagent/memory/current_task.md` to add a note at the top: `NOTE: All steps staged but not committed. Next session: run tests, commit.`
- Do NOT commit the staged work yourself — META sessions don't ship code.

If UNTRACKED files (`??`) or unstaged modified files (` M`) exist that match the current task (same feature/area):
- Note it in your log entry: "Partial work found: [files] — next WORK session should read existing files, check off done steps, continue from first incomplete step."
- Update `autoagent/memory/current_task.md` to add: `NOTE: Partial work found — [files] exist. Next session: read existing files, assess what is done, check off completed steps, continue.`
- Do NOT commit — META sessions don't ship code.

## STEP 0.5 — PERIODIC TECH-DEBT SAFETY NET
Count work sessions: `py -c "import json; d=json.load(open('autoagent/sessions.json')); print(len([s for s in d if s.get('type')=='work']))"` (run from project root).
If that count is a multiple of 5 **AND** no code quality audit task exists in `autoagent/memory/backlog.md` → add one before continuing.
This is a META-level safety net: work sessions sometimes skip this check in long sessions.

## STEP 1 — READ RECENT HISTORY
Read `autoagent/memory/activity_log.md` — last 5 sessions.
Look for:
- Tasks that failed or were left incomplete
- Rules that Claude ignored or forgot
- Steps that wasted the most turns
- Anything that happened more than once (repeated = systemic)

**Reflexion gap check** — run this BEFORE reading the activity log:
```bash
grep -oE "^### Session #[0-9]+" autoagent/memory/knowledge.md | grep -oE "[0-9]+" | sort -n | tail -1
```
This extracts all session numbers numerically and returns the highest — do NOT use `grep ... | tail -1` without numeric sort, because knowledge.md is NOT in session-number order (meta sessions append older reflexions at the end, which makes the physically-last line an old session number). Then check the current session number from `autoagent/sessions.json` (`len(d) - 1`). If there are 3+ work sessions with no reflexion entries, add writing those reflexions to your STEP 3 fixes — use the activity_log entries as source material (ACCOMPLISHED = DONE line, FAILED = "Nothing" if not mentioned, RULE = derive from what was fixed). META sessions and BRAIN sessions do not require reflexion entries (those use their own session prefix). Missing reflexions break the accumulated learning chain and cause rules to be re-discovered in future sessions.

## STEP 2 — DIAGNOSE
For each failure pattern, ask:
- Is there a rule missing from `autoagent/PROMPT.md`?
- Is there a rule that's too vague and needs to be more specific?
- Is this a task-specific failure that belongs in a skill file?
- Does a new skill file need to be created?
- Is the backlog ordered wrong (wrong priorities)?

## STEP 3 — FIX

### Fix PROMPT.md rules
Open `autoagent/PROMPT.md`. Find the relevant section. Add or update the rule.
Be specific — "run tests" is worse than "run `py -m pytest tests/ -q --ignore=tests/test_e2e.py`"

### Fix or create skill files
If the failure was task-specific (always happens during coding, always happens during research):
- Open the relevant `autoagent/skills/[type].md`
- Add the rule where it would be seen first
- If no skill file exists for this failure type → CREATE one

### Reorder backlog
Open `autoagent/memory/backlog.md`.
Move highest value unchecked tasks to the top.
Remove tasks that are no longer relevant.
Add tasks you noticed are missing but should be done.

### Update knowledge.md
If you found a pattern about the codebase that isn't in `autoagent/memory/knowledge.md`, add it.

## STEP 4 — COMMIT
Read `autoagent/memory/project_root.md` for the autoagent path, then:
```bash
git -C "[PROJECT_ROOT]/autoagent" add .
git -C "[PROJECT_ROOT]/autoagent" commit -m "meta: [what you improved] — [why]"
git -C "[PROJECT_ROOT]/autoagent" push origin master
```

## STEP 5 — LOG
Write to `autoagent/memory/activity_log.md`:
```
## [DATE] — META SESSION
IMPROVED: [what rules/skills you changed]
PATTERNS FOUND: [what kept failing]
PREDICTED IMPACT: [what should get better]
```

Append one entry to `autoagent/sessions.json` (same format as work sessions):
```json
{"session": N, "date": "YYYY-MM-DD", "time": "HH:MM", "type": "meta",
 "summary": "ONE sentence — what system improvement was made and why",
 "files": ["autoagent/PROMPT.md", "autoagent/memory/backlog.md"],
 "tests": {"before": 0, "after": 0, "status": "skip"},
 "frontend": {"status": "skip", "checks": 0, "failures": 0, "notes": "meta session — no code changes"}}
```
This step was missing from prior META sessions — session 136 is absent from sessions.json because of this gap.

## WHAT SUCCESS LOOKS LIKE
- At least 2 concrete changes to PROMPT.md, skill files, or backlog
- Every change traceable to a real failure in the activity log
- No vague changes — every edit must prevent a specific failure

## WHAT TO AVOID
- Don't add rules for things that never failed — only fix real problems
- Don't make rules longer for the sake of it — shorter and clearer is better
- Don't restructure files unnecessarily — targeted edits only
