---
name: context-engineering
description: >
  Practical strategies for managing what an LLM sees on each turn — context window
  budgeting, compaction, summarization, retrieval (RAG basics), conversation memory,
  and selective context injection. Use this skill when an agent forgets earlier
  instructions, runs out of context, or returns inconsistent results across long
  sessions.
category: ai-engineering
tags: [context, llm, rag, memory, compaction, agent]
related: [agent-harness-design, prompt-engineering, prompt-caching, rag-deep-dive, llm-cost-optimization, multi-agent-orchestration, tool-design-for-agents]
---

# Context Engineering

> The model only knows what's in its context window. Context engineering is deciding what to put in, what to leave out, and what to summarize — the most underrated lever in agent quality.

## When to Use This Skill

- Agent forgets earlier instructions or facts
- Agent hits context window limits on long sessions
- Long-running agents (Claude Code style) need memory beyond a single conversation
- Building RAG-style retrieval into an agent
- Token cost is dominating spend

---

## Why Context Matters More Than Model Size

Two truths shape this work:

1. **Recall degrades over distance.** Even with 200K-token windows, models attend better to the start and end. Information buried in the middle of a 100K-token context is unreliable. ("Lost in the middle" effect.)
2. **Cost grows linearly with context.** Every turn pays for everything in the prompt. A 50K-token conversation isn't free, even with caching.

**Implication:** A smaller, well-curated context often beats a bloated full-history dump.

---

## The Context Budget

Think of context as a budget — every component costs tokens.

```
Total context window (e.g. 200K tokens)
  = system prompt
  + tool definitions (these add up fast — 5K-15K typical)
  + conversation history
  + tool results (file contents, search results)
  + user's current message
  + room for the model's response (often reserved 4K-8K)
```

### Budget allocation strategy

| Budget item | % of total typical | When to compress |
|-------------|--------------------|------------------|
| System prompt | 1-5% | Almost never — keep stable for caching |
| Tool definitions | 2-10% | Trim unused tools, shorten descriptions |
| Conversation history | 30-70% | First place to compact |
| Tool results | 10-50% | Summarize large blobs (e.g. file contents) |
| Current input | 1-10% | Truncate user-supplied long inputs |

**Track tokens per turn.** If you don't measure, you don't manage.

---

## Three Core Strategies

### Strategy 1: Full History (Default)

Pass every turn verbatim. Simple, predictable.

✅ Use for: short tasks (< 20 turns), debugging, demos.
❌ Avoid for: long sessions, high-volume production.

### Strategy 2: Compaction

Periodically summarize older turns into a compact note.

```
[Original]
Turn 1: User asks to refactor module X
Turn 2: Agent reads file foo.ts (2,000 tokens of code)
Turn 3: Agent reads file bar.ts (3,000 tokens of code)
Turn 4: Agent makes edits...
... 30 turns later ...

[After compaction at turn 30]
<compacted_history>
Earlier in session: refactored module X. Read foo.ts and bar.ts.
Made edits to extract shared `validate()` helper. Tests pass.
Key decisions: kept old API for backward compat per user request.
</compacted_history>

Recent turns: <last 5 turns verbatim>
```

**Rules for good compaction:**

1. **Trigger by token count, not turn count.** Compact when context exceeds N% of window (e.g. 60%).
2. **Preserve the recent.** Always keep last 3-5 turns verbatim — recency matters most.
3. **Preserve key facts explicitly.** Hard-pin file paths, IDs, user preferences. Don't trust the summary alone.
4. **Use a separate model call for the summary.** Don't ask the same agent to summarize itself mid-task.
5. **Compact is lossy. Accept it.** If quality drops, it means something important was lost — refine the summary prompt, don't disable compaction.

### Strategy 3: Retrieval (RAG)

Store turns / docs / facts in external memory; retrieve only relevant pieces each turn.

```
1. User asks question
2. Embed the question
3. Retrieve top-K similar passages from memory
4. Inject only those into context
5. Model answers
```

✅ Use for: long-lived agents, knowledge bases, multi-session memory.
❌ Don't use for: short conversations (overhead exceeds benefit).

**Critical:** Retrieval misses cause silent failures. Mitigations:

- Always include some recent history regardless of retrieval
- Log retrieval queries and inspect when answers are wrong
- Test with deliberately ambiguous queries

---

## Pinning Critical Facts

Some information must survive every compaction or retrieval. Patterns:

### Pin in system prompt
```
You are working in repo: /Users/foo/project
Current branch: feat/oauth
Active issue: #142
```

