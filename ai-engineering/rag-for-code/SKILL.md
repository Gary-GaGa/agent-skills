---
name: rag-for-code
description: >
  RAG for source code — AST/tree-sitter chunking, code embedding models,
  repo metadata, import/call graphs, cross-repo retrieval. Use this skill
  when building "talk to my codebase" RAG, indexing Java/TS/Go monorepos,
  or when generic prose RAG retrieval misses the right code chunks.
category: ai-engineering
tags: [rag, retrieval, embedding, vector-db, llm, search, codebase-design, coding]
keywords: [code RAG, tree-sitter, AST chunking, voyage-code, jina-embeddings-v2-code, CodeRankEmbed, call graph, import graph, monorepo, semantic search for code]
related: [rag-deep-dive, rag-ingestion-pipeline, graphrag-multi-service, agentic-rag, context-engineering, query-rewriting-rag, spring-ai-rag]
---

# RAG for Code

> Code is not prose. Token-based chunking cuts mid-method, generic embeddings miss API names, and the most important signal — who calls whom — is structural, not semantic.

## When to Use This Skill

- Building a "talk to my codebase" Q&A or coding assistant
- Indexing a multi-service / monorepo project for retrieval
- Diagnosing "the model can't find the right function" issues
- Choosing between code embedding models and vector backends
- Combining dense retrieval with structural signals (imports, callers, types)

For language-agnostic RAG fundamentals, pair with [`rag-deep-dive`](../rag-deep-dive/SKILL.md). For multi-service relationship modelling, pair with [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md).

---

## Why Generic RAG Underperforms on Code

| Symptom | Cause |
|---|---|
| Retrieves the right file, wrong function | Token chunking cut a 200-line file at 800-token boundaries |
| Misses by API name (`OrderService.cancel`) | Generic prose embeddings don't tokenise camelCase / snake_case well |
| Returns the test, not the impl | No metadata; retrieval can't disambiguate |
| Cross-file behaviour invisible | Only shows the query target — not its callers / callees |
| Misses on error code or stack trace | Pure dense retrieval; lexical signal lost |

1. **The four code-specific levers**: (1) chunk on AST boundaries, (2) embed with a code-aware model, (3) attach structural metadata, (4) hybrid retrieval (dense + lexical + graph).

---

## 1. Chunking — AST, Not Tokens

### Granularity choices

| Granularity | Best for | Notes |
|---|---|---|
| **Method / function** | "How does `cancelOrder` work?" | Default. ~80% of useful retrievals. |
| **Class / type** | "What's `OrderService` for?" | Pair with method-level chunks; don't pick one or the other. |
| **File** | Small files (< 200 lines), config files | Falls back to file when AST parsing fails. |
| **Symbol-windowed** | Surrounding N lines around a symbol | For diff / "what does this PR touch?" use cases. |

2. **Default to two granularities indexed together**: file-level + method-level. Class-level is implicit if you attach class metadata to method chunks.

3. **Use tree-sitter, not regex.** A single Java parser handles records, sealed classes, lambdas, annotations. Regex misses everything non-trivial.

   ```python
   import tree_sitter_java as tsj
   from tree_sitter import Language, Parser
   parser = Parser(Language(tsj.language()))
   tree = parser.parse(source.encode("utf-8"))
   # Walk: method_declaration, class_declaration, interface_declaration, record_declaration
   ```

4. **Skip generated code.** `target/`, `build/`, `node_modules/`, `*.pb.go`, `openapi-generator` outputs. Tag generated files with metadata if you must keep them.

### Carry context with each chunk

A bare method body is meaningless out of context. Each chunk text should be:

```
// File: src/main/java/com/acme/orders/web/OrderController.java
// Class: OrderController
// Imports (relevant): com.acme.orders.application.OrderService, jakarta.validation.Valid

@PostMapping
public ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest req, ...) {
    Order order = service.create(req.toCommand());
    ...
}
```

5. **Prepend a header with file path, class, key imports.** It both helps retrieval (the path is searchable text) and grounds the model when the chunk is shown.

6. **Include the JavaDoc / docstring.** Domain language lives there.

7. **Cap chunk length** at ~1500 tokens. Methods longer than that almost always need a refactor anyway; truncate with a `// … (truncated, N more lines) …` marker.

---

## 2. Embedding — Code-Aware Models

### Model picks (as of late 2025)

