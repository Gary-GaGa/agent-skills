---
name: spring-boot-fundamentals
description: >
  Spring Boot fundamentals — project structure, auto-configuration,
  profiles, configuration binding, Actuator, and graceful shutdown. Use
  this skill when starting a Spring Boot service, choosing between Spring
  MVC and WebFlux, wiring beans, or hardening a Boot app for production.
category: engineering
tags: [java, spring-boot, backend, design]
keywords: [Spring Boot, Spring MVC, WebFlux, Actuator, application.yml, "@SpringBootApplication", profiles, Maven, Gradle]
related: [java-restful-api, spring-boot-testing, spring-data-jpa, openapi-swagger-spring, gcp-cloud-sql-spring, gcp-firestore-spring, gcp-observability-spring, gcp-pubsub-spring, spring-ai-rag]
---

# Spring Boot Fundamentals

> Boot turns Java services from "weeks of XML" into "one main method" — but only if you stop fighting the conventions.

## When to Use This Skill

- Bootstrapping a new Java backend service (Spring Boot 3.x on Java 17/21)
- Deciding between Spring MVC (servlet) and WebFlux (reactive)
- Wiring beans, profiles, and externalised configuration
- Adding Actuator endpoints, health checks, and graceful shutdown
- Reviewing a Boot project for sane structure before deploying to GKE

---

## Pick Your Stack

| Choice | Default | Notes |
|---|---|---|
| Boot version | **3.2+** | Requires Java 17+. Boot 3.x = Jakarta EE namespace (`jakarta.*`, not `javax.*`). |
| JDK | **Java 21 LTS** | Use 17 only if a dependency forces it. |
| Build tool | **Gradle (Kotlin DSL)** | Maven is fine if the team prefers XML and wider plugin ecosystem. |
| Web stack | **Spring MVC** | WebFlux only if you need non-blocking I/O end-to-end (event streams, very high fan-out). Mixing JPA + WebFlux is usually wrong — JPA is blocking. |
| JSON | Jackson (default) | Don't swap unless you have a reason. |

---

## Project Layout

```
src/
├── main/
│   ├── java/com/acme/orders/
│   │   ├── OrdersApplication.java        ← @SpringBootApplication entry point
│   │   ├── config/                       ← @Configuration classes, beans
│   │   ├── web/                          ← @RestController, DTOs, advice
│   │   ├── domain/                       ← entities, value objects, domain services
│   │   ├── application/                  ← use cases / app services
│   │   └── infrastructure/               ← JPA repos, GCP clients, adapters
│   └── resources/
│       ├── application.yml               ← shared defaults
│       ├── application-local.yml         ← profile overrides
│       ├── application-prod.yml
│       └── db/migration/                 ← Flyway scripts
└── test/
    └── java/com/acme/orders/
        └── ...                            ← mirror main package layout
```

1. **One `@SpringBootApplication` per service.** Place it at the root package. Component scan starts from this package — anything outside it won't be picked up.

2. **Package by feature, not by layer at the top level.** `com.acme.orders.payment.*` beats `com.acme.orders.controller.*` once the service has more than ~10 classes. Inside each feature, layer-by-folder is fine.

---

## `@SpringBootApplication` and Auto-Configuration

```java
@SpringBootApplication
public class OrdersApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrdersApplication.class, args);
    }
}
```

`@SpringBootApplication` = `@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan`.

3. **Trust auto-config.** If a Boot starter is on the classpath, assume it's wired. Don't write `DataSource` beans by hand unless you need to override.

4. **To debug auto-config**, run with `--debug` or hit `/actuator/conditions` (when Actuator is enabled). It shows what was applied and what was skipped and why.

5. **Exclude an auto-config** when it conflicts:
   ```java
   @SpringBootApplication(exclude = SecurityAutoConfiguration.class)
   ```

---

## Bean Wiring

### Constructor injection only

```java
@Service
public class OrderService {
    private final OrderRepository repo;
    private final PaymentClient payments;

    public OrderService(OrderRepository repo, PaymentClient payments) {
        this.repo = repo;
        this.payments = payments;
    }
}
```

6. **Always constructor injection.** Never `@Autowired` on fields. Constructor injection makes dependencies explicit, enables `final`, and works in plain unit tests without Spring.

7. **One constructor → no `@Autowired` annotation needed.** Boot 3 picks it automatically.

8. **`@Component` / `@Service` / `@Repository` / `@Controller` are equivalent for DI.** Use the one that signals intent. `@Repository` adds JPA exception translation.

9. **`@Configuration` + `@Bean` for things you don't own.** Third-party clients, GCP SDK beans, etc.:
   ```java
   @Configuration
   public class GcpConfig {
       @Bean
       public Storage storage() {
           return StorageOptions.getDefaultInstance().getService();
       }
   }
   ```

10. **Avoid `@Lazy` and circular dependencies.** If beans depend on each other, the design is wrong — extract a third bean.

---

## Configuration

### `application.yml` over `.properties`

Tree structure scales. Pick one format, use it everywhere.

```yaml
server:
  port: 8080
  shutdown: graceful

spring:
  application:
    name: orders
  datasource:
    url: ${DB_URL}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate

app:
  payment:
    timeout: PT5S
    retry-attempts: 3
```

### Type-safe binding with `@ConfigurationProperties`

