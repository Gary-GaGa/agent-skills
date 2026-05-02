---
name: multi-agent-orchestration
description: >
  Patterns for coordinating multiple LLM agents — supervisor/worker, planner/
  executor, parallel sub-agents, handoff design, and shared state management.
  Use this skill when a single agent isn't enough and you need to compose
  agents to handle complex workflows. Strongly recommended to start single-agent
  before reaching for this.
category: ai-engineering
tags: [multi-agent, orchestration, supervisor, planner, agent]
related: [agent-harness-design, prompt-engineering, context-engineering]
---

# Multi-Agent Orchestration

> Multi-agent systems multiply tokens, complexity, and failure modes. Use them when single-agent demonstrably fails — not because the architecture sounds sophisticated.

## When to Use This Skill

- A single agent's prompt / tool surface is becoming bloated trying to handle disjoint tasks
- Sub-tasks are clearly independent and can run in parallel
- Different parts of a task need very different expertise (and very different prompts)
- A workflow has a planning phase distinct from an execution phase
- Reviewing an existing multi-agent system that feels over-engineered

---

## Default Position: Don't

Single agents with good prompts and tools handle far more than people assume. Before going multi-agent, exhaust:

- Better tool descriptions
- Sharper system prompt
- More few-shot examples
- Sub-skill loading on demand
- Explicit step-by-step instructions

A 2024 trend was "more agents = better"; production data shows the opposite. The best agentic systems often have one main agent with selective sub-agent dispatch for narrow tasks.

**See [`agent-harness-design`](../agent-harness-design/SKILL.md) for the single vs multi decision.**

---

## When Multi-Agent Genuinely Helps

| Signal | Why multi-agent fits |
|--------|----------------------|
| **Independent parallel work** | True throughput gain (e.g. researching 5 candidates concurrently) |
| **Strong context isolation need** | Sub-task should NOT clutter main context (e.g. exploratory file search) |
| **Distinct expertise** | Specialized prompts + tool sets for sub-domains |
| **Bounded sub-task contracts** | Clear input/output shape; sub-agent failures don't cascade |
| **Volume + cost tolerance** | Tokens are cheap relative to the value |

If 3+ apply, multi-agent is reasonable. If only 1, prefer single agent.

---

## Common Patterns

### Pattern 1: Supervisor + Workers

```
   ┌──────────────┐
   │  Supervisor  │   ← decides what to delegate
   └──────┬───────┘
          │ dispatch
   ┌──────┴────────┐
   ▼      ▼        ▼
[Worker A] [Worker B] [Worker C]   ← specialized; parallel
```

- **Supervisor** decomposes the task, dispatches, synthesizes results.
- **Workers** are narrow specialists (research, code-search, lint, etc.).
- Workers don't talk to each other; supervisor mediates.

**Use for:** parallelizable subtasks, specialized expertise.

### Pattern 2: Planner → Executor

```
[Planner] ──produces plan──► [Executor] ──acts──► [Done]
                                  │
                                  └──can replan if blocked──► [Planner]
```

- **Planner** thinks slowly (often a stronger model), produces an explicit plan.
- **Executor** thinks fast (often a faster model), executes mechanically.
- Replanning is rare; most plans should execute end-to-end.

**Use for:** complex multi-step tasks where the plan is the hard part.

### Pattern 3: Parallel Researchers + Synthesizer

```
        ┌──────────┐
        │  User Q  │
        └────┬─────┘
             │
   ┌─────────┼──────────┐
   ▼         ▼          ▼
[Agent 1] [Agent 2] [Agent 3]   ← each researches an angle
   │         │          │
   └─────────┼──────────┘
             ▼
      [Synthesizer]   ← combines findings
             │
             ▼
         [Answer]
```

**Use for:** exploration tasks, independent research angles.

### Pattern 4: Pipeline (deterministic chain)

```
[Stage 1: extract] → [Stage 2: classify] → [Stage 3: format]
```

**Not really multi-agent** — it's a code-orchestrated pipeline. Use this if stages are well-known and order is fixed; let your harness/code drive, not an LLM.

### Pattern 5: Debate / Critic

```
[Solver] ──proposes──► [Critic] ──critiques──► [Solver]
                                 (iterate 2-3 times)
```

- Solver proposes, critic reviews, solver revises.
- Often 1-2 rounds is enough; more = diminishing returns.

**Use for:** quality-sensitive output (writing, code review, plans).

---

## Handoff Design: The Critical Interface

A handoff between agents loses information. Design the contract carefully.

### Rules

1. **Output schema is part of the agent's interface.** Worker agents must return structured results with known fields.
2. **Include provenance.** Where did this fact come from? Which tool calls? Lets the next agent verify.
3. **Don't dump raw conversation.** Summarize before handing off; otherwise context bloats.
4. **State preconditions and postconditions.** "Worker promises to return ≥ 1 candidate with score ≥ 0.7."
5. **Errors are first-class returns.** Workers return `{result: ..., error: ...}`, not raise unhandled exceptions.

### Handoff payload structure

