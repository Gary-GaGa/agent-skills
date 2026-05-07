---
name: java-restful-api
description: >
  Building RESTful APIs in Java with Spring Boot — controllers, DTOs, Bean
  Validation, global error handling with @ControllerAdvice, RFC 7807
  ProblemDetail, content negotiation, and pagination. Use this skill when
  implementing or reviewing REST endpoints in a Spring MVC project.
category: engineering
tags: [java, spring-boot, api, rest, http, backend, design, validation]
keywords: [Spring MVC, "@RestController", "@ControllerAdvice", ProblemDetail, RFC 7807, Bean Validation, "@Valid", Jackson, ResponseEntity]
related: [spring-boot-fundamentals, openapi-swagger-spring, spring-boot-testing, api-design-rest, auth-patterns, spring-ai-rag]
---

# Java RESTful API (Spring Boot)

> Spring MVC gives you the verbs; the work is keeping DTOs, validation, and error envelopes consistent across every controller.

## When to Use This Skill

- Implementing REST endpoints in a Spring Boot service
- Reviewing controllers for consistency, validation, and error handling
- Migrating from `Map<String, Object>` "free-form" responses to typed DTOs
- Wiring global exception handling and a uniform error envelope
- Pagination, sorting, and filtering in list endpoints

For language-agnostic REST design rules (verbs, status codes, URL shapes), pair with [`api-design-rest`](../api-design-rest/SKILL.md).

---

## Layered Anatomy

```
@RestController          ← HTTP-shaped: @RequestMapping, @Valid, returns ResponseEntity<DTO>
   ↓
Application Service      ← orchestrates use case, transactional boundary
   ↓
Domain                   ← entities, business rules
   ↓
Repository / Adapter     ← JPA, GCP clients, etc.
```

1. **Controllers do not contain business logic.** Parse → validate → call service → map to DTO → return. If you see `if (order.getStatus() == ...)` in a controller, push it down.

2. **Never expose JPA entities directly.** Always map to a DTO. Entities leak persistence concerns (lazy proxies, `@JsonIgnore` battles, schema-coupled fields).

---

## Controllers

### Skeleton

```java
@RestController
@RequestMapping("/api/v1/orders")
@Validated
public class OrderController {

    private final OrderService service;

    public OrderController(OrderService service) {
        this.service = service;
    }

    @PostMapping
    public ResponseEntity<OrderResponse> create(
            @Valid @RequestBody CreateOrderRequest req,
            UriComponentsBuilder uriBuilder) {

        Order order = service.create(req.toCommand());
        URI location = uriBuilder.path("/api/v1/orders/{id}")
                .buildAndExpand(order.id()).toUri();
        return ResponseEntity.created(location).body(OrderResponse.from(order));
    }

    @GetMapping("/{id}")
    public OrderResponse get(@PathVariable UUID id) {
        return OrderResponse.from(service.findById(id));
    }

    @GetMapping
    public PageResponse<OrderResponse> list(
            @RequestParam(required = false) OrderStatus status,
            @ParameterObject Pageable pageable) {
        Page<Order> page = service.list(status, pageable);
        return PageResponse.from(page.map(OrderResponse::from));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void cancel(@PathVariable UUID id) {
        service.cancel(id);
    }
}
```

3. **Use `@RestController`**, not `@Controller` + `@ResponseBody` on every method.

4. **Version in the URL** (`/api/v1/...`). Header versioning is harder to discover and route. See [`rules/api-versioning.md`](../../rules/api-versioning.md).

5. **Return `ResponseEntity` only when you need to set status, headers, or `Location`.** Otherwise return the DTO directly — Boot defaults to `200 OK`.

6. **Use `@ResponseStatus(HttpStatus.NO_CONTENT)`** for `DELETE` and other void-returning endpoints. Avoid returning an empty body with `200`.

7. **Path variables for identity, query params for filters/options.** Don't put filter values in the path.

---

## DTOs

### Use Java records

```java
public record CreateOrderRequest(
        @NotBlank @Size(max = 100) String customerName,
        @NotEmpty @Valid List<OrderLineRequest> lines,
        @Email String contactEmail
) {
    public CreateOrderCommand toCommand() {
        return new CreateOrderCommand(customerName, lines.stream().map(OrderLineRequest::toCommand).toList(), contactEmail);
    }
}

public record OrderLineRequest(
        @NotNull UUID productId,
        @Positive int quantity
) {
    public OrderLineCommand toCommand() { return new OrderLineCommand(productId, quantity); }
}

public record OrderResponse(UUID id, String customerName, OrderStatus status, BigDecimal total, Instant createdAt) {
    public static OrderResponse from(Order order) {
        return new OrderResponse(order.id(), order.customerName(), order.status(), order.total(), order.createdAt());
    }
}
```

8. **Records over Lombok `@Data`.** Records are immutable, concise, and Jackson-compatible out of the box on Boot 3.

9. **Separate request and response DTOs.** Don't reuse `OrderResponse` as the input — they have different validation and different fields (`id`, `createdAt` are server-set).

10. **Map DTO ↔ domain at the controller boundary.** Static `from(...)` and instance `toCommand()` is enough; reach for MapStruct only when mapping count crosses ~15.

11. **Use `@JsonProperty` only when the wire name differs from the field.** Otherwise let Jackson use the record component name. Configure naming strategy globally if you need snake_case:
    ```yaml
    spring:
      jackson:
        property-naming-strategy: SNAKE_CASE
    ```

---

## Bean Validation

### Add the starter

```gradle
implementation 'org.springframework.boot:spring-boot-starter-validation'
```

### Common annotations

