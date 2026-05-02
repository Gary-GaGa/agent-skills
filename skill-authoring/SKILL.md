---
name: skill-authoring
description: >
  Meta-skill for writing good SKILL.md files — frontmatter design, when to load
  references, scope control, description writing for intent matching, and
  versioning. Use this skill when adding a new skill to a skills repo or
  refactoring an existing one for clarity and discoverability.
category: ai-engineering
tags: [skill, agent, meta, documentation, claude-skills]
related: [prompt-engineering, agent-harness-design, tool-design-for-agents]
---

# Skill Authoring

> A skill is a tiny, focused capability package an agent can load on demand. The frontmatter is its API; the body is its implementation. Both deserve the same care you'd give a public function.

## When to Use This Skill

- Writing a new skill for an agent skills repo (Anthropic Skills, internal collections, this repo)
- Refactoring an existing skill that's too big or too vague
- Designing a skill collection's conventions
- Auditing whether agents are actually loading and using skills correctly

---

## What Is a Skill, Mechanically?

A skill is typically:

```
skill-name/
├── SKILL.md          ← entry point with YAML frontmatter
└── references/       ← optional deep-dive docs loaded on demand
    ├── topic-a.md
    └── topic-b.md
```

The agent loads `SKILL.md` based on the frontmatter `description`. References are only loaded when the body of `SKILL.md` instructs.

**This is the key insight:** `SKILL.md` is the dispatch layer. Its job is to say "when am I relevant" (frontmatter) and "what should the agent do/know in 5 minutes" (body). Detail goes in references.

---

## Frontmatter: The Skill's API

```yaml
---
name: my-skill
description: >
  When the user wants to <X>, or asks about <Y>, this skill provides
  <capability>. Use it for <situations>.
category: ai-engineering
tags: [tag1, tag2]
related: [other-skill-name]
---
```

### `name`

1. **Lowercase, kebab-case.** Matches the folder name exactly.
2. **Concrete, not generic.** `prompt-engineering` ✅; `prompts` ❌.
3. **Stable forever.** Renaming breaks `related:` links and references.

### `description` — the most important field

The agent uses `description` to decide whether to load this skill. Treat it as a search query the agent will match against the user's intent.

Rules:

4. **Lead with the trigger.** "When the user wants to ___" or "Use this skill when ___".
5. **Use the user's vocabulary.** If users say "review my code", the description should contain "code review", not "merge candidate quality assessment".
6. **List concrete trigger phrases.** Two or three example user prompts that should fire this skill.
7. **State boundaries.** What it doesn't cover. Prevents over-firing.
8. **Keep under ~300 chars.** This is read by the agent every load — long descriptions cost tokens for every skill in the index.

### Description: bad → good

**Bad:**
```yaml
description: A skill about prompts.
```

**Better:**
```yaml
description: >
  Use this skill when writing or debugging prompts for LLMs. Covers system
  prompt structure, few-shot examples, chain-of-thought, and output formatting.
  Triggers: "write a prompt", "debug my prompt", "improve this prompt".
  Not for: tool schemas (see tool-design-for-agents).
```

The "better" version embeds **trigger keywords** ("prompt", "few-shot", "system prompt"), gives **concrete user phrases**, and **redirects** to a sibling skill.

### `category` and `tags`

9. **One category, multiple tags.** Category is the primary filing; tags are searchable attributes.
10. **Reuse existing tags.** Inconsistent tagging hurts discovery. Check siblings first.
11. **Don't put the language in `tags` if it's universal.** `python` as a tag means "this is python-specific".

### `related`

12. **List sibling skills the agent might want next.** "If you're using X, you'll often need Y."
13. **Make it bidirectional.** If A lists B, B should list A.
14. **Don't list everything.** 1-5 entries; not the whole repo.

---

## Body Structure

A good `SKILL.md` body is **load-once, act-many-times**. Structure:

```markdown
# <Skill Title>

> One-sentence elevator pitch.

## When to Use This Skill
<Concrete situations / trigger phrases.>

## Core Concepts (or "What This Provides")
<Minimum vocabulary the agent needs.>

## Rules / Patterns / Catalogue
<The actual content — numbered, scannable.>

## Examples
<1-3 concrete, runnable examples.>

## Anti-Patterns
<What not to do, with fixes.>

## Checklist
<Pre-flight or review checklist if applicable.>

## References
<Pointers to deeper docs in references/.>

## Related Skills
<Cross-links.>
```

Not every section is required, but **"When to Use" and rule/pattern content are non-negotiable.**

---

## Scope: One Skill, One Idea

The most common skill mistake is **scope sprawl**. Symptoms:

- The skill has 6+ top-level sections covering disjoint topics
- The body is > 600 lines
- The description tries to enumerate everything
- Related skills duplicate parts of the body

### Fix: split

Apply the same logic as function refactoring:

| If the skill covers... | Split into... |
|------------------------|---------------|
| Three distinct workflows | Three skills |
| One workflow with many sub-techniques | Keep one skill, push details to `references/` |
| One concept across two domains | Two skills with shared `related:` |

