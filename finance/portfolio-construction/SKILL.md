---
name: portfolio-construction
description: >
  Portfolio construction guide — asset allocation, diversification,
  rebalancing, personal risk-tolerance assessment, the core-satellite
  strategy, a simplified Kelly criterion, and performance tracking. For
  retail investors graduating from single-stock picking to systematic
  portfolio management.
category: finance
tags: [portfolio, asset-allocation, risk-management, diversification, investing]
related: [tw-stock-fundamental, tw-etf-investing, tw-stock-options, tw-stock-tax, tw-stock-trend]
---

# Portfolio Construction

> ~90% of a portfolio's return is determined by asset allocation, not stock picking. Decide "how much in stocks vs cash" first; pick names later.

## When to Use This Skill

- You hold several stocks and ETFs but have no overall allocation
- Want to graduate from "buy one at a time" to "manage the portfolio"
- Want to set sane allocation ratios for your risk tolerance
- Want to know when to rebalance
- Want to track and improve portfolio performance

---

## 1. Self-Assessing Risk Tolerance

Before allocating, answer these:

| Question | Conservative | Moderate | Aggressive |
|----------|--------------|----------|------------|
| Investment horizon | < 3 yrs | 3–10 yrs | > 10 yrs |
| Age | > 55 | 35–55 | < 35 |
| Income stability | Unstable | Stable | Stable + growing |
| Max acceptable drawdown | -10% | -20% | -30%+ |
| Reaction at -20% | Sell everything | Uncomfortable but hold | Buy more |

### Suggested allocation

| Type | Equity (incl. ETF) | Bonds / Fixed deposit | Cash |
|------|--------------------|------------------------|------|
| **Conservative** | 30–40% | 40–50% | 10–20% |
| **Moderate** | 50–70% | 20–30% | 10–20% |
| **Aggressive** | 70–90% | 0–20% | 10% |

1. **Be honest.** Overestimating your risk tolerance = panic-selling at the bottom (the worst time).
2. **There is no "correct" allocation — only what fits you.** A portfolio you can hold through a downturn is the only good portfolio.

---

## 2. Allocation Framework

### Core-satellite (recommended)

```
Core (60–80%)
├── Broad-market ETF (e.g. 0050 / 006208 in TW; VOO / VTI globally)
├── Dividend ETF (optional)
└── Stable assets (fixed deposit, bond ETFs)

Satellite (20–40%)
├── Individual stocks (5–8 names, fundamentals-screened)
├── Thematic ETFs (semiconductors, ESG, etc.)
└── Options strategies (optional, small allocation)
```

3. **Core: dollar-cost average, don't time.** Satellite can be actively managed.
4. **Core's job is "don't lose"; satellite's job is "outperformance".**

---

## 3. Diversification Principles

### Dimensions of diversification

| Dimension | How |
|-----------|-----|
| **Number of names** | 5–15 holdings (too few = concentration risk; too many = unmanageable) |
| **Industry** | No single industry above ~40% (cap tech at 50%) |
| **Market cap** | Mostly large cap, with some mid/small |
| **Style** | Mix growth + value + dividend |
| **Asset class** | Equity + cash + bonds (per risk tolerance) |
| **Geography (optional)** | TW + US ETFs to spread regional risk |

5. **No single name above 15% of total capital.** No matter how confident.
6. **No single industry above 30–40%.**
7. **Combine low-correlation assets.** TSMC + MediaTek isn't diversification (highly correlated). TSMC + Chunghwa Telecom is.

---

## 4. Position Sizing

### Equal weight (simplest)

Same dollar amount per name. Ten names → 10% each.

### Confidence-weighted

Weight by your conviction:

| Conviction | Weight |
|------------|--------|
| High (fundamentals + chip-flow + technical aligned) | 10–15% |
| Medium (two of three aligned) | 5–10% |
| Low (single signal, or watchlist) | 2–5% |

### Simplified Kelly Criterion

