# Next.js Deployment

Loaded from [`../SKILL.md`](../SKILL.md). Open this when shipping a
Next.js app to Vercel or self-hosting with Docker. Rule numbers are
local to this file (cite as `nextjs-fundamentals/deployment:rule-N`).

---

## Vercel (simplest)

```bash
npx vercel
```

Push to GitHub and Vercel can auto-deploy on every commit. Environment
variables are set in the Vercel dashboard.

---

## Docker (self-hosted)

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

In `next.config.js`:
```js
module.exports = { output: "standalone" };
```

1. **`output: "standalone"`** for Docker. Produces a minimal self-contained server.

---

## Environment Variables

```env
# .env.local (gitignored)
NEXT_PUBLIC_API_URL=http://localhost:8080    # client-accessible
API_URL=http://localhost:8080                # server-only
GOOGLE_ID=xxx
GOOGLE_SECRET=xxx
LINE_ID=xxx
LINE_SECRET=xxx
NEXTAUTH_SECRET=random-secret
NEXTAUTH_URL=http://localhost:3000
```

2. **`NEXT_PUBLIC_` prefix = exposed to browser.** Everything else is server-only.
3. **Never put secrets in `NEXT_PUBLIC_` vars.**
