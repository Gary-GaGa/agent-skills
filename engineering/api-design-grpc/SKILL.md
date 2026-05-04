---
name: api-design-grpc
description: >
  gRPC API design guide — proto file organization, service/message conventions,
  error handling with status codes, streaming patterns, and backward compatibility.
  Use this skill when designing or reviewing gRPC services. Language-agnostic but
  Go examples included.
category: engineering
tags: [api, grpc, protobuf, backend, go, design]
related: [clean-ddd-go, api-design-rest, event-driven-architecture, microservices-patterns]
---

# gRPC API Design

> Design proto files as a contract. Everything the client needs is in the `.proto` — nothing is implicit.

## When to Use This Skill

- Designing a new gRPC service
- Reviewing `.proto` file structure
- Choosing between unary and streaming RPCs
- Handling errors across gRPC boundaries
- Ensuring backward compatibility on proto changes

## gRPC vs REST — When to Use Which

| Factor | gRPC | REST |
|--------|------|------|
| Internal service-to-service | ✅ Preferred | OK |
| Public-facing API | Needs gRPC-Gateway or Connect | ✅ Preferred |
| Streaming (real-time, large data) | ✅ Native support | Workarounds (SSE, WebSocket) |
| Browser clients | Needs gRPC-Web or Connect | ✅ Native |
| Schema enforcement | ✅ Protobuf | OpenAPI (optional) |
| Performance (binary, HTTP/2) | ✅ Faster | JSON/HTTP/1.1 overhead |

**Rule of thumb:** gRPC for internal + performance-sensitive; REST for public + browser-facing.

---

## Proto File Organization

### Directory structure

```
proto/
├── buf.yaml                    # buf config (recommended over raw protoc)
├── buf.gen.yaml                # code generation config
└── myapp/
    └── v1/
        ├── catalog.proto       # one file per bounded context / service
        ├── order.proto
        └── common.proto        # shared messages (Money, Pagination, etc.)
```

### Rules

1. **One service per `.proto` file.** Keeps generated code focused and import-clean.

2. **Package name matches directory path.**
   ```protobuf
   package myapp.v1;
   option go_package = "github.com/myorg/myapp/gen/myapp/v1";
   ```

3. **Version in the package path (`v1`, `v2`), not in the service name.**
   - ✅ `package myapp.v1;` with `service CatalogService { ... }`
   - ❌ `service CatalogServiceV1`

4. **Use `buf` over raw `protoc`.** `buf lint`, `buf breaking`, `buf generate` are strictly better DX.

---

## Naming Conventions

### Services

5. **`<Domain>Service`** — PascalCase, suffixed with `Service`.
   - ✅ `CatalogService`, `OrderService`
   - ❌ `Catalog`, `CatalogAPI`, `CatalogManager`

### RPCs

6. **Verb + Noun.** PascalCase. Matches the domain operation.
   - ✅ `GetProduct`, `ListProducts`, `CreateOrder`, `CancelOrder`
   - ❌ `Product`, `FetchProduct`, `DoCancel`

7. **Standard verbs for CRUD:**

   | Operation | Verb | Example |
   |-----------|------|---------|
   | Read one | `Get` | `GetProduct` |
   | List/search | `List` | `ListProducts` |
   | Create | `Create` | `CreateProduct` |
   | Full update | `Update` | `UpdateProduct` |
   | Delete | `Delete` | `DeleteProduct` |
   | Action | Domain verb | `CancelOrder`, `ReserveStock` |

### Messages

8. **Request: `<RPC>Request`. Response: `<RPC>Response`.** Always dedicated — even if the body is just an ID.
   ```protobuf
   rpc GetProduct(GetProductRequest) returns (GetProductResponse);
   ```
   - ✅ `GetProductRequest { string id = 1; }`
   - ❌ `rpc GetProduct(google.protobuf.StringValue)` — no room to grow.

9. **Fields: `snake_case`.** Protobuf convention; generated code adapts per language.

