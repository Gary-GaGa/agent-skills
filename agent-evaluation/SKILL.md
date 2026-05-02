---
name: agent-evaluation
description: >
  Building eval harnesses for LLM agents — golden tests, behavioral assertions,
  regression detection, and metric selection. Use this skill when you want to
  measure whether a prompt, tool, or harness change is actually an improvement,
  or to catch regressions before users do.
category: ai-engineering
tags: [eval, evaluation, testing, agent, llm, regression]
related: [agent-harness-design, prompt-engineering, agent-observability]
---

# Agent Evaluation

> "It seemed better in my one test" is the most common reason agents regress in production. Evals turn anecdotes into measurements.

## When to Use This Skill

- Before changing a prompt, tool, or harness — to set a baseline
- After a change — to verify improvement and catch regressions
- Comparing models (Claude vs GPT, Sonnet vs Haiku, old vs new)
- Building confidence to ship an agent to more users
- Investigating "this agent was working last week" reports

---

## Why Agent Evals Are Different

Unit tests assume deterministic outputs. Agents are:

- **Non-deterministic** (sampling, temperature)
- **Multi-step** (a single "task" is many tool calls)
- **Subjective** (correct ≠ unique answer)
- **Expensive** (tokens, latency)
- **Slow-feedback** (regressions visible only over many runs)

So eval harnesses look different from typical test suites.

---

## Eval Types

| Type | What it measures | When to use |
|------|------------------|-------------|
| **Golden test** | Output matches a known-good answer (exact / semantic) | Stable tasks, regression detection |
| **Rubric / LLM-as-judge** | Another LLM scores the output on criteria | Subjective tasks (quality of explanation) |
| **Behavioral assertion** | Specific properties hold (e.g. "called tool X", "didn't access file Y") | Tool selection, safety, format |
| **Trajectory test** | The full sequence of actions matches expected pattern | Multi-step task verification |
| **A/B comparison** | Two versions run on same input; humans rank | Subjective improvements |
| **Live evaluation** | Real users + feedback signal | Production monitoring |

You usually need a mix.

---

## Building a Golden Set

Start with 10-30 representative tasks. More is better but start small.

### Selection rules

1. **Cover the variety, not just the happy path.** Include edge cases, ambiguous inputs, "don't know" cases.
2. **Sample from real usage if possible.** Sanitized real queries beat synthetic ones.
3. **Each task has an expected behavior, not just an output.** "Should refuse" is a valid expectation. "Should ask clarifying question" too.
4. **Tag tasks by category.** Aggregate metrics per category surface specific weaknesses.
5. **Don't include the test set in training data.** If you fine-tune later, withhold these.

### Task structure

```yaml
- id: T-007
  category: file-search
  input: "Find any usage of the deprecated `legacyAuth` function"
  expected:
    - tool_called: search_code
    - tool_args.contains: "legacyAuth"
    - response.mentions: ["src/auth/legacy.ts:42", "src/middleware/old.ts:18"]
    - response.suggests: "deprecation warning OR migration"
```

Each task can have:
- **Hard assertions** (must hold; failure = test fails)
- **Soft assertions** (should hold; failure = score reduction)
- **Forbidden behaviors** (must not hold; e.g. "didn't read /etc/passwd")

---

## Metrics

Pick a small set of metrics aligned with what you care about. Don't drown in dashboards.

### Quality metrics

| Metric | What it measures |
|--------|------------------|
| **Task success rate** | % of tasks where all hard assertions pass |
| **Score (rubric)** | Average score from LLM-judge or human rater |
| **Trajectory match** | % of tasks following expected tool sequence |
| **Refusal correctness** | When agent should refuse, does it? When it shouldn't, doesn't it? |

### Operational metrics

| Metric | What it measures |
|--------|------------------|
| **Latency** | P50, P95, P99 wall-clock per task |
| **Token usage** | Input + output tokens per task |
| **Cost** | $ per task (helpful when comparing models) |
| **Iterations** | Tool calls per task — high = inefficient |
| **Cache hit rate** | If using prompt caching |

### Regression metrics

| Metric | What it measures |
|--------|------------------|
| **Diff vs baseline** | Tasks that flipped pass→fail or fail→pass |
| **Stability** | Variance across multiple runs of the same task (high = brittle) |

---

## LLM-as-Judge

For subjective outputs (explanations, summaries, code reviews), use a separate LLM to grade.

### Pattern

```
For each task:
  Run agent → get output
  Send to judge LLM:
    "Given the input <X>, is this output correct/helpful/concise?
     Score 1-5 with brief reasoning."
  Aggregate scores
```

### Pitfalls

