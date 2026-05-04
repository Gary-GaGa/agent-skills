---
name: git-workflow
description: >
  Day-to-day Git workflow for developers — branching, commits, rebase vs merge,
  conflict resolution, PR hygiene, and recovery from common mistakes. Use this
  skill when the user asks how to structure commits, clean up history, handle
  a tricky merge, or set up a team branching strategy.
category: engineering
tags: [git, workflow, version-control, collaboration]
related: [code-review]
---

# Git Workflow

> The 20% of Git you use 80% of the time — done safely and predictably.

## When to Use This Skill

- Choosing a branching strategy for a new project/team
- Structuring commits for a feature
- Cleaning up history before opening a PR
- Resolving merge conflicts
- Recovering from a mistake (`reset`, `reflog`, detached HEAD)
- Deciding rebase vs merge

## Branching Strategies

| Strategy | Fit | How it works |
|----------|-----|--------------|
| **Trunk-based** | Small teams, CI/CD, feature-flagged | Short-lived branches (< 2 days), merge to `main` frequently. Default for most modern teams. |
| **GitHub Flow** | Web apps, continuous deploy | Branch from `main`, PR, merge back. No `develop` branch. |
| **GitFlow** | Scheduled releases, versioned libs | `main`/`develop`/`release/*`/`hotfix/*`. Heavy; usually overkill. |

**Default recommendation: GitHub Flow or trunk-based.** GitFlow is rarely worth the overhead unless you ship versioned releases on a cadence.

### Branch naming

Pick one convention and stick to it:

```
feat/add-oauth-login
fix/race-condition-in-cache
docs/update-readme
chore/bump-deps
claude/<short-descriptor>     # for AI-assisted branches
```

---

## Commit Discipline

**One logical change per commit.** If your commit message needs "and", split it.

See [`rules/commit-messages.md`](../../rules/commit-messages.md) for the full Conventional Commits rule set.

### Atomic commit rule of thumb

Each commit should:
1. Compile on its own.
2. Pass tests on its own (if practical).
3. Have a message explaining *why*, not *what* (the diff shows what).

### Staging surgically

```bash
git add -p          # interactive: pick hunks, not whole files
git restore -p      # interactive: discard hunks
```

Stop using `git add -A` for feature commits. Use it for the first commit of a throwaway branch only.

---

## Rebase vs Merge

| Operation | Use when |
|-----------|----------|
| `git rebase main` on your feature branch | Keep feature branch linear; cleanup before opening PR |
| `git merge main` into your feature branch | Long-lived branch that others pulled from |
| Merge PR with **squash** | Preferred for most feature PRs — one clean commit on `main` |
| Merge PR with **merge commit** | You want to preserve commit history (rare) |
| Merge PR with **rebase** | Keep linear history but preserve each commit — only if commits are atomic |

**Rule:** Never rebase a branch that's been pushed and others may have pulled. Rebasing rewrites history, and force-pushing clobbers their work.

### Clean up before PR

```bash
git rebase -i main             # reorder, squash, reword
git push --force-with-lease    # safer than --force
```

`--force-with-lease` refuses the push if someone else pushed to the branch — protects against overwriting teammates.

---

## Conflict Resolution

1. **Understand both sides first.** Read the `<<<<<<<` and `>>>>>>>` blocks. Don't just pick one.
2. **Small, frequent merges** avoid big conflicts. Rebase or merge `main` daily on long branches.
3. **Conflicts in generated files** (e.g. `go.sum`, lockfiles) → regenerate, don't manually merge.
4. **After resolving:**
   ```bash
   git add <resolved-file>
   git rebase --continue       # or git merge --continue
   ```
5. **Abort if unsure:** `git rebase --abort` / `git merge --abort` — nothing is lost.

---

## Recovery

Git almost never loses data. Recovery cheatsheet:

| Situation | Recovery |
|-----------|----------|
| Deleted a branch | `git reflog` → `git checkout -b recovered <sha>` |
| Bad rebase, want original back | `git reflog` → `git reset --hard HEAD@{5}` |
| Committed to wrong branch | `git reset --soft HEAD~1` (undo commit, keep changes) → switch branch → commit |
| Want to undo last commit but keep changes | `git reset --soft HEAD~1` |
| Want to throw away last commit | `git reset --hard HEAD~1` ⚠️ |
| Accidentally committed secrets | `git reset`, rewrite history, **rotate the secret anyway** |

**`git reflog` is your safety net.** It records every HEAD movement for ~90 days.

---

## PR Hygiene

- **Keep PRs small.** < 400 lines changed is ideal. > 800 means split.
- **One concern per PR.** Don't bundle a refactor with a feature.
- **PR description:** problem → approach → test plan. Link the issue.
- **Draft PRs** are free — open early for visibility, even before ready.

See [`code-review`](../code-review/SKILL.md) for what to expect during review.

---

## Common Mistakes & Fixes

| Mistake | Fix |
|---------|-----|
| `git push --force` instead of `--force-with-lease` | Use `--force-with-lease` always |
| Committed `node_modules/` / `vendor/` / `.env` | `git rm -r --cached`, update `.gitignore`, rotate secrets if exposed |
| Huge "WIP" commits | Rebase-interactive before PR; squash into logical units |
| Merging own PR without review | Set branch protection rules |
| Amending a pushed commit | Creates divergence. Prefer a new commit; only amend if branch is yours alone. |

---

## Checklist Before Opening PR

- [ ] Branch rebased on latest `main` (or cleanly mergeable)
- [ ] Commits are atomic and well-messaged
- [ ] No WIP / debug / generated garbage committed
- [ ] Tests added/updated
- [ ] Diff < 400 lines (split if larger)
- [ ] PR description explains *why*, not just *what*

---

## Related Skills

- [`code-review`](../code-review/SKILL.md) — the other side of the PR
- [`rules/commit-messages.md`](../../rules/commit-messages.md) — commit message format
