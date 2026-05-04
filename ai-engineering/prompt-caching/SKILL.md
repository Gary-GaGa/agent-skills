---
name: prompt-caching
description: >
  Practical guide to LLM prompt caching — what it is, when it helps, cache
  breakpoint placement, hit rate optimization, and when caching hurts. Focused
  on Anthropic's prompt caching but principles transfer. Use this skill when
  optimizing the cost and latency of an agent or chatbot at scale.
category: ai-engineering
tags: [caching, performance, cost, anthropic, claude]
related: [context-engineering, agent-harness-design, prompt-engineering, llm-cost-optimization]
---

# Prompt Caching

> Prompt caching can cut input cost 90% and TTFT 50%+ on repeated calls. But only if you understand what stays cacheable. Move one byte and you blow the cache.

## When to Use This Skill

- Building any production LLM app with > 1K daily calls
- Repeated calls share large stable prefixes (system prompt, tool defs, docs)
- TTFT (time-to-first-token) latency matters
- Investigating why your bill is higher than expected

---

## What Caching Is, Mechanically

Anthropic / OpenAI / others implement prompt caching by:

1. You mark a prefix of the prompt as cacheable.
2. The provider hashes that prefix and stores the model's internal computation.
3. On a subsequent call with the same prefix, computation is reused.
4. You pay much less for the cached input tokens (typically 10% of normal cost).
5. Cache entries expire after some TTL (Anthropic: 5 minutes default, 1 hour with extended).

**Implication:** Caching pays off when you have a large, stable prompt prefix and call it repeatedly within the TTL window.

---

## Cache-Friendly Prompt Architecture

```
┌───────────────────────────────────────────┐
│  STABLE  (cacheable)                      │
│  - System prompt                          │
│  - Tool definitions                       │
│  - Few-shot examples                      │
│  - Reference docs / context               │
├───────────────────────────────────────────┤  ← cache breakpoint
│  STABLE-PER-SESSION                       │
│  - Earlier conversation history           │
├───────────────────────────────────────────┤  ← cache breakpoint
│  DYNAMIC                                  │
│  - Current user message                   │
│  - Latest tool result                     │
└───────────────────────────────────────────┘
```

**Order matters absolutely.** The cacheable prefix must come first. One mutating byte breaks everything after it.

---

## Anthropic-Specific Mechanics

### Cache breakpoints

You mark up to 4 cache breakpoints in a request. Each breakpoint caches everything from the start up to that point.

```python
# Pseudocode
messages = [
    {"role": "system", "content": [
        {"type": "text", "text": LONG_SYSTEM_PROMPT,
         "cache_control": {"type": "ephemeral"}},   # ← breakpoint 1
    ]},
    {"role": "user", "content": [
        {"type": "text", "text": LONG_DOC_CONTEXT,
         "cache_control": {"type": "ephemeral"}},   # ← breakpoint 2
        {"type": "text", "text": current_user_message},  # not cached
    ]}
]
```

### Pricing

| Type | Cost (relative to standard input) |
|------|-----------------------------------|
| Cache write | 1.25× (extra to populate) |
| Cache read (hit) | 0.1× (90% discount) |
| Standard input (no cache) | 1.0× |

**The break-even** for ephemeral cache (5 min TTL): roughly 2 cached calls before saving money. For high-traffic agents this is trivial; for occasional calls, consider whether caching saves anything.

### TTL options

- **Ephemeral (default):** 5 minutes — good for active sessions
- **Extended:** 1 hour (separate pricing) — good for shared system prompts across users

---

## Where to Place Breakpoints

A common pattern with 3-4 breakpoints:

```
Breakpoint 1: After system prompt + tool defs
              (stable across all calls system-wide)

Breakpoint 2: After loaded skills / docs / project context
              (stable per-project or per-task)

Breakpoint 3: After older conversation history
              (stable until next compaction)

Breakpoint 4 (or no breakpoint): Latest exchange
              (always changing)
```

Why each layer is a breakpoint: each can survive different kinds of changes. If only the user's latest message changes, layers 1-3 are still cacheable. If a new doc loads (layer 2 changes), layer 1 still hits.

---

## Maintaining Cache Hit Rate

This is where teams lose 50% of potential savings.

### Don't put dynamic content in stable position

❌ `"You are an agent. Current time: 2024-01-15T14:32:01. Helpful instructions..."`

The timestamp invalidates the cache every second. Move it:

✅ `"You are an agent. Helpful instructions... \n[Current time will be in user message]"`

### Don't reorder messages

The cache key is the literal byte sequence. Swapping `tools` and `system` in the request body busts the cache, even if semantically equivalent.

### Don't fluctuate token boundaries

Subtle changes — extra space, different unicode normalization, different JSON serialization order — produce different hashes.

1. **Pin serialization.** Use stable JSON (sorted keys, no trailing space).
2. **Don't include random nonces or session IDs in cached content.**
3. **Monitor hit rate.** If it's below 70% on stable workloads, find what's mutating.

