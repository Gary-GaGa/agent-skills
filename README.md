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
| [`go-concurrency`](./go-concurrency/SKILL.md) | Go concurrency — goroutines, channels, sync, errgroup, context cancellation, race prevention. | `go` `concurrency` |
| [`go-performance`](./go-performance/SKILL.md) | Go performance — benchmarking, pprof, allocation reduction, escape analysis, GC tuning. | `go` `performance` `profiling` |
| [`observability-go`](./observability-go/SKILL.md) | Go observability — slog, OpenTelemetry tracing, Prometheus metrics, correlation IDs. | `go` `observability` `tracing` |
| [`event-driven-architecture`](./event-driven-architecture/SKILL.md) | Event-driven patterns — message queues, event sourcing, CQRS, saga, idempotent consumers. | `architecture` `events` `cqrs` |
| [`microservices-patterns`](./microservices-patterns/SKILL.md) | Microservices — decomposition, circuit breaker, API gateway, 12-factor, when to stay monolithic. | `architecture` `microservices` |

### AI Engineering

Skills for designing, building, and operating LLM-powered agents and applications.

| Skill | Description | Tags |
|-------|-------------|------|
| [`agent-harness-design`](./agent-harness-design/SKILL.md) | Designing the harness around an LLM — agent loop, single vs multi-agent, autonomy levels, failure modes. | `agent` `harness` `architecture` |
| [`prompt-engineering`](./prompt-engineering/SKILL.md) | System prompt structure, instruction patterns, few-shot, chain-of-thought, output formatting, cross-model differences. | `prompt` `llm` `claude` `gpt` |
| [`context-engineering`](./context-engineering/SKILL.md) | Managing what the model sees per turn — context budget, compaction, retrieval, pinning, tool result compression. | `context` `rag` `memory` |
| [`tool-design-for-agents`](./tool-design-for-agents/SKILL.md) | Designing tools agents use well — naming, descriptions, schemas, errors, idempotency, granularity. | `tool` `agent` `json-schema` |
| [`skill-authoring`](./skill-authoring/SKILL.md) | Meta-skill for writing good SKILL.md files — frontmatter, scope, references, agent-friendly structure. | `skill` `meta` `documentation` |
| [`mcp-server-design`](./mcp-server-design/SKILL.md) | Designing Model Context Protocol servers — tools/resources/prompts, transport, security, versioning. | `mcp` `server` `protocol` |
| [`agent-evaluation`](./agent-evaluation/SKILL.md) | Building eval harnesses — golden tests, behavioral assertions, LLM-as-judge, regression detection, CI. | `eval` `testing` `regression` |
| [`agent-observability`](./agent-observability/SKILL.md) | Tracing, logging, monitoring agents — span design, cost telemetry, multi-turn debugging, prod→eval loop. | `observability` `tracing` `monitoring` |
| [`multi-agent-orchestration`](./multi-agent-orchestration/SKILL.md) | Patterns for coordinating multiple agents — supervisor/worker, planner/executor, debate, handoff design. | `multi-agent` `orchestration` |
| [`agent-safety-guardrails`](./agent-safety-guardrails/SKILL.md) | Safety patterns — input validation, prompt injection defense, tool scoping, refusals, audit logging. | `safety` `security` `guardrails` |
| [`claude-code-customization`](./claude-code-customization/SKILL.md) | Customizing Claude Code — settings.json, hooks, slash commands, sub-agents, MCP servers, plugins. | `claude-code` `customization` |
| [`prompt-caching`](./prompt-caching/SKILL.md) | Optimizing cost and latency with prompt caching — breakpoint placement, hit rate, cache-aware design. | `caching` `performance` `cost` |
| [`rag-deep-dive`](./rag-deep-dive/SKILL.md) | RAG pipeline — chunking, embedding, vector DB, hybrid search, reranking, evaluation. | `rag` `retrieval` `vector-db` |
| [`agentic-coding-patterns`](./agentic-coding-patterns/SKILL.md) | Writing code agents work well with — CLAUDE.md, test-friendly arch, modular structure. | `agent` `coding` `developer-experience` |
| [`llm-cost-optimization`](./llm-cost-optimization/SKILL.md) | LLM cost control — model routing, caching, context reduction, batching, cost budgets. | `cost` `optimization` `tokens` |
| [`fine-tuning-guide`](./fine-tuning-guide/SKILL.md) | When and how to fine-tune — decision flowchart, data prep, training, eval, deployment. | `fine-tuning` `training` `model` |

### DevOps

