---
name: gcp-cloud-sql-spring
description: >
  Connecting Spring Boot to Cloud SQL (PostgreSQL/MySQL) on GCP — Cloud SQL
  Java Connector vs Auth Proxy, IAM database authentication, HikariCP sizing,
  private IP, and read replicas. Use this skill when wiring a Spring Boot
  service to Cloud SQL on GKE or Cloud Run, or when scaling an existing setup.
category: engineering
tags: [java, spring-boot, gcp, database, postgresql, jpa, integration, backend]
keywords: [Cloud SQL, Cloud SQL Auth Proxy, Cloud SQL Java Connector, IAM database authentication, HikariCP, private IP, read replica, PgBouncer]
related: [spring-boot-fundamentals, spring-data-jpa, gcp-fundamentals, gke-deployment]
---

# Cloud SQL from Spring Boot

> Use the Java Connector for direct, mutual-TLS, IAM-authenticated access — no sidecar needed. Or use the proxy when ops prefers a uniform sidecar model.

## When to Use This Skill

- Wiring a new Spring Boot service to Cloud SQL Postgres/MySQL
- Choosing between the Cloud SQL Auth Proxy and the Java Connector
- Replacing password auth with IAM database authentication
- Sizing HikariCP and the Cloud SQL instance for a given workload
- Adding read replicas or migrating to private IP

For JPA/Hibernate patterns, pair with [`spring-data-jpa`](../spring-data-jpa/SKILL.md).

---

## Pick a Connection Strategy

| Option | When |
|---|---|
| **Cloud SQL Java Connector** (`com.google.cloud.sql:postgres-socket-factory`) | Default. No sidecar, mutual TLS handled by JDBC, supports IAM auth. |
| **Cloud SQL Auth Proxy sidecar** | Org standard mandates a sidecar; non-Java consumers in same pod; you want the proxy's connection limits. |
| **Direct private IP** | Cluster and instance both on same VPC and you don't need IAM auth or short-lived certs. Lowest abstraction, no extra dependencies. |

1. **Default to the Java Connector for new Spring Boot services.** One JAR, no sidecar, IAM auth out of the box.

2. **Pick the proxy** when there's a platform mandate or other languages share the workload.

3. **Direct private IP is fine for simple setups** but you lose IAM auth and the connector's automatic cert rotation.

---

## Java Connector

### Dependencies

```gradle
implementation 'org.postgresql:postgresql'
implementation 'com.google.cloud.sql:postgres-socket-factory:1.19.1'
```

### `application.yml`

```yaml
spring:
  datasource:
    url: jdbc:postgresql:///orders?cloudSqlInstance=acme-orders-prod:asia-east1:orders-db&socketFactory=com.google.cloud.sql.postgres.SocketFactory&user=orders-app@acme-orders-prod.iam&enableIamAuth=true
    # Driver fills in `password` from a one-time IAM token; no static password needed
    hikari:
      maximum-pool-size: 10
      minimum-idle: 2
      connection-timeout: 3000
      max-lifetime: 1500000   # 25min, < Cloud SQL idle limit
```

4. **`cloudSqlInstance` format**: `<project>:<region>:<instance>`. Wrong regions are the #1 cause of "ConnectorException: instance not found".

5. **`enableIamAuth=true`** lets the SA authenticate without a password. The connector fetches a short-lived token; nothing static to leak.

6. **The DB user matches the SA email**, with `@<project>.iam` suffix for service accounts and `@acme.com` for human users — minus the trailing `.gserviceaccount.com`.

### Required IAM

```bash
gcloud projects add-iam-policy-binding acme-orders-prod \
    --member "serviceAccount:orders-app@acme-orders-prod.iam.gserviceaccount.com" \
    --role   "roles/cloudsql.client"

gcloud projects add-iam-policy-binding acme-orders-prod \
    --member "serviceAccount:orders-app@acme-orders-prod.iam.gserviceaccount.com" \
    --role   "roles/cloudsql.instanceUser"
```

