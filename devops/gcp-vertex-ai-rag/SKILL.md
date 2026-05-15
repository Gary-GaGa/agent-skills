---
name: gcp-vertex-ai-rag
description: >
  RAG infrastructure on GCP — Vertex AI Vector Search, AlloyDB AI, pgvector
  on Cloud SQL, Firestore vector, Vertex AI RAG Engine; embedding models;
  Document AI; IAM and cost. Use this skill when sizing or selecting the
  GCP RAG stack for a Spring/Java backend.
category: devops
tags: [gcp, cloud, devops, rag, llm, retrieval, vector-db, infrastructure]
keywords: [Vertex AI Vector Search, Vertex AI RAG Engine, AlloyDB AI, pgvector, Cloud SQL, Firestore vector, gemini-embedding, text-embedding-005, Document AI, ScaNN]
related: [gcp-fundamentals, gcp-cloud-sql-spring, spring-ai-rag, rag-deep-dive, rag-ingestion-pipeline]
---

# RAG Infrastructure on GCP

> Three reasonable choices, three sets of trade-offs. Pick by scale, latency, and what you already run — not by what's shiniest.

## When to Use This Skill

- Selecting the vector store for a new RAG system on GCP
- Choosing between DIY (Spring AI + pgvector), Vertex AI Vector Search, or Vertex AI RAG Engine (managed)
- Picking an embedding model on Vertex AI
- Sizing cost and quota before going to production
- Auditing an existing setup for misalignment with workload

For Spring-side code, pair with [`spring-ai-rag`](../../engineering/spring-ai-rag/SKILL.md). For pipeline ops, [`rag-ingestion-pipeline`](../../ai-engineering/rag-ingestion-pipeline/SKILL.md).

---

## Vector Store Options on GCP

| Option | When to pick | When to avoid |
|---|---|---|
| **pgvector on Cloud SQL Postgres** | < 1M chunks, you already run Cloud SQL, want one transactional store | High QPS reads or > ~5M chunks |
| **AlloyDB AI** | Larger pgvector workloads (10M+); want ScaNN-backed index, parallel query | Cost is materially higher than Cloud SQL |
| **Vertex AI Vector Search** | 10M+ chunks, low-latency multi-region serving, need ScaNN/Treelet | Smaller workloads (operational overhead not worth it) |
| **Firestore vector index** | Already using Firestore, < 100k chunks, simple shape | Heavy filtering, large scale |
| **Vertex AI RAG Engine (managed)** | You want zero pipeline code, accept opinionated chunking and retrieval | You need control over chunking, embedding, or retrieval |

1. **Default for a new project**: pgvector on Cloud SQL. You can outgrow it; you can't outgrow zero — and most internal RAGs never hit 1M chunks.

2. **Promote to AlloyDB AI when** pgvector index build time exceeds an hour or QPS sustained > ~50. You keep the same SQL.

3. **Promote to Vertex AI Vector Search when** you cross ~10M chunks, need < 50ms p99 retrieval, or need multi-region serving. You give up Postgres joins.

4. **Vertex AI RAG Engine** is a "managed RAG-as-a-service": you upload documents to a Cloud Storage bucket; it chunks, embeds, indexes, and serves. **Use when** the team can't afford to build a pipeline and the corpus is mostly PDFs and Markdown. **Avoid for** code RAG — you can't override chunking strategy.

---

## pgvector on Cloud SQL

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE rag_chunks (
    id UUID PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL,
    embedding vector(768) NOT NULL
);

CREATE INDEX idx_rag_chunks_hnsw
    ON rag_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_rag_chunks_metadata
    ON rag_chunks USING gin (metadata jsonb_path_ops);
```

5. **HNSW index for most workloads.** Faster recall than IVFFlat at typical scales; slower to build but the build cost is amortised.

6. **Pre-filter with `WHERE` before vector search** when you can. `WHERE metadata->>'service' = 'orders'` plus `ORDER BY embedding <=> ?` is much faster than post-filtering top-1000.

7. **Cloud SQL tier**: at least `db-custom-4-16384` for production RAG — vector ops are CPU and memory hungry. Smaller tiers OOM on index build.

8. **Connect via Cloud SQL Java Connector** with IAM auth. See [`gcp-cloud-sql-spring`](../../engineering/gcp-cloud-sql-spring/SKILL.md).

---

## AlloyDB AI

AlloyDB is Postgres with Google's columnar engine and ScaNN. The RAG-relevant features:

- **`ScaNN`-backed vector index** — Google's nearest-neighbour algorithm; faster and more memory-efficient than HNSW at scale.
- **Parallel query** — vector + filter + join evaluated concurrently.
- **AI-integrated SQL** — `embedding()` function calls Vertex AI directly from SQL (use sparingly; egress and cost).

```sql
CREATE INDEX idx_rag_chunks_scann
    ON rag_chunks USING scann (embedding cosine)
    WITH (num_leaves = 1000);
