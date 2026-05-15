---
name: tw-stock-chip
description: >
  Chip-flow ("chip") analysis for Taiwan-listed stocks — tracking the three
  major institutions (foreign, investment trust, dealer), margin trading
  (financing/short-selling), TDCC shareholder concentration, and "main
  force" broker activity. Helps retail investors read the supply-side of
  a stock to time entries and exits.
category: finance
tags: [stock, taiwan, tw-stock, chip-analysis, institutional-investors, margin-trading]
keywords: [TDCC, foreign investor, investment trust, dealer, margin, short interest]
related: [tw-stock-fundamental, tw-stock-technical, tw-stock-quant, tw-stock-data, tw-stock-trend]
---

# Taiwan Stock Chip-Flow Analysis

> Chip flow answers "who's holding this stock, and are they buying or selling?" Fundamentals decide *whether* to buy; chip flow decides *when*.

## When to Use This Skill

- A stock has cleared fundamentals and you need entry timing
- Saw a sharp move (up or down) and want to know who drove it
- Deciding whether to keep or trim an existing position
- Looking for stocks where a "main force" is quietly accumulating
- Avoiding stocks where retail crowds are over-extended

---

## 1. Three Lenses on Chip Flow

| Dimension | What you watch | Whose behavior |
|-----------|----------------|----------------|
| **Institutional flow** | Foreign / investment-trust / dealer net buy-sell | Large institutions |
| **Margin flow** | Margin (financing) and short balance | Retail (margin), hedgers / shorts (short balance) |
| **Big-holder flow** | TDCC shareholder concentration, % held by 1000-lot holders | True long-term holders |

**Core logic:** chips concentrating in "strong hands" (institutions, big holders) = bullish; concentrating in "weak hands" (retail margin) = bearish warning.

---

## 2. Reading the Three Major Institutions

### Their characteristics

| Institution | Capital nature | Style | What to watch |
|-------------|----------------|-------|---------------|
| **Foreign** | International, large | Mid-to-long term, follows fundamentals, FX, global flows | Consecutive buy/sell days, % of turnover |
| **Investment Trust** | Domestic mutual funds, quarter-end performance pressure | Short-to-mid term, concentrate fire on a few names | Consecutive buys, "investment-trust adopted" lists |
| **Dealer** | Brokers' proprietary capital | Short term, hedging-driven, often tied to warrants/options | Proprietary vs hedging — must distinguish |

### Two sub-categories of "Dealer"

TWSE reports dealer net buy-sell in two columns with very different meanings:

- **Dealer (proprietary)** ← real directional view
- **Dealer (hedging)** ← delta hedge for warrants/options, no directional signal

**Always read the "proprietary" line, ignore the hedging line.**

### Signal interpretation

| Signal | Meaning |
|--------|---------|
| **All three buying** | Strong bullish, but check for short-term overheating |
| **Foreign buying for 5+ consecutive days** | Mid-to-long term turn |
| **Investment trust 3 consecutive buys** | Entering "adoption" period, often lasts weeks |
| **Foreign sell + trust buy** | Mixed view between domestic and overseas |
| **Institution buy + margin also rising** | Retail piling in too — chips messy, expect a pullback |
| **Institution sell but price holds** | Someone is quietly catching it (big holder or main force) |
| **Quarter-end window dressing** | At end of Mar/Jun/Sep/Dec, trusts often push their holdings |

### Estimating institutional cost

The average price during a buying streak is a rough institutional cost basis. When price breaks that cost:
- Foreign cost: usually a mid-term support
- Trust cost: usually a short-term stop
- Break + continued institutional selling → potentially a downtrend

**Note:** rough heuristic, not exact — use as a support-zone reference.

---

## 3. Margin Trading

### Concepts

| Term | Meaning | What it implies |
|------|---------|-----------------|
| **Margin** | Borrowed money to buy (long) | Often retail; balance is a sentiment gauge |
| **Short** | Borrowed shares to sell (short) | Less retail; mostly hedging or pro shorts |
| **Short-to-margin ratio** | Short balance / margin balance | Higher = bears more aggressive |
| **Same-day round-trip** | Buy-sell intraday with no settlement | Speculation gauge |

