---
name: go-concurrency
description: >
  Go concurrency patterns — goroutines, channels, sync primitives, errgroup,
  context cancellation, and race condition prevention. Use this skill when
  writing concurrent Go code, debugging data races, or reviewing goroutine
  lifecycle management.
category: engineering
tags: [go, concurrency, goroutine, channel, sync]
related: [go-testing, debugging-methodology, clean-ddd-go, go-performance, mongodb-go, realtime-websocket]
---

# Go Concurrency

> Concurrency in Go is easy to start and hard to get right. The bugs are silent, intermittent, and often only appear in production under load.

## When to Use This Skill

- Writing code that uses goroutines, channels, or sync primitives
- Debugging data races or deadlocks
- Reviewing concurrent code for correctness
- Deciding between channels vs mutexes

---

## Core Mental Model

```
Don't communicate by sharing memory; share memory by communicating.
```

| Approach | When |
|----------|------|
| **Channels** | Passing ownership of data between goroutines; fan-out/fan-in; signaling |
| **sync.Mutex** | Protecting shared state that isn't naturally "passed" |
| **sync.WaitGroup** | Waiting for N goroutines to finish |
| **errgroup.Group** | WaitGroup + error propagation + context cancellation |
| **sync.Once** | One-time initialization |
| **atomic** | Simple counters, flags — avoid for complex state |

---

## Goroutine Lifecycle

### Every goroutine must have a clear exit path

1. **No fire-and-forget.** Every `go func()` must have a mechanism to stop: context cancellation, channel close, or WaitGroup.

2. **The parent owns the goroutine's lifetime.**
   ```go
   ctx, cancel := context.WithCancel(parentCtx)
   defer cancel()

   go worker(ctx)
   ```

3. **Check `ctx.Done()` in loops.**
   ```go
   func worker(ctx context.Context) {
       for {
           select {
           case <-ctx.Done():
               return
           case job := <-jobs:
               process(job)
           }
       }
   }
   ```

4. **Never leak goroutines.** Use `go test -race` and `runtime.NumGoroutine()` in tests to detect.

---

## Channel Patterns

### Unbuffered vs Buffered

| Type | Behavior | Use |
|------|----------|-----|
| `make(chan T)` | Sender blocks until receiver reads | Synchronization, handoff |
| `make(chan T, N)` | Sender blocks only when buffer full | Decoupling speed differences |

5. **Default to unbuffered.** Only buffer when you've measured a bottleneck.

### Direction

6. **Restrict channel direction in function signatures.**
   ```go
   func producer(out chan<- int) { ... }  // send-only
   func consumer(in <-chan int)  { ... }  // receive-only
   ```

### Fan-out / Fan-in

```go
func fanOut(ctx context.Context, input <-chan Job, workers int) <-chan Result {
    results := make(chan Result)
    var wg sync.WaitGroup
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range input {
                results <- process(ctx, job)
            }
        }()
    }
    go func() {
        wg.Wait()
        close(results)
    }()
    return results
}
```

### Close semantics

7. **Only the sender closes a channel.** Never close from the receiver side.
8. **Closing is a broadcast signal.** All receivers unblock. Use this for "done" signaling.
9. **Don't close a channel just because you're "done writing."** Only close when receivers need to know.

---

## sync Primitives

### Mutex

```go
type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

func (s *SafeMap) Get(key string) int {
    s.mu.RLock()
    defer s.mu.RUnlock()
    return s.m[key]
}

func (s *SafeMap) Set(key string, val int) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.m[key] = val
}
```

10. **Use `RWMutex` when reads dominate.** Multiple readers, single writer.
11. **Keep critical sections small.** Lock, do minimum work, unlock.
12. **Always use `defer mu.Unlock()`.** Prevents forgetting to unlock on early returns.
13. **Don't copy a mutex.** Pass `*sync.Mutex`, never `sync.Mutex` by value.

### WaitGroup

```go
var wg sync.WaitGroup
for _, item := range items {
    wg.Add(1)
    go func(it Item) {
        defer wg.Done()
        process(it)
    }(item)
}
wg.Wait()
```

14. **`Add` before `go`, not inside the goroutine.** Otherwise `Wait` might return before `Add` runs.

### errgroup

```go
g, ctx := errgroup.WithContext(ctx)
for _, url := range urls {
    g.Go(func() error {
        return fetch(ctx, url)
    })
}
if err := g.Wait(); err != nil {
    // first error; ctx is cancelled for all goroutines
}
```

15. **Prefer errgroup over WaitGroup when any goroutine can fail.** It propagates the first error and cancels siblings.

---

## Context Cancellation

16. **Propagate context through the call chain.** First parameter, always.
17. **Check `ctx.Err()` at natural suspension points** — before expensive operations, at loop tops, before network calls.
18. **`context.WithTimeout` for external calls.**
    ```go
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    resp, err := client.Do(req.WithContext(ctx))
    ```
19. **Don't store context in structs.** Pass as function argument. Enforced by `go vet`.

---

## Race Condition Prevention

### The #1 tool: `-race`

```bash
go test -race ./...
go run -race main.go
```

20. **Run `-race` in CI.** Always. Non-negotiable. It catches real bugs.

### Common race patterns

| Pattern | Fix |
|---------|-----|
| Two goroutines write to same map | `sync.RWMutex` or `sync.Map` |
| Goroutine reads variable, main writes it | Channel or mutex |
| Loop variable captured by closure | Capture as parameter: `go func(v T) { ... }(v)` (Go < 1.22) |
| Shared slice append | Mutex around append, or each goroutine writes to own index |

---

## Common Deadlock Patterns

| Pattern | Cause | Fix |
|---------|-------|-----|
| Unbuffered channel, no receiver | Sender blocks forever | Ensure receiver exists before send |
| Lock A then B in one goroutine; lock B then A in another | Lock ordering violation | Consistent lock order everywhere |
| WaitGroup never reaches zero | Missing `Done()` call | `defer wg.Done()` immediately after `Add` |
| Select with no default and all channels blocked | All cases waiting | Add `case <-ctx.Done()` or `default` |

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `go func() { ... }()` with no lifecycle management | Add context/channel-based shutdown |
| `time.Sleep` for synchronization | Use channels, WaitGroup, or errgroup |
| Goroutine per request with no limit | Use a worker pool or `semaphore.Weighted` |
| Passing `sync.Mutex` by value | Pass pointer `*sync.Mutex` |
| Global mutable state without protection | Wrap in a struct with mutex |
| Closing channel from receiver | Only sender closes |
| Ignoring `-race` failures ("it's just a test") | Race in test = race in prod |

---

## Checklist

- [ ] Every goroutine has a clear exit mechanism (context, channel, WaitGroup)
- [ ] Channel direction restricted in function signatures
- [ ] Mutexes protect all shared mutable state
- [ ] Critical sections are minimal
- [ ] `defer mu.Unlock()` used consistently
- [ ] `errgroup` used when goroutines can fail
- [ ] Context propagated; timeouts set for external calls
- [ ] `go test -race` passes
- [ ] No `time.Sleep` for synchronization
- [ ] Goroutine count bounded (worker pool or semaphore)

---

## Related Skills

- [`go-testing`](../go-testing/SKILL.md) — testing concurrent code with `-race`
- [`debugging-methodology`](../debugging-methodology/SKILL.md) — debugging race conditions
- [`rules/go-error-handling`](../../rules/go-error-handling.md) — error propagation with errgroup