### Sizing heuristic

- **Single SKILL.md, no references:** 100-400 lines.
- **SKILL.md + references:** SKILL.md stays under 400; references can be 200-1000 each.
- **If SKILL.md exceeds 400 lines and you can't extract references:** the skill is probably two skills.

---

## Using References

References are loaded on demand. Use them when:

15. **Detail is reference material the agent only needs sometimes.** "API endpoints", "error code tables", "language-specific syntax".
16. **The detail bloats the main file beyond ~400 lines.** Move out to keep the entry-point lean.
17. **The detail is language- or implementation-specific** while the skill is conceptual. Separate the concept (in SKILL.md) from the implementation (in references).

### Reference structure

```
my-skill/
├── SKILL.md
└── references/
    ├── README.md              ← optional index of references
    ├── nodejs-examples.md
    ├── python-examples.md
    └── error-codes.md
```

Inside `SKILL.md`:

```markdown
For complete examples in Node.js, see `references/nodejs-examples.md`.
```

The agent will follow the link only when the topic comes up.

---

## Writing for Two Audiences

A skill is read by:

- **The agent** — programmatically, choosing whether to load and what to do.
- **Humans** — for review, contribution, debugging.

### Agent-friendly traits

- Numbered rules (so they can be cited: "violates rule 7 of <skill>")
- Concrete imperatives ("do X", "don't Y") over abstract advice
- Tables for lookups
- Examples in the format the agent will produce

### Human-friendly traits

- Top elevator-pitch quote
- Cross-references to related skills
- Anti-patterns section with the *why*
- Cohesive narrative across sections

These don't conflict. Good skills serve both.

---

## Versioning & Stability

18. **`name` is forever.** Renaming breaks links and any `related:` pointing here.
19. **`description` can evolve** but big rewrites should bump conceptual scope, not just wording.
20. **Body changes are normal.** Treat `SKILL.md` like any source file — commits, PR review, etc.
21. **Breaking content changes deserve mention.** If a rule reverses (was "use X", now "avoid X"), note it visibly so consumers don't miss it.

---

## Common Mistakes

| Mistake | Why bad | Fix |
|---------|---------|-----|
| Vague description ("a skill about X") | Agent can't match intent | Lead with trigger phrases |
| Description duplicates the title | Adds no signal | Remove or rewrite |
| Body has no concrete rules | Agent has nothing to apply | Add numbered rules with examples |
| Examples don't match what the body teaches | Confuses the agent | Examples are the canonical demonstration |
| Cross-references to non-existent skills | Dangling link | Either create the skill or remove the reference |
| Frontmatter `name` differs from folder | Agent loaders break | Match exactly |
| References nested 3+ levels deep | Agent can't find them | Flat `references/` directory |
| Body restates what the description says | Wasted tokens | Body assumes description is read |

---

## How Agents Actually Load Skills

(Roughly, depending on the harness — but this mental model helps.)

```
1. Agent receives user query
2. Harness reads index of all SKILL.md frontmatter
3. Agent (or rule) selects matching skills based on description + tags
4. Selected SKILL.md(s) loaded into context
5. Agent performs the task with skill content available
6. If body says "see references/foo.md", that's loaded only if relevant
```

Implications:

- **Frontmatter is read for every query.** Keep it tight.
- **Body is read when the skill is selected.** It's OK to be more detailed there.
- **References are read only when the body links to them.** Push depth here.

---

## Authoring Workflow

1. **Identify the gap.** What can't the agent do well today?
2. **One-sentence pitch.** If you can't write it in a sentence, the scope isn't clear.
3. **Draft frontmatter first.** Description forces you to commit to scope.
4. **Outline the body.** Sections, not prose.
5. **Fill in rules and examples.** Numbered, concrete.
6. **Add anti-patterns.** What not to do is often clearer.
7. **Cross-link related skills.** Bidirectional.
8. **Test with the agent.** Run the agent on relevant queries, check whether it loads and applies the skill correctly.
9. **Iterate.** First drafts are rarely tight enough. Expect 2-3 revisions.

---

## Quality Checklist

- [ ] `name` is kebab-case and matches folder
- [ ] `description` leads with trigger phrases, < 300 chars
- [ ] `category` exists in the repo's category list
- [ ] `tags` reuse existing terms where possible
- [ ] Body has clear sections (When to Use, Rules/Patterns, Examples)
- [ ] Rules are numbered for citation
- [ ] At least one concrete, well-formed example
- [ ] Anti-patterns section with at least 3 entries
- [ ] Body length appropriate (100-400 lines for SKILL.md)
- [ ] Cross-references to related skills are bidirectional
- [ ] No broken links to references that don't exist
- [ ] Tested by running the agent on realistic queries

---

## Related Skills

- [`prompt-engineering`](../prompt-engineering/SKILL.md) — descriptions are micro-prompts; same principles apply
- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — tool descriptions follow similar trigger-word logic
- [`agent-harness-design`](../agent-harness-design/SKILL.md) — skills are part of the harness's tool/capability surface
