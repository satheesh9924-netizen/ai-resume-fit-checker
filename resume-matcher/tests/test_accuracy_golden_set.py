"""Golden-set regression suite: each case has a human-judged expected score RANGE (not an
exact value) and expected verdict. Re-run this whenever the prompt changes to catch
quality regressions -- this is the LLM-feature equivalent of a unit test suite."""
import pytest

from .support import read_expected, read_golden_file

GOLDEN_CASES = ["case1_strong_fit", "case2_no_fit", "case3_partial_fit"]


@pytest.mark.parametrize("case_name", GOLDEN_CASES)
def test_match_score_falls_within_expected_range(matcher, case_name):
    resume = read_golden_file(case_name, "resume.txt")
    jd = read_golden_file(case_name, "jd.txt")
    expected = read_expected(case_name)

    result = matcher.match(resume, jd)

    assert expected.min_score <= result.match_score <= expected.max_score, (
        f"[{case_name}] matchScore {result.match_score} outside expected range "
        f"[{expected.min_score},{expected.max_score}]. Reasoning was: {result.reasoning}"
    )
    assert result.verdict == expected.verdict, (
        f"[{case_name}] unexpected verdict. Reasoning was: {result.reasoning}"
    )
