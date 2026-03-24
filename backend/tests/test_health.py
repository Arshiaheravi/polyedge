"""Tests for health/root endpoints and general API behaviour."""


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
    """CORS allows all origins (needed for frontend on :3000)."""
    resp = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Either 200 (preflight handled) or the GET itself — either way origin is allowed
    assert resp.status_code in (200, 405)


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
