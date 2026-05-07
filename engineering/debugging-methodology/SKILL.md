---
name: debugging-methodology
description: >
  A systematic approach to debugging — reproduce, isolate, hypothesize,
  verify. Use this skill when the user is stuck on a bug, has a flaky test,
  is hunting a race condition, or wants a repeatable process instead of
  random print statements.
category: engineering
tags: [debugging, troubleshooting, methodology, observability]
related: [go-concurrency, go-performance, observability-go, agent-observability, gcp-observability-spring]
---

# Debugging Methodology

> The best debuggers aren't smarter — they're more systematic. Bugs don't hide from process.

## When to Use This Skill

- A bug is not obvious after 15 minutes of looking
- Test is flaky and you're tempted to just retry it
- Production incident — need a method, not vibes
- Race condition / timing bug
- "Works on my machine"

## The Loop

```
1. REPRODUCE   — get the bug to happen on demand
2. ISOLATE     — shrink the surface until only the bug remains
3. HYPOTHESIZE — state, in writing, what you think is wrong
4. VERIFY      — design the cheapest experiment that disproves the hypothesis
5. FIX         — once you understand it, the fix is usually small
```

Skipping steps is where hours disappear. Especially step 3 — you *think* you know, but writing it down exposes the gaps.

---

## 1. Reproduce

**If you can't reproduce it, you can't fix it** — you can only guess.

Priorities:
- **Minimum reliable reproduction.** Smallest input, shortest steps.
- **Deterministic if possible.** If flaky, figure out the non-determinism (timing, order, data).
- **Capture the exact environment.** Version, OS, data state.

### Can't reproduce locally?
- Log more at the failure site. Wait for it to happen again.
- Check if it's environment-specific (prod data, different Go version, timezone).
- Ask: *who* can reproduce? What do they do differently?

### Flaky test checklist
- Shared state between tests (global, DB rows, temp files)
- Time-dependent assertions (sleeps, timeouts, `time.Now()`)
- Concurrent goroutines with unbounded order
- External dependency (network, clock, filesystem)

---

## 2. Isolate (Binary Search)

With a reproducer, binary-search the cause:

- **Code:** `git bisect` on commits
- **Input:** halve the input until minimal
- **Features:** disable half the config, half the middleware, half the data
- **Time:** log entry/exit of major blocks, find which half fails

```bash
git bisect start
git bisect bad              # current is broken
git bisect good v1.2.3      # known good tag
# git checks out midpoint; you test; say good or bad
git bisect good             # or: git bisect bad
# repeat until git prints the offending commit
git bisect reset
```

`git bisect` is one of the most underused tools. 20 commits → 5 bisect steps.

---

## 3. Hypothesize (Write It Down)

This is the step most people skip. Force yourself to finish the sentence:

> "I think the bug is caused by ___ because ___. If that's true, then ___ should also happen."

The last clause is the testable prediction. If it doesn't match reality, your hypothesis is wrong — discard it and form a new one, don't bend reality to fit.

**Red flags your hypothesis is weak:**
- "It's probably a race condition." (Why? Prove it.)
- "Something is weird with the cache." (Specific how?)
- "Maybe if I restart it..." (You're out of hypotheses. Go back to step 1.)

---

## 4. Verify (Cheapest Experiment First)

Pick the experiment with the **highest information-per-minute**:

| Technique | When |
|-----------|------|
| Add a log line | 30 seconds, sometimes enough |
| `fmt.Printf` with unique markers | When logs are too noisy to find your entry |
| Step debugger (delve for Go) | When you need state at a specific point |
| Conditional breakpoint | When bug only triggers for specific input |
| `pprof` profiling | Performance / goroutine leak |
| `go test -race` | Suspected race condition |
| `GODEBUG=gctrace=1` | Memory / GC pressure |
| Packet capture / tcpdump | Network-level weirdness |
| Binary search log lines | "When did it start going wrong?" |

**Two critical habits:**
1. **Change one thing at a time.** Two changes = two possible causes for any result.
2. **Always predict before you run.** If the result surprises you, your model is wrong — that's the discovery.

---

## 5. Fix

Once you understand the bug, the fix is usually 1-10 lines. If your fix is 200 lines, you probably didn't understand the bug — you're refactoring.

**Before merging:**
- **Add a regression test** that fails without the fix. No test = it'll come back.
- **Check for siblings.** Same bug pattern elsewhere in the code?
- **Document the gotcha** in a comment if it's non-obvious.

---

## Debugging Tools (Go)

| Tool | Use |
|------|-----|
| `delve` (`dlv debug`) | Interactive debugger |
| `go test -race` | Data race detector |
| `go test -run TestName -v` | Single test, verbose |
| `pprof` (`go tool pprof`) | CPU / memory / goroutine profiles |
| `go test -cpuprofile` / `-memprofile` | Profile test runs |
| `runtime.Stack()` | Dump goroutine stacks at a point |
| `GOTRACEBACK=all` | More complete panic output |
| `GODEBUG=schedtrace=1000` | Runtime scheduler trace |

---

## Observability in Production

When local debugging isn't an option:

1. **Structured logs** with correlation IDs (trace/span)
2. **Metrics** for rates, durations, error counts
3. **Distributed tracing** for cross-service flows
4. **Time-boxed reproductions:** "It happened at 14:03 for user X" + trace ID

If your production bug needs a deploy to add a log line, you don't have enough observability. Add more baseline instrumentation, not just reactive logs.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| "Just add a retry, it's probably transient" | Find the root cause first. Retries hide bugs. |
| `time.Sleep(100 * time.Millisecond)` to "fix" race | Fix the synchronization. Sleeps are timebombs. |
| Mass print-debug, never cleaned up | Use structured logging; remove debug statements or gate behind a flag |
| "Reproduce it in prod" | Extract a local reproducer before guessing |
| Shotgun-fixing multiple things | One change at a time |
| Believing the code over the evidence | Print/log what you assume is true. Often it's not. |

---

## Psychological Notes

- **Rubber-ducking works.** Explaining the bug out loud finds it half the time.
- **Step away when stuck > 45min.** Not a weakness — pattern-matching returns fresh.
- **Write what you've tried.** A running log prevents re-testing the same thing.
- **Trust the evidence over your expectations.** If logs say X, it's X, not "that can't be right".

---

## Debugging Checklist

When stuck, run through these:

- [ ] Can I reproduce it on demand? If not, that's the current task.
- [ ] What's my current hypothesis, in one sentence?
- [ ] What experiment would disprove it?
- [ ] Am I changing one thing at a time?
- [ ] Is my log output telling me what I *think* it's telling me?
- [ ] Have I re-read the error message word by word?
- [ ] Have I checked the obvious stuff? (Env var, config, permissions, version)
- [ ] Has this bug existed in history? (`git log -S "suspicious_string"`)