7. **`cloudsql.client`** allows connecting; **`cloudsql.instanceUser`** is required for IAM auth specifically.

### Create the DB user

```bash
gcloud sql users create orders-app@acme-orders-prod.iam \
    --instance=orders-db \
    --type=cloud_iam_service_account
```

```sql
-- Grant only what the service needs
GRANT CONNECT ON DATABASE orders TO "orders-app@acme-orders-prod.iam";
GRANT USAGE ON SCHEMA public TO "orders-app@acme-orders-prod.iam";
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO "orders-app@acme-orders-prod.iam";
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "orders-app@acme-orders-prod.iam";
```

8. **Don't grant superuser to the app SA.** Migrations should run as a separate user (or a separate SA with broader rights) used only by the migration job.

---

## Cloud SQL Auth Proxy Sidecar

When the platform standard is sidecar:

```yaml
# Deployment.spec.template.spec
containers:
  - name: app
    image: ...
    env:
      - { name: SPRING_DATASOURCE_URL, value: "jdbc:postgresql://127.0.0.1:5432/orders" }

  - name: cloud-sql-proxy
    image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.13.0
    args:
      - "--structured-logs"
      - "--port=5432"
      - "--auto-iam-authn"
      - "acme-orders-prod:asia-east1:orders-db"
    securityContext:
      runAsNonRoot: true
    resources:
      requests: { cpu: "100m", memory: "64Mi" }
      limits:   { cpu: "500m", memory: "128Mi" }
serviceAccountName: orders-app   # Workload Identity → GSA with roles/cloudsql.client
```

9. **Same IAM requirements as the Java Connector.** The proxy is just a cleaner UX in some environments.

10. **Configure pod-level lifecycle so the proxy outlives the app.** Otherwise the app loses DB during shutdown.

---

## HikariCP Sizing

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 2
      connection-timeout: 3000        # fail fast → K8s retries
      idle-timeout: 600000
      max-lifetime: 1500000           # < Cloud SQL idle/wal limits
      leak-detection-threshold: 5000  # log connections held > 5s
```

11. **Pool size × pod count must fit the Cloud SQL `max_connections` quota.** Cloud SQL Postgres caps depend on tier (db-custom-2-4096 ≈ 100; bigger tiers higher). Run the math.

12. **At scale, front Cloud SQL with PgBouncer** (transaction pooling). Without it, autoscaling Spring pods can exhaust connections. Many teams self-host PgBouncer in the cluster; alternatively use Cloud SQL's built-in connection pooling on supported tiers.

13. **`max-lifetime` < Cloud SQL idle disconnect.** Otherwise pods carry stale connections until the next query fails.

14. **`leak-detection-threshold` of 5s** in non-prod helps catch missing `@Transactional` boundaries that hold connections too long.

---

## Private IP

Production should use **Private IP only**:

```bash
gcloud sql instances create orders-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-8192 \
    --region=asia-east1 \
    --network=projects/acme-shared/global/networks/main \
    --no-assign-ip                                        # private only
```

15. **No public IP in production.** A private IP is reachable only from the VPC; the Java Connector still works because it talks to a private endpoint.

16. **VPC Service Controls** for compliance — they wrap the API itself, not just the network. Pair with private IP, not as an alternative.

---

## Read Replicas

```bash
gcloud sql instances create orders-db-replica-1 \
    --master-instance-name=orders-db \
    --tier=db-custom-2-4096 \
    --region=asia-east1
```

```yaml
# Spring config: two DataSources
app:
  datasource:
    primary:   "jdbc:postgresql:///orders?cloudSqlInstance=...orders-db&socketFactory=..."
    replica:   "jdbc:postgresql:///orders?cloudSqlInstance=...orders-db-replica-1&socketFactory=..."
```

```java
@Configuration
public class DataSourceConfig {

    @Primary
    @Bean
    @ConfigurationProperties("spring.datasource.primary.hikari")
    public DataSource primary() { return DataSourceBuilder.create().url(props.primary()).build(); }

