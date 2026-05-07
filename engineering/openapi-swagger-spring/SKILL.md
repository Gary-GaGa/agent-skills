---
name: openapi-swagger-spring
description: >
  OpenAPI 3 and Swagger UI for Spring Boot via springdoc-openapi —
  annotating controllers, generating the spec, securing the docs, and
  choosing between code-first and API-first workflows. Use this skill when
  documenting a Java REST API or generating client SDKs.
category: engineering
tags: [java, spring-boot, api, rest, openapi, api-docs, documentation, design]
keywords: [OpenAPI, Swagger, springdoc-openapi, "@Operation", "@Schema", "@ApiResponse", swagger-ui, openapi-generator, API-first]
related: [spring-boot-fundamentals, java-restful-api, api-design-rest]
---

# OpenAPI / Swagger for Spring Boot

> The contract is the API. Whether you write Java first or YAML first, only one source of truth wins.

## When to Use This Skill

- Adding live API docs to a Spring Boot service
- Generating a typed client SDK (TypeScript, Java, Go) from a Spring service
- Choosing between code-first (annotations → spec) and API-first (spec → code)
- Hardening Swagger UI before deploying to a production environment
- Auditing an existing service for missing or misleading API documentation

---

## Pick a Library: springdoc-openapi

For Spring Boot 3.x, use **springdoc-openapi**. It generates OpenAPI 3 from your controllers and serves Swagger UI.

```gradle
// Spring MVC
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.6.0'

// Spring WebFlux (only if you're on the reactive stack)
// implementation 'org.springdoc:springdoc-openapi-starter-webflux-ui:2.6.0'
```

After adding the starter:

| URL | Purpose |
|---|---|
| `/v3/api-docs` | OpenAPI 3 spec, JSON |
| `/v3/api-docs.yaml` | OpenAPI 3 spec, YAML |
| `/swagger-ui.html` | Swagger UI |

1. **Don't use `springfox`.** It hasn't been maintained for years and doesn't support Boot 3 / Jakarta. Springdoc is the supported choice.

---

## Code-First vs API-First

| Approach | Source of truth | When to pick |
|---|---|---|
| **Code-first** | Java annotations → spec generated at runtime | Single team owns both API and impl; spec rarely consumed externally; fast iteration |
| **API-first** | `openapi.yaml` checked in → server stubs and clients generated | Spec is a published contract; multiple clients (mobile/web/partners); you want PR review on contract changes |

2. **Default to code-first** unless you have an external consumer or a separate frontend team. The friction of regenerating stubs every change is real.

3. **Switch to API-first when** the OpenAPI spec is part of the deliverable (public API, SDK shipped to customers, contract testing across services).

---

## Code-First: Annotating a Controller

```java
@RestController
@RequestMapping("/api/v1/orders")
@Tag(name = "Orders", description = "Order lifecycle operations")
public class OrderController {

    @Operation(summary = "Create an order", description = "Creates a new order in PENDING state.")
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Created",
                headers = @Header(name = "Location", description = "URL of the new order")),
        @ApiResponse(responseCode = "400", description = "Validation failed",
                content = @Content(schema = @Schema(implementation = ProblemDetail.class))),
        @ApiResponse(responseCode = "409", description = "Idempotency conflict",
                content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    })
    @PostMapping
    public ResponseEntity<OrderResponse> create(
            @Parameter(description = "Idempotency key (UUID)", required = false)
            @RequestHeader(value = "Idempotency-Key", required = false) UUID idempotencyKey,
            @Valid @RequestBody CreateOrderRequest req) {
        // ...
    }

    @Operation(summary = "Get an order by ID")
    @ApiResponse(responseCode = "404", description = "Order not found",
            content = @Content(schema = @Schema(implementation = ProblemDetail.class)))
    @GetMapping("/{id}")
    public OrderResponse get(@PathVariable UUID id) { /* ... */ }
}
```

### DTO annotations

