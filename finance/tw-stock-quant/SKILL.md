---
name: tw-stock-quant
description: >
  Quantitative investing for Taiwan-listed stocks — backtest framework
  design, classic factor models (value, momentum, quality, low volatility),
  strategy development workflow, performance metrics, overfitting and
  survivorship bias, and post-go-live discipline. Concept-first; pseudo-code
  examples are language-agnostic (Python / Go / R).
category: finance
tags: [stock, taiwan, tw-stock, quantitative, backtesting, factor-investing, strategy]
keywords: [backtest, factor model, Sharpe, Sortino, Calmar, survivorship bias, look-ahead bias]
related: [tw-stock-fundamental, tw-stock-chip, tw-stock-technical, tw-stock-data, tw-stock-trend]
---

# Taiwan Stock Quantitative Strategy

> Quant isn't really about coding. It's about turning "my investment logic" into rules that are testable, repeatable, and improvable. The code is just the executor.

## When to Use This Skill

- Want to systematize and automate manual stock-picking rules
- Want to backtest whether an investment idea worked historically
- Want a factor model that screens monthly
- Want to compare strategies' risk/return characteristics
- Want discipline-driven execution that resists emotional override

---

## 1. Core Workflow

```
1. Hypothesis     →  "High ROE + low P/E stocks beat the index long-term"
2. Define rules   →  Pick top 20 of {ROE > 15%, P/E < 15} on day 1 of each month
3. Backtest       →  Run on 10 years of historical data
4. Evaluate       →  CAGR, max drawdown, Sharpe
5. Stress test    →  Sub-periods, parameter shifts, transaction costs
6. Paper trade    →  3–6 months on real data without real money
7. Go live        →  Real money, strict rule execution
8. Periodic review→  Has the strategy stopped working? Has the market changed?
```

**No step is optional.** The most common failure is jumping from step 4 to step 7.

---

## 2. Backtest Framework

### Architecture

```
┌──────────────────────────────────────┐
│            Backtest Engine            │
│                                      │
│  History → Signals → Sim trade → Stats│
│                                      │
│  ┌────────┐ ┌────────┐ ┌────────────┐│
│  │ Data   │ │ Strategy│ │ Risk mgmt ││
│  └────────┘ └────────┘ └────────────┘│
└──────────────────────────────────────┘
```

### Key components

| Component | Responsibility | Watch out |
|-----------|----------------|-----------|
| **Data** | Provide OHLCV, financials, chip flow | Use adjusted price (dividend-adjusted) |
| **Signal** | Generate buy/sell/hold per the rules | Don't peek at the future (see below) |
| **Simulator** | Simulate orders, fills, fees, taxes | TW fees: 0.1425% commission + 0.3% securities transaction tax (0.15% for day-trade) |
| **Risk** | Stops, take-profit, position caps | Strategy-level risk control |
| **Stats** | Compute return, drawdown, risk metrics | Compare against benchmark (0050) |

### Taiwan-market specifics

1. **Dividend-adjusted price.** Ex-dividend creates price gaps; un-adjusted price drastically overstates returns. Use back-adjusted close.
2. **Daily price limit.** TW has a ±10% daily limit. Backtest must simulate "couldn't buy at limit-up / couldn't sell at limit-down".
3. **Liquidity.** Small caps may average tens of lots/day. Don't simulate orders larger than X% of daily volume (recommend < 10%).
4. **Survivorship bias.** Backtesting only currently listed stocks excludes the ones that delisted = inflated performance. Use a full history including delisted names.
5. **Earnings release lag.** Q1 reports are released by May 15; using Q1 data in April = look-ahead. Use point-in-time data.

---

## 3. Common Factor Models

### What is a factor?

A factor = a stock characteristic, validated by academia or practice, that explains return differences.

### Five classic factors

| Factor | Definition | Logic | TW applicability |
|--------|------------|-------|-------------------|
| **Value** | Low P/E, low P/B, high yield | Cheap stocks beat expensive ones long-term | High — TW dividend factors work well |
| **Momentum** | Top performers over the past 3–12 months | Rising keeps rising (trend continuation) | High; pair with stops |
| **Quality** | High ROE, low debt, stable earnings | Good companies beat bad ones long-term | High |
| **Low volatility** | Lowest daily-return volatility over 1 year | Low-vol earns better risk-adjusted returns | Mid-high |
| **Size** | Small market cap | Small caps have historically outperformed | Caution: TW small caps lack liquidity |

### Multi-factor composite

Single factors can underperform for stretches. Combining factors:
- Diversifies single-factor risk
- Different factors complement each other in different regimes
- Stabilizes selection

