# Agent Skills

<!-- BEGIN AUTO-GENERATED: summary -->
A curated collection of **79 skills** and **16 rule sheets** across **7 categories**. Each skill is a self-contained capability package that AI coding agents (Claude Code, GitHub Copilot, etc.) can load to gain domain expertise.
<!-- END AUTO-GENERATED: summary -->

---

## How to Navigate

```
README.md (you are here)
  → pick a category below
    → read <category>/INDEX.md for the skill list
      → load <category>/<skill>/SKILL.md for the full skill
```

**For AI agents:** Read this file to identify the category, then load the category's `INDEX.md`, then load the specific `SKILL.md`. This 3-hop approach avoids loading all 59 skills into context.

---

## Categories

<!-- BEGIN AUTO-GENERATED: categories -->
| Category | Skills | Description | Index |
|----------|--------|-------------|-------|
| **[engineering](./engineering/INDEX.md)** | 31 | Software design, Go, APIs, frontend, databases, architecture, integrations. | [→ INDEX](./engineering/INDEX.md) |
| **[ai-engineering](./ai-engineering/INDEX.md)** | 21 | LLM agents, prompts, context, tools, eval, observability, safety, caching. | [→ INDEX](./ai-engineering/INDEX.md) |
| **[devops](./devops/INDEX.md)** | 8 | Docker, GitHub Actions, Terraform, Kubernetes. | [→ INDEX](./devops/INDEX.md) |
| **[data](./data/INDEX.md)** | 3 | SQL, database migrations, data modeling. | [→ INDEX](./data/INDEX.md) |
| **[content](./content/INDEX.md)** | 3 | Medium writing, technical docs, newsletters. | [→ INDEX](./content/INDEX.md) |
| **[finance](./finance/INDEX.md)** | 10 | Taiwan stock analysis, ETF, options, portfolio, tax. | [→ INDEX](./finance/INDEX.md) |
| **[productivity](./productivity/INDEX.md)** | 3 | Learning methodology, second brain, time management. | [→ INDEX](./productivity/INDEX.md) |
| **[rules](./rules/README.md)** | 16 | Lightweight, quotable convention sheets (Go, security, Docker, prompts, etc.). | [→ README](./rules/README.md) |
<!-- END AUTO-GENERATED: categories -->

---

## Repository Layout

```
agent-skills/
├── README.md                 ← you are here (routing file)
├── CONTRIBUTING.md           ← how to add a new skill or rule
├── SKILL_TEMPLATE.md         ← boilerplate for new skills
├── skills.json               ← machine-readable manifest (auto-generated)
├── tags-allowlist.txt        ← curated tag taxonomy (validate warns on unlisted tags)
├── scripts/
│   ├── build_manifest.py     ← regenerates skills.json
│   ├── render_docs.py        ← regenerates README/INDEX/copilot-instructions
│   ├── fix_related.py        ← auto-completes bidirectional related: refs
│   ├── validate.py           ← schema/drift/cross-link checks (runs in CI)
│   └── run_routing_eval.py   ← lexical eval of routing quality
├── evals/
│   ├── README.md             ← eval format and methodology
│   └── skill-routing.jsonl   ← test cases (intent → expected skill)
├── .github/
│   ├── copilot-instructions.md
│   └── workflows/validate.yml
│
├── engineering/              ← category folder
│   ├── INDEX.md              ← lists all skills in this category
│   ├── clean-ddd-go/SKILL.md
│   ├── go-testing/SKILL.md
│   └── ...                   (21 skills)
│
├── ai-engineering/
│   ├── INDEX.md
│   ├── agent-harness-design/SKILL.md
│   └── ...                   (16 skills)
│
├── devops/                   (4 skills)
├── data/                     (3 skills)
├── content/                  (3 skills)
├── finance/                  (9 skills)
├── productivity/             (3 skills)
│
└── rules/                    ← 12 rule sheets (flat .md files)
    ├── README.md
    ├── go-naming.md
    ├── security-checklist.md
    └── ...
```

> Sections wrapped in `<!-- BEGIN AUTO-GENERATED: ... -->` markers in this README,
> the per-category `INDEX.md`, `rules/README.md`, and
> `.github/copilot-instructions.md` are regenerated from `skills.json` by
> `scripts/render_docs.py`. Edit the source `SKILL.md` frontmatter, then run
> `python3 scripts/build_manifest.py && python3 scripts/render_docs.py`.

---

## Adding a New Skill

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the full process. Quick version:

1. Copy [`SKILL_TEMPLATE.md`](./SKILL_TEMPLATE.md) into `<category>/<your-skill>/SKILL.md`.
2. Fill in the frontmatter (`name`, `description`, `category`, `tags`, optional `related`).
3. Run `python3 scripts/build_manifest.py && python3 scripts/render_docs.py` (regenerates `skills.json`, INDEX, README, copilot-instructions).
4. Run `python3 scripts/fix_related.py` if you added `related:` entries.
5. Run `python3 scripts/validate.py` and open a PR against `master`.
