---
name: gke-deployment
description: >
  Deploying containerised services to GKE — Autopilot vs Standard, Workload
  Identity, Deployment/Service/Ingress manifests, GCLB, HPA, PDB, and
  rolling updates. Use this skill when shipping a service to GKE or
  hardening an existing GKE workload for production.
category: devops
tags: [gcp, gke, kubernetes, deployment, devops, container, cloud]
keywords: [GKE, Autopilot, Workload Identity, Ingress, BackendConfig, GCLB, HPA, PodDisruptionBudget, rolling update, readiness probe, liveness probe]
related: [gcp-fundamentals, k8s-fundamentals, cloud-build-artifact-registry, docker-basics, gcp-observability-spring, gcp-cloud-sql-spring]
---

# GKE Deployment

> Most production GKE problems are someone shipping a Deployment without a readinessProbe, a PDB, or a resource request. Get those three right and the cluster is mostly boring.

## When to Use This Skill

- Deploying a new Spring Boot / Java service to GKE
- Reviewing an existing Deployment / Service / Ingress for production readiness
- Choosing between Autopilot and Standard
- Wiring Workload Identity, HPA, and graceful rollout
- Setting up GCLB ingress and TLS

For Kubernetes basics that aren't GKE-specific, pair with [`k8s-fundamentals`](../k8s-fundamentals/SKILL.md).

---

## Autopilot vs Standard

| | Autopilot | Standard |
|---|---|---|
| Node management | Google manages nodes | You manage node pools |
| Billing | Per-pod resource requests, with **compute classes** (general-purpose / balanced / scale-out / accelerator) setting the per-vCPU / per-GB rate | Per-node (sustained-use / committed-use discounts apply) |
| `DaemonSet`, custom kernel modules | Limited / disallowed | Allowed |
| GPUs / specialised hardware | Limited | Full |
| Default security posture | Hardened (no privileged, no host network) | You configure |
| When to pick | **Default for stateless web services** | When you need node control or predictable per-node cost at scale |

1. **Default to Autopilot for a new Spring Boot service.** Stateless HTTP, no privileged needs — Autopilot does the right thing and removes the node-pool scaling chore.

2. **Switch to Standard when** you need GPU/TPU, run privileged DaemonSets (some observability agents), or have very heavy and steady workloads where reserved-instance per-node pricing is materially cheaper.

3. **You can't convert a cluster between modes.** Pick at create time.

---

## Cluster Setup (Once)

```bash
# Autopilot, regional cluster
gcloud container clusters create-auto prod-cluster \
    --region asia-east1 \
    --release-channel regular

# Verify Workload Identity is on
gcloud container clusters describe prod-cluster \
    --region asia-east1 \
    --format="value(workloadIdentityConfig.workloadPool)"
# → acme-orders-prod.svc.id.goog
```

4. **Regional clusters > zonal.** Control plane and node redundancy across zones; survives a zonal outage.

5. **Release channels:** `rapid` (latest), `regular` (default), `stable` (slowest). **Use `regular` for prod;** `stable` lags features by months.

6. **Authorized networks**: `--enable-master-authorized-networks --master-authorized-networks=<CIDRs>` to restrict who can reach the API server. Combined with `--enable-private-nodes` for fully private clusters.

---

## Namespace per Environment / Service

```bash
kubectl create namespace orders
kubectl label namespace orders env=prod team=orders
```

7. **One namespace per service** in a shared cluster, *or* one namespace per env in a per-service cluster — pick a model. Don't mix.

8. **Apply NetworkPolicies per namespace** to restrict cross-namespace traffic. Defaults are wide-open.

---

## Deployment Manifest (Production-Ready)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orders
  namespace: orders
  labels: { app: orders }
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels: { app: orders }
  template:
    metadata:
      labels: { app: orders }
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/actuator/prometheus"
    spec:
      serviceAccountName: orders-app           # KSA bound to GSA via Workload Identity
      terminationGracePeriodSeconds: 60
      containers:
        - name: app
          image: asia-east1-docker.pkg.dev/acme-orders-prod/apps/orders:1.42.0
          imagePullPolicy: IfNotPresent
          ports:
            - { name: http, containerPort: 8080 }
          env:
            - { name: SPRING_PROFILES_ACTIVE, value: "prod" }
            - { name: JAVA_TOOL_OPTIONS, value: "-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError" }
          envFrom:
            - secretRef: { name: orders-db }    # populated from Secret Manager
          resources:
            requests: { cpu: "500m", memory: "768Mi" }
            limits:   { cpu: "1",    memory: "1Gi" }
          startupProbe:
            httpGet: { path: /actuator/health/liveness, port: http }
            failureThreshold: 30
            periodSeconds: 5
          readinessProbe:
            httpGet: { path: /actuator/health/readiness, port: http }
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet: { path: /actuator/health/liveness, port: http }
            periodSeconds: 10
            failureThreshold: 3
          lifecycle:
            preStop:
              exec: { command: ["/bin/sh", "-c", "sleep 10"] }   # let LB notice us before shutdown
