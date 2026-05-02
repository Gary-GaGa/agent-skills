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

### Finance

Skills for personal investing and market analysis (currently Taiwan stock market focused).

| Skill | Description | Tags |
|-------|-------------|------|
| [`tw-stock-fundamental`](./tw-stock-fundamental/SKILL.md) | 台股基本面分析 — 財報判讀、財務比率、選股框架（殖利率/成長/價值）、財報陷阱辨識。 | `tw-stock` `fundamental-analysis` `investing` |
| [`tw-stock-chip`](./tw-stock-chip/SKILL.md) | 台股籌碼面分析 — 三大法人、融資融券、集保大戶、主力分點，搭配基本面判斷進場時機。 | `tw-stock` `chip-analysis` `investing` |
| [`tw-stock-technical`](./tw-stock-technical/SKILL.md) | 台股技術分析 — K 線、均線、MACD、RSI、KD、布林通道、量價關係、支撐壓力。 | `tw-stock` `technical-analysis` `charting` |
| [`tw-stock-quant`](./tw-stock-quant/SKILL.md) | 台股量化策略 — 回測框架、因子模型、績效評估、過擬合防範、策略開發流程。 | `tw-stock` `quantitative` `backtesting` |
| [`tw-stock-data`](./tw-stock-data/SKILL.md) | 台股資料工程 — 資料源、欄位規格、除權息還原、point-in-time、儲存方案、自動化排程。 | `tw-stock` `data-engineering` `pipeline` |

### Rules

Lightweight rule sheets for coding conventions — quotable in reviews, referenceable from skills, feedable to linters. See [`rules/README.md`](./rules/README.md).

| Rule | Topic |
|------|-------|
| [`rules/go-naming.md`](./rules/go-naming.md) | Go naming conventions — packages, types, functions, receivers, files |
| [`rules/go-error-handling.md`](./rules/go-error-handling.md) | Go error handling — sentinel, wrapping, `errors.Is/As`, panic policy |
| [`rules/commit-messages.md`](./rules/commit-messages.md) | Conventional Commits format for git messages |
| [`rules/trading-discipline.md`](./rules/trading-discipline.md) | 交易紀律 — 資金管理、停損停利、心理控制、持股管理（35 條規則） |

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
| `finance` | Personal investing, market analysis, trading discipline. |
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
├── tw-stock-fundamental/
│   └── SKILL.md
├── tw-stock-chip/
│   └── SKILL.md
├── tw-stock-technical/
│   └── SKILL.md
├── tw-stock-quant/
│   └── SKILL.md
├── tw-stock-data/
│   └── SKILL.md
└── rules/                     ← rules: lightweight, quotable conventions
    ├── README.md
    ├── go-naming.md
    ├── go-error-handling.md
    ├── commit-messages.md
    └── trading-discipline.md
```
