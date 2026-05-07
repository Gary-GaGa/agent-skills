---
name: rag-ingestion-pipeline
description: >
  Ingestion pipeline for code/document RAG — source enumeration, parsing,
  chunking, embedding, dedup, incremental git-SHA updates, schema
  migrations, observability. Use this skill when setting up or
  operationalising the data side of a RAG system over multiple repos.
category: ai-engineering
tags: [rag, retrieval, embedding, vector-db, llm, pipeline, data-engineering, automation]
keywords: [ingestion, ETL, incremental indexing, content hash, git SHA, tree-sitter, chunking pipeline, dedup, watcher, schema migration, RAG ops]
related: [rag-for-code, graphrag-multi-service, rag-deep-dive, agent-observability, github-actions, gcp-vertex-ai-rag]
---

# RAG Ingestion Pipeline

> The pipeline is the product. A clever retriever on stale or messy data is worse than a simple retriever on clean data.

## When to Use This Skill

- Designing the first version of a RAG ingestion job for a multi-repo project
- Diagnosing "the index is out of date" or "duplicates everywhere"
- Moving from "nightly full rebuild" to incremental updates
- Adding a new source type (e.g. ADRs, OpenAPI specs, Slack exports) to an existing index
- Operationalising RAG: monitoring, alerting, schema migrations

For chunk-level concerns, pair with [`rag-for-code`](../rag-for-code/SKILL.md). For graph extraction, [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md).

---

## Pipeline Stages

```
sources ─► enumerate ─► fetch ─► parse ─► chunk ─► dedup ─► embed ─► upsert
                                                              │
                                                              └─► graph extract ─► graph store
```

1. **Each stage is independently re-runnable.** Failures should restart the failed stage, not the whole pipeline.

2. **Each stage emits a manifest** (list of `{id, source_hash, parser_version, chunker_version, embed_model}`). The manifest is the contract between stages.

---

## 1. Source Enumeration

Decide what you index — explicitly. Pull from the same sources every run; surprises kill quality.

| Source | Where it lives | How to enumerate |
|---|---|---|
| Code | git repos | `git ls-tree -r HEAD` per repo |
| OpenAPI specs | `**/openapi*.{yaml,json}` in repos | glob |
| ADRs | `docs/adr/*.md` | glob |
| READMEs | `README.md`, `docs/*.md` | glob |
| Migrations | `db/migration/V*.sql` | glob |
| Build files | `pom.xml`, `build.gradle*`, `package.json` | glob |
| Configs | `src/main/resources/application*.yml` | glob |
| Runbooks | wiki / Notion / confluence | API export |
| Issue / PR history | GitHub | search API, time-bounded |

3. **Have an allowlist, not a denylist.** "Index everything except `target/`" silently grows; "index `src/`, `docs/`, `openapi/`" stays bounded.

4. **One enumeration produces a single immutable plan**. Persist it. The whole pipeline operates against this plan; transient repo state changes don't affect the run.

5. **Track what you skip and why.** Generated, vendored, binary, oversized. Surface counts in the run summary; a sudden drop is a parser regression.

---

## 2. Parsing

| Source type | Parser | Notes |
|---|---|---|
| Java | `tree-sitter-java` (or `jdt.ls` for richer info) | Use `jdt.ls` if you need callers/callees |
| TypeScript | `tree-sitter-typescript` / `tsserver` | tsserver gives you imports |
| Go | `tree-sitter-go` / `gopls` | gopls for cross-file resolution |
| Python | `tree-sitter-python` / `jedi` | jedi for symbol resolution |
| YAML | `ruamel.yaml` | Preserves comments — useful for OpenAPI |
| Markdown | `markdown-it` / `mistune` | Split by headings; preserve fenced code untouched |
| OpenAPI | `openapi-spec-validator` + `prance` | Validate before indexing; bad specs ≠ documentation |
| SQL (migrations) | `sqlglot` | Extract table/column names for graph |

6. **Validate before parsing.** A malformed YAML / missing closing brace / corrupt JSON wastes downstream cycles. Reject and report; don't silently skip.

7. **Parser failures are first-class data.** Persist `{file, parser, error, timestamp}`. Aggregate by repo over time; spikes mean a syntax change you don't support.