10. **Enums: `SCREAMING_SNAKE_CASE` with type prefix. First value is `UNSPECIFIED`.**
    ```protobuf
    enum OrderStatus {
      ORDER_STATUS_UNSPECIFIED = 0;
      ORDER_STATUS_PENDING = 1;
      ORDER_STATUS_CONFIRMED = 2;
      ORDER_STATUS_CANCELLED = 3;
    }
    ```
    `UNSPECIFIED = 0` is required — proto3 defaults to 0, and you need to distinguish "not set" from a real value.

---

## Message Design

### Field numbering

11. **Never reuse or change field numbers.** Once assigned, a number is permanent.

12. **Reserve ranges when removing fields.**
    ```protobuf
    message Product {
      reserved 4, 6 to 8;
      reserved "old_field_name";
    }
    ```

13. **Group field numbers by purpose.** 1-15 for frequently-set fields (1-byte tag), 16+ for optional/rare fields.

### Common patterns

14. **Wrapper for optional scalars.** Proto3 can't distinguish "zero" from "not set" for scalars.
    ```protobuf
    import "google/protobuf/wrappers.proto";

    message UpdateProductRequest {
      string id = 1;
      google.protobuf.StringValue name = 2;       // null = don't update
      google.protobuf.Int32Value stock = 3;
    }
    ```
    Or use `optional` keyword (proto3 syntax since 3.15+):
    ```protobuf
    optional string name = 2;
    ```

15. **Use `google.protobuf.Timestamp` for time, `google.protobuf.Duration` for intervals.**
    ```protobuf
    import "google/protobuf/timestamp.proto";
    google.protobuf.Timestamp created_at = 5;
    ```

16. **Pagination in List RPCs:**
    ```protobuf
    message ListProductsRequest {
      int32 page_size = 1;
      string page_token = 2;    // opaque cursor
    }
    message ListProductsResponse {
      repeated Product products = 1;
      string next_page_token = 2;
    }
    ```

17. **`FieldMask` for partial updates.**
    ```protobuf
    import "google/protobuf/field_mask.proto";

    message UpdateProductRequest {
      Product product = 1;
      google.protobuf.FieldMask update_mask = 2;
    }
    ```
    Server only updates fields listed in the mask.

---

## Error Handling

### gRPC Status Codes

