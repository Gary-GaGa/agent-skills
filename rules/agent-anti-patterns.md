# Agent Anti-Patterns

Common mistakes when designing, building, or operating LLM agents. Reference this when reviewing an agent system or debugging behavior. Aligned with skills under the `ai-engineering` category.

---

## Architecture

1. **Multi-agent for the sake of it.** Reaching for sub-agents because the architecture sounds sophisticated.
   - **Symptom:** A 5-agent system that a single well-prompted agent could handle.
   - **Fix:** Start single-agent. Only add sub-agents when you've measured a specific failure they fix.

2. **Premature pipelines.** Coding a 7-stage LLM pipeline when 3 of the stages are deterministic.
   - **Fix:** Code-orchestrate the deterministic stages; use the LLM only for what needs reasoning.

3. **No iteration cap on the agent loop.** Agent spins forever on hard problems.
   - **Fix:** Always bound iterations (e.g. 25). Exit and surface a "didn't converge" error.

4. **Blast radius mismatched with autonomy.** Agent freely deploys to production.
   - **Fix:** Tier actions; require confirmation for irreversible / cross-boundary ops.

---

## Prompts

5. **Vague platitudes ("be helpful and accurate").**
   - **Fix:** Specific behaviors. "List 3-5 issues. Each with file:line and severity."

6. **2,000-word system prompt.** Diluted attention; expensive every call.
   - **Fix:** Refactor. Most prompts should fit in 200-500 words system + 5 examples max.

7. **Critical instruction in the middle of a long prompt.** Lost-in-the-middle effect.
   - **Fix:** Top or bottom (or both).

8. **Treating the prompt as final after first version.** No iteration.
   - **Fix:** Treat prompts as code: version, test, eval each change.

9. **Negative-only instructions ("don't do X").** Models follow positive directives more reliably.
   - **Fix:** Recast as "do Y."

10. **Prompt evolves without an eval set.** Regressions invisible.
    - **Fix:** Build a 20-task golden set; run on every prompt change.

---

## Context

11. **Passing full conversation history every turn forever.** Cost spirals; lost-in-the-middle bites.
    - **Fix:** Compaction with token-count trigger; pin critical facts.

12. **Compacting too aggressively** (every 5 turns).
    - **Fix:** Trigger by tokens (e.g. 60% of window), not turns.

13. **Trusting the summary** alone after compaction. Critical IDs / paths get lost.
    - **Fix:** Pin them outside the summary explicitly.

14. **Putting dynamic state in system prompt** (timestamps, session IDs). Bursts the cache every call.
    - **Fix:** Move to user message; keep system prompt stable.

15. **Tool returns 50K-token blobs.** Eats context budget instantly.
    - **Fix:** Bound at the tool level; return summary or first-N with truncation marker.

---

## Tools

16. **Two tools with overlapping purpose.** Model picks one randomly.
    - **Fix:** Sharper descriptions ("use X for Y, not for Z"); or merge.

17. **Vague tool description ("reads a file").** Selection failures, parameter mistakes.
    - **Fix:** First sentence has trigger words; describe when-to-use, when-not-to-use, return shape.

18. **30+ tools on one agent.** Selection chaos.
    - **Fix:** Curate to 5-15 essential; add lazy loading for rare tools.

19. **`run_command` with no allowlist.** Arbitrary code execution surface.
    - **Fix:** Specific tools per common command; or strict allowlist.

20. **Tool errors as raw exceptions.** Model can't recover gracefully.
    - **Fix:** Return structured error with suggestion: `{"error": "...", "suggestion": "try X"}`.

21. **Destructive tools without confirmation language.** Agent deletes things proactively.
    - **Fix:** Mark in description; gate with confirmation in harness for high-stakes ops.

---

## Evaluation

22. **3-task ad-hoc eval set.** No statistical signal.
    - **Fix:** At least 20 tasks covering happy paths, edge cases, refusals, ambiguity.

23. **Single-run results.** High variance; false confidence in deltas.
    - **Fix:** Run each task 3-5 times; report aggregate; flag high-variance tasks.

24. **Eval set drifts to be easy.** Pass rate climbs but real-world doesn't.
    - **Fix:** Periodically add hard cases from production failures.

25. **Same model judging itself.** Self-preference bias.
    - **Fix:** Use a stronger model as judge; pin temperature to 0.

26. **No baseline tracking.** "I think it's better."
    - **Fix:** Always show eval delta in PRs touching prompts/tools.

---

## Observability

27. **Logging only the final response.** Can't debug intermediate failures.
    - **Fix:** Log every iteration: tool, args, result summary, tokens.

28. **No trace IDs** linking agent to downstream services.
    - **Fix:** Propagate trace IDs through all tool calls.

29. **Discovering cost spikes from monthly bill.**
    - **Fix:** Per-session cost in real-time; alerts at thresholds.

30. **Logs but no dashboards.** Can't see patterns.
    - **Fix:** Minimum: success rate, p95 latency, cost per session, error rate.

---

## Safety

31. **Trust system prompt to enforce all safety.** Easily jailbroken.
    - **Fix:** Capability-based controls at the tool/permission layer.

32. **User input concatenated into system prompt.** Prompt injection paradise.
    - **Fix:** Wrap in delimiters; instruct model to treat as data.

33. **Single root credential** for all tool ops. Maximum blast radius.
    - **Fix:** Scoped credentials per capability.

34. **Confirming on every tool call.** Trains users to click through blindly.
    - **Fix:** Tier by blast radius; reserve gates for genuinely high-stakes ops.

35. **No audit log on mutations.** Can't investigate incidents.
    - **Fix:** Log every mutation with sanitized payload.

---

## Production

36. **Caching not measured.** Don't know if it works.
    - **Fix:** Log cache hit rate per request; target 70%+ on stable workloads.

37. **No rate limiting per user.** One adversarial user can rack up huge bills.
    - **Fix:** Per-user token / cost / call quotas.

38. **Production failures don't feed eval set.**
    - **Fix:** Process: each incident becomes a sanitized eval task.

39. **Privacy as an afterthought.** Raw user inputs in logs forever.
    - **Fix:** Redact at ingest; retention policies; access controls.

---

## General Mindset

40. **"The model is dumb" — when it's actually the harness.** Wrong tool description, missing context, no examples.
    - **Fix:** Before blaming the model, audit: what's in context? what's the tool surface? what does the system prompt say?

41. **Treating prompts and tools as throwaway scripts.** Production agents are software. They deserve version control, code review, tests, observability.
