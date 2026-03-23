import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import Base, engine
from app.routes import admin, alerts, auth, bettors, follows, payments
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(bettors.router)
app.include_router(follows.router)
app.include_router(alerts.router)
app.include_router(payments.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"service": "PolyEdge API", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
