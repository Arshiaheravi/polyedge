"""
Shared fixtures for all tests.
Uses an in-memory SQLite database so tests are isolated and fast.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def clear_stripe_webhook_secret():
    """Prevent .env STRIPE_WEBHOOK_SECRET from triggering real Stripe sig verification in tests."""
    from app.services import stripe_service
    original = stripe_service.settings.stripe_webhook_secret
    stripe_service.settings.stripe_webhook_secret = ""
    yield
    stripe_service.settings.stripe_webhook_secret = original

TEST_DB_URL = "sqlite:///./test_polyedge.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    """Register a user and return (client, token, user_data)."""
    resp = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    return data["access_token"], data["user"]


@pytest.fixture
def auth_headers(registered_user):
    token, _ = registered_user
    return {"Authorization": f"Bearer {token}"}