```yaml
handoff:
  from: supervisor
  to: code_searcher
  task: "Find usages of legacyAuth() across the repo"
  context:
    repo_path: /path/to/repo
    excluded_dirs: [node_modules, .git]
  expected_output:
    schema:
      - file: string
      - line: integer
      - snippet: string
  budget:
    max_iterations: 5
    max_tokens: 10000
    timeout_s: 30
```

The receiver knows exactly what's expected; the sender knows what to budget for.

---

## Shared State

Multi-agent systems need to coordinate without cluttering each agent's context.

### Patterns

| Where | Use for |
|-------|---------|
| **Supervisor's context** | Plan, summary, final synthesis — the supervisor sees everything |
| **External store (DB, file)** | Long-running state, cross-session memory, audit trail |
| **Inter-agent messages** | Explicit handoffs; structured payloads |
| **Worker scratchpad (per-agent context)** | Worker-internal reasoning; discarded after handoff |

**Don't** make every agent see every other agent's full context. That's how you get exponential cost and lost-in-the-middle blunders.

---

## Cost & Latency

Multi-agent multiplies both:

- **Cost ≈ sum(tokens per agent)** — a 3-worker system can be 3-5× single-agent cost.
- **Latency ≈ critical path of the slowest sub-agent** when parallel; sum when sequential.

### Mitigations

- Use cheaper models for narrow worker tasks (Haiku for searching; Sonnet for synthesis).
- Cache shared system prompts (supervisor's prompt is identical across runs).
- Bound iterations per worker explicitly.
- Skip workers whose output is unneeded (early exit / conditional dispatch).

---

## Failure Modes (and How to Catch Them)

| Failure mode | Symptom | Detection / Mitigation |
|--------------|---------|------------------------|
| **Worker confabulation** | Worker returns plausible-but-wrong | Verify with second source; trajectory test |
| **Supervisor over-delegates** | Spawns workers for trivial things | Cost monitoring + supervisor system prompt tuning |
| **Handoff drift** | Each handoff loses fidelity | Structured payloads, not natural-language relays |
| **Loop / no convergence** | Critic and solver fight forever | Max round cap; force ship after N rounds |
| **Worker calls supervisor's tools** | Supervisor's tools leak into worker context | Strict tool scoping per agent |
| **Cascading hallucination** | Worker A's wrong answer feeds worker B | Source-of-truth tools that ground each agent |
| **Token explosion** | Cost spikes unexpectedly | Per-agent token budgets + alerts |

---

## Comparison: When Single vs Multi vs Pipeline

| Workflow | Best fit |
|----------|----------|
| Bounded task, one expert is enough | **Single agent** |
| Task with disjoint sub-tasks, ordered | **Pipeline (code-driven)** |
| Task with disjoint sub-tasks, dynamic | **Supervisor + workers** |
| Task with hard planning + simple execution | **Planner + executor** |
| High-quality output needed | **Solver + critic** |
| Exploratory research | **Parallel researchers + synthesizer** |

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| 5+ agents for a task that worked single-agent | Multiplies cost without benefit | Start single, add agents only when measurably needed |
| Workers calling each other directly | No structured contract; chaos | Mediate through supervisor |
| Same model + same system prompt across all agents | They're the same agent — no specialization | Differentiate prompts/tools meaningfully |
| Handoff via "natural language description" | Information loss across handoffs | Structured payloads |
| No iteration cap on debate / critic | Infinite loops | Hard cap + forced exit |
| All workers see full conversation history | Context cost explodes | Workers see only their task + needed context |
| No per-agent observability | Can't debug which agent failed | Trace each agent separately |

---

## Designing a Multi-Agent System

```
1. Confirm single-agent doesn't work. (If it does, stop here.)
2. Identify the natural decomposition: parallel? sequential? specialist roles?
3. Pick a pattern (supervisor / planner-executor / debate / pipeline).
4. Define each agent's contract: inputs, outputs, tools, budget.
5. Design the handoff payloads.
6. Decide where shared state lives.
7. Set per-agent and total budgets (tokens, iterations, time).
8. Build with full per-agent tracing.
9. Eval against single-agent baseline. Multi-agent must beat it on quality, accept cost.
10. Monitor production for failure modes specific to multi-agent.
```

---

## Checklist

Before shipping multi-agent:

- [ ] Documented why single-agent isn't sufficient (with eval data)
- [ ] Each agent has a clear contract (inputs, outputs, scope)
- [ ] Handoff payloads are structured, not free-text
- [ ] Each agent has its own budget (tokens, iterations, time)
- [ ] Per-agent traces in observability
- [ ] Failure modes (cascading hallucination, loops) are tested
- [ ] Cost is measured and within acceptable bounds
- [ ] Eval beats the single-agent baseline on quality

---

## Related Skills

- [`agent-harness-design`](../agent-harness-design/SKILL.md) — the single vs multi decision lives here
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — each sub-agent needs its own well-designed prompt
- [`context-engineering`](../context-engineering/SKILL.md) — handoffs are a context-engineering problem
- [`agent-observability`](../agent-observability/SKILL.md) — per-agent tracing is essential
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — multi-agent must beat single-agent baseline
