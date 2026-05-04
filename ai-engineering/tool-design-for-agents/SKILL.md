---
name: tool-design-for-agents
description: >
  How to design tools that LLM agents use well — schema design, naming, descriptions,
  error semantics, idempotency, return shape, and selection heuristics. Use this
  skill when adding a new tool to an agent, debugging "the model picks the wrong
  tool", or auditing an existing tool surface.
category: ai-engineering
tags: [tool, agent, json-schema, design, llm]
related: [agent-harness-design, prompt-engineering, mcp-server-design, agent-safety-guardrails, skill-authoring, context-engineering, agent-evaluation]
---

# Tool Design for Agents

> Tools are the agent's hands. A poorly-designed tool surface dooms even the smartest model. Treat tool descriptions and schemas with the same rigour as your system prompt — they ARE part of the prompt.

## When to Use This Skill

- Designing a new tool for an agent
- Debugging "the model picks the wrong tool" or "the model misuses the tool"
- Auditing an existing tool surface for redundancy or gaps
- Migrating tools between providers (Anthropic, OpenAI, MCP)

---

## What Is a Tool, Really?

A tool, from the model's perspective, is:

```
- A name             ("read_file")
- A description      ("Reads a file from the local filesystem...")
- A parameters schema ({"path": "string", "limit": "integer?"})
- A response shape   (text content)
```

The model sees nothing about the implementation. It picks tools by **name + description**, fills parameters from the **schema**, and reasons about results from the **response shape**.

**Implication:** If the model misbehaves, the cause is almost always in those four fields, not in the implementation.

---

## Naming

1. **Verb-noun, lowercase, snake_case.** `read_file`, `search_code`, `create_branch`.
2. **Match user vocabulary, not implementation.** `search_code` not `ripgrep_invoke`.
3. **Avoid abbreviations.** `read_file` beats `rd_f`.
4. **No overlapping names.** If you have `find_file` and `search_file`, the model will guess. Pick one.
5. **Don't reuse names across categories.** A `delete` tool that handles files and database rows confuses selection.

### Naming patterns

| Pattern | Example | Use for |
|---------|---------|---------|
| `<verb>_<noun>` | `read_file`, `list_branches` | Most CRUD-like operations |
| `<verb>_<adjective>_<noun>` | `list_open_pulls` | When the noun has implicit qualifiers |
| `<source>_<verb>` (avoid) | `github_create` | Unclear scope; prefer the inverse |

---

## Description: The Single Highest-Leverage Field

The model decides whether to call your tool primarily from its description. **Optimize this like a search query.**

### Description structure

```
[One-sentence summary of what the tool does, including key trigger words]

[When to use vs not use]

[Important behaviors / constraints]

[Examples (optional)]
```

### Example: bad → good

**Bad:**
```
Reads a file.
```

**Better:**
```
Reads a file from the local filesystem and returns its contents as text.

Use this when:
- The user references a specific file path
- You need to inspect code, config, or data files
- A previous tool result mentioned a path you need to verify

Do not use for:
- Listing files in a directory (use list_dir)
- Searching across many files (use search_code)

Returns: file contents as text. If the file is large, returns the first 2,000 lines with a "truncated" marker.
```

The "good" version embeds **trigger words** ("file path", "inspect"), explicit **boundaries** ("do not use for"), and **return semantics**.

### Rules

6. **Front-load trigger words.** First 100 chars matter most for selection.
7. **State boundaries explicitly.** What it doesn't do prevents misuse.
8. **Document return shape.** Is it truncated? Paginated? Errors as exceptions or strings?
9. **Cross-reference sibling tools.** "Use X for Y; for Z use W instead." Eliminates ambiguity.

---

## Parameter Schema

Use JSON Schema (or whichever schema your provider uses).

### Rules

10. **Each parameter has a `description`.** Required even for "obvious" params like `path`.
11. **Use precise types.** `"type": "integer"` over `"number"` when fractional doesn't make sense.
12. **Use `enum` for fixed choices.** `"status": {"enum": ["open", "closed", "merged"]}` beats free-form strings.
13. **Mark required vs optional explicitly.** Don't rely on implicit defaults.
14. **Provide examples for complex params.** Especially when the format is non-obvious.

### Good example

```json
{
  "type": "object",
  "properties": {
    "path": {
      "type": "string",
      "description": "Absolute path to the file. Relative paths are not supported."
    },
    "offset": {
      "type": "integer",
      "minimum": 0,
      "description": "Line number to start reading from (0-indexed). Defaults to 0."
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 5000,
      "description": "Maximum number of lines to read. Defaults to 2000. Use a smaller value for large files."
    }
  },
  "required": ["path"]
}
```

### Anti-patterns

| Anti-pattern | Fix |
|--------------|-----|
| `"args": {"type": "string"}` (catch-all) | Define each arg as its own typed property |
| Optional params without defaults documented | State the default in description |
| Mutually-exclusive params not constrained | Use `oneOf` or split into separate tools |
| Numeric strings (`"5"` instead of `5`) | Use proper types |

---

## Granularity: Few Coarse vs Many Fine

The classic trade-off:

| Approach | Pros | Cons |
|----------|------|------|
| **Few coarse tools** (`run_command`, `query_db`) | Flexible, fewer descriptions to write | Model errors on syntax/escaping; harder to constrain; safety risk |
| **Many fine tools** (`read_file`, `edit_file`, `list_dir`) | Constrained, predictable, safer | More tools = harder selection; more descriptions to maintain |

### Heuristics

