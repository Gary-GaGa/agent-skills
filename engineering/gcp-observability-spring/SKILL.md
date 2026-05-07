---
name: gcp-observability-spring
description: >
  Observability for Spring Boot on GCP — JSON logs to Cloud Logging,
  OpenTelemetry traces to Cloud Trace, Micrometer metrics to Managed
  Prometheus, correlation IDs, and SLOs. Use this skill when adding
  telemetry to a Spring Boot service or debugging a production incident.
category: engineering
tags: [java, spring-boot, gcp, observability, logging, tracing, metrics, opentelemetry, monitoring]
keywords: [Cloud Logging, Cloud Trace, Cloud Monitoring, Managed Prometheus, Micrometer, OpenTelemetry, structured logging, trace context, correlation ID, SLO, error budget]
related: [spring-boot-fundamentals, gke-deployment, observability-go, debugging-methodology, gcp-fundamentals]
---

# Observability for Spring Boot on GCP

> Three signals — logs, metrics, traces — connected by a trace ID. Get the wiring once; reuse it forever.

## When to Use This Skill

- Adding logs / metrics / traces to a Spring Boot service running on GKE
- Switching from plaintext logs to structured JSON for Cloud Logging
- Wiring OpenTelemetry traces to Cloud Trace
- Exporting Micrometer metrics to Managed Prometheus
- Debugging an incident where you can't correlate a log line to a request

For the language-agnostic pattern catalogue, [`observability-go`](../observability-go/SKILL.md) covers the same ground from the Go side; this skill is the Spring Boot specialisation.

---

## What to Wire (and in What Order)

1. **Structured JSON logs** to Cloud Logging.
2. **Trace context propagation** (W3C `traceparent`).
3. **Trace export** via OpenTelemetry to Cloud Trace.
4. **Metrics** via Micrometer to Managed Prometheus.
5. **Logs ↔ traces correlation**: every log line carries a trace ID.
6. **SLOs and alerts** in Cloud Monitoring.

Each layer is independently useful. Skip nothing in production.

---

## Logging — Structured JSON to Cloud Logging

### Dependencies

```gradle
implementation 'org.springframework.boot:spring-boot-starter-actuator'
implementation 'net.logstash.logback:logstash-logback-encoder:7.4'
```

### `logback-spring.xml`

```xml
<configuration>
  <springProfile name="prod | staging">
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
      <encoder class="net.logstash.logback.encoder.LogstashEncoder">
        <fieldNames>
          <timestamp>time</timestamp>
          <message>message</message>
          <logger>logger</logger>
          <thread>thread</thread>
        </fieldNames>
        <customFields>{"service":"orders","env":"${SPRING_PROFILES_ACTIVE}"}</customFields>
        <providers>
          <pattern>
            <pattern>{
              "severity": "%level",
              "logging.googleapis.com/trace": "projects/${GOOGLE_CLOUD_PROJECT}/traces/%mdc{trace_id}",
              "logging.googleapis.com/spanId": "%mdc{span_id}",
              "logging.googleapis.com/trace_sampled": "%mdc{trace_flags}"
            }</pattern>
          </pattern>
        </providers>
      </encoder>
    </appender>
    <root level="INFO"><appender-ref ref="STDOUT"/></root>
  </springProfile>

  <springProfile name="local | dev">
    <include resource="org/springframework/boot/logging/logback/base.xml"/>
  </springProfile>
</configuration>
```

1. **Cloud Logging recognises specific fields automatically:**
   - `severity` — log level (`ERROR`, `WARN`, `INFO`, `DEBUG`)
   - `logging.googleapis.com/trace` — full resource name → links to Cloud Trace
   - `logging.googleapis.com/spanId` — current span
   - `logging.googleapis.com/trace_sampled` — boolean
   With these set, the GKE log agent ingests JSON with no extra config.

2. **JSON in prod, plaintext in local.** Plaintext is unreadable as JSON in IDE consoles; JSON is unreadable as plaintext in Cloud Logging. Switch by profile.

3. **`stdout` is the right destination on GKE.** The node's logging agent ships `stdout` to Cloud Logging. Don't write to files.

