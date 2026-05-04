---
name: claude-code-customization
description: >
  Customizing Claude Code via settings.json, hooks, slash commands, MCP servers,
  CLAUDE.md memory files, plugins, and statusline. Use this skill when tailoring
  Claude Code to a specific project, automating repetitive workflows, enforcing
  team conventions, or building a personal Claude Code setup.
category: ai-engineering
tags: [claude-code, anthropic, customization, hooks, mcp, settings]
related: [skill-authoring, mcp-server-design, agent-harness-design, agentic-coding-patterns]
---

# Claude Code Customization

> Out of the box, Claude Code is a useful generic agent. Customized, it becomes a project- or team-specific tool that knows your conventions, runs your tests, and enforces your standards automatically.

## When to Use This Skill

- Setting up Claude Code for a new project / team
- Wanting Claude to remember project conventions automatically
- Automating "every time X happens, do Y" patterns
- Adding custom slash commands for common workflows
- Integrating Claude Code with internal tools (via MCP)
- Auditing existing Claude Code customization

---

## The Customization Surface

```
~/.claude/                       ← User-level (across all projects)
  ├── settings.json              ← User settings, hooks, env, permissions
  ├── CLAUDE.md                  ← User-level memory (rare)
  ├── commands/                  ← User-level slash commands
  ├── agents/                    ← User-level sub-agents
  └── skills/                    ← User-level skills

<project>/                       ← Project-level (this repo only)
  ├── CLAUDE.md                  ← Project memory; loaded every session
  ├── .claude/
  │   ├── settings.json          ← Project settings (committed)
  │   ├── settings.local.json    ← Local overrides (gitignored)
  │   ├── commands/              ← Project slash commands
  │   ├── agents/                ← Project sub-agents
  │   └── skills/                ← Project skills
  └── ...
```

**Precedence (most specific wins):**
project local > project committed > user > built-in defaults.

---

## CLAUDE.md (Memory)

A markdown file Claude reads at session start. Content goes straight into the system context.

### What belongs in CLAUDE.md

1. **Project-specific facts.** "This is a Go monolith using Echo and PostgreSQL."
2. **Conventions Claude must follow.** "Use sqlc, not raw queries. All errors wrap with `%w`."
3. **Pointers to deeper docs.** "Architecture details: docs/architecture.md."
4. **Common commands.** "Run tests with `make test`. Build with `make build`."
5. **Things to avoid.** "Don't suggest changes to internal/legacy/."

### Scope discipline

- **Project CLAUDE.md** is loaded for every session in that repo. Keep it under ~500 lines or it bloats every session.
- **User CLAUDE.md** is loaded for every session globally. Reserve for genuine personal preferences.
- **Don't** put project-irrelevant info in user CLAUDE.md (it leaks into every project).

---

## Settings (settings.json)

Located at `~/.claude/settings.json` (user) or `.claude/settings.json` (project).

### Common configuration

```json
{
  "model": "claude-sonnet-4-6",
  "env": {
    "MY_API_KEY": "${secret}"
  },
  "permissions": {
    "allow": ["Bash(npm test:*)", "Bash(git diff)", "Edit", "Read"],
    "deny": ["Bash(rm -rf:*)", "Bash(curl:*)"]
  },
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

### Permissions

The most important safety lever in Claude Code.

| Permission element | Pattern |
|--------------------|---------|
| Allow specific Bash | `"Bash(npm test:*)"` |
| Deny dangerous Bash | `"Bash(rm -rf:*)"`, `"Bash(curl:*)"` |
| Auto-allow tool | `"Edit"`, `"Read"` |
| Auto-allow MCP tool | `"mcp__github__*"` |

**Rule:** Allowlist over denylist where practical. Allow what you know is safe; everything else prompts.

---

## Hooks

Run shell commands at agent lifecycle events.

### Hook events

| Event | When it fires |
|-------|---------------|
| `SessionStart` | Beginning of a new session |
| `UserPromptSubmit` | Before user's prompt is sent to model |
| `PreToolUse` | Before a tool is invoked |
| `PostToolUse` | After a tool completes |
| `Stop` | When Claude stops responding |

### Common hook patterns

| Use case | Event | What it does |
|----------|-------|--------------|
| Run linter on save | `PostToolUse` (Edit/Write) | `eslint $FILE_PATH` |
| Block dangerous commands | `PreToolUse` (Bash) | Inspect command, exit non-zero to block |
| Inject project context | `SessionStart` | Echo current branch / open tickets |
| Format on edit | `PostToolUse` (Edit) | `prettier --write $FILE_PATH` |
| Audit log | `PreToolUse` (any) | Append to log file |
| Notify on completion | `Stop` | Desktop notification |

### Hook design

2. **Hooks are shell, not Claude.** They run as subprocesses; the model doesn't decide what they do.
3. **Exit code matters.** Non-zero from a `PreToolUse` hook blocks the action.
4. **Keep them fast.** Hooks add latency to every event. Sub-second is the goal.
5. **Don't make hooks essential to correctness.** They can fail silently in edge cases. Use as augmentation, not security.

### Example: format on edit

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$CLAUDE_FILE_PATH\" 2>/dev/null || true"
          }
        ]
      }
    ]
  }
}
```

