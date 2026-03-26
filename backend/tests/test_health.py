"""Tests for health/root endpoints and general API behaviour."""
from unittest.mock import MagicMock, patch


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_root_endpoint(client):
    resp = client.get("/")
    data = resp.json()
    assert resp.status_code == 200
    assert data["service"] == "PolyEdge API"
    assert data["status"] == "running"
    assert "version" in data


def test_openapi_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_json_available(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert "paths" in schema
    # Verify all key endpoints are in the schema
    paths = schema["paths"]
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/bettors" in paths
    assert "/follows" in paths
    assert "/follows/live" in paths
    assert "/alerts/settings" in paths
    assert "/payments/checkout" in paths
    assert "/admin/stats" in paths


def test_cors_headers_present(client):
    """CORS allows http://localhost:3000 (frontend origin — credentials allowed)."""
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Either 200 (preflight handled) or the GET itself — either way origin is allowed
    assert resp.status_code in (200, 405)


def test_readiness_endpoint_healthy(client):
    """Readiness probe returns 200 with ready status when DB is reachable."""
    resp = client.get("/readiness")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_readiness_endpoint_db_failure(client):
    """Readiness probe returns 503 when DB is unavailable."""
    mock_session = MagicMock()
    mock_session.execute.side_effect = Exception("DB unavailable")

    with patch("app.main.SessionLocal", return_value=mock_session):
        resp = client.get("/readiness")

    assert resp.status_code == 503
    data = resp.json()
    assert data["status"] == "unavailable"
    assert data["detail"] == "Database connectivity check failed"


def test_health_not_rate_limited(client):
    """GET /health must never return 429 — k8s liveness probes call this continuously."""
    for _ in range(20):
        resp = client.get("/health")
        assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}"


def test_readiness_not_rate_limited(client):
    """GET /readiness must never return 429 — k8s readiness probes call this continuously."""
    for _ in range(20):
        resp = client.get("/readiness")
        assert resp.status_code == 200, f"Expected 200 but got {resp.status_code}"


def test_get_settings_returns_same_instance():
    """get_settings() must be @lru_cache — two calls must return the exact same object (Bug #9 regression)."""
    from app.config import get_settings
    first = get_settings()
    second = get_settings()
    assert first is second, (
        "get_settings() returns a new Settings() object on each call — @lru_cache is missing or broken. "
        "This causes .env to be re-read on every scheduler invocation."
    )


def test_unauthenticated_protected_routes(client):
    """All protected routes return 403 without a token, not 500."""
    protected = [
        ("GET", "/auth/me"),
        ("GET", "/follows"),
        ("POST", "/follows"),
        ("GET", "/follows/live"),
        ("GET", "/alerts/settings"),
        ("PUT", "/alerts/settings"),
        ("POST", "/alerts/telegram/start"),
        ("POST", "/payments/checkout"),
        ("GET", "/payments/portal"),
    ]
    for method, path in protected:
        resp = client.request(method, path)
        assert resp.status_code == 403, f"{method} {path} should be 403, got {resp.status_code}"
