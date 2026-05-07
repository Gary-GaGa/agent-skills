---
name: spring-data-jpa
description: >
  Persistence with Spring Data JPA and Hibernate — entities, repositories,
  transactions, fetch strategies, N+1 prevention, and Flyway migrations.
  Use this skill when modeling domain persistence, writing JPA
  repositories, or diagnosing slow queries in a Spring Boot service.
category: engineering
tags: [java, spring-boot, jpa, hibernate, database, postgresql, backend, sql]
keywords: [Spring Data JPA, Hibernate, "@Entity", "@Transactional", JpaRepository, EntityGraph, Flyway, Liquibase, HikariCP, "N+1"]
related: [spring-boot-fundamentals, spring-boot-testing, gcp-cloud-sql-spring]
---

# Spring Data JPA

> JPA gives you a free abstraction over SQL — and a free way to ship N+1 queries. Pay attention to fetching, transactions, and the SQL that actually runs.

## When to Use This Skill

- Modeling persistence for a Spring Boot service backed by PostgreSQL/MySQL
- Writing or reviewing `@Entity` and `JpaRepository` definitions
- Diagnosing slow queries, lazy-loading exceptions, or N+1 problems
- Setting up Flyway or Liquibase migrations
- Tuning HikariCP for production load

---

## Stack Defaults

| Choice | Default |
|---|---|
| ORM | Hibernate (bundled with `spring-boot-starter-data-jpa`) |
| Pool | HikariCP (default) |
| Database | PostgreSQL 15+ (Cloud SQL on GCP) |
| Migrations | **Flyway** (simpler) — Liquibase if you need branching/rollback |
| ID | `UUID` (application-generated) — easier across services than DB sequences |

---

## Dependencies

```gradle
implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
implementation 'org.flywaydb:flyway-core'
implementation 'org.flywaydb:flyway-database-postgresql'
runtimeOnly    'org.postgresql:postgresql'
```

```yaml
spring:
  datasource:
    url: jdbc:postgresql://${DB_HOST}:5432/${DB_NAME}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    hikari:
      maximum-pool-size: 10
      minimum-idle: 2
      connection-timeout: 3000
  jpa:
    hibernate:
      ddl-auto: validate
    open-in-view: false
    properties:
      hibernate:
        jdbc.time_zone: UTC
        format_sql: true
  flyway:
    enabled: true
    locations: classpath:db/migration
```

1. **`ddl-auto: validate` in non-local environments.** Never `update` or `create-drop`. Schema changes go through Flyway.

2. **`open-in-view: false`** always. The default `true` keeps the persistence context open across the whole HTTP request — masks lazy-loading bugs and holds DB connections far too long.

3. **`spring.jpa.show-sql: true` is for local debugging only.** Use a logger filter in CI/prod (see "Logging SQL" below).

---

## Entities

```java
@Entity
@Table(name = "orders")
public class OrderEntity {

    @Id
    private UUID id;

    @Column(name = "customer_name", nullable = false, length = 100)
    private String customerName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private OrderStatus status;

    @Column(nullable = false)
    private BigDecimal total;

    @Version
    private long version;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true,
               fetch = FetchType.LAZY)
    private List<OrderLineEntity> lines = new ArrayList<>();

    protected OrderEntity() {}  // JPA

    public OrderEntity(UUID id, String customerName, BigDecimal total) {
        this.id = id;
        this.customerName = customerName;
        this.total = total;
        this.status = OrderStatus.PENDING;
        this.createdAt = Instant.now();
    }

    // getters; behavior methods (e.g. cancel(), addLine(...))
}
```

4. **`@Enumerated(EnumType.STRING)` always.** Default is `ORDINAL` — the integer is brittle to enum reordering and unreadable in SQL.

5. **`@Version` for optimistic locking** on entities that are updated concurrently. Hibernate increments it; concurrent updates fail with `OptimisticLockingFailureException`.

6. **No `@OneToMany(fetch = EAGER)`.** Eager joins on collections are the #1 source of cartesian explosions. Default is lazy; load explicitly when you need the data.

7. **`mappedBy` on the inverse side**, not a second join column. Otherwise Hibernate creates an extra link table or duplicate FK.

8. **JPA needs a no-arg constructor.** Make it `protected` so domain code can't accidentally construct an empty entity.

