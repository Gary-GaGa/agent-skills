# Commit Message Rules

Based on [Conventional Commits v1.0.0](https://www.conventionalcommits.org/). Machine-parseable, human-readable, enables automated changelogs and semver bumping.

---

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Subject line is required. Scope, body, and footer are optional.

---

## Rules

### Subject Line

1. **Required shape:** `<type>(<scope>): <subject>` or `<type>: <subject>`.

2. **Lowercase, no trailing period.**
   - ✅ `feat: add oauth login`
   - ❌ `feat: Add OAuth login.`

3. **Imperative mood, present tense.** ("add", not "added" or "adds".)
   - ✅ `fix: handle nil pointer in cache lookup`
   - ❌ `fix: fixed nil pointer` / `fix: fixes nil pointer`

4. **≤ 72 characters** including the `type(scope):` prefix.

5. **Describe the change, not the implementation detail.**
   - ✅ `fix: prevent double-charge on retry`
   - ❌ `fix: add if-check in PaymentService.retry()`

---

### Types

Use exactly one of these:

| Type | When to use | Bumps |
|------|-------------|-------|
| `feat` | New feature (user-facing) | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | — |
| `style` | Formatting, whitespace, semicolons. No code behaviour change | — |
| `refactor` | Code restructure without behaviour change | — |
| `perf` | Performance improvement | PATCH |
| `test` | Adding or updating tests | — |
| `build` | Build system, dependencies (`go.mod`, `package.json`) | — |
| `ci` | CI/CD config (`.github/workflows/`) | — |
| `chore` | Maintenance tasks — repo config, meta | — |
| `revert` | Reverts a previous commit | — |

6. **If multiple types apply, pick the dominant one.** Most prominently, don't mix `feat` and `refactor` in one commit — split them.

7. **Breaking changes:** append `!` after type/scope and add `BREAKING CHANGE:` footer.
   - `feat(api)!: change /users response shape`
   - Bumps MAJOR.

---

### Scope (Optional)

8. **Scope is the affected area of the codebase** — package, module, feature.
   - ✅ `feat(auth): add OAuth provider`
   - ✅ `fix(cache): handle concurrent eviction`
   - Keep consistent across commits — pick a taxonomy (packages, bounded contexts, or features) and stick to it.

9. **Skip scope if the change is global** (`chore: bump go version`) or if scope would duplicate the type.

---

### Body (Optional but Recommended for Non-Trivial Changes)

10. **Separate from subject with a blank line.**

11. **Explain *why*, not *what*.** The diff shows what.
    - ✅ `"Retry count was unbounded, causing infinite loops when downstream was permanently unavailable."`
    - ❌ `"Added maxRetries constant set to 5."`

12. **Wrap at 72 columns.**

13. **Mention trade-offs, rejected alternatives, or context that won't survive in code comments.**

---

### Footer (Optional)

14. **Issue references:** `Closes #123`, `Refs #456`.

15. **Breaking changes:**
    ```
    BREAKING CHANGE: /users now returns { data, meta } instead of a raw array.
    Migration: callers should read response.data.
    ```

16. **Co-authors** (for pair programming):
    ```
    Co-authored-by: Name <email@example.com>
    ```

---

## Examples

### Good

```
feat(catalog): add stock reservation to SellProduct

When a sell succeeds, stock is now decremented atomically and a
ReservationID is returned so refunds can target the same transaction.

Closes #142
```

```
fix(cache): prevent race when two goroutines evict the same key

The previous impl used a non-atomic read-then-delete which could
evict entries inserted between the two calls. Switched to sync.Map's
CompareAndDelete.

Refs #201
```

```
refactor(usecase): extract repository injection into builder

No behaviour change. Preparing for #230 which needs the same
assembly logic in integration tests.
```

```
docs: clarify context propagation in clean-ddd-go skill
```

### Bad

❌ `fix bug` — no type, no scope, no specificity
❌ `Update code.` — trailing period, capital, no type, uninformative
❌ `feat: added new endpoint and refactored auth middleware and fixed a test` — three changes, should be three commits
❌ `WIP` — don't leave WIP commits on main; squash before merge
❌ `fix: PaymentService.ts line 42` — implementation detail, not intent

---

## Enforcement

- **commitlint** (`@commitlint/config-conventional`) for Node projects
- **pre-commit hook** rejecting non-conforming subjects
- **PR linter** like `amannn/action-semantic-pull-request` for GitHub

Automate this — don't rely on discipline alone.
