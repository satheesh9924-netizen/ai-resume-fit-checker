"""Checks that the model's claims are grounded in the source documents rather than invented.
A "matched" skill must share at least one meaningful keyword with the resume (lenient --
catches skills sharing zero real overlap, i.e. outright fabrications). A "missing" skill
must NOT have ALL of its meaningful keywords present (strict -- a single generic shared word
like "testing" isn't enough to call a compound skill phrase "already present"; the whole
claimed capability has to actually be there for the claim to be inconsistent)."""
import re
from typing import List

from .support import read_golden_file

STOPWORDS = {
    "a", "an", "and", "or", "of", "in", "on", "for", "with", "to", "the", "is", "are",
    "was", "were", "be", "been", "this", "that", "using", "use", "based", "level",
    "experience", "professional", "hands", "skills", "tools", "exposure", "familiar",
    "familiarity", "knowledge", "years", "year",
}


def significant_tokens(phrase: str) -> List[str]:
    tokens = re.split(r"[^a-z0-9]+", phrase.lower())
    return [t for t in tokens if len(t) >= 3 and t not in STOPWORDS]


def test_matched_skills_are_grounded_in_resume_text(matcher):
    resume = read_golden_file("case1_strong_fit", "resume.txt")
    jd = read_golden_file("case1_strong_fit", "jd.txt")
    resume_lower = resume.lower()

    result = matcher.match(resume, jd)

    for skill in result.matched_skills:
        tokens = significant_tokens(skill)
        any_token_present = not tokens or any(t in resume_lower for t in tokens)
        assert any_token_present, (
            f'Claimed matched skill "{skill}" shares no keyword with the resume text -- '
            f"possible hallucination. Full reasoning: {result.reasoning}"
        )


def test_missing_skills_are_not_already_present_in_resume(matcher):
    resume = read_golden_file("case3_partial_fit", "resume.txt")
    jd = read_golden_file("case3_partial_fit", "jd.txt")
    resume_lower = resume.lower()

    result = matcher.match(resume, jd)

    for skill in result.missing_skills:
        tokens = significant_tokens(skill)
        fully_present = bool(tokens) and all(t in resume_lower for t in tokens)
        assert not fully_present, (
            f'Skill "{skill}" was listed as missing but is fully present in the resume -- '
            f"inconsistent reasoning: {result.reasoning}"
        )