**In practice:** rank each stock by each factor (percentile), weighted-average, take the top N.

```
Score = 0.3 × Value + 0.3 × Quality + 0.2 × Momentum + 0.2 × Low-vol
```

### Strategy examples

#### Dividend strategy

```
Filter:
  1. Listed ≥ 5 years
  2. Dividends paid 5 years in a row
  3. ROE > 10%
  4. Debt ratio < 60%
  5. FCF positive

Rank by: 0.5 × yield + 0.3 × ROE + 0.2 × revenue YoY

Hold:    top 20
Rebalance: once a year, post ex-dividend
```

#### Momentum strategy

```
Filter:
  1. Price above MA240
  2. 20-day average volume > 500 lots/day
  3. 12-month return > 0

Rank by: 0.6 × 6-month return + 0.4 × 1-month return

Hold:        top 15
Rebalance:   monthly (1st)
Stop-loss:   -10% from entry per name
```

#### Value + Quality blend

```
Filter:
  1. P/E < industry average
  2. P/B < 2
  3. ROE > 15%
  4. OCF > Net income
  5. EPS growth 3 years in a row

Rank by: PEG ascending

Hold:       top 15
Rebalance:  after each quarter's earnings
```

---

## 4. Performance Metrics

### Return metrics

| Metric | Meaning | Good benchmark |
|--------|---------|----------------|
| **CAGR** | Compounded annual growth rate | TW market long-term ~8–10%; strategy should beat market |
| **Cumulative return** | Total return over the backtest | Watch absolute growth |
| **Alpha** | Strategy return − benchmark | > 0 to be worth running |

### Risk metrics

| Metric | Meaning | Good benchmark |
|--------|---------|----------------|
| **Max drawdown (MDD)** | Largest peak-to-trough drop | < 25% good; > 40% dangerous |
| **Volatility** | Std dev of daily/monthly returns | Lower = steadier |
| **Downside risk** | Volatility of negative returns only | Reflects pain better than total volatility |

### Risk-adjusted return

| Metric | Formula | Good benchmark |
|--------|---------|----------------|
| **Sharpe** | (return − risk-free) / volatility | > 1 good, > 1.5 excellent, > 2 elite |
| **Sortino** | (return − risk-free) / downside risk | A truer quality reading than Sharpe |
| **Calmar** | CAGR / MDD | > 0.5 acceptable, > 1 excellent |

### Practical metrics

| Metric | Meaning |
|--------|---------|
| **Win rate** | Winning trades / total. > 50% is good — but low win rate + high payoff ratio also wins |
| **Win/loss ratio** | Avg win / avg loss. > 2 is good |
| **Trade count** | Too few isn't statistically meaningful (target > 100) |
| **Turnover** | Annual traded value / avg position. Higher = more friction cost |

---

## 5. Overfitting — the Quant's Worst Enemy

### What it is

Strategy looks perfect in backtest, dies in production.
**Why:** the strategy learned historical noise, not pattern.

### Warning signs

| Sign | Note |
|------|------|
| Backtest > 30% CAGR with almost no drawdown | Too good, probably wrong |
| Hyper-precise parameters (MA17, RSI(13.5)) | Why 17 and not 15 or 20? |
| Performance collapses with small parameter shifts | Brittle = overfit |
| Only works in a specific time window | Lucky alignment |
| Many conditions (> 5 filters + 3 indicators) | Each condition adds an overfitting dimension |

### Defenses

6. **Out-of-sample testing.** Develop on the first 70% of data, validate on the last 30%. If validation drops sharply → overfit.
7. **Walk-forward.** Rolling backtest: train on past N years, validate next year, roll forward.
8. **Parameter robustness.** Vary key parameters within a sane range (MA20 → MA15..MA25); performance shouldn't shift dramatically.
9. **Simple beats complex.** Fewer conditions, fewer parameters, more intuitive logic = less overfitting risk.
10. **Economic logic.** A strategy needs a reasonable economic story. "Low P/E beats long-term" has a story (value premium); "buy stock #38 on day 17" doesn't.

---

## 6. Strategy Development Workflow

### Step 1: Hypothesis

Write one sentence: "I think ____ stocks will ____ because ____."

For example:
- "High-ROE + low-P/E stocks beat the index because the market underprices quality."
- "Stocks with 3 consecutive monthly revenue highs rise short-term because of the momentum effect."

**If you can't fill in "because", the hypothesis isn't worth backtesting.**

### Step 2: Pseudo-code rules

