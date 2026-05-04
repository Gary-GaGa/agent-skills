---
name: prompt-engineering
description: >
  Practical prompt engineering for building LLM applications. Covers system prompt
  structure, instruction design, few-shot, chain-of-thought, role assignment,
  output formatting, and cross-model differences. Use this skill when crafting
  the prompt for an agent, debugging "the model is wrong" issues, or migrating
  prompts between models.
category: ai-engineering
tags: [prompt, llm, claude, gpt, instruction-design]
related: [agent-harness-design, context-engineering, tool-design-for-agents, agent-evaluation, prompt-caching, skill-authoring, rag-deep-dive, multi-agent-orchestration, fine-tuning-guide]
---

# Prompt Engineering

> A prompt is a program. Variables, control flow, and output schema — just expressed in natural language. Treat it with the rigour of code.

## When to Use This Skill

- Writing the system prompt for a new agent
- Debugging "the model gives wrong answers" issues
- Tuning prompts to reduce token cost while keeping quality
- Migrating prompts between models (Claude ↔ GPT ↔ Gemini)
- Reviewing someone else's prompt

---

## System Prompt Anatomy

A well-structured system prompt usually has these sections, in this order:

```
1. Role / Identity        Who is the model? Persona, expertise.
2. Goal                   What is it trying to accomplish?
3. Context / Background   What does it need to know about the world?
4. Instructions           What rules to follow.
5. Tools (if any)         What it can do (often auto-injected).
6. Output format          Exactly how to respond.
7. Examples (few-shot)    Optional, but powerful.
8. Constraints / Refusals Hard rules.
```

Not every prompt needs all 8 — but check each is either present or deliberately omitted.

### Skeleton

```
You are <role>, an expert in <domain>. Your goal is to <goal>.

# Context
<facts the model needs>

# Instructions
- Do X
- Don't Y
- When Z, do W

# Output Format
Respond in <format>:
<schema>

# Examples
Input: <example input>
Output: <example output>
```

---

## Core Principles

1. **Be specific.** "Be helpful" → useless. "Recommend a refactor with file:line references" → actionable.

2. **Show, don't (only) tell.** One good example outperforms three paragraphs of instructions.

3. **Positive instructions over negative.** "Use bullet points" beats "don't use prose paragraphs". Models follow positive directives more reliably.

4. **Order matters.** What appears first and last gets weighted more (primacy + recency). Put critical instructions at the start of the system prompt and again near the end.

5. **One instruction per line.** Walls of prose hide individual rules. Bullet points let you reference them.

6. **Test for ambiguity.** If a sentence could be interpreted two ways, the model will sometimes pick the wrong one. Reword.

---

## Instruction Patterns

### Conditional logic

```
If the user mentions <X>, do <A>.
If the user mentions <Y>, do <B>.
Otherwise, do <C>.
```

Models handle if/elif/else surprisingly well when written this clearly.

### Step-by-step procedures

```
For each request:
1. Identify the file mentioned.
2. Read it.
3. Make the change.
4. Run tests.
5. Report back with a summary.
```

Numbered steps reduce skipped work.

### Structured refusals

```
Decline requests that:
- Involve real-world harm
- Require fabricating data

When declining, briefly explain why and offer an alternative if possible.
```

### Tone calibration

```
Communication style:
- Direct, no hedging
- Short sentences (avg 15 words)
- One concrete example per concept
- No marketing language
```

---

## Few-Shot Examples

Few-shot = showing input/output pairs. Often the highest-leverage prompt addition.

### Format

```
# Examples

Example 1
Input: <realistic input>
Output: <exact desired output>

Example 2
Input: <a contrasting case>
Output: <correct response>

Example 3
Input: <an edge case>
Output: <expected handling>
```

### Rules

7. **3-5 examples is the sweet spot.** Diminishing returns after that; cost grows linearly.
8. **Cover the variety.** One typical, one contrasting, one edge case.
9. **Examples should be exact format.** If you want JSON, examples are JSON. If you want bullets, examples are bullets.
10. **Don't include errors.** Models pattern-match — if your examples have typos or wrong structure, output will too.

---

## Chain-of-Thought (CoT)

Asking the model to "think step by step" before answering improves reasoning on complex tasks.

### Variants

| Variant | Form |
|---------|------|
| **Zero-shot CoT** | "Think step by step before answering." |
| **Structured CoT** | "First, list assumptions. Then, derive each step. Finally, give the answer." |
| **Hidden reasoning** | "Reason inside `<thinking>` tags. Then provide the final answer outside the tags." (For when output must be clean.) |
| **Extended thinking** (Claude) | Native feature — request thinking via API parameter, not prompt |

### When CoT helps

- Math, logic, multi-step reasoning
- Code review, debugging
- Decisions with multiple criteria

### When CoT hurts

- Simple lookups (overhead, no benefit)
- Streaming UIs (users see "thinking..." too long)
- Strict format outputs (model leaks thinking into output)

