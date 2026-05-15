---
name: cloud-build-artifact-registry
description: >
  CI on Google Cloud — Cloud Build, Artifact Registry, vulnerability
  scanning, and Cloud Deploy for progressive rollouts. Covers Workload
  Identity Federation from external CI. Use this skill when wiring image
  builds and deploys to a GKE service on GCP, or auditing an existing
  GCP-side pipeline.
category: devops
tags: [gcp, ci-cd, devops, container, automation, cloud, deployment]
keywords: [Cloud Build, Artifact Registry, cloudbuild.yaml, Cloud Deploy, Skaffold, Workload Identity Federation, GitHub Actions, vulnerability scanning, image signing]
related: [gcp-fundamentals, gke-deployment, docker-basics, github-actions]
---

# Cloud Build & Artifact Registry

> The only image registry on GCP you should be using is Artifact Registry. The only build that authenticates without long-lived keys is one using Workload Identity Federation.

## When to Use This Skill

- Setting up CI for a Java/Spring Boot service that deploys to GKE
- Migrating from Container Registry (`gcr.io`) to Artifact Registry
- Wiring GitHub Actions to GCP without storing service account keys
- Adding image vulnerability scanning before deploy
- Setting up Cloud Deploy for canary / staged rollouts

---

## Artifact Registry

Artifact Registry replaces the legacy Container Registry (`gcr.io`). It stores Docker, Maven, npm, and other artifact formats.

```bash
# One-time: create a Docker repository
gcloud artifacts repositories create apps \
    --repository-format=docker \
    --location=asia-east1 \
    --description="Application container images"

# Authenticate the local Docker daemon
gcloud auth configure-docker asia-east1-docker.pkg.dev

# Push
docker tag orders:1.42.0 asia-east1-docker.pkg.dev/acme-orders-prod/apps/orders:1.42.0
docker push       asia-east1-docker.pkg.dev/acme-orders-prod/apps/orders:1.42.0
```

1. **Use a regional repository in the same region as your cluster.** `asia-east1` cluster pulls from `asia-east1` repo — sub-second pulls vs cross-region.

2. **One repository per artifact format.** `apps` for Docker, `maven-internal` for JARs, `npm-internal` for JS. Don't mix.

3. **Stop using `gcr.io`.** Container Registry is deprecated. Artifact Registry has finer IAM, vulnerability scanning, and remote/virtual repositories.

### IAM

```bash
gcloud artifacts repositories add-iam-policy-binding apps \
    --location=asia-east1 \
    --member "serviceAccount:cloud-build@acme-orders-prod.iam.gserviceaccount.com" \
    --role   "roles/artifactregistry.writer"

gcloud artifacts repositories add-iam-policy-binding apps \
    --location=asia-east1 \
    --member "serviceAccount:orders-app@acme-orders-prod.iam.gserviceaccount.com" \
    --role   "roles/artifactregistry.reader"
```

4. **`writer` for builders, `reader` for consumers** (GKE node SAs, dev tooling). Don't grant `admin` outside admin scripts.

5. **GKE pulls images automatically when node SAs have `artifactregistry.reader`.** No `imagePullSecrets` needed.

### Maven / npm Repositories

```xml
<!-- pom.xml -->
<distributionManagement>
  <repository>
    <id>artifact-registry</id>
    <url>artifactregistry://asia-east1-maven.pkg.dev/acme-orders-prod/maven-internal</url>
  </repository>
</distributionManagement>
```

6. **Internal libraries belong here.** Don't publish to public Maven Central; consumers authenticate via ADC.

---

## Cloud Build

Cloud Build runs builds in ephemeral containers on GCP. Define a pipeline as `cloudbuild.yaml`.

### Minimal Java + Docker pipeline

```yaml
# cloudbuild.yaml
steps:
  - id: test
    name: gcr.io/cloud-builders/gradle
    entrypoint: bash
    args: ["-c", "./gradlew --no-daemon test"]

  - id: build-jar
    name: gcr.io/cloud-builders/gradle
    entrypoint: bash
    args: ["-c", "./gradlew --no-daemon bootJar"]

  - id: build-image
    name: gcr.io/cloud-builders/docker
    args:
      - build
      - --tag=asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$SHORT_SHA
      - --tag=asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$BRANCH_NAME
      - --cache-from=asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$BRANCH_NAME
      - .

  - id: push
    name: gcr.io/cloud-builders/docker
    args: [push, --all-tags, asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders]

images:
  - asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$SHORT_SHA

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: E2_HIGHCPU_8
```