6. **Use a stronger model as the judge** than the one being evaluated. Otherwise the judge is the bottleneck.
7. **Pin the judge.** Same model, same prompt, same temp (0). Otherwise scores drift across runs.
8. **Judges are biased.** They prefer verbose, well-formatted output. Calibrate by spot-checking.
9. **Show the rubric to the judge.** Don't just say "is this good?" — give criteria.
10. **For high-stakes evals, use human review on a sample** (10-20%) to validate the judge.

---

## Trajectory Tests

For multi-step agents, what matters often isn't just the answer, but how it got there.

```yaml
- id: T-014
  trajectory:
    - tool: list_files
    - tool: read_file
      args.path.matches: ".*config.*"
    - tool: edit_file
  forbidden:
    - tool: run_command  # this task shouldn't need shell
  output:
    contains: ["updated", "config"]
```

**Why:** Agents can produce the right answer for the wrong reasons. Trajectory tests catch silent-fragility bugs.

---

## CI Integration

Run evals as part of the dev loop:

| Trigger | What runs |
|---------|-----------|
| Local pre-commit (optional) | A 5-task smoke set, < 30s |
| PR (gated) | Full golden set on changed prompts/tools |
| Nightly | Full set + extended scenarios + multi-model comparison |
| Release | Pre-deploy gate; must beat baseline on success rate |

### Reporting

For each run, output:
- Pass/fail per task
- Aggregate metrics
- Diff vs previous run (which tasks flipped?)
- Token cost delta

A flaky task that flips intermittently is a real signal — investigate it before pinning around it.

---

## Iteration Workflow

```
1. Add a failing real-world task to the golden set
2. Run baseline → confirm it fails
3. Make a change (prompt tweak, new tool, better description)
4. Re-run → does the new task pass?
5. Re-run full set → did anything else break?
6. If anything broke: triage. Fix or accept the trade-off.
7. Commit the change with the eval delta in the commit message
```

**Every prompt/tool change should come with an eval delta.** "Improved Sonnet's selection accuracy from 78% → 85% on the gold set."

---

## Stability & Variance

Agents are non-deterministic. To handle:

11. **Run each task N times** (3-5 typical). Report majority vote or average score.
12. **Flag high-variance tasks.** A task that's 60/40 pass/fail across runs is unreliable. Investigate.
13. **For determinism in CI**, set `temperature=0` if your provider supports it. (Doesn't make outputs identical, but reduces variance.)
14. **Don't chase 100% pass rate** — it usually means you removed the hard tasks. 70-90% on a hard set is healthier than 100% on an easy set.

---

## Sandbox & Side Effects

Agents that run in eval should not:
- Hit production APIs
- Modify real data
- Send messages
- Cost money beyond eval tokens

### Patterns

- **Mock external services** with deterministic test doubles
- **Sandbox the file system** (separate temp dir per run)
- **Stub network calls** with fixtures
- **Use a separate API key** with hard spend limits

---

## Common Mistakes

| Mistake | Why bad | Fix |
|---------|---------|-----|
| 3-task eval set | No statistical signal | At least 20 |
| Only happy-path tasks | Misses real failures | Include edge cases, refusals, ambiguity |
| Single-run results | High variance, false confidence | N runs per task |
| Manual ad-hoc testing only | Doesn't catch regressions | Codify into eval |
| Judge LLM is same model being evaluated | Self-preference bias | Use a stronger judge |
| Eval set drifts to be easy | Tests too quickly become trivial | Periodically add hard cases |
| Pass rate is the only metric | Misses cost/latency regressions | Track operational metrics too |
| Tests rely on real services | Flaky, costly, slow | Sandbox & mock |

---

## Anti-Patterns to Watch For

- **Goodhart's law in action.** "Pass rate is at 95%, ship it." Then realize you've been optimizing for the rubric, not for users.
- **Eval set as wishlist.** "Eventually we want it to handle X" — then leave a permanent fail. Either fix or remove.
- **No baseline tracking.** "I think it's better." Show the numbers.

---

## Checklist for a Healthy Eval Setup

- [ ] At least 20 tasks covering varied scenarios (happy, edge, refusal, ambiguity)
- [ ] Each task has clear expected behaviors, not just a single output
- [ ] Tasks are versioned alongside the agent code
- [ ] Run multiple times per task (3+); high-variance tasks flagged
- [ ] Operational metrics tracked (latency, tokens, cost)
- [ ] Trajectory tests for multi-step tasks
- [ ] Sandbox for any external side effects
- [ ] Eval delta is part of every prompt/tool/harness change PR
- [ ] CI runs evals on PRs touching the agent
- [ ] Periodic human spot-check (especially for LLM-judged subjective tasks)

---

## Related Skills

- [`agent-harness-design`](../agent-harness-design/SKILL.md) — what you're evaluating
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — most prompt changes need eval verification
- [`agent-observability`](../agent-observability/SKILL.md) — production telemetry feeds back into eval sets
- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — tool changes need trajectory tests
