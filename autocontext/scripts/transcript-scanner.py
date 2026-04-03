#!/usr/bin/env python3
"""
transcript-scanner.py — scan a Claude Code session transcript for meaningful activity.

Usage:
    python3 transcript-scanner.py --transcript /path/to/session.jsonl [--since UNIX_TS] [--config path/to/config.json]

Output (JSON to stdout):
    {"meaningful": true/false, "level": "high"/"medium"/"none",
     "signals": [{"type": "...", "detail": "...", "ts": ...}, ...],
     "tool_counts": {"Write": 1, "Read": 5, ...}}
"""

import argparse
import json
import os
import sys

# ── Default signal classification ─────────────────────────────────────────────

DEFAULT_HIGH_TOOL_NAMES = ["Write", "Edit"]
DEFAULT_MEDIUM_TOOL_NAMES = ["Agent"]

DEFAULT_HIGH_BASH_PATTERNS = [
    "git commit",
    "gh pr create",
    "gh pr merge",
    "firebase deploy",
    "systemctl restart",
    "systemctl stop",
    "systemctl start",
]

DEFAULT_MEDIUM_BASH_PATTERNS = [
    "git push",
    "npm run build",
    "cargo build",
    "pip install",
    "npm install",
]

# Tools whose names contain these strings are high-signal (email tools)
HIGH_TOOL_NAME_SUBSTRINGS = ["email", "compose"]

NOT_MEANINGFUL_TOOLS = {"Read", "Grep", "Glob"}


def not_meaningful_result():
    return {"meaningful": False, "level": "none", "signals": [], "tool_counts": {}}


def load_config(config_path):
    """Load optional config file and return activity_signals overrides (or empty dict)."""
    if not config_path:
        return {}
    try:
        with open(config_path) as f:
            cfg = json.load(f)
        return cfg.get("activity_signals", {})
    except Exception as e:
        sys.stderr.write(f"[transcript-scanner] warning: could not read config: {e}\n")
        return {}


def build_classifiers(overrides):
    """Return (high_tools, medium_tools, high_bash, medium_bash) using overrides where present."""
    high_tools = set(overrides.get("high_tool_names", DEFAULT_HIGH_TOOL_NAMES))
    medium_tools = set(overrides.get("medium_tool_names", DEFAULT_MEDIUM_TOOL_NAMES))
    high_bash = overrides.get("high_bash_patterns", DEFAULT_HIGH_BASH_PATTERNS)
    medium_bash = overrides.get("medium_bash_patterns", DEFAULT_MEDIUM_BASH_PATTERNS)
    return high_tools, medium_tools, high_bash, medium_bash


def classify_tool_use(name, inp, high_tools, medium_tools, high_bash, medium_bash):
    """
    Returns (tier, detail) where tier is "high", "medium", or None.
    inp is the tool_use input dict.
    """
    # Explicit high tool names
    if name in high_tools:
        detail = inp.get("file_path", "")
        return "high", detail

    # Explicit medium tool names
    if name in medium_tools:
        raw = inp.get("description") or inp.get("prompt") or ""
        detail = raw[:120]
        return "medium", detail

    # Email/compose tools (substring match on name) — high
    name_lower = name.lower()
    if any(sub in name_lower for sub in HIGH_TOOL_NAME_SUBSTRINGS):
        return "high", name

    # Bash — check patterns
    if name == "Bash":
        command = inp.get("command", "")
        detail = command[:120]
        for pattern in high_bash:
            if pattern in command:
                return "high", detail
        for pattern in medium_bash:
            if pattern in command:
                return "medium", detail
        # Unmatched Bash — no signal
        return None, detail

    # Low-signal tools (no trigger)
    return None, ""


def scan(transcript_path, since_ts, overrides):
    """
    Parse the JSONL transcript and return the result dict.
    since_ts: float seconds (epoch). Entries with ts_ms/1000 < since_ts are skipped.
              Entries with no ts field are always included (fail-open).
    """
    high_tools, medium_tools, high_bash, medium_bash = build_classifiers(overrides)

    signals = []
    tool_counts = {}
    has_high = False
    has_medium = False

    try:
        with open(transcript_path) as f:
            lines = f.readlines()
    except Exception as e:
        sys.stderr.write(f"[transcript-scanner] could not read transcript: {e}\n")
        return not_meaningful_result()

    for raw_line in lines:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError:
            continue

        # Only process assistant entries
        if entry.get("type") != "assistant":
            continue

        # Timestamp filtering (fail-open: no ts = always include)
        ts_ms = entry.get("ts")
        if since_ts is not None and ts_ms is not None:
            if ts_ms / 1000 < since_ts:
                continue
        # ts_ms is the entry-level ts we store in signals
        entry_ts = ts_ms

        # Walk content array for tool_use blocks
        content = entry.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue

        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue

            name = block.get("name", "")
            inp = block.get("input", {})
            if not isinstance(inp, dict):
                inp = {}

            # Count all tool uses
            tool_counts[name] = tool_counts.get(name, 0) + 1

            tier, detail = classify_tool_use(
                name, inp, high_tools, medium_tools, high_bash, medium_bash
            )

            if tier == "high":
                has_high = True
                signals.append({"type": name, "detail": detail, "ts": entry_ts})
            elif tier == "medium":
                has_medium = True
                signals.append({"type": name, "detail": detail, "ts": entry_ts})

    # Determine overall level
    if has_high:
        level = "high"
    elif has_medium:
        level = "medium"
    else:
        level = "none"

    meaningful = has_high or has_medium

    return {
        "meaningful": meaningful,
        "level": level,
        "signals": signals,
        "tool_counts": tool_counts,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scan a Claude Code transcript for meaningful activity."
    )
    parser.add_argument("--transcript", help="Path to session JSONL transcript")
    parser.add_argument(
        "--since",
        type=float,
        default=None,
        help="Only consider entries after this Unix timestamp (seconds)",
    )
    parser.add_argument("--config", help="Path to config JSON with activity_signals overrides")

    args = parser.parse_args()

    # No transcript path → not meaningful
    if not args.transcript:
        print(json.dumps(not_meaningful_result()))
        return

    # Missing file → not meaningful
    if not os.path.exists(args.transcript):
        print(json.dumps(not_meaningful_result()))
        return

    overrides = load_config(args.config)
    result = scan(args.transcript, args.since, overrides)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
