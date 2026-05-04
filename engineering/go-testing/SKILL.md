---
name: go-testing
description: >
  Guidance for writing effective tests in Go. Use this skill when the user
  wants to add, refactor, or review tests for a Go project — including
  table-driven tests, subtests, mocks/fakes, parallel tests, integration
  tests, and coverage analysis. Pairs naturally with clean-ddd-go.
category: engineering
tags: [go, testing, tdd, quality]
related: [clean-ddd-go, ddd-check, go-concurrency, go-performance, refactoring-patterns, agentic-coding-patterns, github-actions, mongodb-go]
---

# Go Testing

> Practical patterns for writing tests that catch bugs, run fast, and stay readable.

## When to Use This Skill

- Writing new tests for Go code
- Refactoring existing tests that are flaky or hard to read
- Choosing between mocks, fakes, and real dependencies
- Deciding what layer to test (unit / integration / e2e)
- Interpreting coverage reports

## Core Principles

1. **Test behaviour, not implementation.** Tests should survive refactors that preserve behaviour.
2. **Fast, deterministic, independent.** No sleeps, no ordering dependencies, no shared mutable state.
3. **One assertion concept per test.** A test with 10 `assert` lines on unrelated things is really 10 tests.
4. **Arrange → Act → Assert.** Keep the three phases visible. Blank lines are cheap.
5. **Table-driven by default.** Once you have 2+ cases with the same shape, use a table.

---

## Test Structure

### Table-Driven Test (canonical form)

```go
func TestProduct_Sell(t *testing.T) {
    tests := []struct {
        name     string
        stock    int
        qty      int
        wantOK   bool
        wantLeft int
    }{
        {name: "sells when enough stock", stock: 5, qty: 3, wantOK: true, wantLeft: 2},
        {name: "fails when insufficient", stock: 1, qty: 3, wantOK: false, wantLeft: 1},
        {name: "rejects non-positive qty", stock: 5, qty: 0, wantOK: false, wantLeft: 5},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            p := catalog.NewProduct("p1", "Widget", catalog.Price{}, tt.stock)
            got := p.Sell(tt.qty)
            if got != tt.wantOK {
                t.Errorf("Sell() = %v, want %v", got, tt.wantOK)
            }
            if p.Stock != tt.wantLeft {
                t.Errorf("Stock = %d, want %d", p.Stock, tt.wantLeft)
            }
        })
    }
}
```

**Why this form:**
- `t.Run(tt.name, ...)` gives each case a named subtest — fails pinpoint exactly.
- The table is the spec; adding a case is one line.
- No shared state between iterations.

---

## Test Doubles: Mock vs Fake vs Stub

| Type | What it is | When to use |
|------|-----------|-------------|
| **Stub** | Returns canned values. No verification. | You just need the collaborator to return something. |
| **Fake** | Working lightweight implementation (e.g. in-memory repo). | Integration-ish tests of the usecase layer. Preferred for DDD usecase tests. |
| **Mock** | Records calls and verifies them. | You need to assert "was this called with these args". Use sparingly. |

**Default to fakes.** Fakes survive refactors; mocks ossify implementation details.

### In-memory fake example (DDD repository)

```go
type memProductRepo struct {
    mu    sync.Mutex
    items map[string]*catalog.Product
}

func newMemProductRepo() *memProductRepo {
    return &memProductRepo{items: map[string]*catalog.Product{}}
}

func (r *memProductRepo) Save(_ context.Context, p *catalog.Product) error {
    r.mu.Lock(); defer r.mu.Unlock()
    r.items[p.ID] = p
    return nil
}

func (r *memProductRepo) FindByID(_ context.Context, id string) (*catalog.Product, error) {
    r.mu.Lock(); defer r.mu.Unlock()
    return r.items[id], nil
}
```

This is ~20 lines and removes the need for any mocking framework in the usecase layer.

---

## Parallel Tests

```go
func TestSomething(t *testing.T) {
    t.Parallel()
    // ...
}
```

**Pitfalls:**
- Table-driven subtests: capture the loop variable — `tt := tt` before `t.Run`, else all subtests see the last case. (Fixed in Go 1.22+, but be explicit.)
- Don't share mutable state across parallel tests. Each subtest gets its own fake.
- Disable parallel for tests that touch process-wide state (env vars, `os.Chdir`).

---

## Helpers

Mark helpers so failures point to the caller, not the helper:

```go
func newTestProduct(t *testing.T, stock int) *catalog.Product {
    t.Helper()
    return catalog.NewProduct("p1", "Widget", catalog.Price{Amount: 100, Currency: "TWD"}, stock)
}
```

---

## Integration Tests

Separate with build tags:

```go
//go:build integration

package catalog_test
```

Run: `go test -tags=integration ./...`

**Integration test rules:**
- Use real dependencies (DB, HTTP) but in containers (testcontainers-go).
- Tear down in `t.Cleanup(func() { ... })`, not `defer` (survives panics and `t.Fatal`).
- Keep them under 10s each; anything slower goes to e2e.

---

## Coverage

```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

**Read coverage as a smell detector, not a target:**
- Uncovered domain code → write a domain test.
- Uncovered error paths → probably untested edge cases, add them.
- Chasing 100% on adapters often tests the framework, not your logic.
- **Don't optimise for coverage numbers.** 70% meaningful > 95% shallow.

---

## Common Anti-Patterns

| Smell | Fix |
|-------|-----|
| `time.Sleep` in tests | Use channels, `sync.WaitGroup`, or `eventually` helpers. |
| Test depends on previous test's side effects | Each test owns its state. |
| Asserting on error strings | Use `errors.Is` / `errors.As` with sentinel errors. |
| Giant `setup()` that does 20 things | Tests become opaque. Inline setup per test or per subtest. |
| Mocking types you own | Mock boundaries you don't own (DB, HTTP). Use fakes for your own interfaces. |
| Over-specified mocks asserting call order | Refactor to fake + assert final state. |

---

## Checklist

Before merging test code:

- [ ] Each test name describes the scenario and expected outcome
- [ ] Table-driven where 2+ cases share shape
- [ ] No `time.Sleep`, no hidden ordering dependencies
- [ ] `t.Helper()` on helpers; `t.Cleanup()` for teardown
- [ ] Parallel where safe, serial where required (documented why)
- [ ] Integration tests tagged with build tag
- [ ] Error assertions use `errors.Is` / `errors.As`
- [ ] Test fails for the right reason (run with the fix reverted)

---

## Related Skills

- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — architecture this testing style is designed for
- [`ddd-check`](../ddd-check/SKILL.md) — catches structural issues tests can't
- [`rules/go-error-handling.md`](../../rules/go-error-handling.md) — error conventions used in assertions
