#!/usr/bin/env python3
"""Tests for export/import sync."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "skill-evolution"))
from sync import export_all, import_lessons
from store import ensure_store, save_skill_lessons, load_skill_lessons


class TestSync(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.store_a = os.path.join(self.tmpdir, "store-a")
        self.store_b = os.path.join(self.tmpdir, "store-b")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir)

    def test_export_import_round_trip(self):
        ensure_store(self.store_a)
        lessons = [
            {"id": "sl_1", "text": "Lesson one", "confidence": 0.9,
             "validated_count": 3, "source_projects": ["proj-a"],
             "folded": False, "last_validated": "2026-03-14T10:00:00Z"},
        ]
        save_skill_lessons("web-scraping", lessons, self.store_a)

        export_path = export_all(self.store_a)
        self.assertTrue(os.path.exists(export_path))

        # Import into a fresh store
        ensure_store(self.store_b)
        summary = import_lessons(export_path, self.store_b)
        self.assertEqual(summary["web-scraping"]["added"], 1)

        imported = load_skill_lessons("web-scraping", self.store_b)
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0]["text"], "Lesson one")

    def test_union_merge_semantics(self):
        ensure_store(self.store_b)
        existing = [
            {"id": "sl_1", "text": "Lesson one", "confidence": 0.8,
             "validated_count": 2, "source_projects": ["proj-a"],
             "folded": False, "last_validated": "2026-03-10T10:00:00Z"},
        ]
        save_skill_lessons("web-scraping", existing, self.store_b)

        # Create an export with higher confidence and more validations
        export_data = {
            "exported": "2026-03-14T10:00:00Z",
            "skills": {
                "web-scraping": [
                    {"id": "sl_1", "text": "Lesson one", "confidence": 0.95,
                     "validated_count": 5, "source_projects": ["proj-b"],
                     "folded": False, "last_validated": "2026-03-14T10:00:00Z"},
                    {"id": "sl_2", "text": "New lesson", "confidence": 0.7,
                     "validated_count": 1, "source_projects": ["proj-b"],
                     "folded": False, "last_validated": "2026-03-14T10:00:00Z"},
                ],
            },
        }
        export_path = os.path.join(self.tmpdir, "import.json")
        with open(export_path, "w") as f:
            json.dump(export_data, f)

        summary = import_lessons(export_path, self.store_b)
        self.assertEqual(summary["web-scraping"]["added"], 1)
        self.assertEqual(summary["web-scraping"]["merged"], 1)

        merged = load_skill_lessons("web-scraping", self.store_b)
        sl_1 = next(l for l in merged if l["id"] == "sl_1")
        # Additive validated_count
        self.assertEqual(sl_1["validated_count"], 7)  # 2 + 5
        # Highest confidence
        self.assertEqual(sl_1["confidence"], 0.95)
        # Union projects
        self.assertIn("proj-a", sl_1["source_projects"])
        self.assertIn("proj-b", sl_1["source_projects"])


if __name__ == "__main__":
    unittest.main()