7. **Tag every image with `$SHORT_SHA`.** Mutable tags (`:latest`, `:main`) are pointers; immutable ones are what your `Deployment` should reference.

8. **`--cache-from` previous builds.** Without it, layered Dockerfiles re-fetch every dependency. Use a `:cache` tag pointing at the most recent build of the same branch.

9. **`logging: CLOUD_LOGGING_ONLY`** is required for builds run by user-managed service accounts (the new default).

### Triggers

```bash
gcloud builds triggers create github \
    --repo-name=orders \
    --repo-owner=acme \
    --branch-pattern="^main$" \
    --build-config=cloudbuild.yaml \
    --service-account=projects/acme-orders-prod/serviceAccounts/cloud-build@acme-orders-prod.iam.gserviceaccount.com
```

10. **One trigger per branch pattern.** PR triggers, main triggers, and tag triggers all separate.

11. **User-managed Cloud Build SA** — don't use the legacy default. Bind only the roles you need (`roles/artifactregistry.writer`, `roles/clouddeploy.releaser`, `roles/logging.logWriter`).

---

## GitHub Actions → GCP via Workload Identity Federation

Skip the SA key. Use OIDC.

### One-time GCP setup

```bash
# Create a workload identity pool
gcloud iam workload-identity-pools create github-pool \
    --location=global

# Provider for github.com OIDC
gcloud iam workload-identity-pools providers create-oidc github-provider \
    --location=global \
    --workload-identity-pool=github-pool \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository_owner == 'acme'"

# Bind the GSA so GitHub jobs from acme/orders main branch can impersonate
gcloud iam service-accounts add-iam-policy-binding \
    cloud-build@acme-orders-prod.iam.gserviceaccount.com \
    --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/attribute.repository/acme/orders" \
    --role="roles/iam.workloadIdentityUser"
```

### `.github/workflows/deploy.yml`

```yaml
name: deploy
on:
  push: { branches: [main] }

permissions:
  contents: read
  id-token: write   # required for OIDC

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-pool/providers/github-provider
          service_account: cloud-build@acme-orders-prod.iam.gserviceaccount.com

      - uses: google-github-actions/setup-gcloud@v2

      - name: Submit build
        run: gcloud builds submit --config=cloudbuild.yaml --substitutions=SHORT_SHA=$GITHUB_SHA
```

12. **`id-token: write`** must be set on the job. Without it, `auth@v2` can't fetch an OIDC token.

13. **Constrain the principal set.** The example above limits to `acme/orders`; you can also restrict to `attribute.ref` for branch-level rules.

14. **No `GCP_SA_KEY` secret in GitHub.** Anyone who finds an SA key has it forever.

---

## Vulnerability Scanning

Artifact Registry scans pushed images automatically (when `containerscanning.googleapis.com` is enabled). Findings appear in `gcloud artifacts vulnerabilities list`.

### Block deploys with `Binary Authorization` or a build step

```yaml
- id: scan-gate
  name: gcr.io/cloud-builders/gcloud
  entrypoint: bash
  args:
    - -c
    - |
      set -e
      IMAGE=asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$SHORT_SHA
      CRITICAL=$(gcloud artifacts docker images describe $IMAGE \
        --show-package-vulnerability \
        --format='value(package_vulnerability_summary.vulnerabilities.CRITICAL)')
      if [ "${CRITICAL:-0}" -gt 0 ]; then
        echo "Critical vulnerabilities found: $CRITICAL"
        exit 1
      fi
```

15. **Fail the build on `CRITICAL` only at first**, not `HIGH`. Otherwise base-image churn makes builds red half the time. Tighten over time.

16. **Use distroless or minimal base images** to reduce the surface (see [`docker-basics`](../docker-basics/SKILL.md)).

17. **Binary Authorization** enforces signed images at GKE admission. Adds an attestation step to the pipeline; pays off for regulated environments.

