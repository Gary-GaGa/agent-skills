"""Tests for scripts/build_manifest.py — path normalization and frontmatter parser."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_manifest  # noqa: E402


class RelTests(unittest.TestCase):
    def test_uses_forward_slashes(self):
        # Whatever the host OS, manifest paths must use /
        path = build_manifest.REPO_ROOT / "engineering" / "go-testing" / "SKILL.md"
        rel = build_manifest._rel(path)
        self.assertNotIn("\\", rel)
        self.assertEqual(rel, "engineering/go-testing/SKILL.md")


class ParseFrontmatterTests(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        path = Path(f.name)
        self.addCleanup(path.unlink)
        return path

    def test_returns_dict_and_body_line_count(self):
        path = self._write("---\nname: foo\ndescription: bar\n---\nline 1\nline 2\n")
        fm, body_lines = build_manifest.parse_frontmatter(path)
        self.assertEqual(fm["name"], "foo")
        self.assertEqual(fm["description"], "bar")
        # body has 2 newlines
        self.assertEqual(body_lines, 2)

    def test_missing_frontmatter_raises(self):
        path = self._write("no frontmatter here\n")
        with self.assertRaises(ValueError):
            build_manifest.parse_frontmatter(path)

    def test_non_mapping_frontmatter_raises(self):
        # Frontmatter as a list, not a mapping
        path = self._write("---\n- a\n- b\n---\nbody\n")
        with self.assertRaises(ValueError):
            build_manifest.parse_frontmatter(path)


if __name__ == "__main__":
    unittest.main()
