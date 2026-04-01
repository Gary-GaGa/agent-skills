---
name: ddd-check
description: >
  Run this skill whenever the user wants to check, audit, or validate the DDD (Domain-Driven Design)
  or Clean Architecture structure of a Go project — even if they just say "check the architecture",
  "is this DDD correct?", "audit imports", "any layer violations?", or "scan the project".
  This skill scans Go source files for architectural violations across domain, usecase, adapter,
  and infra layers and produces a structured report with file/line references and a pass/fail summary.
  Always use this skill proactively after refactoring sessions or before PRs in DDD Go projects.
---

# DDD Architecture Check — Go Projects

## What This Skill Does

Scans a Go project for Clean Architecture / DDD violations and produces a report with:
- Violation category
- File path + line number
- Severity (🔴 Critical / 🟡 Warning / 🔵 Info)
- Pass/Fail summary per category

---

## Layer Convention

The checks assume this standard structure (adapt if the project differs):

```
app/
├── domain/      → Core business logic. Zero external dependencies.
├── usecase/     → Application layer: interactors, port interfaces, DTOs.
│   ├── port/in/ → Input ports (Usecase interfaces)
│   ├── port/out/→ Output ports (Repository interfaces)
│   └── dto/     → Data Transfer Objects
├── adapter/     → Interface layer: HTTP handlers, CLI, gRPC.
└── infra/       → Infrastructure: DB, cache, external APIs.
```

---

## Checks to Run

Run ALL checks below. Use `grep`, `Glob`, and `Read` tools to scan the codebase.

---

### CHECK 1 — Domain Layer Must Not Import Non-stdlib Packages 🔴

Domain packages (`app/domain/**/*.go`) must only import:
- Go standard library packages
- Other `app/domain/` packages (internal cross-domain is OK)

**How to detect**: Find all `.go` files under `app/domain/`, read their import blocks, flag any import that is NOT stdlib and NOT another `app/domain/` package.

**Common violations**:
- Importing `github.com/...` (3rd party frameworks)
- Importing `app/usecase/...`, `app/infra/...`, `app/adapter/...`

**Severity**: 🔴 Critical — breaks the dependency rule.

---

### CHECK 2 — Adapter/Handler Must Not Use Domain Types Directly 🔴

Files in `app/adapter/**/*.go` must not reference domain struct types in:
- Function signatures exposed via HTTP/gRPC/CLI
- JSON response structs

They should use DTOs from `app/usecase/dto/` instead.

**How to detect**: In adapter files, look for import of `app/domain/` packages **other than** importing domain errors (e.g., `player.ErrXxx`). Importing domain errors is acceptable — importing domain data types for response bodies is not.

**Distinguishing error imports from type imports**: Check if the import is used only with `errors.Is(err, domain.ErrXxx)` pattern (OK) vs used as a field type in a struct or response body (violation).

**Severity**: 🔴 Critical for response types, 🔵 Info for error sentinel imports.

---

### CHECK 3 — Input Port Interface Must Not Leak Domain Types 🟡

Files in `app/usecase/port/in/**/*.go` define the Usecase interface. Their method signatures must only reference:
- Primitive types (`string`, `int64`, `bool`, `time.Time`, `error`)
- DTO types from `app/usecase/dto/`
- Standard library types

**How to detect**: Read port/in interface files, check method signatures for domain type references (anything from `app/domain/`).

**Severity**: 🟡 Warning — makes the adapter tightly coupled to domain internals.

---

### CHECK 4 — Domain Methods Returning Bool for Business Rule Violations 🟡

Domain methods (in `app/domain/**/*.go`) that enforce business rules should return `error`, not `bool`. Returning `bool` loses the reason for failure.

**How to detect**: In domain files, look for method signatures matching patterns like:
- `func (... *SomeType) SomeAction(...) bool`
- Where the method name suggests a command or state change (e.g., `Buy`, `Start`, `Upgrade`, `Apply`, `Select`)

**False positives to exclude**:
- Query/getter methods that naturally return bool: `IsActive()`, `Done()`, `Has...()`
- `bool` as a secondary return alongside error: `(bool, error)` is fine

**Severity**: 🟡 Warning — business rule violations become opaque to callers.

---

### CHECK 5 — Duplicate Guard Clauses (DRY Violations) 🔵

Repeated identical or near-identical patterns in the same file or package suggest a missing helper.

**Common pattern in this project**: Default language initialization guard:
```go
if p.CurrentLanguage == "" {
    p.CurrentLanguage = "go"
    ...
}
```

**How to detect**: Use grep to find files where a similar 3+ line guard block appears more than twice in the same file.

**Severity**: 🔵 Info — not a correctness issue but a maintainability smell.

---

### CHECK 6 — Repository Interface Must Be Defined in Domain or Usecase Layer 🔴

Repository interfaces (the contract for persistence) must live in `app/domain/` or `app/usecase/port/out/`, NOT in `app/infra/`.

**How to detect**: Search `app/infra/**/*.go` for `type ... interface` declarations. If found, they should be structs implementing an interface, not defining one.

**Severity**: 🔴 Critical — violates dependency inversion.

---

### CHECK 7 — Infra Must Not Import Adapter Layer 🔴

`app/infra/**/*.go` must not import `app/adapter/`. The dependency must flow: Adapter → Usecase → Domain ← Infra. Infra importing Adapter creates a cycle.

**How to detect**: Grep import blocks in infra files for `app/adapter`.

**Severity**: 🔴 Critical — circular dependency.

---

## Report Format

After running all checks, output a report in this exact structure:

```
# DDD Architecture Check Report
## Project: <detected project name from go.mod>
## Scanned: <timestamp>

---

## Summary

| Check | Status | Violations |
|-------|--------|------------|
| 1. Domain imports    | ✅ PASS / ❌ FAIL | N |
| 2. Adapter ↔ Domain  | ✅ PASS / ❌ FAIL | N |
| 3. Port interface    | ✅ PASS / ❌ FAIL | N |
| 4. Bool returns      | ✅ PASS / ❌ FAIL | N |
| 5. DRY guard clauses | ✅ PASS / ❌ FAIL | N |
| 6. Repository loc    | ✅ PASS / ❌ FAIL | N |
| 7. Infra→Adapter     | ✅ PASS / ❌ FAIL | N |

**Overall: ✅ CLEAN / ❌ X violation(s) found**

---

## Violations Detail

### 🔴 CHECK 1 — Domain Layer Imports
> (list each violation as:)
- `app/domain/player/player.go:8` — imports `github.com/some/lib` (not stdlib)

### 🟡 CHECK 3 — Port Interface Leaks Domain Types
- (none)

... (only show checks with violations, or show "(none)" for passing checks)

---

## Recommendations

(For each failing check, give 1-2 actionable sentences on how to fix it.)
```

---

## Tips for Running Checks

- Start with `Glob` to enumerate all `.go` files per layer.
- Use `Grep` with the `path` parameter to limit scope to specific directories.
- For import analysis, search for the `import (` block pattern and read surrounding lines.
- When in doubt, `Read` the full file — it's faster than guessing from grep snippets.
- Skip `_test.go` files for checks 1–3 (test files are allowed more flexibility).
- If the project uses a different directory structure than `app/domain/`, adapt accordingly — ask the user if unclear.