---

## Cloud Deploy (Optional, for Progressive Rollouts)

When you outgrow `kubectl set image`:

```yaml
# clouddeploy.yaml
apiVersion: deploy.cloud.google.com/v1
kind: DeliveryPipeline
metadata: { name: orders }
description: Orders rollout
serialPipeline:
  stages:
    - targetId: staging
    - targetId: prod
      strategy:
        canary:
          runtimeConfig: { kubernetes: { serviceNetworking: { service: orders, deployment: orders } } }
          canaryDeployment:
            percentages: [25, 50]
            verify: true
---
apiVersion: deploy.cloud.google.com/v1
kind: Target
metadata: { name: prod }
gke: { cluster: projects/acme-orders-prod/locations/asia-east1/clusters/prod-cluster }
```

```bash
# Trigger a release from a Cloud Build step
gcloud deploy releases create rel-$SHORT_SHA \
    --delivery-pipeline=orders \
    --region=asia-east1 \
    --skaffold-file=skaffold.yaml \
    --images=orders=asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$SHORT_SHA
```

18. **Cloud Deploy doesn't replace `kubectl`/manifests.** It orchestrates Skaffold-rendered manifests across stages. Skaffold renders, Cloud Deploy promotes.

19. **Start with a two-stage pipeline** (`staging → prod`). Add canary only when you have metrics-based verification ready (Cloud Monitoring + `verify` step).

---

## Build Performance

20. **Use `E2_HIGHCPU_8` or `N1_HIGHCPU_8`** for Java builds. Default machine is single-CPU and slow for Gradle.

21. **Cache dependencies in Cloud Storage:**
    ```yaml
    - name: gcr.io/cloud-builders/gsutil
      args: [rsync, -r, gs://cb-cache/$REPO_NAME/gradle, /home/builder/.gradle]
    # ... build ...
    - name: gcr.io/cloud-builders/gsutil
      args: [rsync, -r, /home/builder/.gradle, gs://cb-cache/$REPO_NAME/gradle]
    ```

22. **Or use Jib for Java images** — skips the Docker daemon entirely, layers efficiently, no Dockerfile:
    ```bash
    ./gradlew jib --image=asia-east1-docker.pkg.dev/$PROJECT_ID/apps/orders:$TAG
    ```

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `denied: ... requires authentication` pushing to AR | `gcloud auth configure-docker <region>-docker.pkg.dev` |
| Builds work locally, fail on Cloud Build | Cloud Build SA missing the role; check `roles/artifactregistry.writer`, `roles/logging.logWriter` |
| Images push but pods can't pull | Node SA missing `roles/artifactregistry.reader` on the repo (or wrong project) |
| Workload Identity Federation auth says "audience mismatch" | `attribute-mapping` doesn't match the `attribute-condition`; `principalSet` URI is exact-match |
| Image has `:latest` deployed but rollback shows the same SHA | Stop tagging `:latest` for production; pin by `:$SHORT_SHA` or digest |
| Cloud Build OOM on Java tests | Bump `machineType`; the default 1-CPU machine is too small |

---

## Pre-Production Checklist

- [ ] Regional Artifact Registry repository in the same region as the cluster
- [ ] No `gcr.io` references anywhere
- [ ] User-managed Cloud Build SA with least-privilege roles
- [ ] GitHub Actions auth via Workload Identity Federation; no SA keys in secrets
- [ ] Every image tagged with the immutable commit SHA
- [ ] Vulnerability scanning enabled; build fails on `CRITICAL`
- [ ] GKE node SAs have `artifactregistry.reader`
- [ ] Build cache strategy (`--cache-from` or Jib)
- [ ] (Optional) Cloud Deploy or Argo CD for prod promotion, not raw `kubectl`

---

## Related Skills

- [`gcp-fundamentals`](../gcp-fundamentals/SKILL.md) — IAM, SAs, Workload Identity
- [`gke-deployment`](../gke-deployment/SKILL.md) — what consumes these images
- [`docker-basics`](../docker-basics/SKILL.md) — image construction
- [`github-actions`](../github-actions/SKILL.md) — CI patterns; this skill is the GCP-side complement
