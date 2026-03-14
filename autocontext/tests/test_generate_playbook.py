"""Tests for generate-playbook.py"""
import json
import tempfile
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "generate-playbook.py")


def _run(lessons_data, expect_success=True):
    with tempfile.TemporaryDirectory() as d:
        lessons_path = os.path.join(d, "lessons.json")
        playbook_path = os.path.join(d, "playbook.md")
        with open(lessons_path, "w") as f:
            json.dump(lessons_data, f)
        result = subprocess.run(
            [sys.executable, SCRIPT, lessons_path, playbook_path],
            capture_output=True, text=True,
        )
        if expect_success:
            assert result.returncode == 0, f"Failed: {result.stderr}"
            with open(playbook_path) as f:
                return f.read()
        return result


def test_empty_lessons():
    playbook = _run([])
    assert "0 active lessons" in playbook


def test_groups_by_category():
    lessons = [
        {"id": "a", "category": "efficiency", "text": "Use trailing slash", "confidence": 0.9,
         "validated_count": 3, "tags": ["api"], "deleted": False},
        {"id": "b", "category": "codebase", "text": "Schema uses UUID", "confidence": 0.8,
         "validated_count": 1, "tags": ["db"], "deleted": False},
    ]
    playbook = _run(lessons)
    assert "## Efficiency" in playbook
    assert "## Codebase" in playbook
    assert "Use trailing slash" in playbook
    assert "Schema uses UUID" in playbook


def test_excludes_deleted():
    lessons = [
        {"id": "a", "category": "efficiency", "text": "Active lesson", "confidence": 0.9,
         "validated_count": 1, "tags": [], "deleted": False},
        {"id": "b", "category": "efficiency", "text": "Deleted lesson", "confidence": 0.5,
         "validated_count": 0, "tags": [], "deleted": True},
    ]
    playbook = _run(lessons)
    assert "Active lesson" in playbook
    assert "Deleted lesson" not in playbook
    assert "1 active lessons" in playbook


def test_sorts_by_confidence():
    lessons = [
        {"id": "a", "category": "efficiency", "text": "Low conf", "confidence": 0.3,
         "validated_count": 1, "tags": [], "deleted": False},
        {"id": "b", "category": "efficiency", "text": "High conf", "confidence": 0.9,
         "validated_count": 5, "tags": [], "deleted": False},
    ]
    playbook = _run(lessons)
    high_pos = playbook.index("High conf")
    low_pos = playbook.index("Low conf")
    assert high_pos < low_pos


def test_shows_confidence_and_tags():
    lessons = [
        {"id": "a", "category": "optimization", "text": "Cache is slow", "confidence": 0.75,
         "validated_count": 2, "tags": ["perf", "cache"], "deleted": False},
    ]
    playbook = _run(lessons)
    assert "[0.75]" in playbook
    assert "perf" in playbook
