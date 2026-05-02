# Go Error Handling Rules

How to produce, propagate, and inspect errors in Go code. These rules keep error paths debuggable and callable.

---

## Return & Propagate

1. **Errors are the last return value.**
   - ✅ `func Find(id string) (*Product, error)`
   - ❌ `func Find(id string) (error, *Product)`

2. **Never ignore errors.** Either handle, wrap, or return.
   - ✅ `if err != nil { return fmt.Errorf("save: %w", err) }`
   - ❌ `result, _ := repo.Save(p)`
   - Exception: truly cannot fail (e.g. `io.WriteString` to `strings.Builder`) — add a comment.

3. **Don't return nil alongside a non-nil error.** Callers may check the value, not the error.
   - Exception: when the type has a documented "zero" meaning (e.g. `int`).

4. **Return early on error.** No `else` branch after an error return.
   ```go
   if err != nil {
       return err
   }
   // happy path continues at indent 0
   ```

---

## Wrapping

5. **Wrap with `%w` to preserve the error chain.** Use `%v` only if you're intentionally losing the original.
   - ✅ `fmt.Errorf("find product %s: %w", id, err)`
   - ❌ `fmt.Errorf("find product %s: %v", id, err)` (unless deliberate)

6. **Wrap at layer boundaries, not at every call.** Double-wrapping clutters logs.
   - ✅ Wrap once when crossing a layer (infra → usecase) with layer context.
   - ❌ `fmt.Errorf("layer1: %w", fmt.Errorf("layer2: %w", fmt.Errorf("layer3: %w", err)))` — noise.

7. **Wrap messages are lowercase, no trailing punctuation.**
   - ✅ `"find product: %w"`
   - ❌ `"Find product: %w."`
   - Reason: messages compose (`"outer: inner: root"`). Capitals and periods break the chain.

---

## Sentinel Errors

8. **Define sentinels as package-level `var` with `Err` prefix.**
   ```go
   var (
       ErrNotFound      = errors.New("product not found")
       ErrInvalidInput  = errors.New("invalid input")
   )
   ```

9. **Check sentinels with `errors.Is`, never `==`.**
   - ✅ `if errors.Is(err, catalog.ErrNotFound) { ... }`
   - ❌ `if err == catalog.ErrNotFound { ... }` — fails after wrapping.

10. **Check error types with `errors.As`.**
    ```go
    var verr *ValidationError
    if errors.As(err, &verr) {
        // use verr.Field, verr.Message
    }
    ```

11. **Don't use sentinels for per-instance data.** A sentinel is a *kind* of error. Use a type if you need fields.

---

## Error Types

12. **Custom error types: implement `Error() string`.**
    ```go
    type ValidationError struct {
        Field   string
        Message string
    }

    func (e *ValidationError) Error() string {
        return fmt.Sprintf("validation: %s: %s", e.Field, e.Message)
    }
    ```

13. **Support unwrapping if your type wraps another error.**
    ```go
    func (e *ValidationError) Unwrap() error { return e.Cause }
    ```

14. **Prefer pointer receivers for error types.** Avoids accidental copies hiding state.

---

## Panic Policy

15. **Do not panic for expected failures.** `NotFound`, `InvalidInput`, timeouts → return an error.

16. **Panic only for programmer errors — things that indicate a bug.**
    - Impossible state reached
    - `init()` misconfiguration
    - Type assertion that must succeed by design

17. **Recover at process boundaries only.** HTTP middleware, top of goroutine, `main()`. Don't `recover()` to make the code keep running — it hides bugs.

18. **Library code must not panic** across its API. Panics are fine inside internal helpers but shouldn't escape.

---

## Logging

19. **Log errors at the point they stop propagating.** Every layer wrapping and logging produces duplicate lines.
    - ✅ Log at the HTTP handler / main loop.
    - ❌ Log at every layer on the way up.

20. **Include the wrapped message in logs, not just the outer.**
    - Good logging frameworks auto-unwrap; `%+v` with `pkg/errors` or `slog.Error` handles chains.

21. **Don't log secrets, tokens, PII.** Sanitize before logging.

---

## Context & Cancellation

22. **Check `ctx.Err()` at cancellation points.** Long loops, before expensive operations.

23. **Propagate `context.Canceled` / `context.DeadlineExceeded` faithfully.** Don't convert them to generic errors — callers need to distinguish.

24. **Don't store `context.Context` in structs.** Pass it as a function argument. Enforced by `go vet` / linters.

---

## Sentinel vs Typed: Which When

| Situation | Use |
|-----------|-----|
| Caller only needs to know "this specific failure happened" | **Sentinel** (`ErrNotFound`) |
| Caller needs data about the failure (field name, retry-after, etc.) | **Typed error** (`*ValidationError`) |
| Multiple related failures with shared data shape | **Typed error** with a `Kind` field |

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| `if err != nil { return err }` at every layer | No context for debugging | Wrap with operation name |
| `errors.New(fmt.Sprintf(...))` | Can't be matched with `errors.Is` | Use `fmt.Errorf` |
| Swallowing errors with `_` | Bugs become invisible | Handle or log |
| `if err.Error() == "not found"` | Fragile string matching | Use sentinel + `errors.Is` |
| Returning both value and error when one is meaningless | Caller confusion | Pick one; document the other |
| Panicking on bad user input | Kills the process | Return a validation error |
