---
name: llm-cost-optimization
description: >
  Optimizing LLM application costs — model selection and routing, prompt caching,
  batching, token budgeting, output length control, and when to use smaller
  models. Use this skill when LLM spend is growing faster than value, or when
  designing a cost-conscious agent architecture.
category: ai-engineering
tags: [cost, optimization, llm, tokens, caching, routing]
related: [prompt-caching, context-engineering, agent-harness-design, fine-tuning-guide]
---

# LLM Cost Optimization

> The goal isn't minimum cost — it's maximum value per dollar. A $0.01 call that's wrong is more expensive than a $0.10 call that's right.

## When to Use This Skill

- Monthly LLM bill is growing faster than expected
- Designing a production agent with cost constraints
- Choosing between model tiers for different tasks
- Investigating why token usage is high

---

## Cost Anatomy

```
Cost = Σ (input_tokens × input_rate + output_tokens × output_rate) per call
     + cache_write_tokens × cache_write_rate
     - cache_read_tokens × cache_read_discount
```

### Current approximate rates (2025, varies by provider)

| Model tier | Input (per 1M tokens) | Output (per 1M tokens) |
|------------|----------------------|------------------------|
| Frontier (Opus/GPT-5) | $15-30 | $60-150 |
| Standard (Sonnet/GPT-4.1) | $3-5 | $15-20 |
| Fast (Haiku/GPT-5-mini) | $0.25-1 | $1-5 |

**Input tokens dominate cost for agents.** Long conversations, big tool results, large system prompts.

---

## The Optimization Playbook

### 1. Measure First

1. **Log tokens per call** (input, output, cached).
2. **Track cost per session, per user, per task type.**
3. **Identify the top 3 cost drivers.** Usually: large system prompts, verbose tool results, long conversations.

Don't optimize blindly. The top cost driver might not be what you think.

### 2. Model Routing

Not every task needs the best model.

| Task | Model tier | Why |
|------|-----------|-----|
| Complex reasoning, planning, code generation | Frontier (Opus) | Quality ceiling matters |
| Standard coding, summarization, Q&A | Standard (Sonnet) | Good enough; 3-10× cheaper |
| Classification, extraction, simple formatting | Fast (Haiku) | 15-60× cheaper; fast |
| Embedding | Dedicated embedding model | Not an LLM task |

4. **Route by task complexity.** A classifier (often a fast model or regex) decides which model handles each request.
5. **Default to the cheapest model that meets quality.** Upgrade only when quality drops below threshold.
6. **Eval each tier.** Run your eval set on Haiku, Sonnet, Opus. If Haiku scores 90%+ on a task type, use Haiku.

### 3. Prompt Caching

See [`prompt-caching`](../prompt-caching/SKILL.md) for details.

7. **Cache the stable prefix.** System prompt + tool definitions + loaded docs.
8. **90% cost reduction on cached input tokens.**
9. **Measure cache hit rate.** Target > 70%. Below that, find what's causing misses.

### 4. Context Reduction

10. **Don't send full file contents when a summary suffices.**
11. **Truncate tool results.** Set max return size per tool.
12. **Compact older conversation turns.** See [`context-engineering`](../context-engineering/SKILL.md).
13. **Remove tools the agent doesn't need for the current task.** Each tool definition costs 500-1500 tokens.

### 5. Output Length Control

14. **Set `max_tokens` appropriately.** Don't allocate 4096 for a task that needs 200.
15. **Instruct conciseness in the prompt.** "Respond in 2-3 sentences" saves 80% on verbose answers.
16. **Use structured output (tool calls).** Structured responses are typically shorter than freeform.

### 6. Batching

17. **Batch API** (Anthropic, OpenAI) for non-real-time tasks: 50% cost reduction, higher latency.
18. **Batch similar requests.** "Classify these 10 items" in one call vs 10 separate calls.

### 7. Deduplication

19. **Cache application-level results.** If 100 users ask the same question, answer once and cache.
20. **Semantic deduplication.** If user asks what was just answered 2 turns ago, serve from conversation, don't re-query.

---

## Cost Budgets

### Per-session budgets

```
If session_cost > $1 → warn
If session_cost > $5 → halt (require human approval)
If user_daily_cost > $20 → rate limit
```

21. **Set per-session and per-user cost limits.** Prevents runaway loops.
22. **Log sessions that hit limits.** They reveal design problems or adversarial usage.

### Per-task cost targets

| Task type | Reasonable cost target |
|-----------|----------------------|
| Simple Q&A | $0.001 - $0.01 |
| Code generation (single file) | $0.01 - $0.05 |
| Full PR (multi-file agent loop) | $0.10 - $1.00 |
| Complex research (20+ tool calls) | $0.50 - $5.00 |

These are rough guides — adjust to your value per task.

---

## Measuring ROI

Cost optimization means nothing without quality:

```
Value per dollar = (quality metric × volume) / total cost
```

23. **Track quality alongside cost.** If quality drops 20% to save 10% on cost, you lost.
24. **A/B test model tiers on real traffic.** Compare quality + cost + latency.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Using Opus for everything | Route by task; default to cheapest sufficient |
| No token logging | Log input/output/cached tokens per call |
| 100K-token context on simple Q&A | Reduce context to what's needed |
| No cost limits | Per-session and per-user budgets |
| Optimizing for cost without measuring quality | Always evaluate quality alongside cost |
| Prompt too long to cache effectively | Restructure: stable prefix + dynamic suffix |
| One-call-per-item when batch works | Batch API or multi-item prompts |
| No caching at application level | Cache repeated identical queries |

---

## Cost Optimization Checklist

- [ ] Token usage logged per call (input, output, cached)
- [ ] Cost tracked per session, per user, per task type
- [ ] Top 3 cost drivers identified
- [ ] Model routing in place (frontier/standard/fast per task)
- [ ] Prompt caching enabled; hit rate > 70%
- [ ] Context size bounded (compaction, truncation)
- [ ] Output length controlled (max_tokens, prompt instructions)
- [ ] Per-session and per-user cost limits set
- [ ] Batch API used for non-real-time tasks
- [ ] Quality measured alongside cost (no blind cost cutting)

---

## Related Skills

- [`prompt-caching`](../prompt-caching/SKILL.md) — 90% input cost reduction on stable prefixes
- [`context-engineering`](../context-engineering/SKILL.md) — reducing what's in context
- [`agent-harness-design`](../agent-harness-design/SKILL.md) — harness controls token flow
- [`agent-observability`](../agent-observability/SKILL.md) — cost telemetry in production
