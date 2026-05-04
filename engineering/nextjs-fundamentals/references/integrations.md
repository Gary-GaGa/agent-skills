# Next.js Integrations

Loaded from [`../SKILL.md`](../SKILL.md). Open this when implementing
authentication, forms, styling, or SEO. Rule numbers are local to this
file (cite as `nextjs-fundamentals/integrations:rule-N`).

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

1. **next-auth handles the OAuth flow.** You configure providers; it handles redirects, callbacks, tokens.
2. **Exchange provider tokens for YOUR backend tokens.** next-auth gets Google's token; your backend issues its own JWT.
3. **Store your backend's access token in the next-auth session.** Use it in API calls.

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

4. **Validate with Zod on both client and server.** Share the schema if possible.
5. **react-hook-form for complex forms.** Minimal re-renders, built-in validation integration.

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

6. **shadcn/ui components are copy-pasted into your project** (not npm dep). Full control.
7. **Tailwind for layout and spacing; shadcn for complex components** (dialog, dropdown, form).

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

8. **Server Components enable SSR for SEO.** Google crawls the rendered HTML, not client JS.
9. **Dynamic metadata per page.** `generateMetadata` runs server-side.
