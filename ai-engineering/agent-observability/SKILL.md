---
name: agent-observability
description: >
  Tracing, logging, and monitoring LLM agents in development and production —
  what to log per turn, span design, token cost tracking, multi-turn debugging,
  and failure mode classification. Use this skill when an agent misbehaves in
  ways you can't reproduce, or when setting up production telemetry.
category: ai-engineering
tags: [observability, tracing, logging, agent, debugging, monitoring]
related: [agent-harness-design, agent-evaluation, debugging-methodology, observability-go]
---

# Agent Observability

> Without observability, you're debugging by re-running. With it, you have one trace and the answer is in there. Build the telemetry before the agent ships, not after the first incident.

## When to Use This Skill

- A user reports an agent failure you can't reproduce locally
- Setting up production telemetry for an agent
- Investigating cost spikes or latency regressions
- Designing the trace/log schema for a new harness
- Building a feedback loop from production into the eval set

---

## What "An Agent Run" Actually Is

A single user turn typically expands to many lower-level events:

```
User turn
  └─ Session
       └─ Iteration 1
            ├─ Model call (input → output)
            ├─ Tool selection
            └─ Tool call (args → result)
       └─ Iteration 2
            ├─ Model call
            ├─ Tool call → ERROR
            └─ Retry
       └─ Iteration 3
            └─ Final response
```

**Each level is a span you'll want to query later.** Design the trace structure to mirror this hierarchy.

---

## Log Per Turn: The Minimum Viable Schema

For each agent turn, capture:

| Field | Why |
|-------|-----|
| `session_id` | Tie multiple turns into a conversation |
| `turn_id` | Order within session |
| `user_input` (truncated) | What kicked it off — sanitize PII |
| `model` | Which model + version |
| `system_prompt_hash` | Detect when prompt changes affect behavior |
| `iteration_count` | How many times the loop ran |
| `tool_calls` | List of `(tool_name, args, result_summary, duration, error?)` |
| `final_response` (truncated) | What the user saw |
| `tokens_input` / `tokens_output` | Cost tracking |
| `cache_hits` / `cache_misses` | If using prompt caching |
| `wall_time_ms` | End-to-end latency |
| `error?` | Top-level failure if any |

**Keep raw turns for the recent window** (last N days) and aggregate for older.

---

## Span Design (Distributed Tracing)

If you're using OpenTelemetry or similar:

```
agent.session  (root)
  └─ agent.turn
       ├─ agent.iteration
       │    ├─ llm.call           (attrs: model, input_tokens, output_tokens)
       │    └─ tool.call          (attrs: tool, args, result_size, error)
       ├─ agent.iteration
       │    └─ ...
       └─ agent.compaction       (when context compaction triggers)
```

### Span attributes

For `llm.call`:
- `llm.model`, `llm.temperature`, `llm.max_tokens`
- `llm.input_tokens`, `llm.output_tokens`, `llm.cached_tokens`
- `llm.finish_reason`

For `tool.call`:
- `tool.name`, `tool.args` (truncated), `tool.result_size`
- `tool.error_type` (none / expected / unexpected)
- `tool.duration_ms`

**Trace IDs propagate to downstream services** — link your agent traces with API/DB traces from the tools.

---

## What NOT to Log

| Never log | Why |
|-----------|-----|
| Full system prompts (every turn) | Repetitive; log a hash + version instead |
| Raw API keys / secrets in tool args | Obvious. Sanitize at the ingest boundary |
| Full file contents from `read_file` | Volume; log size + hash |
| User PII unless necessary and policy-allowed | Privacy; redact or hash |
| Vector embeddings | Volume; log retrieval *choice*, not the math |

### Truncation patterns

- Inputs > 1KB: log first 200 chars + total size
- Tool results > 1KB: log size + first 200 chars
- Long conversations: log the last 5 turns verbatim, summary for older

---

## Cost Telemetry

Tokens become real money fast. Log:

- Tokens per turn (input vs output)
- Cumulative tokens per session
- Cost per session (compute from token + model rates)
- Cache effectiveness (hit rate, savings)

### Budget alerts

Set thresholds:

- "Session > $1" → warn, log full trace
- "Session > $5" → halt, require manual review
- "User > $X / day" → rate-limit

Don't discover six-figure bills in the monthly report.

---

## Multi-Turn Debugging

When an agent fails on turn 8 of a long session, you need:

1. **Full conversation reconstruction.** What was in context at turn 8?
2. **Decision rationale.** Why did the agent choose tool X?
3. **State diffs.** What changed between turn 7 and 8?

### Reconstruction tools

- A "replay this session" feature — given session_id, reconstruct exactly what the model saw
- Prompt diffing — compare the actual prompt across turns / sessions
- Tool call graph viewer — visualize which tools fired in what order

### Useful queries

