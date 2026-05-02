# API Versioning Rules

Rules for versioning HTTP and gRPC APIs. Aligned with [`api-design-rest`](../api-design-rest/SKILL.md) and [`api-design-grpc`](../api-design-grpc/SKILL.md).

---

## When to Version

1. **Version only on breaking changes.** Additive changes (new fields, new endpoints) don't need a new version.

2. **Breaking changes = anything that can break an existing client.**
   - Removing a field or endpoint
   - Changing a field's type
   - Changing response structure
   - Changing error codes
   - Changing auth requirements

3. **Non-breaking changes (no new version needed):**
   - Adding a new field to a response
   - Adding a new endpoint
   - Adding a new optional parameter
   - Adding a new enum value (be careful — some clients switch on enums)

---

## Versioning Strategy

4. **REST: URL prefix (`/v1/`, `/v2/`) by default.** Explicit, discoverable, easy to route.

5. **gRPC: package path (`myapp.v1`, `myapp.v2`).** Version in the proto package, not the service name.

6. **Don't use header-based versioning unless you have a strong reason.** Headers are invisible; URL versions are in every log line.

7. **Don't use query parameter versioning** (`?version=2`). Breaks caching, hard to route.

---

## Backward Compatibility

8. **Support N-1 at minimum.** When you launch v2, keep v1 running.

9. **Deprecation notice ≥ 6 months before removal** for public APIs. Internal APIs can be shorter but still require notice.

10. **Deprecation response header.** Add `Deprecation: true` and `Sunset: <date>` headers to v1 responses.

11. **Log v1 usage to track migration.** Don't remove until traffic is near zero.

---

## Migration Path

12. **Provide a migration guide.** Document every breaking change: what was, what is now, what to change.

13. **Dual-write period (if data changes).** Both v1 and v2 write to the same storage during transition.

14. **Don't maintain more than 2 versions concurrently.** v1 + v2 is manageable; v1 + v2 + v3 is a maintenance nightmare.

---

## Semantic Versioning for APIs

15. **MAJOR version = breaking changes** (v1 → v2 in URL). Bump when existing clients would break.

16. **MINOR version = additive changes.** New endpoints, new optional fields. No URL change.

17. **PATCH version = bug fixes.** No interface change. Invisible to clients.

18. **Only MAJOR version appears in the URL.** `/v1/` covers all v1.x.y.

---

## gRPC-Specific

19. **Never change field numbers in proto.** It's a silent breaking change.

20. **Use `reserved` for removed fields.** Prevents accidental reuse.

21. **Run `buf breaking` in CI.** Catches breaking changes against the previous version automatically.

22. **Enums: first value is always `UNSPECIFIED = 0`.** Required for proto3 default behavior.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| New version for every release | Version only on breaking changes |
| No deprecation notice | 6+ months notice with `Sunset` header |
| Removing v1 while clients still use it | Monitor traffic; remove only when near zero |
| `?version=2` query param | URL prefix `/v2/` |
| v1, v2, v3, v4 all active | Support N-1 max |
| Breaking change without migration guide | Document every difference |
| Proto field number reuse | `reserved` keyword |