### Bullish signals

| Signal | Reading |
|--------|---------|
| **Price up, margin down** | Weak hands washed out — healthy advance |
| **Price up, short balance up** | Short squeeze setup, strong short-term momentum |
| **Margin maintenance ratio rising** | Retail profits accumulating |
| **Short-to-margin ratio > 30%** | Squeeze conditions ripe |

### Bearish warnings

| Signal | Reading |
|--------|---------|
| **Price up, margin also surging** | Retail chasing — chips messy, pullback risk |
| **Price down, margin not falling** | Trapped retail not capitulating — unhealthy |
| **Margin maintenance ratio < 130%** | Near forced-liquidation, expect cascading sells |
| **Price down, short balance plunging (squeeze ending)** | Short-term rebound momentum gone |

### Margin call cascade

When the index or stock drops fast:
1. Maintenance ratio drops below 130% → margin firm issues a **margin call**
2. Retail doesn't post within 2 days → **forced liquidation**
3. Forced sells push price lower → triggers more liquidations

**Stocks with margin balance > 20% of share count are vulnerable to cascades on a downturn.**

---

## 4. TDCC Shareholder Concentration

### Where to find it

MOPS → "TDCC Shareholder Concentration" (updated weekly, lagged one week).

### What to look at

By holding-size tier:

| Tier | Usually who | Why it matters |
|------|-------------|----------------|
| **≤ 400 lots** | Retail | Rising % = retail piling in, chips messy |
| **400–1,000 lots** | Mid-large traders | Transitional; informational |
| **≥ 1,000 lots ("1000-lot holders")** | Institutions, founders, long-term capital | **Rising % = chips concentrating, bullish** |

### Concentration metric

**Core indicator: change in % held by 1000-lot holders**

- ✅ 1000-lot % rising for several weeks, retail % falling → chips concentrating in big hands; bullish
- ❌ 1000-lot % falling for several weeks, retail % rising → big holders unloading to retail; warning

**Examples:**
- 1000-lot % goes from 65% to 70% → big holders accumulating
- 1000-lot % goes from 70% to 60% → big holders distributing

### Caveats

- TDCC data is **lagged a week** — read it as structural, not a real-time signal
- ETF holdings count toward big holders; ETF rebalances cause big-holder % swings — adjust for them
- Employee and director holdings also count; cross-check with the insider-holdings filing

---

## 5. Main-Force Activity and Branch Flows

### Broker branches

Each brokerage's branch is one "branch". Branch flow can suggest:

- **Single branch heavy buy** → big trader or main force at that branch entering
- **Multiple branches in sync** → likely the same money operating through several branches
- **Known "main-force branches"** → some branches historically tied to well-known operators

### Patterns

| Pattern | Meaning |
|---------|---------|
| **Accumulation** | Sideways price, lower volume, main-force branch buying in small chunks |
| **Markup** | Main-force branch buys big, volume + price rise |
| **Distribution** | Price chops near highs, main-force branch quietly sells, retail picks up |
| **Dumping** | Main-force sells heavily, sharp drop, retail margin trapped |

### Limits and traps

- Branch data is public — main forces fragment orders across multiple branches to avoid detection
- "Main force" is a subjective definition; sites compute it differently
- **Don't rely on branch tracking exclusively.** It's a supplementary tool, not a holy grail.

---

## 6. Chip Conditions for Entry (Composite Read)

Ideal chip-flow setup before buying:

### Institutional
- [ ] Foreign net buyer (or flat) over the last 5 days
- [ ] No heavy investment-trust selling recently
- [ ] Dealer (proprietary) net buyer

### Margin
- [ ] Margin balance < 15% of share count
- [ ] On recent up-days, margin didn't surge (no retail chase)
- [ ] Margin maintenance stable above 150%

### Big-holder
- [ ] 1000-lot % rising over the last 4 weeks
- [ ] Retail (≤ 400 lots) % falling over the last 4 weeks
- [ ] Insider holdings stable, no large reductions

