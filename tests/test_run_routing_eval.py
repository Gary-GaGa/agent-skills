"""Tests for scripts/run_routing_eval.py — the lexical scorer.

Each test corresponds to a real bug we hit while building the eval
or to a documented scoring rule. If you change the scorer weights or
the tokenizer you should expect these to fail and update them
intentionally.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import run_routing_eval as rre  # noqa: E402


class TokenizeTests(unittest.TestCase):
    def test_basic_latin_words(self):
        self.assertEqual(rre.tokenize("Hello World"), {"hello", "world"})

    def test_drops_stopwords(self):
        # set/up/a/with are stopwords; only "rust"/"async"/"runtime"/"tokio" survive
        toks = rre.tokenize("Set up a Rust async runtime with tokio")
        self.assertEqual(toks, {"rust", "async", "runtime", "tokio"})

    def test_short_tokens_kept_when_meaningful(self):
        # "go" length-2 is kept (not in stopwords); "a" is dropped
        toks = rre.tokenize("a go program")
        self.assertIn("go", toks)
        self.assertIn("program", toks)
        self.assertNotIn("a", toks)

    def test_cjk_uses_bigrams(self):
        toks = rre.tokenize("我想學習")
        # bigrams of "我想學習" = 我想, 想學, 學習
        self.assertEqual(toks, {"我想", "想學", "學習"})

    def test_mixed_locale(self):
        toks = rre.tokenize("我想學 Python 程式設計")
        self.assertIn("python", toks)
        self.assertIn("程式", toks)
        self.assertIn("式設", toks)

    def test_empty_input(self):
        self.assertEqual(rre.tokenize(""), set())


class HasWordTests(unittest.TestCase):
    """Whole-word matching prevents false matches like sync ⊂ async."""

    def test_sync_does_not_match_async(self):
        self.assertFalse(rre.has_word("set up a rust async runtime", "sync"))

    def test_whole_word_latin_match(self):
        self.assertTrue(rre.has_word("a rust async runtime", "rust"))

    def test_docker_does_not_match_dockerfile(self):
        # Dockerfile is one token; "docker" alone should not whole-word-match it
        self.assertFalse(rre.has_word("write a dockerfile", "docker"))

    def test_dockerfile_matches_itself(self):
        self.assertTrue(rre.has_word("write a dockerfile for go", "dockerfile"))

    def test_go_word_match(self):
        self.assertTrue(rre.has_word("dockerfile for go service", "go"))

    def test_cjk_falls_back_to_substring(self):
        # CJK doesn't have word boundaries; substring fallback is correct
        self.assertTrue(rre.has_word("使用 docker 部署", "使用"))

    def test_kebab_case_tag(self):
        self.assertTrue(rre.has_word("hands-on event-driven systems", "event-driven"))


class ScoreSkillTests(unittest.TestCase):
    def _make(self, **overrides):
        skill = {
            "name": "example-skill",
            "tags": [],
            "keywords": [],
            "description": "",
        }
        skill.update(overrides)
        return skill

    def test_keyword_match_weight_3(self):
        skill = self._make(keywords=["MCP"])
        self.assertEqual(rre.score_skill("design an MCP server", skill), 3.0)

    def test_keyword_case_insensitive_substring(self):
        # Multi-word keyword as substring (case-insensitive)
        skill = self._make(keywords=["Model Context Protocol"])
        self.assertEqual(rre.score_skill("model context protocol design", skill), 3.0)

    def test_tag_match_weight_1(self):
        skill = self._make(tags=["go"])
        self.assertEqual(rre.score_skill("write a go service", skill), 1.0)

    def test_tag_does_not_substring_match(self):
        skill = self._make(tags=["sync"])
        # "sync" is in "async" but should not score
        self.assertEqual(rre.score_skill("rust async runtime", skill), 0.0)

    def test_name_segment_match_weight_0_5(self):
        skill = self._make(name="docker-basics")
        # "docker" appears as whole word? In "docker setup" yes.
        self.assertEqual(rre.score_skill("docker setup", skill), 0.5)

    def test_name_segment_too_short_skipped(self):
        # Segments < 3 chars are not counted as name signals
        skill = self._make(name="go-things")
        score = rre.score_skill("go thing", skill)
        # "go" segment is len 2 → skipped; "things" not in intent → skipped
        # No tag, no kw, no desc → expect 0
        self.assertEqual(score, 0.0)

    def test_description_overlap_weight_0_2(self):
        skill = self._make(description="goroutines and channels")
        # tokens: goroutines, channels (post-stopword); intent has "goroutines"
        score = rre.score_skill("how do goroutines work", skill)
        self.assertAlmostEqual(score, 0.2)

    def test_combined_signals(self):
        skill = self._make(
            name="mcp-server-design",
            tags=["mcp", "agent"],
            keywords=["MCP"],
            description="Designing Model Context Protocol servers",
        )
        score = rre.score_skill("design an mcp server", skill)
        # kw "MCP" hit (3.0), tag "mcp" word (1.0), name "mcp" len 3 word (0.5),
        # desc overlap on "server"/"design"/"mcp" tokens (some count).
        self.assertGreaterEqual(score, 4.5)


class AggregateTests(unittest.TestCase):
    def _match_case(self, in_top1=True, in_top3=True, rr=1.0, kind="match"):
        return {"kind": kind, "in_top1": in_top1, "in_top3": in_top3, "rr": rr, "passed": in_top1}

    def test_empty(self):
        out = rre.aggregate([])
        self.assertEqual(out["recall_at_1"], 0.0)
        self.assertEqual(out["mrr"], 0.0)

    def test_perfect_match_set(self):
        cases = [self._match_case() for _ in range(5)]
        out = rre.aggregate(cases)
        self.assertEqual(out["recall_at_1"], 1.0)
        self.assertEqual(out["recall_at_3"], 1.0)
        self.assertEqual(out["mrr"], 1.0)

    def test_partial_recall(self):
        cases = [
            self._match_case(in_top1=True, in_top3=True, rr=1.0),
            self._match_case(in_top1=False, in_top3=True, rr=0.5),  # at rank 2
            self._match_case(in_top1=False, in_top3=False, rr=0.0),
        ]
        out = rre.aggregate(cases)
        self.assertAlmostEqual(out["recall_at_1"], 1 / 3)
        self.assertAlmostEqual(out["recall_at_3"], 2 / 3)
        self.assertAlmostEqual(out["mrr"], (1.0 + 0.5 + 0.0) / 3)

    def test_unanswerable_split(self):
        cases = [
            self._match_case(),  # match
            {"kind": "unanswerable", "passed": True},
            {"kind": "unanswerable", "passed": False},
        ]
        out = rre.aggregate(cases)
        self.assertEqual(out["match_total"], 1)
        self.assertEqual(out["unanswerable_total"], 2)
        self.assertEqual(out["unanswerable_correct"], 1)
        self.assertAlmostEqual(out["unanswerable_accuracy"], 0.5)


class FmtDiffTests(unittest.TestCase):
    def test_no_diff_returns_empty(self):
        self.assertEqual(rre.fmt_diff(0.5, 0.5), "")

    def test_positive_diff_arrow_up(self):
        out = rre.fmt_diff(0.6, 0.5, pct=True)
        self.assertIn("↑", out)
        self.assertIn("10.0%", out)

    def test_negative_diff_arrow_down(self):
        out = rre.fmt_diff(0.4, 0.5, pct=True)
        self.assertIn("↓", out)
        self.assertIn("10.0%", out)


if __name__ == "__main__":
    unittest.main()
