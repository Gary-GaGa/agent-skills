---
name: k8s-fundamentals
description: >
  Kubernetes fundamentals for developers — pods, deployments, services, configmaps,
  secrets, health checks, resource limits, and common debugging. Use this skill
  when deploying to Kubernetes, writing manifests, or debugging pod issues.
  Operator-level topics (cluster setup, networking) are out of scope.
category: devops
tags: [kubernetes, k8s, devops, deployment, container]
related: [docker-basics, github-actions, terraform-basics]
---

# Kubernetes Fundamentals

> Kubernetes manages containers at scale. As a developer, you need to know: how to describe what your app needs (manifests), how K8s runs it (pods/deployments), and how to debug when it doesn't.

## When to Use This Skill

- Deploying a containerized app to Kubernetes
- Writing or reviewing K8s manifests
- Debugging pod crashes, restarts, or connectivity issues
- Configuring health checks, resource limits, or scaling

---

## Core Objects

| Object | What it is | Analogy |
|--------|------------|---------|
| **Pod** | Smallest deployable unit; 1+ containers | A single process |
| **Deployment** | Manages pod replicas with rolling updates | A process manager |
| **Service** | Stable network endpoint for pods | A load balancer |
| **ConfigMap** | Non-sensitive config injected into pods | Environment file |
| **Secret** | Sensitive config (base64 encoded at rest) | `.env` with secrets |
| **Ingress** | HTTP routing from outside the cluster | Reverse proxy |
| **Namespace** | Logical isolation within a cluster | Folders |

---

## Deployment Manifest (Go App Template)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-api
  labels:
    app: catalog-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: catalog-api
  template:
    metadata:
      labels:
        app: catalog-api
    spec:
      containers:
        - name: catalog-api
          image: myregistry/catalog-api:v1.2.3
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /readyz
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: catalog-secrets
                  key: database-url
```

---

## Key Rules

### Images

1. **Pin image tags.** `v1.2.3`, not `latest`. `latest` is not reproducible.
2. **Use a private registry** for production images. Don't pull from Docker Hub in prod.

### Resources

3. **Always set `requests` and `limits`.** Without them, a pod can consume the entire node.
4. **`requests` = guaranteed minimum; `limits` = hard cap.** Set requests to typical usage; limits to peak.
5. **Memory limits are hard kills.** Exceeding memory limit → OOMKilled. Set generously.
6. **CPU limits are throttled, not killed.** Pod slows down but doesn't die.

### Health Checks

7. **`livenessProbe`: is the process stuck?** Failing → K8s restarts the pod.
8. **`readinessProbe`: can it serve traffic?** Failing → removed from Service endpoints (no traffic).
9. **`startupProbe`: for slow-starting apps.** Replaces liveness during startup; prevents premature kills.
10. **Don't make liveness depend on external services.** DB down ≠ your pod is broken. Use readiness for that.

### Config

11. **ConfigMap for non-sensitive config.** Mount as file or inject as env vars.
12. **Secret for sensitive config.** Same API, but encrypted at rest (with proper config).
13. **Don't bake config into the image.** Externalize everything that changes per environment.

---

## Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: catalog-api
spec:
  selector:
    app: catalog-api
  ports:
    - port: 80
      targetPort: 8080
  type: ClusterIP
```

| Type | Scope |
|------|-------|
| `ClusterIP` | Internal only (default) |
| `NodePort` | Accessible on each node's IP:port |
| `LoadBalancer` | Cloud load balancer (external) |

14. **Use `ClusterIP` for internal services.** Expose externally via Ingress, not `LoadBalancer` per service.

---

## Common Debugging

```bash
kubectl get pods                          # list pods
kubectl describe pod <name>               # events, conditions
kubectl logs <pod> [-c container]         # stdout/stderr
kubectl logs <pod> --previous             # logs from crashed container
kubectl exec -it <pod> -- sh             # shell into container
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl top pod                           # resource usage
```

| Symptom | Likely cause | Check |
|---------|--------------|-------|
| `CrashLoopBackOff` | App crashes on start | `kubectl logs --previous` |
| `ImagePullBackOff` | Wrong image name/tag or auth | `kubectl describe pod` → Events |
| `OOMKilled` | Memory limit too low | Increase `limits.memory` |
| `Pending` | No node has enough resources | `kubectl describe pod` → Events |
| `0/3 ready` | Readiness probe failing | Check probe endpoint; `kubectl logs` |
| Can't connect to Service | Wrong selector labels, wrong port | `kubectl get endpoints <svc>` |

---

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: catalog-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: catalog-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

15. **Set `minReplicas: 2` for production.** Single replica = no fault tolerance.

---

## Rolling Updates

Deployment default behavior: replace pods gradually.

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

16. **`maxUnavailable: 0`** — never have fewer pods than desired during update. Requires `maxSurge ≥ 1`.
17. **Readiness probes gate traffic.** New pods receive traffic only when ready.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `latest` image tag | Pin version tags |
| No resource requests/limits | Always set both |
| Liveness probe checks DB | Liveness = process health only; readiness = dependencies |
| Single replica in prod | `minReplicas: 2` minimum |
| Secrets in ConfigMap | Use Secret objects |
| `kubectl apply` from laptop in prod | Apply from CI/CD only |
| No namespace separation | At minimum: `dev`, `staging`, `prod` namespaces |

---

## Checklist

- [ ] Image tag pinned (not `latest`)
- [ ] Resource requests and limits set
- [ ] Liveness probe checks process health (not external deps)
- [ ] Readiness probe checks service-ability
- [ ] Config externalized via ConfigMap / Secret
- [ ] Secrets not in plaintext in manifests (use sealed-secrets or external secret manager)
- [ ] Service type is appropriate (ClusterIP for internal)
- [ ] Min replicas ≥ 2 for production
- [ ] Rolling update strategy with `maxUnavailable: 0`
- [ ] Namespace per environment

---

## Related Skills

- [`docker-basics`](../docker-basics/SKILL.md) — build the image K8s runs
- [`github-actions`](../github-actions/SKILL.md) — deploy to K8s from CI
- [`terraform-basics`](../terraform-basics/SKILL.md) — provision the cluster itself
