# Spring Boot Production Checklist

A compact list of things to verify before a Spring Boot 3.x service goes to production. Cross-references the [`spring-boot-fundamentals`](../engineering/spring-boot-fundamentals/SKILL.md) and [`spring-data-jpa`](../engineering/spring-data-jpa/SKILL.md) skills.

---

## Bootstrapping & Wiring

1. **`@SpringBootApplication` lives at the root package.** Component scan must reach every component you wrote.

2. **Constructor injection only.** No field `@Autowired`. All collaborators are `final`.

3. **No `@Lazy` to "fix" circular dependencies.** Cycles are a design smell — extract a third bean.

4. **One configuration class per concern.** `JacksonConfig`, `SecurityConfig`, `OpenApiConfig`. Don't dump unrelated `@Bean`s into a single class.

5. **`@ConfigurationProperties` records for typed config.** No `@Value("${...}")` scattered across services.

---

## Configuration & Profiles

6. **Profiles: `local`, `dev`, `staging`, `prod`.** No personal-developer profiles checked into source.

7. **`application.yml` holds shared defaults; `application-{profile}.yml` overrides.** No production secrets in either.

8. **Secrets come from env vars or Secret Manager**, never the JAR.

9. **Default `spring.profiles.active` is unset** — pods explicitly set it via env var.

---

## Web Layer

10. **`@RestController` over `@Controller` + `@ResponseBody` per method.**

11. **DTOs as Java records.** No JPA entities exposed in controller signatures.

12. **`@Valid` on every `@RequestBody`; `@Validated` on classes for path/query constraints.**

13. **One `@RestControllerAdvice` returns `ProblemDetail` for every error.** No leaked stack traces or SQL errors to clients.

14. **List endpoints return a wrapped `PageResponse`**, not Spring's raw `Page`.

15. **`Location` header on `201 Created`**, computed via `UriComponentsBuilder`.

---

## Persistence

16. **`spring.jpa.hibernate.ddl-auto: validate` everywhere except local.** Schema changes ship via Flyway/Liquibase.

17. **`spring.jpa.open-in-view: false`.** Always.

18. **`@Enumerated(EnumType.STRING)` on every enum field.** Default ordinal is brittle.

19. **`@Transactional` on application services**, not controllers or repositories.

20. **`@Transactional(readOnly = true)` for queries.** Especially when read replicas are in play.

21. **No `@OneToMany(fetch = EAGER)`.** Lazy by default; fetch explicitly with `@EntityGraph`.

22. **Application-generated UUIDs**, not DB-sequence IDs (unless there's a strong reason).

23. **HikariCP `maximum-pool-size × replicas ≤ DB max_connections`.** Do the math, not vibes.

24. **Migrations as a separate Job in K8s**, not on app startup.

---

## Resilience & Shutdown

25. **`server.shutdown: graceful`** with `spring.lifecycle.timeout-per-shutdown-phase: 30s`.

26. **Liveness and readiness probes wired to Actuator**: `/actuator/health/liveness`, `/actuator/health/readiness`.

27. **JVM honours container memory limits**: `-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError`.

28. **Timeouts configured on every outbound client.** `RestTemplate` / `WebClient` / `Feign` defaults are unbounded.

29. **Retries are explicit** (Resilience4j or Spring Retry); no infinite loops or unbounded queues.

---

## Security

30. **Spring Security applied even on internal services.** Never "just trust the cluster".

31. **Don't disable CSRF blanket-ly for stateless APIs without thinking.** Stateless JWT API + same-origin browser app still needs care.

32. **Don't expose Actuator's `env`, `configprops`, `loggers` publicly.** Limit to internal networks or admin roles.

33. **Use Bean Validation everywhere user input enters** — DTOs, headers, query params.

34. **No hand-rolled crypto.** Use Spring Security's password encoders, JWT libraries, etc.

---

## Observability

35. **Structured JSON logging in prod** (LogstashEncoder). Plaintext only in `local`/`dev`.

36. **No PII or secrets in logs.** Log identifiers, status, timing.

37. **`/actuator/prometheus` exposed; deployment annotated for scraping.**

38. **OpenTelemetry tracing wired** with sampling: 1.0 in dev, ~0.1 in prod.

39. **Trace ID and request ID in every log line**, not just incident-time grep keys.

---

## Testing

40. **Plain JUnit + Mockito for services**, not `@SpringBootTest`.

41. **`@WebMvcTest` for controllers**, with `@Import(GlobalExceptionHandler.class)`.

42. **`@DataJpaTest` + Testcontainers Postgres** — no H2 if production is Postgres.

43. **One `@SpringBootTest` golden-path test per service**, not 50.

44. **Test `Clock` is injected and fixed in time-sensitive tests.**

---

## Build & Image

45. **Java 21 LTS unless a dependency forces 17.**

46. **Spring Boot layered JAR or Jib distroless image.** No `latest` Tomcat as base.

47. **Image tagged with the immutable commit SHA**, not just `:main`.

48. **No `JAVA_OPTS` env var without `-XX:MaxRAMPercentage` set.**

---

## Pre-Merge Quick Audit

```
- [ ] Constructor injection, no field @Autowired
- [ ] @ConfigurationProperties for typed config
- [ ] DTOs (records), no entities in controller signatures
- [ ] @Valid + @RestControllerAdvice + ProblemDetail
- [ ] Flyway migrations; ddl-auto: validate
- [ ] open-in-view: false
- [ ] graceful shutdown + actuator probes
- [ ] HikariCP sized to DB capacity
- [ ] JSON logging, no secrets/PII
- [ ] Tests: slice + plain unit + one full-context smoke
```

If any line above is "no", flag it on the PR before approving.