- "Sessions where iteration_count > 10" → likely loops
- "Sessions where tool X errored 3+ times" → tool quality issue
- "Sessions where response contained 'I don't know'" → capability gap
- "Sessions with cache_hit_rate < 30%" → caching strategy issue

---

## Failure Mode Classification

When something goes wrong, what kind of wrong?

| Class | Symptom | Investigation |
|-------|---------|---------------|
| **Tool failure** | Tool returned error | Tool implementation, network, auth |
| **Selection failure** | Wrong tool picked | Tool description / overlap |
| **Argument failure** | Right tool, bad args | Schema, prompt clarity |
| **Loop / stagnation** | Many iterations, no progress | Stop condition, repeated calls |
| **Hallucination** | Confident wrong output | Tool grounding, model choice |
| **Refusal failure** | Refused valid request | System prompt over-cautious |
| **Format failure** | Output doesn't match spec | Format examples, structured output |
| **Cost / latency** | Too slow / expensive | Context size, model choice |

**Tag each failure with a class.** Aggregating reveals patterns: "30% of failures last week were selection failures" → focus on tool descriptions.

---

## Production → Eval Feedback Loop

Production failures should become eval test cases:

```
1. User reports / monitor catches a failure
2. Pull the full trace
3. Sanitize (remove PII)
4. Add as a task to the eval set with expected behavior
5. Run eval to confirm regression
6. Fix
7. Eval re-run confirms fix without regressing siblings
```

**This is the highest-ROI use of observability.** Each incident enriches your future detection.

---

## Privacy & Compliance

Agent traces are sensitive — they contain user inputs, file contents, business data.

### Rules

1. **Identify what's PII.** Per your data classification.
2. **Redact at ingest, not at query time.** Once raw data is in the log store, it's hard to remove.
3. **Set retention policies.** Raw traces 7-30 days; aggregates longer.
4. **Encrypt at rest.** Traces are an attractive target.
5. **Access controls.** Not every developer needs raw user inputs.
6. **Comply with deletion requests.** If a user requests deletion, traces must be purged.

---

## Sampling

For high-volume agents, full tracing is expensive. Sample:

| Strategy | When |
|----------|------|
| **100% sampling** | Dev/staging, low-volume production |
| **Fixed % (e.g. 10%)** | High-volume baseline |
| **Sample by error** | Always log on failure; sample successes |
| **Tail-based** | Decide after the trace completes — log slow / expensive / errored 100% |

**Always log on error.** Cost a few KB; gain debuggability.

---

## Tools & Stacks

Common stacks:

| Layer | Options |
|-------|---------|
| Trace SDK | OpenTelemetry, vendor-specific (Honeycomb, Datadog) |
| Storage | Honeycomb, Datadog APM, Grafana Tempo, Jaeger |
| Logs | Datadog Logs, Splunk, Loki, Elasticsearch |
| Agent-specific | LangSmith, LangFuse, Weights & Biases Traces, Arize Phoenix |
| Cost / token tracking | Helicone, OpenLLMetry, custom |

**Specialized agent observability tools** (LangSmith, LangFuse, Phoenix) understand prompt/response/tool semantics natively. Worth the lock-in if you're heavy on agent eng.

---

## Common Mistakes

| Mistake | Why bad | Fix |
|---------|---------|-----|
| Logging only the final response | Can't debug intermediate failures | Log every iteration |
| Logging raw prompts every turn | Volume + repetition | Hash + version |
| No trace IDs across services | Can't follow into tool calls | Propagate IDs |
| Logging everything at INFO | Drowns in noise | Use levels; sample appropriately |
| Storing raw embeddings | Volume, no analytical value | Log retrieval choices |
| No cost tracking until the bill | Surprise spend | Per-session cost in real-time |
| Privacy as an afterthought | Compliance risk | Redact at ingest |
| Logs but no dashboards | Can't see patterns | At minimum: success rate, p95 latency, $/session |

---

## Minimum Viable Observability Setup

For a small / new agent, ship at least:

- [ ] Per-turn structured log (session, model, tools, tokens, latency, errors)
- [ ] Distributed traces with `agent.session` → `agent.turn` → `llm.call` / `tool.call` spans
- [ ] PII redaction at ingest
- [ ] A "replay this session" capability
- [ ] Dashboards: success rate, p95 latency, $/session, error rate
- [ ] Always log on error
- [ ] Failure classification on errors (manual or auto)
- [ ] Process: production failures → eval set additions

---

## Related Skills

- [`agent-harness-design`](../agent-harness-design/SKILL.md) — design the harness with hooks for observability
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — eval set is fed by production failures
- [`debugging-methodology`](../../engineering/debugging-methodology/SKILL.md) — same principles, agent-specific application
- [`context-engineering`](../context-engineering/SKILL.md) — observability tells you what's in context
