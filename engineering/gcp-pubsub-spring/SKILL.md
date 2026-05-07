---
name: gcp-pubsub-spring
description: >
  Google Cloud Pub/Sub from Spring Boot via Spring Cloud GCP — publishing,
  pull/push subscribers, ack/nack semantics, ordering keys, dead-letter
  topics, exactly-once delivery. Use this skill when a Spring service
  publishes or consumes Pub/Sub messages.
category: engineering
tags: [java, spring-boot, gcp, pubsub, messaging, event-driven, integration]
keywords: [Pub/Sub, Spring Cloud GCP, PubSubTemplate, ordering keys, dead-letter, exactly-once, push subscription, pull subscription, ack deadline]
related: [spring-boot-fundamentals, gcp-fundamentals, event-driven-architecture, microservices-patterns]
---

# Google Pub/Sub from Spring Boot

> Pub/Sub is at-least-once by default. Design idempotent consumers, configure dead-letters, and treat ordering as opt-in.

## When to Use This Skill

- Publishing domain events from a Spring Boot service to Pub/Sub
- Consuming Pub/Sub messages with a pull or push subscriber
- Choosing between ordering, exactly-once, and dead-letter configurations
- Diagnosing duplicate messages, redelivery storms, or stuck subscribers
- Migrating from RabbitMQ / Kafka to Pub/Sub

For broader event-driven patterns (sagas, CQRS, idempotency), pair with [`event-driven-architecture`](../event-driven-architecture/SKILL.md).

---

## Pub/Sub Model in 90 Seconds

```
Publisher  →  Topic  →  Subscription(s)  →  Subscriber(s)
                          ▲
                  one per consumer group
```

- **Topic**: where you publish.
- **Subscription**: a queue attached to a topic. Each subscription gets every message published. Multiple subscribers on one subscription compete for messages.
- **Pull vs Push**: pull subscribers ask for messages; push subscribers receive HTTPS POSTs from Pub/Sub.
- **Ack deadline**: time the subscriber has to ack a message before it's redelivered (default 10s, max 600s).
- **Delivery**: at-least-once by default. Exactly-once is opt-in per subscription.

1. **One subscription per consumer system.** Don't share `orders-events` between the `inventory` service and the `email` service — give each its own subscription.

2. **Plan for redelivery.** Even with exactly-once enabled, your consumer must be idempotent. Build idempotency into the message or the storage layer.

---

## Setup

### Dependencies

```gradle
implementation 'com.google.cloud:spring-cloud-gcp-starter-pubsub:5.6.0'
```

### Configuration

```yaml
spring:
  cloud:
    gcp:
      project-id: ${GOOGLE_CLOUD_PROJECT:acme-orders-prod}
      pubsub:
        publisher:
          batching:
            enabled: true
            element-count-threshold: 100
            delay-threshold-seconds: 0.05
            flow-control:
              max-outstanding-element-count: 10000
        subscriber:
          executor-threads: 8
          max-ack-extension-period: 600s
          parallel-pull-count: 2
```

3. **Auth via ADC.** On GKE with Workload Identity, no extra config needed. Locally, `gcloud auth application-default login`. See [`gcp-fundamentals`](../../devops/gcp-fundamentals/SKILL.md).

4. **Required IAM roles:**
   - Publisher SA: `roles/pubsub.publisher` on the topic.
   - Subscriber SA: `roles/pubsub.subscriber` on the subscription.

---

## Publishing

```java
@Service
public class OrderEventPublisher {

    private final PubSubTemplate pubsub;
    private static final String TOPIC = "orders-events";

    public OrderEventPublisher(PubSubTemplate pubsub) {
        this.pubsub = pubsub;
    }

    public void publishOrderCreated(Order order) {
        OrderCreatedEvent event = OrderCreatedEvent.from(order);
        Map<String, String> headers = Map.of(
            "event-type", "OrderCreated",
            "event-id", UUID.randomUUID().toString(),
            "schema-version", "1"
        );

        CompletableFuture<String> future = pubsub.publish(TOPIC, event, headers);

        future.whenComplete((messageId, error) -> {
            if (error != null) {
                log.error("Failed to publish OrderCreated for {}", order.id(), error);
            } else {
                log.info("Published OrderCreated for {} → {}", order.id(), messageId);
            }
        });
    }
}
```

5. **Use attributes (headers) for routing and metadata**, not the body. `event-type`, `event-id`, `schema-version`, `correlation-id`. Keep the body for the domain payload.