```
On the first trading day of each month:

1. Get all listed and OTC stocks
2. Exclude: listed < 1 year; 20-day avg volume < 200 lots; financials
3. Filter:  ROE > 15%; P/E < industry average; revenue YoY > 0 for 3 months
4. Rank:    PEG ascending
5. Take top 15
6. Equal weight (1/15 each)
7. Compare to last month's holdings; rotate
8. Per-name stop: -15% from entry
```

### Step 3: Backtest

- Period ≥ 5 years (covering at least one bull/bear cycle)
- Include transaction costs: 0.1425% commission + 0.3% securities transaction tax = ~0.44% round-trip
- Benchmark: TAIEX or 0050 ETF
- Log per-year return, MDD, holdings

### Step 4: Evaluate

Compare strategy vs benchmark on:
- CAGR
- Max drawdown
- Sharpe
- Yearly win/loss

**A strategy that beats the market with 40%+ MDD will probably break the operator's nerves — not a good strategy in practice.**

### Step 5: Stress test

- Restrict the period (e.g., only the financial-crisis window, only COVID)
- Vary parameters (MA20 → MA15/MA25; 10/20 holdings)
- Inflate costs (assume 0.1% slippage)
- Tighter liquidity (exclude < 500 lots/day)

**If any stress test takes the strategy from green to red → it isn't robust.**

### Step 6: Paper trade

Run on real-time data, follow rules, don't actually order. 3–6 months. Goals:
- Validate viability in real market conditions
- Find issues backtests miss (limit-up, illiquidity)
- Build execution discipline

### Step 7: Go live

- Start small (20–30% of total capital)
- Strict rule following — no human override
- Log every trade, including any deviation from the rule
- Review monthly / quarterly

### Step 8: Periodic review

Strategies can fail when market structure changes. Ask:
- Is the last 6 months' performance materially off from backtest?
- Does the factor logic still hold? (Value can underperform during tech bubbles, for instance.)
- Is this a regime change or just a low patch?

**A strategy that trails the market for 1 year + with broken economic logic → consider pause or revision.**

---

## 7. Practical Constraints in Taiwan

| Constraint | Impact | Counter |
|------------|--------|---------|
| Small caps illiquid | Backtest looks great, you can't actually buy | Exclude < 500 lots/day average |
| Daily price limit | Model says buy; market is at limit-up | Simulate limit-up / limit-down |
| Ex-dividend price moves | Un-adjusted price = distorted return | Use adjusted close |
| Earnings release lag | Need point-in-time data to avoid look-ahead | Strictly use data on its release date |
| No share borrow | Shorting is hard in TW | Focus on long-only |
| Fees + taxes | ~0.44% per round-trip; high turnover bleeds | Lower turnover |

---

## 8. Common Traps

| Trap | Note | Counter |
|------|------|---------|
| **Survivorship bias** | Only currently-listed stocks | Use full history with delisted |
| **Look-ahead bias** | Using data not yet released at the time | Strict point-in-time data |
| **Data mining bias** | Test 100 strategies, pick the best | Hypothesize first, then test |
| **Ignoring fees** | Backtest without commission/tax | Always include |
| **Ignoring slippage** | Filling at close is idealized | Add 0.05–0.1% slippage assumption |
| **Over-optimization** | Tune to perfection | Robustness check |
| **Sample too small** | Backtest with 30 trades | At least 100 for statistical significance |

---

## 9. Pre-Live Checklist

For each strategy before live deployment:

- [ ] Has clear economic logic (the "because" exists)
- [ ] Backtest period ≥ 5 years, covers bull and bear
- [ ] Uses adjusted prices
- [ ] Uses point-in-time data (no look-ahead)
- [ ] Includes delisted stocks (no survivorship bias)
- [ ] Costs included (commission + STT + slippage)
- [ ] Simulates limit-up / limit-down and liquidity
- [ ] Out-of-sample or walk-forward validation passes
- [ ] Performance survives ±20% parameter shifts
- [ ] Sharpe > 0.5 after costs
- [ ] Max drawdown within tolerable range
- [ ] ≥ 3 months of paper trading completed
- [ ] Clear "stop / revise" criteria defined

---

## Related Skills

- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — fundamentals as factor source (ROE, P/E, yield)
- [`tw-stock-chip`](../tw-stock-chip/SKILL.md) — chip factors
- [`tw-stock-technical`](../tw-stock-technical/SKILL.md) — momentum / technical factors
- [`tw-stock-data`](../tw-stock-data/SKILL.md) — data engineering for backtests
- [`rules/trading-discipline`](../../rules/trading-discipline.md) — execution discipline
