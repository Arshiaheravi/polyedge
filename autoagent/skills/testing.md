# Skill: Testing

## RULES
- Write tests ALONGSIDE the feature — not after
- One test per branch (if/elif/else) minimum — penalty branches (-5, -10 pts) are most dangerous
- Run `py -m pytest tests/ --collect-only -q` first — catches import errors before full run
- Test command: `py -m pytest tests/ -q --ignore=tests/test_e2e.py`
- **When testing error paths, verify the expected HTTP status code against PROJECT.md spec — NOT current code.** Write the test to match the spec, then fix the code if they diverge. Tests written to match code (not spec) lock in wrong behavior silently. (Session 45: duplicate email register was 400 in code but 409 in spec — test masked it for 45 sessions.)

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
- If route does `from app.services.polymarket import get_leaderboard` → patch `app.routes.bettors.get_leaderboard`
- NOT `app.services.polymarket.get_leaderboard` — that's the wrong binding
- Patch the function at the callsite, not the source module
  - CORRECT: `patch("app.routes.bettors.get_leaderboard", new_callable=AsyncMock)`
  - WRONG: `patch("app.services.polymarket.get_leaderboard", ...)`

### Intra-function imports (APPLIES TO SCHEDULER/SERVICE, NOT JUST ROUTES)
When ANY function (route, service, scheduler, job) uses `from module import func` INSIDE the function body:
- The import runs at call time, looking up `func` from `module` directly
- The calling module (e.g. `scheduler.py`) NEVER holds a reference to `func`
- CORRECT: patch `app.services.notifications.send_telegram`
- WRONG: patch `app.services.scheduler.send_telegram` (doesn't exist there)
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

### Tier gate additions break free-tier tests
- `auth_headers` fixture creates a free-tier user by default
- Adding a tier restriction (403 for free) to any endpoint breaks ALL existing tests for that endpoint that use `auth_headers`
- **Before adding any tier gate**: `grep -rn "def test_.*<endpoint_keyword>" backend/tests/` — check which tests use `auth_headers` (free tier) on that endpoint
- Fix by upgrading the test user: `db_user.subscription_tier = "basic"; db.commit()` before the endpoint call
- (Session 139: 4 tests failed on first run because of this pattern)

### Fake/stub signal objects missing new fields
- When adding a new field to `StockSignal`, `PatternSnapshot`, or any model, ALSO add it to ALL fake/stub objects in test files
- Pattern: `grep -r "FakeSignal\|StubSignal\|_FakeSignal\|MockSignal" tests/` to find all stubs
- A missing attribute on a stub is often silently swallowed by `except` blocks in services, producing 0 rows instead of an error — very hard to debug
- Add the new field (with a safe default like `""` or `0`) to every stub found

## BEFORE ADDING ANY TEST — CHECK FOR EXISTING TEST FILES

**Run this BEFORE adding tests to any file**:
```bash
ls backend/tests/
grep -r "def test_" backend/tests/ | grep "<endpoint_keyword>"
```
Rules:
- If a dedicated file exists for the endpoint (e.g. `test_follows_live.py` for `/follows/live`), add tests THERE — not in `test_follows.py` or generic files.
- If similar test names appear in OTHER files, you likely have a duplicate — don't add another.
- `grep -r "def test_<function>" backend/tests/` before writing any new test function.

(Session 45 audited session 42: 2 `/follows/live` tests added to `test_follows.py` when `test_follows_live.py` already had comprehensive coverage. Took a full META session to find and remove them.)

## BRANCH AUDIT WORKFLOW — how to find coverage gaps systematically

When the backlog is empty, use this audit loop to find 5+ gaps in ~10 minutes:

1. **Pick one service file** (e.g. `polymarket.py`, `notifications.py`, `stripe_service.py`)
2. **List every if/elif/else branch** in each function — count the branches
3. **Grep existing tests** for that function name: `grep -r "function_name" tests/`
4. **For each branch without a test, write one** — the branch is the test name
5. Repeat for routes files after services

**Checklist per function** (from sessions 22-25 — these reliably surface 3-5 gaps):
- [ ] Multi-branch conditional (if A / elif B / else)? → one test per branch
- [ ] `isinstance` guard (if not isinstance(x, list))? → test the non-list path
- [ ] Cache hit path? → second call test returning `cached=True`
- [ ] Empty-collection return? → test with empty input
- [ ] Exception handler? → mock the exception, assert the error status code
- [ ] Each HTTP method (GET/POST/PUT/DELETE) has a no-auth test?
- [ ] All 3 tiers (free/basic/VIP) tested for any tier-gated response field?
- [ ] All webhook event status strings (canceled, past_due, unpaid, active) have a test?

**SYMMETRY AUDIT RULE** (from session #39-40 pattern): When a coverage gap is found in function A of module M, immediately apply the same audit to all analogous functions in M. Example: `send_telegram` had a missing True-return path → check `send_sms` and `send_web_push` for the same gap → they had it too. Testing one does NOT cover the others. After finding any gap type, scan the full module for the same pattern before moving on.

## POLYEDGE-SPECIFIC PATTERNS (read before writing any PolyEdge tests)

### Module-level cache isolation
`bettors.py` and `follows.py` have module-level cache dicts (`_leaderboard_cache`, `_trades_cache`, `_profile_cache`) that persist across tests in the same pytest session. If you test an error path AFTER a success path, the cache serves the success response and your mock is never called.

**Fix**: At the start of any test that exercises an uncached code path, reset the cache directly:
```python
import app.routes.bettors as bettors_mod
bettors_mod._trades_cache = {"data": None, "ts": 0}
bettors_mod._profile_cache.clear()
bettors_mod._leaderboard_cache = {"data": None, "ts": 0}
```
Or use a unique query-param combo not seen by earlier tests (e.g. `time_period=day` instead of `month`).

### Module-level settings monkeypatching
`alerts.py` (and similar files) do `settings = get_settings()` at module import time — the `settings` object is bound once and never re-fetched. `monkeypatch.setattr` on `get_settings` won't work. Patch the attribute directly on the already-bound object:
```python
import app.routes.alerts as alerts_mod
original = alerts_mod.settings.twilio_account_sid
try:
    alerts_mod.settings.twilio_account_sid = "ACtest"
    # ... test body ...
finally:
    alerts_mod.settings.twilio_account_sid = original
```

### Admin endpoint tests — always use get_settings().admin_password
NEVER hardcode `"admin"` as the admin password in tests. The `.env` file overrides the config default, and the test environment loads `.env`.
```python
# WRONG — hardcodes the default, breaks when .env sets a different value
headers={"x-admin-password": "admin"}

# CORRECT
from app.config import get_settings
headers={"x-admin-password": get_settings().admin_password}
```
(Session 146: test_admin_stats_response_has_no_sensitive_fields failed first run because of this exact mistake.)

### Stale mocks when replacing HTTP implementation
When you replace one HTTP library with another (e.g., raw `httpx.AsyncClient` → `pywebpush`), tests that mock the OLD library path break immediately — they mock something that is no longer called.

**Before** replacing any service function's HTTP transport, run:
```bash
grep -n "patch.*httpx\|mock.*httpx\|AsyncMock.*client" backend/tests/
```
Every match that previously asserted `True` (success path) must be updated to mock the NEW library. Tests that assert `False` (early-exit guards) usually survive because the guard fires before the replaced code.
(Session 145: 2 tests broke because they mocked `httpx.AsyncClient` after pywebpush replaced it.)

### PolyEdge test command
```
cd backend && py -m pytest tests/ -v
```
(Use `-v` not `-q` for this project — matches PROJECT.md and gives clearer failure output.)

## PROPERTY-BASED TESTING (Hypothesis) — for invariant coverage

When a route or function has a clear invariant that must hold for ALL valid inputs, write a property-based test using `hypothesis` instead of (or in addition to) example-based tests. This generates adversarial inputs automatically and catches edge cases that examples miss.

**When to use**: Routes with hard business-rule invariants — auth, tier limits, input validation.

**PolyEdge invariants ideal for Hypothesis**:
- `GET /follows` always returns tier + limit fields regardless of input
- `POST /follows` never exceeds TIER_LIMITS for any valid user
- `GET /bettors` always returns a `cached` bool field
- Any protected endpoint always returns 401 when Authorization header is missing

**Pattern**:
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1))  # adversarial address strings
def test_bettor_address_never_crashes_server(client, address):
    resp = client.get(f"/bettors/{address}")
    assert resp.status_code in (200, 404, 502)  # never 500
    assert "detail" in resp.json() or "bets" in resp.json()
