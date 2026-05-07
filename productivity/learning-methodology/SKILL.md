---
name: learning-methodology
description: >
  Systematic learning methodology — the Feynman Technique, spaced repetition,
  deliberate practice, the Learning Pyramid, and a high-efficiency framework
  for technical learning. For developers and lifelong learners who want to
  raise the return on study time.
category: productivity
tags: [learning, methodology, feynman, spaced-repetition, productivity]
related: [second-brain, time-management]
---

# Learning Methodology

> Learning efficiency isn't about hours spent — it's about method. The same hour, with a different approach, can have 10× retention.

## When to Use This Skill

- Learning a new technical domain (Kubernetes, blockchain, machine learning)
- Feeling "I read a lot but remember nothing"
- Building a sustainable learning system
- Wanting to shorten the path from beginner to practitioner

---

## The Learning Pyramid

| Method | Retention |
|--------|-----------|
| Lecture | ~5% |
| Reading | ~10% |
| Audio-visual | ~20% |
| Demonstration | ~30% |
| **Discussion / participation** | ~50% |
| **Hands-on practice** | ~75% |
| **Teaching others** | ~90% |

1. **Passive learning (watch, listen, read) has the lowest retention.** Not useless, but not enough on its own.
2. **Active learning (do, teach, discuss) has the highest retention.** Always pair study with practice.
3. **The most effective study: teach what you just learned.** This is the core of the Feynman Technique.

---

## The Feynman Technique

### Four steps

1. **Pick a concept** — e.g. "gRPC streaming"
2. **Explain it in simple language, as if to a complete beginner** — no jargon
3. **Find where you got stuck** — the parts you can't explain are the parts you don't really understand
4. **Go back, fill the gap, explain again** — repeat until smooth

### How to apply it

- Write a blog post or note targeting an absolute beginner
- Post a "Today I learned X — in plain words..." snippet to a community
- Use analogies: "gRPC streaming is like a phone call (continuous), REST is like postal mail (one Q, one A)"

4. **If you can't explain it simply, you don't understand it well enough.** That's on you, not on the reader.

---

## Spaced Repetition

### The principle

Forgetting curve: ~70% of new material is lost within 24 hours. But reviewing *just before* you'd forget extends retention dramatically.

### Suggested intervals

```
1st review:  1 day later
2nd review:  3 days later
3rd review:  7 days later
4th review: 21 days later
5th review: 60 days later
```

### Tools

- **Anki** — flashcard software that schedules reviews automatically
- **Note-system review** — set a weekly review in Obsidian / Notion

5. **Don't apply spaced repetition to everything.** Reserve it for the core concepts you must remember.
6. **Phrase items as questions.** "What is `context.WithTimeout`?" is a better review prompt than the statement form.

---

## Deliberate Practice

### Versus ordinary practice

| Ordinary practice | Deliberate practice |
|-------------------|---------------------|
| Repeat what's comfortable | Push the edge of ability |
| No specific goal | A concrete small goal each session |
| Done is done | Feedback and correction loop |
| Lots of unfocused hours | Short, focused blocks (45–90 min) |

### Applying it to technical learning

7. **Set a "just beyond your current ability" challenge.** Not redoing what you know, not jumping to what you can't read at all.
8. **One focus per session.** Today: goroutine lifecycle. Not "Go concurrency" in general.
9. **Keep a feedback loop.** Write → run tests → read the result → fix. Tests *are* the feedback.
10. **Short bursts of focus beat long unfocused stretches.** 45 minutes of full attention > 3 distracted hours.

---

## Framework for Learning a New Technology

### Five steps

```
Step 1: Why  — what problem does this solve? Why does it exist?
Step 2: What — core concepts (3–5 keywords)
Step 3: How  — a minimal working example ("hello world")
Step 4: Build — a small project of your own design (not a tutorial copy)
Step 5: Teach — write notes or teach someone else
```

11. **Do not start at Step 3.** Knowing the Why and What is what makes the code make sense.
12. **Step 4 matters most.** Following a tutorial is not learning. Designing a small problem and solving it is.
13. **Step 5 cements memory.** Feynman + spaced repetition.

### Example: learning Kubernetes

```
Step 1: Why  — manual container management hurts at 50+ machines.
Step 2: What — Pod, Deployment, Service, ConfigMap, Ingress.
Step 3: How  — run an nginx Deployment on minikube.
Step 4: Build — deploy your own Go API to K8s (with health checks, env config).
Step 5: Teach — write "5 core K8s concepts from a Go developer's perspective".
```

---

## Learning Anti-Patterns

| Trap | Symptom | Fix |
|------|---------|-----|
| **Tutorial hell** | Watched 10 tutorials, wrote 0 lines of your own | After tutorial #1, hands on |
| **Hoarder** | Bookmarked 100 articles, read 5 | Save only what you need *now* |
| **Perfectionism** | "Once I've seen everything, I'll start" | Start before you're ready |
| **Knowledge anxiety** | "Too many things to learn" | One topic at a time |
| **Comfort-zone loops** | Always doing what you already know | Find the edge; deliberate practice |
| **Read-only mode** | Pure passive intake | Force output via Feynman |
| **No notes** | Read once, forget once | Run a `second-brain` system |

---

## A Suggested Daily Flow

```
Morning (30–60 min)
  - Deliberate practice on one focus skill (coding, problem solving)

Evening (15–30 min)
  - Spaced-repetition review (Anki or notes)
  - Feynman output: a short "Today I learned X, in plain words..."

Weekly (1–2 hr)
  - Review notes from the week
  - Update the learning roadmap (what to learn next week)
```

14. **30 minutes a day beats 8 hours on Saturday.** The spacing effect is real.
15. **Rest is part of learning.** The brain consolidates memory when you stop studying (walks, sleep).

---

## Pre-Flight Checklist

Before starting on a new topic:

- [ ] Wrote down "why am I learning this" (motivation)
- [ ] Listed 3–5 core concepts (the *What*)
- [ ] Found one minimal working example (the *How*)
- [ ] Set a small project goal (the *Build*)
- [ ] Planned where you'll output (the *Teach*) — notes, blog, community
- [ ] Booked a daily learning slot (30–60 minutes)
- [ ] Accepted "imperfect start" beats "perfect procrastination"

---

## Related Skills

- [`second-brain`](../second-brain/SKILL.md) — note system to retain what you learn
- [`time-management`](../time-management/SKILL.md) — finding the time to learn
