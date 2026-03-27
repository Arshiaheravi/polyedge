"""
Playwright E2E: CORS header verification — asserts that API responses from
the backend never return Access-Control-Allow-Origin: * (wildcard), and that
the correct origin is echoed back for trusted requests.

Browser-level verification: Playwright intercepts real browser network responses
and checks the CORS header value, proving the fix is enforced from the browser's
perspective (not just from curl or unit tests).

Covers:
  1. CORS header is NOT wildcard on real browser API requests
  2. CORS header equals http://localhost:3000 for trusted-origin requests
  3. OPTIONS preflight request succeeds with correct headers
  4. Untrusted origin is not reflected back in Access-Control-Allow-Origin

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page, Response
from .conftest import BASE_URL

API_BASE = "http://localhost:8003"


class TestCORSHeaders:
    """Verify CORS response headers are correctly set from a real browser context."""

    def test_cors_header_not_wildcard_on_api_requests(self, page: Page):
        """API responses seen by the browser must not have Access-Control-Allow-Origin: *.

        Wildcard + credentials=True is rejected by all real browsers (CORS spec 3.2.3).
        The server is configured with allow_origins=["http://localhost:3000"].
        This test captures actual browser network responses and asserts the
        server-sent CORS header is never *.
        """
        captured_responses = []

        def on_response(response: Response):
            if API_BASE in response.url:
                try:
                    headers = response.headers
                    if "access-control-allow-origin" in headers:
                        captured_responses.append(
                            {
                                "url": response.url,
                                "cors_header": headers["access-control-allow-origin"],
                            }
                        )
                except Exception:
                    pass  # response may be closed by the time handler runs

        page.on("response", on_response)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15_000)

        if not captured_responses:
            pytest.skip(
                "No API responses with CORS headers captured — "
                "backend may not be running or no cross-origin requests were made"
            )

        wildcards = [r for r in captured_responses if r["cors_header"] == "*"]
        assert not wildcards, (
            f"Access-Control-Allow-Origin: * found in browser responses: {wildcards}. "
            "Wildcard + credentials=True is rejected by all browsers (CORS spec 3.2.3). "
            "Bug #2 regression — server must use explicit allow_origins list, not ['*']."
        )

    def test_cors_header_is_localhost_origin(self, page: Page):
        """API responses from the browser must echo back the correct origin.

        With allow_origins=["http://localhost:3000"], the server must return
        Access-Control-Allow-Origin: http://localhost:3000 (exact match).
        """
        captured: dict = {}

        def on_response(response: Response):
            if API_BASE in response.url and not captured:
                try:
                    headers = response.headers
                    if "access-control-allow-origin" in headers:
                        captured["url"] = response.url
                        captured["cors"] = headers["access-control-allow-origin"]
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=15_000)

        if not captured:
            pytest.skip(
                "No CORS-bearing API response captured — backend may not be running"
            )

        expected_origin = "http://localhost:3000"
        assert captured["cors"] == expected_origin, (
            f"Expected Access-Control-Allow-Origin: {expected_origin!r}, "
            f"got {captured['cors']!r} from {captured['url']}. "
            "Server must echo the exact allowed origin, not wildcard or empty string."
        )

    def test_preflight_cors_request_succeeds(self, page: Page):
        """OPTIONS preflight from the frontend origin must succeed with correct headers.

        Uses page.request.fetch() (playwright-level HTTP, not browser-level) to send
        a preflight-style OPTIONS request and verify the backend responds correctly.
        This directly tests the server's CORSMiddleware preflight handling.
        """
        response = page.request.fetch(
            f"{API_BASE}/auth/login",
            method="OPTIONS",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            },
        )
        assert response.ok, (
            f"Preflight OPTIONS request to /auth/login returned {response.status}. "
            "CORSMiddleware must handle OPTIONS and return 200 with CORS headers."
        )
        all_headers = response.headers
        assert "access-control-allow-origin" in all_headers, (
            "Preflight response missing Access-Control-Allow-Origin header. "
            "CORSMiddleware is not responding to OPTIONS requests correctly."
        )
        assert all_headers["access-control-allow-origin"] != "*", (
            "Preflight response returned wildcard CORS origin. "
            "Wildcard + credentials=True is not allowed per CORS spec 3.2.3."
        )

    def test_untrusted_origin_not_reflected(self, page: Page):
        """Requests with an untrusted Origin must not receive CORS approval.

        Uses page.request.fetch() to send an evil origin and verifies the server
        does NOT reflect it in Access-Control-Allow-Origin. In real browsers, the
        absence of this header causes the browser to block the response.
        """
        response = page.request.fetch(
            f"{API_BASE}/",
            headers={"Origin": "https://evil.example.com"},
        )
        all_headers = response.headers
        cors_header = all_headers.get("access-control-allow-origin", "")

        assert cors_header != "https://evil.example.com", (
            "Server reflected the untrusted origin in Access-Control-Allow-Origin! "
            "This would allow https://evil.example.com to make credentialed requests. "
            "Only http://localhost:3000 should be in the allow list."
        )
        assert cors_header != "*", (
            "Server returned wildcard CORS origin for an untrusted request. "
            "Wildcard + credentials=True is a security misconfiguration (Bug #2)."
        )