```

9. **Always set both `requests` and `limits`.** Autopilot enforces them. Without requests, scheduling is broken; without limits, a pod can starve neighbours.

10. **Java + memory limit:** set `-XX:MaxRAMPercentage` and `-XX:+ExitOnOutOfMemoryError` so the JVM respects the container limit and dies cleanly on OOM (rather than hanging in degraded GC).

11. **Three probes, three roles:**
    - **Startup**: gives slow apps time to boot before liveness kicks in.
    - **Readiness**: removes the pod from Service endpoints when it can't take traffic. **Always wire to `/actuator/health/readiness`** — Spring updates it during shutdown.
    - **Liveness**: kills + restarts a stuck pod. Wire to `/actuator/health/liveness`.

12. **`maxUnavailable: 0` + `maxSurge: 1`** for safe rollouts of small fleets. For larger ones, raise both proportionally.

13. **`terminationGracePeriodSeconds: 60`** + `preStop sleep 10` is the standard pattern for graceful drain. Boot's `server.shutdown: graceful` finishes the in-flight requests; the sleep gives the load balancer time to see the readiness flip.

14. **Pin image by digest in production.** `image: ...@sha256:...` instead of `:1.42.0` if you don't trust your tag immutability.

---

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: orders
  namespace: orders
  annotations:
    cloud.google.com/neg: '{"ingress": true}'    # Container-native LB (NEG)
    cloud.google.com/backend-config: '{"default": "orders-bcfg"}'
spec:
  type: ClusterIP
  selector: { app: orders }
  ports:
    - { name: http, port: 80, targetPort: http }
```

15. **Use Container-Native Load Balancing (NEG)** with `cloud.google.com/neg`. The GCLB hits pods directly via VPC, skipping kube-proxy hops. Big latency win.

16. **`type: ClusterIP` plus an Ingress** for HTTP. `LoadBalancer` Services give you a regional TCP LB per service and burn IPs.

---

## BackendConfig (GCLB-specific knobs)

```yaml
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: orders-bcfg
  namespace: orders
spec:
  timeoutSec: 30
  connectionDraining: { drainingTimeoutSec: 60 }
  healthCheck:
    type: HTTP
    requestPath: /actuator/health/readiness
    port: 8080
  iap:
    enabled: false
```

17. **Always set `connectionDraining`.** Without it, GCLB cuts in-flight connections during pod shutdown.

18. **GCLB health check is separate from the pod readiness probe.** Configure both; LB probes the pod from outside the cluster.

---

## Ingress with Managed TLS

```yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata: { name: orders-cert, namespace: orders }
spec:
  domains: ["api.acme.com"]
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orders
  namespace: orders
  annotations:
    kubernetes.io/ingress.class: gce
    kubernetes.io/ingress.global-static-ip-name: orders-ip
    networking.gke.io/managed-certificates: orders-cert
    networking.gke.io/v1beta1.FrontendConfig: orders-frontend
spec:
  rules:
    - host: api.acme.com
      http:
        paths:
          - path: /api/*
            pathType: ImplementationSpecific
            backend:
              service: { name: orders, port: { number: 80 } }
```

```yaml
apiVersion: networking.gke.io/v1beta1
kind: FrontendConfig
metadata: { name: orders-frontend, namespace: orders }
spec:
  redirectToHttps: { enabled: true }
  sslPolicy: modern-tls
```

19. **Reserve a global static IP** (`gcloud compute addresses create orders-ip --global`) and reference it. Ephemeral IPs change on Ingress recreate and break DNS.

20. **`ManagedCertificate` provisions Google-managed certs** — no Let's Encrypt setup. DNS must point to the IP first; provisioning takes ~15-60 min.

21. **`FrontendConfig` enables HTTPS redirect and TLS policy.** Don't ship plaintext endpoints.

---

## Workload Identity Wiring

In the same `orders` namespace:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: orders-app
  namespace: orders
  annotations:
    iam.gke.io/gcp-service-account: orders-app@acme-orders-prod.iam.gserviceaccount.com
```

Plus the binding (one-time, on the GSA):

```bash
gcloud iam service-accounts add-iam-policy-binding \
    orders-app@acme-orders-prod.iam.gserviceaccount.com \
    --member "serviceAccount:acme-orders-prod.svc.id.goog[orders/orders-app]" \
    --role   "roles/iam.workloadIdentityUser"
```

22. **Spring code uses ADC.** No code change to use Workload Identity vs SA key — see [`gcp-fundamentals`](../gcp-fundamentals/SKILL.md).

---

## HorizontalPodAutoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: orders, namespace: orders }
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orders
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource: { name: cpu, target: { type: Utilization, averageUtilization: 70 } }
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies: [{ type: Percent, value: 50, periodSeconds: 60 }]
    scaleUp:
      stabilizationWindowSeconds: 0
      policies: [{ type: Percent, value: 100, periodSeconds: 30 }]
```

