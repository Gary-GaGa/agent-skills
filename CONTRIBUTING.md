# Contributing a Skill

Thanks for contributing! This repo collects reusable **agent skills** — self-contained capability packages that AI coding agents load to gain domain expertise. This guide walks through adding a new skill end-to-end.

---

## 1. Decide if a Skill Is the Right Shape

A good skill is:

- **Focused** — one coherent domain or task type. If it spans two unrelated topics, split it.
- **Reusable** — useful across multiple projects, not tied to one codebase.
- **Actionable** — tells the agent *what to do* or *what to check*, not just trivia.
- **Stable** — the core conventions change slowly enough that the doc stays relevant.

If your idea is really a one-off prompt, a `CLAUDE.md` in the target repo is probably the better home.

---

## 2. Pick a Category

Every skill has exactly one `category`. Current options:

| Category | For |
|----------|-----|
| `engineering` | Software design, development, architecture patterns. |
| `ai-engineering` | LLM agents, prompts, context, tools, evals, observability, safety. |
| `devops` | CI/CD, containers, infrastructure-as-code, orchestration. |
| `data` | Database design, SQL, migrations, data modeling. |
| `content` | Writing, editing, publishing, content marketing. |
| `finance` | Personal investing, market analysis, trading discipline. |
| `productivity` | Learning, knowledge management, time management. |
| `rules` | Lightweight rule sheets (see ["Adding a Rule" below](#adding-a-rule-lightweight-convention-sheet)). |

If your skill doesn't fit, propose a new category in your PR and add it to `README.md`.

---

## 3. Create the Skill Folder

1. Create a kebab-case directory under the appropriate **category folder**: `<category>/your-skill-name/`.
   - If the skill is region- or stack-specific, suffix appropriately: `tw-stock-data` (Taiwan market), `clean-ddd-go` (Go-specific).
2. Copy `SKILL_TEMPLATE.md` into it as `SKILL.md`.
3. Fill in the frontmatter:

   ```yaml
   ---
   name: your-skill-name          # must match folder name
   description: >
     One to three sentences the agent reads to decide whether to load this skill.
   category: engineering
   tags: [go, testing, ...]
   related: [another-skill]       # optional
   ---
   ```

4. Write the body. Follow the template sections — omit any that don't apply.

---

## 4. Add Deep-Dive References (Optional)

If the skill has >~300 lines of detail, move the depth into `your-skill-name/references/*.md` and keep `SKILL.md` as a lean overview that links out. This keeps the skill cheap to load into an agent's context. See `copilot-sdk/` for an example.

---

## 5. Register the Skill

1. Run `python3 scripts/build_manifest.py` then `python3 scripts/render_docs.py` — this regenerates `skills.json`, the relevant `<category>/INDEX.md`, the categories table in `README.md`, and the skill list in `.github/copilot-instructions.md`. Do not edit those auto-generated regions by hand.
2. If you introduced a new category, register it in `scripts/build_manifest.py` (the `CATEGORIES` list) and create the category folder with an `INDEX.md` that contains the marker blocks (see an existing INDEX as reference).
3. If the skill relates to existing skills, add mutual `related:` entries — `python3 scripts/fix_related.py` will append any missing back-references for you.
4. For cross-category links, use `../../<other-category>/<skill>/SKILL.md`. Same-category links use `../<skill>/SKILL.md`.
5. Run `python3 scripts/validate.py` before opening the PR. The same script runs in CI.

---

## 6. Frontmatter Field Reference

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Must match the folder name exactly. Lowercase, kebab-case. |
| `description` | yes | Intent-matchable blurb. Agents decide to load on this. |
| `category` | yes | One of the defined categories. |
| `tags` | yes | Free-form labels: language, framework, purpose. Lowercase, kebab-case. |
| `keywords` | no | Literal phrases for BM25-style exact matching — proper nouns, acronyms, library names, error codes. Preserve case (`MCP`, `PostgreSQL`, `pgvector`). Add what `tags` and `description` don't already capture; not a synonym for `tags`. Max ~20. |
| `related` | no | List of other skill `name`s that pair with this one. |

Unknown fields are rejected by `validate.py` — typos like `keyword` (vs `keywords`) will fail CI rather than silently going unread.

### When to add `keywords`

The agent matches user intent against `description` (semantic) and `tags`
(soft filter). `keywords` is the literal/BM25 layer — use it for terms a
user is likely to type *exactly* but that don't fit naturally in the
description. Examples:

- `mcp-server-design` → `["MCP", "Model Context Protocol", "stdio", "SSE"]`
- `mongodb-go` → `["MongoDB", "mongo-go-driver", "BSON", "ObjectID"]`
- `auth-patterns` → `["JWT", "OAuth2", "OIDC", "RBAC", "PKCE"]`

Skip `keywords` entirely if `description` and `tags` already cover the
search surface — empty is fine.

---

## 7. Style Guide

- **Language.** All skill content is written in English. If a skill targets a non-English market (Taiwan, Japan, etc.), keep proper nouns and product names in their canonical form (`ECPay`, `LINE Notify`, `0050 ETF`).
- **Code blocks.** Annotate with a language tag so syntax highlighting works.
- **Links.** Use relative paths for intra-repo links (`../other-skill/SKILL.md`).
- **No emojis** unless they carry meaning (e.g. severity markers in `ddd-check`).
- **Tags.** Reuse a tag from `tags-allowlist.txt` if one fits. Add a new tag only when an existing one genuinely doesn't apply, and add the new tag to the allowlist in the same PR — `validate.py` warns on unlisted tags so typos (`golang` vs `go`) don't accumulate silently.
- **References quota.** A skill's SKILL.md plus everything in its `references/` should not exceed ~1500 lines combined. If you blow past it, the skill is probably two skills.

---

## 8. Commit & PR

1. Commit on a feature branch (not `master`). Use a descriptive commit subject like `feat: add <skill-name> skill`.
2. Open a PR against `master`. Include in the description:
   - What the skill covers.
   - A concrete example of a user prompt that should trigger it.
   - Any new category or convention you're introducing.

---

## Adding a Rule (Lightweight Convention Sheet)

Rules are a lighter format than skills. Use a **rule** (not a skill) when:

- The content is a **list of norms** (do this, not that) rather than a how-to.
- It's short enough to read end-to-end in under 2 minutes.
- It's meant to be **quoted** in code review or **referenced** from skills — not dispatched by an agent as an action.
- Examples: naming conventions, error-handling rules, commit-message format.

### How to add

1. Create `rules/<topic>.md`. No frontmatter needed.
2. Start with a 1-2 sentence intro: what it covers, who it applies to, and any authoritative source it aligns with.
3. Number the rules (1, 2, 3 …) so they can be cited as "violates rule 7 of `go-naming`".
4. For each rule: one-line statement, then a ❌ / ✅ example if the rule isn't self-evident.
5. Close with an "Anti-Patterns" table if applicable.
6. Register it in `rules/README.md` and in the Rules section of the root `README.md`.

### Rule vs Skill — rule of thumb

| Signal | Format |
|--------|--------|
| "How do I do X?" | skill |
| "What's the convention for X?" | rule |
| Teaches a workflow | skill |
| Enforceable by lint / auditor | rule |
| Needs examples and prose | skill |
| Numbered list of do/don't | rule |

If a topic needs both, make both and cross-link — e.g. `git-workflow` skill + `commit-messages` rule.

---

## 9. Review Checklist

Before requesting review, confirm:

- [ ] Folder is kebab-case and matches `name` in frontmatter.
- [ ] `SKILL.md` has full frontmatter (`name`, `description`, `category`, `tags`).
- [ ] Description reads like a trigger prompt, not a product blurb.
- [ ] `python3 -m unittest discover -s tests -v` passes (also runs in CI).
- [ ] `python3 scripts/validate.py` passes (also runs in CI).
- [ ] `skills.json`, the relevant `INDEX.md`, `README.md`, and `.github/copilot-instructions.md` are regenerated (run `build_manifest.py` then `render_docs.py`).
- [ ] Cross-references to related skills go both ways. `python3 scripts/fix_related.py` reports missing back-references in dry-run; re-run with `--apply` to mutate the SKILL.md files (review the diff — auto-mutation can add back-references the original author intentionally omitted).
- [ ] If your skill could plausibly collide with an existing one, add a routing eval case to `evals/skill-routing.jsonl` and run `python3 scripts/run_routing_eval.py`.
- [ ] No repo-specific or project-specific assumptions leaked in.
- [ ] Examples compile / render / make sense on a fresh read.
