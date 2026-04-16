# Go Naming Rules

Conventions for naming in Go code. Align with the official [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) and [Effective Go](https://go.dev/doc/effective_go).

---

## Packages

1. **Lowercase, single word, no underscores, no mixedCaps.**
   - ✅ `catalog`, `httputil`, `strconv`
   - ❌ `Catalog`, `http_util`, `strConv`

2. **Name by what the package *provides*, not what it *contains*.**
   - ✅ `http` (provides HTTP), `sort` (provides sorting)
   - ❌ `utils`, `helpers`, `common`, `misc`

3. **Don't stutter.** Package name is a prefix; don't repeat it.
   - ✅ `bytes.Buffer`, `http.Request`
   - ❌ `bytes.BytesBuffer`, `http.HTTPRequest`

4. **Package == directory name.** Enforced by the compiler for public packages.

---

## Types

5. **`MixedCaps` / `mixedCaps`.** Public exported → capital, unexported → lowercase. No underscores.

6. **Short, clear nouns.** Avoid `Data`, `Info`, `Manager`, `Handler` as standalone — they carry no meaning.
   - ✅ `Product`, `InvoiceRenderer`, `ClockSkew`
   - ❌ `ProductData`, `InfoManager`

7. **Interfaces ending in `-er` for single-method.**
   - ✅ `Reader`, `Writer`, `Stringer`, `ProductRepository`
   - ❌ `IProduct`, `ProductInterface` (no Hungarian/C# prefixes)

---

## Functions & Methods

8. **Verb or verb phrase for actions.**
   - ✅ `SellProduct`, `FindByID`, `Close`
   - ❌ `ProductSelling`, `IDFinder`

9. **Noun for getters — no `Get` prefix.**
   - ✅ `p.Stock()`, `req.Header()`
   - ❌ `p.GetStock()`, `req.GetHeader()`

10. **Use `Is` / `Has` / `Can` for booleans.**
    - ✅ `IsActive()`, `HasPermission()`, `CanRetry()`
    - ❌ `Active()` (ambiguous — state or action?)

11. **Consistent parameter order.** When a package has multiple funcs, keep `ctx context.Context` first, then main subject, then options.

---

## Variables

12. **Short scope → short name.** Loop index, single-line scope → `i`, `k`, `v`. Broader scope → descriptive.
    - ✅ `for i := range xs` (single line)
    - ✅ `productRepo` (module-level)
    - ❌ `productRepositoryInstance` (too long)
    - ❌ `x` as a function parameter name in a 30-line function

13. **Receiver names are short and consistent.** 1-2 lowercase letters, same across all methods of the type.
    - ✅ `func (p *Product) Sell(...)` — always `p`
    - ❌ `func (this *Product) Sell(...)`, `func (self *Product) Sell(...)`
    - ❌ Mixing `p` and `product` across methods of the same type

14. **Avoid Hungarian notation and type prefixes.**
    - ✅ `count`, `name`, `users`
    - ❌ `iCount`, `strName`, `arrUsers`

15. **Acronyms: all caps OR all lowercase — pick based on export.**
    - ✅ `URL`, `HTTP`, `ID` in exported names: `ServeHTTP`, `UserID`
    - ✅ lowercase in unexported: `userID`, `httpClient`
    - ❌ `Url`, `Http`, `Id` — never mixed

---

## Constants & Enums

16. **Constants follow same `MixedCaps` rules** — no ALL_CAPS.
    - ✅ `MaxRetries`, `defaultTimeout`
    - ❌ `MAX_RETRIES`, `DEFAULT_TIMEOUT`

17. **Enum-like `iota` groups: prefix with type name** for clarity.
    ```go
    type Status int
    const (
        StatusPending Status = iota
        StatusActive
        StatusClosed
    )
    ```

---

## Errors

18. **Sentinel errors: `Err` prefix.**
    - ✅ `ErrNotFound`, `ErrInvalidInput`
    - ❌ `NotFoundError`, `ErrorNotFound`

19. **Error types (not values): `Error` suffix.**
    - ✅ `type ValidationError struct { ... }`
    - ❌ `type ValidationErr struct { ... }`

See [`go-error-handling.md`](./go-error-handling.md) for error handling rules.

---

## Test Names

20. **`TestXxx` for functions, `TestT_Method` for method tests.**
    - ✅ `TestSellProduct`, `TestProduct_Sell`

21. **Subtests use full sentences describing the scenario.**
    - ✅ `t.Run("returns error when stock is zero", ...)`
    - ❌ `t.Run("case1", ...)`

---

## File Names

22. **Lowercase, words separated by underscores.**
    - ✅ `product.go`, `product_test.go`, `http_client.go`
    - ❌ `Product.go`, `productTest.go`, `http-client.go`

23. **Test files: `_test.go` suffix.** External test package: `_test.go` + `package xxx_test`.
