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


def evaluate(cases: list[dict], skills: list[dict]) -> dict:
    """Run all cases; return aggregate + per-source metrics + per-case results."""
    per_case: list[dict] = []
    for case in cases:
        intent = case["intent"]
        expected: list[str] = case.get("expected", [])
        kind = case.get("kind", "match")
        ranked = rank(intent, skills)
        top_score = ranked[0][0] if ranked else 0.0
        top3 = [{"name": s["name"], "score": round(sc, 2)} for sc, s in ranked[:3]]

        result = {
            "id": case.get("id"),
            "source": case.get("source", "curated"),
            "kind": kind,
            "intent": intent,
            "expected": expected,
            "top3": top3,
            "top_score": round(top_score, 3),
        }

        if kind == "unanswerable":
            result["passed"] = top_score < UNANSWERABLE_THRESHOLD
        else:
            in_top1 = bool(ranked) and ranked[0][1]["name"] in expected
            in_top3 = any(s["name"] in expected for _, s in ranked[:3])
            rr = 0.0
            for i, (_, s) in enumerate(ranked, 1):
                if s["name"] in expected:
                    rr = 1.0 / i
                    break
            result["in_top1"] = in_top1
            result["in_top3"] = in_top3
            result["rr"] = rr
            result["passed"] = in_top1
        per_case.append(result)

    return {
        "summary": aggregate(per_case),
        "by_source": {
            source: aggregate([c for c in per_case if c["source"] == source])
            for source in sorted({c["source"] for c in per_case})
        },
        "cases": per_case,
    }


def aggregate(per_case: list[dict]) -> dict:
    match_cases = [c for c in per_case if c["kind"] != "unanswerable"]
    una_cases = [c for c in per_case if c["kind"] == "unanswerable"]
    n_match = len(match_cases)
    n_una = len(una_cases)
    return {
        "total": len(per_case),
        "match_total": n_match,
        "unanswerable_total": n_una,
        "recall_at_1": (sum(1 for c in match_cases if c["in_top1"]) / n_match) if n_match else 0.0,
        "recall_at_3": (sum(1 for c in match_cases if c["in_top3"]) / n_match) if n_match else 0.0,
        "mrr": (sum(c["rr"] for c in match_cases) / n_match) if n_match else 0.0,
        "unanswerable_correct": sum(1 for c in una_cases if c["passed"]),
        "unanswerable_accuracy": (sum(1 for c in una_cases if c["passed"]) / n_una) if n_una else 1.0,
    }


def fmt_pct(v: float) -> str:
    return f"{v:.1%}"


def fmt_diff(curr: float, base: float, pct: bool = True) -> str:
    delta = curr - base
    if abs(delta) < 1e-9:
        return ""
    arrow = "↑" if delta > 0 else "↓"
    val = f"{abs(delta):.1%}" if pct else f"{abs(delta):.3f}"
    return f"  ({arrow} {val} vs baseline)"


def print_metrics(label: str, summary: dict, baseline: dict | None = None) -> None:
    print(f"  {label}")
    base_summary = baseline or {}
    n_match = summary["match_total"]
    n_una = summary["unanswerable_total"]

    def line(display: str, key: str, fmt: str) -> None:
        current_val = summary[key]
        b = base_summary.get(key)
        diff = ""
        if b is not None:
            diff = fmt_diff(current_val, b, pct=(fmt == "pct"))
        if fmt == "pct":
            print(f"    {display:<22}{current_val:.1%}{diff}")
        else:
            print(f"    {display:<22}{current_val:.3f}{diff}")

    if n_match:
        line("recall@1", "recall_at_1", "pct")
        line("recall@3", "recall_at_3", "pct")
        line("MRR", "mrr", "num")
    if n_una:
        line("unanswerable acc", "unanswerable_accuracy", "pct")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print top-3 per case")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    parser.add_argument("--baseline", type=Path, help="JSON file to compare metrics against")
    parser.add_argument("--update-baseline", type=Path, help="write current results to this baseline file")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        sys.exit(f"error: {MANIFEST_PATH} missing; run scripts/build_manifest.py")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    skills = manifest["skills"]
    cases = load_cases()

    results = evaluate(cases, skills)
    summary = results["summary"]
    by_source = results["by_source"]

    baseline_data = None
    if args.baseline:
        if args.baseline.exists():
            baseline_data = json.loads(args.baseline.read_text(encoding="utf-8"))
        else:
            print(f"warning: baseline {args.baseline} does not exist; skipping comparison", file=sys.stderr)

    if args.update_baseline:
        payload = {"summary": summary, "by_source": by_source}
        args.update_baseline.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"wrote baseline to {args.update_baseline}")

    if args.json:
        out = {"summary": summary, "by_source": by_source}
        if baseline_data:
            out["baseline"] = baseline_data
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print(f"Routing eval results ({summary['total']} cases)")
    base_summary = (baseline_data or {}).get("summary") if baseline_data else None
    print_metrics(
        f"overall ({summary['match_total']} match, {summary['unanswerable_total']} unanswerable)",
        summary,
        base_summary,
    )
    for source, ssum in by_source.items():
        base_src = ((baseline_data or {}).get("by_source") or {}).get(source) if baseline_data else None
        print_metrics(
            f"{source} ({ssum['match_total']} match, {ssum['unanswerable_total']} unanswerable)",
            ssum,
            base_src,
        )

    if args.verbose:
        print("\nPer-case:")
        for c in results["cases"]:
            tag = "OK " if c["passed"] else ("PR3" if c.get("in_top3") else "BAD")
            print(f"  [{tag}] {c['id']} [{c['source']}] {c['kind']}: {c['intent']!r}")
            for entry in c["top3"]:
                star = " *" if entry["name"] in c["expected"] else ""
                print(f"        {entry['score']:.2f}  {entry['name']}{star}")

    failures = [c for c in results["cases"] if not c["passed"]]
    if failures and not args.verbose:
        print(f"\nFailures ({len(failures)}):")
        for c in failures:
            top_str = ", ".join(f"{e['name']}({e['score']})" for e in c["top3"])
            exp_str = ", ".join(c["expected"]) if c["expected"] else "(none — unanswerable)"
            print(f"  {c['id']} [{c['source']}/{c['kind']}] expected: {exp_str}")
            print(f"      intent: {c['intent']}")
            print(f"      top-3:  {top_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
