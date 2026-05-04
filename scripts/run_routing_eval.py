#!/usr/bin/env python3
"""Run the skill-routing eval.

Reads evals/skill-routing.jsonl and scores each test case against the
manifest with a lightweight lexical scorer (no LLM, no network). Reports
recall@1, recall@3, MRR, and unanswerable handling.

Scoring (per skill, given an intent):
    +3.0  per `keywords` entry whose lowercased form appears as a substring
    +1.0  per `tags` entry whose lowercased form appears in the intent
    +0.5  per `name` segment (split by `-`, length >= 3) in the intent
    +0.2  per overlapping token between intent and description (sets, no stopwords)

Tokenizer:
    - Latin: lowercase word-like runs of length >= 2
    - CJK: character bigrams (covers Chinese without a segmenter)

Usage:
    python3 scripts/run_routing_eval.py
    python3 scripts/run_routing_eval.py --verbose   # print top-3 per case
    python3 scripts/run_routing_eval.py --json      # machine-readable summary
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills.json"
EVAL_PATH = REPO_ROOT / "evals" / "skill-routing.jsonl"

UNANSWERABLE_THRESHOLD = 1.0  # top score below this -> "no skill matches"

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "for", "in", "on", "at",
    "use", "this", "skill", "with", "is", "are", "be", "by", "as", "from",
    "how", "do", "i", "my", "we", "you", "your", "it", "that", "can",
    "want", "need", "help", "me", "what", "when", "where", "why",
    "set", "up", "get", "got", "make", "made", "let", "lets", "have", "has",
    "用", "的", "是", "有", "在", "和", "與", "我", "你", "他", "怎",
    "麼", "想", "要", "如", "何",
}


def tokenize(text: str) -> set[str]:
    text = text.lower()
    out: set[str] = set()
    for m in re.findall(r"[a-z][a-z0-9_+#\-]{1,}", text):
        out.add(m.strip("-_"))
    for run in re.findall(r"[一-鿿]+", text):
        if len(run) == 1:
            out.add(run)
        else:
            for i in range(len(run) - 1):
                out.add(run[i:i + 2])
    return {t for t in out if t and t not in STOPWORDS}


def has_word(haystack_lower: str, needle: str) -> bool:
    """Whole-word match for Latin tokens; substring fallback for CJK."""
    n = needle.lower()
    if re.fullmatch(r"[a-z0-9_+#\-]+", n):
        return re.search(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", haystack_lower) is not None
    return n in haystack_lower


def score_skill(intent: str, skill: dict) -> float:
    intent_lower = intent.lower()
    s = 0.0
    # keywords: substring match preserves intent (proper nouns, multi-word phrases)
    for kw in skill.get("keywords") or []:
        if kw.lower() in intent_lower:
            s += 3.0
    # tags: whole-word for Latin so `sync` doesn't match `async`
    for tag in skill.get("tags") or []:
        if has_word(intent_lower, tag):
            s += 1.0
    # name segments
    for part in skill["name"].split("-"):
        if len(part) >= 3 and has_word(intent_lower, part):
            s += 0.5
    # description token overlap (post-stopwords)
    intent_tokens = tokenize(intent)
    desc_tokens = tokenize(skill.get("description", ""))
    overlap = intent_tokens & desc_tokens
    s += 0.2 * len(overlap)
    return s


def rank(intent: str, skills: list[dict]) -> list[tuple[float, dict]]:
    scored = [(score_skill(intent, s), s) for s in skills]
    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    return scored


def load_cases() -> list[dict]:
    if not EVAL_PATH.exists():
        sys.exit(f"error: {EVAL_PATH} not found")
    cases = []
    for i, line in enumerate(EVAL_PATH.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as e:
            sys.exit(f"{EVAL_PATH}:{i}: invalid JSON: {e}")
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print top-3 per case")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        sys.exit(f"error: {MANIFEST_PATH} missing; run scripts/build_manifest.py")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    skills = manifest["skills"]
    cases = load_cases()

    n_total = len(cases)
    n_match = sum(1 for c in cases if c.get("kind") != "unanswerable")
    n_unanswerable = n_total - n_match

    hits_at_1 = 0
    hits_at_3 = 0
    rr_sum = 0.0
    unanswerable_correct = 0
    failures: list[dict] = []

    for case in cases:
        intent = case["intent"]
        expected: list[str] = case.get("expected", [])
        kind = case.get("kind", "match")
        ranked = rank(intent, skills)
        top_score = ranked[0][0] if ranked else 0.0
        top_names = [s["name"] for _, s in ranked[:3]]

        if kind == "unanswerable":
            ok = top_score < UNANSWERABLE_THRESHOLD
            if ok:
                unanswerable_correct += 1
            else:
                failures.append({
                    "id": case.get("id"),
                    "kind": kind,
                    "intent": intent,
                    "top": [(round(sc, 2), s["name"]) for sc, s in ranked[:3]],
                    "expected": expected,
                })
            if args.verbose:
                tag = "OK " if ok else "BAD"
                print(f"  [{tag}] {case.get('id')} unanswerable (top score {top_score:.2f}): {intent!r}")
                for sc, s in ranked[:3]:
                    print(f"        {sc:.2f}  {s['name']}")
            continue

        # match / multi / ambiguous
        rank_of_first_hit = None
        for i, (_, s) in enumerate(ranked, 1):
            if s["name"] in expected:
                rank_of_first_hit = i
                break
        in_top1 = ranked and ranked[0][1]["name"] in expected
        in_top3 = any(s["name"] in expected for _, s in ranked[:3])
        if in_top1:
            hits_at_1 += 1
        if in_top3:
            hits_at_3 += 1
        if rank_of_first_hit:
            rr_sum += 1.0 / rank_of_first_hit

        if not in_top3:
            failures.append({
                "id": case.get("id"),
                "kind": kind,
                "intent": intent,
                "top": [(round(sc, 2), s["name"]) for sc, s in ranked[:3]],
                "expected": expected,
            })
        if args.verbose:
            tag = "OK " if in_top1 else ("PR3" if in_top3 else "BAD")
            print(f"  [{tag}] {case.get('id')} {kind}: {intent!r}")
            for sc, s in ranked[:3]:
                marker = " *" if s["name"] in expected else ""
                print(f"        {sc:.2f}  {s['name']}{marker}")

    summary = {
        "total": n_total,
        "match_total": n_match,
        "unanswerable_total": n_unanswerable,
        "recall_at_1": hits_at_1 / n_match if n_match else 0.0,
        "recall_at_3": hits_at_3 / n_match if n_match else 0.0,
        "mrr": rr_sum / n_match if n_match else 0.0,
        "unanswerable_correct": unanswerable_correct,
        "unanswerable_accuracy": (unanswerable_correct / n_unanswerable) if n_unanswerable else 1.0,
        "failures": failures,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0

    print("Routing eval results")
    print(f"  cases:                 {n_total} ({n_match} match, {n_unanswerable} unanswerable)")
    print(f"  recall@1:              {hits_at_1}/{n_match} = {summary['recall_at_1']:.1%}")
    print(f"  recall@3:              {hits_at_3}/{n_match} = {summary['recall_at_3']:.1%}")
    print(f"  MRR:                   {summary['mrr']:.3f}")
    print(f"  unanswerable correct:  {unanswerable_correct}/{n_unanswerable} = {summary['unanswerable_accuracy']:.1%}")

    if failures and not args.verbose:
        print(f"\nFailures ({len(failures)}):")
        for f in failures:
            top_str = ", ".join(f"{n}({s})" for s, n in f["top"])
            exp_str = ", ".join(f["expected"]) if f["expected"] else "(none — unanswerable)"
            print(f"  {f['id']} [{f['kind']}] expected: {exp_str}")
            print(f"      intent: {f['intent']}")
            print(f"      top-3:  {top_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