```

9. **Switch from Cloud SQL → AlloyDB** when index size or query latency becomes the bottleneck. Schema is portable; client code mostly unchanged.

10. **Don't use SQL `embedding()` in your hot path.** It's convenient for one-off jobs; in steady state, embed in the application and pass the vector.

---

## Vertex AI Vector Search

Two modes:

- **Public endpoint**: easy to deploy, internet-routable.
- **Private endpoint** (PSC): for VPC-only services. Default for production.

```bash
# Create an index
gcloud ai indexes create \
    --display-name=rag-code \
    --metadata-file=index-metadata.json \
    --region=asia-east1
```

```json
{
  "contentsDeltaUri": "gs://acme-rag-deltas/",
  "config": {
    "dimensions": 768,
    "approximateNeighborsCount": 150,
    "distanceMeasureType": "COSINE_DISTANCE",
    "algorithm_config": { "treeAhConfig": { "leafNodeEmbeddingCount": 500 } }
  }
}
```

```bash
# Create an endpoint, deploy index to it
gcloud ai index-endpoints create --display-name=rag-endpoint --region=asia-east1
gcloud ai index-endpoints deploy-index <ENDPOINT_ID> \
    --deployed-index-id=rag_v1 \
    --display-name=rag_v1 \
    --index=<INDEX_ID>
```

11. **Streaming updates vs batch updates.** Streaming for incremental ingest (small, frequent); batch for backfills (large, rare). Mixing them costs you predictability.

12. **Filter restricts and namespaces** for metadata filtering. Restricts are typed and indexed; tokens-style is for free-form match. Pre-design your filter taxonomy — restricts can't be reshaped without re-deploy.

13. **One deployed index per major schema version.** Re-embedding under a new model = new index = new deployment. Keep both online during cutover.

14. **Cost shape**: per-node-per-hour (deployed index) + per-million queries. The hourly is the bulk; idle indexes are expensive. Don't deploy a dev index 24/7.

---

## Vertex AI RAG Engine (Managed)

The fastest path from "I have docs in GCS" to "I have a RAG endpoint".

```python
from vertexai.preview import rag

corpus = rag.create_corpus(
    display_name="orders-docs",
    description="orders microservice documentation",
)
rag.import_files(corpus.name, paths=["gs://acme-rag-source/orders-docs/"])

