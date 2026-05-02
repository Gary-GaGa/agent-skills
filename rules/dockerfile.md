# Dockerfile Rules

Rules for writing production-quality Dockerfiles. Aligned with the [`docker-basics`](../docker-basics/SKILL.md) skill.

---

## Base Image

1. **Pin base image versions.** `golang:1.23-alpine`, not `golang:latest`.

2. **Use minimal bases.** Alpine (~5 MB), distroless (~2 MB), or `scratch` for static binaries.
   - ❌ `FROM ubuntu:latest` (75 MB, unnecessary for most apps)
   - ✅ `FROM alpine:3.20` or `FROM gcr.io/distroless/static`

3. **Multi-stage builds.** Build in SDK image; copy only the artifact to minimal runtime image.

---

## Layer Ordering

4. **Order by change frequency: stable first, volatile last.**
   ```dockerfile
   COPY go.mod go.sum ./      # changes rarely
   RUN go mod download        # cached unless go.mod changes
   COPY . .                   # changes every build
   RUN go build ...           # rebuilds only if source changes
   ```

5. **Combine related `RUN` commands with `&&`.** Fewer layers = smaller image.
   ```dockerfile
   RUN apk --no-cache add ca-certificates tzdata && \
       adduser -D -u 1000 appuser
   ```

6. **Clean up in the same layer as install.** Package manager caches must be removed in the same `RUN`.
   - ✅ `RUN apt-get update && apt-get install -y X && rm -rf /var/lib/apt/lists/*`
   - ❌ Separate `RUN rm -rf /var/lib/apt/lists/*` (cache is already in a previous layer)

---

## Security

7. **Run as non-root.**
   ```dockerfile
   RUN adduser -D -u 1000 appuser
   USER appuser
   ```

8. **Don't store secrets in the image.** No `ENV SECRET=xxx` or `ARG SECRET=xxx` (visible in image history).
   - Build-time secrets: `--mount=type=secret`
   - Runtime secrets: environment variables or mounted files

9. **Use `COPY`, not `ADD`.** `ADD` auto-extracts archives and fetches URLs — unexpected behavior.

10. **Scan images for CVEs.** `docker scout cves`, Trivy, or Snyk in CI.

---

## Build

11. **Always have `.dockerignore`.** Exclude `.git`, `node_modules`, tests, docs, `.env`.

12. **Use `ENTRYPOINT` for the main process.** `CMD` for default arguments that can be overridden.
    ```dockerfile
    ENTRYPOINT ["server"]
    CMD ["--port", "8080"]
    ```

13. **Static binaries for Go:** `CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w"`.
    - `-s -w` strips debug info for smaller binary
    - `CGO_ENABLED=0` removes libc dependency

14. **Set `EXPOSE` for documentation.** Doesn't publish the port; just documents which ports the container listens on.

---

## Go-Specific Template

```dockerfile
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

FROM alpine:3.20
RUN apk --no-cache add ca-certificates tzdata && \
    adduser -D -u 1000 appuser
USER appuser
COPY --from=builder /app/server /usr/local/bin/server
EXPOSE 8080
ENTRYPOINT ["server"]
```

---

## Compose (Local Dev)

15. **Use `depends_on` with `condition: service_healthy`.** Not just startup order.

16. **Named volumes for persistent data.** `volumes: pgdata:`.

17. **Health checks on dependencies.**
    ```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 3s
      retries: 5
    ```

18. **Don't use compose in production.** Use Kubernetes, ECS, or similar.

---

## Image Size

19. **Target sizes:**
    - Go static binary: < 20 MB
    - Go + Alpine: < 30 MB
    - Node.js: < 200 MB
    - Python: < 300 MB

20. **Use `docker images` to check.** If your Go image is > 100 MB, something is wrong (probably not multi-stage).

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `FROM ubuntu` for Go binary | Alpine or scratch |
| No `.dockerignore` | Add one; exclude `.git`, tests, docs |
| `latest` tag | Pin version |
| Root user | `USER appuser` |
| Secrets in `ENV` / `ARG` | Mounted secrets or `--mount=type=secret` |
| `ADD` instead of `COPY` | Use `COPY` unless you need archive extraction |
| `COPY . .` as first instruction | Copy deps first for caching |
| No multi-stage build | Separate build and runtime stages |
