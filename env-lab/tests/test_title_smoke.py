import pytest
from playwright.sync_api import expect

from env_lab.config import get_config

pytestmark = pytest.mark.smoke


def test_page_title_matches_the_target_profile(page):
    cfg = get_config()
    page.goto(cfg.str("urls.web"))
    expect(page).to_have_title(cfg.str("expected.title"))


def test_page_reports_the_targets_version(page):
    cfg = get_config()
    page.goto(cfg.str("urls.web"))
    expect(page.locator("#version")).to_have_text(cfg.version)
