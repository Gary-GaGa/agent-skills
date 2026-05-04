---
name: fine-tuning-guide
description: >
  When and how to fine-tune LLMs — deciding if fine-tuning is the right approach,
  data preparation, evaluation, deployment, and common pitfalls. Use this skill
  when prompt engineering isn't enough and you're considering training a custom model.
category: ai-engineering
tags: [fine-tuning, llm, training, data, model-customization]
related: [prompt-engineering, agent-evaluation, llm-cost-optimization]
---

# Fine-Tuning Guide

> Fine-tuning is the last resort, not the first. Exhaust prompt engineering, few-shot, and RAG before training a custom model. If you still need fine-tuning, this skill tells you how to do it right.

## When to Use This Skill

- Prompt engineering can't achieve the format, style, or accuracy you need
- You have 100+ high-quality training examples
- Latency or cost requirements demand a smaller specialized model
- You need domain-specific behavior that few-shot examples can't teach

---

## Decision: Fine-Tune or Not?

### Try these first (cheaper, faster, reversible)

| Technique | When it's enough |
|-----------|------------------|
| **Better prompt** | 80% of "model is wrong" cases |
| **More few-shot examples** | Format / style issues |
| **RAG** | Knowledge gaps (model doesn't know X) |
| **Bigger model** | Reasoning quality issues |
| **Structured output (tool calls)** | Output format issues |

### Fine-tune when

1. **Consistent style/format that few-shot can't lock in.** Example: always responding in a specific JSON schema with domain-specific fields.
2. **Domain vocabulary/behavior.** Example: medical coding, legal analysis with specific taxonomy.
3. **Cost reduction.** A fine-tuned small model can replace a large model for narrow tasks.
4. **Latency.** Smaller fine-tuned model = faster inference.
5. **You have 100+ high-quality examples.** Fewer than that = fine-tuning overfits or underperforms vs few-shot.

### Don't fine-tune when

- You have < 50 examples (use few-shot instead)
- The task changes frequently (fine-tuning is slow to update)
- You need general reasoning (fine-tuning narrows, not broadens)
- RAG + prompting solves the problem (cheaper, more flexible)

---

## Data Preparation

### Data format

Most providers expect JSONL with `messages`:

```jsonl
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

### Rules

6. **Quality over quantity.** 200 excellent examples beat 2,000 noisy ones.
7. **Diverse inputs.** Cover the variety of real-world queries. Edge cases, short inputs, long inputs, ambiguous inputs.
8. **Consistent outputs.** All assistant responses follow the exact same format, style, and quality you want.
9. **System prompt in training data.** If you use a system prompt in production, include it in training examples.
10. **Split: 80% train, 10% validation, 10% test.** Never evaluate on training data.

### Data quality checklist

- [ ] Each example has a realistic user input (not synthetic-looking)
- [ ] Each assistant response is exactly what you want the model to produce
- [ ] Format is consistent across all examples
- [ ] No contradictory examples (same input, different correct output)
- [ ] Edge cases and failures represented
- [ ] PII redacted
- [ ] At least 100 examples (200+ recommended)

---

## Training

### Provider comparison

| Provider | Fine-tuning support | Models |
|----------|---------------------|--------|
| **OpenAI** | Full (API) | GPT-4o, GPT-4o-mini |
| **Anthropic** | Limited availability | Claude (contact sales) |
| **Together AI** | Open models | Llama, Mistral, etc. |
| **Fireworks** | Open models | Llama, Mixtral |
| **Self-hosted** | Full control | Any open model |

### Hyperparameters (typical)

| Parameter | Start with | Tune if |
|-----------|------------|---------|
| Epochs | 3 | Val loss increasing = reduce; still learning = increase |
| Learning rate | Provider default | Training unstable = lower; learning too slow = higher |
| Batch size | Provider default | Usually not worth tuning |

11. **Start with provider defaults.** Only tune hyperparameters if validation metrics are poor.
12. **Watch validation loss.** If it increases while training loss decreases = overfitting. Stop training or reduce epochs.

---

## Evaluation

### Compare against baselines

```
Baseline 1: Base model + your best prompt (no fine-tuning)
Baseline 2: Base model + few-shot examples
Baseline 3: Larger model + prompt (e.g., GPT-4o with prompt vs fine-tuned GPT-4o-mini)
Fine-tuned: Your custom model
```

13. **Fine-tuning must beat baselines on your eval set.** Otherwise it's not worth the maintenance cost.
14. **Evaluate on the held-out test set, never on training data.**
15. **Measure: accuracy, format compliance, hallucination rate, latency, cost.**

### Regression testing

16. **Fine-tuning can degrade general capabilities.** Test on a few "general knowledge" questions to verify the model didn't lose basic competence.

---

## Deployment

17. **Versioned model names.** `my-model-v1`, `my-model-v2`. Don't overwrite.
18. **Shadow testing.** Run fine-tuned model alongside production model; compare outputs before switching.
19. **Gradual rollout.** 10% → 50% → 100% with monitoring.
20. **Monitor for drift.** Fine-tuned models can degrade over time if the input distribution changes.

---

## Maintenance

21. **Plan for re-training.** New examples, updated guidelines, changed formats → re-train.
22. **Keep the training data versioned.** You'll need to reproduce or augment later.
23. **Document what the model was trained on, when, and what it's intended for.**
24. **Budget for periodic re-evaluation.** Run the eval set monthly to detect degradation.

---

## Anti-Patterns

| Anti-pattern | Fix |
|--------------|-----|
| Fine-tuning before trying prompt engineering | Exhaust prompt + few-shot + RAG first |
| < 50 training examples | Collect more or use few-shot |
| Training on noisy / inconsistent data | Clean rigorously; quality > quantity |
| No validation set | Always hold out 10%+ for validation |
| No comparison against baselines | Must beat base model + good prompt |
| Evaluating on training data | Use held-out test set only |
| Overwriting models without versioning | Version every training run |
| No monitoring after deployment | Monthly eval + drift detection |
| Fine-tuning for knowledge (factual recall) | Use RAG instead |
| Fine-tuning a huge model for a narrow task | Fine-tune the smallest model that works |

---

## Decision Flowchart

```
Can prompt engineering solve it? ──► Yes ──► Don't fine-tune
         │ No
Can few-shot examples solve it? ──► Yes ──► Don't fine-tune
         │ No
Can RAG solve it (knowledge gap)? ──► Yes ──► Don't fine-tune
         │ No
Do you have 100+ quality examples? ──► No ──► Collect more data first
         │ Yes
Is the task narrow and stable? ──► No ──► Reconsider; fine-tuning is brittle for changing tasks
         │ Yes
         └──► Fine-tune the smallest model that meets quality
```

---

## Checklist

- [ ] Confirmed prompt engineering + few-shot + RAG aren't sufficient
- [ ] 100+ high-quality, diverse, consistent training examples
- [ ] Data split into train (80%), validation (10%), test (10%)
- [ ] System prompt included in training examples
- [ ] Baselines established (base model + prompt, larger model)
- [ ] Fine-tuned model beats baselines on held-out test set
- [ ] General capability regression tested
- [ ] Model versioned; training data versioned
- [ ] Shadow testing before full deployment
- [ ] Monthly re-evaluation planned

---

## Related Skills

- [`prompt-engineering`](../prompt-engineering/SKILL.md) — try this first
- [`agent-evaluation`](../agent-evaluation/SKILL.md) — eval framework for fine-tuned models
- [`llm-cost-optimization`](../llm-cost-optimization/SKILL.md) — fine-tuning for cost reduction
