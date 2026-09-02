#!/usr/bin/env python3
"""Score whether website directions are strategically and structurally distinct."""
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path

from _common import read_json, utc_now, write_json
from new_project import DISTINCTNESS_DIMENSIONS

MINIMUM_TARGET = 15


def valid_score(value: object) -> bool:
    return type(value) is int and value in (0, 1, 2)


def rubric_errors(dimensions: object, target: object) -> list[str]:
    errors = []
    if not isinstance(dimensions, list):
        errors.append("dimensions must be a JSON array")
    else:
        if not all(isinstance(dimension, str) for dimension in dimensions):
            errors.append("dimensions must contain only strings")
        duplicates = []
        seen = set()
        for dimension in dimensions:
            if isinstance(dimension, str) and dimension in seen and dimension not in duplicates:
                duplicates.append(dimension)
            if isinstance(dimension, str):
                seen.add(dimension)
        missing = [dimension for dimension in DISTINCTNESS_DIMENSIONS if dimension not in dimensions]
        unknown = [dimension for dimension in dimensions if dimension not in DISTINCTNESS_DIMENSIONS]
        if duplicates:
            errors.append(f"dimensions contain duplicates: {', '.join(str(dimension) for dimension in duplicates)}")
        if missing:
            errors.append(f"dimensions omit required rubric entries: {', '.join(missing)}")
        if unknown:
            errors.append(f"dimensions contain unknown rubric entries: {', '.join(str(dimension) for dimension in unknown)}")
        if dimensions != DISTINCTNESS_DIMENSIONS:
            errors.append("dimensions must exactly match the canonical 11-item rubric")
    if type(target) is not int:
        errors.append("target must be an integer")
    elif target < MINIMUM_TARGET:
        errors.append(f"target must be at least {MINIMUM_TARGET}")
    return errors


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
    directions = read_json(root / "config/directions.json")
    if not isinstance(data, dict):
        print("ERROR: distinctness.json must contain a JSON object")
        return 1
    if not isinstance(directions, list):
        print("ERROR: directions.json must contain a JSON array")
        return 1
    try:
        direction_keys = [direction["key"] for direction in directions]
    except (KeyError, TypeError) as exc:
        print(f"ERROR: directions.json has a direction without a key: {exc}")
        return 1
    if not all(isinstance(key, str) for key in direction_keys) or len(set(direction_keys)) != len(direction_keys):
        print("ERROR: directions.json direction keys must be unique strings")
        return 1

    dimensions = data.get("dimensions")
    pairs = data.get("pairs") or []
    target = data.get("target", MINIMUM_TARGET)
    errors = rubric_errors(dimensions, target)
    if errors:
        report_path = args.report_json or (root / "qa/distinctness.json")
        write_json(report_path, {"generated_at": utc_now(), "target": target, "dimensions": dimensions, "complete": False, "passed": False, "errors": errors, "pairs": []})
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    findings = []
    complete = True
    passed = True
    expected_pairs = {tuple(sorted(pair)) for pair in combinations(direction_keys, 2)}
    seen_pairs: set[tuple[str, str]] = set()
    structure_invalid = False

    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            findings.append({"a": "?", "b": "?", "score": 0, "possible": len(dimensions) * 2, "target": target, "status": "unknown", "missing": [], "invalid": [], "notes": f"Pair {index + 1} is not an object"})
            complete = False
            passed = False
            structure_invalid = True
            continue
        a = pair.get("a", "?")
        b = pair.get("b", "?")
        pair_key = tuple(sorted((a, b))) if isinstance(a, str) and isinstance(b, str) else None
        pair_status = ""
        if pair_key not in expected_pairs:
            pair_status = "unknown"
        elif pair_key in seen_pairs:
            pair_status = "duplicate"
        else:
            seen_pairs.add(pair_key)
        raw_scores = pair.get("scores")
        scores = raw_scores if isinstance(raw_scores, dict) else {}
        missing = [dimension for dimension in dimensions if scores.get(dimension) is None]
        invalid = [dimension for dimension in dimensions if scores.get(dimension) is not None and not valid_score(scores.get(dimension))]
        total = sum(scores[dimension] for dimension in dimensions if valid_score(scores.get(dimension)))
        status = "pass"
        if pair_status:
            status = pair_status
            complete = False
            passed = False
            structure_invalid = True
        elif invalid:
            status = "invalid"
            passed = False
        elif missing:
            status = "incomplete"
            complete = False
        elif total < target:
            status = "below-target"
            passed = False
        findings.append({"a": a, "b": b, "score": total, "possible": len(dimensions) * 2, "target": target, "status": status, "missing": missing, "invalid": invalid, "notes": pair.get("notes", "")})

    for a, b in sorted(expected_pairs - seen_pairs):
        findings.append({"a": a, "b": b, "score": 0, "possible": len(dimensions) * 2, "target": target, "status": "missing", "missing": dimensions, "invalid": [], "notes": "No distinctness score was supplied for this direction pair."})
        complete = False
        passed = False
        structure_invalid = True

    report = {"generated_at": utc_now(), "target": target, "dimensions": dimensions, "complete": complete, "passed": passed and complete, "expected_pairs": [{"a": a, "b": b} for a, b in sorted(expected_pairs)], "pairs": findings}
    report_path = args.report_json or (root / "qa/distinctness.json")
    write_json(report_path, report)

    for finding in findings:
        print(f"{finding['a']} vs {finding['b']}: {finding['score']}/{finding['possible']}, {finding['status']}")
    if structure_invalid or (args.strict and (not complete or not passed)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
