# Scoring experiment — lexical vs TF-IDF vs embeddings

**Status:** TF-IDF run on this commit; embedding script committed but not
yet run (HuggingFace blocked in the sandbox where this experiment was
authored — the maintainer should run `scripts/run_embedding_eval.py`
locally with internet access).

## Why we ran this

`run_routing_eval.py` reports **wild recall@1 = 42.9%**. That number is
ambiguous: is it bad because

  (a) the lexical scorer (substring + whole-word + bigram) is too crude
      to handle paraphrases and typos, or
  (b) the frontmatter (description, tags, keywords) is genuinely too
      generic to discriminate certain skills?

If (a), invest in a better scorer. If (b), invest in tighter
descriptions and keyword backfill. We need data to decide.

## Method

Same eval set (`evals/skill-routing.jsonl`, 47 cases). Three scorers
on the same skills:

| Scorer | Implementation | What it captures |
|--------|----------------|------------------|
| lexical | `run_routing_eval.py` (current baseline) | hand-rolled substring + whole-word + token overlap + CJK bigram |
| tf-idf | `run_tfidf_eval.py` (this PR) | scikit-learn TF-IDF + cosine; CJK bigram tokenizer for parity |
| embedding | `run_embedding_eval.py` (this PR, **not yet run**) | sentence-transformers multilingual MiniLM, cosine on document embeddings |

All three score the same document for each skill: `name + description + tags + keywords`.

## Results

### Lexical (current baseline)

```
overall  recall@1 75.0%  recall@3 90.0%  MRR 0.824  unanswerable 100%
curated  recall@1 92.3%  recall@3 100%   MRR 0.962  unanswerable 100%
wild     recall@1 42.9%  recall@3 71.4%  MRR 0.567  unanswerable 100%
```

### TF-IDF

```
overall  recall@1 77.5%  recall@3 90.0%  MRR 0.837  unanswerable 14.3%
curated  recall@1 96.2%  recall@3 100%   MRR 0.981  unanswerable 0%
wild     recall@1 42.9%  recall@3 71.4%  MRR 0.571  unanswerable 50%
```

Δ vs lexical: curated recall@1 **+3.8 pp**, wild recall@1 **+0.0 pp**,
unanswerable accuracy **−85.7 pp**.

### Embedding

Not yet run. Run locally with:

```bash
pip install sentence-transformers
python3 scripts/run_embedding_eval.py --compare-lexical
```

## Findings

### 1. TF-IDF does not close the wild gap

The lexical scorer was already strong enough on the easy (curated)
cases (92.3%) — TF-IDF nudges that to 96.2% but **the wild number
doesn't move at all (42.9%)**. The same 4 skills miss top-1 under both
scorers:

| ID | Intent | Expected | Why both miss |
|----|--------|----------|---------------|
| w04 | 想自動化 deploy 流程 每次 push 就跑測試 | github-actions | description vocabulary doesn't overlap; CJK tokens have no IDF discriminator |
| w08 | containzr keep crashing 怎麼 debug | k8s-fundamentals | typo (`containzr`) makes the only signal token invisible |
| w09 | claude 一直忘記我之前說的 怎麼讓他記住 | context-engineering | "claude" tag dominates and routes to claude-code-customization |
| w12 | 怎麼讓 agent 一邊講話一邊呼叫 function | tool-design-for-agents | "agent" + "function call" not in description; routes to agent-harness-design |

Each of these is a **frontmatter** problem, not a scorer problem:
- w04 needs `keywords: [自動化部署, push 觸發]` on github-actions
- w08 needs k8s-fundamentals to mention "container crash" in keywords
- w09 needs context-engineering to claim "claude 忘記" / "remember"
- w12 needs tool-design-for-agents keywords for "function call"

### 2. TF-IDF breaks unanswerable detection

Unanswerable accuracy crashes from 100% → 14.3%. The reason is
structural: TF-IDF cosine is non-zero whenever documents share any
common English token (`help`, `how`, `do`). At any reasonable
threshold, "Help me cook a beef wellington" gets a 0.26 cosine to
skill-authoring (which contains "help"). The lexical scorer's
zero-default behavior — score is 0 unless a tag/keyword/word actually
matches — is exactly what the unanswerable filter relies on.

This is a known weakness of pure TF-IDF for retrieval. The fix in
production systems is a re-ranking layer or an absolute-similarity
threshold relative to the corpus mean — too much for this experiment.

### 3. Embedding ceiling

The embedding script is the eventual answer to "could a smarter scorer
fix the wild cases". Until it runs, we have a hypothesis:

- **If embedding wild recall@1 jumps to 70%+** → semantic paraphrasing
  is the gap. Recommend wiring a hybrid scorer (lexical floor +
  embedding tie-breaker) into the runner.
- **If embedding wild recall@1 stays ≤ 55%** → frontmatter is the gap.
  The 4 failing wild cases above are the action items; we should
  backfill keywords on those skills, not rebuild the scorer.

The TF-IDF data already weakly favors hypothesis #2. The case studies
above (w04, w08, w09, w12) all describe vocabulary mismatches that
embeddings can sometimes bridge — but `containzr` is still a typo that
no tokenizer fixes.

## Recommendation (pending embedding run)

Don't replace the lexical scorer yet. Instead:

1. **Run `scripts/run_embedding_eval.py` locally to get the actual
   embedding number.** This is the missing data point.
2. **Backfill keywords on the four failing wild skills.** Even if
   embeddings help, explicit keywords are cheaper and more
   inspectable than relying on a model.
3. **Keep the lexical scorer as the CI eval.** Its zero-default
   behavior is what makes the unanswerable check work; embeddings
   are an offline diagnostic.

## How to reproduce

```bash
# Lexical baseline (current default)
python3 scripts/run_routing_eval.py

# TF-IDF (this PR)
python3 scripts/run_tfidf_eval.py --compare-lexical

# Embeddings (this PR; needs network)
pip install sentence-transformers
python3 scripts/run_embedding_eval.py --compare-lexical
```
