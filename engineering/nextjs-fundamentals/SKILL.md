---
name: nextjs-fundamentals
description: >
  Next.js fundamentals for frontend development — App Router, server/client
  components, data fetching, API routes, authentication (next-auth), Tailwind +
  shadcn/ui, and deployment. Use this skill when building a Next.js frontend
  that connects to a separate backend API.
category: engineering
tags: [nextjs, react, frontend, typescript, tailwind, ssr]
related: [api-design-rest, auth-patterns, realtime-websocket]
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

## Authentication (next-auth)

```ts
// lib/auth.ts
import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import LINE from "next-auth/providers/line";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    Google({ clientId: process.env.GOOGLE_ID!, clientSecret: process.env.GOOGLE_SECRET! }),
    LINE({ clientId: process.env.LINE_ID!, clientSecret: process.env.LINE_SECRET! }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account) {
        // exchange provider token for your backend's token
        const res = await fetch(`${API_URL}/auth/social`, {
          method: "POST",
          body: JSON.stringify({ provider: account.provider, token: account.access_token }),
        });
        const data = await res.json();
        token.accessToken = data.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      return session;
    },
  },
});
```

11. **next-auth handles the OAuth flow.** You configure providers; it handles redirects, callbacks, tokens.
12. **Exchange provider tokens for YOUR backend tokens.** next-auth gets Google's token; your backend issues its own JWT.
13. **Store your backend's access token in the next-auth session.** Use it in API calls.

---

## Forms with Server Actions

```tsx
// app/groups/create/page.tsx
"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({
  sport: z.string().min(1),
  location: z.string().min(1),
  date: z.string(),
  maxMembers: z.number().min(2).max(30),
});

export default function CreateGroupPage() {
  const form = useForm({ resolver: zodResolver(schema) });

  async function onSubmit(data: z.infer<typeof schema>) {
    const res = await fetch("/api/groups", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (res.ok) router.push("/groups");
  }

  return <form onSubmit={form.handleSubmit(onSubmit)}>...</form>;
}
```

14. **Validate with Zod on both client and server.** Share the schema if possible.
15. **react-hook-form for complex forms.** Minimal re-renders, built-in validation integration.

---

## Styling with Tailwind + shadcn/ui

```tsx
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

function GroupCard({ group }: { group: Group }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{group.sport}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{group.location.name}</p>
        <p className="text-sm">{group.schedule.date} {group.schedule.startTime}</p>
        <p className="font-medium">{group.members.length}/{group.maxMembers} 人</p>
        <Button className="mt-2 w-full">加入</Button>
      </CardContent>
    </Card>
  );
}
```

16. **shadcn/ui components are copy-pasted into your project** (not npm dep). Full control.
17. **Tailwind for layout and spacing; shadcn for complex components** (dialog, dropdown, form).

---

## SEO

```tsx
// app/groups/[id]/page.tsx
import { Metadata } from "next";

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const group = await fetchGroup(params.id);
  return {
    title: `${group.sport} — ${group.location.name}`,
    description: `${group.schedule.date} ${group.schedule.startTime}，還有 ${group.maxMembers - group.members.length} 個名額`,
  };
}
```

18. **Server Components enable SSR for SEO.** Google crawls the rendered HTML, not client JS.
19. **Dynamic metadata per page.** `generateMetadata` runs server-side.

---

## Deployment

### Vercel (simplest)

```bash
npx vercel
```

### Docker (self-hosted)

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

20. **`output: "standalone"`** for Docker. Produces a minimal self-contained server.

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

21. **`NEXT_PUBLIC_` prefix = exposed to browser.** Everything else is server-only.
22. **Never put secrets in `NEXT_PUBLIC_` vars.**

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
- [ ] next-auth configured with social providers
- [ ] Forms validated with Zod
- [ ] SEO metadata on public pages
- [ ] Environment variables properly scoped (NEXT_PUBLIC_ vs server-only)
- [ ] Tailwind + shadcn/ui for styling
- [ ] `output: "standalone"` if Docker-deployed

---

## Related Skills

- [`api-design-rest`](../api-design-rest/SKILL.md) — the REST API the frontend consumes
- [`auth-patterns`](../auth-patterns/SKILL.md) — backend auth that next-auth integrates with
- [`realtime-websocket`](../realtime-websocket/SKILL.md) — live updates for group status