6. **Always log the published `messageId`** at info — it's the only stable correlation key with Pub/Sub-side logs.

7. **Don't `.get()` on the future in a request thread.** Block only when sending is part of an outbox pattern (atomic with the DB transaction); otherwise let it complete async and handle errors via the callback.

8. **Outbox pattern for transactional publishing.** Save the event to an `outbox` table inside the same DB transaction; a separate worker reads from outbox and publishes. Without it, `tx commit + publish failed` desyncs DB and bus. See [`event-driven-architecture`](../event-driven-architecture/SKILL.md).

---

## Ordering

Pub/Sub orders messages with the **same ordering key** within a region.

```bash
gcloud pubsub topics create orders-events
gcloud pubsub subscriptions create orders-events.inventory \
    --topic=orders-events \
    --enable-message-ordering
```

```java
public void publishOrderCreated(Order order) {
    Map<String, String> headers = Map.of(
        "event-type", "OrderCreated",
        "googclient_OrderingKey", order.id().toString()   // Spring Cloud GCP convention
    );
    pubsub.publish("orders-events", event, headers);
}
```

9. **Ordering is opt-in per subscription.** Without `--enable-message-ordering` on the subscription, messages may be delivered out of order even if you set the key.

10. **Ordering key = aggregate ID** in DDD terms. Ordering "all orders in the system" doesn't scale; ordering "events for order 42" does.

11. **A single failed message blocks the ordering key.** Keep your consumer fast and resilient, or accept the blocking trade-off explicitly.

---

## Pull Subscriber

For long-running workers in GKE pods.

### Create the subscription

```bash
gcloud pubsub subscriptions create orders-events.inventory \
    --topic=orders-events \
    --ack-deadline=30 \
    --message-retention-duration=7d \
    --dead-letter-topic=projects/$PROJECT_ID/topics/orders-events-dlq \
    --max-delivery-attempts=5
```

### Spring listener

```java
@Configuration
public class PubSubInboundConfig {

    @Bean
    public Subscriber inventoryListener(PubSubTemplate pubsub, OrderEventHandler handler) {
        return pubsub.subscribe("orders-events.inventory", message -> {
            try {
                String eventType = message.getPubsubMessage().getAttributesMap().get("event-type");
                String eventId   = message.getPubsubMessage().getAttributesMap().get("event-id");
                handler.handle(eventType, eventId, message.getPubsubMessage().getData().toStringUtf8());
                message.ack();
            } catch (TransientException e) {
                log.warn("transient error, will retry", e);
                message.nack();                        // immediate redelivery
            } catch (Exception e) {
                log.error("permanent error, dead-lettering", e);
                message.ack();                         // ack so it isn't re-tried; alternatively let max-delivery-attempts route it to DLQ
            }
        });
    }
}
```

12. **`ack` after the side effect succeeds.** Acking before processing means you lose the message on failure.

13. **`nack` for transient failures.** Pub/Sub redelivers per its retry policy. Use exponential backoff via subscription config, not by holding the thread.

14. **Make the handler idempotent.** Track processed `event-id`s in a small table or cache, or use `INSERT ... ON CONFLICT DO NOTHING` semantics on the side-effect write.

15. **Set `ack-deadline`** to your 99th-percentile processing time + buffer. Too short → unnecessary redelivery; too long → slow recovery from a stuck pod.

---

## Dead-Letter Topic

```bash
gcloud pubsub topics create orders-events-dlq

# Subscribe an alerting / re-drive subscription
gcloud pubsub subscriptions create orders-events-dlq.alerts \
    --topic=orders-events-dlq

# IAM: subscription needs to be allowed to publish to the DLQ
gcloud pubsub topics add-iam-policy-binding orders-events-dlq \
    --member="serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-pubsub.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"
```

16. **Always configure a DLQ.** Without it, "poison" messages cycle forever and the subscription's backlog grows.

17. **Alert on DLQ depth, not on the main subscription's redelivery rate.** Redelivery is normal; DLQ growth is not.

18. **Build a re-drive job.** A small worker that reads the DLQ, re-publishes to the main topic after fix, and acks. Don't manually click in the console.

---

## Push Subscriber (HTTPS Receiver)

For simple stateless handlers; integrates well with Cloud Run.