Hit at least 2 of 3 dimensions, no violation in the third — chips are healthy.

---

## 7. Common Traps

### 1. Institutional buy ≠ guaranteed up

Institutions hedge, rebalance, and prune. A 1–2 day buy may be just rebalancing.
**Look at 5-day trends**, not single days.

### 2. Hedge-driven misreads

When foreign investors short via securities lending, they may go long on cash to hedge — creating a misleading "foreign buying" signal.
When **securities-lending short balance jumps**, suspect the foreign buy is hedging rather than directional.

### 3. Trust quarter-end window dressing

Before quarter-ends, trusts push the prices of their key holdings to inflate NAV.
Pullback often follows the close — **chasing late-quarter rallies often means buying the top**.

### 4. ETF-rebalance noise

When an ETF (0050, 0056, etc.) adjusts constituents, newly added stocks see heavy passive institutional buying — that's mechanical, not a fundamentals view.
**Check whether the stock was recently added to / removed from an ETF.**

### 5. Branch (short-term) vs TDCC (structural)

Branch flow is a short-term signal (days to weeks). TDCC concentration is structural (weeks to months).
**Don't mix horizons.**

### 6. Short cover ≠ squeeze

A real squeeze needs: high short-to-margin ratio + rising short balance + price strengthening.
"Short balance just dropped" alone may be profit-taking, not a squeeze.

---

## 8. Personal Workflow

### Step 1: Start with a fundamentals shortlist
Chip-flow is a timing tool, not a screen. Use fundamentals to find names worth owning, chip-flow to time entry.
(See [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md).)

### Step 2: Keep a chip-flow journal
For each shortlisted name, log weekly:
- 5-day / 20-day institutional net buy-sell
- Weekly margin balance change
- 1000-lot holder % change
- Special events (ex-div, ETF rebalance, earnings)

### Step 3: Wait for the chip signal
Wait until "chips concentrating + retail leaving + institutions turning buyer" partially aligns.
**If it doesn't align, keep waiting.** Chip-flow analysis has no "must act now" pressure.

### Step 4: Scale in
Even with a clear chip signal, scale in over 2–3 tranches to spread the entry.
Single all-in is the biggest killer when the chip read is wrong.

### Step 5: Monitor continuously
After entry, keep watching the chip structure. When:
- 1000-lot % starts falling
- Institutions sell consistently
- Margin balance abnormally surges

→ go to caution; decide reduce or exit by your fundamental thesis.

---

## 9. Weekly Observation Checklist

Per shortlisted stock:

- [ ] Foreign 5-day / 20-day net flow
- [ ] Investment trust adoption activity
- [ ] Dealer (proprietary, not hedging) direction
- [ ] Securities-lending short balance — abnormal increase?
- [ ] Margin balance week-over-week (% of share count)
- [ ] Short balance and short-to-margin ratio
- [ ] Margin maintenance (per stock and overall)
- [ ] 1000-lot holder % over the last 4 weeks
- [ ] Retail (≤ 400 lots) % over the last 4 weeks
- [ ] Anomalous main-force branch activity
- [ ] ETF-rebalance or other technical effect to discount

---

## 10. Combining Fundamentals and Chip Flow

| Fundamentals | Chip flow | Verdict |
|--------------|-----------|---------|
| Good | Good | **Core holding** — can add |
| Good | Bad | **Watch and wait** — let chips wash |
| Bad | Good | **Short-term theme** — small position with stop |
| Bad | Bad | **Avoid entirely** |

Chip-flow only = short-term trading. Fundamentals only = risks buying late in the cycle. **Both is a complete decision.**

---

## Related Skills

- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — fundamentals as the screen ahead of chip-flow timing
- [`tw-stock-technical`](../tw-stock-technical/SKILL.md) — technical patterns alongside chip flow
- [`tw-stock-quant`](../tw-stock-quant/SKILL.md) — chip factors in a backtest
- [`tw-stock-data`](../tw-stock-data/SKILL.md) — sourcing chip-flow data
