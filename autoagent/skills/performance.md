# Skill: Performance

**When to use**: When building features that hit external APIs, query databases, handle
concurrent users, or process lists of tickers. Also use when a route feels slow.

## The most common performance killers (in order)

### 0. Co-locating related fields in the same batch query
When adding a new field that uses the same underlying query data as an existing field, compute BOTH in the same loop iteration:
```python
# WRONG — two separate queries for the same ticker history
for ticker in tickers:
    s.score_history = get_score_history(db, ticker)   # query 1
    s.score_velocity = get_score_velocity(db, ticker)  # query 2 (same table!)

# CORRECT — one query, compute both fields from the result
for ticker in tickers:
    hist = get_score_history(db, ticker)  # one query
    s.score_history = hist
    s.score_velocity = calculate_velocity(hist)  # same data, no extra query
```
Pattern: when you add a second field from the same source, ask "do I already have this data in scope?" before writing a new query.

### 1. N+1 queries — most common, easy to miss
```python
# WRONG — hits DB once per ticker (N+1)
for ticker in tickers:
    signal = db.query(Signal).filter(Signal.ticker == ticker).first()
    results.append(signal)

# CORRECT — one query for all tickers
signals = db.query(Signal).filter(Signal.ticker.in_(tickers)).all()
signal_map = {s.ticker: s for s in signals}
```

### 2. Blocking I/O on async routes
```python
# WRONG — blocks the entire event loop while yfinance fetches
@router.get("/dashboard")
async def get_dashboard():
    data = yf.download("AAPL")  # sync call inside async route

# CORRECT — run sync code in a thread pool
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

@router.get("/dashboard")
async def get_dashboard():
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(executor, yf.download, "AAPL")
```

### 3. Fetching more data than needed
```python
# WRONG — downloads 5 years of daily data to check RSI
hist = ticker.history(period="5y")

# CORRECT — only fetch what the calculation needs
hist = ticker.history(period="6mo")  # RSI needs ~14 bars minimum
```

### 4. Re-fetching data already in cache
```python
# Always check cache first for expensive API calls
from src.stockcards.services.cache import cache

cached = await cache.get(f"signal:{ticker}")
if cached:
    return cached

result = await expensive_fetch(ticker)
await cache.set(f"signal:{ticker}", result, ttl=300)  # 5 min TTL
```

### 5. Sequential external calls that can be parallel
```python
# WRONG — fetches tickers one by one
results = []
for ticker in tickers:
    results.append(await fetch_signal(ticker))  # sequential

# CORRECT — fetch all at once
import asyncio
results = await asyncio.gather(*[fetch_signal(t) for t in tickers])
```

## Profiling a slow route

```python
import time

@router.get("/dashboard")
async def get_dashboard():
    t0 = time.time()

    data = await fetch_data()
    print(f"fetch_data: {time.time()-t0:.3f}s")

    signals = process(data)
    print(f"process: {time.time()-t0:.3f}s")

    return signals
```

Run it, read the output — the slowest step is where to optimize.

## StockCards-specific performance rules

- **Screener**: Never call yfinance for >75 tickers in a single request — batch in groups of 25
- **Dashboard endpoint**: Must respond in <3s — cache aggressive (5 min TTL for signal data)
- **Analysis functions** (`services/analysis.py`): Pure functions, no I/O — inherently fast
- **Redis cache**: Always try cache first before yfinance — saves 2-3s per ticker batch

## Quick wins when a route is slow

1. Add caching with 5-min TTL
2. Check for N+1 DB queries
3. Move sync yfinance calls to `run_in_executor`
4. Reduce historical data window (6mo instead of 1y)
5. Parallelize with `asyncio.gather`