```java
public record CreateOrderRequest(
        @Schema(description = "Customer's full name", example = "Alice Wong", maxLength = 100)
        @NotBlank @Size(max = 100) String customerName,

        @Schema(description = "Line items in this order")
        @NotEmpty @Valid List<OrderLineRequest> lines,

        @Schema(description = "Optional contact email", example = "alice@example.com")
        @Email String contactEmail
) {}
```

4. **Bean Validation is reflected automatically.** `@NotBlank`, `@Size`, `@Min`, `@Email` already produce schema constraints. Don't restate them in `@Schema`.

5. **Always supply `example`** on `@Schema`. It's what makes Swagger UI's "Try it out" useful.

6. **Group endpoints with `@Tag`** at the class level. One tag per controller is the rule of thumb.

7. **Document error responses with the same DTO every time.** Use the `ProblemDetail` schema returned by your `@RestControllerAdvice` (see `java-restful-api`).

---

## Global Configuration

```java
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI ordersOpenAPI(@Value("${spring.application.name}") String appName) {
        return new OpenAPI()
            .info(new Info()
                .title(appName + " API")
                .version("v1")
                .description("Order management service")
                .contact(new Contact().name("Platform Team").email("platform@acme.com"))
                .license(new License().name("Proprietary")))
            .servers(List.of(
                new Server().url("https://api.acme.com").description("Production"),
                new Server().url("http://localhost:8080").description("Local")))
            .components(new Components()
                .addSecuritySchemes("bearer-jwt", new SecurityScheme()
                    .type(SecurityScheme.Type.HTTP)
                    .scheme("bearer")
                    .bearerFormat("JWT")))
            .addSecurityItem(new SecurityRequirement().addList("bearer-jwt"));
    }
}
```

8. **Define a global security scheme** so Swagger UI's "Authorize" button works. Otherwise testers will paste tokens into URLs.

9. **`servers` list matters for "Try it out".** Without it, Swagger UI calls the page's origin — fine for local but breaks when the spec is hosted elsewhere.

---

## `application.yml` Settings

```yaml
springdoc:
  api-docs:
    path: /v3/api-docs
    enabled: true
  swagger-ui:
    path: /swagger-ui.html
    operationsSorter: method
    tagsSorter: alpha
    tryItOutEnabled: true
    persistAuthorization: true
  packages-to-scan: com.acme.orders.web   # narrow scan
  paths-to-match: /api/**
```

10. **Restrict `packages-to-scan`** to your controller package. Otherwise every Boot internal endpoint surfaces in the spec.

11. **`paths-to-match: /api/**`** keeps `/actuator/*` out of the public spec.

---

## Per-Environment Exposure

`/v3/api-docs` and `/swagger-ui.html` should not be public on production by default.

```yaml
# application-prod.yml
springdoc:
  api-docs:
    enabled: false
  swagger-ui:
    enabled: false
```

12. **Disable in production** unless the API is intentionally public. Internal services should serve the spec only on the cluster's internal network or behind auth.

13. **If you must expose it in prod**, gate it with Spring Security:
    ```java
    .requestMatchers("/v3/api-docs/**", "/swagger-ui/**").hasRole("API_DOCS")
    ```

14. **Don't ship the YAML in the JAR for code-first projects.** Generated at runtime is fine.

---

## API-First Workflow

When the OpenAPI YAML is the source of truth:

### 1. Author `src/main/resources/openapi/orders-api.yaml`

```yaml
openapi: 3.0.3
info:
  title: Orders API
  version: 1.0.0
paths:
  /api/v1/orders/{id}:
    get:
      operationId: getOrder
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema: { $ref: "#/components/schemas/OrderResponse" }
        "404":
          $ref: "#/components/responses/NotFound"
components:
  schemas:
    OrderResponse:
      type: object
      required: [id, status, total]
      properties:
        id: { type: string, format: uuid }
        status: { type: string, enum: [PENDING, PAID, CANCELLED] }
        total: { type: number }
  responses:
    NotFound:
      description: Resource not found
      content:
        application/problem+json:
          schema: { $ref: "#/components/schemas/Problem" }
```

