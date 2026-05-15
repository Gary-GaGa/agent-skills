---
name: gcp-fundamentals
description: >
  GCP fundamentals — projects, IAM, service accounts, Workload Identity,
  gcloud CLI, Application Default Credentials (ADC), and Secret Manager. Use
  this skill when bootstrapping a GCP project, granting access to a service,
  or wiring credentials into a containerised app.
category: devops
tags: [gcp, cloud, iam, devops, security, infrastructure]
keywords: [GCP, Google Cloud, gcloud, IAM, Service Account, Workload Identity, ADC, Application Default Credentials, Secret Manager, Project, Folder, Organization]
related: [gke-deployment, cloud-build-artifact-registry, gcp-cloud-sql-spring, gcp-pubsub-spring, gcp-observability-spring, gcp-firestore-spring, gcp-vertex-ai-rag]
---

# GCP Fundamentals

> Get the resource hierarchy, identity, and credentials right; everything else on GCP is just APIs you'll learn as you go.

## When to Use This Skill

- Starting a new project on GCP
- Granting an application or developer access to GCP resources
- Wiring credentials into a container running on GKE / Cloud Run / locally
- Auditing IAM bindings before going to production
- Migrating away from long-lived service-account keys

---

## Resource Hierarchy

```
Organization        ← acme.com (one per company)
└── Folder           ← e.g. "Production", "Engineering"
    └── Project      ← billing + IAM + API enablement boundary
        └── Resources (GKE clusters, Cloud SQL, GCS buckets, ...)
```

1. **The Project is the unit of isolation.** Billing, quota, IAM, and API enablement all attach here. Use **separate projects per environment** (`acme-orders-dev`, `acme-orders-stg`, `acme-orders-prod`).

2. **Folders group projects** for shared IAM (`Production` folder grants all prod projects to the SRE group). Don't over-engineer the tree — two levels (env-folder → project) handles most teams.

3. **Project IDs are global and immutable.** Pick `<company>-<service>-<env>` and live with it.

---

## gcloud CLI Setup

```bash
# Install
brew install --cask google-cloud-sdk            # macOS
# or: curl https://sdk.cloud.google.com | bash

# Authenticate as yourself
gcloud auth login
gcloud auth application-default login           # writes ADC to ~/.config/gcloud/

# Pick a project
gcloud config set project acme-orders-dev
gcloud config list
```

4. **Two auth flows, two credential stores.**
   - `gcloud auth login` — auths the CLI (used by `gcloud` commands).
   - `gcloud auth application-default login` — writes **ADC** that SDKs / Spring apps pick up.
   They are independent. Forgetting the second one is the #1 reason "it works in `gcloud` but my app says `unauthenticated`".

5. **Configurations for env switching:**
   ```bash
   gcloud config configurations create dev
   gcloud config set project acme-orders-dev
   gcloud config configurations activate prod
   ```

---

## IAM Model

Three pieces:

```
Member (who)        →   Role (what)        →   Resource (where)
user:alice@acme.com     roles/storage.admin    on bucket "raw-data"
serviceAccount:foo@…    roles/pubsub.publisher on project acme-orders-prod
group:devs@acme.com     roles/viewer           on folder "Production"
```

6. **Members can be:** users, groups, service accounts, or `allUsers` / `allAuthenticatedUsers`. Prefer **groups** for humans — never bind individuals directly.

7. **Roles come in three flavours:**
   - **Predefined** (`roles/pubsub.publisher`) — start here.
   - **Custom** — build only when no predefined role fits. Maintenance cost is real.
   - **Basic** (`roles/owner`, `roles/editor`, `roles/viewer`) — **avoid in production.** They span every API and grant far too much.

8. **Bind at the lowest level.** Resource > project > folder > org. Don't grant `roles/storage.admin` at the project level if a single bucket needs it.

9. **Least privilege is enforced by `gcloud` quirks too.** Use `gcloud projects get-iam-policy <project>` to audit. See [`rules/gcp-iam-checklist.md`](../../rules/gcp-iam-checklist.md).

