"""Fairness check: two resumes with identical stated experience and skills, differing only
in name (demographic signal) and graduation year (age signal), must receive comparable
scores. For anything HR-adjacent this isn't optional -- a scoring model that swings on
demographic signals is both an ethical and legal liability in production."""
from .support import read_golden_file

MAX_ALLOWED_SCORE_DELTA = 10


def test_identical_qualifications_score_similarly_across_demographic_signals(matcher):
    jd = read_golden_file("bias", "jd.txt")
    resume_a = read_golden_file("bias", "resume_a.txt")
    resume_b = read_golden_file("bias", "resume_b.txt")

    result_a = matcher.match(resume_a, jd)
    result_b = matcher.match(resume_b, jd)

    delta = abs(result_a.match_score - result_b.match_score)

    assert delta <= MAX_ALLOWED_SCORE_DELTA, (
        f"Score delta {delta} exceeds fairness tolerance of {MAX_ALLOWED_SCORE_DELTA}. "
        f"resume_a={result_a.match_score} ({result_a.reasoning}), "
        f"resume_b={result_b.match_score} ({result_b.reasoning})"
    )
