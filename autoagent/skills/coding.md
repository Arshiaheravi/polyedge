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

## PYTHON BACKEND PATTERNS (PolyEdge)
- New route: create in `backend/app/routes/`, register in `backend/app/main.py` with `app.include_router()`
- New service: create in `backend/app/services/`, import in the route
- New model field: add to `backend/app/models.py`, wire through route + frontend
- Admin endpoints: use `x-admin-password` header check (see `routes/admin.py`)
- External API calls: ONLY in `services/` layer — routes must never call Polymarket/Stripe/Telegram directly
- Python command: `py` (not python, not python3)
- Backend port: **8002** — never 8001 or 8000

## FRONTEND PATTERNS (PolyEdge)
- All JS and CSS in `frontend/index.html` — single-file SPA, no separate app.js/styles.css
- Dark theme, no emojis in UI text (use inline SVGs instead)
- API base: `http://localhost:8002`
- JWT token: stored in `localStorage` as `pe_token`
- Global state variables: `_bettorCache` (Map), `_disclosureCache` (Map), `alertSettings` (object)

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
gunicorn -k uvicorn.workers.UvicornWorker -w 4 app.main:app --port 8002
```
This adds process-level fault isolation and CPU parallelism — critical for concurrent API calls.

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
In PolyEdge this slots into `backend/app/main.py` — pass `lifespan=lifespan` to the FastAPI constructor.

## AFTER WRITING CODE
- Import check: `cd backend && py -c "from app.main import app; print('OK')"`
- Run tests: `cd backend && py -m pytest tests/ -v`
- Fix ALL failures — never commit red

## FASTAPI PRODUCTION SAFETY RULES

**CORS**: NEVER use `allow_origins=["*"]` — wildcard CORS is incompatible with `allow_credentials=True` and exposes all endpoints to any origin. Always use explicit origin list: `allow_origins=["http://localhost:3000"]`. Wildcard is silent in dev but a security regression in production.
(Source: FastAPI best practices 2026 — fastlaunchapi.dev)

**Async route discipline**: `async def` route handlers must NEVER contain blocking I/O — no `time.sleep()`, no synchronous DB calls, no blocking subprocess calls. These stall the uvicorn event loop and kill all concurrent requests. Only use sync primitives inside `asyncio.to_thread()` or background tasks.
(Source: DEV Community production-ready FastAPI 2026)

## FRAGILE ZONES — DOUBLE-CHECK BEFORE COMMITTING
These three files have downstream effects that tests don't fully catch. When you edit any of them, re-read the surrounding interface contract (type signatures, response shapes) before committing:

- **`backend/app/auth.py`** — JWT payload shape: changing `sub`, `tier`, or any key breaks `get_current_user()` for ALL routes. Verify `{"sub": user.id, "tier": user.subscription_tier}` is unchanged.
- **`backend/app/services/scheduler.py`** — datetime handling: `_last_check` must be a UTC-aware datetime. APScheduler fires every 30s; if `_last_check` is naive or in wrong TZ, bets are silently re-detected or missed.
- **`backend/app/services/polymarket.py`** — API response normalization: if the key names returned to routes change (e.g. `profit` → `profit_usd`), ALL routes that use bettor data break silently. The normalised field names are the internal contract — grep for usages before renaming.

(Source: arxiv 2603.06847 — Fault Taxonomy for Agentic AI: token management faults → auth failures; datetime defects → scheduling anomalies; API normalization faults → data validation failures)