```
Optimal position % = win_rate − (1 − win_rate) / win_loss_ratio
```

Example: 60% win rate, average win/loss ratio 2:1
→ 0.6 − 0.4 / 2 = 0.4 = 40%

**In practice, use 1/4 to 1/2 Kelly.** Full Kelly has too much volatility.

8. **Build new positions in tranches starting at 1/3 of the target.** Add the rest after the thesis confirms.

---

## 5. Rebalancing

### When

| Trigger | Action |
|---------|--------|
| **Calendar:** quarterly or semi-annually | Check whether allocations have drifted from target |
| **Drift:** any asset class > 5% off target | Sell the over-allocated, buy the under-allocated |
| **Event:** after a sharp move | Mechanically adjust back to target |

### How

```
Target: 0050 60%, individual stocks 30%, cash 10%
Actual: 0050 72%, individual stocks 22%, cash  6%

→ Sell some 0050 (72%→60%), add to stocks (22%→30%), refill cash (6%→10%)
```

9. **Rebalancing mechanizes "sell high, buy low".** It naturally trims winners and tops up laggards.
10. **Don't over-rebalance.** Each adjustment has cost. 2–4 times per year is enough.

---

## 6. Performance Tracking

### Core metrics

| Metric | How to compute | Good benchmark |
|--------|----------------|----------------|
| **Annualized return** | Total return (incl. dividends) / years | > broad-market index (0050) |
| **Max drawdown (MDD)** | Peak-to-trough loss | < 25% (moderate type) |
| **Sharpe ratio** | (return − risk-free rate) / volatility | > 0.5 |

### How to track

11. **Log total portfolio value monthly.** One line in Excel or Google Sheets.
12. **Compare against a benchmark.** Your stock-picked portfolio vs. dollar-cost averaging into 0050. If you trail 0050 long-term, raise the ETF allocation.
13. **Full review once a year.** Which positions contributed, which dragged.

---

## 7. Construction Steps

### Step 1: Decide risk tolerance
→ Set the high-level equity / cash / bond split.

### Step 2: Decide core / satellite split
→ Usually 70/30 or 60/40.

### Step 3: Pick core
→ 1–2 broad-market ETFs, dollar-cost average.

### Step 4: Pick satellites
→ 5–8 names (fundamentals filter + chip-flow timing).

### Step 5: Decide position sizes
→ Equal weight or confidence-weighted.

### Step 6: Set rebalancing rule
→ Quarterly + drift trigger > 5%.

### Step 7: Execute and log
→ Monthly log; annual review.

---

## Common Traps

| Trap | Counter |
|------|---------|
| **No allocation, just a pile of stocks** | Decide the high-level split first, names second |
| **Concentrated in one sector** | Cap industry at 30–40% |
| **Never rebalance** | Use calendar + drift triggers |
| **Tweak every week** | Quarterly is enough; over-tweaking = high cost |
| **No performance tracking** | One line per month; compare to benchmark yearly |
| **Overestimating risk tolerance** | Stress-test with a real downturn (how did 2022's 20% drop feel?) |

---

## Pre-Flight Checklist

- [ ] Risk tolerance self-assessed
- [ ] High-level equity / cash / bond split decided
- [ ] Core occupies 60–80% (ETF, dollar-cost average)
- [ ] Satellite occupies 20–40% (stocks / thematic ETFs)
- [ ] Single name ≤ 15%, single industry ≤ 40%
- [ ] Rebalancing rule set (frequency + drift threshold)
- [ ] Performance tracking sheet in place
- [ ] At least one full annual portfolio review

---

## Related Skills

- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — pick satellite names
- [`tw-etf-investing`](../tw-etf-investing/SKILL.md) — choose core ETFs
- [`tw-stock-options`](../tw-stock-options/SKILL.md) — options as satellite strategy
- [`rules/trading-discipline`](../../rules/trading-discipline.md) — trading discipline rules
