# GCP IAM Checklist

A short list of IAM rules to verify before going to production on GCP. Cross-references [`gcp-fundamentals`](../devops/gcp-fundamentals/SKILL.md) and [`gke-deployment`](../devops/gke-deployment/SKILL.md).

---

## Identities

1. **One service account per workload.** `orders-app`, `orders-migrations`, `orders-pubsub-worker` — separate identities make audit and revocation trivial.

2. **Humans bind through groups, not directly.**
   - ✅ `group:platform-admins@acme.com → roles/container.admin`
   - ❌ `user:alice@acme.com → roles/container.admin`

3. **No service account keys (`*.json`) in production.** Use Workload Identity (GKE) or direct SA assignment (Cloud Run / Cloud Functions / Cloud Build).

4. **CI/CD uses Workload Identity Federation**, not a checked-in SA key.

5. **Don't share an SA across services.** "Convenient" SAs (`apps@`, `general@`) become root-of-trust for everything you forget about.

---

## Roles

6. **No `roles/owner`, `roles/editor`, `roles/viewer` on service accounts.** They're project-wide, multi-API, and far too broad.

7. **Predefined roles before custom.** Custom roles work but are real maintenance.

8. **Bind at the lowest level.** Resource > project > folder > org. Don't grant `roles/storage.admin` at the project level if a single bucket needs it.

9. **App SAs get `client`/`reader`/`writer` scopes; never `admin`.**
   - ✅ `roles/cloudsql.client`, `roles/pubsub.publisher`, `roles/secretmanager.secretAccessor`
   - ❌ `roles/cloudsql.admin`, `roles/pubsub.admin`, `roles/secretmanager.admin`

10. **Migration / setup SAs separate from app SAs.** Migrations get DDL rights; the app does not.

---

## Workload Identity (GKE)

11. **Cluster has a workload pool** (`workload-pool=<project>.svc.id.goog`).

12. **KSA is annotated with the GSA email.**
    ```yaml
    annotations:
      iam.gke.io/gcp-service-account: orders-app@<project>.iam.gserviceaccount.com
    ```

13. **GSA grants `roles/iam.workloadIdentityUser` to the KSA principal.**
    ```bash
    gcloud iam service-accounts add-iam-policy-binding \
        orders-app@$PROJECT.iam.gserviceaccount.com \
        --member "serviceAccount:$PROJECT.svc.id.goog[$NAMESPACE/$KSA]" \
        --role   "roles/iam.workloadIdentityUser"
    ```

14. **Pods reference the KSA via `serviceAccountName`**, not the default.

15. **Spring code uses ADC.** No `GOOGLE_APPLICATION_CREDENTIALS` env var, no key file.

---

## Project Hygiene

16. **Separate projects per environment** (`acme-orders-dev`, `…-stg`, `…-prod`). Cross-environment IAM bindings are an explicit smell.

17. **APIs enabled deliberately**, captured in Terraform / `gcloud services enable` scripts. Surprise enablement is an audit nightmare.

18. **Billing budget + alert per project.** `gcloud billing budgets create` set to a sensible monthly cap.

19. **Resources labelled** with `env`, `team`, `cost-center`. Without labels, billing reports lie.

---

## Audit Practices

20. **Run `gcloud projects get-iam-policy <project>` regularly.** Diff against the IaC-declared bindings.

21. **Cloud Audit Logs are on for Admin Read, Data Write.** Required for incident forensics.

22. **No long-lived `roles/iam.serviceAccountTokenCreator`** outside CI tooling. It's effectively impersonation rights.

23. **Review external members.** Bindings on `user:*@gmail.com` or other domains are red flags unless explicitly intended.

24. **Document who can `actAs`/impersonate which SAs.** That's a privilege-escalation graph, not just a binding list.

---

## Secret Manager

25. **App SAs get `roles/secretmanager.secretAccessor`** on individual secrets, not the whole project.
    - ✅ `gcloud secrets add-iam-policy-binding db-password --member ... --role secretAccessor`
    - ❌ Project-level `roles/secretmanager.secretAccessor`

26. **No app SA gets `roles/secretmanager.admin`.** Only the bootstrap / rotation script.

27. **Secrets versioned**, never edited in place. Rotate by adding a new version; destroy after retention.

28. **Don't copy secrets into K8s `Secret` objects** when Secret Manager + the CSI driver is wired up — fewer audit boundaries.

---

## Quick Audit Block

```
- [ ] No SA keys in CI secrets, repo history, or pods
- [ ] Workload Identity enabled on every cluster
- [ ] One SA per workload; no shared "general" SAs
- [ ] No roles/owner / editor / admin on app SAs
- [ ] Bindings at resource scope where possible
- [ ] Separate projects per environment
- [ ] Labels on every resource
- [ ] Audit Logs on; periodic IAM diff against IaC
- [ ] Secret Manager scoped to per-secret accessor role
```

If any line above is "no", fix before shipping.

---

## Anti-Patterns

| Anti-pattern | Why it's wrong | Fix |
|---|---|---|
| `roles/owner` on the app SA "to make it work" | Grants every API in the project | Find the specific predefined role; revoke owner |
| One SA shared by every service | Compromise blast radius is the whole estate | One SA per workload |
| SA key checked into Git | Long-lived credential, hard to rotate | Workload Identity / Federation; rotate immediately |
| Granting `serviceAccountUser` org-wide | Lets anyone impersonate everything | Bind on the specific SA, with the specific consumer |
| Production secrets in `application-prod.yml` | Ships in the JAR | Secret Manager, env vars |
| K8s `Secret` mirrored from Secret Manager | Two stores to audit | Use the Secret Manager CSI driver |
| Cross-project IAM binding "for convenience" | Hides scope creep | Make it explicit IaC; or move resources into one project |