4. **Log structured context, not concatenated strings:**
   ```java
   log.atInfo()
      .addKeyValue("orderId", orderId)
      .addKeyValue("customerId", customerId)
      .log("Order paid");
   ```
   Becomes `{"message": "Order paid", "orderId": "...", "customerId": "..."}` — queryable in Logs Explorer.

5. **Don't log secrets, full request/response bodies, or PII.** Log identifiers, log status, log timings.

---

## Tracing — OpenTelemetry → Cloud Trace

### Dependencies

```gradle
implementation 'io.micrometer:micrometer-tracing-bridge-otel'
implementation 'io.opentelemetry:opentelemetry-exporter-otlp'
implementation 'com.google.cloud.opentelemetry:exporter-trace:0.30.0'
```

Or, simpler: run the **OpenTelemetry Collector** as a sidecar / DaemonSet and export via OTLP. The Collector forwards to Cloud Trace. This is the recommended path because the Collector handles credentials, batching, and retries uniformly.

### `application.yml`

```yaml
management:
  tracing:
    sampling:
      probability: 0.1            # 10% in prod; 1.0 in dev
  otlp:
    tracing:
      endpoint: http://otel-collector.observability.svc:4318/v1/traces
```

6. **W3C `traceparent` propagation is the default.** All Spring HTTP/WebClient instrumentation reads and writes it automatically.

7. **`spring-boot-starter-actuator` + `micrometer-tracing-bridge-otel` is enough** — Boot 3 wires Micrometer Observation API to OpenTelemetry. `RestTemplate`, `WebClient`, `@RequestMapping`, JDBC, JPA: instrumented.

8. **Sample at 100% in dev, 10% in prod**, more if you can afford the cost. Sub-1% sampling makes hunting individual issues impossible.

9. **Log + trace correlation comes for free** when `LogstashEncoder` reads the MDC — Boot 3 puts `trace_id` and `span_id` there.

### Custom spans

```java
@Service
public class OrderService {
    private final ObservationRegistry registry;

    public Order create(CreateOrderCommand cmd) {
        return Observation.createNotStarted("order.create", registry)
            .lowCardinalityKeyValue("status", "PENDING")
            .observe(() -> doCreate(cmd));
    }
}
```

10. **Use the Observation API**, not raw OpenTelemetry. It produces both metrics and traces from one annotation.

11. **Low-cardinality keys for metrics, high-cardinality for traces.** Don't tag metrics with `userId`; tag with `region` or `tier`.

---

## Metrics — Micrometer → Managed Prometheus

### Dependencies

```gradle
implementation 'io.micrometer:micrometer-registry-prometheus'
```

### `application.yml`

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health, info, metrics, prometheus
  metrics:
    distribution:
      percentiles-histogram:
        http.server.requests: true
    tags:
      service: orders
      env: ${SPRING_PROFILES_ACTIVE}
```

### Deployment annotations

```yaml
metadata:
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8080"
    prometheus.io/path: "/actuator/prometheus"
