"""Tests for scripts/render_docs.py — marker block replacement and
table rendering against a synthetic manifest."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import render_docs  # noqa: E402


def _fake_manifest():
    return {
        "schema_version": 1,
        "categories": [
            {"name": "engineering", "title": "Engineering", "description": "Eng stuff.", "skill_count": 1},
            {"name": "data", "title": "Data", "description": "Data stuff.", "skill_count": 1},
        ],
        "skills": [
            {
                "name": "go-testing",
                "category": "engineering",
                "description": "Test patterns for Go.",
                "tags": ["go", "testing"],
                "keywords": [],
                "related": [],
                "path": "engineering/go-testing/SKILL.md",
                "body_lines": 100,
                "references": [],
            },
            {
                "name": "sql-fundamentals",
                "category": "data",
                "description": "SQL basics.",
                "tags": ["sql"],
                "keywords": ["PostgreSQL"],
                "related": [],
                "path": "data/sql-fundamentals/SKILL.md",
                "body_lines": 80,
                "references": [],
            },
        ],
        "rules": [
            {"name": "go-naming", "path": "rules/go-naming.md", "topic": "Go naming."},
        ],
        "totals": {"skills": 2, "rules": 1, "categories": 2},
    }


class ReplaceBlockTests(unittest.TestCase):
    def test_replaces_block_content(self):
        text = (
            "intro\n"
            "<!-- BEGIN AUTO-GENERATED: x -->\n"
            "old content\n"
            "<!-- END AUTO-GENERATED: x -->\n"
            "outro\n"
        )
        out = render_docs.replace_block(text, "x", "new content")
        self.assertIn("new content", out)
        self.assertNotIn("old content", out)
        # markers preserved
        self.assertIn("BEGIN AUTO-GENERATED: x", out)
        self.assertIn("END AUTO-GENERATED: x", out)
        # surrounding text preserved
        self.assertIn("intro", out)
        self.assertIn("outro", out)

    def test_missing_block_raises(self):
        with self.assertRaises(ValueError):
            render_docs.replace_block("no markers here", "x", "new")

    def test_only_target_block_replaced(self):
        text = (
            "<!-- BEGIN AUTO-GENERATED: a -->\nA\n<!-- END AUTO-GENERATED: a -->\n"
            "<!-- BEGIN AUTO-GENERATED: b -->\nB\n<!-- END AUTO-GENERATED: b -->\n"
        )
        out = render_docs.replace_block(text, "b", "NEW")
        self.assertIn("\nA\n", out)  # block a untouched
        self.assertIn("NEW", out)
        self.assertNotIn("\nB\n", out)


class RenderTableTests(unittest.TestCase):
    def test_categories_table_lists_each_category(self):
        out = render_docs.render_categories_table(_fake_manifest())
        self.assertIn("[engineering]", out)
        self.assertIn("[data]", out)
        self.assertIn("[rules]", out)  # rules row appended

    def test_index_table_has_full_description(self):
        out = render_docs.render_index_table(_fake_manifest(), "engineering")
        self.assertIn("go-testing", out)
        self.assertIn("Test patterns for Go.", out)
        # not other categories
        self.assertNotIn("sql-fundamentals", out)

    def test_repo_summary_includes_totals(self):
        summary = render_docs.render_repo_summary(_fake_manifest())
        self.assertIn("**2 skills**", summary)
        self.assertIn("**1 rule sheets**", summary)


if __name__ == "__main__":
    unittest.main()
