---
name: nextjs-fundamentals
description: >
  Next.js fundamentals for frontend development — App Router, server/client
  components, data fetching, API routes, authentication (next-auth), Tailwind +
  shadcn/ui, and deployment. Use this skill when building a Next.js frontend
  that connects to a separate backend API.
category: engineering
tags: [nextjs, react, frontend, typescript, tailwind, ssr]
related: [api-design-rest, auth-patterns, realtime-websocket, line-integration-tw]
---

# Next.js Fundamentals

> Next.js gives React structure: file-based routing, server rendering, API routes, and deployment — so you focus on the product, not the plumbing.

## When to Use This Skill

- Building a React frontend with Next.js (App Router)
- Setting up a new Next.js project
- Choosing between Server Components and Client Components
- Integrating with an external backend API
- Adding authentication with next-auth
- Deploying to Vercel or self-hosting with Docker

---

## Project Setup

```bash
npx create-next-app@latest booking-frontend \
  --typescript --tailwind --eslint --app --src-dir
cd booking-frontend
npm install
npm run dev   # http://localhost:3000
```

### Recommended additional deps

```bash
npm install @tanstack/react-query zod zustand
npm install next-auth@beta
npx shadcn@latest init   # UI component library
```

---

## App Router Structure

```
src/
├── app/
│   ├── layout.tsx          # root layout (shared across all pages)
│   ├── page.tsx            # home page (/)
│   ├── globals.css
│   ├── groups/
│   │   ├── page.tsx        # /groups (list)
│   │   ├── [id]/
│   │   │   └── page.tsx    # /groups/:id (detail)
│   │   └── create/
│   │       └── page.tsx    # /groups/create
│   ├── profile/
│   │   └── page.tsx        # /profile
│   └── api/
│       └── auth/
│           └── [...nextauth]/
│               └── route.ts  # next-auth handler
├── components/
│   ├── ui/                 # shadcn components
│   ├── group-card.tsx
│   └── navbar.tsx
├── lib/
│   ├── api.ts              # API client
│   ├── auth.ts             # next-auth config
│   └── utils.ts
└── types/
    └── index.ts            # shared TypeScript types
```

### Rules

1. **`app/` directory = routes.** Every `page.tsx` is a route. `layout.tsx` wraps child routes.
2. **`components/` for reusable UI.** Not in `app/` — keep routes thin.
3. **`lib/` for utilities.** API client, auth config, helpers.
4. **`types/` for shared TypeScript types.** Especially API response types.

---

## Server Components vs Client Components

### Server Components (default in App Router)

- Run on the server only
- Can `async/await` directly (fetch data)
- Can't use `useState`, `useEffect`, `onClick`
- Smaller bundle (code stays on server)

```tsx
// app/groups/page.tsx — Server Component (default)
export default async function GroupsPage() {
  const groups = await fetch(`${API_URL}/groups`).then(r => r.json());
  return (
    <div>
      {groups.map(g => <GroupCard key={g.id} group={g} />)}
    </div>
  );
}
```

### Client Components

- Run in the browser
- Can use hooks (`useState`, `useEffect`)
- Required for interactivity (forms, buttons, real-time)

```tsx
// components/join-button.tsx
"use client";

import { useState } from "react";

export function JoinButton({ groupId }: { groupId: string }) {
  const [loading, setLoading] = useState(false);

  async function handleJoin() {
    setLoading(true);
    await fetch(`/api/groups/${groupId}/join`, { method: "POST" });
    setLoading(false);
  }

  return <button onClick={handleJoin} disabled={loading}>Join</button>;
}
```

5. **Default to Server Components.** Only add `"use client"` when you need interactivity.
6. **Server Components can render Client Components.** Not the reverse.
7. **Keep Client Components small.** Extract the interactive part; leave data fetching to server.

---

## Data Fetching

### From external API (your Go backend)

```tsx
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;

export async function fetchGroups(): Promise<Group[]> {
  const res = await fetch(`${API_URL}/v1/groups`, {
    next: { revalidate: 60 },  // ISR: revalidate every 60s
  });
  if (!res.ok) throw new Error("Failed to fetch groups");
  return res.json();
}
```

### With React Query (Client Components)

```tsx
"use client";
import { useQuery } from "@tanstack/react-query";

export function GroupList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["groups"],
    queryFn: () => fetch("/api/groups").then(r => r.json()),
  });

  if (isLoading) return <Spinner />;
  if (error) return <Error message={error.message} />;
  return <div>{data.map(g => <GroupCard key={g.id} group={g} />)}</div>;
}
```

8. **Server Components: `fetch` directly.** Use `next: { revalidate: N }` for caching.
9. **Client Components: React Query.** Handles loading, error, caching, refetching.
10. **API URL: `NEXT_PUBLIC_` prefix for client-accessible env vars.** Without prefix = server-only.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| `"use client"` on every component | Default to Server Component; add only for interactivity |
| Fetching data in Client Component when Server works | Move fetch to Server Component |
| API keys in `NEXT_PUBLIC_` | Server-only env vars; proxy through API route |
| No loading/error states | React Query or Suspense boundaries |
| Giant `page.tsx` with logic + UI | Extract components; keep page thin |
| Inline styles | Tailwind classes |
| No TypeScript types for API responses | Define in `types/`; validate with Zod |

---

## Checklist

- [ ] App Router with `src/app/` structure
- [ ] Server Components by default; `"use client"` only where needed
- [ ] API client in `lib/api.ts` with error handling
- [ ] React Query for client-side data fetching
- [ ] next-auth configured with social providers (see `references/integrations.md`)
- [ ] Forms validated with Zod (see `references/integrations.md`)
- [ ] SEO metadata on public pages (see `references/integrations.md`)
- [ ] Environment variables properly scoped (see `references/deployment.md`)
- [ ] Tailwind + shadcn/ui for styling (see `references/integrations.md`)
- [ ] `output: "standalone"` if Docker-deployed (see `references/deployment.md`)

---

## References

Loaded on demand when the body links to them:

- [`references/integrations.md`](./references/integrations.md) — next-auth, forms with Zod, Tailwind + shadcn/ui, SEO metadata.
- [`references/deployment.md`](./references/deployment.md) — Vercel deployment, Docker self-hosting, environment variable scoping.

---

## Related Skills

- [`api-design-rest`](../api-design-rest/SKILL.md) — the REST API the frontend consumes
- [`auth-patterns`](../auth-patterns/SKILL.md) — backend auth that next-auth integrates with
- [`realtime-websocket`](../realtime-websocket/SKILL.md) — live updates for group status