15. **Fine-grained for high-frequency, well-known operations.** Reading files, listing directories, common DB queries.
16. **Coarse for long-tail.** A `run_command` tool for the 10% of cases not covered by fine tools.
17. **Aim for 5-15 tools per agent.** Below 5 = limited; above 15 = poor selection unless they form clear sub-groups.
18. **Don't expose the full implementation.** A "git" tool with 30 sub-commands is bad; pick the 5-7 verbs the agent needs.

---

## Return Shape

What the tool returns is what the model reasons about. Design the return like an API response.

### Rules

19. **Return structured information when possible.** A list of matches with `{file, line, snippet}` beats a wall of text.
20. **Bound the size.** Truncate at a known limit, mark the truncation explicitly.
21. **Errors are part of the contract.** Return errors in a way the model can reason about — don't just throw.
22. **Don't return implementation noise.** SQL stack traces, internal IDs, transient state — strip before return.

### Error patterns

| Style | When |
|-------|------|
| **Exception (provider serializes)** | True bugs, malformed input |
| **Error in result body** | Expected failures the model should reason about (file not found, permission denied) |
| **Empty result** | Valid query, no matches — the model should know "no results" vs "tool failed" |

**Distinguish "tool failed" from "no answer".** They have different recovery paths.

### Example error returns

```json
// File not found — model can react ("ah, let me look elsewhere")
{ "error": "FILE_NOT_FOUND", "path": "/foo/bar", "suggestion": "Try list_dir to find the correct path" }

// Permission denied — model should escalate, not retry
{ "error": "PERMISSION_DENIED", "path": "/etc/shadow", "fatal": true }

// Empty — not an error, just no matches
{ "matches": [] }
```

---

## Idempotency & Side Effects

23. **Mark side effects loudly.** A `delete_branch` description should say so up front.
24. **Idempotent tools first.** Read-only tools encourage safe exploration. The model can call them freely without breaking anything.
25. **For destructive tools, encourage confirmation.** Either via the system prompt ("ask before destructive ops") or via the tool itself (a dry-run mode).

### Tool taxonomy

| Type | Examples | Default model behavior |
|------|----------|------------------------|
| **Read-only** | `read_file`, `list_dir`, `search_code` | Call freely |
| **Local mutation** | `edit_file`, `create_file` | Verify intent, often OK |
| **Network mutation** | `create_pr`, `send_email` | Should confirm with user |
| **Irreversible** | `delete_branch`, `force_push` | Strong confirmation required |

---

## Tool Result Size Management

Tools that return lots of data (file contents, search results, query rows) eat context fast.

Patterns:

| Pattern | When |
|---------|------|
| **Truncate with marker** | "First 2000 lines of N. Truncated." Default for read tools. |
| **Paginate** | Provide `cursor` / `next_token`. Good when the model may want all of it. |
| **Summarize at the tool** | Tool returns a summary; provide a separate `read_full` if needed. |
| **Filter at the tool** | Take a filter/regex; return only matches. |

**Rule:** A tool result > ~5K tokens is a smell. Either the tool is too coarse, or it should be summarizing.

---

## Tool Discovery: How Many to Show?

Every tool definition costs tokens (often 500-1500 each). On large surfaces:

- **Always available:** Core tools the agent uses 80% of the time (3-7 of them).
- **Lazily loaded:** Less-used tools loaded on demand (via meta-tools, MCP, or prompt-driven discovery).

### Lazy loading patterns

- **Meta-tool pattern.** A `list_available_tools(query)` tool returns matching tools' definitions.
- **Tier loading.** Common tools always shown; advanced tools shown when keywords appear in input.
- **MCP servers as namespaces.** Group related tools; load the namespace when relevant.

For most agents (< 20 tools), all-tools-always is fine.

---

## Common Failure Modes

| Failure | Likely cause | Fix |
|---------|--------------|-----|
| Picks wrong tool | Overlapping descriptions | Sharpen boundaries; add "use X for Y, not for Z" |
| Wrong parameters | Vague schema | Add examples, descriptions, enums |
| Calls tool repeatedly with same input | Result not informative | Make result more useful or add error explanation |
| Never calls a tool | Description doesn't match query language | Add trigger words; describe in user vocabulary |
| Calls dangerous tool unprompted | No autonomy guidance | Mark side effects; add confirmation |
| Tool result too large | No truncation | Add limits + truncation marker |
| Tool error confuses model | Poor error message | Errors should suggest next action |

---

## Auditing an Existing Tool Surface

Run this checklist on each tool:

- [ ] Name follows verb-noun convention
- [ ] Description has trigger words in first 100 chars
- [ ] Description states when NOT to use it
- [ ] Each parameter has a description
- [ ] Required vs optional is explicit
- [ ] Enums used for fixed choices
- [ ] Return shape documented
- [ ] Errors are recoverable signals, not noise
- [ ] Side effects clearly marked
- [ ] Result size is bounded

For the surface as a whole:

- [ ] No two tools have overlapping purpose
- [ ] Total count is 5-20 (or you have lazy loading)
- [ ] Read-only tools form the majority
- [ ] Destructive tools are clearly distinguished
- [ ] You've tested the agent picks correctly on representative queries

---

## Related Skills

- [`agent-harness-design`](../agent-harness-design/SKILL.md) — tools live in the harness
- [`prompt-engineering`](../prompt-engineering/SKILL.md) — descriptions are part of the prompt
- [`mcp-server-design`](../mcp-server-design/SKILL.md) — packaging tools as MCP servers
- [`context-engineering`](../context-engineering/SKILL.md) — tool result size affects context budget
- [`rules/tool-schema`](../../rules/tool-schema.md) — quick rule sheet for tool schemas