| Code | When | REST equivalent |
|------|------|-----------------|
| `OK` (0) | Success | 200 |
| `INVALID_ARGUMENT` (3) | Bad input | 400 |
| `NOT_FOUND` (5) | Resource doesn't exist | 404 |
| `ALREADY_EXISTS` (6) | Duplicate creation | 409 |
| `PERMISSION_DENIED` (7) | Authenticated but not authorised | 403 |
| `UNAUTHENTICATED` (16) | No or invalid credentials | 401 |
| `FAILED_PRECONDITION` (9) | State conflict (e.g. can't cancel shipped order) | 409/412 |
| `RESOURCE_EXHAUSTED` (8) | Rate limited, quota | 429 |
| `UNIMPLEMENTED` (12) | RPC not implemented | 501 |
| `INTERNAL` (13) | Bug, unexpected failure | 500 |
| `UNAVAILABLE` (14) | Transient, retry | 503 |
| `DEADLINE_EXCEEDED` (4) | Timeout | 504 |

18. **Use the narrowest code.** `INVALID_ARGUMENT` ≠ `FAILED_PRECONDITION` — the first is bad input format, the second is valid input at the wrong time.

19. **Add detail with `errdetails`.**
    ```go
    st := status.New(codes.InvalidArgument, "validation failed")
    st, _ = st.WithDetails(&errdetails.BadRequest{
        FieldViolations: []*errdetails.BadRequest_FieldViolation{
            {Field: "stock", Description: "must be positive"},
        },
    })
    return nil, st.Err()
    ```

20. **Don't leak internals.** `INTERNAL` errors should have generic messages; log the real cause server-side.

---

## Streaming

| Pattern | Use case | Example |
|---------|----------|---------|
| **Unary** | Simple request/response | `GetProduct` |
| **Server streaming** | Server pushes many results | `WatchOrderStatus`, `ExportProducts` |
| **Client streaming** | Client pushes many inputs | `UploadChunks`, `BatchImport` |
| **Bidirectional** | Real-time interactive | `Chat`, `LiveSync` |

```protobuf
service OrderService {
  rpc WatchOrder(WatchOrderRequest) returns (stream OrderEvent);
  rpc BatchImport(stream ImportProductRequest) returns (BatchImportResponse);
}
```

21. **Default to unary.** Streaming adds complexity (error handling, backpressure, reconnection). Only use when unary doesn't fit.

22. **Server streaming: send a terminal message or rely on server close.** Client needs to know when the stream is done.

23. **Handle stream errors at each `Recv()` / `Send()`.** `io.EOF` = normal close, anything else = error.

---

## Backward Compatibility

### Safe changes (won't break existing clients)

- Adding a new field to a message (with new field number)
- Adding a new RPC to a service
- Adding a new enum value (but NOT as 0)
- Adding a new service

### Breaking changes (require version bump to `v2`)

- Removing or renaming a field
- Changing a field's type or number
- Removing an RPC or service
- Changing an RPC's request/response type
- Reordering enum values

24. **Run `buf breaking` in CI.** It catches breaking changes against the previous version automatically.

25. **Deprecate before removing.**
    ```protobuf
    message Product {
      string name = 1;
      string display_name = 3;  // replaces name
      reserved 2;
      string old_sku = 2 [deprecated = true];  // ← actually: use reserved
    }
    ```

---

## Go Implementation Notes

### Server

```go
type catalogServer struct {
    pb.UnimplementedCatalogServiceServer
    usecase portin.CatalogUsecase
}

func (s *catalogServer) GetProduct(ctx context.Context, req *pb.GetProductRequest) (*pb.GetProductResponse, error) {
    if req.GetId() == "" {
        return nil, status.Error(codes.InvalidArgument, "id is required")
    }
    result, err := s.usecase.GetProduct(ctx, req.GetId())
    if errors.Is(err, catalog.ErrProductNotFound) {
        return nil, status.Error(codes.NotFound, "product not found")
    }
    if err != nil {
        return nil, status.Error(codes.Internal, "internal error")
    }
    return toProtoResponse(result), nil
}
```

### Interceptors (middleware)

```go
grpc.UnaryInterceptor(grpc_middleware.ChainUnaryServer(
    grpc_recovery.UnaryServerInterceptor(),
    grpc_zap.UnaryServerInterceptor(logger),
    grpc_auth.UnaryServerInterceptor(authFunc),
))
```

### Testing

```go
func TestGetProduct(t *testing.T) {
    srv := grpc.NewServer()
    pb.RegisterCatalogServiceServer(srv, newTestCatalogServer())
    lis := bufconn.Listen(1024 * 1024)
    go srv.Serve(lis)

    conn, _ := grpc.DialContext(ctx, "",
        grpc.WithContextDialer(func(ctx context.Context, s string) (net.Conn, error) {
            return lis.Dial()
        }),
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    )
    client := pb.NewCatalogServiceClient(conn)

    resp, err := client.GetProduct(ctx, &pb.GetProductRequest{Id: "p1"})
    assert.NoError(t, err)
    assert.Equal(t, "Widget", resp.GetProduct().GetName())
}
```

---

## Checklist

- [ ] One service per `.proto` file
- [ ] Package path includes version (`v1`)
- [ ] RPCs follow Verb + Noun convention
- [ ] Request/Response messages are per-RPC (not shared generics)
- [ ] Enums start with `UNSPECIFIED = 0` and use type prefix
- [ ] `FieldMask` for partial updates
- [ ] Pagination with `page_token` / `next_page_token`
- [ ] Status codes are the narrowest correct fit
- [ ] No internal details in error messages
- [ ] `buf lint` and `buf breaking` pass in CI
- [ ] Streaming only where unary doesn't fit

---

## Related Skills

- [`api-design-rest`](../api-design-rest/SKILL.md) — when HTTP/JSON is more appropriate
- [`clean-ddd-go`](../clean-ddd-go/SKILL.md) — gRPC server lives in the adapter layer
- [`go-testing`](../go-testing/SKILL.md) — testing gRPC with `bufconn`
