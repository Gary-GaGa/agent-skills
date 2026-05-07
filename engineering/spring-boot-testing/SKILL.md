---
name: spring-boot-testing
description: >
  Testing Spring Boot applications — slice tests (@WebMvcTest, @DataJpaTest),
  full-context @SpringBootTest, MockMvc / WebTestClient, Testcontainers for
  real PostgreSQL/Pub-Sub, and test data builders. Use this skill when writing
  or reviewing tests for a Java Spring Boot service.
category: engineering
tags: [java, spring-boot, testing, tdd, quality, backend]
keywords: ["@SpringBootTest", "@WebMvcTest", "@DataJpaTest", MockMvc, WebTestClient, Testcontainers, JUnit 5, AssertJ, Mockito, "@MockBean"]
related: [spring-boot-fundamentals, java-restful-api, spring-data-jpa]
---

# Spring Boot Testing

> Slice when you can, boot when you must, container when it's a database.

## When to Use This Skill

- Adding a new test to a Spring Boot service
- Reviewing whether a test should be a slice test or a full `@SpringBootTest`
- Replacing in-memory H2 with Testcontainers PostgreSQL
- Speeding up a slow test suite
- Writing tests for controllers, repositories, or HTTP clients

---

## The Testing Pyramid for Spring Boot

```
       ┌──────────────────────────┐
       │  E2E / @SpringBootTest    │  few; full app + Testcontainers
       └──────────────────────────┘
       ┌──────────────────────────┐
       │  Slice tests              │  more; @WebMvcTest, @DataJpaTest
       └──────────────────────────┘
       ┌──────────────────────────┐
       │  Plain unit tests         │  most; no Spring context
       └──────────────────────────┘
```

1. **Default to plain JUnit + Mockito** for services and domain logic. Constructor injection makes this trivial — no Spring needed.

2. **Use slice tests for adapter layers** (controllers, repositories, HTTP clients). They load only the beans they need and run fast.

3. **Use `@SpringBootTest` sparingly** — only when you genuinely need the full wired app (smoke test, end-to-end happy path).

---

## Plain Unit Tests (No Spring)

```java
class OrderServiceTest {

    @Test
    void rejectsOrderWhenStockIsZero() {
        InventoryClient inventory = mock(InventoryClient.class);
        OrderRepository repo = mock(OrderRepository.class);
        when(inventory.stockOf(productId)).thenReturn(0);

        OrderService service = new OrderService(repo, inventory);

        assertThatThrownBy(() -> service.create(commandFor(productId, 1)))
            .isInstanceOf(OutOfStockException.class);

        verifyNoInteractions(repo);
    }
}
```

4. **No `@ExtendWith(SpringExtension.class)` here.** It's a pure JUnit test. Spring adds nothing.

5. **AssertJ for fluent assertions.** Comes with `spring-boot-starter-test`. Use `assertThat(...)`, not `assertEquals(...)`.

6. **Mockito for collaborators.** `@MockBean` is for slice tests; for plain tests, just `mock(Foo.class)`.

---

## `@WebMvcTest` — Controller Slice

```java
@WebMvcTest(OrderController.class)
@Import(GlobalExceptionHandler.class)
class OrderControllerTest {

    @Autowired MockMvc mvc;
    @MockBean OrderService service;

    @Test
    void createsOrderAndReturns201WithLocation() throws Exception {
        when(service.create(any())).thenReturn(new Order(orderId, "Alice", PENDING, BigDecimal.TEN, Instant.now()));

        mvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "customerName": "Alice",
                      "lines": [{"productId": "%s", "quantity": 2}]
                    }
                    """.formatted(productId)))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", endsWith("/api/v1/orders/" + orderId)))
            .andExpect(jsonPath("$.id").value(orderId.toString()))
            .andExpect(jsonPath("$.status").value("PENDING"));
    }

    @Test
    void returnsProblemDetailOnValidationFailure() throws Exception {
        mvc.perform(post("/api/v1/orders")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
            .andExpect(status().isBadRequest())
            .andExpect(content().contentType(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.title").value("Validation failed"))
            .andExpect(jsonPath("$.errors[*].field", hasItem("customerName")));
    }
}
```

7. **`@WebMvcTest` only loads the web layer.** No JPA, no service beans. Mock dependencies with `@MockBean`.

8. **`@Import(GlobalExceptionHandler.class)`** — `@WebMvcTest` doesn't pick up your `@RestControllerAdvice` automatically. Import it or your error tests won't reflect production behaviour.

9. **MockMvc, not real HTTP.** Faster than `RestTemplate` against an embedded server, and lets you assert on the rendered response.

10. **For WebFlux**, use `@WebFluxTest` and `WebTestClient` instead.

---

