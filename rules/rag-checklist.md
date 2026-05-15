# RAG Pre-Production Checklist

A condensed list of things to verify before a RAG system goes live. Cross-references [`rag-deep-dive`](../ai-engineering/rag-deep-dive/SKILL.md), [`rag-for-code`](../ai-engineering/rag-for-code/SKILL.md), [`rag-ingestion-pipeline`](../ai-engineering/rag-ingestion-pipeline/SKILL.md), and [`graphrag-multi-service`](../ai-engineering/graphrag-multi-service/SKILL.md).

---

## Corpus & Ingestion

1. **Allowlist source enumeration.** Index `src/`, `docs/`, `openapi/` — not "everything except `target/`".

2. **Generated and vendor code excluded.** `target/`, `build/`, `node_modules/`, `dist/`, `*.pb.go`, `openapi-generator` outputs.

3. **Tests tagged, not dropped.** `is_test=true` metadata; filter at retrieval, not at ingest.

4. **One canonical content hash per source file.** Lets the pipeline skip unchanged files cheaply.

5. **Deterministic chunk IDs.** Same source → same ID. Otherwise dedup and incremental updates collapse.

6. **Pinned parser, chunker, embedder versions per chunk.** Mixed-version reads are silent quality regressions.

7. **Atomic per-file upsert + tombstone deletes.** A half-indexed file is the worst state.

8. **Incremental indexing on git push.** Full rebuild is a weekly guardrail, not the default.

---

## Chunking

9. **Code: AST-bound chunks** via tree-sitter. Method + file granularity indexed together.

10. **Prose: heading-bound chunks.** Don't token-split a markdown doc that has headings.

11. **Chunk text starts with a header**: `path`, `class`, `symbol`. Both retrieval signal and grounding aid.

12. **Hard length cap** with explicit truncation marker. Never silently drop content.

13. **JavaDoc / docstrings included** with the surrounding method or class.

---

## Embedding

14. **Same model for indexing and querying.** Mismatch = silent drift.

15. **Code corpora use a code-aware embedder** (`voyage-code-3`, `gemini-embedding-001`, `jina-embeddings-v2-code`). Generic embeddings underperform on code by 5–15 points recall.

16. **Embedding dimensions pinned** in collection metadata. Schema rejects mixed dims.

17. **Cost guardrail before reindex.** Token estimate × $/1M × safety factor; budget kill switch.

---

## Vector Store

18. **HNSW or ScaNN, not flat scan**, beyond ~10k vectors.

19. **Metadata indexed** (GIN on JSONB for Postgres; restricts on Vertex AI). You will filter by `service` and `kind`.

20. **One collection / namespace per service.** Filter cheaply; reindex independently.

21. **Cloud SQL / AlloyDB tier sized for vector ops.** At least `db-custom-4-16384` for production pgvector.

22. **Vector Search private endpoint (PSC)** in production. No public endpoint.

---

## Retrieval

23. **Hybrid (dense + lexical) by default.** Pure dense misses identifiers, error codes, stack traces.

24. **Reciprocal Rank Fusion** to merge legs. Code-aware reranker on top.

25. **Top-K to retrieve** is 20–30; top-K to model is 5–8. Reranking does the cut.

26. **Pre-filter on metadata** before similarity (`service == 'orders'`), not post-filter.

27. **Stack traces and identifiers route lexical-first**, not dense.

---

## Query Handling

28. **Question router** decides one-shot / HyDE / multi-query / agentic / graph / lexical.

29. **HyDE and multi-query for natural-language questions** over code/docs corpora.

30. **Decomposition only for compound multi-hop questions.** Cap depth at 1.

31. **Cache rewrites by normalised question hash.**

---

## Generation Prompt

32. **System prompt grounds and refuses.** "Answer using ONLY the context. If not present, say I don't know."

33. **Citations as `path:line` in the answer**, surfaced as a typed field for client rendering.

