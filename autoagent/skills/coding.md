# Skill: Coding

## BEFORE WRITING ANY CODE — EVIDENCE FIRST
- Run `git diff` — check if there's in-progress work to finish first
- Check `autoagent/memory/knowledge.md` for existing patterns
- **Read the file you're about to change before touching it** — never modify code you haven't read
- Find the existing pattern for what you're building and follow it exactly
- If current_task.md has unchecked steps, continue those — don't restart

## MINIMAL CHANGE PRINCIPLE
Make the smallest change that solves the problem. Before every edit ask:
- "Does this file actually need to change, or just the one I'm already editing?"
- "Is this logic already somewhere else I can call instead of duplicate?"
- "Am I adding an abstraction for ONE use case?" → don't, just write the code
Over-engineering is the #1 agent failure mode. 3 lines that work > 30 that are "cleaner".

## PYTHON BACKEND PATTERNS
- New route: create in `src/stockcards/routes/`, register in `src/stockcards/app.py`
- New service: create in `src/stockcards/services/`, import in the route
- New model field: add to `src/stockcards/models/signals.py`, wire through route + frontend
- Admin endpoints: use `_require_admin` dependency (see `routes/admin.py`)
- Pure functions only in `services/analysis.py` — no I/O, no HTTP, no yfinance
- Python command: `py` (not python, not python3)

## FRONTEND PATTERNS
- All JS in `frontend/app.js` — no separate files
- All CSS in `frontend/styles.css` — no separate files
- Dark theme, no emojis except flag emojis (🇺🇸 🇨🇦)
- Ticker display: never add `.TO` suffix — backend handles it
- API base: `http://localhost:8000`

## DICT KEY CONTRACT — CHECK ALL 3 LAYERS
When a function returns a dict with new keys:
1. Route passes ALL keys to model constructor
2. Model has fields for all keys
3. Frontend uses same key names
Missing any layer = silent bug

## 8-STEP WIRING CHAIN (scoring features)
When adding a new scoring dimension, check all 8 layers — missing any produces wrong scores or missing chips with NO error message:
1. Pure function in `services/analysis.py` (no I/O)
2. Call it in `routes/dashboard.py` with the price data
3. Pass result as parameter to `signals.generate_signal()`
4. Add parameter to `generate_signal()` signature
5. Add scoring logic inside `generate_signal()`
6. Add to `score_breakdown` dict in `dashboard.py`
7. Pass to `StockSignal()` constructor
8. Add field to `StockSignal` model + frontend badge

## EXTERNAL API ERROR HANDLING PATTERNS

**Alpaca Trading API** — wrap order submission in exponential backoff:
- Retry on 503/504: `time.sleep(2**attempt)` up to 3 attempts
- Re-raise immediately on 401/403: auth errors are not retryable, stop and alert
- Always call `get_open_position(ticker)` before any sell order to avoid position-not-found errors
- Use `alpaca-py` SDK (not deprecated `alpaca-trade-api`) — Pydantic-first, cleaner error messages

**Production startup** — use Gunicorn + Uvicorn workers instead of raw `uvicorn`:
```
gunicorn -k uvicorn.workers.UvicornWorker -w 4 src.stockcards.app:create_app --factory --port 8000
```
This adds process-level fault isolation and CPU parallelism — critical for concurrent screener calls.

## FASTAPI STARTUP/SHUTDOWN — USE LIFESPAN, NOT @app.on_event
`@app.on_event("startup")` / `@app.on_event("shutdown")` are deprecated since FastAPI 0.103+. Use `lifespan`:
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: warm cache, init connections
    await cache.connect()
    yield
    # shutdown: flush and close
    await cache.disconnect()

app = FastAPI(lifespan=lifespan)
```
In StockCards this slots into `create_app()` — pass `lifespan=lifespan` to the FastAPI constructor.

## AFTER WRITING CODE
- Import check: `py -c "from src.stockcards.app import create_app; print('OK')"`
- Run tests: `py -m pytest tests/ -q --ignore=tests/test_e2e.py`
- Fix ALL failures — never commit red
