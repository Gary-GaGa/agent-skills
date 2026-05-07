---
name: second-brain
description: >
  Personal knowledge management (PKM) system — Zettelkasten, the PARA method,
  tool selection (Obsidian / Notion / Logseq), linking strategy, regular review,
  and the workflow from input to output. For people who want a system that
  manages their notes, ideas, and reading material end-to-end.
category: productivity
tags: [pkm, second-brain, zettelkasten, obsidian, note-taking, productivity]
related: [learning-methodology, time-management]
---

# Second Brain (Personal Knowledge Management)

> Your brain is for having ideas, not for storing them. Outsource the storage and the linking to a system.

## When to Use This Skill

- Studied a lot but can't recall or find anything
- Notes scattered across phone, sticky notes, multiple apps
- Want to convert reading into usable knowledge
- Want a knowledge base you can "have a conversation with"
- Want to write or create more efficiently (have raw material to compose from)

---

## Core Principles

1. **Capture anything worth remembering.** Don't trust memory; trust the system.
2. **One note = one idea.** Atomic notes — one concept per note.
3. **Linking matters more than categorizing.** Links between notes create new ideas; folders are just storage.
4. **Review regularly.** A system that isn't reviewed rots.
5. **Serve action.** The point of PKM is output (writing, decisions, problem solving), not hoarding.

---

## Method Choice

### PARA (Tiago Forte)

Organized by *purpose*:

```
Projects/   — bounded efforts with a goal and deadline (book, build, launch)
Areas/      — ongoing responsibility (health, finances, career)
Resources/  — topics of interest (technical, investing, hobbies)
Archives/   — no longer active
```

**Best for:** action-oriented people, project-centric work.

### Zettelkasten (Luhmann)

Organized by *links*:

- Each note has a unique ID
- Notes connect via bidirectional links
- No strict folder hierarchy
- New ideas emerge from following links

**Best for:** researchers, writers, anyone trying to generate original ideas.

### Hybrid (recommended for beginners)

```
PARA manages "what to do" (Projects, Areas)
Zettelkasten manages "what you know" (organize Resources/ with links)
```

6. **Don't spend forever picking a method.** Pick one, start, adjust at the 3-month mark.

---

## Tool Choice

| Tool | Strengths | Best for |
|------|-----------|----------|
| **Obsidian** | Local Markdown, bidirectional links, rich plugin ecosystem | Developers, Zettelkasten |
| **Logseq** | Outline-based, local-first, bidirectional links | Daily-journal flow, outline thinkers |
| **Notion** | Databases, collaboration, templates | Teams, project + notes hybrid |
| **Apple Notes** | Simple, syncs across devices | Quick capture, low-maintenance |
| **Heptabase** | Whiteboard-style visual links | Visual thinkers |

7. **Obsidian is the best fit for developers.** Local Markdown (no lock-in), Git-backable, bidirectional links, large plugin ecosystem.
8. **The tool doesn't matter — the habit does.** The most-used tool beats the most-featured tool.

---

## Note Types

| Type | Purpose | Example |
|------|---------|---------|
| **Fleeting note** | Capture an idea fast, unprocessed | "gRPC streaming might fit X" |
| **Literature note** | Summary + your takeaways from a reading | 3–5 bullets after reading an article |
| **Permanent note** | A standalone concept written in your own words | "The optimal review interval for spaced repetition is..." |
| **Project note** | Working notes for a specific project | Sprint retro, tech decision log |

### The flow

```
Fleeting → daily processing → Literature / Permanent → linked to existing notes → reviewed
```

9. **A fleeting note is not a permanent note.** Process within 24 hours (promote or delete).
10. **Permanent notes are written in your own words.** Copy-paste is data, not knowledge. Rewriting in your words = understood.

---

## Linking Strategy

### How to add links

11. **When writing a new note, ask: "what is this related to?"** Find 2–3 existing notes to link.
12. **Bidirectional links are the point.** `[[Concept A]]` linking to `[[Concept B]]` automatically backlinks B → A.
13. **Use MOC (Map of Content) as an index.** A "table of contents" for a topic, listing related notes.

```markdown
# Go Concurrency MOC

Related notes:
- [[goroutine lifecycle]]
- [[channel direction restrictions]]
- [[errgroup patterns]]
- [[common race conditions]]
- [[context cancellation propagation]]
```

14. **Don't over-categorize.** 3–5 top-level folders is plenty. Links > folders.

---

## Review System

| Review | Frequency | What you do |
|--------|-----------|-------------|
| **Daily review** | 5 min/day | Process fleeting notes, recap today's learnings |
| **Weekly review** | 30 min/week | Tidy this week's notes, update project progress, find new links |
| **Monthly review** | 1 hr/month | Survey the vault, archive finished projects, find knowledge gaps |
| **Random resurfacing** | Daily | Obsidian Random Note plugin to surface old notes |

15. **The daily review is the most important habit.** Five minutes is enough. Skip it = the system slowly dies.
16. **Random resurfacing creates serendipitous links.** This is one of the most valuable PKM features.

---

## Knowledge Workflow: Input to Output

```
Input (reading, listening, experience)
   ↓
Capture (fleeting notes, highlights)
   ↓
Process (rewrite in your own words → permanent note)
   ↓
Link (find related notes, add bidirectional links)
   ↓
Review (daily / weekly cleanup)
   ↓
Output (write articles, make decisions, teach others)
```

17. **Output is the only real test.** A vault that only takes input is a fancy bookmark folder.
18. **Writing is the best output.** After learning a topic, write a note or article.

---

## Common Traps

| Trap | Fix |
|------|-----|
| **Tool obsession** — constant tool switching | Pick one, use it 3 months before reassessing |
| **Hoarder** — input only, no output | Set an output goal (1 article / month) |
| **Perfectionism** — every note must be polished | Drafts are fine; refine on review |
| **Compulsive categorizing** | Links > folders. Don't burn 30 minutes deciding where it goes |
| **No review** | Calendar reminder; build the daily 5-minute habit |
| **Recording everything** | Only what changes your mind or you'll need later |

---

## Quick-Start Checklist

- [ ] Pick a tool (Obsidian recommended)
- [ ] Create 4 top-level folders (Projects / Areas / Resources / Archives)
- [ ] Schedule a daily 5-minute review slot
- [ ] Write your first permanent note (the most important thing you learned today)
- [ ] Link it to at least one existing note
- [ ] Commit to using the system for 3 months before reassessing

---

## Related Skills

- [`learning-methodology`](../learning-methodology/SKILL.md) — the second brain is where the learning lives
- [`time-management`](../time-management/SKILL.md) — finding the time to review and process
