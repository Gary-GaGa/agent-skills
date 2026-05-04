---
name: technical-writing-en
description: >
  English technical writing guide — READMEs, API docs, architecture decision
  records (ADRs), changelogs, and inline documentation. Use this skill when
  writing developer-facing documentation, reviewing someone's docs, or
  setting documentation standards for a team.
category: content
tags: [writing, documentation, readme, adr, api-docs, english]
related: [medium-writing-zh, skill-authoring, code-review]
---

# Technical Writing (English)

> Good docs answer one question clearly. Bad docs answer many questions vaguely.

## When to Use This Skill

- Writing a README for a new project
- Documenting an API
- Writing an architecture decision record (ADR)
- Reviewing someone's documentation
- Setting documentation standards for a team

---

## README.md

Every repo needs one. The reader is a developer who just cloned the repo.

### Structure

```markdown
# Project Name

One-line description.

## Quick Start
How to install, configure, and run in < 5 minutes.

## Usage
Core use cases with code examples.

## Development
How to set up the dev environment, run tests, lint.

## Architecture (optional)
High-level diagram + link to detailed docs.

## Contributing (optional)
How to contribute; link to CONTRIBUTING.md.

## License
```

### Rules

1. **Lead with what the project does, not what it is.** "Generates API documentation from OpenAPI specs" > "A documentation generation framework".
2. **Quick Start comes first.** The reader's first question is "how do I run this?"
3. **Code examples are mandatory.** A README without a code example is incomplete.
4. **Keep it current.** Stale READMEs erode trust. Update when commands or architecture change.

---

## API Documentation

### What to document per endpoint

```markdown
### Create Order

`POST /v1/orders`

Creates a new order for the authenticated user.

**Request Body**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| items | array | yes | List of {product_id, quantity} |
| currency | string | no | ISO 4217 code. Default: "TWD" |

**Response** `201 Created`
​```json
{
  "id": "ord-42",
  "status": "pending",
  "total": 1500
}
​```

**Errors**
| Status | Code | When |
|--------|------|------|
| 400 | INVALID_INPUT | Missing required fields |
| 401 | UNAUTHORIZED | No or invalid token |
```

### Rules

5. **Document every field.** Even "obvious" ones. What's obvious to you isn't to your caller.
6. **Include realistic examples.** Real JSON, real values (sanitized).
7. **Document errors explicitly.** Not just success paths.
8. **Version your docs with your API.** `/v1` docs and `/v2` docs are separate.

---

## Architecture Decision Records (ADRs)

Capture the *why* behind significant decisions. Format:

```markdown
# ADR-001: Use sqlc over GORM

## Status
Accepted (2025-01-15)

## Context
We need a Go SQL layer. Options: raw database/sql, GORM, sqlc, sqlx.

## Decision
Use sqlc. It generates type-safe Go from SQL queries with zero runtime reflection.

## Consequences
- Positive: compile-time query validation, no ORM magic, fast
- Negative: must write raw SQL (team needs SQL skills), harder dynamic queries
- Neutral: migration tooling is separate (using golang-migrate)

## Alternatives Considered
- GORM: too much magic; hard to debug generated queries
- sqlx: good, but no compile-time safety
- raw database/sql: verbose; error-prone scanning
```

### Rules

9. **One decision per ADR.** "Use Kafka" and "Use PostgreSQL" are separate ADRs.
10. **Include alternatives considered.** The reader needs to know what was rejected and why.
11. **ADRs are immutable.** If you reverse a decision, write a new ADR that supersedes the old one.
12. **Status field is important.** `Proposed`, `Accepted`, `Deprecated`, `Superseded by ADR-XXX`.

---

## Changelogs

### Format (Keep a Changelog)

```markdown
## [1.2.0] - 2025-01-15

### Added
- OAuth2 login flow (#142)

### Fixed
- Race condition in cache eviction (#201)

### Changed
- Minimum Go version is now 1.23

### Removed
- Deprecated /v1/legacy endpoint
```

13. **Human-readable, not git log.** Users care about *what changed for them*, not commit hashes.
14. **Group by type: Added, Fixed, Changed, Removed.**
15. **Link to issues/PRs.** `(#142)` links to the context.

---

## Inline Documentation (Code Comments)

16. **Comment the *why*, not the *what*.** The code shows what; comments explain non-obvious reasoning.
17. **No comment is better than a wrong comment.** Stale comments mislead.
18. **Godoc style for Go:** One-line comment above exported symbols starting with the symbol name.
    ```go
    // ProductRepository defines persistence operations for Product aggregates.
    type ProductRepository interface { ... }
    ```

---

## Writing Style Rules

19. **Active voice.** "The server validates the token" > "The token is validated by the server".
20. **Present tense.** "Returns a list" > "Will return a list".
21. **Short sentences.** Max 25 words. Break long sentences at conjunctions.
22. **One idea per paragraph.** If a paragraph covers two things, split it.
23. **Use "you" for the reader.** "You can configure..." > "Users can configure..."
24. **Avoid jargon without explanation.** First use of a term: define it or link to definition.
25. **Code formatting for code.** `function_name`, `variable`, `--flag` in backticks.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| README that starts with installation | Start with what the project does |
| No code examples | Add at least one per section |
| "See the code for documentation" | Write actual docs |
| Giant wall of text | Use headings, tables, code blocks |
| Documenting implementation details that change | Document behavior and contracts |
| Comments that restate the code | Delete them; comment the why |
| Never updating docs | Review docs in PRs; stale docs = wrong docs |

---

## Checklist

- [ ] README has: description, quick start, usage with examples, dev setup
- [ ] API docs cover every endpoint with request/response/errors
- [ ] ADRs exist for significant decisions
- [ ] Changelog updated on each release
- [ ] No stale documentation (verified in last quarter)
- [ ] Active voice, present tense, short sentences
- [ ] Code examples are realistic and tested

---

## Related Skills

- [`medium-writing-zh`](../medium-writing-zh/SKILL.md) — blog writing (different audience, different rules)
- [`skill-authoring`](../../ai-engineering/skill-authoring/SKILL.md) — writing skill docs follows similar principles
- [`code-review`](../../engineering/code-review/SKILL.md) — docs are part of the review
