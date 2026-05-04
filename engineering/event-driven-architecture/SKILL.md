---
name: event-driven-architecture
description: >
  Event-driven architecture patterns — message queues, event sourcing, CQRS,
  saga pattern, and eventual consistency. Use this skill when designing systems
  that communicate via events or messages, or when decoupling services in a
  distributed system. Language-agnostic with Go examples.
category: engineering
tags: [architecture, event-driven, messaging, cqrs, event-sourcing, saga]
related: [clean-ddd-go, microservices-patterns, api-design-grpc, realtime-websocket]
---

# Event-Driven Architecture

> Events decouple the "when" from the "what." The producer says "X happened"; consumers decide independently what to do about it.

## When to Use This Skill

- Designing async communication between services
- Choosing between sync (HTTP/gRPC) and async (events/messages)
- Implementing event sourcing or CQRS
- Handling distributed transactions (saga pattern)
- Reviewing a system for coupling and consistency issues

---

## Core Concepts

### Event vs Command vs Query

| Type | Direction | Semantics | Example |
|------|-----------|-----------|---------|
| **Event** | Broadcast | "Something happened" (past tense) | `OrderPlaced`, `PaymentFailed` |
| **Command** | Targeted | "Do something" (imperative) | `ChargePayment`, `ShipOrder` |
| **Query** | Targeted | "Tell me something" | `GetOrderStatus` |

Events are facts. They don't dictate what to do next — that's the consumer's decision.

### Message Queue vs Event Stream

| Pattern | Delivery | Example | When |
|---------|----------|---------|------|
| **Message Queue** | Each message consumed by one consumer | RabbitMQ, SQS | Task distribution, work queue |
| **Event Stream / Log** | Each event readable by many consumers | Kafka, NATS JetStream, Redpanda | Broadcast, replay, audit trail |

---

## When Events vs Sync Calls

| Use events when | Use sync calls when |
|-----------------|---------------------|
| Consumer can process later | Caller needs the result immediately |
| Multiple consumers need the same data | One specific service must respond |
| Decoupling is more important than latency | Strong consistency required |
| Failures should be retried independently | Transaction must be atomic |

**Default to sync (HTTP/gRPC) until you need decoupling.** Events add complexity (ordering, idempotency, monitoring).

---

## Event Design

### Structure

```json
{
  "event_id": "evt-a1b2c3",
  "event_type": "order.placed",
  "timestamp": "2025-01-15T14:30:00Z",
  "source": "order-service",
  "data": {
    "order_id": "ord-42",
    "customer_id": "cust-7",
    "total": 1500,
    "items": [...]
  },
  "metadata": {
    "correlation_id": "req-xyz",
    "version": 1
  }
}
```

### Rules

