#!/usr/bin/env python3
"""Tests for the global skill lesson store."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "skill-evolution"))
from store import (
    ensure_store, load_index, load_skill_lessons, save_skill_lessons,
    promote_lesson, get_eligible_lessons, mark_folded,
)


class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store = os.path.join(self.tmpdir, "skill-lessons")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_ensure_store_creates_structure(self):
        path = ensure_store(self.store)
        self.assertTrue(os.path.isdir(path))
        self.assertTrue(os.path.isdir(os.path.join(path, "backups")))
        self.assertTrue(os.path.isdir(os.path.join(path, "exports")))
        self.assertTrue(os.path.isfile(os.path.join(path, "index.json")))

    def test_promote_lesson(self):
        ensure_store(self.store)
        lesson = {
            "id": "lesson_abc123",
            "text": "Use Selenium for JS-heavy sites",
            "confidence": 0.9,
            "validated_count": 5,
        }
        result = promote_lesson(lesson, "web-scraping", "rosen-frontend", self.store)
        self.assertTrue(result)

        lessons = load_skill_lessons("web-scraping", self.store)
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["text"], "Use Selenium for JS-heavy sites")
        self.assertEqual(lessons[0]["source_projects"], ["rosen-frontend"])

        # Dedup
        result2 = promote_lesson(lesson, "web-scraping", "rosen-frontend", self.store)
        self.assertFalse(result2)
        self.assertEqual(len(load_skill_lessons("web-scraping", self.store)), 1)

    def test_get_eligible_lessons(self):
        ensure_store(self.store)
        lessons = [
            {"id": "sl_1", "text": "High conf", "confidence": 0.92, "validated_count": 5, "folded": False},
            {"id": "sl_2", "text": "Low conf", "confidence": 0.5, "validated_count": 1, "folded": False},
            {"id": "sl_3", "text": "Already folded", "confidence": 0.95, "validated_count": 10, "folded": True},
        ]
        save_skill_lessons("test-skill", lessons, self.store)

        eligible = get_eligible_lessons("test-skill", 0.85, 3, self.store)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0]["id"], "sl_1")

    def test_mark_folded(self):
        ensure_store(self.store)
        lessons = [
            {"id": "sl_1", "text": "Fold me", "confidence": 0.9, "validated_count": 5, "folded": False},
            {"id": "sl_2", "text": "Keep me", "confidence": 0.9, "validated_count": 5, "folded": False},
        ]
        save_skill_lessons("test-skill", lessons, self.store)

        mark_folded("test-skill", ["sl_1"], self.store)
        updated = load_skill_lessons("test-skill", self.store)
        self.assertTrue(updated[0]["folded"])
        self.assertFalse(updated[1]["folded"])

    def test_index_updated_on_save(self):
        ensure_store(self.store)
        lessons = [{"id": "sl_1", "text": "Test", "confidence": 0.9, "validated_count": 5, "folded": False}]
        save_skill_lessons("web-scraping", lessons, self.store)

        index = load_index(self.store)
        self.assertIn("web-scraping", index["skills"])
        self.assertEqual(index["skills"]["web-scraping"]["lesson_count"], 1)


if __name__ == "__main__":
    unittest.main()