Skills for deployment, CI/CD, and infrastructure.

| Skill | Description | Tags |
|-------|-------------|------|
| [`docker-basics`](./docker-basics/SKILL.md) | Docker best practices — Dockerfile, multi-stage builds, image optimization, compose, security. | `docker` `container` `devops` |
| [`github-actions`](./github-actions/SKILL.md) | GitHub Actions CI/CD — workflows, caching, matrix, secrets, reusable workflows. | `ci-cd` `github-actions` `automation` |
| [`terraform-basics`](./terraform-basics/SKILL.md) | Terraform fundamentals — HCL, state, modules, plan/apply safety, remote backend. | `terraform` `iac` `infrastructure` |
| [`k8s-fundamentals`](./k8s-fundamentals/SKILL.md) | Kubernetes for developers — pods, deployments, services, health checks, resource limits, debugging. | `kubernetes` `k8s` `deployment` |

### Data

Skills for database design, queries, and data management.

| Skill | Description | Tags |
|-------|-------------|------|
| [`sql-fundamentals`](./sql-fundamentals/SKILL.md) | SQL for developers — schema design, indexing, query optimization, N+1, transactions. | `sql` `database` `postgresql` |
| [`database-migrations`](./database-migrations/SKILL.md) | Database migration best practices — expand-contract, safe ops, backfill batching, tooling. | `migration` `schema` `database` |
| [`data-modeling`](./data-modeling/SKILL.md) | Data modeling — ER design, normalization, patterns (polymorphism, hierarchy, audit), DDD mapping. | `data-modeling` `schema` `er-diagram` |

### Content

Skills for writing, editing, and content strategy.

| Skill | Description | Tags |
|-------|-------------|------|
| [`medium-writing-zh`](./medium-writing-zh/SKILL.md) | 繁體中文 Medium 寫作與經營完整指南 — 排版、SEO、標籤、互動與收益策略。 | `writing` `medium` `zh-tw` |
| [`technical-writing-en`](./technical-writing-en/SKILL.md) | English technical writing — READMEs, API docs, ADRs, changelogs, writing style. | `writing` `documentation` `english` |
| [`newsletter-writing-zh`](./newsletter-writing-zh/SKILL.md) | 繁體中文電子報經營 — 平台選擇、成長策略、寫作技巧、指標追蹤。 | `writing` `newsletter` `zh-tw` |

### Finance

Skills for personal investing and market analysis (currently Taiwan stock market focused).

| Skill | Description | Tags |
|-------|-------------|------|
| [`tw-stock-fundamental`](./tw-stock-fundamental/SKILL.md) | 台股基本面分析 — 財報判讀、財務比率、選股框架（殖利率/成長/價值）、財報陷阱辨識。 | `tw-stock` `fundamental-analysis` `investing` |
| [`tw-stock-chip`](./tw-stock-chip/SKILL.md) | 台股籌碼面分析 — 三大法人、融資融券、集保大戶、主力分點，搭配基本面判斷進場時機。 | `tw-stock` `chip-analysis` `investing` |
| [`tw-stock-technical`](./tw-stock-technical/SKILL.md) | 台股技術分析 — K 線、均線、MACD、RSI、KD、布林通道、量價關係、支撐壓力。 | `tw-stock` `technical-analysis` `charting` |
| [`tw-stock-quant`](./tw-stock-quant/SKILL.md) | 台股量化策略 — 回測框架、因子模型、績效評估、過擬合防範、策略開發流程。 | `tw-stock` `quantitative` `backtesting` |
| [`tw-stock-data`](./tw-stock-data/SKILL.md) | 台股資料工程 — 資料源、欄位規格、除權息還原、point-in-time、儲存方案、自動化排程。 | `tw-stock` `data-engineering` `pipeline` |
| [`tw-stock-options`](./tw-stock-options/SKILL.md) | 台股選擇權基礎 — 買賣權、Greeks、常見策略、台指選擇權合約、風險管理。 | `tw-stock` `options` `derivatives` |
| [`tw-etf-investing`](./tw-etf-investing/SKILL.md) | 台股 ETF 投資 — 主流 ETF 比較、定期定額、核心衛星配置、內扣費用。 | `tw-stock` `etf` `passive-investing` |
| [`portfolio-construction`](./portfolio-construction/SKILL.md) | 投資組合建構 — 資產配置、風險分散、再平衡、position sizing、績效追蹤。 | `portfolio` `asset-allocation` `risk` |
| [`tw-stock-tax`](./tw-stock-tax/SKILL.md) | 台股稅務 — 證交稅、股利所得稅、二代健保、資本利得免稅、節稅策略。 | `tw-stock` `tax` `investing` |

