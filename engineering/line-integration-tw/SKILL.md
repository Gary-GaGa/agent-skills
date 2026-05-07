---
name: line-integration-tw
description: >
  LINE platform integration for the Taiwan market — LINE Login, LINE Notify,
  LIFF, the Messaging API, and Rich Menu, with patterns for common scenarios
  like group sign-ups and reservations. For web services that need LINE-based
  social login, push notifications, or in-LINE web apps in Taiwan.
category: engineering
tags: [line, taiwan, login, notification, liff, messaging, integration]
keywords: [LINE Login, LINE Notify, LIFF, Messaging API, Rich Menu, Flex Message]
related: [auth-patterns, nextjs-fundamentals, realtime-websocket, tw-payment-integration]
---

# LINE Integration (Taiwan Market)

> LINE penetration in Taiwan is over 90%. If your target users are in Taiwan, LINE Login + LINE Notify is essentially mandatory.

## When to Use This Skill

- Implementing LINE Login (social sign-in)
- Sending notifications via LINE Notify (free, simple)
- Sending messages via the Messaging API (official account)
- Embedding a web app inside LINE with LIFF
- Building an interactive bottom menu via Rich Menu

---

## LINE Developer Console Setup

### Create a Channel

1. Go to [LINE Developers Console](https://developers.line.biz/)
2. Create a Provider
3. Create a Channel:
   - **LINE Login** — for social sign-in
   - **Messaging API** — for messages and Rich Menu
   - **LINE Notify** — simple push notifications (separate service)

### What to record

| Item | Where to find it |
|------|------------------|
| Channel ID | Channel basic settings |
| Channel Secret | Channel basic settings |
| Channel Access Token | Messaging API → Issue |
| Callback URL | LINE Login → settings |
| Webhook URL | Messaging API → settings |
| LIFF ID | LINE Login → LIFF → add |

---

## LINE Login

### Flow (OAuth 2.0 authorization code)

```
1. Frontend redirects to LINE authorization page
2. User consents
3. LINE redirects back to your callback URL (with `code`)
4. Backend exchanges `code` for access_token + id_token
5. Backend uses access_token to fetch user profile
6. Backend creates/updates the user → issues your own JWT
```

### Go backend

```go
// Step 4: exchange code for token
func exchangeLineToken(code, redirectURI string) (*LineTokenResponse, error) {
    data := url.Values{
        "grant_type":    {"authorization_code"},
        "code":          {code},
        "redirect_uri":  {redirectURI},
        "client_id":     {lineChannelID},
        "client_secret": {lineChannelSecret},
    }
    resp, err := http.PostForm("https://api.line.me/oauth2/v2.1/token", data)
    // parse response → LineTokenResponse{AccessToken, IDToken, ...}
}

// Step 5: get user profile
func getLineProfile(accessToken string) (*LineProfile, error) {
    req, _ := http.NewRequest("GET", "https://api.line.me/v2/profile", nil)
    req.Header.Set("Authorization", "Bearer "+accessToken)
    // parse response → LineProfile{UserID, DisplayName, PictureURL}
}
```

### Frontend redirect

```tsx
const LINE_AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize";
const params = new URLSearchParams({
  response_type: "code",
  client_id: process.env.NEXT_PUBLIC_LINE_CHANNEL_ID!,
  redirect_uri: `${window.location.origin}/auth/line/callback`,
  state: generateRandomState(),   // CSRF protection
  scope: "profile openid email",
});
window.location.href = `${LINE_AUTH_URL}?${params}`;
```

### Rules

1. **Always verify the `state` parameter.** Without it, you're open to CSRF.
2. **LINE User ID is per-Channel-unique.** The same person has different UserIDs across different Channels.
3. **`email` scope must be requested separately.** Apply for it in the LINE Login Channel settings.
4. **`id_token` is a JWT containing user info.** You can decode it directly to get name, picture, email — no second profile call needed.

---

## LINE Notify (free push)

The simplest notification path: free, no official-account requirement, up to 1000 messages/hour per token.

### User-authorization flow

```
1. User clicks "Connect LINE Notify" on your site
2. Redirects to LINE Notify auth page
3. User picks a chat (themself or a group) to receive notifications
4. LINE returns a code → your backend exchanges for access_token
5. Store the token; later use it to send notifications
```

### Sending a notification

```go
func sendLineNotify(token, message string) error {
    data := url.Values{"message": {message}}
    req, _ := http.NewRequest("POST",
        "https://notify-api.line.me/api/notify",
        strings.NewReader(data.Encode()))
    req.Header.Set("Authorization", "Bearer "+token)
    req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
    resp, err := http.DefaultClient.Do(req)
    // check resp.StatusCode == 200
    return err
}
```

### Where it fits

| Scenario | Notification |
|----------|--------------|
| Someone joins a meetup | "Alice joined your basketball group! (5/10)" |
| Group is full | "Your badminton group is full at 6 — game on!" |
| Group cancelled | "Tomorrow's volleyball is cancelled — venue under maintenance" |
| Event reminder | "Reminder: basketball tomorrow 19:00 at XX gym" |

5. **LINE Notify is per-user token.** Each user has their own token after authorizing.
6. **Group notifications:** during authorization, the user can choose a group; messages go to the group. Useful for meetup/group scenarios.
7. **Free, but limited:** 1000 messages/hour per token. Plenty for small apps.

---

## Messaging API (Official Account)

More powerful than LINE Notify: Flex Messages (rich layout), Quick Reply, Rich Menu.

### Sending a push message

```go
func sendPushMessage(userID, text string) error {
    body := map[string]any{
        "to": userID,
        "messages": []map[string]any{
            {"type": "text", "text": text},
        },
    }
    jsonBody, _ := json.Marshal(body)
    req, _ := http.NewRequest("POST",
        "https://api.line.me/v2/bot/message/push",
        bytes.NewReader(jsonBody))
    req.Header.Set("Authorization", "Bearer "+channelAccessToken)
    req.Header.Set("Content-Type", "application/json")
    resp, err := http.DefaultClient.Do(req)
    return err
}
```

### Flex Message (rich layout)

```go
// A meetup card
flexMessage := map[string]any{
    "type": "flex",
    "altText": "New meetup: basketball @ XX gym",
    "contents": map[string]any{
        "type": "bubble",
        "header": map[string]any{...},
        "body": map[string]any{
            "type": "box", "layout": "vertical",
            "contents": []map[string]any{
                {"type": "text", "text": "🏀 Basketball", "weight": "bold", "size": "xl"},
                {"type": "text", "text": "📍 XX Gym"},
                {"type": "text", "text": "📅 2025/01/20 19:00-21:00"},
                {"type": "text", "text": "👥 3/10 people"},
            },
        },
        "footer": map[string]any{
            "type": "box", "layout": "vertical",
            "contents": []map[string]any{
                {"type": "button", "action": map[string]any{
                    "type": "uri", "label": "Join now",
                    "uri": "https://your-app.com/groups/abc123",
                }},
            },
        },
    },
}
```

8. **Push messages have a free quota.** Free tier: 200/month; paid tiers are usage-based.
9. **Flex Message Simulator** for designing layouts: [https://developers.line.biz/flex-simulator/](https://developers.line.biz/flex-simulator/)

---

## LIFF (LINE Frontend Framework)

Embed your web app inside LINE: a user clicks a link in chat → your web app opens, but inside LINE.

### Where it fits

- Meetup sign-up page (share the link in a LINE group → user signs up without leaving LINE)
- Profile editing
- Payment page

### Frontend usage

```tsx
import liff from "@line/liff";

async function initLIFF() {
  await liff.init({ liffId: "your-liff-id" });
  if (!liff.isLoggedIn()) {
    liff.login();
    return;
  }
  const profile = await liff.getProfile();
  // profile.userId, profile.displayName, profile.pictureUrl
}
```

10. **LIFF gets LINE user info automatically.** No separate LINE Login flow needed.
11. **LIFF can share messages to chats.** `liff.shareTargetPicker(messages)` lets the user share a meetup link.
12. **Three LIFF sizes:** Compact (bottom popup), Tall (2/3 screen), Full (full screen).

---

## Rich Menu (Bottom Menu)

A tappable image menu at the bottom of an Official Account chat.

```json
{
  "size": {"width": 2500, "height": 843},
  "areas": [
    {
      "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
      "action": {"type": "uri", "uri": "https://your-app.com/groups"}
    },
    {
      "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
      "action": {"type": "uri", "uri": "https://your-app.com/groups/create"}
    },
    {
      "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
      "action": {"type": "uri", "uri": "https://your-app.com/profile"}
    }
  ]
}
```

Three buttons that match a meetup app: "Find groups", "Create group", "My profile".

---

## Recommended LINE Integration for a Meetup Service

| Feature | Use | Priority |
|---------|-----|----------|
| Sign-in | LINE Login | Must |
| Group-created / full notifications | LINE Notify | Must |
| Share meetup to LINE | LIFF `shareTargetPicker` | Recommended |
| Rich meetup card | Messaging API Flex Message | Recommended |
| Bottom menu | Rich Menu | Nice to have |
| In-LINE sign-up | LIFF | Nice to have |

13. **Start with LINE Login + LINE Notify.** Together they cover 80% of needs and are cheap to implement.
14. **Add LIFF and Flex Message later.** They polish the experience without being on the critical path.

---

## Common Traps

| Trap | Counter |
|------|---------|
| **LINE User ID differs across Channels** | Use your own user ID as the primary key; LINE ID is an external identity |
| **Forgetting state validation** | CSRF risk — always validate |
| **LINE Notify token leak** | The token *is* the send permission. Store in DB, never in the frontend |
| **LIFF init failure unhandled** | Check whether you're inside LINE; have a browser fallback |
| **Messaging API quota exhausted** | Monitor usage; route critical notifications via LINE Notify (free) |
| **Webhook returns non-200** | LINE retries. Return 200 first, then process asynchronously |
| **Channel Access Token expiration** | Use long-lived tokens or auto-rotate |

---

## Pre-Flight Checklist

- [ ] LINE Login Channel configured (Callback URL, scope)
- [ ] LINE Login flow → backend token exchange → user creation
- [ ] `state` parameter validated (CSRF)
- [ ] LINE Notify authorization flow tested
- [ ] Notification scenarios defined (which events trigger pushes)
- [ ] LINE User ID mapped to your system's user ID
- [ ] Channel Secret / Access Token never in frontend or git
- [ ] Stage uses a separate LINE Channel
- [ ] LIFF (if used) tested both inside LINE and in a regular browser

---

## Related Skills

- [`auth-patterns`](../auth-patterns/SKILL.md) — LINE Login is one OAuth flavor
- [`nextjs-fundamentals`](../nextjs-fundamentals/SKILL.md) — frontend LIFF + LINE Login integration
- [`realtime-websocket`](../realtime-websocket/SKILL.md) — pair real-time updates with LINE Notify
- [`tw-payment-integration`](../tw-payment-integration/SKILL.md) — payment flow