9. **Application-generated UUIDs over DB sequences.** No round-trip to fetch the ID; works across sharded / multi-region deployments.

---

## Repositories

```java
public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {

    List<OrderEntity> findByStatus(OrderStatus status);

    @Query("select o from OrderEntity o where o.customerName like :name%")
    Page<OrderEntity> searchByCustomer(@Param("name") String name, Pageable pageable);

    @EntityGraph(attributePaths = "lines")
    Optional<OrderEntity> findWithLinesById(UUID id);

    @Modifying
    @Query("update OrderEntity o set o.status = :status where o.id = :id")
    int updateStatus(@Param("id") UUID id, @Param("status") OrderStatus status);
}
```

10. **Derived query names for simple cases** (`findByStatus`, `findByCustomerNameAndStatus`). Stop deriving once the name passes ~50 chars; switch to `@Query`.

11. **`@EntityGraph` for ad-hoc fetch joins** without changing the entity's default fetch type. Cleaner than `JOIN FETCH` strings.

12. **`@Modifying` on bulk updates/deletes.** Without it, JPA throws. Pair with `clearAutomatically = true` if the same transaction reads after the update.

13. **Return `Optional<T>`, not `null`,** for single-row finders — that's the Spring Data convention. Throw a domain `NotFoundException` in the service layer.

---

## Transactions

```java
@Service
public class OrderService {

    private final OrderRepository repo;

    public OrderService(OrderRepository repo) { this.repo = repo; }

    @Transactional
    public Order create(CreateOrderCommand cmd) {
        OrderEntity entity = new OrderEntity(UUID.randomUUID(), cmd.customerName(), cmd.total());
        cmd.lines().forEach(l -> entity.addLine(new OrderLineEntity(l.productId(), l.quantity())));
        return repo.save(entity).toDomain();
    }

    @Transactional(readOnly = true)
    public Order findById(UUID id) {
        return repo.findById(id)
            .map(OrderEntity::toDomain)
            .orElseThrow(() -> new OrderNotFoundException(id));
    }
}
```

14. **`@Transactional` on application services**, not repositories or controllers. The use case defines the boundary.

15. **`readOnly = true` for queries.** Hibernate skips dirty-checking and the connection can be routed to a replica when configured.

16. **`@Transactional` only works on Spring-managed beans called via the proxy.** Self-invocation (`this.foo()`) bypasses it. Extract to another bean if needed.

17. **Default propagation is `REQUIRED`.** Don't change it without a reason; nested transactions are rarely what you want.

18. **Default rollback is on `RuntimeException` only.** Checked exceptions don't roll back unless you add `rollbackFor = Exception.class`. Prefer unchecked domain exceptions.

---

## Avoiding N+1

The classic problem:

```java
List<OrderEntity> orders = repo.findAll();         // 1 query
orders.forEach(o -> o.getLines().size());          // N queries (lazy)
```

Fixes:

```java
// 1. Entity graph
@EntityGraph(attributePaths = "lines")
List<OrderEntity> findAll();

// 2. JPQL fetch join
@Query("select distinct o from OrderEntity o join fetch o.lines")
List<OrderEntity> findAllWithLines();

// 3. @BatchSize (predictable IN(...) batches when fetch joins are awkward)
@OneToMany(mappedBy = "order")
@BatchSize(size = 50)
private List<OrderLineEntity> lines;
```

19. **Default to `@EntityGraph`** for the simple case. Use fetch join when you also need filtering on the joined side.

20. **`distinct` is required when fetch-joining a collection.** Otherwise Hibernate returns one row per child × parent combination.

21. **Don't fetch-join two collections at once.** Cartesian product. Split into two queries or use `@BatchSize`.

22. **Pagination + fetch join on a collection issues a warning.** Hibernate fetches all rows into memory and paginates in-app. Paginate the parent first, then fetch children.

---

## DTO Projections

For read-heavy endpoints, skip the entity:

```java
public interface OrderSummary {
    UUID getId();
    String getCustomerName();
    OrderStatus getStatus();
    BigDecimal getTotal();
}

public interface OrderRepository extends JpaRepository<OrderEntity, UUID> {
    List<OrderSummary> findAllProjectedBy();
}
```

23. **Projection interfaces select only the columns they need.** Faster, no lazy-loading footguns. Use them for list/search endpoints.

