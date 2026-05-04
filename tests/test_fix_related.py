"""Tests for scripts/fix_related.py — single-line related list editor."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import fix_related  # noqa: E402


SAMPLE = """---
name: foo
description: bar
category: engineering
tags: [a]
related: [x, y]
---

# Body
"""


class AddRelatedTests(unittest.TestCase):
    def _write(self, body: str) -> Path:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
        f.write(body)
        f.close()
        path = Path(f.name)
        self.addCleanup(path.unlink)
        return path

    def test_appends_new_entry(self):
        path = self._write(SAMPLE)
        fix_related.add_related(path, ["z"])
        text = path.read_text(encoding="utf-8")
        self.assertIn("related: [x, y, z]", text)

    def test_idempotent(self):
        path = self._write(SAMPLE)
        fix_related.add_related(path, ["x"])  # already present
        text = path.read_text(encoding="utf-8")
        self.assertIn("related: [x, y]", text)
        self.assertEqual(text.count("[x"), 1)

    def test_multiple_appends(self):
        path = self._write(SAMPLE)
        fix_related.add_related(path, ["m", "n"])
        text = path.read_text(encoding="utf-8")
        self.assertIn("related: [x, y, m, n]", text)

    def test_empty_related_list(self):
        body = SAMPLE.replace("related: [x, y]", "related: []")
        path = self._write(body)
        fix_related.add_related(path, ["z"])
        text = path.read_text(encoding="utf-8")
        self.assertIn("related: [z]", text)


if __name__ == "__main__":
    unittest.main()