1. **Past tense naming.** `OrderPlaced`, not `PlaceOrder` (that's a command).
2. **Include enough data for consumers.** Don't force them to call back for details.
3. **But not too much.** Large payloads are expensive to transport and store.
4. **Version events.** Schema will evolve; `version` field lets consumers handle migrations.
5. **`event_id` is unique.** For idempotent processing.
6. **`correlation_id` links to the originating request.** Critical for tracing.

---

## Patterns

### Event Sourcing

Instead of storing current state, store the sequence of events that produced it.

```
Events: [OrderCreated, ItemAdded, ItemAdded, PaymentReceived, OrderShipped]
State: derive by replaying events
```

**Pros:** Full audit trail, can rebuild state at any point, natural fit for event-driven.
**Cons:** Complexity (snapshots needed for performance), eventual consistency, harder to query.

**Use when:** Audit trail is critical (finance, legal), or you need time-travel debugging.
**Avoid when:** Simple CRUD with no audit requirements.

### CQRS (Command Query Responsibility Segregation)

Separate the write model (commands) from the read model (queries).

```
Commands → Write Model → Events → Read Model → Queries
```

**Pros:** Read and write models optimized independently; scales reads independently.
**Cons:** Eventual consistency between models; two models to maintain.

**CQRS doesn't require Event Sourcing.** You can do CQRS with a normal DB + change data capture.

### Saga Pattern

Coordinate a distributed transaction across services without a single DB transaction.

#### Choreography (event-based)

```
OrderService: emit OrderPlaced
PaymentService: on OrderPlaced → charge → emit PaymentSucceeded
ShippingService: on PaymentSucceeded → ship → emit OrderShipped
```

Each service reacts independently. Compensating actions for failure:

```
PaymentService: on ShippingFailed → refund → emit PaymentRefunded
```

#### Orchestration (central coordinator)

```
SagaOrchestrator:
  1. call PaymentService.Charge()
  2. if ok → call ShippingService.Ship()
  3. if fail → call PaymentService.Refund()
```

| | Choreography | Orchestration |
|-|--------------|---------------|
| Coupling | Loosely coupled | Orchestrator is a single point |
| Visibility | Hard to see full flow | Orchestrator shows the full flow |
| Complexity | Grows with number of services | Concentrated in orchestrator |

7. **Start with orchestration.** It's easier to reason about and debug. Move to choreography only when the orchestrator becomes a bottleneck.

---

## Idempotent Consumers

Events may be delivered more than once (at-least-once delivery). Consumers must handle duplicates.

### Patterns

| Pattern | How |
|---------|-----|
| **Idempotency key** | Store `event_id` in a processed-events table; skip if seen |
| **Upsert** | Write operations are naturally idempotent (INSERT ON CONFLICT UPDATE) |
| **Version check** | Only apply if entity version matches expected |

8. **Design every consumer to be idempotent.** Assume at-least-once delivery always.

---

## Ordering

Most message systems guarantee ordering per partition/key, not globally.

9. **Partition by entity ID.** All events for `order-42` go to the same partition → ordered.
10. **Don't depend on global ordering** across different entities. It's not guaranteed and limits throughput.

---

## Error Handling

| Strategy | When |
|----------|------|
| **Retry with backoff** | Transient errors (network, timeout) |
| **Dead letter queue (DLQ)** | Permanent failures; human review |
| **Compensating action** | Saga step failed; undo previous steps |
| **Skip and alert** | Non-critical consumer; log and move on |

11. **Every consumer must have a DLQ strategy.** Poison messages that fail forever must not block the queue.

---

## Monitoring

| Metric | Why |
|--------|-----|
| Consumer lag | How far behind the consumer is |
| Processing rate | Events per second |
| Error rate | Failed processing attempts |
| DLQ depth | How many messages need human attention |
| End-to-end latency | Time from event publish to consumer ack |

12. **Alert on consumer lag.** Growing lag = consumer can't keep up or is stuck.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Events as remote procedure calls | Events are facts, not commands |
| Giant event payloads (100KB+) | Include IDs + essential data; consumers fetch details |
| No idempotency handling | Store event_id; skip duplicates |
| Global ordering dependency | Partition by entity; accept eventual consistency |
| No DLQ | Poison messages block all processing |
| Event schema changes without versioning | Version field + backward-compatible evolution |
| Using events for everything (even simple sync queries) | Use sync calls when latency matters |
| No monitoring on consumer lag | Silent failures accumulate |

---

## Checklist

- [ ] Events named in past tense with clear domain language
- [ ] Event schema includes id, type, timestamp, source, version
- [ ] Consumers are idempotent
- [ ] Partitioning strategy defined (typically by entity ID)
- [ ] DLQ configured for every consumer
- [ ] Consumer lag monitored and alerted
- [ ] Saga compensating actions defined for each step
- [ ] Event versioning strategy in place

---

## Related Skills

- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — domain events emerge from aggregate root transitions
- [`microservices-patterns`](../microservices-patterns/SKILL.md) — events are the primary inter-service communication
- [`api-design-grpc`](../api-design-grpc/SKILL.md) — sync alternative for request/response
