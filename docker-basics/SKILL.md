---
name: docker-basics
description: >
  Docker best practices for developers — Dockerfile patterns, multi-stage builds,
  image optimization, docker-compose for local dev, security hardening, and
  .dockerignore. Use this skill when containerizing an application, optimizing
  image size, or setting up a local development environment.
category: devops
tags: [docker, container, dockerfile, compose, devops]
related: [github-actions, k8s-fundamentals, terraform-basics]
---

# Docker Basics

> Containers are not VMs. A good Dockerfile is a repeatable build script that produces the smallest, safest image possible.

## When to Use This Skill

- Containerizing an application for the first time
- Optimizing a slow or bloated Docker build
- Setting up docker-compose for local development
- Reviewing a Dockerfile for security or efficiency
- Debugging "it works locally but not in Docker"

---

## Dockerfile: Go Application (Production Template)

```dockerfile
# Stage 1: Build
FROM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

# Stage 2: Run
FROM alpine:3.20
RUN apk --no-cache add ca-certificates tzdata
RUN adduser -D -u 1000 appuser
USER appuser
COPY --from=builder /app/server /usr/local/bin/server
EXPOSE 8080
ENTRYPOINT ["server"]
```

### Why this template

- **Multi-stage** — build tools stay in stage 1; final image has only the binary
- **`CGO_ENABLED=0`** — static binary, no libc dependency
- **`-ldflags="-s -w"`** — strip debug info, smaller binary
- **Non-root user** — `appuser` with UID 1000
- **Minimal base** — `alpine` (~5 MB); or `scratch` for even smaller

---

## Key Rules

### Build optimization

1. **Order layers by change frequency.** Stable layers first (`COPY go.mod` before `COPY .`). Docker caches unchanged layers.
2. **Use multi-stage builds.** Build in a full SDK image; copy only the artifact to a minimal runtime image.
3. **Pin base image versions.** `golang:1.23-alpine`, not `golang:latest`.
4. **Minimize layers.** Combine related `RUN` commands with `&&`.
5. **Use `.dockerignore`.** Exclude `.git`, `node_modules`, `vendor`, test data, docs.

### Image size

6. **Alpine or distroless base.** Alpine ~5 MB; distroless ~2 MB; Ubuntu ~75 MB.
7. **For Go/Rust static binaries: `FROM scratch`.** Zero OS, smallest possible image.
8. **Remove package manager cache** in the same `RUN` layer: `apk --no-cache add ...`.
9. **Don't install tools you don't need in production.** No `vim`, `curl`, `git` in the final image.

### Security

10. **Run as non-root.** `RUN adduser` + `USER appuser`.
11. **Don't store secrets in images.** Use env vars, mounted secrets, or secret managers.
12. **Scan images for CVEs.** `docker scout cves`, Trivy, Snyk.
13. **Use `COPY`, not `ADD`.** `ADD` auto-extracts archives and fetches URLs — unexpected behavior.
14. **Read-only filesystem when possible.** `docker run --read-only`.

---

## .dockerignore

```
.git
.github
.env
*.md
docs/
node_modules/
vendor/
**/*_test.go
coverage.out
```

15. **Always have a `.dockerignore`.** Without it, the entire repo (including `.git`) is sent as build context.

---

## docker-compose (Local Dev)

```yaml
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/myapp?sslmode=disable
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: myapp
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

### Compose rules

16. **Use `depends_on` with `condition: service_healthy`.** Don't rely on startup order alone.
17. **Named volumes for persistent data.** Anonymous volumes are hard to manage.
18. **Override files for local dev.** `docker-compose.override.yml` — mount source for hot-reload.
19. **Don't use compose in production.** Use Kubernetes, ECS, or similar orchestrators.

---

## Common Debugging

| Problem | Fix |
|---------|-----|
| Build cache not working | Check layer order; `COPY . .` too early invalidates everything |
| Image is 1GB+ | Multi-stage build; smaller base; check `.dockerignore` |
| Container exits immediately | Check `ENTRYPOINT`/`CMD`; logs via `docker logs <id>` |
| "Permission denied" in container | Non-root user can't write to root-owned paths; `chown` or use `/tmp` |
| Can't connect to DB from container | Use service name (`db`), not `localhost`; check network |
| Slow builds | Copy dependency files first (go.mod, package.json); let Docker cache them |

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `FROM ubuntu` for a Go binary | `FROM alpine` or `FROM scratch` |
| `RUN apt-get update` without cleanup in same layer | `RUN apt-get update && apt-get install -y X && rm -rf /var/lib/apt/lists/*` |
| Running as root | `USER appuser` |
| `COPY . .` as the first instruction | Copy dependency files first for caching |
| Secrets in `ENV` or `ARG` | Build-time: `--mount=type=secret`; runtime: mounted secrets |
| No `.dockerignore` | Build context includes `.git`, tests, etc. |
| `latest` tag in production | Pin version: `alpine:3.20` |

---

## Checklist

- [ ] Multi-stage build (build + runtime stages)
- [ ] Base image pinned and minimal
- [ ] Layers ordered by change frequency
- [ ] `.dockerignore` excludes `.git`, tests, docs
- [ ] Non-root user
- [ ] No secrets in image
- [ ] `ENTRYPOINT` (not `CMD`) for the main process
- [ ] Image scanned for CVEs
- [ ] Compose has health checks for dependencies
- [ ] Image size is reasonable (< 50 MB for Go; < 200 MB for Node)

---

## Related Skills

- [`github-actions`](../github-actions/SKILL.md) — build and push images in CI
- [`rules/dockerfile`](../rules/dockerfile.md) — quick rule sheet for Dockerfile conventions
