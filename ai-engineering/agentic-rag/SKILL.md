---
name: agentic-rag
description: >
  Agentic RAG — letting an LLM agent retrieve iteratively via tools (grep,
  AST query, file read, graph traversal) instead of fixed top-K vector
  search. Use this skill when one-shot retrieval can't reach multi-hop
  answers or when code RAG needs structural exploration.
category: ai-engineering
tags: [rag, retrieval, llm, search, agent, tool, coding]
keywords: [agentic RAG, ReAct, tool calling, grep tool, ripgrep, AST query, LSP, retrieval agent, self-correcting RAG]
related: [rag-for-code, graphrag-multi-service, query-rewriting-rag, tool-design-for-agents, agent-harness-design]
---

# Agentic RAG

> One-shot retrieval is fixed; you get K chunks, the model answers. An agent retrieves until it has the answer — fewer wrong tool calls than you'd think, and far better recall on hard questions.

## When to Use This Skill

- One-shot RAG keeps missing on multi-hop or exploratory questions
- The corpus is code/docs and the model would benefit from `grep` and file reads
- Answers depend on following references (callers, schemas, ADRs cited from docs)
- You're willing to trade latency for recall on hard queries
- Building a "talk to your codebase" agent rather than a Q&A bot

For one-shot retrieval, see [`rag-deep-dive`](../rag-deep-dive/SKILL.md). For the structural-relationship side, [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md). For code-specific concerns, [`rag-for-code`](../rag-for-code/SKILL.md).

---

## One-Shot RAG vs Agentic RAG

| | One-shot RAG | Agentic RAG |
|---|---|---|
| Retrieval | One vector search | Tool calls in a loop |
| Latency | ~1–3s | 5–30s |
| Cost per query | Low | 3–10× higher |
| Recall on hard queries | Plateaus | Higher |
| Failure mode | "I don't know" | Wandering / over-retrieval |
| Best for | FAQ, definition, single-fact lookup | Multi-hop, exploratory, code archaeology |

1. **Don't replace one-shot with agentic everywhere.** Most queries need one-shot; some need agentic. Route at the top of the pipeline (see [`query-rewriting-rag`](../query-rewriting-rag/SKILL.md)).

2. **Agentic RAG is a specialisation of agent design**, not a different paradigm. Everything in [`agent-harness-design`](../agent-harness-design/SKILL.md) and [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) applies.

---

## A Minimal Tool Set for Code Agentic RAG

```
search_semantic(query, top_k=10, filters={}) → chunks
search_lexical(pattern, glob='**/*', context_lines=3) → matches    # ripgrep
read_file(path, start_line=1, end_line=200) → text
list_directory(path) → entries
find_symbol(name, kind='method'|'class') → matches                  # ctags / LSP
find_callers(symbol) → caller list                                  # LSP / static
find_callees(symbol) → callee list
get_endpoint(service, operationId) → openapi excerpt
graph_query(cypher_or_dsl) → result                                 # if you have a graph
```

3. **Start with three tools**: `search_semantic`, `search_lexical`, `read_file`. Most code questions don't need more. Add structural tools (callers, graph) when measurement shows they help.

4. **Tools must be cheap.** `search_lexical` over a 5M-LOC monorepo cannot take 30 seconds. Pre-build ripgrep / ctags / LSP indices.

5. **Bound output size aggressively.** A `grep` matching 5000 lines is useless to the agent. Default to top 30 results, paginate if asked.

6. **Each tool returns text the agent can quote.** Return chunk content with `path:line` headers, not opaque IDs.

---

## Agent Loop

```
system: You are a senior engineer. Use the tools to find evidence in the
        codebase before answering. Cite `path:line` for every claim.

user: Why does the orders service throw OptimisticLockingFailureException
      under load?

agent: <thinks>
       I should look for OptimisticLockingFailureException usage and
       @Version-annotated entities in the orders service.
       </thinks>
       Tool: search_lexical(pattern="OptimisticLockingFailureException", glob="orders/**")
       → 4 matches; the relevant one is OrderEntity with @Version

       Tool: read_file(path="orders/.../OrderEntity.java", start_line=1, end_line=80)
       → @Version private long version; ...

       Tool: search_lexical(pattern="@Retryable|RetryTemplate", glob="orders/**")
       → no matches in service code

answer: Under concurrent updates, JPA's @Version optimistic lock at
        OrderEntity.java:32 throws when versions diverge. The orders
        service has no retry logic around OrderService.cancel
        (OrderService.java:48), so the exception bubbles up as a 500.
        ...
```

7. **Keep the loop simple — single agent, ReAct-style.** Multi-agent retrieval rarely justifies the complexity for RAG. See [`multi-agent-orchestration`](../multi-agent-orchestration/SKILL.md) for when it does.

8. **Cap iterations.** 8–12 tool calls is plenty; beyond that the agent is wandering. Hard-stop and synthesise from what's been gathered.

9. **System prompt enforces evidence.** "Don't answer without quoting at least one snippet" prevents the agent from short-circuiting to memorised guesses.

10. **Constrain tool order softly**, not hardly. "Prefer semantic search before lexical" is a guideline; let the agent override when the question is identifier-style.

---

## When the Agent Should Stop

