---
name: github-actions
description: >
  GitHub Actions CI/CD patterns — workflow structure, common triggers, matrix
  builds, caching, secrets management, reusable workflows, and deployment
  patterns. Use this skill when setting up or optimizing CI/CD pipelines
  on GitHub.
category: devops
tags: [github-actions, ci-cd, devops, automation, github]
related: [docker-basics, git-workflow, go-testing, k8s-fundamentals, terraform-basics]
---

# GitHub Actions

> CI/CD should be fast, reliable, and boring. If your pipeline surprises you, it's broken.

## When to Use This Skill

- Setting up CI/CD for a new GitHub repo
- Optimizing slow pipelines (caching, matrix, concurrency)
- Managing secrets and environments securely
- Creating reusable workflows for a team / org
- Debugging failing GitHub Actions

---

## Workflow Anatomy

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - run: go test -race ./...

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: golangci/golangci-lint-action@v6
```

### Rules

1. **Explicit `permissions`.** Principle of least privilege. `contents: read` is enough for most CI.
2. **Pin action versions with SHA, not tag, for third-party actions.** Tags can be reassigned; SHAs are immutable. `uses: actions/checkout@<sha>`.
3. **Jobs run in parallel by default.** Use `needs:` to create dependencies.

---

## Common Triggers

| Trigger | Use |
|---------|-----|
| `push` to main | CI + deploy |
| `pull_request` | CI on PRs (test, lint, build) |
| `schedule` (cron) | Nightly builds, dependency checks |
| `workflow_dispatch` | Manual trigger with optional inputs |
| `release` | Deploy on GitHub Release |

### Path filtering

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'go.mod'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

4. **Use path filters** to skip CI on doc-only changes.

---

## Caching

### Go

```yaml
- uses: actions/setup-go@v5
  with:
    go-version: '1.23'
    cache: true  # caches ~/go/pkg/mod and ~/.cache/go-build
```

### Node

```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
```

### Manual caching

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/my-tool
    key: ${{ runner.os }}-my-tool-${{ hashFiles('config.lock') }}
    restore-keys: |
      ${{ runner.os }}-my-tool-
```

5. **Cache key should include a hash of the lockfile.** Stale cache = subtle bugs.
6. **`restore-keys` for partial cache hits.** Better than a cold start.

---

## Matrix Builds

```yaml
jobs:
  test:
    strategy:
      matrix:
        go-version: ['1.22', '1.23']
        os: [ubuntu-latest, macos-latest]
      fail-fast: false
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - run: go test ./...
```

7. **`fail-fast: false`** — don't cancel other matrix jobs when one fails. You want the full picture.

---

## Secrets

```yaml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

8. **Never hardcode secrets.** Use GitHub Secrets (repo or org level).
9. **Use environments** for production secrets with required reviewers.
10. **Rotate secrets on a schedule.** At minimum: when anyone with access leaves.
11. **Secrets are masked in logs** automatically, but don't echo them explicitly.

---

## Reusable Workflows

```yaml
# .github/workflows/go-ci.yml (reusable)
on:
  workflow_call:
    inputs:
      go-version:
        type: string
        default: '1.23'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ inputs.go-version }}
      - run: go test -race ./...
```

```yaml
# .github/workflows/ci.yml (caller)
jobs:
  go:
    uses: ./.github/workflows/go-ci.yml
    with:
      go-version: '1.23'
```

12. **Extract common patterns into reusable workflows.** Share across repos via org-level workflows.

---

## Concurrency

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

13. **Cancel redundant runs.** New push to the same PR cancels the old run. Saves minutes and money.

---

## Go CI Template (Complete)

```yaml
name: Go CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
          cache: true
      - run: go vet ./...
      - run: go test -race -coverprofile=coverage.out ./...
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.out

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
      - uses: golangci/golangci-lint-action@v6

  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'
          cache: true
      - run: CGO_ENABLED=0 go build -o server ./cmd/server
```

---

## Common Debugging

| Problem | Fix |
|---------|-----|
| "Permission denied" on action | Check `permissions:` block; add needed scope |
| Cache never hits | Check key formula; ensure lockfile is committed |
| Workflow runs twice on PR | Remove `push` trigger for PR branches; keep only `pull_request` |
| Secret is empty | Check secret name matches; check environment restrictions |
| Job takes 15+ minutes | Add caching; check for unnecessary steps; parallelize |
| Flaky tests | Fix the test, not the CI; don't add retries as a band-aid |

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `permissions: write-all` | Minimum required permissions |
| Third-party actions pinned to `@v3` | Pin to SHA for supply-chain security |
| No caching | Add caching for deps and build artifacts |
| 30-minute pipeline | Parallelize; cache; skip unnecessary steps |
| Secrets in workflow file | Use GitHub Secrets |
| No `concurrency` control | Cancel redundant runs |
| One mega-job | Split into parallel jobs (test, lint, build) |
| Ignoring flaky tests ("just retry") | Fix the flake |

---

## Checklist

- [ ] `permissions` set to minimum required
- [ ] Actions pinned to SHA (third-party) or major version (first-party)
- [ ] Caching configured (Go modules, npm, etc.)
- [ ] Matrix for multi-version testing if applicable
- [ ] Secrets in GitHub Secrets, not hardcoded
- [ ] `concurrency` cancels redundant runs
- [ ] Jobs parallelized (test | lint | build)
- [ ] Path filters skip CI on doc-only changes
- [ ] Build artifact uploaded if downstream jobs need it

---

## Related Skills

- [`docker-basics`](../docker-basics/SKILL.md) — build/push Docker images in Actions
- [`git-workflow`](../../engineering/git-workflow/SKILL.md) — PR workflow that CI validates
- [`go-testing`](../../engineering/go-testing/SKILL.md) — tests the pipeline runs
