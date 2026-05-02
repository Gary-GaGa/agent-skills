# Go Logging Rules

Rules for structured logging in Go services. Aligned with the [`observability-go`](../observability-go/SKILL.md) skill.

---

## Format

1. **Structured logging always.** Key-value pairs, not printf.
   - ✅ `slog.Info("order processed", "order_id", id, "duration_ms", d)`
   - ❌ `log.Printf("processed order %s in %dms", id, d)`

2. **Use `log/slog` (Go 1.21+).** Stdlib, no dependency, pluggable handlers.

3. **JSON handler in production.** Text handler for local dev.

---

## Levels

4. **Levels mean something. Be consistent.**

| Level | Use |
|-------|-----|
| `DEBUG` | Development-only detail; disabled in production |
| `INFO` | Normal operations worth recording |
| `WARN` | Unexpected but recoverable; worth investigating |
| `ERROR` | Failed operation requiring attention or action |

5. **Don't use `ERROR` for expected conditions.** "User not found" on a lookup is `INFO`, not `ERROR`. `ERROR` means something is broken.

6. **Don't use `WARN` as a softer `ERROR`.** `WARN` means "this shouldn't normally happen but we handled it."

---

## What to Log

7. **Log at boundaries.** HTTP handler entry/exit, external API calls, DB queries, message processing.

8. **Log errors where they stop propagating.** Typically the HTTP handler or top-level goroutine — not every layer.
   - ❌ Log in repository → log in service → log in handler (3 duplicate lines)
   - ✅ Log once in handler with full context

9. **Include correlation IDs on every log line.** `request_id`, `trace_id`, `user_id`.

10. **Log operation outcome (success/failure) and duration.** Essential for monitoring.

---

## What NOT to Log

11. **Never log secrets, tokens, API keys, passwords.**

12. **Never log PII** (personal identifiable information) unless policy explicitly allows and you have redaction in place.

13. **Don't log full request/response bodies.** Log size + hash. Full bodies in DEBUG only.

14. **Don't log stack traces for expected errors.** Stack traces for panics and unexpected errors only.

---

## Context & Enrichment

15. **Use `slog.With()` to add context fields.** Create per-request loggers.
    ```go
    logger := slog.With("request_id", reqID, "user_id", userID)
    ```

16. **Include trace_id from OpenTelemetry when available.**

17. **Don't repeat static fields in every log call.** Set them once with `slog.With`.

---

## Performance

18. **slog is lazy; heavy fields (JSON marshal, etc.) are fine as long as level is checked.**

19. **Don't log inside tight loops.** Rate-limit or sample if needed.

20. **Don't log large objects.** Log IDs and sizes, not full contents.

---

## Output

21. **Log to stdout.** Let the infrastructure (Docker, K8s, log shipper) handle routing.

22. **One log line per event.** Multi-line logs break parsing.

23. **Timestamps in UTC (ISO 8601).** slog does this by default with JSON handler.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `log.Println` / `fmt.Println` | Use `slog` |
| Logging at every layer | Log at boundaries only |
| `log.Fatal` in library code | Return error; let caller decide |
| No correlation IDs | Add `request_id` / `trace_id` |
| Secrets in log output | Sanitize at log point |
| `ERROR` for "not found" | `INFO` — it's expected |
| Logging full HTTP body | Log size + content-type only |
