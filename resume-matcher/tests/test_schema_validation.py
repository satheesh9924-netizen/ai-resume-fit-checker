"""Validates that Claude's output conforms to the required structure, regardless of whether
the match verdict itself is "correct" -- an LLM can be well-calibrated and still return
malformed output under load, so structure is tested independently of accuracy."""
from resume_matcher.matcher import VALID_VERDICTS

from .support import read_golden_file


def test_match_result_has_well_formed_fields(matcher):
    resume = read_golden_file("case1_strong_fit", "resume.txt")
    jd = read_golden_file("case1_strong_fit", "jd.txt")

    result = matcher.match(resume, jd)

    assert 0 <= result.match_score <= 100, f"matchScore out of range: {result.match_score}"
    assert result.verdict in VALID_VERDICTS, f"Unexpected verdict: {result.verdict}"
    assert result.matched_skills is not None
    assert result.missing_skills is not None
    assert result.reasoning is not None
    assert result.reasoning.strip() != ""
