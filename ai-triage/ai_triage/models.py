from dataclasses import dataclass

VALID_CATEGORIES = ["FLAKY", "REGRESSION", "ENVIRONMENT", "UNKNOWN"]


@dataclass(frozen=True)
class TestFailure:
    __test__ = False  # not a pytest test class despite the name

    class_name: str
    test_name: str
    error_message: str
    stack_trace: str


@dataclass(frozen=True)
class TriageResult:
    category: str
    summary: str
    suggested_action: str