response = rag.retrieval_query(
    rag_resources=[rag.RagResource(rag_corpus=corpus.name)],
    text="How do we cancel an order?",
    similarity_top_k=10,
)
```

15. **The corpus does the chunking and embedding.** You can configure chunk size and overlap; you cannot plug in a tree-sitter chunker. **This is the disqualifier for code RAG.**

16. **Use it for unstructured corpora**: PDFs, design docs, runbooks, knowledge base articles. For these, the managed pipeline is genuinely faster than building your own.

17. **Costs**: per-corpus storage + per-query. Cheaper than running your own infra at small scale; surprisingly close to DIY at large scale.

---

## Embedding Models on Vertex AI

| Model | Dims | Languages | Notes |
|---|---|---|---|
| `text-embedding-005` | 768 | English | Latest general-purpose; default if you're not sure |
| `text-multilingual-embedding-002` | 768 | 100+ | Multilingual; small quality dip vs English-only |
| `gemini-embedding-001` | 3072 (truncatable) | Multilingual + code | Highest quality; can downsample dims |
| `text-embedding-large-exp-03-07` | 3072 | English | Experimental large model |

18. **For code-heavy corpora, evaluate `voyage-code-3` (third-party) against `gemini-embedding-001`.** The Vertex models are general-purpose; code-specific models often win on retrieval recall for code search.

19. **Pin the model in your collection metadata.** Switching means re-embedding every chunk. The mistake of "let me try the new one" without a migration plan is expensive.

20. **`gemini-embedding-001` supports dimension truncation.** If 3072 is too much for your store/budget, request 768 or 1536. Quality decay is sub-linear.

21. **Cost shape**: per million tokens embedded. Estimate before reindex: tokens in corpus × $/1M × safety factor (1.3).

---

## Document AI (Parsing PDFs and Forms)

If your corpus has PDFs, scanned forms, or structured documents:

```python
from google.cloud import documentai
client = documentai.DocumentProcessorServiceClient()
result = client.process_document(request={
    "name": processor_name,
    "raw_document": { "content": pdf_bytes, "mime_type": "application/pdf" },
})
text = result.document.text
```

22. **Use a Layout Parser processor for general documents.** It returns text with layout (paragraphs, tables, headings) preserved — much better RAG input than raw PDF text extraction.

23. **For forms (invoices, contracts), use a Custom Extractor.** Trains on your samples; returns structured fields you can feed to RAG metadata.

24. **Don't run Document AI inside your app.** It's a heavy, async API. Use a Cloud Run job triggered by GCS upload events.

---

## IAM and Networking

25. **Service account roles** (one per workload):
    - Spring app SA: `roles/aiplatform.user` (chat + embedding APIs), `roles/cloudsql.client` + `roles/cloudsql.instanceUser` (pgvector)
    - Ingestion job SA: same as app + `roles/storage.objectViewer` (GCS sources)
    - Document AI processor SA: `roles/documentai.apiUser`

26. **Vertex AI Vector Search private endpoint** uses Private Service Connect. Same VPC as your GKE cluster; no public IP. Mandatory for production.

27. **Quotas to pre-request**: tokens per minute for the embedding model (default is small for new projects); concurrent online prediction requests; index nodes per region.

28. **VPC Service Controls** if data residency / exfil prevention matters. Wrap the AI Platform API; pgvector lives in your private VPC anyway.

---

## Cost Sketch (Rough, Late 2025)

For a 5M-chunk code RAG, ~10 QPS, asia-east1:

| Item | Vertex AI Vector Search | AlloyDB AI | pgvector on Cloud SQL |
|---|---|---|---|
| Storage / index | 1 e2 deployed node, ~$200/mo | 4 vCPU instance, ~$400/mo | db-custom-4-16384, ~$300/mo |
| Embedding (one-time) | $50–200 (5M chunks × ~200 tok) | same | same |
| Query embedding | ~$20/mo | same | same |
| Chat (Gemini 2.5 Pro) | $1k–5k/mo (workload-dependent) | same | same |
| **Total infra** | **$200–500/mo** | **$400–700/mo** | **$300–500/mo** |
| Operational complexity | Medium (deployment, restricts) | Low (Postgres) | Low (Postgres) |

29. **At this scale, infra is noise next to LLM cost.** Optimise prompt length and caching first; vector DB second.

30. **Always set a billing budget alert.** Embedding-loop bugs and unbounded ingest jobs are the #1 reason for surprise bills.

---

## Multi-Region Considerations

31. **Pick the region closest to your serving cluster.** `asia-east1` for Taiwan-served workloads; cross-region adds 50–150ms.

32. **Vertex AI Vector Search supports multi-region endpoint deployment** — pay per node per region. AlloyDB and Cloud SQL replicas can be cross-region read replicas.

33. **Embeddings are region-pinned.** Re-embedding is needed if you migrate regions because dimensions and behaviour are guaranteed only within a deployment.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Cloud SQL tier too small; index build OOMs | At least `db-custom-4-16384`; monitor `pg_stat_progress_create_index` |
| Embedding dim mismatch between ingest and query | Pin model + dim in collection metadata; reject mixed |
| Vector Search index left deployed in dev 24/7 | Tear down nightly; or share dev/staging endpoint |
| Document AI invoked from request thread | Move to Cloud Run job triggered by GCS upload |
| RAG Engine used for code; bad chunks; bad recall | Pick DIY (Spring AI + pgvector) for code |
| Cross-region: cluster in `asia-east1`, vector store in `us-central1` | Co-locate; or accept 100ms latency tax |
| Model upgrade without re-embedding | Coordinated migration: new collection, dual-write, switch reads, retire old |

---

## Pre-Production Checklist

- [ ] Vector store choice matches expected scale and existing infra
- [ ] Embedding model pinned per collection; dimensions match
- [ ] Cloud SQL / AlloyDB tier sized for vector ops; not the smallest
- [ ] Vector Search endpoint is private (PSC), not public
- [ ] Service accounts: least-privilege per workload (`aiplatform.user`, not `aiplatform.admin`)
- [ ] Region co-located with serving cluster
- [ ] Quotas pre-requested for tokens-per-minute and concurrent predictions
- [ ] Cost monitoring + budget alert
- [ ] Reindex / re-embedding migration plan documented
- [ ] Dev / staging environments don't keep an idle deployed index 24/7

---

## Related Skills

- [`gcp-fundamentals`](../gcp-fundamentals/SKILL.md) — IAM, ADC, quotas
- [`gcp-cloud-sql-spring`](../../engineering/gcp-cloud-sql-spring/SKILL.md) — pgvector connectivity
- [`spring-ai-rag`](../../engineering/spring-ai-rag/SKILL.md) — Spring side of the integration
- [`rag-deep-dive`](../../ai-engineering/rag-deep-dive/SKILL.md) — RAG strategy
- [`rag-ingestion-pipeline`](../../ai-engineering/rag-ingestion-pipeline/SKILL.md) — feeding the store
- [`gke-deployment`](../gke-deployment/SKILL.md) — running the RAG service in GKE