```

12. **Managed Prometheus auto-discovers via these annotations.** Or use `PodMonitoring` CRD for explicit selection.

13. **Histograms over gauges for latency.** Without histograms you can't compute p95/p99 in queries.

14. **Boot's defaults are good.** `http.server.requests`, JVM, HikariCP, JDBC pool — all there. Add custom counters/timers only for domain metrics:
    ```java
    Counter.builder("orders.created")
        .tag("status", "PENDING")
        .register(registry)
        .increment();
    ```

15. **Beware tag cardinality explosions.** Tag by user ID = death. Tag by enum or country = fine.

---

## Correlation IDs

Spring Boot 3 + Micrometer Tracing puts `trace_id` and `span_id` in the MDC automatically. For **a custom request ID** you also want to expose:

```java
@Component
public class CorrelationIdFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String requestId = Optional.ofNullable(req.getHeader("X-Request-Id"))
                .orElseGet(() -> UUID.randomUUID().toString());
        MDC.put("requestId", requestId);
        res.setHeader("X-Request-Id", requestId);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.remove("requestId");
        }
    }
}
```

16. **Trace ID is for cross-service correlation; request ID is for human-friendly support.** Print both in logs.

17. **Propagate trace context outbound.** `RestTemplate` / `WebClient` from Boot 3 do this automatically. If you call gRPC or Pub/Sub directly, attach `traceparent` manually.

---

## Pub/Sub Trace Propagation

```java
Map<String, String> attrs = new HashMap<>();
W3CTraceContextPropagator.getInstance().inject(Context.current(), attrs, Map::put);
attrs.put("event-type", "OrderCreated");
pubsub.publish(topic, payload, attrs);
```

18. **Publishing is a side effect; trace it as one.** Otherwise the consumer's trace shows up as a brand-new request.

19. **On the consumer**, extract trace context from message attributes and re-establish it before processing. The Spring Cloud GCP Pub/Sub instrumentation does this if you enable it; verify in Cloud Trace.

---

## Cloud Monitoring: SLOs & Alerts

20. **Define SLIs first**: availability (`http_server_requests_seconds_count{status!~"5.."} / count`), latency p99, error rate. Don't alert on raw CPU.

21. **SLO targets per service**: e.g. 99.9% availability, p95 < 300ms over 30 days. Set the **error budget** and alert when burn rate exceeds 2% of monthly budget per hour.

22. **Alert on symptoms (user-visible) before causes (infra).** A spike in 500s page-traders; a CPU spike doesn't.

23. **Use Cloud Monitoring's native alerting policies** for prometheus metrics — they integrate with notification channels and incidents.

---

## Local Development

```yaml
# application-local.yml
management:
  tracing:
    sampling:
      probability: 1.0
  otlp:
    tracing:
      endpoint: http://localhost:4318/v1/traces  # or skip; tracing disabled if no exporter
logging:
  level:
    org.hibernate.SQL: DEBUG
```

24. **Run a local OpenTelemetry Collector + Jaeger UI** for trace inspection without sending to Cloud Trace:
    ```bash
    docker run -p 16686:16686 -p 4318:4318 jaegertracing/all-in-one:latest
    ```

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Logs show as plain `textPayload` in Cloud Logging | LogstashEncoder not active or pattern fields wrong; check `severity` is set |
| Trace ID present in logs but no traces in Cloud Trace | Exporter endpoint wrong, sampling at 0%, or Collector not running |
| p99 latency unavailable in dashboards | Histogram disabled — turn on `percentiles-histogram` |
| Metrics cardinality explodes; Prometheus OOMs | A high-cardinality tag (user/order ID) on a metric — drop it |
| Trace breaks when calling Pub/Sub or gRPC | Manual context propagation needed; framework instrumentation incomplete |
| Cloud Logging quota exhausted | Drop debug-level logs in prod; sample noisy paths |

---

## Pre-Production Checklist

- [ ] Logs to stdout in JSON, with `severity` and `logging.googleapis.com/trace` fields
- [ ] No PII / secrets in log payloads
- [ ] OpenTelemetry tracing wired; Collector or direct Cloud Trace exporter
- [ ] Sampling rate set per environment (1.0 dev, 0.1 prod)
- [ ] Micrometer Prometheus endpoint exposed; histograms enabled
- [ ] Deployment annotated for Managed Prometheus scraping
- [ ] Trace context propagated on outbound HTTP, gRPC, Pub/Sub
- [ ] `X-Request-Id` filter in place; trace + request IDs in every log
- [ ] SLOs defined; alerts on burn rate, not raw signals
- [ ] Incident runbook references log/trace/metric queries by name

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — Actuator, profiles
- [`gke-deployment`](../../devops/gke-deployment/SKILL.md) — Prometheus annotations, log paths
- [`gcp-fundamentals`](../../devops/gcp-fundamentals/SKILL.md) — enabling APIs, IAM
- [`observability-go`](../observability-go/SKILL.md) — same patterns, Go-flavoured
- [`debugging-methodology`](../debugging-methodology/SKILL.md) — how to use signals during incidents