```bash
gcloud pubsub subscriptions create orders-events.email \
    --topic=orders-events \
    --push-endpoint=https://orders.acme.com/internal/pubsub/orders \
    --push-auth-service-account=pubsub-pusher@$PROJECT_ID.iam.gserviceaccount.com
```

```java
@RestController
@RequestMapping("/internal/pubsub/orders")
public class OrdersPushController {

    @PostMapping
    public ResponseEntity<Void> handle(@RequestBody PushMessage push) {
        // Pub/Sub authenticates via OIDC token in Authorization header
        // Validate the token, then process
        try {
            handler.handle(push.message().attributes(), push.message().dataDecoded());
            return ResponseEntity.noContent().build();             // 204 = ack
        } catch (TransientException e) {
            return ResponseEntity.status(503).build();             // any non-2xx = nack
        }
    }
}
```

19. **HTTP 2xx = ack; non-2xx = nack.** No body needed.

20. **Verify the OIDC token** that Pub/Sub sends in the `Authorization` header. Don't expose the endpoint without auth.

21. **Pull > push for high-throughput workers** — pull can flow-control. Push subscribers can be overrun by traffic spikes.

---

## Exactly-Once Delivery

```bash
gcloud pubsub subscriptions create orders-events.payment \
    --topic=orders-events \
    --enable-exactly-once-delivery \
    --ack-deadline=60
```

22. **Even with exactly-once, build idempotent consumers.** It guarantees no duplicate ack-delivery, but your code may still re-process if it crashed mid-side-effect.

23. **Exactly-once requires a longer minimum ack deadline (60s).** Plan throughput accordingly.

---

## Schema Registry (Optional)

Pub/Sub supports Avro and protobuf schemas. Worth the trouble when schemas are versioned and consumed by multiple services:

```bash
gcloud pubsub schemas create orders-events-schema \
    --type=AVRO \
    --definition-file=schema.avsc

gcloud pubsub topics create orders-events --schema=orders-events-schema --message-encoding=JSON
```

24. **JSON-on-a-schema** is the easiest starting point — human-readable in the console, validated by Pub/Sub.

25. **Treat the schema as code.** Version it, evolve it under backward-compat rules (additive only on the existing version; new major version → new topic).

---

## Local Development

Use the **Pub/Sub emulator**:

```bash
gcloud beta emulators pubsub start --project=local-test --host-port=localhost:8085
export PUBSUB_EMULATOR_HOST=localhost:8085
```

```yaml
# application-local.yml
spring:
  cloud:
    gcp:
      pubsub:
        emulator-host: localhost:8085
      project-id: local-test
```

26. **Topics and subscriptions don't auto-create on the emulator.** Add a small startup script in your local-dev profile.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Messages re-deliver constantly | Handler taking longer than `ack-deadline`; raise deadline or use `max-ack-extension-period` |
| `nack` goes into a tight redelivery loop | Configure subscription `retry-policy` with exponential backoff (`min-backoff`, `max-backoff`) |
| DLQ never receives messages despite errors | The handler `ack`s on exception; switch to `nack` and let `max-delivery-attempts` route to DLQ |
| Ordering broken even with key set | Subscription not created with `--enable-message-ordering` |
| Subscriber pod uses 100% CPU on idle | `parallel-pull-count` set too high for low traffic — lower it |
| Publisher futures never complete in tests | Replace `PubSubTemplate` with a `@MockBean` or use the emulator |

---

## Pre-Production Checklist

- [ ] One subscription per consumer system
- [ ] Dead-letter topic + alert on DLQ depth
- [ ] Ack deadline aligned with 99th-percentile processing time
- [ ] Idempotent consumers (event-id tracking or upsert semantics)
- [ ] Outbox pattern for publishers that must stay consistent with the DB
- [ ] Ordering keys only where needed; aggregate-ID grain
- [ ] OIDC auth on push endpoints, or pull workers in private subnets
- [ ] Schema (Avro/JSON) defined and versioned for cross-service topics
- [ ] Emulator wired into `local` profile

---

## Related Skills

- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — bean wiring, config, profiles
- [`event-driven-architecture`](../event-driven-architecture/SKILL.md) — outbox, sagas, eventual consistency
- [`microservices-patterns`](../microservices-patterns/SKILL.md) — when to publish events vs sync calls
- [`gcp-fundamentals`](../../devops/gcp-fundamentals/SKILL.md) — IAM, Workload Identity, ADC
- [`gcp-observability-spring`](../gcp-observability-spring/SKILL.md) — tracing message flow with correlation IDs
