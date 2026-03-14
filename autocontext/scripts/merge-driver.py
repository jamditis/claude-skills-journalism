#!/usr/bin/env python3
"""Three-way merge driver for lessons.json.

Usage: merge-driver.py <ancestor> <ours> <theirs>
Outputs merged JSON to stdout. Exit 0 on success.
"""
import json
import sys
from datetime import datetime


def parse_ts(ts_str):
    """Parse timestamp string, return (datetime_obj, original_str) or (None, "")."""
    if not ts_str:
        return None, ""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt, ts_str
    except Exception:
        return None, ""


def merge_lesson(ancestor, ours, theirs):
    """Merge a single lesson modified on both sides."""
    result = dict(ours)

    # Additive validated_count
    anc_count = (ancestor or {}).get("validated_count", 0)
    ours_delta = ours.get("validated_count", 0) - anc_count
    theirs_delta = theirs.get("validated_count", 0) - anc_count
    result["validated_count"] = anc_count + max(0, ours_delta) + max(0, theirs_delta)

    # Higher confidence
    result["confidence"] = max(ours.get("confidence", 0), theirs.get("confidence", 0))

    # Most recent last_validated (compare as datetime, not string)
    ours_dt, ours_lv = parse_ts(ours.get("last_validated", ""))
    theirs_dt, theirs_lv = parse_ts(theirs.get("last_validated", ""))
    if ours_dt and theirs_dt:
        result["last_validated"] = ours_lv if ours_dt >= theirs_dt else theirs_lv
    else:
        result["last_validated"] = ours_lv or theirs_lv

    # Deleted wins
    if ours.get("deleted") or theirs.get("deleted"):
        result["deleted"] = True

    # Tags union
    ours_tags = set(ours.get("tags", []))
    theirs_tags = set(theirs.get("tags", []))
    result["tags"] = sorted(ours_tags | theirs_tags)

    # Text/context/category conflicts
    for field in ("text", "context", "category"):
        ours_val = ours.get(field)
        theirs_val = theirs.get(field)
        anc_val = (ancestor or {}).get(field)
        if ours_val != theirs_val:
            if ours_val != anc_val and theirs_val != anc_val:
                # Both sides changed differently — conflict
                result["needs_review"] = True
            elif theirs_val != anc_val:
                # Only theirs changed — take theirs
                result[field] = theirs_val

    # Supersedes conflicts
    ours_sup = ours.get("supersedes")
    theirs_sup = theirs.get("supersedes")
    if ours_sup and theirs_sup and ours_sup != theirs_sup:
        result["needs_review"] = True
    elif theirs_sup and not ours_sup:
        result["supersedes"] = theirs_sup

    return result


def merge(ancestor_path, ours_path, theirs_path):
    with open(ancestor_path) as f:
        ancestor = {l["id"]: l for l in json.load(f)}
    with open(ours_path) as f:
        ours = {l["id"]: l for l in json.load(f)}
    with open(theirs_path) as f:
        theirs = {l["id"]: l for l in json.load(f)}

    all_ids = set(ancestor) | set(ours) | set(theirs)
    merged = []

    for lid in sorted(all_ids):
        in_ours = lid in ours
        in_theirs = lid in theirs

        if in_ours and in_theirs:
            if ours[lid] == theirs[lid]:
                merged.append(ours[lid])
            else:
                merged.append(merge_lesson(
                    ancestor.get(lid), ours[lid], theirs[lid]
                ))
        elif in_ours:
            merged.append(ours[lid])
        elif in_theirs:
            merged.append(theirs[lid])

    return merged


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <ancestor> <ours> <theirs>", file=sys.stderr)
        sys.exit(1)
    result = merge(sys.argv[1], sys.argv[2], sys.argv[3])
    print(json.dumps(result, indent=2))