```

**Install**: `pip install hypothesis` (add to requirements.txt if using).
(Source: dasroot.net Python Agent Testing Best Practices 2026 — 72% of deployed agents show non-deterministic behavior; invariant testing is more reliable than example-based for coverage of auth and validation paths.)

## WHAT "TESTS PASS" MEANS
- Zero failures in `tests/` (excluding test_e2e.py)
- No collection errors
- Same or higher test count than before your change
- Never commit if count drops — investigate why

## PARAMETRIZE BEST PRACTICES

When writing parametrized tests with `@pytest.mark.parametrize`, always use `pytest.param()` with named IDs for readable failure output:

```python
# WRONG — auto-generated IDs like [tier0-1] are unreadable in failure output
@pytest.mark.parametrize("tier,limit", [("free", 1), ("basic", 5), ("vip", 999999)])

# CORRECT — named IDs show "FAILED test_follows[tier_free]" not "FAILED test_follows[0]"
@pytest.mark.parametrize("tier,limit", [
    pytest.param("free", 1, id="tier_free"),
    pytest.param("basic", 5, id="tier_basic"),
    pytest.param("vip", 999999, id="tier_vip"),
])
```

Named IDs immediately pinpoint WHICH parameter set failed without reading the parameter values from the test name.
(Source: rednafi.com pytest.param best practices 2026 — confirmed on PolyEdge tier tests)

### Advanced: dict-based parametrize (cleaner for multi-field cases)
Pack all inputs and expected value into a dict. Avoids positional fragility when adding fields:
```python
@pytest.mark.parametrize("case", [
    pytest.param({"tier": "free",  "endpoint": "/follows", "expected": 200}, id="free-follows"),
    pytest.param({"tier": "basic", "endpoint": "/follows", "expected": 200}, id="basic-follows"),
    pytest.param({"tier": "free",  "endpoint": "/markets/consensus", "expected": 200}, id="free-consensus"),
])
def test_tier_access(case, client, auth_headers_for_tier):
    headers = auth_headers_for_tier(case["tier"])
    resp = client.get(case["endpoint"], headers=headers)
    assert resp.status_code == case["expected"]
