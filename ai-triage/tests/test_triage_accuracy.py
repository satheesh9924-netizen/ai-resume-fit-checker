"""Golden-set regression suite for the triage bot itself: each fixture is a synthetic failure
with an obvious human-judged category. Re-run whenever SYSTEM_PROMPT changes to catch
classification regressions before they reach real CI failures."""
import json
import pathlib

import pytest

from ai_triage.models import TestFailure, VALID_CATEGORIES

GOLDEN_DIR = pathlib.Path(__file__).parent / "golden"
GOLDEN_FILES = ["flaky_timeout.json", "regression_selector.json", "environment_docker.json"]


@pytest.mark.parametrize("fixture_file", GOLDEN_FILES)
def test_classifies_failure_into_expected_category(triage, fixture_file):
    data = json.loads((GOLDEN_DIR / fixture_file).read_text(encoding="utf-8"))
    failure = TestFailure(
        class_name=data["className"],
        test_name=data["testName"],
        error_message=data["errorMessage"],
        stack_trace=data["stackTrace"],
    )

    result = triage.triage(failure)

    assert result.category in VALID_CATEGORIES, f"Unexpected category: {result.category}"
    assert result.category == data["expectedCategory"], f"[{fixture_file}] Summary was: {result.summary}"
