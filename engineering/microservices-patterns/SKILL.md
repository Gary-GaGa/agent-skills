---
name: microservices-patterns
description: >
  Microservices architecture patterns — service decomposition, communication
  (sync/async), service discovery, circuit breaker, API gateway, 12-factor,
  and when to stay monolithic. Use this skill when designing distributed systems,
  splitting a monolith, or reviewing a microservices architecture.
category: engineering
tags: [architecture, microservices, distributed-systems, 12-factor, patterns]
related: [clean-ddd-go, event-driven-architecture, api-design-rest, api-design-grpc, gcp-pubsub-spring, graphrag-multi-service]
---

# Microservices Patterns

> Microservices are a deployment strategy, not an architecture silver bullet. Most teams should start as a modular monolith and extract services only when they have a clear operational reason.

## When to Use This Skill

- Evaluating whether to use microservices or stay monolithic
- Decomposing a monolith into services
- Choosing communication patterns between services
- Implementing resilience patterns (circuit breaker, retry, timeout)
- Reviewing a distributed system for common pitfalls

---

## Should You Use Microservices?

### Reasons that justify microservices

| Signal | Why it helps |
|--------|--------------|
| **Independent deployment** is needed | Team A ships without waiting for Team B |
| **Different scaling needs** | Service X needs 100 instances; Y needs 2 |
| **Different tech stacks per domain** | ML team needs Python; API team uses Go |
| **Team autonomy** at scale (50+ engineers) | Ownership boundaries = team boundaries |

### Reasons that DON'T justify microservices

| Non-reason | Why |
|------------|-----|
| "It's modern" | Complexity for complexity's sake |
| "Monoliths don't scale" | They do — most services are I/O bound, not compute bound |
| "Separation of concerns" | Modules/packages achieve this without the network |
| Team < 10 engineers | Coordination overhead > autonomy benefit |

**Default: modular monolith.** Extract services when operational need is clear. The cost of microservices (network, latency, observability, deployment) is paid up front; the benefits come later.

---

## Service Decomposition

### By bounded context (DDD)

Each service owns one bounded context with its own data.

```
Order Service → orders DB
Payment Service → payments DB
Inventory Service → inventory DB
```

1. **Each service owns its data.** No shared databases. If Service A needs Service B's data, it calls B's API or subscribes to B's events.

2. **Bounded context = team boundary.** The team that owns the service owns the domain, the data, and the deployment.

### Service size heuristic

3. **A service should be replaceable in 2 weeks.** If it's bigger, it's doing too much. If it's smaller, the overhead isn't worth it.

---

## Communication Patterns

### Synchronous (request/response)

| Protocol | When |
|----------|------|
| **REST (HTTP/JSON)** | Public APIs, simple CRUD, browser-facing |
| **gRPC** | Internal service-to-service, performance-sensitive, streaming |

### Asynchronous (events/messages)

| Pattern | When |
|---------|------|
| **Event stream (Kafka)** | Broadcast, audit trail, many consumers |
| **Message queue (RabbitMQ/SQS)** | Task distribution, work queue |

4. **Sync for queries, async for commands.** "Get order status" = sync call. "Process payment" = async event.
5. **Prefer async for cross-service writes.** Reduces coupling and handles failures more gracefully.

See [`event-driven-architecture`](../event-driven-architecture/SKILL.md) for event patterns.

---

## Resilience Patterns

### Circuit Breaker

When a downstream service fails, stop calling it and fail fast.

```
Closed (normal) → errors exceed threshold → Open (fail fast)
Open → after timeout → Half-Open (probe with one request)
Half-Open → success → Closed  |  failure → Open
```

6. **Use circuit breakers on all cross-service calls.** Libraries: `sony/gobreaker` (Go).

### Retry with Backoff

```go
backoff := time.Second
for attempt := 0; attempt < maxRetries; attempt++ {
    err := call(ctx)
    if err == nil { return nil }
    time.Sleep(backoff)
    backoff *= 2
}
```

7. **Only retry on transient errors.** Don't retry 400s, auth failures, or permanent conditions.
8. **Add jitter.** Prevents thundering herd: `backoff + rand(0, backoff/2)`.

### Timeout