### 2. Generate server interfaces with the OpenAPI Generator

```gradle
plugins {
    id 'org.openapi.generator' version '7.6.0'
}

openApiGenerate {
    generatorName = 'spring'
    inputSpec = "$rootDir/src/main/resources/openapi/orders-api.yaml"
    outputDir = "$buildDir/generated/openapi"
    apiPackage = 'com.acme.orders.api'
    modelPackage = 'com.acme.orders.api.model'
    configOptions = [
        interfaceOnly: 'true',
        useSpringBoot3: 'true',
        useTags: 'true',
        skipDefaultInterface: 'true'
    ]
}

sourceSets.main.java.srcDirs += "$buildDir/generated/openapi/src/main/java"
compileJava.dependsOn tasks.openApiGenerate
```

### 3. Implement the generated interface

```java
@RestController
public class OrderController implements OrdersApi {
    @Override
    public ResponseEntity<OrderResponse> getOrder(UUID id) { ... }
}
```

15. **`interfaceOnly: true`** — generate only the interface; you implement it. Don't let the generator create controllers you'd then edit.

16. **Generate clients separately.** A consuming service or frontend imports only the model + client, not the server interface. Use a different generator config (`generatorName = 'typescript-fetch'`, `'java'`, etc.).

17. **Treat the YAML like code.** Lint with `spectral`, version it, review changes in PRs. Breaking changes bump `info.version`.

---

## Versioning the Spec

18. **One spec per major API version.** `/v1` and `/v2` get separate `GroupedOpenApi` beans:
    ```java
    @Bean
    public GroupedOpenApi v1() {
        return GroupedOpenApi.builder().group("v1").pathsToMatch("/api/v1/**").build();
    }
    @Bean
    public GroupedOpenApi v2() {
        return GroupedOpenApi.builder().group("v2").pathsToMatch("/api/v2/**").build();
    }
    ```

19. **Additive changes don't bump the version.** Adding a field, a new endpoint, a new optional param — same version. Removing or renaming = breaking. See [`rules/api-versioning.md`](../../rules/api-versioning.md).

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Spec lists every actuator and Spring internal endpoint | Set `paths-to-match: /api/**` and `packages-to-scan` |
| Swagger UI loads but every "Try it out" returns 401 | Configure global `bearer-jwt` scheme; use the Authorize button |
| `@Schema(implementation = SomeInterface.class)` shows nothing | Springdoc needs concrete classes; use a sealed type with `@Schema(oneOf = {...})` |
| Polymorphic responses missing discriminator | Add `@JsonTypeInfo` + `@Schema(discriminatorProperty = "type")` |
| Generated TypeScript client uses `any` everywhere | The Java DTO is missing types/`@Schema`; regenerate after fixing |
| Spec drifts from impl | If code-first, contract tests; if API-first, regenerate interface and let compile fail |

---

## Checklist

- [ ] `springdoc-openapi-starter-webmvc-ui` (or webflux) on the classpath
- [ ] One `OpenAPI` bean with `info`, `servers`, `securitySchemes`
- [ ] `packages-to-scan` and `paths-to-match` restrict the spec to your API
- [ ] Every controller has `@Tag`; every endpoint has `@Operation` + responses
- [ ] DTOs have `@Schema(example = ...)` on non-obvious fields
- [ ] Error responses reference a shared `ProblemDetail` schema
- [ ] Swagger UI disabled or auth-gated in production
- [ ] If API-first: YAML is source of truth, generator runs in build, generator-created files are gitignored
- [ ] Contract tests or schema diff in CI to catch spec drift

---

## Related Skills

- [`java-restful-api`](../java-restful-api/SKILL.md) — the controllers being annotated
- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — wiring config beans
- [`api-design-rest`](../api-design-rest/SKILL.md) — design rules the spec should reflect
