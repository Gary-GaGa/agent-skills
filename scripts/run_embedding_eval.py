#!/usr/bin/env python3
"""Embedding-based routing eval — A/B against the lexical scorer.

Scores user intents against skills by cosine similarity of multilingual
sentence embeddings (no LLM, no API calls — model runs locally on CPU
in a few seconds for the full eval set).

Why this exists:
    The lexical scorer in run_routing_eval.py reports wild recall@1 ~43%.
    We don't know whether that's because the scorer is too crude
    (semantic paraphrases miss) or because the frontmatter itself is
    too generic. This script gives the embedding ceiling, so we can
    decide whether to invest in better scoring or better content.

This is NOT a CI check — sentence-transformers is a heavy dependency
(>1 GB once torch lands). Run it manually when you want a fresh number.

Usage:
    pip install sentence-transformers
    python3 scripts/run_embedding_eval.py
    python3 scripts/run_embedding_eval.py --verbose
    python3 scripts/run_embedding_eval.py --compare-lexical
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "skills.json"
EVAL_PATH = REPO_ROOT / "evals" / "skill-routing.jsonl"

# Multilingual model — smaller (~118 MB) and CJK-capable. We keep this
# in the script rather than the docs because changing the model changes
# the numbers; the script is the source of truth.
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
UNANSWERABLE_THRESHOLD = 0.35  # cosine; tuned empirically on this eval set


def skill_text(skill: dict) -> str:
    """Build the document we embed for a skill. Description carries the
    semantic intent; tags + keywords add anchor terms that help on the
    paraphrase + proper-noun cases respectively."""
    parts = [skill["name"].replace("-", " "), skill.get("description", "")]
    if skill.get("tags"):
        parts.append("tags: " + ", ".join(skill["tags"]))
    if skill.get("keywords"):
        parts.append("keywords: " + ", ".join(skill["keywords"]))
    return "\n".join(parts)


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
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError as e:
        sys.exit(f"error: {e}. Install with: pip install sentence-transformers")

    print(f"loading model: {MODEL_NAME}", file=sys.stderr)
    model = SentenceTransformer(MODEL_NAME)
    print(f"embedding {len(skills)} skills...", file=sys.stderr)
    skill_docs = [skill_text(s) for s in skills]
    skill_emb = model.encode(skill_docs, normalize_embeddings=True, show_progress_bar=False)
    print(f"embedding {len(cases)} intents...", file=sys.stderr)
    intent_emb = model.encode([c["intent"] for c in cases], normalize_embeddings=True, show_progress_bar=False)

    per_case = []
    sims_all = intent_emb @ skill_emb.T  # (n_cases, n_skills)
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


def print_metrics(label: str, summary: dict, lexical: dict | None = None) -> None:
    print(f"  {label}")
    n_match = summary["match_total"]
    n_una = summary["unanswerable_total"]

    def show(display: str, val: float, lex: float | None, pct: bool) -> None:
        diff = ""
        if lex is not None:
            delta = val - lex
            if abs(delta) >= 1e-9:
                arrow = "↑" if delta > 0 else "↓"
                diff = f"  ({arrow} {abs(delta):.1%} vs lexical)" if pct else f"  ({arrow} {abs(delta):.3f} vs lexical)"
        if pct:
            print(f"    {display:<22}{val:.1%}{diff}")
        else:
            print(f"    {display:<22}{val:.3f}{diff}")

    if n_match:
        show("recall@1", summary["recall_at_1"], (lexical or {}).get("recall_at_1"), True)
        show("recall@3", summary["recall_at_3"], (lexical or {}).get("recall_at_3"), True)
        show("MRR", summary["mrr"], (lexical or {}).get("mrr"), False)
    if n_una:
        show(
            "unanswerable acc",
            summary["unanswerable_accuracy"],
            (lexical or {}).get("unanswerable_accuracy"),
            True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print top-3 per case")
    parser.add_argument("--compare-lexical", action="store_true",
                        help="run the lexical scorer too and show side-by-side diffs")
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
        out = {"embedding": results}
        if lexical_results:
            out["lexical"] = lexical_results
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print(f"Embedding routing eval ({results['summary']['total']} cases)")
    print(f"  model: {MODEL_NAME}")
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
