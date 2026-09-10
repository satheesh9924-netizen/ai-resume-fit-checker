import pytest

from ai_triage.failure_triage import FailureTriage
from ai_triage.llm_client import create_client


@pytest.fixture(scope="session")
def triage():
    return FailureTriage(create_client())
