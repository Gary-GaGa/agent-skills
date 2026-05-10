---
name: gcp-firestore-spring
description: >
  Firestore in Native Mode from Spring Boot via Spring Cloud GCP — document
  modelling, repositories, transactions, security rules vs server-side
  access, and when not to choose Firestore. Use this skill when using
  Firestore as the primary or auxiliary store for a Spring backend.
category: engineering
tags: [java, spring-boot, gcp, firestore, database, nosql, document-db, integration]
keywords: [Firestore, Native mode, Datastore mode, FirestoreTemplate, "@Document", composite index, security rules, eventual consistency, document database]
related: [spring-boot-fundamentals, gcp-fundamentals, data-modeling, mongodb-go]
---

# Firestore from Spring Boot

> Firestore is fast and zero-ops — but it's a document store with hierarchical keys, capped queries, and per-document write throughput. Pick it for the right shape of data, not for "we don't want SQL".

## When to Use This Skill

- Modelling data for Firestore in a Spring Boot service
- Choosing between Firestore Native mode, Datastore mode, and Cloud SQL
- Writing repositories with Spring Cloud GCP's Firestore integration
- Designing collections, indexes, and transaction boundaries
- Diagnosing slow queries or hot-document write conflicts

For relational modelling, see [`gcp-cloud-sql-spring`](../gcp-cloud-sql-spring/SKILL.md). For broader NoSQL trade-offs, [`mongodb-go`](../mongodb-go/SKILL.md) covers similar mental models.

---

## When (Not) to Use Firestore

| Pick Firestore when | Pick something else when |
|---|---|
| Mostly key-based reads, simple equality / range filters | Multi-table joins, aggregate analytics |
| Mobile/web SDK clients reading directly with security rules | Strict relational integrity, FKs, complex constraints |
| Hierarchical data fits naturally (`tenants/{id}/orders/{id}`) | High write throughput on a single key (>1 write/sec/document) |
| You want serverless, no instance to size | You need stored procedures, triggers, or rich SQL |

1. **Firestore is great for "user profile + sub-collections" shapes**, not for an order-management backbone with reporting. Don't force it.

2. **Native mode** is the modern API (mobile SDKs, real-time listeners). **Datastore mode** is legacy compatibility — pick Native unless migrating an existing Datastore app.

3. **One-write-per-second-per-document soft limit.** A counter incremented per request will throttle. Use sharding or a different store.

---

## Setup

### Dependencies

```gradle
implementation 'com.google.cloud:spring-cloud-gcp-starter-data-firestore:5.6.0'
```

### Configuration

```yaml
spring:
  cloud:
    gcp:
      project-id: ${GOOGLE_CLOUD_PROJECT:acme-orders-prod}
      firestore:
        database-id: "(default)"
```

4. **Auth via ADC** (Workload Identity on GKE; `gcloud auth application-default login` locally).