### Cache-aware compaction

When you compact older history (replace turns with a summary), you've changed the cached middle. The cache for layer 3 is gone; the next call rebuilds it. Plan compactions to minimize churn.

---

## Measurement: Track Cache Hit Rate

Every API response includes cache metrics:

```json
{
  "usage": {
    "input_tokens": 100,
    "cache_creation_input_tokens": 5000,
    "cache_read_input_tokens": 10000,
    "output_tokens": 200
  }
}
```

Calculate:
- **Cache hit rate** = `cache_read / (cache_read + cache_creation + input)` ideal > 70%
- **Effective cost** = cache_creation × 1.25 + cache_read × 0.1 + input × 1.0 (per token rate)

Log per request and aggregate. **If cache hit rate is low, the architecture is wrong, not the model.**

---

## When Caching Hurts

| Situation | Why caching is worse |
|-----------|---------------------|
| Single-shot calls (one-off scripts) | Cache write overhead, no benefit |
| Highly variable system prompts | Constant cache misses; pay write penalty repeatedly |
| Prompts < ~1K tokens | Overhead exceeds savings |
| Calls spread far apart in time | Cache TTL expires; behaves like no cache |
| Different users / sessions with no shared structure | No reuse; pure overhead |

For these, just don't cache — or cache only the system prompt at most.

---

## Common Patterns

### A. Stable system prompt only

For chatbots where the system prompt is large and stable per-app:

```
[breakpoint] System prompt (5K tokens, cacheable)
[breakpoint] Conversation so far
Current user message
```

Hit rate: very high. Savings: large on input cost.

### B. RAG with stable corpus

When retrieving from a fixed corpus (documentation, knowledge base):

```
[breakpoint] System prompt + tool defs
[breakpoint] Top-K retrieved docs (stable per query)
Current user message
```

If users ask similar questions, the retrieved docs may repeat — additional savings.

### C. Coding agent with project context

Claude Code-style agent loading project files:

```
[breakpoint] System prompt (very stable)
[breakpoint] CLAUDE.md + project skills (stable per project)
[breakpoint] Loaded files / earlier turns
Current user message + tool result
```

Hit rate stays high across sessions in the same project.

### D. Long-running agent loop

Within a single session, every iteration after the first benefits:

```
Iteration 1: cache write + standard input cost
Iteration 2-N: cache read for everything before the latest exchange
```

For 20-iteration agent loops, this is a 50%+ cost reduction on input.

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| Putting `current_time` in system prompt | Bust cache every call | Move to user message |
| Reordering tool defs randomly | Different hash each time | Sort tools deterministically |
| Caching tiny prompts (< 1K tokens) | Overhead > savings | Don't cache |
| 5+ breakpoints (max is 4) | API rejects | Consolidate |
| Never measuring hit rate | Don't know if caching works | Log it from day 1 |
| Mixing user-specific data into "stable" prefix | Per-user cache miss | Move to per-user layer |
| One huge cache entry of everything | Any change invalidates all | Multiple breakpoints layer-by-layer |
| Cache + non-deterministic prompt assembly | Subtle misses | Pin assembly order |

---

## Migrating Other Providers

OpenAI's prompt caching is automatic and structurally similar (cache the prefix; reuse on stable prefix). Differences:

- Automatic vs explicit breakpoints
- Pricing model
- TTL
- Coverage by model

The architectural advice (stable prefix first, dynamic last; minimize churn; measure hit rate) transfers across providers.

---

## Implementation Workflow

When adding caching to an existing app:

1. **Analyze prompt structure.** What's stable per-call vs per-session vs per-user?
2. **Reorder messages.** Stable → less stable → dynamic.
3. **Identify breakpoint candidates.** 2-4 layers usually enough.
4. **Pin serialization.** Make tool defs and other JSON deterministic.
5. **Add cache_control markers.**
6. **Run a sample of typical requests.** Measure hit rate.
7. **Iterate.** If hit rate < expected, find the mutation source.
8. **Monitor in production.** Alert on hit rate drops.

---

## Checklist

- [ ] Stable content (system prompt, tools, docs) is at the beginning of the prompt
- [ ] Dynamic content (timestamps, user input, tool results) is at the end
- [ ] Cache breakpoints are placed at natural stability boundaries (1-4)
- [ ] Tool definitions are deterministically serialized
- [ ] No per-user / per-session content in the "stable" cached layer
- [ ] Cache hit rate is logged per request
- [ ] Hit rate target is set (e.g. > 70% for steady-state workloads)
- [ ] Alerts fire on hit rate degradation
- [ ] You've measured cost before/after caching to validate savings

---

## Related Skills

- [`context-engineering`](../context-engineering/SKILL.md) — context layout determines cacheability
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — keep system prompt stable for caching
- [`agent-harness-design`](../agent-harness-design/SKILL.md) — harness controls how prompts are assembled
- [`agent-observability`](../agent-observability/SKILL.md) — track cache hit rate in production telemetry
