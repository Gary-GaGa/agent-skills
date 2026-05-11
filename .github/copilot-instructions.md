# Copilot instructions (repository-level)

Purpose: Short, focused guidance for Copilot agents and CLI sessions working in this repository: how to build/test/lint (when code is present), the high-level architecture, and repo-specific conventions to follow.

---

## Quick repository snapshot

This repo is a collection of reusable **agent skills**, organized into **category folders**. Each category has an `INDEX.md` listing its skills; each skill has a `SKILL.md` entry point with YAML frontmatter.

**Structure:** `<category>/<skill>/SKILL.md` (e.g. `engineering/go-testing/SKILL.md`).

**Navigation:** `README.md` → `<category>/INDEX.md` → `<category>/<skill>/SKILL.md`.

<!-- BEGIN AUTO-GENERATED: skill-list -->
Current skills — 79 total across 7 categories:

**engineering (31):** api-design-grpc, api-design-rest, auth-patterns, clean-ddd-go, code-review, copilot-sdk, ddd-check, debugging-methodology, event-driven-architecture, gcp-cloud-sql-spring, gcp-firestore-spring, gcp-observability-spring, gcp-pubsub-spring, git-workflow, go-concurrency, go-performance, go-testing, java-restful-api, line-integration-tw, microservices-patterns, mongodb-go, nextjs-fundamentals, observability-go, openapi-swagger-spring, realtime-websocket, refactoring-patterns, spring-ai-rag, spring-boot-fundamentals, spring-boot-testing, spring-data-jpa, tw-payment-integration

**ai-engineering (21):** agent-evaluation, agent-harness-design, agent-observability, agent-safety-guardrails, agentic-coding-patterns, agentic-rag, claude-code-customization, context-engineering, fine-tuning-guide, graphrag-multi-service, llm-cost-optimization, mcp-server-design, multi-agent-orchestration, prompt-caching, prompt-engineering, query-rewriting-rag, rag-deep-dive, rag-for-code, rag-ingestion-pipeline, skill-authoring, tool-design-for-agents

**devops (8):** cloud-build-artifact-registry, docker-basics, gcp-fundamentals, gcp-vertex-ai-rag, github-actions, gke-deployment, k8s-fundamentals, terraform-basics

**data (3):** data-modeling, database-migrations, sql-fundamentals

**content (3):** medium-writing, newsletter-writing, technical-writing

**finance (10):** portfolio-construction, tw-etf-investing, tw-stock-chip, tw-stock-data, tw-stock-fundamental, tw-stock-options, tw-stock-quant, tw-stock-tax, tw-stock-technical, tw-stock-trend

**productivity (3):** learning-methodology, second-brain, time-management

Rule sheets (16) in `rules/`: agent-anti-patterns, api-versioning, commit-messages, dockerfile, gcp-iam-checklist, go-concurrency, go-error-handling, go-logging, go-naming, java-naming, prompt-style, rag-checklist, security-checklist, spring-boot-checklist, tool-schema, trading-discipline
<!-- END AUTO-GENERATED: skill-list -->

Repo-level files:
- `README.md` — skill index organized by category
- `CONTRIBUTING.md` — how to add a new skill or rule
- `SKILL_TEMPLATE.md` — template/boilerplate for new skills
- `rules/README.md` — index of rule sheets

There are no repository-wide build scripts at the root (no `go.mod`, `package.json`, or `pyproject.toml`); the folders are documentation/examples.

---

## Build, test, and lint commands

Notes: no project-level CI scripts were found; below are the exact commands to run when you add or operate on language-specific code in these folders.

Go (applies to `clean-ddd-go` or any Go code added here)
- Build all packages: `go build ./...`
- Run full test suite: `go test ./...`
- Run a single package's tests: `go test ./internal/domain/catalog -v`
- Run a single test function in a package: `go test ./internal/domain/catalog -run TestProduct_Sell -v`
- Run a single test across packages: `go test ./... -run TestProduct_Sell -v`
- Format: `gofmt -w .` or `go fmt ./...`
- Vet: `go vet ./...`
- Lint (if configured): `golangci-lint run` (only if `golangci-lint` is installed and config exists)

Node / TypeScript (if/when present)
- Install: `npm install`
- Run tests: `npm test`
- Run a single test (Jest example): `npm test -- -t "TestName"` or `npx jest path/to/file -t "TestName"`

Python (if/when present)
- Install deps: `pip install -r requirements.txt` or use venv
- Run full test suite: `pytest`
- Run a single test: `pytest path/to/test_file.py::test_name -q`

Use these exact commands in Copilot-run steps when asked to run or edit tests; prefer package-level `go test` with `-run` for single tests in Go.

