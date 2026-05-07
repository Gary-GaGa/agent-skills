---
name: query-rewriting-rag
description: >
  Improving RAG retrieval recall by rewriting queries before search — HyDE,
  multi-query expansion, decomposition, step-back prompting, and routing.
  Use this skill when a RAG pipeline retrieves the wrong chunks despite a
  sensible question, or complex multi-hop questions fail consistently.
category: ai-engineering
tags: [rag, retrieval, llm, search, prompt, optimization]
keywords: [HyDE, query rewriting, query expansion, multi-query, query decomposition, step-back prompting, routing, RAG fusion]
related: [rag-deep-dive, rag-for-code, graphrag-multi-service, agentic-rag, prompt-engineering]
---

# Query Rewriting for RAG

> The question the user types and the way the answer is written rarely match. Closing that gap is often the single biggest win for retrieval recall.

## When to Use This Skill

- A RAG pipeline returns the wrong chunks despite a sensible question
- Complex multi-hop questions ("which services consume events from X?") fail consistently
- Code RAG: natural-language questions don't surface code with matching API names
- You've tuned chunking, embedding, and reranking and still want more recall

For RAG fundamentals, pair with [`rag-deep-dive`](../rag-deep-dive/SKILL.md). For code-specific concerns, [`rag-for-code`](../rag-for-code/SKILL.md). For tool-calling retrieval, [`agentic-rag`](../agentic-rag/SKILL.md).

---

## Why Rewriting Helps

The user types: *"how do we cancel an order?"*

The code says: `@PostMapping("/{id}/cancel") void cancel(@PathVariable UUID id)` and `@Transactional public void cancelOrder(...)`.

A dense retriever that embeds the user's prose poorly resolves to the code: low lexical overlap, weak semantic match. **Rewriting the query** — into a hypothetical answer, a list of variants, or smaller sub-questions — closes the gap.

1. **Rewriting is cheaper than reranking** at retrieval time but more expensive than direct search. Use it when retrieval recall is the bottleneck, not when it's already high.

2. **Rewriting is not query understanding.** It's expanding the surface area of what you search for. Don't expect it to fix bad chunks or missing data.

---

## Technique 1 — HyDE (Hypothetical Document Embeddings)

Generate a *fake answer* with an LLM, then embed and search using that.

```
User: "how do we cancel an order?"
LLM: "To cancel an order, call POST /api/v1/orders/{id}/cancel.
       The OrderService cancelOrder method marks the order CANCELLED
       and publishes an OrderCancelled event."
embed(LLM_answer) → search → retrieve top-K
```

3. **Why it works**: the embedding of a plausible answer is structurally closer to the real answer's chunks than the embedding of the question.

4. **HyDE is gold for code RAG.** The hypothetical answer naturally introduces method names (`cancelOrder`), endpoint paths (`/orders/{id}/cancel`), and event names (`OrderCancelled`) that the dense retriever otherwise can't surface.

5. **Use a small, fast model for the rewrite.** A 70B model is overkill; an 8B Haiku/Gemini-Flash is fine. The hypothetical answer doesn't need to be correct — it needs to be plausible.

6. **Search with both** the original query and the HyDE answer. RRF-merge the top-K of each. You don't lose precise lexical matches that way.

---

## Technique 2 — Multi-Query Expansion

Generate N paraphrases / variants, retrieve for each, fuse.

```
Original: "how does authentication work?"
Variants:
  - "how is the user identity verified?"
  - "what authentication mechanism is used (JWT, session, OAuth)?"
  - "where is the SecurityFilterChain configured?"
  - "how are unauthenticated requests rejected?"
```

7. **Search each variant; merge with RRF.** Recall improves; precision drops slightly; reranking handles the precision side.

8. **3–5 variants is the sweet spot.** More than 5 starts adding noise without recall gains and costs more.

9. **Tune the variant prompt to your domain.** A generic "give me 5 paraphrases" yields paraphrases. A code-aware "give me 5 ways an engineer might phrase this looking for code" yields better variants.

---

## Technique 3 — Query Decomposition

For multi-hop / compound questions, split.

```
Original: "What events does the orders service publish, and which services consume them?"
Decomposed:
  1. "What events does the orders service publish?"
  2. "What topics is each event published to?"
  3. "Which services subscribe to those topics?"
```

10. **Decomposition fits multi-hop questions** that no single chunk can answer. Each sub-question retrieves its own context; the final synthesis happens in the answer prompt.

11. **Use a planner model**: prompt it to either answer directly or output a list of sub-questions in JSON. Keep the prompt strict; off-format output silently breaks the pipeline.

12. **Don't over-decompose.** "How does X work?" is one question. Decomposition adds latency and cost; reach for it only when the question structure demands it.

---

## Technique 4 — Step-Back Prompting

Generate a more *abstract* version of the question, retrieve, then answer the original.

```
User: "Why does the orders service throw OptimisticLockingFailureException
       under load?"
Step-back: "How does the orders service handle concurrent updates?"
```

