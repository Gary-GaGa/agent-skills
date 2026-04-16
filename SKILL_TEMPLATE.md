---
name: your-skill-name
description: >
  One to three sentences describing when an agent should invoke this skill.
  Write it in the form "Use this skill when the user wants to …". Include
  concrete trigger phrases so intent-matching works well. Keep under ~300 chars.
category: engineering        # one of: engineering | content | devops | testing | review | data
tags: [tag1, tag2, tag3]     # free-form, lowercase, kebab-case; include language/framework/purpose
related: []                  # optional; list sibling skill names (e.g. [clean-ddd-go])
---

# <Skill Title>

> Replace this quote with a one-line elevator pitch for the skill.

## When to Use This Skill

Describe the situations, user phrases, or task types that should trigger this skill. Be specific — good matching beats clever writing.

Examples of trigger intent:
- "help me do X in Y"
- "review my <thing>"
- "explain how <concept> works"

## What This Skill Provides

Bullet list of the concrete capabilities the skill delivers:

- Capability 1
- Capability 2
- Capability 3

## Core Concepts

Explain the minimum vocabulary an agent needs to operate effectively in this domain. Keep it tight — link out to references for depth.

## Rules / Conventions

If the skill enforces a methodology or style, list the rules here. Number them so they can be referenced from reports or PRs.

1. Rule one.
2. Rule two.
3. Rule three.

## Examples

Provide 1–3 minimal, runnable examples that demonstrate the skill in action. Prefer real code / real prose over pseudocode.

```lang
// example
```

## Checklist (optional)

If the skill includes a pre-flight or review checklist, put it here as a task list.

- [ ] Item 1
- [ ] Item 2

## References (optional)

If your skill has a `references/` subdirectory with deeper docs loaded on demand, list them here:

- `references/foo.md` — short description
- `references/bar.md` — short description

## Related Skills (optional)

- [`other-skill`](../other-skill/SKILL.md) — how it relates
