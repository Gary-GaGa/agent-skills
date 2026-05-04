---
name: auth-patterns
description: >
  Authentication and authorization patterns for web applications — JWT, session,
  OAuth2/OIDC, social login (Google, LINE), role-based access control (RBAC),
  password hashing, and token refresh. Use this skill when implementing login,
  protecting API endpoints, or integrating third-party auth providers.
category: engineering
tags: [auth, jwt, oauth, security, rbac, session]
related: [api-design-rest, mongodb-go, nextjs-fundamentals, line-integration-tw, tw-payment-integration]
---

# Authentication & Authorization Patterns

> Authentication = "who are you?" Authorization = "what can you do?" They're different systems with different failure modes. Don't conflate them.

## When to Use This Skill

- Implementing user registration and login
- Choosing between JWT and sessions
- Integrating social login (Google, LINE, GitHub)
- Designing role-based or resource-based authorization
- Securing API endpoints
- Implementing token refresh and logout

---

## Auth Flow Overview

```
┌──────────┐    credentials    ┌──────────┐    token/session    ┌──────────┐
│  Client  │ ────────────────► │ Auth API │ ──────────────────► │  Client  │
│ (browser)│                   │ (verify) │                     │ (stores) │
└──────────┘                   └──────────┘                     └────┬─────┘
                                                                     │
                                          token in header            │
┌──────────┐    verify token    ┌──────────┐◄────────────────────────┘
│   API    │◄───────────────── │Middleware │
│(protected)│                   │ (decode) │
└──────────┘                   └──────────┘
```

---

## JWT vs Session

| | JWT (stateless) | Session (stateful) |
|-|-----------------|-------------------|
| **Storage** | Token in client (cookie/localStorage) | Session ID in cookie; data on server |
| **Scalability** | No server state; any server can verify | Needs shared session store (Redis) |
| **Revocation** | Hard (needs blocklist or short expiry) | Easy (delete from store) |
| **Size** | Token grows with claims | Cookie is small (just ID) |
| **Best for** | API-to-API, microservices, mobile | Server-rendered apps, single backend |

### Recommendation for frontend-backend separation

1. **Use JWT with short-lived access token + refresh token.**
   - Access token: 15-30 min expiry, sent in `Authorization: Bearer` header
   - Refresh token: 7-30 days, stored in httpOnly cookie, used to get new access token

```go
type TokenPair struct {
    AccessToken  string `json:"access_token"`
    RefreshToken string `json:"-"` // sent as httpOnly cookie, not in body
    ExpiresIn    int    `json:"expires_in"`
}
```

---

## JWT Implementation (Go)

### Generate

```go
import "github.com/golang-jwt/jwt/v5"

type Claims struct {
    UserID string `json:"user_id"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

func GenerateAccessToken(userID, role, secret string) (string, error) {
    claims := Claims{
        UserID: userID,
        Role:   role,
        RegisteredClaims: jwt.RegisteredClaims{
            ExpiresAt: jwt.NewNumericDate(time.Now().Add(15 * time.Minute)),
            IssuedAt:  jwt.NewNumericDate(time.Now()),
            Issuer:    "booking-api",
        },
    }
    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString([]byte(secret))
}
```

### Verify (middleware)

```go
func AuthMiddleware(secret string) func(next http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            tokenStr := extractBearerToken(r)
            if tokenStr == "" {
                http.Error(w, "unauthorized", http.StatusUnauthorized)
                return
            }
            claims := &Claims{}
            token, err := jwt.ParseWithClaims(tokenStr, claims,
                func(t *jwt.Token) (any, error) {
                    return []byte(secret), nil
                })
            if err != nil || !token.Valid {
                http.Error(w, "unauthorized", http.StatusUnauthorized)
                return
            }
            ctx := context.WithValue(r.Context(), ctxUserKey, claims)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}
```

### Rules

2. **Use HS256 for single-service; RS256 for multi-service.** RS256 lets services verify without sharing the secret.
3. **Never store JWT secret in code.** Environment variable or secret manager.
4. **Validate all claims.** Expiry, issuer, audience. Don't just decode.
5. **Keep access tokens short-lived (15-30 min).** Limits damage from stolen tokens.

---

## OAuth2 / Social Login

### Flow (Authorization Code)

```
1. User clicks "Login with Google"
2. Redirect to Google's auth page
3. User authorizes; Google redirects back with `code`
4. Backend exchanges `code` for tokens (server-to-server)
5. Backend fetches user profile from Google
6. Backend creates/updates user in DB
7. Backend issues its own JWT to client
```

### Go implementation sketch

```go
// Step 4: exchange code for token
func handleOAuthCallback(w http.ResponseWriter, r *http.Request) {
    code := r.URL.Query().Get("code")
    token, err := oauthConfig.Exchange(ctx, code)
    // Step 5: get user info
    userInfo, err := getUserInfo(ctx, token)
    // Step 6: upsert user
    user, err := userService.FindOrCreateByProvider(ctx, "google", userInfo)
    // Step 7: issue our JWT
    accessToken, err := GenerateAccessToken(user.ID, user.Role, secret)
    // set refresh token cookie, redirect to frontend
}
```

6. **Exchange happens server-to-server.** The `code` is exchanged by your backend, not the frontend.
7. **Store provider + provider_user_id in your DB.** One user can have multiple auth providers.
8. **Issue YOUR tokens after OAuth.** Don't use Google/LINE's tokens for your API auth.

---

## Password Authentication

If you also support email/password login:

```go
import "golang.org/x/crypto/bcrypt"

