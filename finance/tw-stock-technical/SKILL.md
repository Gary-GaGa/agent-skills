---
name: tw-stock-technical
description: >
  Technical analysis for Taiwan-listed stocks — candlestick patterns, moving
  averages, MACD, RSI, KD, Bollinger Bands, volume-price relationships,
  support / resistance, and a multi-indicator confluence framework. Concept-
  focused; pairs best with fundamental and chip-flow analysis.
category: finance
tags: [stock, taiwan, tw-stock, technical-analysis, charting, indicators]
keywords: [MACD, RSI, KD, Bollinger Bands, moving average, support, resistance, candlestick]
related: [tw-stock-fundamental, tw-stock-chip, tw-stock-quant, tw-stock-data, tw-stock-options]
---

# Taiwan Stock Technical Analysis

> Technical analysis answers "what is the current price action implying?" It doesn't tell you whether the company is good (fundamentals), nor who is buying (chip flow); it tells you "where the market consensus is moving".

## When to Use This Skill

- You have a fundamentals + chip-flow shortlist and need actual entry/exit prices
- Reading the tape and judging short-term (1–2 week) trend direction
- Setting technical-level stops and targets
- Reading TAIEX overall regime
- Avoiding entering against weak technicals

---

## 1. Candlestick Basics

### Single candles

| Pattern | Visual | Meaning |
|---------|--------|---------|
| **Long red (long bull)** | Long body, short wicks | Bulls dominate (in TW: red = up) |
| **Long black (long bear)** | Long body, short wicks | Bears dominate (in TW: black = down) |
| **Doji** | Tiny body, equal upper/lower wicks | Indecision; reversal hint |
| **Long upper wick** | Upper wick > 2x body | Selling pressure above (shooting star) |
| **Long lower wick** | Lower wick > 2x body | Buying pressure below (hammer) |

**TW convention:** Taiwan candles are red-up / black-down (opposite of US convention). Calibrate when reading TA books.

### Common combinations

| Pattern | Where | Meaning |
|---------|-------|---------|
| **Morning Star** | Bottom | Down → doji → up; bottom-reversal signal |
| **Evening Star** | Top | Up → doji → down; top-reversal signal |
| **Engulfing** | Top / Bottom | Second bar fully engulfs the first; strong reversal |
| **Three white soldiers** | Bottom | Three rising bull candles; bullish setup |
| **Three black crows** | Top | Three falling bear candles; bearish move |
| **Island reversal** | Top / Bottom | Gap up then gap down (or reverse); strong reversal |

### Usage rules

1. **Don't decide on a single candle.** It's a clue, not a conclusion.
2. **Pair with location and volume.** A doji mid-trend is not the same as a doji at a key support.
3. **Daily for short term, weekly for medium term, monthly for long term.** Signals across timeframes can conflict — defer to the longer frame.

---

## 2. Moving Averages

### Common MAs

| MA | Tag | Type | Represents |
|----|-----|------|------------|
| 5-day | MA5 | Short | Weekly average — ultra-short trading line |
| 10-day | MA10 | Short | Two-week average |
| 20-day | MA20 | Short-mid | Monthly line — most-watched by retail |
| 60-day | MA60 | Mid | Quarterly line — institutional cost line |
| 120-day | MA120 | Mid-long | Half-year line |
| 240-day | MA240 | Long | Annual line — long-term bull/bear divider |

### MA stacking

| Stack | Pattern | Meaning |
|-------|---------|---------|
| **Bullish stack** | MA5 > MA20 > MA60 > MA120 > MA240 | Strong uptrend |
| **Bearish stack** | MA5 < MA20 < MA60 < MA120 < MA240 | Strong downtrend |
| **Tangle** | All MAs converged | Imminent breakout, direction unconfirmed |

### MA signals

| Signal | Meaning | Note |
|--------|---------|------|
| **Golden cross** | Short MA crosses up through long MA | Bull start, but volume must confirm |
| **Death cross** | Short MA crosses down through long MA | Bear start |
| **Reclaim MA20** | Close > MA20 | First step in short-term strength |
| **Lose MA60** | Close < MA60 | Mid-term weakness; institutional cost line breached |
| **Lose MA240** | Close < MA240 | Long-term bull/bear flip warning |

### Rules

4. **MAs are lagging indicators.** They confirm trend, not predict reversals.
5. **After a break, watch for "holding" vs "false break".** Three consecutive closes above/below is more reliable.
6. **In bullish stacks, look for pullback buys (test MA, hold).** In bearish stacks, look for rebound shorts.

---

## 3. Indicators

### MACD (Moving Average Convergence Divergence)

- **Components:** DIF, MACD (signal), histogram
- **Default:** 12, 26, 9

