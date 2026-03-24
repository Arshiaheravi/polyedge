# Skill: Agent Patterns (Autonomous Coding Best Practices)

**When to use**: Every session. These are the meta-rules that prevent the most common
autonomous agent failure modes. Read this alongside task-specific skills.

---

## FAILURE MODES — know these, avoid them

### 1. Kitchen Sink (most common)
**Symptom**: Start task A → get distracted by issue B → lose thread of A
**Fix**: One task per session. If you notice something unrelated, add it to backlog and stay on task.

### 2. Infinite Exploration
**Symptom**: `"investigate the screener"` → reads 50 files → context full → no code written
**Fix**: Scope narrowly before exploring.
- Bad: `"investigate the screener system"`
- Good: `"read screener.py lines 40-80 to understand how CA tickers are filtered"`

### 3. Symptom Suppression
**Symptom**: Build fails → add `try/except` to hide error → problem returns later
**Fix**: Always fix the root cause. If you don't understand why it's failing, read the error more carefully before touching code.

### 4. Correction Loop
**Symptom**: Make a change → wrong → fix → still wrong → fix again → 3rd attempt
**Fix**: After 2 failed attempts at the same problem, stop. Re-read the relevant source files from scratch. The assumption you're working from is wrong.

### 5. Trust Without Verify
**Symptom**: Write code → looks right → mark task done → bug found next session
**Fix**: After every feature, explicitly verify: run tests, do import check, check the affected API endpoint with curl.

### 6. Over-Implementation
**Symptom**: Task says "add a field" → agent adds field + refactors the whole model + adds new tests + cleans up unrelated code
**Fix**: Do exactly what the task says. Nothing more. Log any improvements you notice to backlog instead.

### 7. Brittle Test Cascade
**Symptom**: Add a 3rd pass to a screener → 3 existing tests assert `call_count == 2` → all fail → took 2 retries to find root cause
**Fix**: Before adding any loop iteration or list element, run `grep -r "call_count\|assert.*==.*[0-9]" tests/` to find hard-coded counts. Update them preemptively. Also grep for fake/stub objects (`FakeSignal`, `StubSignal`, `MockSignal`) when adding model fields — they won't have the new attribute and service `except` blocks may silently swallow the error.

---

## PLANNING — use before multi-file changes

Before touching code on any task that changes 3+ files:
1. Write a plan in `autoagent/memory/current_task.md` FIRST
2. List: which files change, what changes in each, what tests verify it
3. Ask yourself: "Is there a simpler way that changes fewer files?"

Example plan:
```
# Current Task: Add sector bonus chip to signal card
Files changing:
- services/signals.py — add sector_bonus param
- routes/dashboard.py — calculate and pass sector_bonus
- models/signals.py — add sector_bonus field
- frontend/app.js — render chip if sector_bonus > 0
Tests:
- test_signals.py — sector bonus adds to score
- test_routes.py — sector_bonus in response
```

---

## VERIFICATION CONTRACT — specify before coding

Before writing any feature code, state the verification criteria:
```
# Verifying [feature]:
# 1. curl http://localhost:8000/api/signals → includes sector_bonus field
# 2. py -m pytest tests/test_signals.py::test_sector_bonus → passes
# 3. frontend shows green chip when sector_bonus > 2
```
These become the acceptance criteria. Feature is done when all 3 pass — not when code looks right.

---

## CONTEXT MANAGEMENT

- When you've read many files and the session is long: emit a `CONTEXT_SUMMARY` block (see PROMPT.md) before continuing
- Prioritize reading: current_task.md → relevant service file → relevant test file. Don't read files speculatively.
- If you need to investigate something unrelated to the task, add it to backlog — don't explore now

---

## SELF-CRITIQUE — run before every commit

After finishing an implementation but BEFORE running tests, re-read the 3 most-changed functions and ask:
1. Does this match what the task required? (compare to current_task.md)
2. Is there an obvious edge case missing? (empty list, None, zero, negative number)
3. Did I change anything I wasn't supposed to? (check git diff for unintended changes)

This 2-minute check catches ~20% of bugs before tests run.

---

## REFERENCE EXISTING PATTERNS

Before writing new code, find the existing pattern:
```bash
# Find how existing similar features are built
grep -r "similar_function" src/stockcards/routes/
```
Then follow that pattern exactly. Consistency beats cleverness.