23. **`minReplicas >= 2`** for redundancy; >= 3 if you also have a PDB requiring `maxUnavailable: 1`.

24. **Scale up fast, scale down slowly.** The defaults are conservative on scale-up — override the `scaleUp` policy.

25. **For non-CPU-bound services, use custom metrics** (RPS via Prometheus + custom-metrics-adapter, or queue depth for workers).

---

## PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: orders, namespace: orders }
spec:
  minAvailable: 2
  selector:
    matchLabels: { app: orders }
```

26. **A PDB protects against voluntary disruptions** (node drains, cluster upgrades), not pod crashes. Without it, a node upgrade can take all your pods at once.

27. **`minAvailable` < replicas.** A PDB equal to replicas blocks all maintenance forever.

---

## Config & Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: orders-app, namespace: orders }
data:
  application-prod.yml: |
    app:
      payment:
        timeout: PT5S
        retry-attempts: 3
```

For secrets, prefer the **Secret Manager CSI driver** so secrets aren't stored in etcd:

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata: { name: orders-secrets, namespace: orders }
spec:
  provider: gke
  parameters:
    secrets: |
      - resourceName: "projects/acme-orders-prod/secrets/db-password/versions/latest"
        path: "db-password"
```

28. **ConfigMap for non-secret config**, Secret Manager for secrets. Don't put DB passwords in a `Secret` if Secret Manager is wired up.

---

## Rolling Update Workflow

```bash
# Build & push (see cloud-build-artifact-registry)
IMAGE=asia-east1-docker.pkg.dev/acme-orders-prod/apps/orders:1.42.1

kubectl -n orders set image deployment/orders app=$IMAGE
kubectl -n orders rollout status deployment/orders --timeout=5m

# Roll back if needed
kubectl -n orders rollout undo deployment/orders
```

29. **`kubectl rollout status` is your gate.** Fail the deploy job if it doesn't return 0.

30. **`kubectl rollout undo` requires `revisionHistoryLimit > 0`.** Don't set it to 0 to "save space" — you give up your one-command rollback.

---

## Observability Hooks

- Wire `/actuator/prometheus` → Managed Prometheus (annotations on the Deployment, see manifest above).
- JSON logs → Cloud Logging (auto-ingested by GKE log agent).
- OpenTelemetry traces → Cloud Trace.

See [`gcp-observability-spring`](../../engineering/gcp-observability-spring/SKILL.md) for the Spring side.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| 502s during deploy | `terminationGracePeriodSeconds`, `preStop sleep`, Spring graceful shutdown, `maxUnavailable: 0` |
| Pod stuck CrashLoopBackOff with OOM | JVM not respecting container limit — set `-XX:MaxRAMPercentage` |
| Liveness restarts pod during long startup | Add `startupProbe`; raise `failureThreshold` |
| Workload Identity returns `unauthenticated` | KSA annotation typo, or missing `roles/iam.workloadIdentityUser` binding on the GSA |
| GCLB health check fails but pod is healthy | `BackendConfig.healthCheck` not set or pointing at a path that requires auth |
| Single replica + `maxUnavailable: 0` won't roll | Either `replicas: 2+` or accept brief downtime with `maxUnavailable: 1` |
| Ingress takes hours to provision | DNS pointing to wrong IP (must point to the static IP *before* cert provisions) |

---

## Pre-Production Checklist

- [ ] Regional Autopilot cluster on the `regular` release channel
- [ ] Workload Identity enabled; KSA annotated and bound to GSA
- [ ] Resource `requests` and `limits` set; JVM honours `MaxRAMPercentage`
- [ ] Startup, readiness, liveness probes configured
- [ ] Graceful shutdown: `terminationGracePeriodSeconds`, `preStop sleep`, Spring `server.shutdown: graceful`
- [ ] `maxUnavailable: 0`, `maxSurge: 1` (or proportional for large fleets)
- [ ] HPA with sane min/max and scale policies
- [ ] PodDisruptionBudget set
- [ ] Service uses NEG; Ingress uses static IP + ManagedCertificate
- [ ] Secrets via Secret Manager CSI, not `Secret` objects
- [ ] Prometheus scrape annotations; logs structured JSON
- [ ] `kubectl rollout` integrated into the deploy pipeline as a gate

---

## Related Skills

- [`gcp-fundamentals`](../gcp-fundamentals/SKILL.md) — IAM, projects, Workload Identity setup
- [`k8s-fundamentals`](../k8s-fundamentals/SKILL.md) — non-GKE-specific Kubernetes
- [`cloud-build-artifact-registry`](../cloud-build-artifact-registry/SKILL.md) — build images and feed them in
- [`docker-basics`](../docker-basics/SKILL.md) — image you're shipping
- [`gcp-observability-spring`](../../engineering/gcp-observability-spring/SKILL.md) — logs/metrics/traces from Spring
- [`spring-boot-fundamentals`](../../engineering/spring-boot-fundamentals/SKILL.md) — graceful shutdown, Actuator config