---

## High-level architecture (clean-ddd-go exemplar)

This repository contains a Clean Architecture + Domain-Driven Design exemplar in `clean-ddd-go`. Use this as the authoritative architecture guide.

Layers (dependencies point inward):
- Domain (core business rules) — pure Go, no external packages
- Usecase (application business rules / orchestrators)
- Interface (adapters): `in/` (HTTP/CLI/gRPC handlers) and `out/` (repository implementations)
- Infrastructure (DB clients, logging, shared setup)

Directory mapping used by the exemplar:
```
cmd/
internal/
  domain/<context>/        # entities, value objects, repository interfaces
  usecase/                 # ports (in/), dto/, service implementations
  interface/in/            # input adapters (HTTP, CLI, gRPC)
  interface/out/persistence/<db>/<context>/po/  # PO + converters
  infrastructure/          # DB client creation, logging, config
```

Key architectural rules (explicit, authoritative for this project):
- Domain packages must have zero external dependencies.
- Repository interfaces (output ports) live in `internal/domain`.
- Usecases accept `context.Context` as the first parameter and exchange DTOs (never return domain entities directly).
- Adapters implement domain repository interfaces and convert between Domain ↔ PO (persistence objects).
- Packages are organized by bounded context (e.g., `catalog/`, `personnel/`), not by technical role.

---

## Key conventions (patterns to preserve)

Domain & Usecase
- Value objects are immutable; domain methods return new instances instead of mutating values in-place.
- Aggregate Root per bounded context controls child entities.
- Guard clauses and domain-level validation belong inside domain methods.
- Service constructors use constructor injection: `NewService(repo domain.Repository)`.
- All repository/usecase methods take `context.Context` as the first parameter.

Adapters & Persistence
- Persistence Objects (POs) live alongside adapter implementations under `internal/interface/out/persistence/.../po/` and include bidirectional converters.
- Each adapter package implements a single interface — keep handler logic separate from persistence logic.

Errors & Tests
- Use sentinel domain errors (e.g., `ErrProductNotFound`) defined in service packages and wrap infra errors with `%w`.
- Domain tests should be plain Go unit tests (no external resources). Use mocks for repository interfaces in usecase tests. Integration tests exercise adapters against real infra.

Naming & DTOs
- Use `internal/usecase/dto` for DTOs exchanged across the usecase boundary.
- Do not expose domain entities to outer layers; map to DTOs at the usecase boundary.

Copilot SDK / Agent-specific conventions (from `copilot-sdk`):
- Register session event handlers before calling `send()`; otherwise streaming events may be missed.
- Event access patterns (important when writing code that inspects events):
  - TypeScript: `event.type` (string), `event.data.content`, `event.data.deltaContent`
  - Python: `event.type.value` (enum -> use `.value`), `event.data.content` / `event.data.delta_content`
  - Go: `event.Type` (string); `event.Data.Content` and `event.Data.DeltaContent` are pointers — always check for `nil` before dereferencing
  - .NET: pattern-match on event classes and use `evt.Data.Content` / `DeltaContent`
- Streaming behavior: `streaming: true` produces `assistant.message_delta` events (use `deltaContent`) and a final `assistant.message` with full content; rely on `session.idle` or `sendAndWait()` to know completion.
- Custom agents (repo-level) belong in `.github/agents/` and must include YAML frontmatter with at least `description` and (recommended) an explicit `tools` list.

---

## Files and locations to consult

- `README.md` — routing file; lists categories with links to each `INDEX.md`.
- `<category>/INDEX.md` — lists all skills in that category with one-line descriptions.
- `<category>/<skill>/SKILL.md` — the full skill content.
- `rules/*.md` — lightweight rule sheets (12 total); cite by filename in reviews and feedback.
- `CONTRIBUTING.md` / `SKILL_TEMPLATE.md` — process and boilerplate for adding new skills or rules.
- `engineering/copilot-sdk/references/` — deep-dive docs for the Copilot SDK.

---

## Other assistant configs

No repository-level Claude/OpenCode, Cursor, Jules/AGENTS, Windsurf, Aider, or Cline config files were found; if added, add a short summary here so Copilot knows to merge their guidance.

---

## How to use this file during Copilot sessions

- Use this file as the primary source of repository-specific rules when reasoning about edits or running tests.
- If asked to add features or fix bugs in `clean-ddd-go`, prefer domain/usecase-first changes and the rules above (no external domain deps, DTO boundaries, constructor injection).
- When asked to modify or run Copilot SDK examples, follow the event-access patterns and the handler-before-send rule.

---

_Last updated: autogenerated by Copilot CLI session_