13. **Step-back retrieves architectural context** that the specific question can't reach: design docs, ADRs, the relevant entity's `@Version` annotation, transaction patterns.

14. **Combine step-back retrieval with the original question's retrieval.** Send both context sets to the answer model; let it weigh.

---

## Technique 5 — Routing

Not strictly rewriting, but adjacent: *route* the question to a strategy.

```
classify(question) →
  ├─ "definition / lookup" → lexical-first retrieval
  ├─ "behaviour / how" → HyDE + dense
  ├─ "relationship / cross-service" → graph + dense (graphrag-multi-service)
  ├─ "trace / error" → log/trace store; not dense at all
  └─ default → multi-query + rerank
```

15. **A small classifier (rule-based or model-based) up front** is cheaper than running every technique on every query.

16. **Routing rules first; LLM classifier when rules fall short.** "Contains stack trace" → trace store. "Starts with 'why'" → step-back. "Contains 'and which'" → decomposition.

17. **Log the route taken.** When recall regresses, you want to know whether the router shifted or the underlying retriever did.

---

## Combining Techniques

A robust pipeline runs multiple legs in parallel:

```
question
  ├─► original query   → dense + lexical → top 20
  ├─► HyDE             → dense           → top 20
  ├─► multi-query (×3) → dense           → top 20 each
  └─► (optional) decomp → dense per sub  → top 10 each
                          │
                       RRF merge
                          │
                       Rerank → top 8 → answer
```

18. **Run legs in parallel.** Total latency = max(legs), not sum.

19. **Each leg fetches more than you'd serve** because RRF and reranking dilute. 20 per leg → ~8 final is typical.

20. **Cap fan-out to control cost.** HyDE call + 3 query rewrites + decomposition × 3 sub-questions = up to 8 model calls. Most queries don't need them all; route.

---

## Caching Rewrites

21. **Same question → same rewrites.** Cache by hashed normalised question (lowercase, strip punctuation). Hit rate is high in production; cost recovery is immediate.

22. **HyDE answers can be cached more aggressively** than user queries because they're synthetic. Pre-generate for FAQs; serve from cache.

23. **Invalidate when the rewrite prompt or model changes.** Otherwise a prompt regression silently affects retrieval.

---

## Evaluation

24. **Compare retrieval recall@K with and without each technique** on your eval set. Don't compose techniques without measurement; sometimes HyDE + multi-query is worse than HyDE alone (noise wins).

25. **Track per-route metrics.** A router that sends everything down one branch is fine; one whose branches diverge in quality silently is a bug.

26. **Watch for over-fitting to the eval set.** A rewrite that wins on 50 questions might lose on production traffic. Hold out a set; recheck monthly.

---

## When NOT to Rewrite

27. **Lexical/structural queries** — `OrderRepository.findByStatus`, error codes, stack traces. Rewriting can drift from the exact identifier you need. Send to lexical-first retrieval.

28. **Trivial questions** — "what is `Order`?" — direct embedding finds it. Rewriting adds latency for nothing.

29. **Questions referencing the conversation history** — "and what about the next one?" — rewrite using *conversation context*, not in isolation. This is the stand-alone-question rewrite, a different technique.

30. **High-throughput, low-latency endpoints** where the per-query rewrite cost is unaffordable. Use precomputed query templates instead.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| HyDE hallucinates a method name that doesn't exist; retrieves wrong chunks | Always combine with original query; don't trust HyDE alone |
| 5 multi-queries return the same paraphrase 5 times | Variant prompt isn't actually generating diverse phrasings; tune or model-up |
| Decomposition recurses or loops | Cap depth at 1; reject nested decomposition output |
| Cost per query 5×'s without recall improvement | Route; don't run all techniques on all queries |
| Cache hit rate near zero | Question normalisation (lowercase, trim, strip punctuation) before hashing |
| Step-back goes too abstract; retrieves nothing | Constrain the step-back prompt: "more abstract but in the same domain" |

---

## Pre-Production Checklist

- [ ] Pipeline runs original-query retrieval as a baseline always
- [ ] HyDE for natural-language questions over code/docs corpora
- [ ] Multi-query (3–5 variants) merged via RRF
- [ ] Decomposition only for compound/multi-hop questions; depth capped at 1
- [ ] Routing rules log the chosen path
- [ ] Rewrite cache by normalised question hash
- [ ] Cost guardrail: max model calls per query
- [ ] Eval set measures recall with/without each technique
- [ ] Lexical/error/stack-trace queries bypass rewriting

---

## Related Skills

- [`rag-deep-dive`](../rag-deep-dive/SKILL.md) — retrieval fundamentals these techniques sit on top of
- [`rag-for-code`](../rag-for-code/SKILL.md) — HyDE is especially valuable for code RAG
- [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md) — relationship questions belong on the graph leg
- [`agentic-rag`](../agentic-rag/SKILL.md) — alternative to rewriting: let the agent retrieve iteratively
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — the rewrite prompts are prompts
- [`llm-cost-optimization`](../llm-cost-optimization/SKILL.md) — rewriting multiplies model calls
