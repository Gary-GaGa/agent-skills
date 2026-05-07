# Java Naming Rules

Conventions for naming in modern Java (17+) code, with a slant toward Spring Boot services. Aligns with [Oracle's Java Code Conventions](https://www.oracle.com/java/technologies/javase/codeconventions-namingconventions.html) and [Google Java Style](https://google.github.io/styleguide/javaguide.html).

---

## Packages

1. **All lowercase, no underscores, no camelCase.**
   - ✅ `com.acme.orders.payment`
   - ❌ `com.acme.Orders`, `com.acme.orders_module`

2. **Reverse-DNS rooted, then by feature.** `com.<org>.<service>.<feature>`. The top-level `com.acme.orders.web` / `.application` / `.domain` / `.infrastructure` split is fine inside a feature once the service grows.

3. **No `util`, `helper`, `common`, `misc` packages.** Name by what they provide (`com.acme.orders.money`, `com.acme.orders.idempotency`).

---

## Classes & Records

4. **PascalCase nouns or noun phrases.**
   - ✅ `OrderService`, `PaymentResult`, `CustomerRepository`
   - ❌ `orderService`, `Order_Service`

5. **No Hungarian or interface prefixes.**
   - ✅ `OrderRepository` (interface), `JpaOrderRepository` (impl)
   - ❌ `IOrderRepository`, `OrderRepositoryImpl` *only when* there's exactly one impl — name the impl by its variant (`Jpa…`, `InMemory…`, `Stub…`).

6. **Records for DTOs and value objects.** Same rules as classes. Don't suffix records with `Record`.
   - ✅ `record CreateOrderRequest(...)`, `record Money(BigDecimal amount, Currency currency)`
   - ❌ `CreateOrderRequestRecord`

7. **Test classes: `<Sut>Test`** for unit tests, `<Sut>IT` for integration tests. Spring Boot's Surefire/Failsafe split runs them separately.
   - ✅ `OrderServiceTest`, `OrderControllerIT`

---

## Interfaces

8. **Same PascalCase rules; no `I` prefix.** Java is not C#.
   - ✅ `OrderRepository`, `Clock`, `Validator`
   - ❌ `IOrderRepository`

9. **Single-method functional interfaces named for the verb.**
   - ✅ `Predicate<T>`, `Supplier<T>`, `OrderValidator`
   - ❌ `PredicateInterface`, `OrderValidatorIF`

---

## Methods

10. **camelCase verbs / verb phrases for actions.**
    - ✅ `placeOrder`, `findById`, `cancel`
    - ❌ `OrderPlacement`, `idFinder`, `Cancel`

11. **Getters keep `get*` for JavaBeans compatibility; records use the component name.**
    - ✅ `customer.getName()` (POJO), `customer.name()` (record)
    - ❌ `customer.name()` on a non-record JavaBean — Jackson and JPA expect `getName`

12. **Boolean methods use `is*`, `has*`, `can*`, `should*`.**
    - ✅ `isActive()`, `hasPermission()`, `canRetry()`
    - ❌ `active()` (ambiguous on a non-record)

13. **Async/reactive return types in the name when overloaded with sync.**
    - ✅ `findById(...)` returns `Optional<T>`; `findByIdAsync(...)` returns `CompletableFuture<T>` only when a sync sibling exists.

---

## Variables

14. **camelCase, descriptive at scope.** Loop counters and lambda params can be 1-2 chars (`i`, `e`); fields and longer-scope locals get full words.
    - ✅ `for (int i = 0; ...)`, `customers.forEach(c -> ...)`, `BigDecimal totalPrice;`
    - ❌ `BigDecimal tp;`, `Customer customerInstance` (verbose)

15. **No type prefixes.**
    - ✅ `name`, `count`, `customers`
    - ❌ `strName`, `iCount`, `arrCustomers`

16. **`final` everywhere it fits.** Method params, locals, fields. `final` becomes the default with records and constructor injection.

17. **Acronyms: PascalCase per word boundary.** Treat acronyms as words; only the first letter is capital in identifiers.
    - ✅ `httpClient`, `userId`, `OrderUrl`, `parseHtml`
    - ❌ `HTTPClient`, `userID`, `OrderURL`, `parseHTML`
    - Exception: well-known two-letter all-caps in class names (e.g. `IOException`) follow JDK precedent.

---

## Constants

18. **`UPPER_SNAKE_CASE` for `static final` primitives and immutable singletons.**
    - ✅ `public static final int MAX_RETRIES = 3;`
    - ❌ `MaxRetries`, `maxRetries`

19. **`private static final` for "constants" that are implementation details.** Don't expose unless callers need it.

---

## Enums

20. **Enum type: PascalCase noun. Enum constants: `UPPER_SNAKE_CASE`.**
    ```java
    public enum OrderStatus { PENDING, PAID, CANCELLED, REFUNDED }
    ```

21. **Don't suffix `Enum`.**
    - ✅ `OrderStatus`
    - ❌ `OrderStatusEnum`

---

## Exceptions

22. **`*Exception` suffix; PascalCase.**
    - ✅ `OrderNotFoundException`, `ValidationException`
    - ❌ `OrderNotFoundError`, `ErrOrderNotFound`

23. **Domain exceptions extend `RuntimeException`.** Checked exceptions for domain conditions are usually noise. Use unchecked + `@RestControllerAdvice` mapping (see `java-restful-api`).

---

## Spring-Specific

24. **Controllers end in `Controller`.** `@RestController class OrderController { … }`.

25. **Services end in `Service` or are named for the use case.**
    - ✅ `OrderService`, `PlaceOrderUseCase`
    - ❌ `OrderManager`, `OrderHandler`

26. **Repositories end in `Repository`.** Spring Data scans for them.
    - ✅ `OrderRepository extends JpaRepository<...>`

27. **Configuration classes end in `Config` or `Configuration`.** Pick one per project.
    - ✅ `JacksonConfig`, `SecurityConfig`

28. **Profiles are lowercase**: `local`, `dev`, `staging`, `prod`. No `LOCAL`, no `Production`.

---

## File Names

29. **One public class per file; file name matches the class.**
    - ✅ `OrderService.java` contains `public class OrderService`
    - ❌ Two public classes in `Orders.java`

30. **`package-info.java`** for package-level annotations and Javadoc. Don't sprinkle `@NonNullApi` annotations across files.

---

## Anti-Patterns

| Anti-pattern | Why it's wrong | Use instead |
|---|---|---|
| `Util`, `Helper`, `Manager` classes | Means "I gave up naming" | Name by capability: `MoneyFormatter`, `IdempotencyKeyGenerator` |
| `data`, `info`, `obj` suffixes | Adds noise | `Order`, not `OrderData` |
| `IOrderRepository` interface prefix | C#/COM convention | `OrderRepository` |
| `OrderServiceImpl` when only one impl exists | Useless naming | Just `OrderService` (concrete) or merge interface + class |
| `m_field`, `_field`, `mField` | Hungarian/historical | Plain `field`, with `final` for clarity |
| `getterMethod` on records | Records expose components by name | `customer.name()`, not `customer.getName()` |
| `MAX_RETRIES` for instance fields | UPPER_SNAKE is for `static final` only | `maxRetries` |
| Method names like `process`, `handle`, `execute` | Carries no information | `placeOrder`, `applyDiscount`, `dispatchEvent` |
