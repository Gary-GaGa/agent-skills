---
name: agentic-coding-patterns
description: >
  Patterns for writing code that AI coding agents work well with — CLAUDE.md
  design, test-friendly architecture, modular structure, clear naming, and
  conventions that reduce agent errors. Use this skill when setting up a repo
  for AI-assisted development or improving agent effectiveness on your codebase.
category: ai-engineering
tags: [agent, coding, claude-code, developer-experience, codebase-design]
related: [claude-code-customization, skill-authoring, clean-ddd-go, go-testing]
---

# Agentic Coding Patterns

> The codebase is the agent's world model. A codebase that's clear to humans is 10× clearer to agents. A codebase that confuses humans is 100× worse for agents.

## When to Use This Skill

- Setting up a repo for Claude Code / Copilot / Cursor / other AI coding tools
- Agent keeps making wrong assumptions about your code
- Want to reduce "context" the agent needs to be effective
- Preparing a codebase for AI-assisted development at scale

---

## Core Principle

**Make the implicit explicit.** Agents can't ask hallway questions. Everything they need must be discoverable from files.

---

## 1. CLAUDE.md (or equivalent memory file)

The single highest-ROI investment for agent-assisted repos.

### What to include

```markdown
# Project: catalog-api

## Stack
Go 1.23, Echo framework, PostgreSQL 16, sqlc for queries.

## Commands
- `make test` — run all tests
- `make lint` — golangci-lint
- `make build` — build binary to ./bin/server
- `make migrate-up` — run DB migrations

## Architecture
Clean Architecture (see clean-ddd-go skill):
- internal/domain/ — entities, value objects, repository interfaces
- internal/usecase/ — services, DTOs, port interfaces
- internal/interface/ — HTTP handlers, repository implementations
- internal/infrastructure/ — DB client, config, logger

## Conventions
- Errors: wrap with %w at layer boundaries (see rules/go-error-handling)
- Naming: follow rules/go-naming
- Tests: table-driven, fakes over mocks
- Commits: Conventional Commits format

## Things to avoid
- Don't modify internal/legacy/ — it's being deprecated
- Don't use raw SQL; use sqlc generated code
- Don't add dependencies without discussing first
```

### Rules

1. **Keep CLAUDE.md under 500 lines.** It loads every session.
2. **Update it when conventions change.** Stale CLAUDE.md = wrong agent behavior.
3. **Point to skills/rules instead of duplicating.** "See rules/go-naming" beats copying 50 rules.
4. **Include the commands.** Agents need to know how to test, lint, build.

---

## 2. Test-Friendly Architecture

Agents verify their work by running tests. Make this easy.

5. **Tests must be runnable with one command.** `make test` or `go test ./...`. No manual setup.
6. **Tests must be fast.** < 30 seconds for the full suite. Agents run tests many times per session.
7. **Tests must be deterministic.** Flaky tests confuse agents (and humans).
8. **Failing tests must have clear error messages.** `expected 5, got 3 for product.Stock` > `assertion failed`.
9. **Tests exist for the code the agent will modify.** No tests = agent can't verify its work.

---

## 3. Modular Structure

10. **Small files.** Files under 300 lines are navigable by agents. 1000+ line files cause context overflow.
11. **One concept per file.** `product.go` has the Product entity. `repository.go` has the repository interface.
12. **Predictable file locations.** If the agent knows "handlers live in `internal/interface/in/http/`", it finds them immediately.
13. **Consistent patterns across modules.** Every bounded context has the same file structure → agent learns the pattern once.

---

## 4. Clear Naming

14. **Function names describe the action.** `SellProduct`, not `Process`.
15. **Variable names describe the content.** `productRepo`, not `r` or `repo1`.
16. **Avoid abbreviations the agent might misinterpret.** `ctx` and `err` are universally understood; `prdRepo` is not.
17. **Boolean names are questions.** `IsActive()`, `HasPermission()`, `CanRetry()`.

---

## 5. Discoverable Documentation

18. **README.md at repo root.** How to set up, run, test. The agent reads this first.
19. **Architecture decision records (ADRs) for non-obvious choices.** "Why we use sqlc instead of GORM" helps the agent avoid suggesting GORM.
20. **Inline comments only for the non-obvious.** Don't comment what the code does (agent can read); comment why it does it differently than expected.

---

## 6. Reducing Agent Errors

### Linting as guardrails

21. **Strict linter config committed to repo.** The agent runs the linter; violations guide self-correction.
22. **Format on save via hooks.** Agent doesn't need to think about formatting.

### Type safety

23. **Strong types over stringly-typed code.** `type OrderID string` > `string` everywhere. The agent makes fewer type confusion errors.
24. **Enums / constants over magic strings.** `StatusActive` > `"active"`. Agent can autocomplete and verify.

### Error messages

25. **Actionable error messages.** `"product not found: id=%s"` > `"not found"`. Agents (and humans) need context for debugging.

---

## 7. Agent-Friendly Git Practices

26. **Small PRs.** Agent-generated PRs should be < 400 lines. Configure your workflow to encourage this.
27. **Clear commit messages.** Conventional Commits. The agent uses history to understand intent.
28. **Branch protection.** CI must pass before merge. The agent can't accidentally push broken code.

---

## 8. Project-Level Agent Configuration

```
project/
├── CLAUDE.md                    # memory
├── .claude/
│   ├── settings.json            # permissions, hooks
│   └── commands/
│       ├── pre-pr.md            # /pre-pr slash command
│       └── test-coverage.md     # /test-coverage
├── .golangci.yml                # linter config
├── Makefile                     # standard commands
└── ...
```

29. **Slash commands for common workflows.** `/pre-pr` runs lint + test + build. Agent doesn't have to remember.
30. **Hooks for auto-formatting.** Post-edit hook runs `gofmt`. Agent's output is always formatted.

See [`claude-code-customization`](../claude-code-customization/SKILL.md).

---

## Anti-Patterns

| Anti-pattern | Why bad for agents | Fix |
|--------------|-------------------|-----|
| No CLAUDE.md | Agent doesn't know conventions | Write one |
| 2000-line files | Context overflow | Split files |
| No tests | Agent can't verify work | Write tests first |
| Slow test suite (5+ min) | Agent productivity drops | Optimize or split fast/slow |
| Undocumented setup steps | Agent can't run locally | Document in README |
| Inconsistent structure across modules | Agent can't generalize | Standardize |
| Magic strings everywhere | Type confusion | Use typed constants |
| No linter | Agent's code may have issues | Add golangci-lint config |
| Stale CLAUDE.md | Agent follows outdated rules | Update when conventions change |

---

## Checklist

- [ ] CLAUDE.md exists and is < 500 lines
- [ ] Build/test/lint commands documented and work with one command
- [ ] Tests run < 30s and are deterministic
- [ ] File sizes mostly < 300 lines
- [ ] One concept per file, predictable locations
- [ ] Naming is descriptive (no abbreviations, boolean questions)
- [ ] Linter config committed; hooks auto-format
- [ ] Typed constants over magic strings
- [ ] Slash commands for common workflows
- [ ] CLAUDE.md references shared skills/rules, not duplicates

---

## Related Skills

- [`claude-code-customization`](../claude-code-customization/SKILL.md) — configure Claude Code for the repo
- [`skill-authoring`](../skill-authoring/SKILL.md) — skills the agent loads on demand
- [`clean-ddd-go`](../../engineering/clean-ddd-go/SKILL.md) — architecture agents navigate easily
- [`go-testing`](../../engineering/go-testing/SKILL.md) — tests agents run to verify work