| Model | Strengths | Notes |
|---|---|---|
| **Voyage `voyage-code-3`** | Best quality across languages, instructable | API; pair with Voyage rerank |
| **Jina `jina-embeddings-v2-base-code`** | Self-hostable, multilingual code | Open weights |
| **`SFR-Embedding-Code-2B`** | High quality, open | Larger; needs GPU for serving |
| **`CodeRankEmbed`** | Optimised for code search ranking | Open |
| **OpenAI `text-embedding-3-large`** | Strong general baseline | OK on code; lags vs code-specific |

8. **Code-specific embeddings beat general ones by 5–15 points on retrieval recall** in code search. Worth the switch.

9. **Same model for indexing and querying.** Different models → incompatible vectors → silent drift.

10. **For multilingual repos** (Java + TS + Go), use a multilingual code model (`voyage-code-3`, `jina-embeddings-v2-base-code`) rather than one model per language.

### Query-side tweaks

Code questions often look nothing like the code:

- Question: *"How do we authenticate users?"*
- Code: `SecurityFilterChain`, `JwtAuthenticationFilter`, `UserDetailsService`

11. **Use instructable embeddings** when available. Voyage and a few open models accept a task description ("Retrieve Java code that handles HTTP authentication"). Boost recall.

12. **Hybrid search is non-negotiable for code.** BM25 catches API names, error codes, and identifiers that dense embeddings smear.

---

## 3. Metadata — The Hidden Lever

Each chunk in your vector store should carry:

```json
{
  "id": "orders/.../OrderController.java#create:42",
  "repo": "orders",
  "service": "orders",
  "language": "java",
  "path": "src/main/java/com/acme/orders/web/OrderController.java",
  "kind": "method",
  "package": "com.acme.orders.web",
  "class": "OrderController",
  "symbol": "create",
  "signature": "ResponseEntity<OrderResponse> create(CreateOrderRequest, UriComponentsBuilder)",
  "annotations": ["@PostMapping", "@Valid"],
  "imports": ["com.acme.orders.application.OrderService", "jakarta.validation.Valid"],
  "callers": ["OrderControllerTest.createsOrderAndReturns201"],
  "callees": ["OrderService.create", "UriComponentsBuilder.path"],
  "is_generated": false,
  "is_test": false,
  "git_sha": "ab12cd3",
  "indexed_at": "2026-05-07T10:00:00Z"
}
```

13. **`kind` and `is_test`/`is_generated` are the metadata that pay for themselves immediately.** Filter `kind=method` for "implementation" queries; exclude tests by default unless the user asks.

14. **`callers`/`callees` enable graph-aware retrieval** without committing to a full graph DB up front. Build them in the ingest pipeline (LSP / `jdt.ls` for Java, `gopls` for Go, `tsserver` for TS).

15. **`git_sha` per chunk** lets you express staleness and incremental re-indexing. See [`rag-ingestion-pipeline`](../rag-ingestion-pipeline/SKILL.md).

---

## 4. Retrieval — Hybrid + Structural

### The pipeline

```
query
  ├─► dense   (code embedding model, top 30)
  ├─► lexical (BM25 over symbol/path/identifier tokens, top 30)
  └─► graph   (callers/callees of dense top-5, top 10)
                    │
              merge (RRF) → rerank → top 8
```

16. **Reciprocal Rank Fusion (RRF) is the simple merge.** Score each result by `Σ 1 / (k + rank)` over sources; sort. No tuning needed for a strong baseline.

17. **Add a graph leg only when chunks have caller/callee metadata.** Don't fake it with naive co-occurrence.

18. **Rerank with a code-aware reranker** (Voyage Rerank, Cohere Rerank, `bge-reranker-v2-m3`). Cuts noise from 40 → 8.

19. **Filter by service / repo / language pre-search** when the user implies it ("how does the orders service publish events?"). Saves recall budget.

### Special-case lexical hits

20. **Stack traces and error codes**: route to lexical-only first. A `NullPointerException at OrderService.cancel(OrderService.java:123)` should retrieve that exact line, not its semantic neighbour.

21. **Identifier queries** (`OrderRepository.findByStatus`) belong in lexical primary, dense secondary.

---

## 5. Repo & Multi-Service Layout

```
indexed_corpus/
  per-service/                       ← one collection / namespace per service
    orders/   { code chunks, openapi.yaml, README, ADRs }
    inventory/
    billing/
  shared/                            ← libraries, design docs, runbooks
```

