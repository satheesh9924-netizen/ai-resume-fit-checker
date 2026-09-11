import json
import pathlib
from dataclasses import dataclass

GOLDEN_DIR = pathlib.Path(__file__).parent / "golden"


def read_golden_file(case_name: str, file_name: str) -> str:
    path = GOLDEN_DIR / case_name / file_name
    if not path.exists():
        raise FileNotFoundError(f"Missing test fixture: {path}")
    return path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class ExpectedRange:
    min_score: int
    max_score: int
    verdict: str


def read_expected(case_name: str) -> ExpectedRange:
    data = json.loads(read_golden_file(case_name, "expected.json"))
    return ExpectedRange(min_score=data["minScore"], max_score=data["maxScore"], verdict=data["verdict"])