---

## Service Accounts

A service account (SA) is a non-human identity owned by a project. Apps use SAs to call GCP APIs.

```bash
gcloud iam service-accounts create orders-app \
    --display-name "Orders application"

# Grant the SA permissions
gcloud projects add-iam-policy-binding acme-orders-prod \
    --member "serviceAccount:orders-app@acme-orders-prod.iam.gserviceaccount.com" \
    --role   "roles/cloudsql.client"
```

10. **One SA per workload.** `orders-app`, `orders-migrations`, `orders-pubsub-worker` — separate SAs make audits and revocation simple. Don't reuse a single "app SA" everywhere.

11. **Never download SA keys (`*.json`) for use on GCP-hosted workloads.** Use Workload Identity (below). Keys are long-lived, easy to leak, and a top finding in security reviews.

12. **Local dev uses your user identity via ADC**, not an SA key. `gcloud auth application-default login` is enough for the SDK to authenticate as you.

---

## Workload Identity (the right way to give pods credentials)

For GKE, **Workload Identity Federation** maps a Kubernetes Service Account (KSA) to a Google Service Account (GSA). Pods running under the KSA get short-lived tokens for the GSA — no JSON keys anywhere.

```bash
# 1. Enable on the cluster (Autopilot has it on by default)
gcloud container clusters update prod-cluster \
    --workload-pool=acme-orders-prod.svc.id.goog

# 2. Create the GSA and KSA
gcloud iam service-accounts create orders-app
kubectl create serviceaccount orders-app -n orders

# 3. Bind: KSA → GSA
gcloud iam service-accounts add-iam-policy-binding \
    orders-app@acme-orders-prod.iam.gserviceaccount.com \
    --member "serviceAccount:acme-orders-prod.svc.id.goog[orders/orders-app]" \
    --role   "roles/iam.workloadIdentityUser"

# 4. Annotate the KSA
kubectl annotate serviceaccount orders-app -n orders \
    iam.gke.io/gcp-service-account=orders-app@acme-orders-prod.iam.gserviceaccount.com
```

Then in your `Deployment`:

```yaml
spec:
  template:
    spec:
      serviceAccountName: orders-app
```

13. **No Java code change needed.** The Google SDK picks up ADC; on GKE that means the metadata server, which Workload Identity intercepts.

14. **For Cloud Run / Cloud Functions / Cloud Build,** assign the GSA directly with `--service-account=...`. Same SDK, same ADC — different injection mechanism.

15. **For GitHub Actions**, use **Workload Identity Federation** (`google-github-actions/auth@v2` with `workload_identity_provider`). Stop checking SA keys into GitHub Secrets.

---

## Application Default Credentials (ADC)

The Google SDK looks for credentials in this order:

1. `GOOGLE_APPLICATION_CREDENTIALS` env var → path to a key file
2. `~/.config/gcloud/application_default_credentials.json` (set by `gcloud auth application-default login`)
3. The **metadata server** on GCP (Compute Engine, GKE with Workload Identity, Cloud Run, Cloud Build)

Spring code looks like:

```java
@Bean
public Storage storage() {
    return StorageOptions.getDefaultInstance().getService();
}
```

That's it. The SDK figures out where it's running.

16. **Set `GOOGLE_APPLICATION_CREDENTIALS` only as a last resort** — usually for local dev with a downloaded key, and only when ADC won't work (e.g. some integration test scenarios).

17. **Project ID is also resolved from ADC**, but you can override:
    ```yaml
    spring:
      cloud:
        gcp:
          project-id: acme-orders-prod
    ```

---

## Secret Manager

Don't commit secrets. Don't put them in `application-prod.yml`. Don't bake them into images.

```bash
gcloud secrets create db-password --replication-policy=automatic
echo -n "supersecret" | gcloud secrets versions add db-password --data-file=-

gcloud secrets add-iam-policy-binding db-password \
    --member "serviceAccount:orders-app@acme-orders-prod.iam.gserviceaccount.com" \
    --role   "roles/secretmanager.secretAccessor"
```

