---
name: graphrag-multi-service
description: >
  Knowledge-graph RAG for multi-microservice projects — modelling services,
  endpoints, events, dependencies as a graph; extracting edges from OpenAPI
  / Pub-Sub / Maven; hybrid graph + vector retrieval. Use this skill when
  "talk to my codebase" RAG misses cross-service relationships.
category: ai-engineering
tags: [rag, retrieval, embedding, vector-db, llm, search, microservices, architecture]
keywords: [GraphRAG, knowledge graph, Microsoft GraphRAG, LightRAG, Neo4j, property graph, service map, call graph, OpenAPI, Pub/Sub, hybrid retrieval]
related: [rag-for-code, rag-deep-dive, rag-ingestion-pipeline, microservices-patterns, event-driven-architecture, agentic-rag, query-rewriting-rag]
---

# GraphRAG for Multi-Service Projects

> Pure dense retrieval is fine for "how does this function work". It collapses on "which services consume the OrderCreated event?" That's a graph question. Build the graph.

## When to Use This Skill

- A RAG over multiple microservices keeps missing cross-service questions
- You need to answer questions about dependencies, contracts, blast radius
- Vector retrieval finds individual files but never the *path* between two things
- Choosing between Microsoft GraphRAG, LightRAG, Neo4j + vector, or DIY
- Your AI assistant should reason about architecture, not just code

For pure-dense code RAG, pair with [`rag-for-code`](../rag-for-code/SKILL.md). For ingestion mechanics, [`rag-ingestion-pipeline`](../rag-ingestion-pipeline/SKILL.md).

---

## When Graphs Beat Pure Vectors

| Question | Vector RAG | Graph RAG |
|---|---|---|
| "How does `OrderService.cancel` work?" | ✅ Strong | OK (same chunks) |
| "Which services subscribe to `orders-events`?" | ❌ Misses | ✅ Edge query |
| "If I change the `/api/v1/orders` schema, who breaks?" | ❌ | ✅ Reverse traversal |
| "Show me the call path from API to DB for placing an order" | ❌ | ✅ Path query |
| "What's the blast radius of a `payments` outage?" | ❌ | ✅ Reverse dependency |
| "What domain events does inventory publish?" | Weak | ✅ Direct |

1. **The graph is necessary when the answer is a relationship**, not a snippet. If the user wouldn't expect to find the answer in any single file, don't bet on vector retrieval.

---

## Schema — A Property Graph for a Microservice Estate

The minimum viable nodes and edges:

```
Nodes
─────
(Service)         { id, name, repo, owner_team, language, runtime }
(Endpoint)        { id, service, method, path, operationId, version }
(Event)           { id, name, version, schema_uri }
(Topic)           { id, name }                              ← Pub/Sub topic / Kafka topic
(Subscription)    { id, topic, service, ack_deadline }
(Entity)          { id, service, name, kind: aggregate|value }   ← domain entities
(Repository)      { id, service, name, table }
(Library)         { id, group, artifact, version }
(Database)        { id, kind, instance }
(Doc)             { id, kind: README|ADR|runbook, uri }

Edges
─────
(Service)-[:EXPOSES]->(Endpoint)
(Service)-[:CALLS]->(Endpoint)              ← cross-service call
(Service)-[:PUBLISHES]->(Event)->(Topic)
(Subscription)-[:CONSUMES]->(Topic)
(Service)-[:OWNS]->(Subscription)
(Service)-[:DEFINES]->(Entity)
(Entity)-[:PERSISTED_BY]->(Repository)->(Database)
(Service)-[:DEPENDS_ON]->(Library)
(Service)-[:DOCUMENTED_BY]->(Doc)
```

2. **Start with this schema; resist the urge to add nodes "just in case".** Every node type is a parser to write and a consistency surface to maintain.

3. **Edges are typed and directional.** `CALLS` and `IS_CALLED_BY` are the same edge traversed differently — don't materialise both.

---

## Where Edges Come From

This is the bulk of the work. Extract from artefacts you already have:

| Source | Yields | How |
|---|---|---|
| **OpenAPI specs** | `Endpoint`, `EXPOSES` | Parse `paths.*`; one node per `operationId` |
| **Spring `@RestController`** | `Endpoint`, `EXPOSES` | tree-sitter / `jdt.ls` |
| **HTTP clients** (`RestTemplate`, `WebClient`, OpenFeign `@FeignClient`) | `CALLS` | Match URL templates to known `Endpoint` paths |
| **Spring Cloud GCP Pub/Sub `@MessageMapping`, `Subscriber`** | `CONSUMES` | Annotation + topic name extraction |
| **`PubSubTemplate.publish("topic", ...)`** | `PUBLISHES` | Static analysis of literal topic names |
| **`pom.xml` / `build.gradle`** | `Library`, `DEPENDS_ON` | XML / Gradle parsing |
| **Flyway / JPA `@Entity`** | `Entity`, `Repository`, `PERSISTED_BY` | Schema parse + annotation scan |
| **README / ADRs** | `Doc`, `DOCUMENTED_BY` | Front-matter or path heuristics |
| **OpenTelemetry traces** | `CALLS` (runtime confirmation) | Aggregate spans across services |

4. **Two-phase extraction**: (1) per-repo static analysis produces typed nodes/edges with confidence; (2) cross-repo resolver matches `CALLS` from "URL string" to a known `Endpoint` ID. Phase 2 is where most bugs live.

5. **Mark edge confidence.** Static URL match = high; pattern-matched URL string = medium; OTel-observed = high but volatile. Filter low-confidence edges out of the default retrieval.

6. **Don't infer edges from natural language.** If a README says "we call billing", that's a `Doc` mention, not a `CALLS` edge. Mixing inferred and parsed edges destroys precision.

---

## Pick the Stack

| Option | When |
|---|---|
| **Microsoft GraphRAG** | You want a batteries-included pipeline (LLM extracts entities + relations, summarises communities). Pay for: token cost + opacity. Best for *unstructured* corpora (incident postmortems, design docs). |
| **LightRAG** | Cheaper, faster GraphRAG variant. Same trade-off (LLM-extracted graph) at a fraction of the cost. |
| **Neo4j + vector index** | You're willing to build the graph yourself from artefacts (recommended for code/microservice RAG). Vector + Cypher in one store. |
| **AlloyDB AI / pgvector + your tables** | You already run Postgres; graph queries via recursive CTEs are fine for small/medium graphs. Avoids new infra. |
| **DIY** (Python + DuckDB + a vector store) | Smallest dependency; works at small scale; you own the schema. |

7. **For a microservice estate where artefacts (OpenAPI, code, deps) exist, build the graph deterministically and pick Neo4j or pgvector.** LLM-extracted graphs (GraphRAG/LightRAG) are wasteful when you have parseable sources.

8. **For unstructured corpora** (years of postmortems, RFCs, Slack exports), Microsoft GraphRAG / LightRAG genuinely shine. Different problem.

9. **Don't put the graph and the vector store in different systems if you can avoid it.** Cross-system joins at query time hurt latency and complicate ops.

---

## Hybrid Retrieval Pipeline

```
question
   │
   ├── 1) Classify intent
   │       relationship? lookup? definition? trace?
   │
   ├── 2a) Vector retrieve (top 20 chunks)        ← from rag-for-code store
   │
   ├── 2b) Graph traverse
   │       - Map question entities → graph nodes (NER over service/endpoint/event names)
   │       - Cypher / SQL for the relationship
   │       - Return: paths, neighbours, summary stats
   │
   ├── 3) Merge: chunks + graph fragment (as JSON or pseudo-Cypher)
   │
   └── 4) LLM with grounded prompt: "Here are chunks; here is the graph fragment."
```

10. **Question routing**: a small classifier (or rules on intent verbs — *which*, *who*, *path*, *blast radius*, *consumers of*) decides whether to lean vector, graph, or both. Default to both for safety.

11. **Materialise common queries**. "Consumers of topic X", "callers of endpoint Y" are run thousands of times — cache the answer in a `service_map` view.

12. **Render graph fragments as compact text.** Don't dump JSON: the model handles `Service(orders) --PUBLISHES--> Event(OrderCreated v1) --ON--> Topic(orders-events)` better than a 200-line JSON tree.

13. **Pass at most 30–50 edges** in the prompt. Beyond that the model gets lost. Summarise with counts ("12 services consume `orders-events`; top 5 by call volume: …").

---

