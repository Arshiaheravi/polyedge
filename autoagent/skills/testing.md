# Skill: Testing

## RULES
- Write tests ALONGSIDE the feature — not after
- One test per branch (if/elif/else) minimum — penalty branches (-5, -10 pts) are most dangerous
- Run `py -m pytest tests/ --collect-only -q` first — catches import errors before full run
- Test command: `py -m pytest tests/ -q --ignore=tests/test_e2e.py`

## TEST-FIRST SPECIFICATION (evals-as-specs pattern)
Before writing any feature code, write out in plain English what the tests will verify:
```
# Tests for [feature]:
# 1. returns X when input is Y (happy path)
# 2. returns Z when edge case W occurs
# 3. does NOT return P when guard condition Q is false
```
This takes 60 seconds and catches scope drift before you write a line of production code.
The test list becomes the acceptance criteria — if all 3 pass, the feature is done.
This matters because: agents tend to implement the first interpretation of a task, not the correct one.
Writing tests first forces you to clarify intent before you lock it in code.

## PATCHING — MOST COMMON SOURCE OF FAILURES
- ALWAYS patch at the namespace where the name is looked up
- If route does `from stockcards.services.X import func` → patch `stockcards.routes.routefile.func`
- NOT `stockcards.services.X.func` — that's the wrong binding
- Patch the guard function, not the third-party symbol
  - CORRECT: patch `_get_resend_module`
  - WRONG: patch `resend.Emails.send`

### Intra-function imports (APPLIES TO SCHEDULER/SERVICE, NOT JUST ROUTES)
When ANY function (route, service, scheduler, job) uses `from module import func` INSIDE the function body:
- The import runs at call time, looking up `func` from `module` directly
- The calling module (e.g. `scheduler.py`) NEVER holds a reference to `func`
- CORRECT: patch `stockcards.services.email_service.send_welcome_email_2`
- WRONG: patch `stockcards.services.scheduler.send_welcome_email_2` (doesn't exist)
- Rule: trace the import statement to its origin module, patch there

### Float formatting in test assertions
- `:.0f` uses banker's rounding in Python: 112.51 → "113", not "112"
- NEVER assert `"112"` in subject when the value is `112.51` and format is `:.0f`
- CORRECT: assert `"113"` in subject, or use `str(round(112.51))` to compute expected
- Safer: assert a substring that doesn't depend on rounding (e.g. `"track record"` instead of specific number)

## E2E TESTS
- Guard with `pytest.importorskip("selenium")` — missing selenium crashes entire collection
- E2E tests live in `tests/test_e2e.py` — always ignore with `--ignore=tests/test_e2e.py`

## TEST STRUCTURE — FROM ECC TDD SKILL
- **One assert per test**: Each test verifies exactly one behavior. Multiple asserts hide which one failed.
- **Arrange-Act-Assert (AAA)**: Set up → call the function → assert output. One blank line between sections.
- **Independent tests**: No test shares mutable state with another. Each test creates its own fixtures.
- **Test user-visible behavior, not implementation details**: Assert what a function returns, not which internal method it calls.

## VERIFICATION CONTRACT — state before coding (from research 2025)
Before writing ANY feature code, state the full verification criteria:
```
# Verifying [feature]:
# 1. curl http://localhost:8000/api/endpoint → includes new_field in response
# 2. py -m pytest tests/test_X.py::test_new_feature → passes
# 3. frontend renders correctly (Playwright check if UI changed)
```
Feature is done when ALL criteria pass — not when the code looks correct.
Provide expected outputs upfront: concrete values, not vague descriptions.

## END-TO-END VERIFICATION (not just unit tests)
After unit tests pass, verify as a real user would:
```bash
# Start backend, hit the actual endpoint
curl -s http://localhost:8000/api/dashboard?market=CA | python -m json.tool | grep new_field
```
Unit tests passing ≠ feature working. Always verify the full flow at least once.

## BRITTLE TEST PATTERNS — AVOID THESE

### Hard-coded iteration counts in mocks
- When you add a new pass/iteration to a loop, tests that assert `mock.call_count == N` fail immediately
- WRONG: `assert mock_fetch.call_count == 2`
- CORRECT: `assert mock_fetch.call_count == 3` (update when adding a pass) OR better: `assert mock_fetch.called` (count-agnostic)
- Before adding a new loop pass: `grep -r "call_count ==" tests/` to find all assertions that hard-code the old count. Update BOTH the assertion value AND the test name to reflect the new expectation.

### Fake/stub signal objects missing new fields
- When adding a new field to `StockSignal`, `PatternSnapshot`, or any model, ALSO add it to ALL fake/stub objects in test files
- Pattern: `grep -r "FakeSignal\|StubSignal\|_FakeSignal\|MockSignal" tests/` to find all stubs
- A missing attribute on a stub is often silently swallowed by `except` blocks in services, producing 0 rows instead of an error — very hard to debug
- Add the new field (with a safe default like `""` or `0`) to every stub found

## WHAT "TESTS PASS" MEANS
- Zero failures in `tests/` (excluding test_e2e.py)
- No collection errors
- Same or higher test count than before your change
- Never commit if count drops — investigate why

## IMPORT CHECK BEFORE TESTS
`py -c "from src.stockcards.app import create_app; print('OK')"`
If this fails, fix imports first — pytest will fail on collection.