| Annotation | Use |
|---|---|
| `@NotNull` | Reference must not be null |
| `@NotBlank` | String not null and trimmed length > 0 |
| `@NotEmpty` | Collection / array / string size > 0 |
| `@Size(min, max)` | Bound length / size |
| `@Min` / `@Max` / `@Positive` / `@PositiveOrZero` | Numeric bounds |
| `@Email` | Email format |
| `@Pattern(regexp = ...)` | Regex |
| `@Valid` | Recursively validate nested DTOs |

12. **Always `@Valid` on `@RequestBody`.** Without it, no constraints fire.

13. **For path/query params, use `@Validated` on the controller class** plus `@Min`, `@Pattern`, etc. directly on the method parameters:
    ```java
    @GetMapping("/{id}")
    public ... get(@PathVariable @org.hibernate.validator.constraints.UUID String id) { ... }
    ```

14. **Validate enums via Jackson, not Bean Validation.** Define the enum and Jackson rejects unknown values with `400` automatically.

---

## Error Handling — RFC 7807 ProblemDetail

Spring Boot 3 ships with `org.springframework.http.ProblemDetail`. Use it.

### Global advice

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setType(URI.create("https://api.acme.com/errors/validation"));
        pd.setTitle("Validation failed");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
                .map(e -> Map.of("field", e.getField(), "message", e.getDefaultMessage()))
                .toList());
        return pd;
    }

    @ExceptionHandler(OrderNotFoundException.class)
    public ProblemDetail handleNotFound(OrderNotFoundException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        pd.setType(URI.create("https://api.acme.com/errors/order-not-found"));
        pd.setTitle("Order not found");
        pd.setDetail(ex.getMessage());
        pd.setProperty("orderId", ex.orderId());
        return pd;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleUnexpected(Exception ex) {
        log.error("unexpected error", ex);
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        pd.setTitle("Internal server error");
        return pd;
    }
}
```

Wire format (`application/problem+json`):

```json
{
  "type": "https://api.acme.com/errors/validation",
  "title": "Validation failed",
  "status": 400,
  "errors": [
    {"field": "customerName", "message": "must not be blank"}
  ]
}
```

15. **One `@RestControllerAdvice` per service.** Don't sprinkle `@ExceptionHandler` across controllers — drift is guaranteed.

16. **Map domain exceptions to status codes in one place.** Domain code throws `OrderNotFoundException`; the advice maps it to `404`. Domain doesn't know about HTTP.

17. **Never leak stack traces or SQL errors to the client.** Log at error level; return a generic problem detail.

18. **`title` is human, `type` is a stable URI clients can switch on.** Don't change `type` URIs once published — they're part of the contract.

---

## Pagination

Use Spring Data's `Pageable`:

```java
@GetMapping
public PageResponse<OrderResponse> list(@ParameterObject Pageable pageable) {
    return PageResponse.from(service.list(pageable).map(OrderResponse::from));
}
```

Request: `GET /api/v1/orders?page=0&size=20&sort=createdAt,desc`

Response wrapper:

```java
public record PageResponse<T>(List<T> items, int page, int size, long totalElements, int totalPages) {
    public static <T> PageResponse<T> from(Page<T> page) {
        return new PageResponse<>(page.getContent(), page.getNumber(), page.getSize(),
                page.getTotalElements(), page.getTotalPages());
    }
}
```

19. **Don't return Spring's `Page` directly.** Its JSON shape is unstable across versions and exposes internals (`pageable.sort.unsorted` etc.). Wrap it.

20. **Cap `size` server-side.** Reject or clamp `size > 100`.

---

## Content Negotiation

21. **Default to `application/json`.** Use `produces = MediaType.APPLICATION_JSON_VALUE` only when restricting.

22. **Errors use `application/problem+json`.** Boot sets this automatically when you return `ProblemDetail`.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Returning JPA entity → Jackson trips on lazy proxy → 500 | DTOs only |
| `@RequestBody` without `@Valid` → constraints don't fire | Add `@Valid` |
| `@Valid` on path params doesn't work | Use `@Validated` on the class + constraints on params |
| `@PathVariable Long id` accepts non-numeric → 400 with leaky message | Type-coerce to UUID/Long; rely on `MethodArgumentTypeMismatchException` handler |
| Returning `Optional<T>` from a controller | Throw a `NotFoundException` instead; let advice map to 404 |
| Mixing `Map<String, Object>` and DTOs | Pick DTOs everywhere |
| `@RequestParam` with default `""` instead of `Optional` | Use `required = false` and `Optional<String>` (or just `String` and check for null) |

---

## Pre-Merge Checklist

- [ ] `@RestController` + `/api/v{n}/...` URL prefix
- [ ] Records for request and response DTOs
- [ ] `@Valid` on every `@RequestBody`
- [ ] `@Validated` on the class for `@PathVariable` / `@RequestParam` constraints
- [ ] No JPA entities in controller signatures
- [ ] Single `@RestControllerAdvice` returning `ProblemDetail`
- [ ] Domain exceptions, not `ResponseStatusException`, in service layer
- [ ] List endpoints return wrapped `PageResponse`, not raw `Page`
- [ ] `Location` header set on `201 Created`
- [ ] OpenAPI annotations (see [`openapi-swagger-spring`](../openapi-swagger-spring/SKILL.md))

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — project setup, config, profiles
- [`openapi-swagger-spring`](../openapi-swagger-spring/SKILL.md) — annotate these controllers
- [`spring-boot-testing`](../spring-boot-testing/SKILL.md) — `@WebMvcTest` and MockMvc for these controllers
- [`api-design-rest`](../api-design-rest/SKILL.md) — language-agnostic REST design rules
- [`auth-patterns`](../auth-patterns/SKILL.md) — securing these endpoints
