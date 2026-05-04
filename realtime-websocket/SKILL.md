---
name: realtime-websocket
description: >
  Real-time communication patterns for web apps — WebSocket, SSE, Socket.IO,
  Go server implementation, React client integration, and common patterns
  (presence, pub/sub, rooms). Use this skill when building features that
  need live updates (chat, notifications, collaborative editing, live status).
category: engineering
tags: [websocket, sse, realtime, go, react, socket-io]
related: [api-design-rest, nextjs-fundamentals, go-concurrency, event-driven-architecture]
---

# Real-Time WebSocket

> REST is request-response. WebSocket is a persistent connection — server can push to client anytime. Use it when the client needs to know about changes as they happen, not only when it asks.

## When to Use This Skill

- Building live features: group join/leave updates, chat, notifications
- Choosing between WebSocket, SSE, and polling
- Implementing a WebSocket server in Go
- Integrating real-time in a React/Next.js frontend
- Designing room/channel-based pub/sub

---

## When to Use What

| Method | Direction | Best for | Complexity |
|--------|-----------|----------|------------|
| **Polling** | Client → Server (repeated) | Simple, low-frequency updates | Low |
| **SSE (Server-Sent Events)** | Server → Client (one-way) | Notifications, feeds, status updates | Low |
| **WebSocket** | Bidirectional | Chat, collaborative, gaming, high-frequency | Medium |
| **Socket.IO** | Bidirectional + features | WebSocket + auto-reconnect, rooms, fallback | Medium |

### Decision

1. **If the client only needs to receive updates → SSE.** Simpler than WebSocket.
2. **If bidirectional communication is needed → WebSocket.**
3. **If you need rooms, reconnection, fallback → Socket.IO** (wraps WebSocket).
4. **If updates are every 30s+ and low-frequency → polling is fine.** Don't over-engineer.

For a group sports booking app: **WebSocket or SSE** for "someone joined/left the group" updates.

---

## Go WebSocket Server (gorilla/websocket)

### Setup

```go
import "github.com/gorilla/websocket"

var upgrader = websocket.Upgrader{
    CheckOrigin: func(r *http.Request) bool {
        return isAllowedOrigin(r.Header.Get("Origin"))
    },
}

func handleWS(w http.ResponseWriter, r *http.Request) {
    conn, err := upgrader.Upgrade(w, r, nil)
    if err != nil { return }
    defer conn.Close()

    client := &Client{conn: conn, groupID: r.URL.Query().Get("group_id")}
    hub.Register(client)
    defer hub.Unregister(client)

    go client.writePump()
    client.readPump()
}
```

### Hub pattern (central message router)

```go
type Hub struct {
    clients    map[*Client]bool
    rooms      map[string]map[*Client]bool
    register   chan *Client
    unregister chan *Client
    broadcast  chan Message
}

func (h *Hub) Run() {
    for {
        select {
        case client := <-h.register:
            h.clients[client] = true
            h.rooms[client.groupID][client] = true

        case client := <-h.unregister:
            delete(h.clients, client)
            delete(h.rooms[client.groupID], client)
            close(client.send)

        case msg := <-h.broadcast:
            for client := range h.rooms[msg.RoomID] {
                select {
                case client.send <- msg.Data:
                default:
                    close(client.send)
                    delete(h.clients, client)
                }
            }
        }
    }
}
```

### Client read/write pumps

```go
type Client struct {
    conn    *websocket.Conn
    send    chan []byte
    groupID string
}

func (c *Client) readPump() {
    defer func() { hub.unregister <- c; c.conn.Close() }()
    c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
    c.conn.SetPongHandler(func(string) error {
        c.conn.SetReadDeadline(time.Now().Add(60 * time.Second))
        return nil
    })
    for {
        _, message, err := c.conn.ReadMessage()
        if err != nil { break }
        handleMessage(c, message)
    }
}

func (c *Client) writePump() {
    ticker := time.NewTicker(30 * time.Second)
    defer func() { ticker.Stop(); c.conn.Close() }()
    for {
        select {
        case msg, ok := <-c.send:
            if !ok { c.conn.WriteMessage(websocket.CloseMessage, nil); return }
            c.conn.WriteMessage(websocket.TextMessage, msg)
        case <-ticker.C:
            c.conn.WriteMessage(websocket.PingMessage, nil)
        }
    }
}
```

5. **Ping/pong keeps the connection alive.** Without it, idle connections get killed by proxies.
6. **Separate read and write goroutines per client.** WebSocket connections are not safe for concurrent writes.
7. **Hub is the single goroutine that manages all connections.** No mutexes needed — channel-based.

---

## SSE (Server-Sent Events) — Go

Simpler for one-way server→client:

