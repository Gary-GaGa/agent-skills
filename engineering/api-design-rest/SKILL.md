---
name: api-design-rest
description: >
  RESTful API design principles for backend developers. Use this skill when
  designing new HTTP APIs, reviewing endpoint structure, choosing status codes,
  handling errors, or planning versioning and pagination. Language-agnostic but
  examples lean Go.
category: engineering
tags: [api, rest, http, backend, go, design]
related: [clean-ddd-go, api-design-grpc, auth-patterns, microservices-patterns, nextjs-fundamentals, realtime-websocket, tw-payment-integration, java-restful-api, openapi-swagger-spring]
---

# RESTful API Design

> Good APIs are boring — predictable URL shapes, consistent error bodies, obvious status codes.

## When to Use This Skill

- Designing a new HTTP API from scratch
- Reviewing existing endpoints for consistency
- Deciding on error format, pagination, or versioning strategy
- Mapping domain operations to HTTP verbs

---

## Resource-Oriented URLs

### Rules

1. **URLs are nouns (resources), not verbs.**
   - ✅ `GET /products/42`
   - ❌ `GET /getProduct?id=42`

2. **Plural collection names.**
   - ✅ `/users`, `/users/5`, `/users/5/orders`
   - ❌ `/user/5`

3. **Nest only when the child can't exist without the parent.** Max 2 levels.
   - ✅ `/users/5/orders/12`
   - ❌ `/users/5/orders/12/items/3/reviews` — flatten to `/order-items/3/reviews`

4. **Use kebab-case for multi-word segments.**
   - ✅ `/order-items`
   - ❌ `/orderItems`, `/order_items`

5. **No trailing slashes.** Either redirect or reject — pick one repo-wide.

---

## HTTP Verbs

| Verb | Semantics | Idempotent | Safe |
|------|-----------|------------|------|
| `GET` | Read a resource or list | Yes | Yes |
| `POST` | Create a new resource | No | No |
| `PUT` | Full replace of a resource | Yes | No |
| `PATCH` | Partial update | No* | No |
| `DELETE` | Remove a resource | Yes | No |

*PATCH is idempotent if the patch body is deterministic (e.g. `{"stock": 5}`), not if it's a relative operation (`{"stock": "+1"}`).

### When POST is the right verb

- Creating a resource (`POST /users`)
- Actions that don't map to CRUD — use a sub-resource:
  - ✅ `POST /orders/42/cancel` (action on a resource)
  - ✅ `POST /reports/generate` (trigger an async job)
  - ❌ `POST /cancelOrder` (verb-based URL)

---

## Status Codes

Use the **narrowest correct code**. Don't return 200 for everything.

### Success

| Code | When |
|------|------|
| `200 OK` | Successful GET, PUT, PATCH, DELETE with body |
| `201 Created` | Successful POST that created a resource. Include `Location` header. |
| `204 No Content` | Successful DELETE or PUT/PATCH with no response body |

### Client Errors

| Code | When |
|------|------|
| `400 Bad Request` | Malformed body, missing required field, validation failure |
| `401 Unauthorized` | No or invalid authentication token |
| `403 Forbidden` | Authenticated but not authorised for this resource |
| `404 Not Found` | Resource doesn't exist. Also use for endpoints that exist but the user shouldn't know about |
| `409 Conflict` | State conflict (e.g. duplicate email, version mismatch) |
| `422 Unprocessable Entity` | Body is valid JSON/format, but semantically wrong (optional — 400 is fine too) |
| `429 Too Many Requests` | Rate limited. Include `Retry-After` header. |

### Server Errors

| Code | When |
|------|------|
| `500 Internal Server Error` | Unhandled exception, bug |
| `502 Bad Gateway` | Upstream service failed |
| `503 Service Unavailable` | Overloaded or in maintenance. Include `Retry-After`. |
| `504 Gateway Timeout` | Upstream service timed out |

---

## Error Response Format

Pick **one** format and use it everywhere. Recommended:

```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Stock quantity must be positive.",
    "details": [
      {
        "field": "stock",
        "reason": "must be > 0",
        "value": -3
      }
    ]
  }
}
```

### Rules

6. **Machine-readable `code`, human-readable `message`.** Clients switch on `code`; `message` is for logs and UI.

