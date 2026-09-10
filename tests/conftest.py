import os
import pathlib

import allure
import pytest
from playwright.sync_api import sync_playwright

TARGET_DIR = pathlib.Path("target")


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    headless = os.environ.get("HEADLESS", "true").lower() != "false"
    browser = playwright_instance.chromium.launch(headless=headless)
    yield browser
    browser.close()


@pytest.fixture
def context(browser):
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield context
    context.close()


@pytest.fixture
def page(context, request):
    page = context.new_page()
    yield page

    failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    test_name = request.node.name

    if failed:
        (TARGET_DIR / "screenshots").mkdir(parents=True, exist_ok=True)
        (TARGET_DIR / "traces").mkdir(parents=True, exist_ok=True)

        screenshot_path = TARGET_DIR / "screenshots" / f"{test_name}.png"
        page.screenshot(path=str(screenshot_path))
        allure.attach.file(str(screenshot_path), name=f"{test_name} - screenshot",
                            attachment_type=allure.attachment_type.PNG)

        trace_path = TARGET_DIR / "traces" / f"{test_name}-trace.zip"
        context.tracing.stop(path=str(trace_path))
        allure.attach.file(str(trace_path), name=f"{test_name} - trace", extension="zip")
    else:
        context.tracing.stop()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)
