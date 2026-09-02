#!/usr/bin/env python3
"""Score whether website directions are strategically and structurally distinct."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import read_json, utc_now, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--strict", action="store_true", help="Fail on incomplete scores or pairs below target")
    parser.add_argument("--report-json", type=Path)
    args = parser.parse_args()

    root = args.project_dir.resolve()
    config_path = root / "config/distinctness.json"
    if not config_path.is_file():
        message = f"Missing {config_path}"
        print(f"WARNING: {message}")
        return 1 if args.strict else 0

    data = read_json(config_path)
    dimensions = data.get("dimensions") or []
    pairs = data.get("pairs") or []
    target = int(data.get("target", 15))
    findings = []
    complete = True
    passed = True

    for pair in pairs:
        a = pair.get("a", "?")
        b = pair.get("b", "?")
        scores = pair.get("scores") or {}
        missing = [dimension for dimension in dimensions if scores.get(dimension) is None]
        invalid = [dimension for dimension in dimensions if scores.get(dimension) is not None and scores.get(dimension) not in (0, 1, 2)]
        total = sum(int(scores.get(dimension) or 0) for dimension in dimensions if scores.get(dimension) in (0, 1, 2))
        status = "pass"
        if invalid:
            status = "invalid"
            passed = False
        elif missing:
            status = "incomplete"
            complete = False
        elif total < target:
            status = "below-target"
            passed = False
        findings.append({"a": a, "b": b, "score": total, "possible": len(dimensions) * 2, "target": target, "status": status, "missing": missing, "invalid": invalid, "notes": pair.get("notes", "")})

    report = {"generated_at": utc_now(), "target": target, "dimensions": dimensions, "complete": complete, "passed": passed and complete, "pairs": findings}
    report_path = args.report_json or (root / "qa/distinctness.json")
    write_json(report_path, report)

    for finding in findings:
        print(f"{finding['a']} vs {finding['b']}: {finding['score']}/{finding['possible']}, {finding['status']}")
    if not findings:
        print("WARNING: no direction pairs are defined")
        return 1 if args.strict else 0
    if args.strict and (not complete or not passed):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
