---
name: mcp-server-design
description: >
  Designing Model Context Protocol (MCP) servers — when to use MCP vs custom
  tools, server lifecycle, the three primitives (tools, resources, prompts),
  transport choices (stdio vs HTTP/SSE), and security considerations. Use
  this skill when building a new MCP server or deciding whether MCP is the
  right packaging for a capability.
category: ai-engineering
tags: [mcp, agent, tool, server, protocol]
related: [tool-design-for-agents, agent-harness-design, claude-code-customization]
---

# MCP Server Design

> MCP is a USB-C port for tools. Once you've built an MCP server, any compatible client (Claude Desktop, Claude Code, Cursor, custom agents) can use it. The cost: a layer of indirection that's not always worth it.

## When to Use This Skill

- Deciding whether to wrap a capability as an MCP server vs an in-process tool
- Designing a new MCP server from scratch
- Choosing between stdio and HTTP/SSE transport
- Picking the right MCP primitive (tool / resource / prompt) for a capability
- Auditing an existing MCP server for safety and ergonomics

---

## What MCP Is, in 30 Seconds

```
MCP Server (your code)  ←──── MCP protocol ────→  MCP Client (Claude Code, etc.)
                                                          │
                                                          └─→ The LLM gets tools/resources/prompts
```

- **Open protocol** — vendor-agnostic, JSON-RPC over stdio or HTTP/SSE
- **Three primitives** — Tools (callable), Resources (readable data), Prompts (templates)
- **One server, many clients** — write once, use across apps