    @Bean
    @ConfigurationProperties("spring.datasource.replica.hikari")
    public DataSource replica() { return DataSourceBuilder.create().url(props.replica()).build(); }

    @Bean
    public DataSource routing(@Qualifier("primary") DataSource p, @Qualifier("replica") DataSource r) {
        var routing = new AbstractRoutingDataSource() {
            @Override protected Object determineCurrentLookupKey() {
                return TransactionSynchronizationManager.isCurrentTransactionReadOnly() ? "replica" : "primary";
            }
        };
        routing.setTargetDataSources(Map.of("primary", p, "replica", r));
        routing.setDefaultTargetDataSource(p);
        return routing;
    }
}
```

17. **`@Transactional(readOnly = true)` routes to the replica.** The whole flow depends on the read-only flag being set correctly on services.

18. **Replicas lag.** Don't read-after-write your own changes from a replica. Either pin to primary for the read in that flow, or use cursors that tolerate staleness.

---

## Migrations

19. **Run Flyway/Liquibase as a separate Job, not inside app startup**, in production. App startup is the wrong place for a slow or risky DDL change.

   ```yaml
   # k8s Job that runs migrations before the app rolls out
   apiVersion: batch/v1
   kind: Job
   metadata: { name: orders-migrate-1.42.0 }
   spec:
     template:
       spec:
         serviceAccountName: orders-migrate   # broader permissions than the app SA
         restartPolicy: Never
         containers:
           - name: migrate
             image: asia-east1-docker.pkg.dev/.../orders:1.42.0
             command: ["java", "-jar", "/app/app.jar", "--spring.profiles.active=migrate"]
   ```

20. **The migration SA has DDL rights, the app SA does not.** Least privilege, again.

---

## Local Development

```bash
# Option A: Cloud SQL Auth Proxy locally
cloud-sql-proxy acme-orders-dev:asia-east1:orders-db &

# Option B: Local Postgres in Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=local postgres:15
```

21. **Don't share a Cloud SQL dev instance across developers.** Schema drift, fixture pollution. Local Docker > shared remote DB.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `org.postgresql.util.PSQLException: FATAL: PAM authentication failed` | The DB user wasn't created as a `cloud_iam_service_account` user, or `enableIamAuth` is missing |
| Pods exhaust connections under autoscale | Add PgBouncer; reduce per-pod pool size |
| `Connection is not available, request timed out after 30000ms` | Pool too small, leaked connection (`leak-detection-threshold`), or DB instance saturated |
| Long startup blamed on Hibernate | Migrations are running on app startup; split into a Job |
| Read replica is hot, primary cool | Code uses `readOnly = true` everywhere; reads from replica even when consistency required |
| Connection drops every ~10 minutes | `max-lifetime` > Cloud SQL idle timeout — lower it |

---

## Pre-Production Checklist

- [ ] Cloud SQL instance with private IP only
- [ ] App SA: `roles/cloudsql.client` + `roles/cloudsql.instanceUser`
- [ ] DB user is an IAM SA user; no static password
- [ ] App SA has table-level grants only; no superuser
- [ ] Migrations run as a separate Job with broader privileges
- [ ] HikariCP pool size × replicas ≤ Cloud SQL `max_connections`
- [ ] `max-lifetime` < instance idle timeout
- [ ] `leak-detection-threshold` set in non-prod
- [ ] PgBouncer in front if pod count × pool > 50
- [ ] `@Transactional(readOnly = true)` audited if read replicas are used

---

## Related Skills

- [`spring-data-jpa`](../spring-data-jpa/SKILL.md) — entities, repositories, transactions
- [`spring-boot-fundamentals`](../spring-boot-fundamentals/SKILL.md) — DataSource auto-config and profiles
- [`gcp-fundamentals`](../../devops/gcp-fundamentals/SKILL.md) — Workload Identity, ADC, IAM
- [`gke-deployment`](../../devops/gke-deployment/SKILL.md) — pod-side proxy / connector wiring
- [`database-migrations`](../../data/database-migrations/SKILL.md) — Flyway/Liquibase strategy
