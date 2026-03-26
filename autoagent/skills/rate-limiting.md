# Skill: Rate Limiting (PolyEdge FastAPI)

## WHEN TO USE THIS SKILL
When adding rate limiting to auth routes (`POST /auth/register`, `POST /auth/login`) or any public endpoint vulnerable to brute force. The backlog item targets 10 req/min per IP on auth routes.

## PACKAGE
```bash
pip install slowapi
```
Add to `backend/requirements.txt`.

## SETUP — `backend/app/main.py`
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter instance (module level, above app creation)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```
`get_remote_address` extracts the real client IP (handles X-Forwarded-For via Starlette).

## ROUTE DECORATOR PATTERN
```python
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import the module-level limiter (defined in main.py)
# In PolyEdge: import from app.main or define in a shared limiter.py

@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, form_data: LoginForm, db: Session = Depends(get_db)):
    ...
```
**CRITICAL**: The `request: Request` parameter MUST be in the function signature — slowapi reads it to extract the client IP. Without it, you'll get a 500 error.

## RATE LIMIT STRING FORMATS
```
"10/minute"   → 10 requests per minute
"100/hour"    → 100 requests per hour
"5/second"    → 5 requests per second
"10/minute;5/second"  → multiple limits (both apply)
```

## RESPONSE ON LIMIT EXCEEDED
slowapi automatically returns HTTP 429 Too Many Requests with:
```json
{"error": "Rate limit exceeded: 10 per 1 minute"}
```
No extra code needed — `_rate_limit_exceeded_handler` handles it.

## POLYEDGE-SPECIFIC TARGETS
Apply to these routes in `backend/app/routes/auth.py`:
- `POST /auth/register` — limit: `"10/minute"` (prevents mass account creation)
- `POST /auth/login` — limit: `"10/minute"` (prevents brute force)

The backlog item says 10 req/min per IP. Both auth routes should use the same limit.

## TESTING RATE LIMITS
```python
def test_rapid_login_attempts_trigger_429(client):
    # Make 11 requests — the 11th should be 429
    for i in range(10):
        client.post("/auth/login", json={"email": "x@x.com", "password": "wrong"})
    resp = client.post("/auth/login", json={"email": "x@x.com", "password": "wrong"})
    assert resp.status_code == 429
```
Note: slowapi uses in-memory storage by default. In tests with a shared `client` fixture, limits accumulate across test calls. Reset between tests by using a fresh limiter or `limiter.reset()`.

## KNOWN CAVEATS
- Behind a reverse proxy (nginx/Cloudflare), `get_remote_address` may return the proxy IP. For PolyEdge (local dev), this is fine. For production, add `app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")` from `uvicorn.middleware.proxy_headers`.
- slowapi uses `in-memory` storage by default — limits reset on server restart and don't work across multiple uvicorn workers. For production with Gunicorn multi-worker, use Redis backend: `Limiter(key_func=get_remote_address, storage_uri="redis://localhost:6379")`.

## SOURCES
- slowapi.readthedocs.io — official docs, read 2026-03-26
- backlog.md: "Rate limiting on auth routes — add slowapi/starlette middleware to limit POST /auth/register and POST /auth/login to 10 req/min per IP"