```go
func handleSSE(w http.ResponseWriter, r *http.Request) {
    flusher, ok := w.(http.Flusher)
    if !ok { http.Error(w, "SSE not supported", 500); return }

    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    w.Header().Set("Connection", "keep-alive")

    groupID := r.URL.Query().Get("group_id")
    ch := hub.Subscribe(groupID)
    defer hub.Unsubscribe(groupID, ch)

    for {
        select {
        case msg := <-ch:
            fmt.Fprintf(w, "event: %s\ndata: %s\n\n", msg.Event, msg.Data)
            flusher.Flush()
        case <-r.Context().Done():
            return
        }
    }
}
```

8. **SSE auto-reconnects natively.** Browsers reconnect automatically on disconnect.
9. **SSE is HTTP — works through most proxies.** WebSocket upgrade can be blocked.

---

## React Client (Next.js)

### WebSocket hook

```tsx
"use client";
import { useEffect, useRef, useCallback } from "react";

export function useWebSocket(url: string, onMessage: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onclose = () => {
      setTimeout(() => { /* reconnect logic */ }, 3000);
    };

    return () => ws.close();
  }, [url]);

  const send = useCallback((data: any) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);

  return { send };
}
```

### Usage in component

```tsx
"use client";

export function GroupLiveStatus({ groupId }: { groupId: string }) {
  const [members, setMembers] = useState<Member[]>([]);

  useWebSocket(`${WS_URL}/ws?group_id=${groupId}`, (data) => {
    if (data.event === "member_joined") {
      setMembers(prev => [...prev, data.member]);
    }
    if (data.event === "member_left") {
      setMembers(prev => prev.filter(m => m.id !== data.member.id));
    }
  });

  return <MemberList members={members} />;
}
```

### SSE hook (even simpler)

```tsx
"use client";

export function useSSE(url: string, onEvent: (event: string, data: any) => void) {
  useEffect(() => {
    const source = new EventSource(url);
    source.addEventListener("member_joined", (e) => onEvent("member_joined", JSON.parse(e.data)));
    source.addEventListener("member_left", (e) => onEvent("member_left", JSON.parse(e.data)));
    return () => source.close();
  }, [url]);
}
```

10. **SSE is simpler client-side.** Native `EventSource` API, auto-reconnect, no library needed.

---

## Message Protocol

### Structure

```json
{
  "event": "member_joined",
  "room": "group_abc123",
  "data": {
    "user_id": "user_456",
    "name": "Alice",
    "joined_at": "2025-01-15T19:30:00Z"
  },
  "timestamp": "2025-01-15T19:30:00Z"
}
```

11. **Typed events.** `event` field tells the client what happened; `data` carries the payload.
12. **Include `timestamp`.** For ordering and deduplication.
13. **Include `room/channel`.** Client can verify it's for the right group.

---

## Common Patterns

### Rooms / Channels

Group connections by topic (e.g. one room per group):

```
Room "group_abc" → [Client A, Client B, Client C]
Room "group_def" → [Client D, Client E]
```

Messages broadcast only within the room.

### Presence

Track who's online:

```json
// On connect
{"event": "presence_join", "data": {"user_id": "123", "name": "Alice"}}

// On disconnect
{"event": "presence_leave", "data": {"user_id": "123"}}

// Periodic
{"event": "presence_list", "data": {"users": [...]}}
```

### Scaling (multiple server instances)

Single Hub works for one server. For multiple:

14. **Use Redis Pub/Sub as the message bus.** Each server subscribes; broadcasts propagate across instances.
15. **Or use NATS / Kafka for more complex routing.**

---

## Security

16. **Authenticate on connect.** Pass JWT as query param or first message; verify before accepting.
17. **Authorize per room.** Only group members can subscribe to that group's room.
18. **Rate-limit messages.** Prevent flooding.
19. **Validate all incoming messages.** Treat client messages as untrusted input.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| WebSocket when SSE suffices | One-way updates → SSE |
| No ping/pong | Connections die silently |
| Concurrent writes to same conn | One write goroutine per client |
| No reconnection on client | Auto-reconnect with backoff |
| Auth only at HTTP level | Re-verify JWT on WS connect |
| Broadcasting to all clients | Use rooms/channels |
| No message typing | `event` field on every message |
| Unlimited message rate | Rate-limit per client |

---

## Checklist

- [ ] Chose the right method (polling / SSE / WebSocket) for the use case
- [ ] Ping/pong configured for keepalive
- [ ] Separate read/write goroutines per client (WebSocket)
- [ ] Hub pattern for connection management
- [ ] Room-based broadcasting (not global)
- [ ] Authentication on connect (JWT)
- [ ] Authorization per room (membership check)
- [ ] Client auto-reconnects with backoff
- [ ] Messages have `event`, `data`, `timestamp` structure
- [ ] Rate limiting on incoming messages

---

## Related Skills

- [`api-design-rest`](../api-design-rest/SKILL.md) — REST for CRUD; WebSocket for live updates
- [`nextjs-fundamentals`](../nextjs-fundamentals/SKILL.md) — React client integration
- [`go-concurrency`](../go-concurrency/SKILL.md) — goroutine patterns for the hub
- [`event-driven-architecture`](../event-driven-architecture/SKILL.md) — events as the source of real-time messages