func HashPassword(password string) (string, error) {
    hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    return string(hash), err
}

func CheckPassword(hash, password string) bool {
    return bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) == nil
}
```

9. **bcrypt, scrypt, or argon2. Never SHA-256 or MD5.**
10. **Rate-limit login attempts.** Max 5-10 per minute per account.
11. **Don't reveal whether email exists.** "Invalid email or password" for both cases.

---

## Refresh Token Flow

```
Client: access token expired (401)
Client: POST /auth/refresh (refresh_token in httpOnly cookie)
Server: verify refresh token → issue new access + refresh tokens
Server: invalidate old refresh token (rotation)
Client: retry original request with new access token
```

12. **Refresh token rotation.** Each refresh issues a new refresh token and invalidates the old one. Detects token theft.
13. **Store refresh tokens server-side.** In DB or Redis with user_id, expiry, and device info.
14. **Refresh token in httpOnly, Secure, SameSite=Strict cookie.** Not in localStorage (XSS vulnerable).

---

## Authorization (RBAC)

### Simple role-based

```go
type Role string
const (
    RoleUser  Role = "user"
    RoleAdmin Role = "admin"
)

func RequireRole(roles ...Role) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            claims := ClaimsFromContext(r.Context())
            for _, role := range roles {
                if Role(claims.Role) == role {
                    next.ServeHTTP(w, r)
                    return
                }
            }
            http.Error(w, "forbidden", http.StatusForbidden)
        })
    }
}

// Usage
mux.Handle("DELETE /groups/{id}", RequireRole(RoleAdmin)(deleteGroupHandler))
```

### Resource-based (ownership)

```go
func RequireGroupOwner(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        claims := ClaimsFromContext(r.Context())
        groupID := r.PathValue("id")
        group, _ := groupRepo.FindByID(ctx, groupID)
        if group.CreatedBy.Hex() != claims.UserID {
            http.Error(w, "forbidden", http.StatusForbidden)
            return
        }
        next.ServeHTTP(w, r)
    })
}
```

15. **Check permissions on every request.** Don't rely on frontend hiding buttons.
16. **Default deny.** No permission = no access.
17. **Check ownership for resource operations.** User A can't edit User B's group.

---

## Logout

18. **Access token: let it expire.** Short-lived tokens make logout less critical.
19. **Refresh token: delete from server-side store + clear cookie.**
20. **For immediate logout (rare): maintain a token blocklist.** Check on every request. Adds state but enables instant revocation.

---

## Security Rules

21. **HTTPS only.** Tokens in cleartext HTTP can be intercepted.
22. **CORS: whitelist specific origins.** Not `*` for authenticated endpoints.
23. **CSRF protection for cookie-based auth.** SameSite=Strict or CSRF tokens.
24. **Don't store tokens in localStorage.** XSS can read it. Use httpOnly cookies for refresh tokens.
25. **Log auth events.** Login success/failure, token refresh, logout. Essential for incident response.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| JWT with no expiry | 15-30 min access, 7-30 day refresh |
| Secret in source code | Environment variable |
| Storing JWT in localStorage | httpOnly cookie for refresh; memory for access |
| Same token for all purposes | Separate access + refresh tokens |
| No rate limiting on login | Max 5-10 attempts per minute |
| "Email not found" vs "Wrong password" | Same message for both |
| Frontend-only auth checks | Server validates on every request |
| No refresh token rotation | Rotate on each refresh |
| Using Google's token as your API token | Issue your own tokens after OAuth |

---

## Checklist

- [ ] Access token: short-lived (15-30 min), in Authorization header
- [ ] Refresh token: httpOnly cookie, server-side storage, rotation
- [ ] Password hashing: bcrypt/argon2 (not MD5/SHA)
- [ ] OAuth: code exchange server-to-server
- [ ] Login rate limiting: max 5-10/min per account
- [ ] RBAC middleware on protected routes
- [ ] Resource ownership checked (not just role)
- [ ] HTTPS enforced
- [ ] Auth events logged
- [ ] CORS configured with specific origins

---

## Related Skills

- [`api-design-rest`](../api-design-rest/SKILL.md) — 401/403 status codes, auth headers
- [`mongodb-go`](../mongodb-go/SKILL.md) — storing users, refresh tokens
- [`nextjs-fundamentals`](../nextjs-fundamentals/SKILL.md) — frontend auth integration (next-auth)
- [`line-integration-tw`](../line-integration-tw/SKILL.md) — LINE Login as OAuth provider
- [`rules/security-checklist`](../../rules/security-checklist.md) — broader security rules