```

### Advanced: inline xfail/skip inside parametrize (co-locate skip logic with data)
```python
@pytest.mark.parametrize("token", [
    pytest.param("valid_token", id="valid"),
    pytest.param("expired", id="expired",
                 marks=pytest.mark.xfail(reason="expiry check not wired yet")),
])
def test_auth(token): ...
```

## MUTATION TESTING — find test gaps that code coverage misses

Code coverage tells you which lines ran; mutation testing tells you whether your tests would catch a real bug.
A "surviving mutant" = a code change that didn't break any test = a test gap.

**When to run**: After a burst of new test-writing sessions (e.g. sessions 164-172), when you want to verify the test suite actually enforces the business logic, not just executes the code.

**Install**:
```bash
cd backend && py -m pip install mutmut
```

**Run**:
```bash
cd backend && py -m mutmut run --paths-to-mutate "app/" --tests-dir "tests/"
```

**View surviving mutants** (test gaps):
```bash
py -m mutmut results                 # shows killed/survived counts
py -m mutmut show <mutant_id>        # shows the specific code change that survived
py -m mutmut show --all-survived     # shows ALL surviving mutants = your test gap list
```

**What to do with survivors**:
Each surviving mutant points to a code branch or comparison that no test asserts on.
Write a test that would kill it, then re-run mutmut to confirm mutation score increased.

**Target mutation score**: > 70% killed = strong test suite. < 50% = significant gaps.

**PolyEdge scope** (narrows runtime from hours to minutes):
```bash
# Focus on business-critical files only
py -m mutmut run --paths-to-mutate "app/services/polymarket.py" --tests-dir "tests/"
py -m mutmut run --paths-to-mutate "app/routes/bettors.py" --tests-dir "tests/"
```

**Caveat**: Mutation testing is slow on large codebases (~5-20 min for PolyEdge's app/).
Use it as a periodic audit tool (every 20 sessions or when a file has 0 surviving mutants as a milestone), not in every session's test gate.

(Source: mutmut v2.5+ Python mutation testing — 25% more logical bugs caught vs coverage-only testing; pytest-gremlins alternative uses coverage-guided selection for 10-100x fewer test runs)

### Advanced: `itertools.product` for tier × endpoint matrix (PolyEdge use case)
```python
import itertools
TIERS = ["free", "basic", "vip"]
ENDPOINTS = ["/follows", "/alerts/settings", "/markets/consensus"]

@pytest.mark.parametrize("tier,endpoint", list(itertools.product(TIERS, ENDPOINTS)))
def test_no_500(tier, endpoint, client):
    resp = client.get(endpoint, headers=auth_headers_for(tier))
    assert resp.status_code != 500
```
Generates 9 cases automatically (3 tiers × 3 endpoints). Add a new endpoint → 3 new cases with 1 line.

(Source: fiddler.ai Advanced Pytest Patterns 2026; mergify.com pytest.param guide 2026)

## IMPORT CHECK BEFORE TESTS
```bash
cd backend && py -c "from app.main import app; print('OK')"
```
If this fails, fix imports first — pytest will fail on collection.
