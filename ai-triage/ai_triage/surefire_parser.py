import pathlib
from typing import List

from defusedxml.ElementTree import parse as safe_parse

from .models import TestFailure


def parse_directory(surefire_reports_dir: pathlib.Path) -> List[TestFailure]:
    failures: List[TestFailure] = []
    if not surefire_reports_dir.is_dir():
        return failures

    xml_files = sorted(
        p for p in surefire_reports_dir.iterdir()
        if p.name.startswith("TEST-") and p.name.endswith(".xml")
    )
    for xml_file in xml_files:
        failures.extend(_parse_file(xml_file))
    return failures


def _parse_file(xml_file: pathlib.Path) -> List[TestFailure]:
    failures: List[TestFailure] = []
    try:
        tree = safe_parse(str(xml_file))
    except Exception as e:
        raise RuntimeError(f"Failed to parse surefire report: {xml_file}") from e

    for testcase in tree.getroot().iter("testcase"):
        problem = testcase.find("failure")
        if problem is None:
            problem = testcase.find("error")
        if problem is None:
            continue
        failures.append(TestFailure(
            class_name=testcase.get("classname", ""),
            test_name=testcase.get("name", ""),
            error_message=problem.get("message", ""),
            stack_trace=problem.text or "",
        ))
    return failures
