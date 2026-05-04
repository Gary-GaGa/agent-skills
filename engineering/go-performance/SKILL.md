---
name: go-performance
description: >
  Go performance analysis and optimization — benchmarking, pprof profiling,
  memory allocation reduction, escape analysis, and common performance pitfalls.
  Use this skill when a Go program is too slow or uses too much memory, or when
  reviewing code for performance-sensitive paths.
category: engineering
tags: [go, performance, profiling, pprof, benchmark, optimization]
related: [go-concurrency, go-testing, debugging-methodology]
---

# Go Performance

> Measure first, optimize second. Most performance "intuition" is wrong. Profilers don't lie.

## When to Use This Skill

- A Go service is too slow or consuming too much memory
- Need to benchmark a critical code path
- Reviewing performance-sensitive code
- Investigating GC pauses or allocation pressure

---

## The Optimization Workflow

```
1. Define the goal (latency target, memory budget)
2. Benchmark the current state
3. Profile to find the bottleneck
4. Fix the bottleneck (one change at a time)
5. Re-benchmark to verify improvement
6. Repeat until goal is met or ROI is too low
```

**Never skip step 2.** Optimizing without benchmarks is guessing.

---

## Benchmarking

```go
func BenchmarkProcess(b *testing.B) {
    data := setupTestData()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        Process(data)
    }
}
```

```bash
go test -bench=BenchmarkProcess -benchmem -count=5 ./...
```

| Flag | Purpose |
|------|---------|
| `-bench=.` | Run all benchmarks |
| `-benchmem` | Report allocations |
| `-count=5` | Run 5 times for statistical stability |
| `-benchtime=3s` | Minimum time per benchmark |
| `-cpuprofile=cpu.out` | Capture CPU profile during bench |
| `-memprofile=mem.out` | Capture memory profile |

### Reading benchmark output

```
BenchmarkProcess-8    500000    2340 ns/op    128 B/op    3 allocs/op
```

- `2340 ns/op` — time per operation
- `128 B/op` — bytes allocated per operation
- `3 allocs/op` — heap allocations per operation

### Comparing benchmarks

```bash
go install golang.org/x/perf/cmd/benchstat@latest
go test -bench=. -count=10 ./... > old.txt
# make changes
go test -bench=. -count=10 ./... > new.txt
benchstat old.txt new.txt
```

`benchstat` gives you confidence intervals and p-values. If `p > 0.05`, the difference is noise.

---

## Profiling with pprof

### CPU profile

```bash
go test -cpuprofile=cpu.out -bench=BenchmarkProcess ./...
go tool pprof cpu.out
# (pprof) top 20
# (pprof) web          # opens flamegraph in browser
# (pprof) list Process  # line-level breakdown
```

### Memory profile

```bash
go test -memprofile=mem.out -bench=BenchmarkProcess ./...
go tool pprof -alloc_space mem.out   # total allocations
go tool pprof -inuse_space mem.out   # live memory
```

### HTTP pprof (production)

```go
import _ "net/http/pprof"
go http.ListenAndServe(":6060", nil)
```

```bash
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30  # CPU
go tool pprof http://localhost:6060/debug/pprof/heap                 # memory
go tool pprof http://localhost:6060/debug/pprof/goroutine            # goroutine count
```

### What to look for

| Profile | Red flags |
|---------|-----------|
| CPU | One function dominating >30% of total time |
| Heap (alloc_space) | Hot path allocating many small objects |
| Heap (inuse_space) | Growing over time = possible leak |
| Goroutine | Count growing over time = goroutine leak |

---

## Allocation Reduction

Allocations → GC pressure → latency spikes. On hot paths, minimize allocations.

### Common sources and fixes

| Source | Fix |
|--------|-----|
| `fmt.Sprintf` in hot loops | `strconv.Itoa`, `strings.Builder`, pre-format |
| Returning `[]byte` from functions | Pass a buffer as parameter, let caller own it |
| Interface conversions | Avoid boxing primitives; use concrete types on hot paths |
| Slice growing via `append` | Pre-allocate: `make([]T, 0, expectedCap)` |
| Map creation in loops | Reuse maps; `clear(m)` to reset (Go 1.21+) |
| String concatenation | `strings.Builder` for multi-part strings |
| Closures capturing variables | May cause heap escape; move to struct method |

### Escape analysis

```bash
go build -gcflags="-m" ./...
```

Tells you what escapes to the heap. Common escapes:

- Returning a pointer to a local variable
- Storing in an interface
- Captured by a closure that outlives the stack frame
- Sent to a channel

**Don't micro-optimize escapes everywhere.** Only on hot paths identified by profiling.

---

## Common Performance Patterns

### Sync.Pool for reusable objects

```go
var bufPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func process() {
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bufPool.Put(buf)
    // use buf
}
```

Use for: large buffers, temporary structs on hot paths. Don't use for: small objects (overhead > savings).

### Pre-sized collections

```go
result := make([]Item, 0, len(input))  // known size
m := make(map[string]int, len(keys))   // hint
```

### Struct field ordering

Order fields by size (largest first) to minimize padding:

```go
// 24 bytes (no padding)
type Good struct {
    A int64   // 8
    B int32   // 4
    C int16   // 2
    D bool    // 1
}

// 32 bytes (padding between fields)
type Bad struct {
    D bool
    A int64
    C int16
    B int32
}
```

Use `fieldalignment` linter to detect.

---

## GC Tuning

### `GOGC` (default 100)

Controls GC frequency: higher = less frequent GC = more memory usage.

- `GOGC=200` — GC at 2× live heap (less CPU, more RAM)
- `GOGC=50` — GC at 1.5× live heap (more CPU, less RAM)
- `GOMEMLIMIT` (Go 1.19+) — hard memory limit; GC becomes more aggressive near the limit

### When to tune GC

- Default is fine for 95% of applications.
- Tune if: GC pause is visible in p99 latency, or memory is tightly constrained.
- Profile first; don't guess.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Optimizing without profiling | Profile first, then optimize |
| Micro-optimizing cold paths | Focus on hot paths only |
| `reflect` on hot paths | Use code generation or concrete types |
| `fmt.Sprintf` in tight loops | `strconv` or `strings.Builder` |
| Creating goroutines without bound | Worker pool with bounded size |
| Ignoring `benchstat` confidence intervals | Not significant = not real |
| `sync.Pool` for tiny objects | Overhead exceeds savings |
| Premature struct alignment | Only matters on cache-line-hot structs |

---

## Checklist

- [ ] Performance goal defined (latency, throughput, memory)
- [ ] Benchmark exists for the critical path
- [ ] pprof profile identifies the actual bottleneck
- [ ] One change at a time, re-benchmarked after each
- [ ] `benchstat` confirms significance (p < 0.05)
- [ ] Allocations reduced on hot paths (check with `-benchmem`)
- [ ] No premature optimization on cold paths
- [ ] GC tuning only if profiles show GC as the bottleneck

---

## Related Skills

- [`go-concurrency`](../go-concurrency/SKILL.md) — concurrent code has its own perf pitfalls
- [`go-testing`](../go-testing/SKILL.md) — benchmarks live in test files
- [`debugging-methodology`](../debugging-methodology/SKILL.md) — same systematic approach