| Signal | Meaning |
|--------|---------|
| DIF crosses up MACD (golden cross) | Bull momentum strengthening |
| DIF crosses down MACD (death cross) | Bear momentum strengthening |
| Histogram flips from negative to positive | Down momentum easing; potential reversal |
| Histogram shrinks consecutively | Current trend losing strength |
| **Bearish divergence** (price new high, DIF doesn't) | Top — pullback expected |
| **Bullish divergence** (price new low, DIF doesn't) | Bottom — rebound expected |

**Key:** MACD divergence is one of the strongest reversal signals in TA.

### RSI (Relative Strength Index)

- **Range:** 0–100
- **Default:** RSI(14)

| Range | Meaning |
|-------|---------|
| RSI > 80 | Overbought; short-term pullback risk high |
| RSI < 20 | Oversold; rebound likely |
| Around RSI 50 | Bull/bear divider; follow trend direction |
| RSI divergence | Same logic as MACD divergence |

**Note:** strong stocks can stay above RSI 80 for weeks. Overbought ≠ "must drop" — it just means "risen too fast".

### KD (Stochastic)

- **Components:** K and D lines (D = smoothed K)
- **Range:** 0–100
- **Default:** 9, 3, 3

| Signal | Meaning |
|--------|---------|
| K crosses up D (golden cross) | Short-term buy |
| K crosses down D (death cross) | Short-term sell |
| KD > 80 | Overbought zone |
| KD < 20 | Oversold zone |
| Sustained low (KD < 20) | Oversold but pressure persists; don't catch a falling knife |
| Sustained high (KD > 80) | Overbought but momentum continues; don't fade the top |

**KD vs RSI:** KD is more sensitive (short-term); RSI is steadier (mid-term).

### Bollinger Bands

- **Components:** middle (MA20), upper (+2σ), lower (−2σ)
- Statistically ~95% of price action stays inside the bands.

| Pattern | Meaning |
|---------|---------|
| **Touches upper** | Short-term hot, but strong trends can ride it (not a sell) |
| **Touches lower** | Short-term cold, but weak trends can ride it (not a buy) |
| **Squeeze (narrowing)** | Volatility low; breakout pending. Direction unknown. |
| **Sudden expansion** | Trend ignition; follow the breakout direction |
| **Drops below lower then closes back inside** | False break; rebound signal |

---

## 4. Volume-Price Relationships

### Core principle

**Volume leads price.** Price moves without volume confirmation are unreliable.

| Combination | Meaning |
|-------------|---------|
| **Up + volume up** | Healthy advance, bulls confident |
| **Up + volume down** | Chase momentum fading; rally may top |
| **Down + volume up** | Panic selling, but could also be a shakeout (depends on level) |
| **Down + volume down** | Selling pressure easing; possibly approaching a bottom |
| **Massive bull candle on huge volume** | Breakout (most meaningful at the bottom of a range) |
| **Massive bear candle on huge volume** | Bull-to-bull capitulation / distribution (most dangerous at highs) |
| **Up on flat volume** | Suspicious advance; persistence questionable |

### Volume baselines

7. **"Massive volume" = volume > 2× the 20-day average.**
8. **"Low volume" = volume < 50% of the 20-day average.**
9. **Use relative volume.** TSMC's 30,000-lot daily average vs a small cap's 300-lot daily average aren't directly comparable.

---

## 5. Support and Resistance

### Support (where buyers tend to appear)

| Source | Notes |
|--------|-------|
| **Prior low** | Buyers often catch the prior low |
| **Moving averages** | MA20, MA60, MA240 are dynamic supports |
| **Upper edge of an unfilled gap** | Unfilled gaps = strong support |
| **Round numbers** | Psychological levels (NT$100, NT$500) |
| **Bottom of high-volume node** | Lower bound of a big-volume zone |

### Resistance (where sellers tend to appear)

| Source | Notes |
|--------|-------|
| **Prior high** | Sellers often take profit at the prior high |
| **Moving averages (in bearish stack)** | MAs become resistance in a downtrend |
| **Lower edge of a downward gap** | Gap-down lower edge = resistance |
| **Trapped supply zone** | Prior high-volume sideways zone — "trapped" longs sell on recovery |

### Support/resistance flip

10. **Support broken becomes resistance; resistance broken becomes support.** One of the most fundamental rules in TA.

---

## 6. Price Patterns

### Reversal patterns

| Pattern | Where | Meaning |
|---------|-------|---------|
| **Head and shoulders top** | Top | LS-Head-RS, breakdown of neckline confirms downside |
| **Inverse head and shoulders** | Bottom | Mirror; neckline breakout confirms upside |
| **Double top (M)** | Top | Two failed pushes through resistance |
| **Double bottom (W)** | Bottom | Two successful holds at support |
| **Rounded top / bottom** | Top / Bottom | Slow reversal, energy gradually shifting |

### Continuation patterns

| Pattern | Meaning |
|---------|---------|
| **Flag** | Small counter-trend consolidation; resumes prior direction on completion |
| **Triangle convergence** | Highs and lows converge; breakout direction = trend direction |
| **Box / range** | Sideways within a band; long on upside break, short on downside break |

### Pattern usage

11. **All patterns must be "confirmed" before they count.** H&S top requires neckline break; triangle requires edge break. Until then, "tentative".
12. **Volume must agree.** Reversal completion should be accompanied by volume on the breakout side.
13. **Timeframe matters.** A weekly pattern beats a daily one (a weekly W-bottom is far more reliable).

---

## 7. Multi-Indicator Confluence

**A single indicator can deceive. Multiple indicators pointing the same way is what counts.**

### Entry signal (≥ 3 of 5)

- [ ] Trend: price above MA20; MAs in bullish stack (or at least not bearish)
- [ ] Volume: recent breakout on heavy volume, or volume-price agreement
- [ ] Indicators: MACD golden cross or histogram flip; RSI > 50
- [ ] Pattern: bottom-reversal candle near a support level
- [ ] No bearish divergence on MACD or RSI

### Exit / caution signal (any 2 of 4)

- [ ] Price loses MA20 and doesn't reclaim within 3 days
- [ ] MACD death cross or bearish divergence
- [ ] Massive bearish candle on heavy volume
- [ ] Loses key support (prior low, gap, neckline)

### Cross-timeframe integration

| Larger frame (weekly) | Smaller frame (daily) | Strategy |
|-----------------------|------------------------|----------|
| Bullish | Bullish | **Aggressive long** |
| Bullish | Pullback | **Wait for pullback to end** (best buy) |
| Bearish | Rebound | **Watch or scalp the bounce** (high risk) |
| Bearish | Bearish | **Sit in cash** |

14. **The larger frame sets direction; the smaller frame sets timing.** Don't size up on a weekly bear because of a daily golden cross.

---

## 8. Common Traps

| Trap | Description | Counter |
|------|-------------|---------|
| **False breakout** | Price pokes through resistance and pulls back | Wait for close + next-day hold |
| **Indicator saturation** | KD / RSI stays in extreme zone for a long time | In strong trends saturation is normal — don't fade |
| **Single-indicator decisions** | Buying on RSI oversold or MACD golden cross alone | Wait for confluence |
| **Ignoring index regime** | A great single-stock setup can't survive an index crash | Read the index trend first |
| **Screen addiction** | Watching tick-by-tick, emotional decisions | Set entry/exit conditions, walk away |
| **Hindsight bias** | "It was so obvious here" | Decide only on what's visible at the moment |
| **Predicting instead of following** | "I think it'll reverse" | Wait for the signal |

---

## 9. Pre-Decision Checklist

Before any technical decision:

- [ ] TAIEX trend direction (above or below MA20)
- [ ] Stock's regime: up / down / range?
- [ ] MA stacking (bullish / bearish / tangled)
- [ ] Recent support and resistance levels
- [ ] Volume-price agreement (volume on rallies vs not)
- [ ] MACD direction (golden / death cross) and any divergence
- [ ] RSI / KD zone (normal / overbought / oversold)
- [ ] Bollinger width (squeeze or expanding)
- [ ] Any completed pattern (H&S top, W-bottom, etc.)
- [ ] Alignment with fundamentals and chip flow

---

## 10. Integrating with Fundamentals and Chip Flow

| Fundamentals | Chip flow | Technicals | Verdict |
|--------------|-----------|------------|---------|
| Good | Good | Good | **Best entry** |
| Good | Good | Bad | Wait for technicals to turn (reclaim support) |
| Good | Bad | Good | Technicals may be just a bounce; cautious |
| Bad | — | Good | Pure technical play, short-term mindset, hard stop |

**Three-way confluence is the highest-probability entry.** Any leg missing → smaller size or wait.

---

## Related Skills

- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — fundamentals: "is it worth owning?"
- [`tw-stock-chip`](../tw-stock-chip/SKILL.md) — chip flow: "who's buying?"
- [`tw-stock-quant`](../tw-stock-quant/SKILL.md) — turning patterns into a backtest
- [`tw-stock-data`](../tw-stock-data/SKILL.md) — sourcing the data
- [`tw-stock-options`](../tw-stock-options/SKILL.md) — TAIEX options
- [`rules/trading-discipline`](../../rules/trading-discipline.md) — entry/exit discipline
