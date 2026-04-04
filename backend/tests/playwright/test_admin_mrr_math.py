"""
Playwright E2E: admin stats MRR math correct via browser fetch.

Fetches /admin/stats from a browser page context (with x-admin-password header)
and asserts that mrr_estimate equals basic_count*4.99 + vip_count*9.99 within $0.01.

Response shape: {"users":{"total":N,"free":N,"basic":N,"vip":N}, "mrr_estimate":N, ...}

Also asserts tier counts sum to total and that missing header is rejected (422).

Requires servers running:
  backend:  py -m uvicorn app.main:app --port 8003
  frontend: py -m http.server 3000 --directory frontend
"""
import pytest
from playwright.sync_api import Page
from .conftest import BASE_URL, API_BASE

ADMIN_PASSWORD = "polyedge-admin-2026"


def _fetch_admin_stats(page: Page) -> dict:
    """Fetch /admin/stats from the browser page context and return parsed JSON."""
    return page.evaluate(f"""async () => {{
        const res = await fetch('{API_BASE}/admin/stats', {{
            headers: {{ 'x-admin-password': '{ADMIN_PASSWORD}' }}
        }});
        if (!res.ok) return {{ _error: res.status }};
        return await res.json();
    }}""")


class TestAdminMrrMath:

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_admin_mrr_equals_basic_times_499_plus_vip_times_999(self, page: Page):
        """mrr_estimate must equal basic_count*4.99 + vip_count*9.99 (within $0.01)."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        result = _fetch_admin_stats(page)
        assert "_error" not in result, \
            f"/admin/stats fetch failed with status: {result.get('_error')}"

        users = result.get("users", {})
        basic_count = users.get("basic", 0)
        vip_count = users.get("vip", 0)
        reported_mrr = result.get("mrr_estimate")

        assert reported_mrr is not None, \
            "mrr_estimate field missing from /admin/stats response"

        expected_mrr = round(basic_count * 4.99 + vip_count * 9.99, 2)
        assert abs(reported_mrr - expected_mrr) < 0.01, (
            f"MRR math wrong: reported={reported_mrr}, "
            f"expected={expected_mrr} "
            f"(basic={basic_count}×$4.99 + vip={vip_count}×$9.99)"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_admin_stats_user_counts_sum_to_total(self, page: Page):
        """free + basic + vip must equal total in users object."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        result = _fetch_admin_stats(page)
        assert "_error" not in result, \
            f"/admin/stats fetch failed with status: {result.get('_error')}"

        users = result.get("users", {})
        free_count = users.get("free", 0)
        basic_count = users.get("basic", 0)
        vip_count = users.get("vip", 0)
        total = users.get("total", -1)

        tier_sum = free_count + basic_count + vip_count
        assert tier_sum == total, (
            f"Tier counts don't sum to total: "
            f"free({free_count}) + basic({basic_count}) + vip({vip_count}) = {tier_sum}, "
            f"total = {total}"
        )

    @pytest.mark.skipif(not BASE_URL, reason="frontend server not configured")
    def test_admin_stats_without_header_rejected(self, page: Page):
        """Fetching /admin/stats without the password header must be rejected (4xx)."""
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle", timeout=10_000)

        status = page.evaluate(f"""async () => {{
            const res = await fetch('{API_BASE}/admin/stats');
            return res.status;
        }}""")

        # FastAPI returns 422 when required header is missing (validation error)
        # and 403 when wrong password is provided — both are rejections
        assert status >= 400, \
            f"/admin/stats without header must be rejected (4xx), got {status}"
