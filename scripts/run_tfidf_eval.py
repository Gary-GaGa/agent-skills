#!/usr/bin/env python3
"""TF-IDF routing eval — middle baseline between naive lexical and embeddings.

Why this script exists:
    The lexical scorer in run_routing_eval.py is hand-rolled (substring +
    whole-word + bigram). TF-IDF with cosine similarity is the smallest
    "real IR" baseline — no LLM, no model download — that handles term
    weighting, IDF discounting of common words, and length normalization.
    If TF-IDF closes most of the gap to embeddings, the lesson is "tune
    the lexical scorer". If it doesn't, we know we genuinely need
    semantic embeddings to handle paraphrases.

Pure offline (scikit-learn only, no network), runs in milliseconds.

Usage:
    python3 scripts/run_tfidf_eval.py
    python3 scripts/run_tfidf_eval.py --compare-lexical
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills.json"
EVAL_PATH = REPO_ROOT / "evals" / "skill-routing.jsonl"

UNANSWERABLE_THRESHOLD = 0.10  # cosine; tuned so curated unanswerable cases stay 100%


def skill_text(skill: dict) -> str:
    """Document we vectorize for each skill — same fields as the
    embedding script for parity."""
    parts = [skill["name"].replace("-", " "), skill.get("description", "")]
    if skill.get("tags"):
        parts.append(" ".join(skill["tags"]))
    if skill.get("keywords"):
        parts.append(" ".join(skill["keywords"]))
    return " ".join(parts)


def cjk_aware_tokenize(text: str) -> list[str]:
    """TfidfVectorizer's default token regex doesn't handle CJK. We
    tokenize Latin words and CJK character bigrams (same approach as
    run_routing_eval.tokenize)."""
    import re
    out: list[str] = []
    for m in re.findall(r"[A-Za-z][A-Za-z0-9_+#\-]*", text):
        out.append(m.lower())
    for run in re.findall(r"[一-鿿]+", text):
        if len(run) == 1:
            out.append(run)
        else:
            for i in range(len(run) - 1):
                out.append(run[i:i + 2])
    return out


def load_cases() -> list[dict]:
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


def evaluate(cases: list[dict], skills: list[dict], verbose: bool = False) -> dict:
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
    except ImportError as e:
        sys.exit(f"error: {e}. Install with: pip install scikit-learn")

    vectorizer = TfidfVectorizer(tokenizer=cjk_aware_tokenize, lowercase=False)
    skill_docs = [skill_text(s) for s in skills]
    skill_vec = vectorizer.fit_transform(skill_docs)
    intent_vec = vectorizer.transform([c["intent"] for c in cases])

    # cosine similarity (vectors are L2-normalized by TfidfVectorizer)
    sims_all = (intent_vec @ skill_vec.T).toarray()

    per_case = []
    for ci, case in enumerate(cases):
        sims = sims_all[ci]
        order = np.argsort(-sims)
        top3_idx = order[:3]
        top3 = [{"name": skills[i]["name"], "score": float(round(sims[i], 3))} for i in top3_idx]
        top_score = float(sims[order[0]])
        kind = case.get("kind", "match")
        expected = case.get("expected", [])

        result = {
            "id": case.get("id"),
            "source": case.get("source", "curated"),
            "kind": kind,
            "intent": case["intent"],
            "expected": expected,
            "top3": top3,
            "top_score": round(top_score, 3),
        }
        if kind == "unanswerable":
            result["passed"] = top_score < UNANSWERABLE_THRESHOLD
        else:
            in_top1 = skills[order[0]]["name"] in expected
            in_top3 = any(skills[i]["name"] in expected for i in top3_idx)
            rr = 0.0
            for rank, i in enumerate(order, 1):
                if skills[i]["name"] in expected:
                    rr = 1.0 / rank
                    break
            result["in_top1"] = in_top1
            result["in_top3"] = in_top3
            result["rr"] = rr
            result["passed"] = in_top1
        per_case.append(result)

        if verbose:
            tag = "OK " if result["passed"] else ("PR3" if result.get("in_top3") else "BAD")
            print(f"  [{tag}] {case.get('id')} [{result['source']}] {kind}: {case['intent']!r}")
            for entry in top3:
                star = " *" if entry["name"] in expected else ""
                print(f"        {entry['score']:.3f}  {entry['name']}{star}")

    return {
        "summary": aggregate(per_case),
        "by_source": {
            source: aggregate([c for c in per_case if c["source"] == source])
            for source in sorted({c["source"] for c in per_case})
        },
        "cases": per_case,
    }


def print_metrics(label: str, summary: dict, baseline: dict | None = None, baseline_label: str = "lexical") -> None:
    print(f"  {label}")
    n_match = summary["match_total"]
    n_una = summary["unanswerable_total"]

    def show(display: str, val: float, base: float | None, pct: bool) -> None:
        diff = ""
        if base is not None:
            delta = val - base
            if abs(delta) >= 1e-9:
                arrow = "↑" if delta > 0 else "↓"
                diff = f"  ({arrow} {abs(delta):.1%} vs {baseline_label})" if pct else f"  ({arrow} {abs(delta):.3f} vs {baseline_label})"
        if pct:
            print(f"    {display:<22}{val:.1%}{diff}")
        else:
            print(f"    {display:<22}{val:.3f}{diff}")

    if n_match:
        show("recall@1", summary["recall_at_1"], (baseline or {}).get("recall_at_1"), True)
        show("recall@3", summary["recall_at_3"], (baseline or {}).get("recall_at_3"), True)
        show("MRR", summary["mrr"], (baseline or {}).get("mrr"), False)
    if n_una:
        show("unanswerable acc", summary["unanswerable_accuracy"], (baseline or {}).get("unanswerable_accuracy"), True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print top-3 per case")
    parser.add_argument("--compare-lexical", action="store_true",
                        help="run the naive lexical scorer too and show side-by-side diffs")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    skills = manifest["skills"]
    cases = load_cases()

    results = evaluate(cases, skills, verbose=args.verbose)

    lexical_results = None
    if args.compare_lexical:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import run_routing_eval as rre
        lexical_results = rre.evaluate(cases, skills)

    if args.json:
        out = {"tfidf": results}
        if lexical_results:
            out["lexical"] = lexical_results
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print(f"TF-IDF routing eval ({results['summary']['total']} cases)")
    print(f"  unanswerable threshold (cosine): {UNANSWERABLE_THRESHOLD}")
    base = (lexical_results or {}).get("summary")
    print_metrics(
        f"overall ({results['summary']['match_total']} match, {results['summary']['unanswerable_total']} unanswerable)",
        results["summary"],
        base,
    )
    for source, ssum in results["by_source"].items():
        lex_src = ((lexical_results or {}).get("by_source") or {}).get(source) if lexical_results else None
        print_metrics(
            f"{source} ({ssum['match_total']} match, {ssum['unanswerable_total']} unanswerable)",
            ssum,
            lex_src,
        )

    failures = [c for c in results["cases"] if not c["passed"]]
    if failures and not args.verbose:
        print(f"\nFailures ({len(failures)}):")
        for c in failures:
            top_str = ", ".join(f"{e['name']}({e['score']:.2f})" for e in c["top3"])
            exp_str = ", ".join(c["expected"]) if c["expected"] else "(none — unanswerable)"
            print(f"  {c['id']} [{c['source']}/{c['kind']}] expected: {exp_str}")
            print(f"      intent: {c['intent']}")
            print(f"      top-3:  {top_str}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