5. **IAM**: app SA needs `roles/datastore.user` (yes, that's the role even for Firestore Native).

---

## Document Modelling

### Entity

```java
@Document(collectionName = "orders")
public record OrderDoc(
        @DocumentId String id,                    // Firestore document ID
        String customerName,
        OrderStatus status,
        BigDecimal total,
        Instant createdAt,
        List<OrderLineDoc> lines                  // embedded sub-array, not a sub-collection
) {}
```

6. **Two API surfaces in Spring Cloud GCP**: `FirestoreReactiveRepository` (Reactor / WebFlux-friendly) and `FirestoreTemplate` (blocking). For an MVC service stick with the template; for WebFlux use the reactive repository. Direct usage of the official Google `Firestore` client is fine when you want fewer abstractions.

7. **Embed small, bounded child collections** (≤ ~50 items per parent). Use sub-collections when children grow unbounded.

8. **Document size limit: 1 MiB.** That's plenty for most domain objects, restrictive for blobs — store binaries in GCS and reference them by URL.

### Sub-Collections vs Embedded Lists

```
orders/                                           ← top-level collection
  ord_42/                                         ← document
    customerName: "Alice"
    status: "PENDING"
    lines: [...]                                  ← embedded (small, fixed size)
    payments/                                     ← sub-collection (unbounded)
      pay_1/
      pay_2/
```

9. **Sub-collections are not loaded with the parent.** Each sub-collection read is a separate query — design for that round-trip cost.

10. **Hierarchical paths are an index, not just aesthetics.** Querying "all payments for order 42" is fast because the path is part of the key.

---

## Repositories

```java
public interface OrderRepository extends FirestoreReactiveRepository<OrderDoc> {
    Flux<OrderDoc> findByStatus(OrderStatus status);
    Flux<OrderDoc> findByCustomerNameAndStatus(String customerName, OrderStatus status);
    Mono<OrderDoc> findById(String id);
}
```

Service:

```java
@Service
public class OrderService {

    private final OrderRepository repo;
    public OrderService(OrderRepository repo) { this.repo = repo; }

    public Mono<OrderDoc> create(CreateOrderCommand cmd) {
        OrderDoc doc = new OrderDoc(UUID.randomUUID().toString(), cmd.customerName(),
                OrderStatus.PENDING, cmd.total(), Instant.now(), cmd.lines());
        return repo.save(doc);
    }
}
```

11. **`FirestoreReactiveRepository` returns `Mono`/`Flux`.** Don't `.block()` on them in an MVC request thread — use `FirestoreTemplate` instead. Match the abstraction to your stack: WebFlux end-to-end with reactive repos; MVC with the blocking template; lowest layer with the Google `Firestore` client.

12. **Derived queries are limited to equality, range, and array-contains.** No `OR` (well, limited), no `JOIN`, no aggregation across collections.

---

## Indexes

Firestore auto-indexes single-field equality and inequality. Anything else needs a **composite index**.

```yaml
# firestore.indexes.json (deployable via gcloud)
{
  "indexes": [
    {
      "collectionGroup": "orders",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "status",    "order": "ASCENDING" },
        { "fieldPath": "createdAt", "order": "DESCENDING" }
      ]
    }
  ]
}
```

```bash
gcloud firestore indexes composite create --file=firestore.indexes.json
```

13. **The first time you run a query that needs a composite index, Firestore returns an error with a one-click "create index" link.** Use it during local dev — but commit the resulting index definition to the repo so prod isn't surprised.

14. **Indexes cost storage and write throughput.** Each indexed field adds work to every write. Don't index fields you don't query on.

15. **`array-contains` is one query type, `array-contains-any` is another, only one per query.** Plan accordingly.

---

## Transactions

```java
public Mono<Void> markPaid(String orderId, String paymentId) {
    return firestore.runTransaction(tx -> {
        DocumentReference ref = firestore.collection("orders").document(orderId);
        return Mono.fromFuture(toCF(tx.get(ref)))
            .flatMap(snapshot -> {
                OrderDoc doc = snapshot.toObject(OrderDoc.class);
                if (doc.status() != OrderStatus.PENDING) {
                    return Mono.error(new IllegalStateException("Not pending"));
                }
                tx.update(ref, Map.of("status", OrderStatus.PAID, "paidAt", Instant.now()));
                return Mono.empty();
            }).then();
    });
}
```

16. **Transactions are read-then-write with optimistic concurrency.** If the read documents change between read and commit, the transaction retries (up to 5 times by default).

17. **Transactions span up to 500 documents.** Don't try to batch-update millions in one transaction.

18. **No transactions across databases.** Cross-DB consistency requires sagas or outbox patterns. See [`event-driven-architecture`](../event-driven-architecture/SKILL.md).

---

## Server-Side Access vs Security Rules

Firestore can be read directly by mobile/web SDKs governed by **security rules**. Spring backends bypass rules — they authenticate as a service account and have full access.

19. **Decide which clients read what.** Mixed access (web SDK + backend) is fine but you must keep both contracts clear:
   - SDK: governed by `firestore.rules`
   - Backend: governed by IAM + your service code

20. **Don't put business logic in security rules.** Rules check identity and shape; complex invariants belong in a backend or in Cloud Functions.

21. **Audit rules in CI.** `firebase emulators:exec --only firestore "npm test"` against rule unit tests.

---

## Listening for Real-Time Changes

```java
firestore.collection("orders")
    .whereEqualTo("status", "PENDING")
    .addSnapshotListener((snapshots, error) -> {
        if (error != null) { log.error("listen failed", error); return; }
        snapshots.getDocumentChanges().forEach(change -> {
            switch (change.getType()) {
                case ADDED -> handleNew(change.getDocument());
                case MODIFIED -> handleUpdated(change.getDocument());
                case REMOVED -> handleRemoved(change.getDocument());
            }
        });
    });
```

22. **Listeners are great for low-traffic dashboards and presence.** Don't run thousands of listeners per pod — connection count matters.

23. **For cross-service event flow, use Pub/Sub triggered from Firestore changes** (Cloud Functions / Eventarc), not direct listeners across services.

---

## Local Development

```bash
firebase emulators:start --only firestore
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

```yaml
# application-local.yml
spring:
  cloud:
    gcp:
      firestore:
        emulator:
          enabled: true
        host-port: localhost:8080
```

24. **Emulator data is in-memory by default.** `--export-on-exit` and `--import` to seed.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `FAILED_PRECONDITION: The query requires an index` | Create the composite index from the error link, commit `firestore.indexes.json` |
| Counter document hot — slow writes | Shard the counter (e.g. 10 sub-counters); aggregate on read |
| Large arrays make documents exceed 1 MiB | Move to sub-collection |
| Transaction retries on benign cases | Narrow the read in the transaction; large `tx.get` sets cause more conflicts |
| Mixing reactive and blocking code | Pick a lane; don't `.block()` reactive repos in request threads |
| Local emulator works, prod fails | Indexes only exist locally; create them in prod via `gcloud firestore indexes` |

---

## Pre-Production Checklist

- [ ] Firestore in Native mode (not Datastore mode)
- [ ] One DB per environment / project
- [ ] Composite indexes committed in `firestore.indexes.json`
- [ ] No "hot" documents (single document with high write rate)
- [ ] Document size budget respected; binaries in GCS
- [ ] Transactions kept small (< 500 documents, narrow reads)
- [ ] Security rules + tests if SDK clients access directly
- [ ] App SA has `roles/datastore.user` only
- [ ] Emulator wired into local profile

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — bean wiring, profiles
- [`gcp-fundamentals`](../../devops/gcp-fundamentals/SKILL.md) — IAM, Workload Identity
- [`data-modeling`](../../data/data-modeling/SKILL.md) — modelling principles, normalisation
- [`gcp-cloud-sql-spring`](../gcp-cloud-sql-spring/SKILL.md) — when relational is the better fit
- [`mongodb-go`](../mongodb-go/SKILL.md) — similar document-store decisions, in Go