8. **Pin parser versions.** A `tree-sitter-java` upgrade silently changes node names. Bump the `parser_version` field; treat re-parsing as a migration.

---

## 3. Chunking

For code: AST-bound chunks (method / class / file). For docs: heading-bound. See [`rag-for-code`](../rag-for-code/SKILL.md) for code chunking detail.

```python
@dataclass
class Chunk:
    id: str                  # deterministic: hash(repo, path, kind, symbol, start_line)
    text: str
    metadata: dict           # see rag-for-code skill
    source_hash: str         # sha256 of source file content
    chunker_version: str
    parser_version: str
```

9. **`id` must be deterministic and stable across runs.** A re-index of unchanged source must produce the same `id`. Otherwise dedup and incremental updates collapse.

10. **`source_hash` is the file content hash, not the chunk content hash.** Lets you skip a whole file when nothing changed.

11. **Don't include line numbers in the `id` if they shift trivially.** Hash by symbol path (`com.acme.OrderService#cancel`) where possible; fall back to start_line only when symbols don't apply.

12. **Cap chunk length at a known token budget** (e.g. 1500 for code, 800 for prose). Truncate explicitly and mark — never silently drop content.

---

## 4. Dedup

Even on a single run, you'll see:

- The same code copy-pasted across services (don't dedup these — each instance has its own context).
- Generated files committed in two repos (do dedup or, better, drop both).
- Identical README sections across repos (boilerplate disclaimers).

13. **Dedup by `(content_hash, kind=doc)`** for documentation; keep one canonical with metadata listing all sources.

14. **Don't dedup code by content hash.** Identical methods in two services are not the same chunk — service identity is part of meaning.

15. **Boilerplate filter.** Common license headers, generated banners — strip before hashing chunks for embedding so they don't poison similarity.

---

## 5. Embedding

```python
def embed_batch(chunks: list[Chunk]) -> list[Vector]:
    # batch by token count, not chunk count
    # respect provider rate limits
    # retry with exponential backoff on transient errors
    # checkpoint every N batches
```

16. **Batch by token count, not row count.** Most providers price per token and have per-request token caps. 512-row batches with 50-token rows under-utilise; 32-row batches with 1500-token rows blow the cap.

17. **Idempotency by `(chunker_version, embed_model, chunk.id)`**. Re-running the embed stage skips chunks that already have a vector under the current model.

18. **Pin `embed_model` per collection.** Switching models requires reindexing. Refuse to write a chunk embedded by `voyage-code-3` into a collection tagged `text-embedding-3-large`.

19. **Cost guardrails.** Estimate tokens × $/1M before a full reindex. Have a budget kill switch.

---

## 6. Upsert

```python
def upsert(chunks: list[EmbeddedChunk], collection: str):
    # vector + metadata in one write
    # delete chunks whose source files have been removed since last run
    # mark stale: chunks with parser_version < current
```

20. **Upsert, don't insert.** Re-running on the same `chunk.id` overwrites; the system stays self-healing.

21. **Tombstone deletes.** When a file disappears, its chunks must too. Track per-`source_hash`/per-`path` chunk sets and reconcile on each run.

22. **Atomic per-source updates.** All chunks of one file land or none do. A half-indexed file is the worst state — partial answers, missing citations.

---

## 7. Incremental Updates

Full reindex of a 5M-LOC monorepo costs hours and dollars. Don't do it on every change.

```
on git push to main:
  1. compute changed paths (git diff)
  2. parse + chunk + embed only changed files
  3. tombstone deleted paths
  4. write manifest entry { run_id, sha_before, sha_after, files_changed }
```

23. **Trigger off `git push`, not crons.** Webhooks / CI on push give minute-level freshness.

24. **Use `git diff --name-status` between the previous run's `sha_after` and the new HEAD.** Handle `R` (rename) and `D` (delete) explicitly.

25. **Schedule a "full rebuild" weekly** as a guardrail against missed updates / version skew. Compare the result against the incremental state and alert on diffs.

26. **Watch for renames.** A renamed file produces tombstones for the old `id` and new chunks for the new `id` — content unchanged, IDs different. This is correct, but caches and references must be invalidated.

---

## 8. Schema Migrations

The data evolves. Treat the index like a database.

```yaml
# .rag/schema.yml
version: 7
chunker_version: 4
parser_versions:
  java: tree-sitter-java@0.23.5
  typescript: tree-sitter-typescript@0.23.0
embed_model: voyage-code-3
metadata_fields:
  required: [repo, service, kind, path, source_hash, chunker_version, parser_version, embed_model]
  optional: [class, symbol, signature, callers, callees, git_sha]
```

27. **Bump `version` and reindex on schema-breaking changes.** New required field → all existing chunks need backfill or replacement.

28. **Dual-write during migrations.** New writes hit both schemas; reads prefer new; switch over when coverage hits 100%; remove old.

29. **Keep one prior version online** so a regression doesn't take retrieval down with it.

---

## 9. Observability

What you log per run:

```json
{
  "run_id": "ing-2026-05-07T10:30:00Z",
  "trigger": "github-push",
  "repos": ["orders", "inventory", "billing"],
  "files_seen": 4128,
  "files_skipped": {"generated": 312, "vendor": 1840, "binary": 17, "too_large": 4},
  "files_parsed": 1955,
  "parse_errors": 3,
  "chunks_total": 18420,
  "chunks_new": 412,
  "chunks_updated": 88,
  "chunks_tombstoned": 11,
  "tokens_embedded": 2140000,
  "embed_cost_usd": 0.43,
  "duration_seconds": 412
}
```

30. **Alert on**: parse error rate > 1%, chunk count drop > 10% run-over-run, embed cost > daily budget, run duration > p99.

31. **Per-repo dashboards.** A failing repo silently shrinking the index is a top-3 RAG outage cause. Show last-success timestamp per repo.

32. **Sample-based eval after every run.** Run 20 retrieval-eval queries against the new index; alert on regression. Cheap insurance.

---

## 10. Local Dev Loop

33. **The pipeline must run on a laptop against a single repo** without provisioning anything. Use a local vector store (chroma, pgvector via Docker, or DuckDB + a vector extension) for development.

34. **Mock the embedding API behind an interface.** A local "fake embedder" that hashes content lets you exercise the whole pipeline cheaply in tests.

35. **Golden-file tests for parsing/chunking.** A small fixture repo + expected chunks JSON. Catches regressions instantly.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Nightly full rebuild lasts 6 hours | Incremental on push; weekly full as guardrail |
| Renames double-count chunks | Detect via `git diff -M`; tombstone old id, write new |
| Index slowly fills with deleted files | Tombstone reconciliation; periodic full rebuild diff |
| Boss asks "what's in the index?" → no answer | Manifest per run, queryable |
| Schema change goes out without reindex | Schema version pinned per chunk; refuse mixed reads |
| Embedding cost surprise | Pre-run token estimate; budget kill switch |
| Half-indexed files break citations | Per-file atomic updates |
| Generated code inflates the index | Allowlist enumeration; skip-counts surfaced |
| Parser silently drops 10% of files | Parse-error rate alert; per-repo dashboard |

---

## Pre-Production Checklist

- [ ] Allowlist-based source enumeration; skipped-file counts logged
- [ ] Stage manifests persisted; each stage independently re-runnable
- [ ] Deterministic chunk `id` using stable symbol paths
- [ ] `source_hash`, `parser_version`, `chunker_version`, `embed_model` on every chunk
- [ ] Incremental updates by git diff; weekly full guardrail
- [ ] Atomic per-file upsert; tombstones for deleted files
- [ ] Schema versioned; dual-write migration plan documented
- [ ] Observability: per-run summary, parse-error rate, chunk-count drift, cost
- [ ] Sample retrieval eval after every run; regression alert
- [ ] Pipeline runnable on a laptop against a single repo

---

## Related Skills

- [`rag-for-code`](../rag-for-code/SKILL.md) — chunk-level concerns this pipeline produces
- [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md) — graph extraction often shares the parsing stage
- [`rag-deep-dive`](../rag-deep-dive/SKILL.md) — retrieval-side concerns
- [`agent-observability`](../agent-observability/SKILL.md) — telemetry patterns
- [`github-actions`](../../devops/github-actions/SKILL.md) — push-triggered reindex
