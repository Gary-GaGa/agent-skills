"""Tests for scripts/validate.py — focused on the helpers that proved
brittle during the build (code stripping, marker regex, schema check).
The high-level pipeline (collect_all_skills, drift checks) is covered
by `python3 scripts/validate.py` running in CI."""
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate  # noqa: E402


class StripCodeTests(unittest.TestCase):
    def test_fenced_block_removed(self):
        text = "before\n```python\ncode here\n```\nafter"
        out = validate._strip_code(text)
        self.assertNotIn("code here", out)
        self.assertIn("before", out)
        self.assertIn("after", out)

    def test_inline_code_preserved(self):
        # copilot-sdk wraps real reference filenames in backticks; we must
        # NOT strip inline code or those mentions disappear.
        text = "see `references/foo.md` for details"
        out = validate._strip_code(text)
        self.assertIn("references/foo.md", out)

    def test_multiple_fenced_blocks(self):
        text = "a\n```\none\n```\nb\n```\ntwo\n```\nc"
        out = validate._strip_code(text)
        self.assertNotIn("one", out)
        self.assertNotIn("two", out)
        self.assertIn("a", out)
        self.assertIn("b", out)
        self.assertIn("c", out)


class MarkerRegexTests(unittest.TestCase):
    def test_canonical_begin_marker(self):
        m = validate.MARKER_BEGIN_RE.search("<!-- BEGIN AUTO-GENERATED: summary -->")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "summary")

    def test_kebab_case_id(self):
        m = validate.MARKER_BEGIN_RE.search("<!-- BEGIN AUTO-GENERATED: skills-table -->")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "skills-table")

    def test_does_not_match_ellipsis_id(self):
        # README explains the convention with "<!-- BEGIN AUTO-GENERATED: ... -->"
        # — the literal "..." should not be captured as a real ID.
        m = validate.MARKER_BEGIN_RE.search("<!-- BEGIN AUTO-GENERATED: ... -->")
        self.assertIsNone(m)

    def test_end_matches(self):
        m = validate.MARKER_END_RE.search("<!-- END AUTO-GENERATED: summary -->")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "summary")


class FrontmatterTests(unittest.TestCase):
    """validate.parse_frontmatter calls path.relative_to(REPO_ROOT) when
    reporting errors, so test files must live under REPO_ROOT."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=REPO_ROOT)
        self.addCleanup(self._tmp.cleanup)
        self.tmpdir = Path(self._tmp.name)

    def _write(self, body: str) -> Path:
        path = self.tmpdir / "skill.md"
        path.write_text(body, encoding="utf-8")
        return path

    def test_parses_simple_frontmatter(self):
        path = self._write("---\nname: foo\ncategory: engineering\n---\nbody\n")
        fm = validate.parse_frontmatter(path)
        self.assertEqual(fm["name"], "foo")
        self.assertEqual(fm["category"], "engineering")

    def test_missing_frontmatter_records_error(self):
        validate.errors.clear()
        path = self._write("no frontmatter here\n")
        out = validate.parse_frontmatter(path)
        self.assertIsNone(out)
        self.assertTrue(any("missing frontmatter" in e for e in validate.errors))


class AllowedFieldsTests(unittest.TestCase):
    def test_known_set(self):
        # Required + optional combined; unknown fields should be flagged.
        self.assertEqual(
            validate.ALLOWED_FIELDS,
            {
                "name", "description", "category", "tags", "keywords", "related",
                "last_verified", "freshness_budget",
            },
        )


if __name__ == "__main__":
    unittest.main()