24. **Don't return entities from controllers.** Map to a DTO at the service boundary (see [`java-restful-api`](../java-restful-api/SKILL.md)).

---

## Flyway Migrations

```
src/main/resources/db/migration/
  V1__create_orders.sql
  V2__add_total_to_orders.sql
  V3__add_status_index.sql
```

```sql
-- V1__create_orders.sql
CREATE TABLE orders (
    id           uuid PRIMARY KEY,
    customer_name varchar(100) NOT NULL,
    status        varchar(20) NOT NULL,
    total         numeric(12, 2) NOT NULL,
    version       bigint NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_orders_status ON orders (status);
```

25. **Filename: `V<version>__<snake_case_description>.sql`.** Two underscores between version and description.

26. **Migrations are immutable once merged.** A new requirement = a new file, never edit V3 after it's been applied somewhere.

27. **Run Flyway at app startup.** `spring.flyway.enabled: true` (default). For zero-downtime, keep migrations backward-compatible (additive) and split breaking changes across deploys.

28. **Test migrations in `@DataJpaTest` with Testcontainers** — same Postgres version as prod. See [`spring-boot-testing`](../spring-boot-testing/SKILL.md).

---

## HikariCP Tuning

| Knob | Default | Production starting point |
|---|---|---|
| `maximum-pool-size` | 10 | `min(2 * CPU, ~20)` per instance; size to DB capacity, not pod CPU |
| `minimum-idle` | same as max | 2–5; don't pin idle connections you don't need |
| `connection-timeout` | 30s | 3s — fail fast and let K8s retry |
| `idle-timeout` | 10min | OK |
| `max-lifetime` | 30min | Slightly less than DB's `wal_sender_timeout` / proxy idle limit |

29. **Pool size × replica count must fit your DB max connections.** Cloud SQL Postgres caps connections per instance — count them.

30. **Use a connection pooler (PgBouncer / Cloud SQL connector) at scale.** Hundreds of pods × 10 connections each will exhaust Postgres.

---

## Logging SQL

For local development:

```yaml
spring:
  jpa:
    properties:
      hibernate:
        format_sql: true

logging:
  level:
    org.hibernate.SQL: DEBUG
    org.hibernate.orm.jdbc.bind: TRACE   # parameter values (Hibernate 6)
```

31. **Don't enable `bind` logging in prod** — leaks PII. Use the SQL log without parameters, or rely on Cloud SQL query insights.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `LazyInitializationException` outside transaction | Either eager-fetch what you need with `@EntityGraph`, or map inside the transaction |
| `ddl-auto: update` "works on local" then drops a column in prod | Use Flyway; set `ddl-auto: validate` |
| Inserts return generated IDs slowly | Use application-generated UUIDs |
| `findAll()` loads 10M rows | Always paginate; never expose unbounded list endpoints |
| `@Transactional` annotation on a private method silently does nothing | Move to public; remember Spring proxies |
| Entity equals/hashCode breaks Set membership after persist | Implement equals/hashCode on a stable business key, not the auto-generated ID |
| `cascade = ALL` deletes children unexpectedly | Be explicit: only `PERSIST, MERGE` for most aggregates; `orphanRemoval` for owned collections |

---

## Checklist

- [ ] PostgreSQL (or matching prod DB) used in tests via Testcontainers
- [ ] `ddl-auto: validate`, Flyway runs migrations
- [ ] `open-in-view: false`
- [ ] `@Enumerated(EnumType.STRING)` everywhere
- [ ] Lazy by default; explicit `@EntityGraph` for fetch
- [ ] No N+1 in profiled hot paths
- [ ] Repositories return `Optional<T>` for single rows
- [ ] `@Transactional` on services; `readOnly = true` for queries
- [ ] HikariCP sized to DB capacity, not pod count
- [ ] No JPA entities exposed in controller responses

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — DataSource auto-config and profiles
- [`spring-boot-testing`](../spring-boot-testing/SKILL.md) — `@DataJpaTest` + Testcontainers
- [`gcp-cloud-sql-spring`](../gcp-cloud-sql-spring/SKILL.md) — Cloud SQL connectivity from Spring
- [`sql-fundamentals`](../../data/sql-fundamentals/SKILL.md) — what JPA generates under the hood
- [`database-migrations`](../../data/database-migrations/SKILL.md) — migration strategy
