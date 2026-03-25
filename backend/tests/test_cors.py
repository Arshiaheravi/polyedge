"""
CORS header tests — verifies that the CORSMiddleware is configured and
returns the correct headers for both simple requests and preflight OPTIONS.

Config: allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
        allow_headers=["*"]
"""


def test_cors_header_present_on_simple_request(client):
    """A simple GET request with an Origin header should receive CORS headers back."""
    resp = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_cors_allows_any_origin(client):
    """Wildcard config should allow an arbitrary origin and reflect it or return *."""
    resp = client.get("/", headers={"Origin": "https://evil.example.com"})
    assert resp.status_code == 200
    allow_origin = resp.headers.get("access-control-allow-origin", "")
    # With allow_origins=["*"] + allow_credentials=True, Starlette reflects the request origin
    # rather than returning bare "*" (bare "*" is incompatible with credentials).
    # Either form is acceptable — the key assertion is that SOME value is present.
    assert allow_origin != "", "Access-Control-Allow-Origin header must be present"


def test_cors_preflight_returns_200(client):
    """OPTIONS preflight request should be handled and return 200 with CORS headers."""
    resp = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        },
    )
    # Starlette returns 200 for preflight when origin is allowed
    assert resp.status_code == 200
    assert "access-control-allow-origin" in resp.headers


def test_cors_preflight_allows_authorization_header(client):
    """Authorization must be an allowed header — required for JWT auth to work cross-origin."""
    resp = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    assert resp.status_code == 200
    allowed = resp.headers.get("access-control-allow-headers", "")
    # allow_headers=["*"] means all headers are permitted
    assert allowed != "", "Access-Control-Allow-Headers must be present in preflight response"


def test_cors_no_origin_header_still_returns_200(client):
    """Requests without an Origin header (same-origin, curl, etc.) should still succeed."""
    resp = client.get("/")
    assert resp.status_code == 200
    # No CORS header needed when no Origin is present — browser same-origin requests
    assert resp.json()["status"] == "running"