7. **Don't leak internals.** No stack traces, no SQL errors, no internal paths in production.

8. **Consistent structure.** Every 4xx/5xx returns the same envelope. No "sometimes it's `{error: ...}`, sometimes `{message: ...}`".

9. **`details` for field-level validation.** List every failing field, not just the first one.

---

## Pagination

### Offset-based (simple, good for most cases)

```
GET /products?page=2&per_page=20
```

Response includes:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "per_page": 20,
    "total_count": 142,
    "total_pages": 8
  }
}
```

### Cursor-based (efficient for large/live datasets)

```
GET /products?cursor=eyJpZCI6NDJ9&limit=20
```

Response:
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6NjJ9",
    "has_more": true
  }
}
```

10. **Default to cursor-based for feeds, timelines, and anything where rows can be inserted between pages.** Offset-based skips or duplicates rows in that scenario.

11. **Always set a max `per_page` / `limit` server-side.** Don't trust the client.

---

## Filtering, Sorting, Search

```
GET /products?status=active&sort=-created_at&q=widget
```

12. **Filters are query params matching field names.** Multiple values: `status=active,pending` or `status=active&status=pending` — pick one.

13. **Sort with `-` prefix for descending.** `sort=name` (asc), `sort=-created_at` (desc). Multiple: `sort=-created_at,name`.

14. **Full-text search: `q=` parameter.** Keep it separate from field filters.

---

## Versioning

| Strategy | URL | Header |
|----------|-----|--------|
| **URL prefix** | `/v1/users`, `/v2/users` | — |
| **Header** | `/users` | `Accept: application/vnd.myapp.v2+json` |

15. **Default: URL prefix.** It's explicit, discoverable, and easy to route.

16. **Only bump the version for breaking changes.** Additive changes (new fields, new endpoints) don't need a new version.

17. **Support N-1 at minimum.** Deprecate old versions with notice, don't drop them overnight.

---

## Idempotency

18. **GET, PUT, DELETE are naturally idempotent.** Repeating them produces the same result.

19. **POST is not.** For critical POST operations (payments, orders), support an `Idempotency-Key` header:
    ```
    POST /payments
    Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
    ```
    Server stores the key → result mapping. Duplicate requests return the stored result.

---

## HATEOAS (Hypermedia Links)

Optional, but useful for discoverability:

```json
{
  "id": 42,
  "name": "Widget",
  "links": {
    "self": "/products/42",
    "orders": "/products/42/orders"
  }
}
```

20. **Don't over-engineer.** Links to `self` and closely related resources are enough. Full HATEOAS is rarely worth the complexity.

---

## Go Implementation Notes

### Handler structure (Clean Architecture adapter)

```go
func (h *ProductHandler) GetProduct(w http.ResponseWriter, r *http.Request) {
    id := chi.URLParam(r, "id")

    result, err := h.usecase.GetProduct(r.Context(), id)
    if errors.Is(err, catalog.ErrProductNotFound) {
        writeError(w, http.StatusNotFound, "PRODUCT_NOT_FOUND", "Product not found")
        return
    }
    if err != nil {
        writeError(w, http.StatusInternalServerError, "INTERNAL", "Internal server error")
        return
    }

    writeJSON(w, http.StatusOK, result)
}
```

### Consistent error writer

```go
func writeError(w http.ResponseWriter, status int, code, message string) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(map[string]any{
        "error": map[string]any{
            "code":    code,
            "message": message,
        },
    })
}
```

---

## Checklist

- [ ] URLs are nouns, plural, kebab-case
- [ ] Correct HTTP verb for each operation
- [ ] Narrowest status code used
- [ ] Error response format is consistent across all endpoints
- [ ] No internal details in error messages
- [ ] Pagination for all list endpoints
- [ ] Sorting/filtering on query params
- [ ] Versioning strategy decided and documented
- [ ] Idempotency-Key for critical POST operations
- [ ] Rate limiting with `429` + `Retry-After`
- [ ] `Content-Type` and `Accept` headers handled correctly

---

## Related Skills

- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — architecture; handlers live in the adapter layer
- [`api-design-grpc`](../api-design-grpc/SKILL.md) — when HTTP/JSON isn't the right choice
- [`code-review`](../code-review/SKILL.md) — use this checklist during API reviews