## Communities and Summaries (When You Need Them)

For "what does the orders subsystem do?" type queries, the answer is "everything within the orders bounded context". GraphRAG calls these **communities**:

14. **Compute communities by graph clustering** (Leiden / Louvain on the service graph). Pre-summarise each community with an LLM ("the orders subsystem owns OrderService, depends on inventory and billing, exposes 12 endpoints, publishes 3 events").

15. **Index community summaries as documents** in your vector store. Now "what's in the orders area?" retrieves a single dense, accurate paragraph instead of 50 unrelated chunks.

16. **Recompute summaries when** edges into/out of the community change beyond a threshold (e.g. 10% of edges). Don't recompute every commit.

---

## Evaluation

You need a graph-aware eval set, not just a chunk-based one.

| Eval type | Question shape | Ground truth | Metric |
|---|---|---|---|
| **Edge recall** | "Which services consume `orders-events`?" | Set of services | Recall, precision |
| **Path queries** | "Trace from `/api/v1/orders` to its DB" | Ordered edge list | Edit distance vs gold path |
| **Blast radius** | "If `payments` is down, what breaks?" | Set of dependent services | Recall |
| **Consistency** | "Service A publishes event X" — is it backed by code? | Boolean (parsed match) | Accuracy |
| **Negative** | "Does orders depend on shipping?" (no edge) | False | Refusal correctness |

17. **Build the eval set from the graph itself**, then verify with humans. Sample 50 random `CALLS` edges; ask the system to confirm them; spot-check.

18. **Track graph drift over time.** Edges that disappear without a corresponding code change usually mean a parser regression, not a real change.

---

## Operational Concerns

19. **Re-extract on every merge to main.** Daily is too slow when relationships change.

20. **Versioned schemas.** When you add a new node type or rename an edge, write a migration. The graph is now part of your product surface.

21. **Privacy and access control.** Graph queries can leak architecture. If you serve this externally, restrict by service ownership and authentication.

22. **Observability for the graph itself**: edge count by type, parse error rate per repo, last-extract time per service. A silent parser failure removes edges and degrades retrieval invisibly.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| LLM-extracted graph drifts and is unverifiable | Build deterministically from parseable artefacts; reserve LLM extraction for unstructured docs |
| URL strings don't match `Endpoint` paths | Canonicalise both sides (lowercase, strip query, normalise placeholders); match path templates not literals |
| `CALLS` edges over-reported (every WebClient bean creation looks like a call) | Bind edges to the actual `.exchange/.retrieve` call site, not the bean construction |
| Cross-service call graph from OTel only | Misses unexercised paths; combine with static; mark sources |
| Communities recomputed on every commit | Throttle by edge-change-ratio threshold |
| Graph in Neo4j, vectors in Pinecone, joined at query time | Co-locate or accept the latency / ops tax |
| "Talk to the graph" prompt dumps JSON | Render compact pseudo-Cypher; cap edge count |

---

## Pre-Production Checklist

- [ ] Property-graph schema documented; node and edge types finite and named
- [ ] Edges extracted deterministically from OpenAPI / code / Pub-Sub / deps; LLM extraction reserved for unstructured docs
- [ ] Edge confidence recorded; low-confidence filtered by default
- [ ] Graph + vectors co-located, or query plan accounts for the join
- [ ] Question router decides vector / graph / both
- [ ] Graph fragment rendered compactly in prompts; ≤ 50 edges
- [ ] Community summaries pre-computed for "subsystem" questions
- [ ] Re-extraction on merge to main; drift detection in CI
- [ ] Eval set covers edge recall, path queries, blast radius, refusal
- [ ] Access control: graph queries respect service-ownership boundaries

---

## Related Skills

- [`rag-for-code`](../rag-for-code/SKILL.md) — chunk-level code retrieval; this skill complements it
- [`rag-deep-dive`](../rag-deep-dive/SKILL.md) — RAG fundamentals
- [`rag-ingestion-pipeline`](../rag-ingestion-pipeline/SKILL.md) — extraction is the long pole
- [`microservices-patterns`](../../engineering/microservices-patterns/SKILL.md) — the architecture being graphed
- [`event-driven-architecture`](../../engineering/event-driven-architecture/SKILL.md) — events and topics as first-class graph nodes
