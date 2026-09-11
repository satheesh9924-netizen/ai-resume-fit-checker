import pytest

from resume_matcher.llm_client import create_client
from resume_matcher.matcher import ResumeMatcher


@pytest.fixture(scope="session")
def matcher():
    return ResumeMatcher(create_client())
