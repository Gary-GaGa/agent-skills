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

### Content

Skills for writing, editing, and content strategy.

| Skill | Description | Tags |
|-------|-------------|------|
| [`medium-writing-zh`](./medium-writing-zh/SKILL.md) | 繁體中文 Medium 寫作與經營完整指南 — 排版、SEO、標籤、互動與收益策略。 | `writing` `medium` `zh-tw` |

---

## Categories

Skills are organized along two axes:

- **`category`** — the primary domain (`engineering`, `content`, …). Each skill has exactly one category.
- **`tags`** — free-form labels for cross-cutting attributes (language, framework, purpose). A skill may have many tags.

Current categories:

| Category | Purpose |
|----------|---------|
| `engineering` | Software design, development, auditing, SDK usage. |
| `content` | Writing, editing, publishing, content marketing. |

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
├── clean-ddd-go/
│   └── SKILL.md
├── ddd-check/
│   └── SKILL.md
├── copilot-sdk/
│   ├── SKILL.md
│   └── references/            ← deep-dive docs loaded on demand
└── medium-writing-zh/
    └── SKILL.md
```
