import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.limiter import limiter
from app.routes import admin, alerts, auth, bettors, follows, markets, payments
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Starting background scheduler...")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Stopping scheduler...")
    stop_scheduler()


app = FastAPI(
    title="PolyEdge API",
    description="Copy the best Polymarket bettors in real-time",
    version="1.0.0",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(bettors.router)
app.include_router(follows.router)
app.include_router(alerts.router)
app.include_router(markets.router)
app.include_router(payments.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"service": "PolyEdge API", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/readiness")
def readiness():
    """Readiness probe — checks DB connectivity. Returns 200 if DB is reachable, 503 otherwise."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(status_code=503, content={"status": "unavailable", "detail": "Database connectivity check failed"})
    finally:
        db.close()
