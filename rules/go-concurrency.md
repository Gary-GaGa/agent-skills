# Go Concurrency Rules

Rules for writing safe concurrent Go code. Aligned with the [`go-concurrency`](../go-concurrency/SKILL.md) skill.

---

## Goroutine Lifecycle

1. **Every goroutine must have a clear exit path.** Context cancellation, channel close, or WaitGroup.

2. **The parent owns the goroutine's lifetime.** Create context in parent, pass to child.

3. **Check `ctx.Done()` in every loop.** Without it, goroutines may run forever.

4. **Never fire-and-forget.** `go func() { ... }()` without a stop mechanism is a goroutine leak.

---

## Channels

5. **Default to unbuffered channels.** Only buffer when you've measured a bottleneck.

6. **Restrict direction in function signatures.** `chan<- T` for send-only, `<-chan T` for receive-only.

7. **Only the sender closes a channel.** Never close from the receiver side.

8. **Closing is a broadcast signal.** Use it to tell all receivers "no more data."

---

## Mutexes

9. **Use `RWMutex` when reads dominate.** Multiple readers, exclusive writer.

10. **Keep critical sections small.** Lock → minimum work → unlock.

11. **Always `defer mu.Unlock()`.** Prevents forgetting to unlock on early returns/panics.

12. **Never copy a mutex.** Pass by pointer: `*sync.Mutex`, not `sync.Mutex`.

---

## WaitGroup & errgroup

13. **Call `wg.Add(N)` before starting goroutines, not inside them.**

14. **Prefer `errgroup` over `WaitGroup` when goroutines can fail.** Propagates first error, cancels siblings.

---

## Context

15. **Propagate context through the call chain.** First parameter, always.

16. **Use `context.WithTimeout` for external calls.** No unbounded waits.

17. **Don't store context in structs.** Pass as function argument. Enforced by `go vet`.

---

## Race Prevention

18. **Run `go test -race` in CI. Always. Non-negotiable.**

19. **Capture loop variables in closures (Go < 1.22).** `go func(v T) { ... }(v)`.

20. **Don't share mutable state between goroutines without synchronization.** Use channels or mutex.

---

## Resource Limits

21. **Bound goroutine count.** Use worker pools or `semaphore.Weighted`. Don't spawn unlimited goroutines.

22. **Never use `time.Sleep` for synchronization.** Use channels, WaitGroup, or errgroup.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `go func() { ... }()` with no lifecycle | Add context/channel shutdown |
| `time.Sleep` to "wait for goroutine" | WaitGroup or channel |
| Shared map without mutex | `sync.RWMutex` or `sync.Map` |
| Passing `sync.Mutex` by value | Pass `*sync.Mutex` |
| Global mutable state unprotected | Wrap in struct with mutex |
| Ignoring `-race` failures | Fix them; race in test = race in prod |
