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
| `engineering` | Software design, development, SDK usage, auditing. |
| `ai-engineering` | LLM agents, prompts, context, tools, evals, observability, safety. |
| `content` | Writing, editing, publishing, content marketing. |
| `finance` | Personal investing, market analysis, trading discipline. |
| `rules` | Lightweight rule sheets (see ["Adding a Rule" below](#adding-a-rule-lightweight-convention-sheet)). |

Planned (open a PR to add):

- `devops`, `testing`, `review`, `data`

If your skill doesn't fit, propose a new category in your PR and add it to `README.md`.

---

## 3. Create the Skill Folder

1. Create a kebab-case directory at the repo root: `your-skill-name/`.
   - If the skill is language- or locale-specific, suffix with the code: `medium-writing-zh`, `clean-ddd-go`.
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

1. Add a row to the relevant category table in `README.md`.
2. If you introduced a new category, add it to the category table in `README.md` and update `.github/copilot-instructions.md`.
3. If the skill relates to existing skills, add mutual `related:` entries and cross-link them in prose.

---

## 6. Frontmatter Field Reference

| Field | Required | Purpose |
|-------|----------|---------|
| `name` | yes | Must match the folder name exactly. Lowercase, kebab-case. |
| `description` | yes | Intent-matchable blurb. Agents decide to load on this. |
| `category` | yes | One of the defined categories. |
| `tags` | yes | Free-form labels: language, framework, purpose. Lowercase, kebab-case. |
| `related` | no | List of other skill `name`s that pair with this one. |

---

## 7. Style Guide

- **Language.** Use the language that best serves the audience. Chinese skills should be written in 繁體中文; SDK/architecture skills are typically English.
- **Mixed text.** In Chinese prose, put a half-width space between CJK and Latin/numbers (`使用 Medium 撰寫`).
- **Code blocks.** Annotate with a language tag so syntax highlighting works.
- **Links.** Use relative paths for intra-repo links (`../other-skill/SKILL.md`).
- **No emojis** unless they carry meaning (e.g. severity markers in `ddd-check`).

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
- [ ] Skill is registered in `README.md` under the correct category.
- [ ] Cross-references to related skills go both ways.
- [ ] No repo-specific or project-specific assumptions leaked in.
- [ ] Examples compile / render / make sense on a fresh read.