### Productivity

Skills for learning, knowledge management, and personal effectiveness.

| Skill | Description | Tags |
|-------|-------------|------|
| [`learning-methodology`](./learning-methodology/SKILL.md) | 學習方法論 — 費曼技巧、間隔重複、刻意練習、技術學習五步法。 | `learning` `methodology` `productivity` |
| [`second-brain`](./second-brain/SKILL.md) | 第二大腦 — PARA + Zettelkasten、Obsidian、筆記類型、連結策略、回顧系統。 | `pkm` `note-taking` `obsidian` |
| [`time-management`](./time-management/SKILL.md) | 時間管理 — Eisenhower、深度工作、時間盒、能量管理、每日每週回顧。 | `time-management` `deep-work` `focus` |

### Rules

Lightweight rule sheets for coding conventions — quotable in reviews, referenceable from skills, feedable to linters. See [`rules/README.md`](./rules/README.md).

| Rule | Topic |
|------|-------|
| [`rules/go-naming.md`](./rules/go-naming.md) | Go naming conventions — packages, types, functions, receivers, files |
| [`rules/go-error-handling.md`](./rules/go-error-handling.md) | Go error handling — sentinel, wrapping, `errors.Is/As`, panic policy |
| [`rules/commit-messages.md`](./rules/commit-messages.md) | Conventional Commits format for git messages |
| [`rules/trading-discipline.md`](./rules/trading-discipline.md) | 交易紀律 — 資金管理、停損停利、心理控制、持股管理（35 條規則） |
| [`rules/prompt-style.md`](./rules/prompt-style.md) | Prompt writing rules — structure, instructions, examples, output format, refusals |
| [`rules/tool-schema.md`](./rules/tool-schema.md) | Tool schema rules — naming, descriptions, parameters, errors, side effects |
| [`rules/agent-anti-patterns.md`](./rules/agent-anti-patterns.md) | 41 numbered agent design / prompt / tool / eval / safety anti-patterns |
| [`rules/go-concurrency.md`](./rules/go-concurrency.md) | Go concurrency rules — goroutine lifecycle, channels, mutexes, context, race prevention |
| [`rules/go-logging.md`](./rules/go-logging.md) | Go logging rules — slog, levels, what to log, what not to log, correlation IDs |
| [`rules/api-versioning.md`](./rules/api-versioning.md) | API versioning rules — when to bump, backward compat, deprecation process |
| [`rules/security-checklist.md`](./rules/security-checklist.md) | Security checklist — OWASP Top 10 condensed, injection, auth, secrets, headers |
| [`rules/dockerfile.md`](./rules/dockerfile.md) | Dockerfile rules — base image, layer ordering, security, multi-stage, compose |

---

## Categories

Skills are organized along two axes:

- **`category`** — the primary domain (`engineering`, `content`, `rules`, …). Each skill has exactly one category.
- **`tags`** — free-form labels for cross-cutting attributes (language, framework, purpose). A skill may have many tags.

Current categories:

| Category | Purpose |
|----------|---------|
| `engineering` | Software design, development, auditing, architecture patterns. |
| `ai-engineering` | LLM agents, prompts, context, tools, evals, observability, safety. |
| `devops` | CI/CD, containers, infrastructure-as-code, orchestration. |
| `data` | Database design, SQL, migrations, data modeling. |
| `content` | Writing, editing, publishing, content marketing. |
| `finance` | Personal investing, market analysis, trading discipline. |
| `productivity` | Learning, knowledge management, time management. |
| `rules` | Lightweight rule sheets — conventions and norms cited by skills. |

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
├── agent-harness-design/
│   └── SKILL.md
├── prompt-engineering/
│   └── SKILL.md
├── context-engineering/
│   └── SKILL.md
├── tool-design-for-agents/
│   └── SKILL.md
├── skill-authoring/
│   └── SKILL.md
├── mcp-server-design/
│   └── SKILL.md
├── agent-evaluation/
│   └── SKILL.md
├── agent-observability/
│   └── SKILL.md
├── multi-agent-orchestration/
│   └── SKILL.md
├── agent-safety-guardrails/
│   └── SKILL.md
├── claude-code-customization/
│   └── SKILL.md
├── prompt-caching/
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
    ├── trading-discipline.md
    ├── prompt-style.md
    ├── tool-schema.md
    └── agent-anti-patterns.md
```
