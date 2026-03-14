#!/usr/bin/env python3
"""Tests for evolution engine components."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "skill-evolution"))
from apply_edit import backup_skill, apply_edit, rollback
from generate_diff import generate_append_fallback


class TestApplyEdit(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.skill_path = os.path.join(self.tmpdir, "SKILL.md")
        self.backup_dir = os.path.join(self.tmpdir, "backups")
        with open(self.skill_path, "w") as f:
            f.write("# Original content\n\nSome guidance here.\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_backup_creates_file(self):
        backup_path = backup_skill(self.skill_path, self.backup_dir)
        self.assertTrue(os.path.exists(backup_path))
        with open(backup_path) as f:
            self.assertIn("Original content", f.read())

    def test_apply_edit_writes_and_backs_up(self):
        new_content = "# Updated content\n\nBetter guidance.\n"
        backup_path, success = apply_edit(self.skill_path, new_content, self.backup_dir)
        self.assertTrue(success)
        with open(self.skill_path) as f:
            self.assertEqual(f.read(), new_content)
        self.assertTrue(os.path.exists(backup_path))


class TestAppendFallback(unittest.TestCase):
    def test_generates_markdown(self):
        lessons = [
            {"text": "Use Selenium for JS sites", "confidence": 0.92, "source_projects": ["proj-a"]},
            {"text": "Set User-Agent header", "confidence": 0.88, "source_projects": ["proj-b"]},
        ]
        result = generate_append_fallback(lessons)
        self.assertIn("## Learned patterns", result)
        self.assertIn("Use Selenium", result)
        self.assertIn("Set User-Agent", result)
        self.assertIn("proj-a", result)


if __name__ == "__main__":
    unittest.main()
