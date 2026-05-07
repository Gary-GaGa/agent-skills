---
name: agent-harness-design
description: >
  Conceptual guide to designing the harness around an LLM — the agent loop,
  single vs multi-agent decisions, when to use sub-agents, context management
  strategy, and tool selection patterns. Language- and provider-agnostic.
  Use this skill when designing a new agent system or auditing an existing one.
category: ai-engineering
tags: [agent, harness, llm, architecture, design]
related: [prompt-engineering, context-engineering, tool-design-for-agents, agent-evaluation, agent-observability, multi-agent-orchestration, agent-safety-guardrails, mcp-server-design, skill-authoring, claude-code-customization, prompt-caching, llm-cost-optimization, copilot-sdk, agentic-rag]
---

# Agent Harness Design

> The model is one component. The harness — loop, context, tools, memory, evaluation — is most of the engineering. Get the harness right, and a smaller model often beats a larger one with a worse harness.

## When to Use This Skill

- Designing a new LLM-powered agent from scratch
- Auditing an existing agent that's behaving poorly
- Deciding whether to use a single agent, sub-agents, or pipelines
- Choosing how much autonomy to give the agent
- Debugging "the model is dumb" complaints (usually it's the harness)

---

## The Agent Loop

The simplest viable agent loop:

```
┌──────────────────────────────────────────────────┐
│  1. Observe    →   gather inputs / tool results  │
│  2. Think      →   LLM produces next action      │
│  3. Act        →   execute the chosen tool       │
│  4. Loop       →   feed result back to step 1    │
│       │                                          │
│       └─ exit when:                              │
│            - LLM emits a "done" signal           │
│            - max iterations reached              │
│            - error / safety violation            │
└──────────────────────────────────────────────────┘
```

Every harness — Claude Code, ReAct, AutoGPT, OpenAI Assistants — is a variation on this.

### Key design choices in the loop

1. **Stop condition.** When does the loop end? Explicit "done" tool? No more tool calls? Iteration limit? Pick clearly and document.
2. **Iteration budget.** Cap turns (e.g. 25). Without a cap, agents can spin forever on hard problems.
3. **State passed forward.** Full conversation? Compacted summary? Selective tool results? This is the single biggest lever for quality and cost.
4. **Error recovery.** Tool errors — retry once, surface to model, or abort?

---

## Single Agent vs Multi-Agent vs Pipeline

| Pattern | When to use | Cost | Complexity |
|---------|-------------|------|------------|
| **Single agent** | Default. Bounded task, one expert is enough. | Low | Low |
| **Sub-agents** | Sub-task is independent and parallelizable; OR has very different context needs (specialist) | Higher | Medium |
| **Pipeline (deterministic)** | Steps are well-known and ordered — let code orchestrate, not the LLM | Lowest | Lowest |
| **Multi-agent (orchestrator + workers)** | Workflow is dynamic, needs delegation and synthesis | Highest | Highest |

**Default rule:** Start single-agent. Add sub-agents only when you've measured a specific failure mode they fix.

### Anti-pattern: multi-agent for the sake of it

Don't reach for multi-agent because it sounds sophisticated. Multi-agent systems:
- Multiply token cost
- Multiply failure modes (handoff bugs, context loss between agents)
- Are harder to debug
- Often perform *worse* than a single well-prompted agent

See [`multi-agent-orchestration`](../multi-agent-orchestration/SKILL.md) for when it actually helps.

---

## When to Use a Sub-Agent

Spawn a sub-agent when **at least one** of these is true:

| Signal | Why a sub-agent helps |
|--------|----------------------|
| **Independent work** | The sub-task has no information dependency on parallel work — perfect for parallelism |
| **Context isolation** | The main agent doesn't need the sub-task's intermediate steps, only the final answer (saves context) |
| **Different expertise** | The sub-task needs a specialized system prompt or tool set |
| **Bounded scope** | Sub-task has a clear input → output contract |

Don't use sub-agents when:
- The task is sequential and information-dependent
- You just want "two opinions" — that's prompt engineering, not architecture
- The sub-task is small enough that the orchestration overhead exceeds the benefit

---

## Context Management Strategy

The model only sees what's in its context window. Three core strategies:

### 1. Full history (default)

Pass the complete conversation each turn. Simple, predictable, expensive at scale.

**Use when:** Short conversations, small token budgets, debugging.

### 2. Compaction

Periodically summarize earlier turns into a compact note, freeing context.

**Use when:** Long-running agents (Claude Code style), conversations exceeding ~50% of context window.

**Risk:** Important details lost in summary. Pin critical facts (file paths, IDs) outside the summary.

### 3. Retrieval (RAG-style)

Store turns in external memory; retrieve only relevant pieces each turn.

**Use when:** Very long-lived agents, knowledge bases, multi-session memory.

**Risk:** Retrieval misses → silent capability loss. Always include some recent history regardless of retrieval.

See [`context-engineering`](../context-engineering/SKILL.md) for details.

---

## Tool Selection: How Many, How Granular?

### The trade-off

- **Few coarse tools** (e.g. `run_command`) — model is flexible but errors are common (escaped strings, wrong syntax).
- **Many fine tools** (e.g. `read_file`, `edit_file`, `list_dir`) — model is constrained, errors fewer, but selection cognitive load grows.

### Heuristics

5. **Aim for 5-15 tools per agent.** Fewer = limited capability; more = poor selection.
6. **Each tool does one thing.** `read_file` good. `read_or_write_file` bad.
7. **Names should match user intent vocabulary.** `search_code` not `grep_invocation`.
8. **Tool descriptions are part of the prompt.** Optimize them with the same care as the system prompt.

See [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md).

---

## Autonomy Spectrum

How much should the agent decide vs ask?

```
Low autonomy ────────────────────────────────────► High autonomy
   Asks user every step    Asks at decision points    Acts freely
```

| Level | Use case | Example |
|-------|----------|---------|
| **Confirm each action** | High-stakes, irreversible operations | Production deployments, sending emails |
| **Confirm milestones** | Multi-step tasks with checkpoints | Code refactor across many files |
| **Free execution + summary** | Bounded, reversible, low-stakes | Code search, file reads, internal queries |

**Match autonomy to blast radius.** A coding agent can freely edit local files; the same agent should ask before pushing to main.

---

## State the Agent Maintains

Beyond the conversation, agents typically have:

| State | Examples | Storage |
|-------|----------|---------|
| **Working memory** | Current task, plan, scratchpad | In context |
| **Tool state** | Open files, DB connections, auth tokens | External (handled by tools) |
| **Long-term memory** | User preferences, past sessions | External DB / file |
| **Iteration metadata** | Turn count, time elapsed, errors so far | Harness, not in context |

Decide for each: who owns it, how is it persisted, when is it shown to the model?

---

## Failure Modes & Mitigations

| Failure mode | Likely cause | Mitigation |
|--------------|--------------|------------|
| Loops forever, repeats same tool call | No progress detection | Add max iteration; detect repeated identical calls |
| Forgets earlier instructions | Context overflow / poor compaction | Pin critical instructions in system prompt; selective context |
| Picks wrong tool | Vague tool description, overlapping tools | Sharpen descriptions, eliminate overlap |
| Hallucinates results | No tool returned facts; model filled in | Encourage "I don't know"; add a "search" tool |
| Gives up too early | No re-try guidance in prompt | Explicit "if X fails, try Y" guidance |
| Asks too many clarifying questions | Prompt over-emphasizes caution | Tune prompt to act when low-stakes |

---

## Iteration & Improvement Loop

Agent quality comes from iteration, not first-shot design:

```
1. Build minimal harness (single agent, full history, 5 tools)
2. Run on a small set of representative tasks
3. Identify the most common failure mode
4. Fix one thing (better tool description, prompt tweak, add/remove a tool)
5. Re-run, measure delta
6. Repeat
```

**Don't redesign the harness on a single anecdote.** Collect 5+ failures of the same mode before changing architecture.

---

## Design Checklist

Before shipping an agent:

- [ ] The agent loop has an explicit stop condition and iteration cap
- [ ] Tool count is 5-15; each tool is sharply described
- [ ] Context strategy is decided (full / compacted / retrieved)
- [ ] Autonomy level matches blast radius of the agent's actions
- [ ] Failure modes are listed and at least the top 3 have mitigations
- [ ] You can answer: "what does the model see on turn N?"
- [ ] You have a small eval set to detect regressions
- [ ] Instrumentation logs every turn (tool, args, result, tokens)

---

## Related Skills

- [`prompt-engineering`](../prompt-engineering/SKILL.md) — the system prompt that drives the loop
- [`context-engineering`](../context-engineering/SKILL.md) — managing what the model sees each turn
- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — designing the tools the model picks from
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — how to measure whether your harness changes are improvements
- [`multi-agent-orchestration`](../multi-agent-orchestration/SKILL.md) — when single-agent isn't enough
