# Drift Surface — `gcp-vertex-ai-rag`

> **Last verified: 2026-05-07.** Items below change frequently. Verify against the linked GCP docs before quoting them.

The parent skill ([`SKILL.md`](../SKILL.md)) holds the durable design (decision tree, IAM principles, schema patterns). This file collects everything that goes stale within months — model names, library versions, pricing, GA status, gcloud command shapes — with a canonical URL for each so it's mechanical to re-verify.

When `validate.py` warns that this skill is past its `freshness_budget`, walk this file top-to-bottom, hit each verify URL, and bump `last_verified` in the parent `SKILL.md` frontmatter once everything still matches.

---

## Embedding models on Vertex AI

| Model | Dims | Languages | Notes |
|---|---|---|---|
| `text-embedding-005` | 768 | English | Latest stable general-purpose model as of verify date |
| `text-multilingual-embedding-002` | 768 | 100+ | Multilingual; small quality dip vs English-only |
| `gemini-embedding-001` | 3072 (truncatable to 768/1536) | Multilingual + code | Highest quality; supports Matryoshka dimension truncation |
| `text-embedding-large-exp-03-07` | 3072 | English | Experimental large model — marked **Experimental** by Google |

**Verify at:** <https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings>

What changes here:
- Model lifecycle (preview → GA → deprecated → removed)
- Dimensions and truncation support
- New models replacing old ones

When you see a model name in this file that isn't in the linked page's "currently available" list, it's gone. Reindex with the replacement.

---

## Vertex AI RAG Engine SDK

```python
# As of verify date this lives under vertexai.preview — check the import path
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

**Verify at:** <https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview>

Likely changes:
- `vertexai.preview.rag` → `vertexai.rag` once GA (import path move)
- New methods (`update_corpus`, fine-grained chunking config)
- GA status — when GA, drop the "preview" marker in the parent skill

---

## Vertex AI Vector Search index config

```bash
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
gcloud ai index-endpoints create --display-name=rag-endpoint --region=asia-east1
gcloud ai index-endpoints deploy-index <ENDPOINT_ID> \
    --deployed-index-id=rag_v1 \
    --display-name=rag_v1 \
    --index=<INDEX_ID>
```

**Verify at:**
- Index config: <https://cloud.google.com/vertex-ai/docs/vector-search/create-manage-index>
- Endpoint deployment: <https://cloud.google.com/vertex-ai/docs/vector-search/deploy-index-public>

Likely changes:
- `algorithm_config` shape (Google ships new ANN algorithms periodically)
- `gcloud ai` subcommand renames (`indexes` → `vector-search` etc.)
- New index types (e.g. ScaNN configurations)

---

## AlloyDB AI ScaNN syntax

```sql
CREATE INDEX idx_rag_chunks_scann
    ON rag_chunks USING scann (embedding cosine)
    WITH (num_leaves = 1000);
```

**Verify at:** <https://cloud.google.com/alloydb/docs/ai/store-index-query-vectors>

ScaNN in AlloyDB is recent; index parameters and supported distance functions evolve. Check the page above for current operator class names and `WITH` options.

---

## IAM role names

App / workload service-account roles:

| Workload | Role(s) |
|---|---|
| Spring app SA | `roles/aiplatform.user` (chat + embedding APIs), `roles/cloudsql.client` + `roles/cloudsql.instanceUser` (pgvector via Java Connector) |
| Ingestion job SA | Above + `roles/storage.objectViewer` (GCS sources) |
| Document AI processor SA | `roles/documentai.apiUser` |
| Vector Search query SA | `roles/aiplatform.user` (covers vector search calls) |

**Verify at:**
- Vertex AI roles: <https://cloud.google.com/vertex-ai/docs/general/access-control>
- Cloud SQL roles: <https://cloud.google.com/sql/docs/postgres/iam-roles>
- Document AI roles: <https://cloud.google.com/document-ai/docs/access-control/iam-roles>

Roles are renamed less often than APIs but happen (e.g. when Google splits a coarse role into finer ones). The principle in the parent skill — least privilege per workload, no `admin` on apps — stays.

---

## Cloud SQL tier sizing for vector ops

| Workload | Minimum tier (verify date) |
|---|---|
| Production RAG (5M chunks, ~10 QPS) | `db-custom-4-16384` (4 vCPU, 16 GB) |
| Production RAG (10M+ chunks) | `db-custom-8-32768` or migrate to AlloyDB |
| Dev / staging | `db-custom-2-7680` |

Smaller tiers OOM during HNSW index build.

**Verify at:** <https://cloud.google.com/sql/docs/postgres/instance-settings>

---

## Cost sketch (very rough, verify date)

For a 5M-chunk code RAG, ~10 QPS, asia-east1:

| Item | Vertex AI Vector Search | AlloyDB AI | pgvector on Cloud SQL |
|---|---|---|---|
| Storage / index | 1 e2 deployed node, ~$200/mo | 4 vCPU instance, ~$400/mo | db-custom-4-16384, ~$300/mo |
| Embedding (one-time) | $50–200 (5M chunks × ~200 tok) | same | same |
| Query embedding | ~$20/mo | same | same |
| Chat (Gemini 2.5 Pro tier) | $1k–5k/mo (workload-dependent) | same | same |
| **Total infra** | **$200–500/mo** | **$400–700/mo** | **$300–500/mo** |
| Operational complexity | Medium | Low (Postgres) | Low (Postgres) |

**Verify at:**
- Vertex AI pricing: <https://cloud.google.com/vertex-ai/pricing>
- Cloud SQL pricing: <https://cloud.google.com/sql/pricing>
- AlloyDB pricing: <https://cloud.google.com/alloydb/pricing>

Numbers are within ±30% of reality at the verify date and re-quoted from the pricing pages. Use the [GCP pricing calculator](https://cloud.google.com/products/calculator) for any decision that depends on more than one significant figure.

---

## Library / SDK versions referenced in the parent skill

| Component | Version pin | Verify at |
|---|---|---|
| Spring AI | `1.0.x` GA | <https://github.com/spring-projects/spring-ai/releases> |
| Spring Cloud GCP | `5.x` | <https://github.com/GoogleCloudPlatform/spring-cloud-gcp/releases> |
| Cloud SQL Java Connector (`postgres-socket-factory`) | `1.19.x` | <https://github.com/GoogleCloudPlatform/cloud-sql-jdbc-socket-factory/releases> |
| Cloud SQL Auth Proxy | `2.13.x` | <https://github.com/GoogleCloudPlatform/cloud-sql-proxy/releases> |
| pgvector | latest, paired with Postgres 15+ | <https://github.com/pgvector/pgvector/releases> |

When the parent skill quotes a specific version (`1.19.1`, `2.13.0`), it was current at the verify date. Bump only after running the smoke tests in [`spring-ai-rag`](../../../engineering/spring-ai-rag/SKILL.md).

---

## Re-verification procedure

1. Open each `Verify at:` URL above; spot-check the value.
2. Update inline tables / numbers in this file as needed.
3. Bump `last_verified` in `../SKILL.md` frontmatter.
4. Run `python3 scripts/validate.py` — the freshness warning should clear.
5. Open a PR titled `chore(drift): re-verify gcp-vertex-ai-rag YYYY-MM`.

If a major drift appears (model retired, library renamed, pricing model changed by >50%), open a follow-up issue rather than silently editing — it likely affects sibling skills too.