# Rules

Lightweight, quotable rule sheets for coding conventions. Unlike **skills** (which teach how to do something), **rules** state norms compactly so they can be:

- Referenced from skills and checklists
- Quoted in code review comments
- Fed into linters and auditors (like `ddd-check`)
- Read end-to-end in under 2 minutes

Each rule sheet is a single `.md` file. No frontmatter required — rules are meant to be read, not dispatched.

---

## Index

<!-- BEGIN AUTO-GENERATED: rules-index -->
| Rule | Topic |
|------|-------|
| [`agent-anti-patterns.md`](./agent-anti-patterns.md) | 41 numbered anti-patterns across agent architecture, prompts, tools, eval, safety |
| [`api-versioning.md`](./api-versioning.md) | API versioning — when to bump, backward compat, deprecation process |
| [`commit-messages.md`](./commit-messages.md) | Conventional Commits format for git messages |
| [`dockerfile.md`](./dockerfile.md) | Dockerfile — base image, layer ordering, security, multi-stage |
| [`gcp-iam-checklist.md`](./gcp-iam-checklist.md) | GCP IAM — service accounts, Workload Identity, least privilege, secret hygiene |
| [`go-concurrency.md`](./go-concurrency.md) | Go concurrency — goroutine lifecycle, channels, mutexes, context, race prevention |
| [`go-error-handling.md`](./go-error-handling.md) | Go error handling — sentinel, wrapping, `errors.Is/As`, panic policy |
| [`go-logging.md`](./go-logging.md) | Go logging — slog, levels, what to log / not to log, correlation IDs |
| [`go-naming.md`](./go-naming.md) | Go naming conventions — packages, types, functions, receivers |
| [`java-naming.md`](./java-naming.md) | Java naming conventions — packages, classes, methods, Spring Boot specifics |
| [`prompt-style.md`](./prompt-style.md) | Prompt writing — structure, instructions, examples, output format, refusals |
| [`rag-checklist.md`](./rag-checklist.md) | RAG production checklist — corpus, chunking, embedding, retrieval, generation, ops, eval |
| [`security-checklist.md`](./security-checklist.md) | Security checklist — OWASP Top 10 condensed for code review |
| [`spring-boot-checklist.md`](./spring-boot-checklist.md) | Spring Boot production checklist — wiring, persistence, security, observability |
| [`tool-schema.md`](./tool-schema.md) | Tool schemas — naming, descriptions, parameters, errors, side effects |
| [`trading-discipline.md`](./trading-discipline.md) | Trading discipline — position sizing, stops, psychological control, holdings management |
<!-- END AUTO-GENERATED: rules-index -->

---

## Adding a Rule

1. Create `rules/<topic>.md`.
2. Start with a 1-2 sentence intro: what this rule set covers, who it applies to.
3. Number rules so they can be cited (e.g. "violates rule 4 of `go-naming`").
4. For each rule: a one-line statement, then a brief ❌ / ✅ example if not self-evident.
5. Add a row to the index above.

Keep it tight. If a rule needs multiple paragraphs of explanation, it probably belongs in a skill instead.