### Example: block production-touching commands

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"$CLAUDE_TOOL_INPUT\" | grep -qE 'production|prod-' && exit 1 || exit 0"
          }
        ]
      }
    ]
  }
}
```

---

## Slash Commands

Custom commands the user types as `/<name>`. Resolve to a templated prompt.

### Location

```
.claude/commands/<name>.md       ← project
~/.claude/commands/<name>.md     ← user
```

### Format

```markdown
---
description: Run a security review on the current branch
---

Review all changes on the current branch (`git diff main...HEAD`) for:
- SQL injection
- XSS
- Hardcoded secrets
- Authentication / authorization issues
- Dependency vulnerabilities

Output a markdown report with severity levels.
```

When the user types `/security-review`, the markdown body becomes the prompt.

### Patterns

6. **Use slash commands for recurring multi-step prompts.** "Generate a release note", "Audit the API surface", "Run pre-PR checks".
7. **Parameterize via `$ARGUMENTS`.** `/explain-file $ARGUMENTS` lets the user pass context.
8. **Project-level commands beat user-level** when the workflow is project-specific.

---

## Sub-Agents

Reusable specialized agents in `.claude/agents/<name>.md`.

### Format

```markdown
---
description: A code reviewer focused on Go-specific issues
tools: [Read, Grep, Glob]
model: claude-sonnet-4-6
---

You are a strict Go code reviewer. For each file you review:

1. Check error handling follows the rules in `rules/go-error-handling.md`.
2. Verify naming follows `rules/go-naming.md`.
3. Flag any unsafe constructs.

Report findings as a markdown checklist.
```

The user invokes via the `Agent` tool. Useful for delegating bounded sub-tasks.

---

## MCP Servers

Configure in `settings.json` or via `mcp` CLI.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "${env:GITHUB_TOKEN}" }
    }
  }
}
```

See [`mcp-server-design`](../mcp-server-design/SKILL.md) for design principles.

### Common MCP servers worth knowing

- **Filesystem** — local file access (built-in via tools, but MCP version adds capabilities)
- **GitHub** — issues, PRs, repos
- **Slack / Linear / Notion** — common SaaS integrations
- **Database connectors** — Postgres, MySQL, etc.

---

## Statusline

Customize the bottom-of-terminal status display.

```json
{
  "statusLine": {
    "type": "command",
    "command": "echo \"$(git branch --show-current) | $(date +%H:%M)\""
  }
}
```

The output of the command becomes the statusline. Useful for showing branch, model, token usage, etc.

---

## Plugins

Plugins are bundles of skills, agents, commands, hooks, and settings distributable as a single unit.

```
my-plugin/
├── plugin.json
├── skills/
├── agents/
├── commands/
├── hooks/
└── settings.json
```

Install via the marketplace or directly. Useful for sharing team-specific Claude Code configurations.

---

## Composing for a Project: A Template

For a typical project repo, ship:

```
project/
├── CLAUDE.md                      # project conventions, commands, gotchas
├── .claude/
│   ├── settings.json              # permissions, hooks, MCP refs
│   ├── commands/
│   │   ├── pre-pr.md              # /pre-pr — run linter, tests, type check
│   │   ├── audit-deps.md          # /audit-deps — security scan
│   │   └── update-changelog.md    # /update-changelog
│   ├── agents/
│   │   └── code-reviewer.md       # specialist agent
│   └── skills/                    # local project-specific skills
└── ...
```

This gets new contributors productive immediately and encodes team norms in code.

---

## Anti-Patterns

| Anti-pattern | Why bad | Fix |
|--------------|---------|-----|
| 2,000-line CLAUDE.md | Bloats every session | Trim to essentials; link to detail docs |
| Project conventions in user CLAUDE.md | Leaks into every project | Move to project CLAUDE.md |
| Permissions allowlist `*` | Defeats the safety layer | Specific patterns only |
| Hook that takes 10s on every edit | Cripples UX | Keep hooks < 1s |
| Hooks doing security enforcement | Can fail silently | Use permissions for security; hooks for ergonomics |
| Slash commands for one-off prompts | Bloats command list | Reserve commands for recurring workflows |
| Customization scattered across personal dotfiles | Not portable, not shareable | Use project `.claude/` for project-specific |

---

## Auditing Existing Customization

For an inherited project setup, run through:

- [ ] CLAUDE.md is current and concise (< 500 lines)
- [ ] Permissions explicitly allow common safe ops (faster UX)
- [ ] Permissions explicitly deny dangerous ops (`rm -rf`, `curl`)
- [ ] Hooks are documented (what they do, why, expected runtime)
- [ ] Slash commands cover common workflows
- [ ] MCP servers are pinned to known versions
- [ ] No secrets in committed settings.json (use `${env:VAR}`)
- [ ] settings.local.json is gitignored

---

## Related Skills

- [`skill-authoring`](../skill-authoring/SKILL.md) — writing skills that load in Claude Code
- [`mcp-server-design`](../mcp-server-design/SKILL.md) — building MCP servers Claude Code can use
- [`agent-harness-design`](../agent-harness-design/SKILL.md) — Claude Code is one specific harness
- [`agent-safety-guardrails`](../agent-safety-guardrails/SKILL.md) — permissions are the safety layer