11. **Stopping conditions, in order**:
    - Found enough evidence to answer with citations
    - Hit iteration cap
    - Two consecutive tool calls returned nothing new
    - Total token budget exhausted

12. **The agent decides "enough evidence" via the prompt**. Phrasing like "stop when you can cite at least 3 files supporting your answer or have run 8 tool calls" works in practice.

13. **Surface stop reason in the response.** Telemetry needs to distinguish "found answer in 3 calls" from "ran out of budget at call 12".

---

## Self-Correction

14. **If the agent's first answer cites paths that don't exist** (hallucinated), force a re-verify step. A small post-validator that runs `read_file` on each cited path and rejects unverified citations is cheap and effective.

15. **For numeric / structural claims** ("12 services consume this topic"), the agent should call a tool to count, not eyeball.

16. **Don't ask the agent to score its own answer.** Self-evaluation is unreliable. Use a separate eval pass with a different prompt or model.

---

## Hybrid: One-Shot Then Agentic

The pragmatic middle:

```
1. one_shot_retrieval(question)   → top 8 chunks
2. attempt_answer(chunks)         → if confident, return
3. else: agentic_loop(question, chunks_as_starting_context)
```

17. **Use one-shot retrieval as the first leg of the agentic loop.** The agent inherits the chunks; it only takes more turns when needed.

18. **Confidence routing**: if the model's answer cites all retrieved chunks and refuses no parts, ship; if it says "I'm not sure" or cites only one of eight chunks, escalate to the agent loop.

19. **Most production traffic stays one-shot.** Only ~10–20% needs the agentic path; that's where it pays for itself.

---

## Cost & Latency Control

20. **Stream the agent's tool-call deltas to the client** so the UX shows progress. A 15-second blank wait feels broken.

21. **Use a smaller model for tool selection**, larger for synthesis. Haiku/Flash for "decide the next tool call"; Sonnet/Pro for "write the final answer". Mixed model routing is supported by Spring AI and most agent frameworks.

22. **Cache tool results by argument hash** within a single conversation. The agent re-asking the same `read_file(path, lines)` is common and free to dedup.

23. **Hard cap on token spend per conversation.** Without it, a question that loops costs 50× a normal one. Reject calls when the cap trips; report a structured error.

---

## Observability

24. **Log every tool call**: `name`, `args`, `result_summary` (counts, top-K paths), latency, tokens. The trace tells you where time and money go.

25. **Per-conversation rollups**: tool calls / tokens / cost / final answer length / refused?. Dashboards over weeks reveal which tools earn their keep.

26. **Sample full transcripts.** Routing logs aggregate; full transcripts of a random 1% of conversations let humans review reasoning quality.

---

## Evaluation

27. **Eval is harder than one-shot RAG.** Final answer quality is necessary but not sufficient — you also want low tool-call count and no hallucinated citations.

28. **Composite metrics**:
    - Answer correctness (graded; expert review or LLM-as-judge with a held-out reference)
    - Citation validity (cited paths exist; cited content matches)
    - Efficiency (tool calls per question; tokens per answer)
    - Refusal correctness (says "I don't know" when answer isn't in corpus)

29. **Track regression across iterations.** A tool API change can drop tool-call success without changing accuracy until later. Pre-merge eval gate is worth the build time.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Agent loops on the same tool call | Track recent calls in the loop; refuse exact duplicates |
| Wanders through the repo for 30 turns | Iteration cap; force-synthesise on cap hit |
| Hallucinated citations to non-existent files | Post-validate citations; reject answer with invalid ones |
| `grep` returns 5000 lines; agent overwhelmed | Result cap; "use a more specific pattern" hint |
| Cost surprise from one user's exploratory session | Per-user / per-conversation token budget |
| Tool descriptions misleading; wrong tool always picked | Audit and rewrite tool descriptions; see `tool-design-for-agents` |
| Model "thinks" for paragraphs before each tool call | Trim system prompt; use `tool_choice=auto` not "force reasoning" |

---

## Pre-Production Checklist

- [ ] Three core tools at minimum: semantic search, lexical search, read_file
- [ ] Structural tools (callers/callees, graph) added based on measured benefit
- [ ] Tools return `path:line`-headed snippets, capped result size
- [ ] Iteration cap; per-conversation token budget; tool-call dedup
- [ ] System prompt enforces evidence-based answering and citation
- [ ] Citation post-validator rejects hallucinated paths
- [ ] Streaming UX shows tool-call progress
- [ ] Smaller model for tool selection, larger for synthesis
- [ ] Telemetry: per-tool latency, calls per question, cost
- [ ] Eval set scores correctness, citation validity, efficiency, refusal

---

## Related Skills

- [`rag-for-code`](../rag-for-code/SKILL.md) — what's being retrieved
- [`graphrag-multi-service`](../graphrag-multi-service/SKILL.md) — when graph tools join the toolset
- [`query-rewriting-rag`](../query-rewriting-rag/SKILL.md) — alternative to agentic for many query types
- [`agent-harness-design`](../agent-harness-design/SKILL.md) — loop design, sub-agents
- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — tool naming, schema, descriptions
- [`agent-observability`](../agent-observability/SKILL.md) — telemetry patterns
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — eval framework
- [`llm-cost-optimization`](../llm-cost-optimization/SKILL.md) — model routing, caps