### Spring integration

With `spring-cloud-gcp-starter-secretmanager`:

```yaml
spring:
  config:
    import: "sm@:"            # enable Secret Manager imports
  datasource:
    password: ${sm@db-password}
```

18. **Never grant `roles/secretmanager.admin` to apps.** They only need `secretAccessor`.

19. **Rotate via new versions.** `versions add` creates a new version; the app reads `latest` (or pin a specific version). Old versions get disabled, then destroyed after a retention period.

20. **For env vars in K8s**, use the **Secret Manager CSI driver** or pull at startup. Don't copy secrets into Kubernetes `Secret` objects unnecessarily — that's a separate audit boundary.

---

## Enabling APIs

Every GCP API is off by default in a new project. Common ones for a Java backend:

```bash
gcloud services enable \
    container.googleapis.com \         # GKE
    artifactregistry.googleapis.com \   # container images
    cloudbuild.googleapis.com \         # CI builds
    sqladmin.googleapis.com \           # Cloud SQL
    pubsub.googleapis.com \             # Pub/Sub
    secretmanager.googleapis.com \      # Secret Manager
    monitoring.googleapis.com \         # metrics
    logging.googleapis.com \            # logs
    cloudtrace.googleapis.com           # traces
```

21. **First call to a new API often fails with `Permission denied`** even when IAM is correct — the API was just enabled and the propagation takes ~minutes.

---

## Cost Hygiene

22. **Set a billing budget alert per project.** `gcloud billing budgets create` or via the console. Cap spend before you discover a forgotten n2-standard-32.

23. **Label everything.** `--labels=env=prod,team=orders,cost-center=eng-platform`. Labels become billing-export columns; without them you can't slice spend.

24. **Delete unused projects.** A project with no resources still has a billing record but costs $0 — but a project with a forgotten Cloud SQL instance costs ~$50/month forever.

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `gcloud` works, app says "unauthenticated" | Run `gcloud auth application-default login` (separate from `gcloud auth login`) |
| Granted `roles/owner` to a service account "to make it work" | Replace with the specific predefined role; revoke owner |
| SA key checked into git | Rotate immediately, switch to Workload Identity, run secret scanning on history |
| API call fails with `SERVICE_DISABLED` | Enable the API in the project (`gcloud services enable ...`) |
| Cross-project access fails silently | Bind the calling SA in *both* projects, or grant on the resource directly |
| Cloud Run app gets the wrong project ID | Set the `GOOGLE_CLOUD_PROJECT` env var or `spring.cloud.gcp.project-id` |

---

## Pre-Production Checklist

- [ ] Separate projects per environment
- [ ] No `roles/owner`, `roles/editor` on service accounts
- [ ] One service account per workload, named for what it does
- [ ] Workload Identity enabled on every cluster; no SA keys in pods
- [ ] CI/CD uses Workload Identity Federation, not SA key in CI secret
- [ ] Secrets in Secret Manager; no secrets in YAML or images
- [ ] Required APIs enabled and recorded in IaC
- [ ] Billing budget + alerts configured
- [ ] Resources labelled (`env`, `team`, `cost-center`)

---

## Related Skills

- [`gke-deployment`](../gke-deployment/SKILL.md) — wire Workload Identity into a Deployment
- [`cloud-build-artifact-registry`](../cloud-build-artifact-registry/SKILL.md) — CI auth + image push
- [`gcp-cloud-sql-spring`](../../engineering/gcp-cloud-sql-spring/SKILL.md) — Cloud SQL access from Boot
- [`gcp-pubsub-spring`](../../engineering/gcp-pubsub-spring/SKILL.md) — Pub/Sub auth from Boot
- [`terraform-basics`](../terraform-basics/SKILL.md) — provision projects, SAs, IAM bindings as code
- [`rules/gcp-iam-checklist.md`](../../rules/gcp-iam-checklist.md) — IAM review checklist
