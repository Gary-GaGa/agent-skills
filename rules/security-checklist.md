# Security Checklist

Condensed security rules for code review, based on OWASP Top 10. Check every item before merging code that handles user input, authentication, or external data.

---

## Input Validation

1. **Validate all user input at the boundary.** Type, length, format, range. Reject invalid input; don't try to sanitize.

2. **Never trust client-side validation.** Always re-validate server-side.

3. **Use allowlists over denylists.** Define what's valid; reject everything else.

---

## Injection

4. **SQL: use parameterized queries or ORM/query builder. Never concatenate.**
   - ✅ `db.Query("SELECT * FROM users WHERE id = $1", id)`
   - ❌ `db.Query("SELECT * FROM users WHERE id = " + id)`

5. **Command injection: avoid `exec` with user input. If unavoidable, use allowlist of commands and escape arguments.**

6. **XSS: escape all user-generated content in HTML output.** Use framework auto-escaping. Never inject raw HTML from user input.

7. **Path traversal: validate file paths. Reject `..`, absolute paths, and null bytes.**

---

## Authentication

8. **Hash passwords with bcrypt, scrypt, or argon2.** Never SHA-256 or MD5. Never store plaintext.

9. **Use constant-time comparison for secrets.** `crypto/subtle.ConstantTimeCompare` (Go). Prevents timing attacks.

10. **Session tokens: cryptographically random, >= 128 bits.** Use `crypto/rand`, not `math/rand`.

11. **JWT: validate signature, issuer, audience, and expiration on every request.** Don't just decode.

12. **Multi-factor authentication for admin / sensitive operations.**

---

## Authorization

13. **Check permissions on every request.** Don't rely on UI hiding buttons.

14. **Default deny.** If no rule explicitly grants access, deny.

15. **Check object ownership.** User A should not access User B's data. `WHERE user_id = current_user.id`.

16. **Principle of least privilege.** Grant minimum required permissions. Service accounts too.

---

## Secrets Management

17. **Never hardcode secrets in source code.** Use environment variables, vault, or secret manager.

18. **Never commit secrets to git.** Use `.gitignore` for `.env` files. Use `git-secrets` or `trufflehog` to scan.

19. **Rotate secrets on a schedule.** At minimum: when anyone with access leaves.

20. **Don't log secrets.** Redact API keys, tokens, passwords from all log output.

21. **Different secrets per environment.** Dev, staging, prod have separate credentials.

---

## HTTPS & Transport

22. **HTTPS everywhere.** No exceptions for "internal" services in production.

23. **HSTS header.** `Strict-Transport-Security: max-age=31536000; includeSubDomains`.

24. **TLS 1.2 minimum.** Disable TLS 1.0, 1.1, and all SSL versions.

---

## Headers & CORS

25. **Set security headers:**
    ```
    Content-Security-Policy: default-src 'self'
    X-Content-Type-Options: nosniff
    X-Frame-Options: DENY
    Referrer-Policy: strict-origin-when-cross-origin
    ```

26. **CORS: allowlist specific origins.** Never `Access-Control-Allow-Origin: *` for authenticated endpoints.

---

## Dependencies

27. **Audit dependencies regularly.** `npm audit`, `go vuln check`, `pip audit`.

28. **Pin dependency versions.** Use lockfiles (`go.sum`, `package-lock.json`).

29. **Remove unused dependencies.** Every dependency is attack surface.

---

## Error Handling

30. **Don't expose stack traces or internal errors to users.** Generic message to client; full details to logs.

31. **Don't reveal system information in errors.** No database engine versions, file paths, or internal IPs.

---

## Rate Limiting

32. **Rate-limit all public endpoints.** Per IP and per user/API key.

33. **Rate-limit login attempts.** Max 5-10 per minute per account. Lock after N failures.

34. **Return `429 Too Many Requests` with `Retry-After` header.**

---

## Data Protection

35. **Encrypt sensitive data at rest.** Database encryption, disk encryption.

36. **Minimize data collection.** Don't store data you don't need.

37. **Implement data retention policies.** Auto-delete old data per policy.

38. **PII access logging.** Know who accessed what personal data and when.

---

## Code Review Security Questions

Before approving a PR, ask:

- [ ] Does this handle user input? → Rules 1-7
- [ ] Does this touch auth? → Rules 8-16
- [ ] Does this use secrets? → Rules 17-21
- [ ] Does this expose an API? → Rules 22-26, 32-34
- [ ] Does this add a dependency? → Rules 27-29
- [ ] Does this return errors to users? → Rules 30-31
- [ ] Does this store or process PII? → Rules 35-38
