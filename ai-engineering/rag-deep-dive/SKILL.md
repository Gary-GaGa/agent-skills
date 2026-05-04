---
name: rag-deep-dive
description: >
  Retrieval-Augmented Generation deep dive — chunking strategies, embedding
  models, vector databases, retrieval quality, reranking, hybrid search, and
  evaluation. Use this skill when building a RAG pipeline, debugging poor
  retrieval quality, or choosing between RAG approaches.
category: ai-engineering
tags: [rag, retrieval, embedding, vector-db, llm, search]
related: [context-engineering, prompt-engineering, agent-evaluation]
---

# RAG Deep Dive

> RAG turns a general model into a domain expert by grounding its answers in your data. The retrieval quality is the ceiling — no amount of prompting fixes bad retrieval.

## When to Use This Skill

- Building a knowledge-base Q&A system
- Grounding an agent's answers in documentation or internal data
- Debugging "the model doesn't know about X" (it's a retrieval miss)
- Choosing chunking / embedding / vector DB strategy
- Evaluating RAG pipeline quality

---

## The RAG Pipeline

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Documents│────►│ Chunking │────►│ Embedding│────►│ Vector DB│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                         │
User query ─► Embed query ─► Similarity search ──────────┘
                                    │
                              Top-K chunks
                                    │
                            ┌───────▼───────┐
                            │  (Reranker)   │  ← optional
                            └───────┬───────┘
                                    │
                            ┌───────▼───────┐
                            │  LLM + context│
                            └───────┬───────┘
                                    │
                                 Answer
```

---

## 1. Chunking

### Strategy comparison

| Strategy | Chunk size | Pros | Cons |
|----------|-----------|------|------|
| **Fixed-size** | 500-1000 tokens, 100-200 overlap | Simple, predictable | Cuts mid-sentence / mid-idea |
| **Semantic (paragraph/section)** | Natural boundaries (headings, `\n\n`) | Coherent chunks | Uneven sizes |
| **Recursive** | Split by `\n\n`, then `\n`, then sentence, then word | Balances coherence and size | More complex |
| **Document-aware** | Markdown headings, code blocks, API endpoints | Best coherence per domain | Requires format-specific logic |

### Rules

1. **Chunk size: 200-800 tokens is the sweet spot.** Smaller = more precise but noisier. Larger = more context but diluted relevance.
2. **Overlap by 10-20%.** Prevents cutting important ideas at boundaries.
3. **Include metadata.** Each chunk carries: `source`, `section`, `page`, `url`. Critical for citations.
4. **Don't chunk code the same as prose.** Code needs function-level or file-level chunks, not token-based splitting.

---

## 2. Embedding

### Model selection

| Model | Dims | Speed | Quality |
|-------|------|-------|---------|
| OpenAI `text-embedding-3-small` | 1536 | Fast | Good |
| OpenAI `text-embedding-3-large` | 3072 | Medium | Better |
| Cohere `embed-english-v3` | 1024 | Fast | Very good |
| `bge-large-en-v1.5` (open source) | 1024 | Self-host | Good |
| Voyage AI `voyage-3` | 1024 | Fast | Excellent for code |

5. **Match embedding model to your domain.** Code-focused → Voyage AI or CodeBERT. General → OpenAI or Cohere.
6. **Same model for indexing and querying.** Different models produce incompatible vectors.
7. **Normalize embeddings** if your DB supports cosine similarity natively.

---

## 3. Vector Database

| DB | Type | Strengths |
|----|------|-----------|
| **pgvector** (PostgreSQL) | Extension | Familiar SQL, no new infra, good for < 10M vectors |
| **Pinecone** | Managed SaaS | Zero-ops, fast, metadata filtering |
| **Weaviate** | Self-hosted/cloud | Hybrid search (vector + keyword), rich schema |
| **Qdrant** | Self-hosted/cloud | Rust, fast, good filtering |
| **ChromaDB** | Embedded | Prototyping, single-machine |

8. **For < 1M vectors and a PostgreSQL stack, start with pgvector.** No new infra.
9. **For > 10M vectors or extreme latency needs, use a dedicated vector DB.**
10. **Store metadata alongside vectors.** Filter by source, date, category before similarity.

---

## 4. Retrieval

### Similarity search

```
query_embedding = embed(user_query)
results = vector_db.search(query_embedding, top_k=20, filter={"source": "docs"})
```

### Hybrid search (vector + keyword)

Combine semantic similarity with BM25 (keyword) search:

```
Vector results (semantic meaning) + BM25 results (exact keywords)
→ Merge with Reciprocal Rank Fusion (RRF)
→ Top-K final results
```

11. **Hybrid search consistently outperforms vector-only.** Especially for proper nouns, acronyms, error codes.
12. **Top-K for retrieval: 10-20.** More than needed; the reranker narrows down.

---

## 5. Reranking

A reranker scores each retrieved chunk against the query with a cross-encoder (much more accurate than embedding similarity, but slower).

```
Retrieved 20 chunks → Reranker scores each → Take top 5
```

| Reranker | Quality |
|----------|---------|
| Cohere Rerank | Excellent, API |
| `bge-reranker-v2-m3` | Good, self-host |
| Voyage Rerank | Excellent for code |

13. **Always rerank for production RAG.** Retrieval recall is high but noisy; reranking improves precision significantly.
14. **Rerank is expensive — apply on top-20, not top-1000.**

---

## 6. Context Assembly

After retrieval, assemble the prompt:

```
System: You are a helpful assistant. Answer based only on the provided context.
        If the answer is not in the context, say "I don't know."

Context:
[chunk 1: {source: docs/auth.md, content: "..."}]
[chunk 2: {source: docs/api.md, content: "..."}]

User: {query}
```

15. **Include source attribution in chunks.** The model can cite: "According to docs/auth.md..."
16. **Cap context at ~30% of the window.** Leave room for system prompt, conversation, and response.
17. **Order chunks by relevance** (best first). Primacy effect helps.
18. **Tell the model to refuse if context doesn't answer.** Reduces hallucination.

---

## Evaluation

### What to measure

| Metric | What it measures |
|--------|------------------|
| **Retrieval recall@K** | % of relevant chunks in top-K | 
| **Retrieval precision@K** | % of top-K that are relevant |
| **MRR (Mean Reciprocal Rank)** | How high is the first relevant result? |
| **Answer correctness** | Does the final answer match the expected answer? |
| **Faithfulness** | Is the answer grounded in the retrieved context (no hallucination)? |
| **Answer relevance** | Does the answer address the question? |

### Building an eval set

19. **20-50 question-answer pairs with tagged relevant chunks.** Covers retrieval and generation quality.
20. **Include "unanswerable" questions.** The system should say "I don't know", not hallucinate.
21. **Measure retrieval and generation separately.** Bad retrieval + good generation = wrong diagnosis.

---

## Common Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Correct info exists but not retrieved | Embedding mismatch; query phrasing differs from doc | Hybrid search; query rewriting |
| Retrieved but wrong chunk | Chunks too large; relevant info diluted | Smaller chunks; better boundaries |
| Retrieved but model ignores it | Context too long; critical info buried | Rerank; put best chunks first |
| Model hallucinates despite context | Weak "answer from context" instruction | Stronger grounding prompt; add "I don't know" examples |
| Proper nouns / codes not found | Embedding-only search misses exact matches | Hybrid search (BM25 + vector) |
| Stale information | Docs updated but index not | Incremental re-indexing pipeline |

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Fixed 1000-token chunks for everything | Domain-aware chunking |
| No metadata on chunks | Include source, section, date |
| Vector-only search | Add BM25 keyword search (hybrid) |
| Top-3 without reranking | Retrieve top-20, rerank to top-5 |
| "Answer from context" without examples | Add few-shot examples of grounded answers + refusals |
| No retrieval evaluation | Build a golden set; measure recall and precision |
| Same embedding model for code and prose | Use domain-specific models |
| Re-embedding everything daily | Incremental: only changed docs |

---

## Checklist

- [ ] Chunking strategy matches document types (prose vs code vs structured)
- [ ] Chunks include metadata (source, section, date)
- [ ] Embedding model matches domain
- [ ] Hybrid search enabled (vector + keyword)
- [ ] Reranker in the pipeline
- [ ] Context assembly capped at ~30% of window
- [ ] System prompt instructs "answer from context only"
- [ ] Eval set includes 20+ questions with expected answers
- [ ] Retrieval and generation evaluated separately
- [ ] "Unanswerable" questions test refusal behavior

---

## Related Skills

- [`context-engineering`](../context-engineering/SKILL.md) — RAG is a context strategy
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — grounding prompts for RAG
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — eval framework applies to RAG too