```java
@ConfigurationProperties(prefix = "app.payment")
public record PaymentProperties(Duration timeout, int retryAttempts) {}
```

```java
@SpringBootApplication
@EnableConfigurationProperties(PaymentProperties.class)
public class OrdersApplication { ... }
```

11. **Use `@ConfigurationProperties` records, not `@Value` everywhere.** `@Value("${app.payment.timeout}")` scattered across 30 classes is unmaintainable; one bound record is.

12. **Never commit secrets to `application.yml`.** Use env vars (`${DB_PASSWORD}`) and pull from GCP Secret Manager in production. See `gcp-fundamentals`.

### Profiles

```bash
java -jar app.jar --spring.profiles.active=prod
# or
SPRING_PROFILES_ACTIVE=prod java -jar app.jar
```

13. **Profile names: `local`, `dev`, `staging`, `prod`.** Don't invent new ones per developer.

14. **`application-{profile}.yml` overrides `application.yml`.** Keep `application.yml` for shared defaults; put environment-specific values in profile files.

15. **Don't put `prod` secrets in `application-prod.yml`.** That file ships in the JAR. Inject from env / Secret Manager.

---

## Actuator (Production Endpoints)

Add `spring-boot-starter-actuator`. Then:

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health, info, metrics, prometheus
  endpoint:
    health:
      probes:
        enabled: true
      show-details: when-authorized
  health:
    livenessstate:
      enabled: true
    readinessstate:
      enabled: true
```

16. **Expose only what's needed in production.** `/actuator/env` and `/actuator/configprops` leak config — keep them off in prod or behind auth.

17. **Use Kubernetes probes.** Boot exposes `/actuator/health/liveness` and `/actuator/health/readiness` automatically — wire them in your `Deployment` (see `gke-deployment`).

18. **Expose `/actuator/prometheus`** for scraping (with `micrometer-registry-prometheus` on the classpath). See `observability-spring`.

---

## Graceful Shutdown

```yaml
server:
  shutdown: graceful

spring:
  lifecycle:
    timeout-per-shutdown-phase: 30s
```

19. **Always enable graceful shutdown for K8s.** On `SIGTERM`, Boot stops accepting new requests but lets in-flight ones finish (up to the timeout). Without it, you'll see 502s during rolling deploys.

---

## Logging

Boot uses Logback by default with a pre-configured pattern.

20. **Use SLF4J in code; never `System.out.println`.**
    ```java
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    log.info("Order {} placed by {}", orderId, userId);
    ```

21. **Use placeholders (`{}`), not string concatenation.** Avoids cost when the level is disabled.

22. **For GCP, switch to JSON logging** so Cloud Logging parses fields. See `observability-spring`.

---

## Common Starters

| Starter | What it pulls in |
|---|---|
| `spring-boot-starter-web` | Spring MVC, embedded Tomcat, Jackson |
| `spring-boot-starter-webflux` | Reactive stack — only if going non-blocking end-to-end |
| `spring-boot-starter-data-jpa` | Hibernate + JPA + HikariCP |
| `spring-boot-starter-validation` | Bean Validation (Jakarta) — needed for `@Valid` |
| `spring-boot-starter-security` | Spring Security — auth filter chain |
| `spring-boot-starter-actuator` | Health, metrics, info endpoints |
| `spring-boot-starter-test` | JUnit 5, Mockito, AssertJ, Testcontainers integration |
| `springdoc-openapi-starter-webmvc-ui` | OpenAPI 3 + Swagger UI (third-party, not Spring) |
| `spring-cloud-gcp-starter` | GCP integration base — credentials, project ID |

---

## Minimal Hello-World Service

```java
@RestController
@RequestMapping("/api/v1/health")
public class HealthController {

    @GetMapping
    public Map<String, String> ping() {
        return Map.of("status", "ok");
    }
}
```

```java
@SpringBootApplication
public class OrdersApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrdersApplication.class, args);
    }
}
```

```bash
./gradlew bootRun
curl http://localhost:8080/api/v1/health
# {"status":"ok"}
```

---

## Pre-Production Checklist

- [ ] Java 21, Boot 3.2+
- [ ] `@SpringBootApplication` at root package
- [ ] Constructor injection only — no `@Autowired` fields
- [ ] `@ConfigurationProperties` for typed config
- [ ] Profiles: `local`, `dev`, `staging`, `prod`; no secrets in profile files
- [ ] `server.shutdown: graceful` enabled
- [ ] Actuator health probes wired (`/actuator/health/liveness`, `/readiness`)
- [ ] Sensitive Actuator endpoints not exposed publicly
- [ ] SLF4J logging only; JSON format in prod
- [ ] Build produces a slim layered JAR or distroless image (see `docker-basics`)

---

## Related Skills

- [`java-restful-api`](../java-restful-api/SKILL.md) — controller, DTO, validation, error handling
- [`spring-boot-testing`](../spring-boot-testing/SKILL.md) — slice tests, Testcontainers, MockMvc
- [`spring-data-jpa`](../spring-data-jpa/SKILL.md) — persistence layer
- [`openapi-swagger-spring`](../openapi-swagger-spring/SKILL.md) — API contract & docs
- [`gke-deployment`](../../devops/gke-deployment/SKILL.md) — deploying the resulting image
