"""
Playwright conftest — shared fixtures for all frontend E2E tests.
Requires: pip install pytest-playwright
          py -m playwright install chromium
"""
import pytest
from playwright.sync_api import sync_playwright, Browser, Page

BASE_URL = "http://localhost:3000"

ACCOUNTS = {
    "free":  {"email": "free@polyedge.com",  "password": "FreeTest123!"},
    "basic": {"email": "basic@polyedge.com", "password": "BasicTest123!"},
    "vip":   {"email": "vip@polyedge.com",   "password": "VipTest123!"},
}


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture()
def page(browser: Browser):
    ctx = browser.new_context()
    pg = ctx.new_page()
    yield pg
    ctx.close()


def login(page: Page, tier: str) -> None:
    """Helper: open app, log in as the given tier account.

    Nav buttons are display:none at desktop viewport — navigate via JS evaluate.
    Input IDs are #login-email / #login-password; submit button is #login-submit.
    """
    creds = ACCOUNTS[tier]
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle", timeout=10_000)
    # Navigate to login form via JS (avoids clicking display:none nav elements)
    page.evaluate("showView('auth', 'login')")
    page.fill("#login-email", creds["email"])
    page.fill("#login-password", creds["password"])
    page.click("#login-submit")
    # Wait for the dashboard view to become visible (class 'hidden' is removed on login)
    page.wait_for_function(
        "!document.getElementById('view-dashboard').classList.contains('hidden')",
        timeout=10_000,
    )