### Pin in a "notes" section
```
<notes>
- User prefers TypeScript over JavaScript
- Tests live in __tests__/ next to source
- Don't suggest removing the legacy /v1 API
</notes>
```

### Pin via tool state
Some facts should live in tool responses, not the prompt. E.g. "what files have I edited" → a `list_changes` tool, not memorized.

**Rule of thumb:** If it changes, put it in tool state. If it's stable, put it in system prompt.

---

## Selective Context Injection

Don't always inject everything you have. Select per-turn:

| Situation | What to inject |
|-----------|----------------|
| User asks a code question | Recent file reads + relevant code snippets, not all conversation |
| User asks for a status update | Compacted summary + last action, not raw turn-by-turn |
| Model is in the middle of a tool sequence | Last few tool calls + plan, not earliest setup |
| New session, no prior context | Bare system prompt + user message |

This is sometimes called "context routing" or "dynamic prompting".

---

## Tool Result Compression

Tool results often dominate context size. Compress at three layers:

### 1. At the tool level

The tool itself returns a compressed result, not raw data:

- ❌ `read_file` returns full 10,000-line file
- ✅ `read_file` returns first 2,000 lines, with a flag if truncated
- ✅ `grep` returns matching lines, not full files
- ✅ `list_dir` returns names, not full stats per file

### 2. At the agent level

The agent summarizes tool results before continuing:

```
Model: <calls grep, gets 200 matches>
Model thinks: "200 matches is too many. Let me narrow."
Model: <calls grep with more specific pattern, gets 8 matches>
Model: <continues with 8>
```

Encourage this in the system prompt.

### 3. At the harness level

The harness post-processes tool results:

- Truncate after N tokens with "...truncated" notice
- Drop earlier tool results from context once newer ones supersede them
- Replace verbose results with summaries when they're no longer the focus

---

## Memory Across Sessions

For agents that span sessions (e.g. coding assistants over weeks):

| Memory type | Stored where | Used how |
|-------------|--------------|----------|
| **User preferences** | Stable file (e.g. CLAUDE.md, settings) | Loaded into system prompt every session |
| **Project facts** | Stable file (e.g. README, CLAUDE.md) | Loaded once or via retrieval |
| **Recent decisions** | Per-session log | Summarized into next session's start |
| **Code state** | The codebase itself | Read on demand via tools |

**Don't put state in the model's "memory".** Put it in files the agent reads. The codebase is the source of truth; the agent is stateless between sessions.

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| Pass full 100K-turn history every call | Cost + lost-in-the-middle | Compaction |
| Compact too aggressively (e.g. every 5 turns) | Loses fidelity, model forgets | Trigger by token count |
| Trust summary as "good enough" | Summary loses critical IDs/paths | Pin facts explicitly |
| Put dynamic state in system prompt | Cache invalidates every call | Move dynamic state to user message or notes section |
| Raw RAG with no recent history | Model can't follow conversation flow | Always include last N turns |
| One big prompt with everything | Lost-in-the-middle, expensive | Selective injection per turn |
| Tool returns 50K-token blob | Eats context budget | Tool returns summary or first N |

---

## Measurement

What to measure:

- **Tokens per turn** (input and output, separately)
- **Cumulative tokens per session**
- **Cache hit rate** (with prompt caching)
- **Compaction events** — how often, how lossy
- **Recall checks** — periodically test "do you remember the user said X?"

What to log:

- For each turn: input tokens, output tokens, did compaction trigger
- For each compaction: turns compressed, original size, summary size

---

## Decision Tree

```
Is the conversation > 30 turns expected? ────► Yes ────► Use compaction
                  │
                  No
                  │
Will the agent span sessions? ────► Yes ────► External memory + retrieval
                  │
                  No
                  │
Is context cost a concern? ────► Yes ────► Selective injection + caching
                  │
                  No
                  │
                  └────► Full history (default)
```

---

## Checklist

- [ ] You can answer: "what does the model see on turn N?"
- [ ] System prompt is stable (caching-friendly)
- [ ] Token usage per turn is logged and reviewed
- [ ] Long sessions have a compaction trigger
- [ ] Compaction preserves critical facts (pinned)
- [ ] Tool results are bounded in size
- [ ] Cross-session state lives in files, not "memory"
- [ ] You've tested "does the model remember X" after long runs

---

## Related Skills

- [`agent-harness-design`](../agent-harness-design/SKILL.md) — context strategy is part of harness design
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — what fills the context
- [`prompt-caching`](../prompt-caching/SKILL.md) — making stable context cheap
- [`agent-observability`](../agent-observability/SKILL.md) — measuring context behavior
- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — tool design affects context size