## `@DataJpaTest` — Repository Slice

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired OrderRepository repo;

    @Test
    void findsByStatus() {
        repo.save(new OrderEntity(UUID.randomUUID(), "Alice", PENDING));
        repo.save(new OrderEntity(UUID.randomUUID(), "Bob", PAID));

        List<OrderEntity> pending = repo.findByStatus(PENDING);

        assertThat(pending).hasSize(1).extracting("customerName").containsExactly("Alice");
    }
}
```

11. **Don't use H2 for tests if production uses PostgreSQL.** SQL dialects diverge; you'll miss bugs that only show up in prod. Use Testcontainers.

12. **`@AutoConfigureTestDatabase(replace = NONE)`** — required to keep `@DataJpaTest` from swapping in an in-memory DB.

13. **One `static` container shared across tests in the class.** Spinning up Postgres per-test is too slow. Combine with `@DirtiesContext` only when you must.

14. **`@Sql` for fixture loading**:
    ```java
    @Test
    @Sql("/fixtures/orders.sql")
    void findsByStatus() { ... }
    ```

---

## `@SpringBootTest` — Full Context

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
@ActiveProfiles("test")
class OrderEndToEndTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        // ...
    }

    @Autowired TestRestTemplate rest;
    @MockBean PaymentClient paymentClient;

    @Test
    void placesAndPaysOrder() {
        when(paymentClient.charge(any())).thenReturn(new PaymentResult(SUCCESS, "txn-1"));

        ResponseEntity<OrderResponse> created = rest.postForEntity("/api/v1/orders", request, OrderResponse.class);
        assertThat(created.getStatusCode()).isEqualTo(HttpStatus.CREATED);

        ResponseEntity<OrderResponse> paid = rest.postForEntity(
            "/api/v1/orders/" + created.getBody().id() + "/pay", null, OrderResponse.class);
        assertThat(paid.getBody().status()).isEqualTo(OrderStatus.PAID);
    }
}
```

15. **`webEnvironment = RANDOM_PORT`** boots a real server on a random port. Use `TestRestTemplate` or `WebTestClient` to call it.

16. **Mock external integrations.** Don't call real Stripe / Pub/Sub / SendGrid in tests. `@MockBean` replaces the bean in the context.

17. **Use `@SpringBootTest` for the golden path only.** Edge cases belong in slice tests where they run faster.

---

## Test Data Builders

```java
public final class OrderFixture {

    public static CreateOrderRequest aValidRequest() {
        return new CreateOrderRequest("Alice", List.of(aLine()), "alice@example.com");
    }

    public static OrderLineRequest aLine() {
        return new OrderLineRequest(UUID.randomUUID(), 2);
    }

    public static OrderEntity persisted(EntityManager em) {
        var entity = new OrderEntity(UUID.randomUUID(), "Alice", PENDING);
        em.persist(entity);
        em.flush();
        return entity;
    }
}
```

18. **Builders > random object factories** for clarity. Avoid `EasyRandom`-style "make me anything" — tests become hard to debug.

19. **Static factory methods named `aXxx`** read well: `aValidRequest()`, `aPaidOrder()`.

---

## Running Tests

```bash
./gradlew test                  # run all
./gradlew test --tests "*Order*"  # filter
./gradlew test -i               # info-level output
```

20. **Parallel execution.** JUnit 5 supports it via `junit-platform.properties`:
    ```
    junit.jupiter.execution.parallel.enabled=true
    junit.jupiter.execution.parallel.mode.default=concurrent
    ```
    Slice tests parallelise well; `@SpringBootTest` classes need separate JVM forks if they share state.

21. **Reuse the Spring context.** Boot caches contexts across test classes that share `@SpringBootTest` config. Don't add `@DirtiesContext` reflexively — it kills the cache.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `@WebMvcTest` returns 200 for an invalid body | Forgot `@Import(GlobalExceptionHandler.class)` |
| Tests pass locally, fail in CI with "context failed to load" | Missing `@ActiveProfiles` or test-only `application-test.yml`; check for env vars |
| H2 test passes, prod fails on Postgres-specific SQL | Switch to Testcontainers |
| Each test boots a new context (slow) | Shared `@TestConfiguration` and avoid `@DirtiesContext` |
| `@MockBean` not replacing the bean | Bean defined in a `@TestConfiguration` after the prod bean wins; use `@MockBean` not `@TestConfiguration`-defined mocks |
| `LocalDateTime.now()` makes tests flaky | Inject a `Clock` bean; use `Clock.fixed(...)` in tests |

---

## Checklist

- [ ] Plain unit tests for services / domain (no Spring)
- [ ] `@WebMvcTest` + MockMvc for controllers, with `@Import` of advice
- [ ] `@DataJpaTest` + Testcontainers Postgres for repositories
- [ ] One `@SpringBootTest` golden-path test per service
- [ ] AssertJ assertions, Mockito mocks
- [ ] Test fixtures via builders, not random object generators
- [ ] No real external services hit during tests
- [ ] CI runs the full suite with the same Postgres version as prod

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — what's being tested
- [`java-restful-api`](../java-restful-api/SKILL.md) — controllers under `@WebMvcTest`
- [`spring-data-jpa`](../spring-data-jpa/SKILL.md) — repositories under `@DataJpaTest`