Spec: [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## When to Use MCP vs an In-Process Tool

| Use MCP when | Use in-process tool when |
|--------------|--------------------------|
| Multiple agent apps need the same capability | One app, no reuse expected |
| The capability has its own runtime / dependencies | Capability is a few lines of code |
| You want users to install/configure independently | Capability is core to your app |
| It's data exposure (resources) more than action (tools) | Pure action, no shareable data |
| It's a wrapper around an existing service (Slack, GitHub) | New custom logic |

**Rule of thumb:** MCP shines for **integrations** (wrapping APIs, databases, dev tools). Don't reach for it for in-app helpers.

### The cost of MCP

- Extra process to manage (stdio) or service to deploy (HTTP)
- Serialization overhead per call
- Authentication/authorization layer to design
- Versioning and protocol compatibility concerns
- Debugging across the wire

For small-team internal tools, a direct tool implementation is often simpler.

---

## The Three Primitives

### 1. Tools

Callable operations the model invokes. Same design principles as any agent tool.

**Use for:** actions, computations, mutations.

```
search_issues, create_pr, send_message, query_db
```

See [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) for the design principles.

### 2. Resources

Readable, addressable data. The client (or model) requests by URI.

**Use for:** files, database rows, logs, structured data the model wants to read.

```
file:///path/to/foo.txt
issues://github/repo/42
db://schema/users/123
```

Resources differ from tools in that they're **named, addressable, and meant to be read** — not invoked with arbitrary arguments.

### 3. Prompts

Pre-built prompt templates with parameters that the user (not the model) selects, e.g. as a slash command.

**Use for:** common workflows the user wants to trigger directly.

```
/summarize_pr <pr_number>
/explain_query <query>
/security_review
```

### Picking the right primitive

| Question | Pick |
|----------|------|
| Does the model invoke it with computed arguments? | **Tool** |
| Does the model want to read named data? | **Resource** |
| Does the user trigger a templated prompt? | **Prompt** |

Many MCP servers use only tools. Resources and prompts are powerful but optional.

---

## Server Lifecycle

```
1. Client launches server (stdio) or connects (HTTP)
2. Capability negotiation (handshake) — server lists what it offers
3. Client lists tools / resources / prompts
4. Model invokes (via client) → server executes → response
5. Server runs until client disconnects
```

### Lifecycle considerations

1. **Cold start matters.** stdio servers spawn per session. Startup > 1s feels sluggish.
2. **Persistent state** must outlive the process for stdio (write to disk / external store).
3. **Capability advertisement is honest.** Don't list tools you can't actually serve under current config.

---

## Transport: stdio vs HTTP/SSE

| | stdio | HTTP/SSE |
|---|-------|----------|
| **Best for** | Local dev tools, per-user installs | Hosted services, multi-user |
| **Setup** | Spawned by client | Run as a service |
| **Auth** | Trust the local user | Need explicit auth (OAuth, tokens) |
| **State** | Per-process; ephemeral by default | Can be persistent |
| **Cost to operate** | Free | Hosting costs |
| **Distribution** | Bundle as binary or npm/pip package | Provide URL |

**Default:** stdio for personal/local tools (Claude Desktop, Claude Code installs); HTTP/SSE for shared/hosted services.

---

## Security & Trust

MCP servers can do almost anything — read your files, hit external APIs, exfiltrate data. **Treat installation like installing a CLI tool.**

### Server-side rules

4. **Authenticate users at the boundary.** HTTP servers need explicit auth (no anonymous tools that mutate).
5. **Scope down credentials.** A GitHub MCP server should use a token with the minimum scopes needed.
6. **Validate every input.** The model can hallucinate parameters. Treat them as untrusted.
7. **Don't return secrets in tool responses.** Even if the user has access — the model now sees them.
8. **Log mutations.** Anything that creates/modifies external state should leave an audit trail.

### Client-side considerations (for users)

- Only install MCP servers you trust the source of (same as installing CLIs)
- Review the tools the server advertises; deny anything unnecessary
- For HTTP servers, use scoped tokens, rotate regularly

---

## Designing the Tool Surface

Same principles as [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md), with MCP-specific notes:

9. **Namespace your tools.** If the server is for GitHub, prefix with `gh_` or use a server-level namespace. Multiple MCP servers may load simultaneously; collisions are real.
10. **Don't expose every endpoint.** A "GitHub MCP server" with 80 tools is unusable. Pick the 10-15 the agent actually needs.
11. **Group with resources.** Static data (issue templates, schema definitions) belongs in resources, not tools.
12. **Be conservative with destructive tools.** Provide read-only tools by default; gate mutations behind explicit config or scopes.

---

## Common Designs

### A. CRUD wrapper (e.g. database, ticketing system)

- Tools: `create_X`, `update_X`, `delete_X`
- Resources: `X://<id>` for reads
- Prompts: optional templates for common queries

Map operations to the agent's mental model — not 1:1 with the underlying API.

### B. Read-only data exposure

- All resources, no tools (or one tool: `search_X`)
- Cleaner UX; no "tool noise" for the model

### C. Process automation

- Tools: high-level verbs (`deploy`, `rollback`, `run_check`)
- Each tool wraps a multi-step internal flow
- Prompts: "/deploy <env>" templates the user can invoke

### D. Local file/dev tooling

- stdio transport
- Tools for read/edit/search
- Resources for files (`file://...`)

---

## Versioning & Compatibility

13. **MCP protocol version is in the handshake.** Servers should support the negotiated version or fail clearly.
14. **Tool signatures are part of your API contract.** Renaming a tool or removing a parameter breaks downstream agents.
15. **Add tools / parameters; don't change them.** Same backward-compat rules as any API.
16. **Document changes per release.** Users need to know if they should pin a version.

---

## Testing MCP Servers

| Layer | How |
|-------|-----|
| **Unit** | Test handlers as plain functions |
| **Protocol** | Use the `mcp` CLI / inspector to send raw JSON-RPC |
| **Integration** | Wire to a real client (Claude Code, Inspector) and run end-to-end |
| **Agent** | Eval the agent's behavior with this server in the toolbox |

Inspectors / dev tools:

- **MCP Inspector** — official UI for poking at servers
- Library-specific test helpers (`mcp.client.create_test_server` etc.)

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| Wrapping every API endpoint as a tool | Tool noise; bad selection | Curate the 10-15 the agent needs |
| Mixing many unrelated capabilities in one server | Hard to install/scope | Split into focused servers |
| Returning huge raw API responses | Eats context budget | Summarize / paginate at the server |
| Echoing tool errors as raw exceptions | Model can't recover | Return structured error with hint |
| Mutating tools without auth | Anyone with the URL can act | Add OAuth or token auth |
| Server with no description on tools | Model can't pick correctly | Same description discipline as any tool |
| Long startup blocking client | UX feels broken | Lazy-init expensive setup |

---

## Audit Checklist

Before publishing an MCP server:

- [ ] Server name is clear (`github-mcp` not `mcp1`)
- [ ] Tool count is justified (5-20; more requires lazy loading or splitting)
- [ ] Each tool has a description with trigger words
- [ ] Resources used for read-only addressable data
- [ ] Mutating tools have auth + audit logging
- [ ] Errors are structured, not raw exceptions
- [ ] Tested with at least one real MCP client (not just unit tests)
- [ ] Documented: install, configure, usage, capabilities
- [ ] Version pinning + changelog for breaking changes
- [ ] Security: token scopes minimized, secrets not in responses

---

## Related Skills

- [`tool-design-for-agents`](../tool-design-for-agents/SKILL.md) — tool design principles apply to MCP tools
- [`agent-harness-design`](../agent-harness-design/SKILL.md) — MCP servers slot into the harness's tool surface
- [`claude-code-customization`](../claude-code-customization/SKILL.md) — using MCP servers in Claude Code
- [`agent-safety-guardrails`](../agent-safety-guardrails/SKILL.md) — MCP servers are a security boundary
