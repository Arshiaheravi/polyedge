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
- Backend port: **8003** — never 8001, 8000, or 8002 (8002 was retired 2026-03-26)

## FRONTEND PATTERNS (PolyEdge)
- All JS and CSS in `frontend/index.html` — single-file SPA, no separate app.js/styles.css
- Dark theme, no emojis in UI text (use inline SVGs instead)
- API base: `http://localhost:8003`
- JWT token: stored in `localStorage` as `pe_token`
- Global state variables: `_bettorCache` (Map), `_disclosureCache` (Map), `alertSettings` (object)

## DICT KEY CONTRACT — CHECK ALL 3 LAYERS
When a function returns a dict with new keys:
1. Route passes ALL keys to model constructor
2. Model has fields for all keys
3. Frontend uses same key names
Missing any layer = silent bug

## POLYEDGE FEATURE WIRING CHAIN
When adding a new tier-gated feature, verify all layers — missing any silently exposes premium content or hides it from paying users:
1. Service function in `backend/app/services/polymarket.py` (no I/O side effects)
2. Route in `backend/app/routes/` — imports service, checks `current_user.subscription_tier`
3. Tier gate: enforce in route with `if user.subscription_tier == "free": return locked_response`
4. Register route in `backend/app/main.py` with `app.include_router()`
5. Frontend JS: call endpoint, render gated content per tier
6. Cache key includes tier if response differs by tier (bug #1 pattern: profile cache must key on `{address}_{tier}`)
7. Write test for each tier (free/basic/vip) asserting correct content visible/locked
8. Check profile cache reverse-order (free caches first → VIP should still get unlocked)

## EXTERNAL API ERROR HANDLING PATTERNS

**Alpaca Trading API** — wrap order submission in exponential backoff:
- Retry on 503/504: `time.sleep(2**attempt)` up to 3 attempts
- Re-raise immediately on 401/403: auth errors are not retryable, stop and alert
- Always call `get_open_position(ticker)` before any sell order to avoid position-not-found errors
- Use `alpaca-py` SDK (not deprecated `alpaca-trade-api`) — Pydantic-first, cleaner error messages

**Production startup** — use Gunicorn + Uvicorn workers instead of raw `uvicorn`:
```
gunicorn -k uvicorn.workers.UvicornWorker -w 4 app.main:app --port 8003
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

**FastAPI v0.132+ strict Content-Type (breaking change)**: FastAPI v0.132+ enforces `Content-Type: application/json` for JSON request bodies by default. If upgrading FastAPI, frontend `fetch()` calls that POST JSON without explicit Content-Type header will receive 415 Unsupported Media Type. Fix: add `headers: {'Content-Type': 'application/json'}` to all fetch() POST calls, or set `app = FastAPI(strict_content_type=False)` to opt out. Check with `py -m pip show fastapi | grep Version` before upgrading.
(Source: FastAPI release notes v0.132.0, 2026)

**FastAPI native SSE (v0.135.0)**: FastAPI now has first-class SSE support via StreamingResponse + `yield`. For PolyEdge's bet alert stream, use `StreamingResponse(generate_events(), media_type="text/event-stream")` where `generate_events()` is an async generator yielding `f"data: {json.dumps(event)}\n\n"`. Eliminates the need for external SSE libraries.
(Source: FastAPI release notes v0.135.0, 2026)

**FastAPI v0.134.0 streaming JSON Lines**: `yield` inside route handlers now streams JSON Lines directly. Pattern:
```python
async def generate_bets():
    async for bet in poll_bets():
        yield json.dumps(bet) + "\n"

@router.get("/stream/bets")
async def stream_bets():
    return StreamingResponse(generate_bets(), media_type="application/x-ndjson")
```
Requires Starlette ≥ 0.46.0. Useful for PolyEdge's real-time bet feed endpoint (backlogged SSE item).
(Source: FastAPI release notes v0.134.0, 2026)

**FastAPI v0.131.0 deprecation**: `ORJSONResponse` and `UJSONResponse` are deprecated. Use standard `JSONResponse` (now Pydantic/Rust-backed for performance in v0.130+). If you see `DeprecationWarning: ORJSONResponse`, switch to `JSONResponse`.
(Source: FastAPI release notes v0.131.0, 2026)

## FRAGILE ZONES — DOUBLE-CHECK BEFORE COMMITTING
These three files have downstream effects that tests don't fully catch. When you edit any of them, re-read the surrounding interface contract (type signatures, response shapes) before committing:

- **`backend/app/auth.py`** — JWT payload shape: changing `sub`, `tier`, or any key breaks `get_current_user()` for ALL routes. Verify `{"sub": user.id, "tier": user.subscription_tier}` is unchanged.
- **`backend/app/services/scheduler.py`** — datetime handling: `_last_check` must be a UTC-aware datetime. APScheduler fires every 30s; if `_last_check` is naive or in wrong TZ, bets are silently re-detected or missed.
- **`backend/app/services/polymarket.py`** — API response normalization: if the key names returned to routes change (e.g. `profit` → `profit_usd`), ALL routes that use bettor data break silently. The normalised field names are the internal contract — grep for usages before renaming.

(Source: arxiv 2603.06847 — Fault Taxonomy for Agentic AI: token management faults → auth failures; datetime defects → scheduling anomalies; API normalization faults → data validation failures)