34. **Server-side citation verification.** Reject answers citing paths that aren't in the retrieved set.

35. **Context cap at 30–40% of model window.** Leaves room for follow-ups and the answer.

36. **Order chunks: docs > impl > tests; ties by relevance.** Primacy effect.

---

## Multi-Service / Graph

37. **OpenAPI specs indexed per operation**, not as one giant blob.

38. **Pub/Sub topics, events, subscriptions modelled as graph nodes** when "which services consume X" is a question users ask.

39. **Edges extracted deterministically** from parseable artefacts (OpenAPI, code, deps). LLM extraction reserved for unstructured docs.

40. **Edge confidence recorded; low-confidence filtered by default.**

41. **Graph fragments rendered compactly in prompts** (pseudo-Cypher, ≤ 50 edges).

---

## Observability

42. **Per-run ingest manifest** with files-seen / parsed / skipped / errored counts.

43. **Alerts on**: parse error rate > 1%, chunk count drop > 10% run-over-run, embed cost > daily budget.

44. **Per-question trace** from retrieval → rerank → generation. Tokens and chunk IDs logged.

45. **Sample retrieval eval after each ingest run.** Fast regression detection.

---

## Cost & Auth

46. **Rate limit per authenticated user**, not per IP.

47. **Per-conversation token budget.** Hard cap; reject with structured error on trip.

48. **Cost tracked per request and per user.** Counters with `model` and `route` tags.

49. **Service account scoped per workload**: app SA, ingest SA, doc-ai SA — not shared.

50. **No SA keys.** Workload Identity / ADC.

---

## Evaluation

51. **Eval set ≥ 30 questions** before launch. Cover symbol lookup, behaviour, cross-service, negative (refusal), and multi-hop.

52. **Retrieval and generation measured separately.** Right answer with wrong chunks ≠ working RAG.

53. **Citation validity is a metric.** Hallucinated citations fail the eval even if the prose is plausible.

54. **Hold-out set untouched by tuning.** Re-check monthly.

---

## Quick Audit Block

```
Ingest:
- [ ] Allowlist sources; tombstone deletes; incremental updates
- [ ] Deterministic chunk IDs; pinned versions on each chunk

Retrieval:
- [ ] Hybrid dense + lexical; RRF; reranker
- [ ] One collection per service; metadata filtering pre-search

Generation:
- [ ] Grounding system prompt; citation field; server-verified citations
- [ ] Context capped at 30–40% of window

Ops:
- [ ] Per-run ingest dashboard; cost & error alerts
- [ ] Per-user rate limit & token budget
- [ ] Eval suite gates releases

Multi-service:
- [ ] OpenAPI per-operation chunks
- [ ] Graph for relationship questions
- [ ] Edge extraction deterministic; confidence labelled
```

If any line above is "no" before launch, fix or accept the trade-off explicitly.

---

## Anti-Patterns

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| Token-splitting code | Cuts methods mid-line; ruins recall | AST chunker (tree-sitter) |
| One giant collection for 50 services | Filtering at search time; reindex blast radius | One per service |
| Embedding model upgrade in place | Silently breaks similarity for old chunks | New collection, dual-write, switch reads |
| `topK=50` to be safe | Blows the prompt budget; reranker isn't seeing it | 20–30 retrieve, 5–8 to model |
| RAG endpoint on shared rate limit | One user drains LLM budget | Per-user limit & token cap |
| Citations injected by the model, no verification | Hallucinated paths | Server-side verify; reject on mismatch |
| Nightly full reindex | Slow, expensive, risky | Incremental on push; full as guardrail |
| Generated code in the index | Pollutes results | Allowlist; skip generated paths |
| LLM-extracts the service graph | Drifts; unverifiable | Build deterministically from OpenAPI + code |
| Vector store and graph in different regions / clusters | Cross-system join at query time | Co-locate or accept the latency tax |
