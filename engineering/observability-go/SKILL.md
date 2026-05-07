---
name: observability-go
description: >
  Observability for Go services — structured logging with slog, OpenTelemetry
  tracing, metrics with Prometheus, distributed tracing patterns, and
  correlation IDs. Use this skill when adding observability to a Go service
  or debugging production issues with inadequate telemetry.
category: engineering
tags: [go, observability, logging, tracing, metrics, opentelemetry, slog]
related: [debugging-methodology, go-performance, agent-observability, gcp-observability-spring]
---

# Go Observability

> Observability is not about dashboards. It's about answering questions you didn't predict when you wrote the code.

## When to Use This Skill

- Adding logging, tracing, or metrics to a Go service
- Debugging a production issue with insufficient telemetry
- Choosing between slog, zap, zerolog
- Setting up OpenTelemetry tracing
- Designing structured log format for a team

---

## The Three Pillars

| Pillar | What it captures | Tool (Go) |
|--------|------------------|-----------|
| **Logs** | Discrete events with context | `log/slog` (stdlib, Go 1.21+) |
| **Traces** | Request flow across services/functions | OpenTelemetry SDK |
| **Metrics** | Aggregated measurements over time | Prometheus client / OTel metrics |

Use all three. Logs tell you *what happened*. Traces tell you *where it happened in the flow*. Metrics tell you *how often and how fast*.

---

## Structured Logging with slog

### Why slog

- **Stdlib** (Go 1.21+) — no dependency
- **Structured by default** — key-value pairs, not printf
- **Pluggable handlers** — JSON for production, text for dev

### Basic usage

```go
slog.Info("order processed",
    "order_id", order.ID,
    "total", order.Total,
    "duration_ms", elapsed.Milliseconds(),
)
```

Output (JSON handler):
```json
{"time":"2025-01-15T14:30:00Z","level":"INFO","msg":"order processed","order_id":"ord-42","total":1500,"duration_ms":23}
```

### Setup

```go
handler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
})
slog.SetDefault(slog.New(handler))
```

### Logger with context

```go
logger := slog.With("service", "catalog", "version", version)
logger.Info("starting")

// Per-request
reqLogger := logger.With("request_id", requestID, "user_id", userID)
reqLogger.Info("handling request")
```

### Logging rules

1. **Structured, always.** `slog.Info("msg", "key", val)` not `log.Printf("msg %s", val)`.
2. **Log at boundaries.** HTTP handler entry/exit, external API calls, DB queries.
3. **Log errors where they stop propagating** — typically the HTTP handler, not every layer.
4. **Include correlation IDs** (request_id, trace_id) on every log line.
5. **Levels mean something:**

| Level | Use |
|-------|-----|
| `DEBUG` | Development-only detail |
| `INFO` | Normal operations worth recording |
| `WARN` | Unexpected but recoverable |
| `ERROR` | Failed operation requiring attention |

6. **Never log secrets, tokens, PII.** Sanitize before logging.

---

## Distributed Tracing with OpenTelemetry

### Concepts

- **Trace** — a full request journey (across services)
- **Span** — one unit of work within a trace (function, HTTP call, DB query)
- **Context propagation** — trace/span IDs passed through `context.Context`

### Setup

```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() func() {
    exporter, _ := otlptracegrpc.New(ctx)
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource),
    )
    otel.SetTracerProvider(tp)
    return func() { tp.Shutdown(ctx) }
}
```

### Creating spans

```go
tracer := otel.Tracer("catalog-service")

func GetProduct(ctx context.Context, id string) (*Product, error) {
    ctx, span := tracer.Start(ctx, "GetProduct")
    defer span.End()

    span.SetAttributes(attribute.String("product.id", id))

    product, err := repo.FindByID(ctx, id)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
        return nil, err
    }
    return product, nil
}
```

### Auto-instrumentation

Use middleware for automatic span creation:

- **HTTP:** `otelhttp.NewHandler(handler)`
- **gRPC:** `otelgrpc.UnaryServerInterceptor()`
- **SQL:** `otelsql.Open(driver, dsn)` or instrumented drivers
- **Redis, Mongo, etc.:** OTel contrib packages

### Trace propagation

Inject trace context into outgoing HTTP calls:

```go
otelhttp.NewTransport(http.DefaultTransport)
```

Inbound: middleware extracts trace context from headers (`traceparent`).

7. **Always propagate context.** Traces break without `context.Context` flowing through.

---

## Metrics with Prometheus

### Common metrics

| Type | Use | Example |
|------|-----|---------|
| **Counter** | Monotonically increasing | `http_requests_total` |
| **Histogram** | Distribution of values | `http_request_duration_seconds` |
| **Gauge** | Current value (up/down) | `db_connections_active` |

### Minimal setup

```go
import "github.com/prometheus/client_golang/prometheus"

var httpDuration = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Buckets: prometheus.DefBuckets,
    },
    []string{"method", "path", "status"},
)

func init() { prometheus.MustRegister(httpDuration) }
```

### RED method (for services)

- **Rate** — requests per second
- **Errors** — error rate
- **Duration** — latency distribution (p50, p95, p99)

### USE method (for resources)

- **Utilization** — % busy (CPU, memory, disk)
- **Saturation** — queue depth
- **Errors** — resource-level errors

8. **Every service should export at minimum: request rate, error rate, latency histogram.**

---

## Correlation: Tying It All Together

The key: **trace_id and span_id appear in logs, traces, AND metrics labels.**

```go
// Extract trace ID from context and add to logger
span := trace.SpanFromContext(ctx)
traceID := span.SpanContext().TraceID().String()
logger := slog.With("trace_id", traceID)
```

Now you can: see a slow trace → find the matching log lines → find the matching metric spike.

---

## What to Instrument

| Layer | What to capture |
|-------|----------------|
| **HTTP handler** | Method, path, status, duration, request_id |
| **Database calls** | Query type (SELECT/INSERT), table, duration, error |
| **External API calls** | Service, endpoint, status, duration |
| **Business logic** | Domain events (order_created, payment_failed) |
| **Background jobs** | Job type, duration, success/failure |

9. **Instrument boundaries, not every function.** Entry/exit of services, not internal helpers.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `log.Println` (unstructured) | `slog` with key-value pairs |
| Logging at every layer (duplicate lines) | Log at boundaries only |
| No correlation ID | Add request_id / trace_id to every log |
| High-cardinality metric labels (user_id) | Use trace attributes, not metric labels |
| Logging full request/response bodies | Log size + hash; full bodies in debug only |
| No metrics at all | At minimum: RED method per service |
| Tracing without context propagation | Traces break at service boundaries |
| Alerting on every ERROR log | Alert on rate-of-change and thresholds |

---

## Checklist

- [ ] Structured logging with slog (JSON in production)
- [ ] Correlation IDs (request_id, trace_id) on every log line
- [ ] OpenTelemetry tracing with auto-instrumented HTTP/gRPC/DB
- [ ] Context propagated through all function calls
- [ ] RED metrics exported (rate, errors, duration)
- [ ] No secrets or PII in logs
- [ ] Log levels used consistently
- [ ] Dashboards for key metrics (p95 latency, error rate)
- [ ] Alerts on meaningful thresholds (not raw error count)

---

## Related Skills

- [`debugging-methodology`](../debugging-methodology/SKILL.md) — observability feeds the debug loop
- [`go-performance`](../go-performance/SKILL.md) — pprof for performance; OTel for production visibility
- [`agent-observability`](../../ai-engineering/agent-observability/SKILL.md) — same principles for LLM agents
