---
name: refactoring-patterns
description: >
  Safe, mechanical refactoring patterns — extract, inline, rename, replace conditional
  with polymorphism, and more. Use this skill when the user wants to clean up code without
  changing behaviour, is planning a refactor before adding a feature, or is reviewing
  a refactoring PR. Language-agnostic with Go examples.
category: engineering
tags: [refactoring, code-quality, patterns, go]
related: [clean-ddd-go, code-review, go-testing]
---

# Refactoring Patterns

> Refactoring is changing the structure of code without changing its behaviour. Tests prove the behaviour is preserved.

## When to Use This Skill

- Code works but is hard to read, extend, or test
- You need to add a feature but the current structure fights you
- A PR review pointed out structural issues
- You're preparing a module for extraction

## The Refactoring Contract

1. **Tests first.** If there are no tests, write characterisation tests before touching anything.
2. **One refactoring at a time.** Commit after each. Revert is cheap; disentangling two mixed refactors is not.
3. **No behaviour changes.** If a test breaks, your refactoring changed behaviour — fix it or revert.
4. **Separate refactoring commits from feature commits.** Reviewers can verify independently.

---

## Catalogue of Patterns

### Extract Function

**When:** A block of code does one identifiable thing, or you see a comment explaining what the next 10 lines do.

**Before:**
```go
func ProcessOrder(ctx context.Context, order *Order) error {
    // validate
    if order.Total <= 0 {
        return ErrInvalidTotal
    }
    if len(order.Items) == 0 {
        return ErrNoItems
    }

    // charge
    charge, err := gateway.Charge(ctx, order.Total)
    if err != nil {
        return fmt.Errorf("charge: %w", err)
    }
    order.ChargeID = charge.ID

    // notify
    if err := mailer.Send(ctx, order.Email, "confirmed", order); err != nil {
        log.Warn("email failed", "err", err)
    }
    return nil
}
```

**After:**
```go
func ProcessOrder(ctx context.Context, order *Order) error {
    if err := validateOrder(order); err != nil {
        return err
    }
    if err := chargeOrder(ctx, order); err != nil {
        return err
    }
    notifyCustomer(ctx, order)
    return nil
}

func validateOrder(order *Order) error {
    if order.Total <= 0 {
        return ErrInvalidTotal
    }
    if len(order.Items) == 0 {
        return ErrNoItems
    }
    return nil
}

func chargeOrder(ctx context.Context, order *Order) error {
    charge, err := gateway.Charge(ctx, order.Total)
    if err != nil {
        return fmt.Errorf("charge: %w", err)
    }
    order.ChargeID = charge.ID
    return nil
}

func notifyCustomer(ctx context.Context, order *Order) {
    if err := mailer.Send(ctx, order.Email, "confirmed", order); err != nil {
        log.Warn("email failed", "err", err)
    }
}
```

**Signals to extract:**
- Comments acting as section headers → the section is a function
- Deep nesting (3+ levels) → the inner block is a function
- Block used in multiple places → extract and reuse

---

### Inline Function

**When:** A function does nothing useful beyond its body — it's a needless indirection.

**Before:**
```go
func isEligible(age int) bool {
    return age >= 18
}

// used exactly once:
if isEligible(user.Age) { ... }
```

**After (if truly only used once and the meaning is obvious):**
```go
if user.Age >= 18 { ... }
```

**Don't inline if:** the function name adds clarity the expression doesn't, or it's used in multiple places.

---

### Rename (Variable, Function, Type)

**When:** The name doesn't say what the thing *is* or *does*. This is the highest-ROI refactoring.

Common improvements:

| Before | After | Why |
|--------|-------|-----|
| `data` | `orderSummary` | What data? |
| `process` | `chargeAndNotify` | Process how? |
| `flag` | `isRetryable` | Flag for what? |
| `tmp` | `formattedAddress` | Temporary what? |
| `err2` | `chargeErr` | Which error? |

**Mechanics:** Use your IDE's rename refactoring, not find-and-replace. It handles scope correctly.

---

### Extract Interface

**When:** You need to test a concrete dependency in isolation, or two implementations share a shape.

**Before:**
```go
type Service struct {
    db *sql.DB
}

func (s *Service) GetProduct(ctx context.Context, id string) (*Product, error) {
    row := s.db.QueryRowContext(ctx, "SELECT ...")
    // ...
}
```

**After:**
```go
type ProductRepository interface {
    FindByID(ctx context.Context, id string) (*Product, error)
}

type Service struct {
    products ProductRepository
}
```

Now `Service` can be tested with a fake repository. This is the dependency-inversion step in Clean Architecture.

**Don't over-extract:** If only one implementation will ever exist and you don't need test isolation, skip it. Interfaces are cheap to add later.

---

### Replace Conditional with Polymorphism

**When:** A switch/if-chain dispatches on a type field and the branches are non-trivial.

**Before:**
```go
func CalculateShipping(order Order) int {
    switch order.ShipMethod {
    case "standard":
        return order.Weight * 5
    case "express":
        return order.Weight*10 + 500
    case "overnight":
        return order.Weight*20 + 2000
    default:
        return 0
    }
}
```

