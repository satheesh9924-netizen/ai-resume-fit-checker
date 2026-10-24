import os
import pathlib
import time

import allure
import pytest

from env_lab import http
from env_lab.config import get_config, skip_reason
from env_lab.context import headers

TARGET_DIR = pathlib.Path("target")
_environment_checked = False


# ---------- capability gating: the test declares what it NEEDS, the profile says what the target OFFERS ----------
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    required = [key for marker in item.iter_markers("requires") for key in marker.args]
    marker = item.get_closest_marker("min_version")
    reason = skip_reason(get_config(), required, marker.args[0] if marker else None)
    if reason:
        pytest.skip(reason)  # reported as skipped, with the reason, never silently dropped


# ---------- readiness: wait once for the environment unless the test is marked offline ----------
def _wait_for_environment(timeout=120):
    cfg = get_config()
    auth = http.basic_auth(cfg.str("rabbit.user"), cfg.str("rabbit.password"))
    probes = [
        (cfg.str("urls.web") + "/", None),
        (cfg.str("urls.orders") + "/__admin/mappings", None),
        (cfg.str("urls.payment") + "/payments/health", None),
        (cfg.str("urls.rabbit") + "/api/overview", auth),
    ]
    deadline = time.monotonic() + timeout
    for url, probe_headers in probes:
        while True:
            try:
                if http.get(url, probe_headers, timeout=5).status < 500:
                    break
            except Exception:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError(f"Environment not ready: {url}")
            time.sleep(1)


@pytest.fixture(autouse=True)
def environment_ready(request):
    global _environment_checked
    if request.node.get_closest_marker("offline") or _environment_checked:
        return
    _wait_for_environment()
    _environment_checked = True


# ---------- Playwright fixtures (same pattern as the root tests, plus tenant headers) ----------
@pytest.fixture(scope="session")
def playwright_instance():
    from playwright.sync_api import sync_playwright
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
    context = browser.new_context(extra_http_headers=headers())
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