---

## Output Formatting

### Markdown

Most user-facing prompts. Models output good markdown by default.

```
# Output Format
Respond in markdown:
- Top-level summary in 1-2 sentences
- Bulleted list of findings
- Code blocks for any code references
```

### JSON

For programmatic consumption.

```
# Output Format
Respond with valid JSON matching this schema:
{
  "decision": "approve" | "reject" | "needs_review",
  "reason": "<one-sentence explanation>",
  "evidence": ["<quoted text>", ...]
}

Do not include markdown fences or commentary outside the JSON.
```

For Claude, prefer **tool calls with structured output** over freeform JSON — tool schemas are enforced, freeform JSON can fail to parse.

### XML tags

Useful for delimiting sections in input or output:

```
<context>
The user's repository is a Go monolith with...
</context>

<task>
Explain why test X is flaky.
</task>
```

Claude is particularly good at parsing XML tags. They reduce ambiguity about boundaries.

---

## Variables and Templating

Treat the prompt as a function:

```
You are reviewing a pull request titled "{title}" by {author}.

The diff is:
<diff>
{diff}
</diff>

Identify any of these issues: ...
```

Rules:

11. **Always escape user input.** A user could include text like "ignore previous instructions" — don't let it leak into your control flow. Use clear delimiters (`<user_input>...</user_input>`).
12. **Validate variable types.** `{count}` should be a number, not "five". Validate in code, not in the prompt.
13. **Test with empty / extreme values.** What if `{diff}` is empty? 100 lines? 10,000 lines?

---

## Cross-Model Differences

| Behavior | Claude | GPT-4 | Gemini |
|----------|--------|-------|--------|
| **XML tags** | Excellent parsing | Decent | Decent |
| **Markdown output** | Native, clean | Native | Tends to over-decorate |
| **Long context** | Strong recall (200K) | Good (128K) | Strong (1M+) but variable |
| **Strict JSON output** | Use tool calls | Native JSON mode | Native JSON mode |
| **Refusal style** | Direct, brief | Verbose, hedging | Variable |
| **System prompt adherence** | Strong | Strong | Looser |

**When migrating between models:**
- Re-test all prompts; behaviors differ
- Replace XML with explicit headings if moving from Claude → others
- Replace freeform JSON with structured outputs where supported
- Re-tune temperature and max tokens

---

## Common Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| "Be helpful and accurate" | Vague platitude, no signal | Specific behaviors |
| 2,000-word system prompt | Diluted attention, costly | Refactor — most prompts shouldn't exceed 500 words system + 5 examples |
| Negative-only instructions | Models follow positive better | Recast as positive |
| Putting critical info in middle | Lost-in-the-middle effect | Top or bottom |
| One example | Pattern-locks the model | Provide 3-5 with variety |
| Format described in prose | Model misses details | Show the format directly |
| Mixing instructions with examples | Confusion | Clear sections |
| No iteration | Prompt is treated as final | Prompts are code — version, test, iterate |

---

## Testing & Iteration

Prompts need tests like code:

1. **Build a small eval set.** 10-20 representative inputs with expected behaviors.
2. **Run before any prompt change.** Note pass/fail.
3. **Make change, re-run.** Compare deltas.
4. **Track regressions.** A change that fixes case 7 but breaks cases 2 and 5 is a net loss.

See [`agent-evaluation`](../agent-evaluation/SKILL.md) for how to build this.

---

## Compression: Reducing Prompt Cost

Long prompts are expensive (per call) and slow. To compress:

| Technique | Impact |
|-----------|--------|
| Remove "please", "kindly", "if you don't mind" | -5% tokens, no quality change |
| Replace prose with bullet points | -20-30% tokens, often clearer |
| Move stable parts to system prompt + cache | -50%+ on repeated calls (with caching) |
| Use shorthand internally with one explanation | "F:N — file path:line number" |
| Drop few-shot examples that no longer fail | Re-add if regressions appear |

**Don't compress at the cost of clarity.** A working 800-token prompt beats a broken 400-token one.

See [`prompt-caching`](../prompt-caching/SKILL.md) for caching strategies.

---

## Checklist

- [ ] Role and goal stated clearly in the first paragraph
- [ ] Instructions are specific and use positive directives
- [ ] Output format is shown, not just described
- [ ] 3-5 few-shot examples (if task is non-trivial)
- [ ] User input is escaped with explicit delimiters
- [ ] Tested on representative inputs, including edge cases
- [ ] Total length is justified — no padding
- [ ] Key instructions appear at start and re-emphasized at end if long

---

## Related Skills

- [`agent-harness-design`](../agent-harness-design/SKILL.md) — the system the prompt drives
- [`context-engineering`](../context-engineering/SKILL.md) — what surrounds the prompt at runtime
- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — tool descriptions are part of the prompt
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — testing prompts systematically
- [`rules/prompt-style`](../../rules/prompt-style.md) — quick rule sheet for prompt writing
