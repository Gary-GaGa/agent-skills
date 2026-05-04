# Evals

Repeatable measurements of how well the skills repo serves the agent
that loads from it. Self-hosted, no LLM calls, runs in milliseconds.

## skill-routing.jsonl

Tests whether `description` + `tags` + `keywords` correctly route a
user intent to the right skill. Each line is one test case:

```json
{"id": "001", "source": "curated", "kind": "match",
 "intent": "Help me design an MCP server", "expected": ["mcp-server-design"]}
```

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Stable short ID. Numeric for `match`, `m##` for multi, `a##` for ambiguous, `u##` for unanswerable, `w##` for wild. |
| `source` | yes | `curated` or `wild` (see below). |
| `intent` | yes | A user prompt. |
| `expected` | yes | List of skill `name`s the agent should load. Empty list for `unanswerable`. |
| `kind` | yes | One of `match`, `multi`, `ambiguous`, `unanswerable`. |
| `notes` | no | Optional human note about the test. |

### `source` — why two pools

| Source | What it is | Why it exists |
|--------|------------|---------------|
| `curated` | Clean prompts written alongside the scorer, often using vocabulary that overlaps with frontmatter. | Quick smoke test; high recall here means the obvious case works. |
| `wild` | Paraphrased, conversational, dialect-mixed, partial, or misleading prompts that deliberately avoid frontmatter vocabulary. | Stress test. Low recall here exposes where `keywords:` should be added or `description:` tightened. |

The headline number is the **wild** recall@1; the curated number is a
floor, not a target.

### `kind` semantics

| Kind | Pass condition |
|------|----------------|
| `match` | The expected skill appears in top-1 (counts toward `recall@1`). |
| `multi` | Any expected skill in top-3. RR is the reciprocal of the first hit's rank. |
| `ambiguous` | Top-3 contains at least one expected skill (intent legitimately spans multiple skills). |
| `unanswerable` | Top score is below `UNANSWERABLE_THRESHOLD` (1.0). The harness should report "no matching skill". |

## Running

```bash
python3 scripts/run_routing_eval.py                              # summary
python3 scripts/run_routing_eval.py --verbose                    # per-case top-3
python3 scripts/run_routing_eval.py --json                       # machine output
python3 scripts/run_routing_eval.py --baseline evals/baseline.json  # diff vs baseline
python3 scripts/run_routing_eval.py --update-baseline evals/baseline.json  # snapshot
```

## Baseline workflow

`evals/baseline.json` is the agreed-upon snapshot of metrics. CI prints
the current eval against this baseline (informational only — it does
not fail the build, since recall fluctuates with content edits).

When a PR intentionally improves or refactors routing:

1. Run `python3 scripts/run_routing_eval.py --baseline evals/baseline.json`.
2. Confirm the deltas match what you expected.
3. If yes, run `python3 scripts/run_routing_eval.py --update-baseline evals/baseline.json` and commit the change in the same PR.

When a PR shows an *unexpected* regression (e.g. a description edit
that drops recall on a wild case), treat it as a signal that the edit
removed a trigger phrase — investigate before merging.

## Scoring

A pure-lexical scorer; no embeddings, no LLM. Per skill, per intent:

| Signal | Weight | Match style |
|--------|--------|-------------|
| `keywords` entry appears in intent | +3.0 | case-insensitive substring (preserves multi-word phrases like `Model Context Protocol`) |
| `tags` entry appears in intent | +1.0 | whole-word (so `sync` doesn't match `async`) |
| `name` segment (length ≥ 3) appears in intent | +0.5 | whole-word |
| Intent token ∩ description token | +0.2 each | post-stopword sets; CJK uses character bigrams |

This is intentionally crude — it's a baseline that exposes where the
frontmatter is too generic. If a real-world prompt fails, the fix is
usually one of:

1. Add a `keywords:` entry that the user is likely to type literally.
2. Tighten the `description` to include a missing trigger phrase.
3. Add a `tag` that's specific to the skill's domain.

## What this eval is *not*

- **Not a semantic test.** Embedding-similarity routing will outperform
  this scorer on paraphrases. The lexical baseline guards against the
  obvious failure modes; LLM-as-judge or vector retrieval would be a
  separate eval.
- **Not exhaustive.** ~50 cases sample the failure space; they don't
  prove the routing is correct everywhere. Add cases when you find
  routing bugs in the wild.
- **Not a hard CI gate.** Recall fluctuates with content edits. Treat
  regressions as a signal to investigate, not an automatic fail.

## When to add cases

- A user reported the agent loaded the wrong skill — add their prompt
  as a `wild` case with the correct expected skill.
- You added a new skill whose description overlaps with an existing one
  — add cases that distinguish them.
- You noticed a category that has zero coverage in the eval set.

## Current baseline

See `evals/baseline.json` for the committed snapshot. As of writing:

| Source | recall@1 | recall@3 | MRR | unanswerable |
|--------|----------|----------|-----|--------------|
| overall (47 cases) | 75.0% | 90.0% | 0.824 | 100% |
| curated (31 cases) | 92.3% | 100.0% | 0.962 | 100% |
| wild (16 cases) | 42.9% | 71.4% | 0.567 | 100% |

The 50-percentage-point gap between curated and wild is the selection
bias the wild pool exists to expose. Closing it is the job of `keywords:`
backfill and tighter descriptions.
