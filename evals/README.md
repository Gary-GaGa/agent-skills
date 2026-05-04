# Evals

Repeatable measurements of how well the skills repo serves the agent
that loads from it. Self-hosted, no LLM calls, runs in milliseconds.

## skill-routing.jsonl

Tests whether `description` + `tags` + `keywords` correctly route a
user intent to the right skill. Each line is one test case:

```json
{"id": "001", "kind": "match", "intent": "Help me design an MCP server", "expected": ["mcp-server-design"]}
```

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `id` | yes | Stable short ID. Numeric for `match`, `m##` for multi, `a##` for ambiguous, `u##` for unanswerable. |
| `intent` | yes | A realistic user prompt. Mix English and Chinese. Don't paraphrase the description verbatim. |
| `expected` | yes | List of skill `name`s the agent should load. Empty list for `unanswerable`. |
| `kind` | yes | One of `match`, `multi`, `ambiguous`, `unanswerable`. |
| `notes` | no | Optional human note about the test. |

### `kind` semantics

| Kind | Pass condition |
|------|----------------|
| `match` | The expected skill appears in top-1 (counts toward `recall@1`). |
| `multi` | Any expected skill in top-3. RR is the reciprocal of the first hit's rank. |
| `ambiguous` | Top-3 contains at least one expected skill (intent legitimately spans multiple skills). |
| `unanswerable` | Top score is below `UNANSWERABLE_THRESHOLD` (1.0). The harness should report "no matching skill". |

## Running

```bash
python3 scripts/run_routing_eval.py            # summary
python3 scripts/run_routing_eval.py --verbose  # per-case top-3
python3 scripts/run_routing_eval.py --json     # machine output
```

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
- **Not exhaustive.** ~30 cases sample the failure space; they don't
  prove the routing is correct everywhere. Add cases when you find
  routing bugs in the wild.
- **Not a hard CI gate.** Recall@1 fluctuates with content edits.
  Treat regressions as a signal to investigate, not an automatic fail.

## When to add cases

- A user reported the agent loaded the wrong skill — add their prompt
  with the correct expected skill.
- You added a new skill whose description overlaps with an existing one
  — add cases that distinguish them.
- You noticed a category that has zero coverage in the eval set.

## Current baseline

Run `python3 scripts/run_routing_eval.py` to see the current numbers.
The eval set should grow with the skill set; the scorer is stable.
