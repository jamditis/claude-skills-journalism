"""Tests for seed-from-claude-md.py"""
import json
import tempfile
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "seed-from-claude-md.py")


def _seed(claude_md_content):
    with tempfile.TemporaryDirectory() as d:
        claude_md = os.path.join(d, "CLAUDE.md")
        lessons_path = os.path.join(d, "lessons.json")
        with open(claude_md, "w") as f:
            f.write(claude_md_content)
        with open(lessons_path, "w") as f:
            json.dump([], f)
        result = subprocess.run(
            [sys.executable, SCRIPT, claude_md, lessons_path],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        with open(lessons_path) as f:
            return json.load(f)


def test_extracts_from_bullet_points():
    md = """# CLAUDE.md
## Key gotchas
- POST /api/ideas/ needs trailing slash
- Always use timeout --foreground in tmux
"""
    lessons = _seed(md)
    assert len(lessons) >= 2
    texts = [l["text"] for l in lessons]
    assert any("trailing slash" in t for t in texts)


def test_skips_short_bullets():
    md = """# CLAUDE.md
- Short
- This is a real lesson about the API requiring trailing slashes
"""
    lessons = _seed(md)
    texts = [l["text"] for l in lessons]
    assert not any("Short" == t for t in texts)
    assert any("trailing slash" in t for t in texts)


def test_assigns_categories():
    md = """# CLAUDE.md
## Architecture
- Belt items use distance-offset struct for O(1) updates
## Bug fixes
- scorer.py escapes curly braces to prevent format() breakage
"""
    lessons = _seed(md)
    categories = {l["category"] for l in lessons}
    assert "codebase" in categories or "efficiency" in categories


def test_empty_claude_md():
    lessons = _seed("# CLAUDE.md\n\nNo specific notes.\n")
    assert isinstance(lessons, list)
    assert len(lessons) == 0


def test_no_duplicates():
    md = """# CLAUDE.md
- Same lesson appears here
- Same lesson appears here
"""
    lessons = _seed(md)
    texts = [l["text"] for l in lessons]
    assert len(texts) == len(set(texts))
