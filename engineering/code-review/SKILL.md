---
name: code-review
description: >
  How to give and receive code review effectively. Use this skill when the
  user is reviewing someone's PR, preparing a PR for review, or wants a
  review checklist. Covers what to look for, tone, comment severity, and
  how to disagree productively.
category: engineering
tags: [code-review, collaboration, quality, pr]
related: [git-workflow, refactoring-patterns, technical-writing-en, ddd-check]
---

# Code Review

> Review is not a gate. It's a conversation about how the change could be better — including "ship it".

## When to Use This Skill

- Reviewing a teammate's PR
- Preparing your own PR for review
- Receiving difficult feedback
- Setting review norms on a new team

## Principles

1. **Review the code, not the coder.** "This function is hard to follow" ≠ "you write hard code".
2. **Assume competence and goodwill.** Ask before accusing. "What's the intent here?" beats "this is wrong".
3. **Be explicit about severity.** Is it blocking? Or a suggestion? Use a prefix (see below).
4. **Small PRs get better reviews.** Push back on 1000-line PRs — split them.
5. **Ship faster, revisit.** A good-enough PR merged today > a perfect PR merged in 3 weeks.

---

## Comment Severity Conventions

Prefix comments so the author knows what's blocking:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `blocking:` | Must fix before merge | `blocking: this drops user input into SQL without escaping` |
| `suggestion:` | Think about it, author decides | `suggestion: we could extract this to a helper` |
| `nit:` | Style / taste, purely optional | `nit: prefer const over let here` |
| `question:` | Genuinely asking, not implying | `question: why is this retry count 5?` |
| `praise:` | Call out good work | `praise: nice error wrapping here` |

Teams should agree on these prefixes. When every comment looks equal, authors can't tell what's urgent.

---

## What to Look For (Reviewer Checklist)

### Correctness
- [ ] Does the code do what the PR says it does?
- [ ] Edge cases: empty input, nil, overflow, concurrent access
- [ ] Error paths handled, not swallowed
- [ ] Resource leaks: `defer Close()`, context cancellation

### Design
- [ ] Is this the right layer? (Domain logic in handler = flag)
- [ ] Are abstractions pulling their weight? (Single-use interface = flag)
- [ ] Does this introduce coupling that will hurt later?
- [ ] Could this be simpler?

### Readability
- [ ] Will I understand this in 6 months?
- [ ] Names reveal intent (not `data`, `info`, `manager`)
- [ ] Comments explain *why*, not *what*
- [ ] Functions do one thing

### Tests
- [ ] New behaviour has new tests
- [ ] Tests fail when the fix is reverted (the best sanity check)
- [ ] Edge cases covered, not just happy path

### Security
- [ ] Untrusted input validated
- [ ] No secrets in code/logs
- [ ] Auth checks on new endpoints
- [ ] SQL parameterized, no string concat

### Performance (when relevant)
- [ ] No accidental N+1
- [ ] No unbounded loops/allocations on hot path
- [ ] Don't over-optimise — measure first

---

## Receiving Review

### Good instincts to build

- **Assume the reviewer is trying to help.** Even blunt comments usually are.
- **"Why?" over "but".** If feedback doesn't make sense, ask for the reasoning before defending.
- **Separate the change from your ego.** The code is not you.
- **Take it offline when needed.** Threads > 3 replies deep → jump on a call / DM.
- **Batch responses.** Address all comments, then request re-review. Don't spam re-requests.

### Pushing back productively

Disagreement is fine. Do it with:
- **Evidence.** Link docs, tests, benchmarks.
- **Acknowledgement.** "I see your point about X, but Y because…"
- **Alternatives.** "Would Z address your concern?"

If stuck, escalate: "Let's ask a third reviewer" or "I'll merge as-is, file a follow-up for the deeper change."

---

## Giving Review

### Structure your comments

- **Lead with the most important thing.** Top-level PR comment: overall take.
- **Inline comments for specifics.**
- **Summarise at the end** if there's a pattern: "Overall looks good — main thing is the error handling in patterns 2 & 3."

### Tone

✅ "What happens if `user` is nil here?"
❌ "You didn't check for nil."

✅ "suggestion: extract to a helper — I see this pattern twice."
❌ "Why are you repeating this?"

### When not to comment

- The code works and is readable → approve, skip style nits
- You'd write it differently but it's equally valid → say nothing, or `nit:` only
- You're unsure → ask a question instead of asserting

---

## Size & Speed Norms

- **< 200 lines**: review within hours, usually one pass
- **200–400 lines**: review same day
- **400–800 lines**: ask author to split; if truly necessary, 1-day turnaround
- **> 800 lines**: block until split, unless it's boilerplate (e.g. generated code, migrations)

**Being a fast reviewer is a kindness** — authors context-switch back in cheaply.

---

## Anti-Patterns

| Anti-pattern | Why it's bad | Fix |
|--------------|--------------|-----|
| "LGTM 🚀" on 500-line PR in 2 min | Rubber stamp, no signal | Read it or say "skimmed" |
| Rewrite in review comments | Author's skill doesn't grow | Ask questions; let them solve |
| Blocking on style with no lint config | Subjective, unproductive | Automate via formatter/linter |
| Scope creep in comments | PRs never ship | File follow-up issues |
| Reviewing weeks later | Author lost context | Either review now or defer officially |

---

## Related Skills

- [`git-workflow`](../git-workflow/SKILL.md) — PR hygiene before review
- [`ddd-check`](../ddd-check/SKILL.md) — automate architectural checks so review focuses on design