9. **Every cross-service call has a timeout.** No exceptions. Use `context.WithTimeout`.
10. **Timeouts cascade.** If Service A calls B with 5s timeout, B calls C with 3s. Never longer than the parent.

### Bulkhead

Isolate failures so one slow dependency doesn't consume all resources.

- **Thread pool / goroutine pool per dependency** — slow calls can't starve the whole service.
- **Connection limits per downstream** — prevent one service from monopolizing DB connections.

---

## API Gateway

Single entry point for external clients:

```
Client → API Gateway → Service A
                     → Service B
                     → Service C
```

Responsibilities: routing, auth, rate limiting, TLS termination, request transformation.

11. **Don't put business logic in the gateway.** It's infrastructure, not a service.
12. **For internal service-to-service calls, skip the gateway.** Direct communication is simpler and faster.

---

## Service Discovery

Services need to find each other dynamically.

| Approach | When |
|----------|------|
| **DNS-based** (Kubernetes service names) | K8s environments (default choice) |
| **Service registry** (Consul, etcd) | Non-K8s, dynamic membership |
| **Static config** | Simple setups, few services |

13. **If you're on Kubernetes, use Kubernetes DNS.** No additional service discovery needed.

---

## Data Management

14. **Database per service.** Shared databases create tight coupling that defeats microservices.
15. **Cross-service joins don't exist.** Denormalize, use events to sync read models, or make an API call.
16. **Eventual consistency is the default.** Accept it. Design UIs to show "processing" states.
17. **Distributed transactions: use Saga pattern, not 2PC.** Two-phase commit doesn't work well across services. See event-driven-architecture.

---

## 12-Factor App (Condensed)

| Factor | Rule |
|--------|------|
| Codebase | One repo per service (or monorepo with clear boundaries) |
| Dependencies | Explicitly declared (go.mod, package.json) |
| Config | Environment variables, not hardcoded |
| Backing services | Treat DB, cache, queue as attached resources |
| Build/release/run | Strict separation; immutable releases |
| Processes | Stateless; store state in external services |
| Port binding | Service exports HTTP via port binding |
| Concurrency | Scale out via process model |
| Disposability | Fast startup, graceful shutdown |
| Dev/prod parity | Keep environments as similar as possible |
| Logs | Treat as event streams (stdout) |
| Admin processes | One-off tasks run as processes, not SSH |

---

## Observability in Microservices

18. **Distributed tracing is non-negotiable.** Without it, debugging a request across 5 services is impossible.
19. **Correlation IDs propagate through all calls.** HTTP headers (`X-Request-ID`, `traceparent`), message metadata.
20. **Centralized logging.** Every service logs to the same system (ELK, Datadog, Loki).
21. **Service-level dashboards.** Each service: request rate, error rate, latency (RED).

See [`observability-go`](../observability-go/SKILL.md).

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Shared database across services | Database per service |
| "Distributed monolith" (services tightly coupled) | If they always deploy together, merge them |
| Nano-services (50-line services) | Merge until "replaceable in 2 weeks" |
| Synchronous chain (A→B→C→D) for writes | Async events for cross-service commands |
| No circuit breaker | Add for all cross-service calls |
| No timeout | `context.WithTimeout` on every external call |
| Business logic in API gateway | Gateway is infra only |
| "Microservices first" for a 3-person team | Start monolith; extract when needed |

---

## Decision Checklist

Before going microservices:

- [ ] Team is > 10 engineers or scaling toward it
- [ ] Clear bounded contexts identified (DDD)
- [ ] Independent deployment is a real need
- [ ] Observability infrastructure exists (tracing, logging, metrics)
- [ ] CI/CD can handle N services
- [ ] Team understands eventual consistency trade-offs
- [ ] Operational overhead (monitoring, deploy, debug) is budgeted

---

## Related Skills

- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — bounded contexts define service boundaries
- [`event-driven-architecture`](../event-driven-architecture/SKILL.md) — async communication between services
- [`api-design-rest`](../api-design-rest/SKILL.md) — sync API design for service interfaces
- [`api-design-grpc`](../api-design-grpc/SKILL.md) — high-performance internal communication
- [`observability-go`](../observability-go/SKILL.md) — distributed tracing across services