**After:**
```go
type ShippingCalculator interface {
    Calculate(weight int) int
}

type standardShipping struct{}
func (s standardShipping) Calculate(weight int) int { return weight * 5 }

type expressShipping struct{}
func (e expressShipping) Calculate(weight int) int { return weight*10 + 500 }

type overnightShipping struct{}
func (o overnightShipping) Calculate(weight int) int { return weight*20 + 2000 }
```

**Don't do this for:** 2-3 line branches with no growth expected. The switch is simpler.

---

### Extract Variable

**When:** A complex expression is hard to read inline.

**Before:**
```go
if user.Age >= 18 && user.Country == "TW" && user.KYCStatus == "approved" && !user.IsBanned {
    // ...
}
```

**After:**
```go
isAdult := user.Age >= 18
isLocalUser := user.Country == "TW"
isVerified := user.KYCStatus == "approved"
isInGoodStanding := !user.IsBanned

if isAdult && isLocalUser && isVerified && isInGoodStanding {
    // ...
}
```

Each variable name documents the *intent* of the condition.

---

### Replace Magic Number/String with Constant

**When:** A literal value appears in code and its meaning isn't obvious.

**Before:**
```go
if retries > 5 { return ErrTooManyRetries }
time.Sleep(30 * time.Second)
```

**After:**
```go
const maxRetries = 5
const retryBackoff = 30 * time.Second

if retries > maxRetries { return ErrTooManyRetries }
time.Sleep(retryBackoff)
```

---

### Move Function to Receiver (or Move Method to Package Function)

**When:** A function knows too much about another type's internals, or a method doesn't use its receiver.

**Signal:** Function takes a `*Foo` and accesses 3+ of its fields → it should probably be a method on `Foo`.

**Reverse signal:** Method doesn't use `self`/receiver at all → it's a package-level function wearing a method hat.

---

### Decompose Large Struct

**When:** A struct has 10+ fields and they naturally group into sub-concerns.

**Before:**
```go
type Order struct {
    ID, CustomerName, CustomerEmail, CustomerPhone string
    Street, City, State, Zip, Country string
    Items []Item
    Total int
}
```

**After:**
```go
type Order struct {
    ID       string
    Customer Customer
    Address  Address
    Items    []Item
    Total    int
}

type Customer struct { Name, Email, Phone string }
type Address struct { Street, City, State, Zip, Country string }
```

This often reveals value objects in DDD terms.

---

## Refactoring Smells (When to Refactor)

| Smell | Likely refactoring |
|-------|-------------------|
| Function > 40 lines | Extract Function |
| 3+ levels of nesting | Extract Function, Guard Clause |
| Duplicate blocks (3+ lines, 2+ places) | Extract Function |
| Long parameter list (5+ params) | Extract Parameter Object / Struct |
| Switch on type field with non-trivial branches | Replace Conditional with Polymorphism |
| Comment explaining *what* the next block does | Extract Function (name replaces comment) |
| Struct with 10+ fields | Decompose Large Struct |
| Function name doesn't match what it does | Rename |
| Test requires complex setup to reach one line | Extract the dependency behind an interface |

---

## The "Preparatory Refactoring" Workflow

When you need to add a feature but the code isn't shaped for it:

```
1. Write tests for existing behaviour (if missing)
2. Refactor until the new feature has a natural home
3. Commit the refactoring (separate PR or commit)
4. Add the feature in a clean commit
```

This keeps the feature diff small and reviewable. Kent Beck: *"Make the change easy, then make the easy change."*

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| Refactoring without tests | You can't prove behaviour is preserved | Write tests first |
| Mixing refactoring + feature in one commit | Reviewers can't tell which changes are intentional | Separate commits |
| Extracting too early (premature abstraction) | Code is harder to read, not easier | Wait for 3 concrete examples before extracting |
| Renaming for the sake of renaming | Churn without value | Only rename if the current name is misleading |
| Giant refactoring PRs | Unreviewable, risky | Break into incremental PRs, each independently shippable |
| "While I'm here" scope creep | Refactoring spreads beyond the task | Stick to the original scope; file TODOs for the rest |

---

## Checklist

Before submitting a refactoring PR:

- [ ] Tests pass before and after each commit
- [ ] No behaviour change (no new test assertions needed for the refactoring itself)
- [ ] Each commit is a single, named refactoring
- [ ] PR contains only refactoring, no feature changes
- [ ] Names are clearer than before
- [ ] Complexity (nesting, function length, parameter count) is reduced
- [ ] No premature abstraction — at least 2-3 concrete uses justify each extraction

---

## Related Skills

- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — architecture that refactoring often moves toward
- [`go-testing`](../go-testing/SKILL.md) — tests that make refactoring safe
- [`code-review`](../code-review/SKILL.md) — reviewing refactoring PRs
- [`debugging-methodology`](../debugging-methodology/SKILL.md) — when a refactoring introduces a regression
