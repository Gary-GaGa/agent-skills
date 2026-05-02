# Rules

Lightweight, quotable rule sheets for coding conventions. Unlike **skills** (which teach how to do something), **rules** state norms compactly so they can be:

- Referenced from skills and checklists
- Quoted in code review comments
- Fed into linters and auditors (like `ddd-check`)
- Read end-to-end in under 2 minutes

Each rule sheet is a single `.md` file. No frontmatter required — rules are meant to be read, not dispatched.

---

## Index

| Rule | Topic |
|------|-------|
| [`go-naming.md`](./go-naming.md) | Go naming conventions — packages, types, functions, receivers |
| [`go-error-handling.md`](./go-error-handling.md) | Go error handling — sentinel, wrapping, `errors.Is/As`, panic policy |
| [`commit-messages.md`](./commit-messages.md) | Conventional Commits format for git messages |
| [`trading-discipline.md`](./trading-discipline.md) | 交易紀律 — 資金管理、停損停利、心理控制、持股管理 |

---

## Adding a Rule

1. Create `rules/<topic>.md`.
2. Start with a 1-2 sentence intro: what this rule set covers, who it applies to.
3. Number rules so they can be cited (e.g. "violates rule 4 of `go-naming`").
4. For each rule: a one-line statement, then a brief ❌ / ✅ example if not self-evident.
5. Add a row to the index above.

Keep it tight. If a rule needs multiple paragraphs of explanation, it probably belongs in a skill instead.
