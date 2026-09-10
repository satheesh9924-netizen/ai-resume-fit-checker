import re

from playwright.sync_api import expect


def test_homepage_title(page):
    """Verify Playwright homepage title"""
    page.goto("https://playwright.dev")
    expect(page).to_have_title(re.compile("Playwright"))


def test_docs_navigation(page):
    """Verify Docs navigation"""
    page.goto("https://playwright.dev")
    page.get_by_role("link", name="Get started").click()
    expect(page).to_have_url(re.compile(r".*docs/intro"))
    expect(page.get_by_role("heading", name=re.compile("Installation", re.IGNORECASE))).to_be_visible()
