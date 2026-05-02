# Agent Skills

A curated collection of reusable **agent skills** — each folder is a self-contained capability package that AI coding agents (Claude Code, GitHub Copilot, etc.) can load to gain domain expertise in a specific area.

Every skill lives in its own directory and exposes a `SKILL.md` entry point with YAML frontmatter (`name`, `description`, `category`, `tags`). Agents (and humans) can browse this README to discover skills, then load the relevant `SKILL.md` on demand.

---

## Skill Index

### Engineering

Skills that help design, build, or audit software.

| Skill | Description | Tags |
|-------|-------------|------|
| [`clean-ddd-go`](./clean-ddd-go/SKILL.md) | Clean Architecture + DDD patterns for Go projects — layers, bounded contexts, aggregates, repositories. | `go` `architecture` `ddd` |
| [`ddd-check`](./ddd-check/SKILL.md) | Automated auditor that scans a Go project for Clean Architecture / DDD violations and produces a report. | `go` `audit` `lint` |
| [`copilot-sdk`](./copilot-sdk/SKILL.md) | Build agents and apps with the GitHub Copilot SDK (TypeScript, Python, Go, .NET), including MCP and custom tools. | `sdk` `ai-agent` `mcp` |
| [`go-testing`](./go-testing/SKILL.md) | Effective testing in Go — table-driven tests, fakes vs mocks, parallel tests, coverage interpretation. | `go` `testing` `tdd` |
| [`git-workflow`](./git-workflow/SKILL.md) | Day-to-day Git workflow — branching, atomic commits, rebase vs merge, conflict resolution, recovery. | `git` `workflow` |
| [`code-review`](./code-review/SKILL.md) | How to give and receive code review — severity prefixes, what to look for, pushing back productively. | `code-review` `collaboration` |
| [`debugging-methodology`](./debugging-methodology/SKILL.md) | Systematic debugging — reproduce, isolate, hypothesize, verify. Includes Go-specific tooling. | `debugging` `methodology` |
| [`api-design-rest`](./api-design-rest/SKILL.md) | RESTful API design — resource URLs, status codes, error format, pagination, versioning, idempotency. | `api` `rest` `http` |
| [`api-design-grpc`](./api-design-grpc/SKILL.md) | gRPC API design — proto organization, naming, status codes, streaming, backward compatibility. | `api` `grpc` `protobuf` |
| [`refactoring-patterns`](./refactoring-patterns/SKILL.md) | Safe, mechanical refactoring — extract, inline, rename, decompose. Tests-first workflow. | `refactoring` `patterns` |

### Content

Skills for writing, editing, and content strategy.

| Skill | Description | Tags |
|-------|-------------|------|
| [`medium-writing-zh`](./medium-writing-zh/SKILL.md) | 繁體中文 Medium 寫作與經營完整指南 — 排版、SEO、標籤、互動與收益策略。 | `writing` `medium` `zh-tw` |

### Rules

Lightweight rule sheets for coding conventions — quotable in reviews, referenceable from skills, feedable to linters. See [`rules/README.md`](./rules/README.md).

| Rule | Topic |
|------|-------|
| [`rules/go-naming.md`](./rules/go-naming.md) | Go naming conventions — packages, types, functions, receivers, files |
| [`rules/go-error-handling.md`](./rules/go-error-handling.md) | Go error handling — sentinel, wrapping, `errors.Is/As`, panic policy |
| [`rules/commit-messages.md`](./rules/commit-messages.md) | Conventional Commits format for git messages |

---

## Categories

Skills are organized along two axes:

- **`category`** — the primary domain (`engineering`, `content`, `rules`, …). Each skill has exactly one category.
- **`tags`** — free-form labels for cross-cutting attributes (language, framework, purpose). A skill may have many tags.

Current categories:

| Category | Purpose |
|----------|---------|
| `engineering` | Software design, development, auditing, SDK usage. |
| `content` | Writing, editing, publishing, content marketing. |
| `rules` | Lightweight rule sheets — conventions and norms cited by skills. |

Planned categories (to be added as skills are contributed):

- `devops` — CI/CD, deployment, infrastructure-as-code.
- `testing` — test strategy, fixtures, property-based testing.
- `review` — code review, PR review, security review.
- `data` — data modelling, SQL, analytics.

---

## Using a Skill

1. Browse the index above and pick a skill relevant to your task.
2. Open its `SKILL.md` — the frontmatter tells you when to use it and what it covers.
3. If the skill has a `references/` subdirectory, those are deep-dive docs loaded on demand.
4. Related skills are cross-linked via the `related:` frontmatter field.

For AI agents: the top-level `description` and `tags` are designed to be matchable against user intent. Load `SKILL.md` when you detect relevant keywords or tasks.

---

## Adding a New Skill

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full process. Quick version:

1. Copy [`SKILL_TEMPLATE.md`](./SKILL_TEMPLATE.md) into a new folder named after your skill (kebab-case).
2. Fill in the frontmatter (`name`, `description`, `category`, `tags`, optional `related`).
3. Add a row to the relevant category table in this README.
4. Open a PR against `master`.

---

## Repository Layout

```
agent-skills/
├── README.md                  ← you are here
├── CONTRIBUTING.md            ← how to add a new skill
├── SKILL_TEMPLATE.md          ← copy this to start a new skill
├── .github/
│   └── copilot-instructions.md
├── clean-ddd-go/              ← skills: one SKILL.md per folder
│   └── SKILL.md
├── ddd-check/
│   └── SKILL.md
├── copilot-sdk/
│   ├── SKILL.md
│   └── references/            ← deep-dive docs loaded on demand
├── go-testing/
│   └── SKILL.md
├── git-workflow/
│   └── SKILL.md
├── code-review/
│   └── SKILL.md
├── debugging-methodology/
│   └── SKILL.md
├── api-design-rest/
│   └── SKILL.md
├── api-design-grpc/
│   └── SKILL.md
├── refactoring-patterns/
│   └── SKILL.md
├── medium-writing-zh/
│   └── SKILL.md
└── rules/                     ← rules: lightweight, quotable conventions
    ├── README.md
    ├── go-naming.md
    ├── go-error-handling.md
    └── commit-messages.md
```