22. **One collection (or namespace) per service.** Lets you filter cheaply ("answer only from orders") and re-index per service without disturbing others.

23. **Index docs alongside code** — README, ADRs, OpenAPI specs, runbooks. The model needs both. Tag them with `kind=doc`.

24. **OpenAPI specs are gold for cross-service questions.** Index each operation as a separate chunk with `service`, `path`, `method`, `summary`, `requestBody`, `responses`. Expensive once, paid back forever.

25. **Service boundaries belong in metadata, not in the chunk text.** "Service: orders" as a JSON field, not "this code belongs to the orders service" prose.

---

## 6. Prompt Assembly for Code Q&A

```
System: You answer questions about the company's microservices. Use ONLY the
provided code/doc snippets. Cite each claim with `path:line` from the snippet
header. If the answer isn't in the snippets, say "I don't know" and suggest
which service or file might have it.

Snippets:
[1] orders/src/.../OrderController.java#create:42
    @PostMapping ResponseEntity<OrderResponse> create(...) { ... }

[2] orders/src/.../OrderService.java#create:18
    @Transactional public Order create(CreateOrderCommand cmd) { ... }

[3] orders/openapi/orders-api.yaml#/paths/~1api~1v1~1orders/post
    operationId: createOrder
    requestBody: ...

User: How does the orders service handle a new order?
```

26. **Keep the snippet header machine-readable.** `path:line` (or `path#symbol:line`) lets the model produce structured citations a tool can verify.

27. **Cap context at 30–40% of the model's window.** Leave room for follow-ups and the answer.

28. **Order chunks: docs > impl > tests.** When tied, by relevance. The model uses the first authoritative match; tests are last because they describe behaviour, not specify it.

---

## 7. Evaluation

Build a code-RAG eval set early. 30–80 questions covering:

- **Symbol lookup**: "Where is `OrderRepository` defined?" — exact-match recall is the metric.
- **Behaviour queries**: "How is an order cancelled?" — relevant-chunk recall@5.
- **Cross-service**: "What event does orders publish on payment?" — multi-service retrieval; needs graph signal.
- **Negative**: "Where is the GraphQL endpoint?" (there isn't one) — refusal correctness.
- **Stale** (after refactor): chunks that should *not* be retrieved post-rename.

29. **Ground-truth chunks are file:line ranges.** A chunk overlaps a ground-truth range = hit. Lets you re-chunk without rebuilding the eval.

30. **Measure retrieval and generation separately.** A wrong answer with the right chunks is a prompt problem; a refusal with chunks present is a grounding problem.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Chunks too large; precision suffers | AST-bound chunks (method-level), not token-bound |
| Asks "how do we auth?" returns Spring docs in `node_modules` | Filter generated and dependency code at ingest |
| Pulls in `Test`-suffixed classes for impl questions | `is_test` metadata + filter |
| Embedding model swap silently kills recall | Pin model in collection metadata; refuse to mix |
| Multi-service questions miss cross-references | Add OpenAPI/event topic chunks; graph-leg retrieval |
| Tree-sitter throws on a file → entire file dropped | Fall back to file-level chunk on parse error; never silently skip |
| Updates take all night | Incremental ingest by `git_sha`; only re-embed changed files |

---

## Pre-Production Checklist

- [ ] AST chunking via tree-sitter; method + file granularity
- [ ] Generated and test code tagged in metadata, not in chunk content
- [ ] Code-specific embedding model; same model index + query
- [ ] Hybrid retrieval (dense + BM25), RRF merge, code-aware rerank
- [ ] Metadata: repo, service, kind, package, class, symbol, signature, callers, callees, git_sha
- [ ] One collection / namespace per service
- [ ] OpenAPI specs and ADRs indexed alongside code
- [ ] Snippet header uses `path:line`; system prompt enforces citation
- [ ] Eval set ≥ 30 questions; retrieval and generation measured separately
- [ ] Incremental re-indexing on git push, not nightly full rebuild

---

## Related Skills

- [`rag-deep-dive`](../rag-deep-dive/SKILL.md) — generic RAG fundamentals this builds on
- [`rag-ingestion-pipeline`](../rag-ingestion-pipeline/SKILL.md) — how chunks get into the store
- [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md) — when caller/callee metadata isn't enough
- [`agentic-rag`](../agentic-rag/SKILL.md) — combine retrieval with grep/AST tools
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — eval framework for the pipeline
