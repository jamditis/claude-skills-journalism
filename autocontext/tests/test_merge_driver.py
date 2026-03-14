"""Tests for merge-driver.py — lessons.json three-way merge."""
import json
import tempfile
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "merge-driver.py")


def _merge(ancestor, ours, theirs):
    with tempfile.TemporaryDirectory() as d:
        paths = {}
        for name, data in [("ancestor", ancestor), ("ours", ours), ("theirs", theirs)]:
            p = os.path.join(d, f"{name}.json")
            with open(p, "w") as f:
                json.dump(data, f)
            paths[name] = p
        result = subprocess.run(
            [sys.executable, SCRIPT, paths["ancestor"], paths["ours"], paths["theirs"]],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Merge failed: {result.stderr}"
        return json.loads(result.stdout)


def test_union_new_lessons():
    ancestor = []
    ours = [{"id": "a", "text": "lesson A", "validated_count": 1, "confidence": 0.5,
             "deleted": False, "tags": ["x"]}]
    theirs = [{"id": "b", "text": "lesson B", "validated_count": 1, "confidence": 0.5,
               "deleted": False, "tags": ["y"]}]
    merged = _merge(ancestor, ours, theirs)
    ids = {l["id"] for l in merged}
    assert ids == {"a", "b"}


def test_additive_validated_count():
    ancestor = [{"id": "a", "text": "lesson", "validated_count": 5, "confidence": 0.7,
                 "deleted": False, "tags": [], "last_validated": "2026-03-01T00:00:00Z"}]
    ours = [{"id": "a", "text": "lesson", "validated_count": 7, "confidence": 0.8,
             "deleted": False, "tags": [], "last_validated": "2026-03-10T00:00:00Z"}]
    theirs = [{"id": "a", "text": "lesson", "validated_count": 8, "confidence": 0.75,
               "deleted": False, "tags": [], "last_validated": "2026-03-12T00:00:00Z"}]
    merged = _merge(ancestor, ours, theirs)
    lesson = merged[0]
    # ours added 2, theirs added 3, total from ancestor = 5 + 2 + 3 = 10
    assert lesson["validated_count"] == 10
    assert lesson["confidence"] == 0.8  # higher wins
    assert lesson["last_validated"] == "2026-03-12T00:00:00Z"  # most recent


def test_deleted_wins():
    ancestor = [{"id": "a", "text": "lesson", "validated_count": 1, "confidence": 0.5,
                 "deleted": False, "tags": []}]
    ours = [{"id": "a", "text": "lesson", "validated_count": 1, "confidence": 0.5,
             "deleted": True, "tags": []}]
    theirs = [{"id": "a", "text": "lesson", "validated_count": 2, "confidence": 0.6,
               "deleted": False, "tags": []}]
    merged = _merge(ancestor, ours, theirs)
    assert merged[0]["deleted"] is True


def test_tags_union():
    ancestor = [{"id": "a", "text": "lesson", "validated_count": 1, "confidence": 0.5,
                 "deleted": False, "tags": ["common"]}]
    ours = [{"id": "a", "text": "lesson", "validated_count": 1, "confidence": 0.5,
             "deleted": False, "tags": ["common", "ours-tag"]}]
    theirs = [{"id": "a", "text": "lesson", "validated_count": 1, "confidence": 0.5,
               "deleted": False, "tags": ["common", "theirs-tag"]}]
    merged = _merge(ancestor, ours, theirs)
    assert set(merged[0]["tags"]) == {"common", "ours-tag", "theirs-tag"}


def test_text_conflict_flags_review():
    ancestor = [{"id": "a", "text": "original text", "validated_count": 1, "confidence": 0.5,
                 "deleted": False, "tags": []}]
    ours = [{"id": "a", "text": "our edit", "validated_count": 1, "confidence": 0.5,
             "deleted": False, "tags": []}]
    theirs = [{"id": "a", "text": "their edit", "validated_count": 1, "confidence": 0.5,
               "deleted": False, "tags": []}]
    merged = _merge(ancestor, ours, theirs)
    assert merged[0].get("needs_review") is True


def test_one_side_text_change_no_conflict():
    """If only one side changed text, take that change without flagging."""
    ancestor = [{"id": "a", "text": "original", "validated_count": 1, "confidence": 0.5,
                 "deleted": False, "tags": []}]
    ours = [{"id": "a", "text": "updated text", "validated_count": 1, "confidence": 0.5,
             "deleted": False, "tags": []}]
    theirs = [{"id": "a", "text": "original", "validated_count": 1, "confidence": 0.5,
               "deleted": False, "tags": []}]
    merged = _merge(ancestor, ours, theirs)
    assert merged[0]["text"] == "updated text"
    assert merged[0].get("needs_review") is not True
