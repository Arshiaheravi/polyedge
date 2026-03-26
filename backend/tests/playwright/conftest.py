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
    """Helper: open app, log in as the given tier account."""
    creds = ACCOUNTS[tier]
    page.goto(BASE_URL)
    page.click("text=Login")
    page.fill("input[type=email]", creds["email"])
    page.fill("input[type=password]", creds["password"])
    page.click("button[type=submit]")
    page.wait_for_selector("#dashboard", timeout=10_000)
