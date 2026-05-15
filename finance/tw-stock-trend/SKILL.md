---
name: tw-stock-trend
description: >
  Trend identification for Taiwan-listed stocks — Dow theory structure
  (HH/HL vs LH/LL), multi-timeframe alignment, strength and phase, pullback
  vs reversal. Use this skill to answer "is this stock in an uptrend or
  downtrend, and how strong?" before any entry / exit decision.
category: finance
tags: [stock, taiwan, tw-stock, technical-analysis, charting, indicators]
keywords: [trend, uptrend, downtrend, Dow theory, higher high, lower low, swing point, ADX, pullback, reversal, break of structure, Wyckoff]
related: [tw-stock-technical, tw-stock-chip, tw-stock-fundamental, tw-stock-quant, portfolio-construction]
---

# Taiwan Stock Trend Identification

> "Is this stock going up or down?" sounds simple, but it's the first question every other decision depends on. Get the trend wrong and even perfect entry timing loses money.

## When to Use This Skill

- Deciding whether to look for long or short setups on a specific stock
- Reading TAIEX or sector regime before picking entries
- Distinguishing a pullback (still in trend) from a reversal (trend over)
- Sizing positions: full size in clear trends, small in chop
- Validating that a fundamental or chip-flow thesis isn't fighting price action

Pair with [`tw-stock-technical`](../tw-stock-technical/SKILL.md) for the indicator-level detail (MACD, RSI, KD, Bollinger). This skill is the **framework** above those indicators.

---

## 1. The Definition — Structure, Not Indicators

Indicators lag price. **Trend is defined by structure first.**

### Dow theory in two lines

- **Uptrend** = Higher Highs **and** Higher Lows (HH + HL)
- **Downtrend** = Lower Highs **and** Lower Lows (LH + LL)
- **Sideways** = Neither; swings overlap

```
Uptrend                Downtrend              Sideways
       /\                  \                   /\    /\
      /  \    /\          /\\                 /  \  /  \
   /\/    \  /  \        /  \\               /    \/    \
  /        \/    \  →   /    \\  →          /            \
                       /      \\
```

### What counts as a "swing high / low"?

1. **A swing high** is a candle whose high is higher than the N candles to its left and right (typically N=3 on daily, N=5 on weekly). Same with swing lows.

2. **Filter by significance.** On a noisy stock, use a 2–3% minimum move between swings; otherwise every tiny wiggle counts and the structure becomes meaningless.

3. **Mark the last two swing highs and last two swing lows.** That's all you need to read structure:
   - Last swing high > prior swing high? **HH**
   - Last swing low > prior swing low? **HL**
   - Both true → uptrend confirmed
   - Either flips → trend in question

---

## 2. Three Timeframes — Dow's Three Trends

| Frame | Horizon | Use |
|---|---|---|
| **Primary** (monthly / weekly K) | Months to years | Strategic direction; long-term position |
| **Secondary** (weekly / daily K) | Weeks to months | Tactical entry; medium-term swing |
| **Minor** (daily / hourly K) | Days to weeks | Execution timing; short-term scalp |

### Multi-timeframe alignment

| Primary | Secondary | Minor | Action |
|---|---|---|---|
| Up | Up | Up | **Full long** — strongest setup |
| Up | Up | Down | **Buy the pullback** — best risk/reward |
| Up | Down | Down | **Wait** — secondary correction within primary up |
| Down | Up | Up | **Counter-trend bounce** — small size, fast exit |
| Down | Down | Down | **Full short / cash** |
| Down | Down | Up | **Sell the rally** — counter-trend retracement |

4. **The larger frame sets direction; the smaller frame sets timing.** Don't open a primary-down trade because a minor frame turned up.

5. **Conflicts default to the higher frame.** Weekly up + daily down → wait, don't fight the weekly.

6. **For Taiwan retail with day jobs, the daily K is usually the action frame, weekly K is the trend frame.** Hourly is noise unless you trade actively.

---

## 3. Indicator Overlay — Confirming Structure

Structure alone is enough to identify a trend, but indicators **filter noise** and **measure strength**.

### Moving average stack

7. **The 20/60/120/240 MA stack confirms trend.** Bullish stack (MA5 > MA20 > MA60 > MA120 > MA240) = strong uptrend; bearish stack = strong downtrend. Tangle = no trend, look for range.

8. **MA240 as primary bull/bear divider.** Price above MA240 with MA240 sloping up = primary uptrend; below with slope down = primary downtrend. Crossing MA240 is a structurally significant event.

9. **MA20 slope as secondary signal.** Up-sloping MA20 = secondary uptrend; flat = range; down-sloping = secondary downtrend. Slope, not just position.

### ADX — Is there a trend at all?

| ADX value | Meaning |
|---|---|
| < 20 | **No trend** (range / chop) — trend strategies fail |
| 20–25 | Trend forming |
| 25–40 | Clear trend |
| > 40 | Very strong (and often near exhaustion) |

10. **ADX doesn't tell you direction.** It tells you *whether* there's a trend. Pair with structure or MA slope for direction.

11. **Below 20 ADX = trade differently.** Switch to range strategies (buy support, sell resistance, mean-revert). Most trend-following losses come from forcing trend trades in chop.

---

## 4. Trend Strength — How Convicted Is the Trend?

| Strong trend | Weak trend |
|---|---|
| Shallow pullbacks (3–5% in uptrend) | Deep pullbacks (>10%, near MA60) |
| Pullbacks die at MA20 / MA10 | Pullbacks repeatedly break MA20 |
| Volume rises on impulse, falls on pullback | Volume flat or inverted |
| ADX rising and > 25 | ADX < 20 or falling |
| Few overlapping bars; clean swings | Lots of overlap; choppy candles |
| MAs fan out (widening separation) | MAs converge |

12. **Pullback depth measures conviction.** A 3% pullback in a $100 stock that holds MA20 is gold; a 12% pullback that pierces MA60 is a different animal.

13. **Volume on impulse vs pullback** is the most underused signal. Uptrend with rising-volume rallies and falling-volume pullbacks → real demand. The reverse → distribution.

14. **A strong trend can stay overbought for weeks.** Don't fade RSI > 70 or KD > 80 in a strong trend; that's where the move is. See `tw-stock-technical` rule on "indicator saturation".

---

## 5. Trend Phase — Wyckoff's Four Phases

Trends move through a cycle:

```
Accumulation  →  Markup  →  Distribution  →  Markdown  →  Accumulation
(sideways      (impulse     (sideways         (impulse
 at bottom,     up,          at top,           down,
 quiet)         crowd in)    crowd selling)    crowd out)
```

### How to recognise each

| Phase | Price | Volume | Behaviour |
|---|---|---|---|
| **Accumulation** | Sideways range after a downtrend | Quiet, then occasional spike on lows that hold | Smart money buying; retail bored |
| **Markup** | Trending up, HH/HL | Rising on rallies, falling on pullbacks | Retail piles in late |
| **Distribution** | Sideways range after an uptrend | High but choppy, big up-down candles | Smart money selling into strength |
| **Markdown** | Trending down, LH/LL | Rising on declines, falling on bounces | Retail holds, hopes, eventually capitulates |

15. **Distribution looks like accumulation at the wrong end.** The price action is similar (sideways with big bars); the context (after a sustained rally vs after a sustained decline) decides which.

16. **Accumulation often coincides with bad fundamentals**; distribution often coincides with euphoric news. Pair this with `tw-stock-fundamental` and `tw-stock-chip` to disambiguate.

---

## 6. Pullback vs Reversal — The Hardest Call

In an uptrend, when price drops, is it a healthy pullback or the start of a downtrend?

### Pullback (still in uptrend)

- Holds the most recent HL or bounces from MA20 / MA60
- Reduces depth and volume as it goes
- Resumes within a few bars (typically 3–10 days)
- Makes a new HL above the previous HL on the bounce

### Reversal (uptrend probably over)

- **Break of structure (BoS)**: closes below the most recent HL → uptrend invalidated
- The bounce that follows fails to make a new HH (only LH)
- Two failed attempts to break the prior high
- Volume profile flips: heavier on declines than rallies
- MA20 turns down and price stays below

17. **The single sharpest signal: HL gets violated.** That's "break of structure". Below the most recent HL, the uptrend is no longer technically intact.

18. **One BoS is a warning, not a verdict.** Wait for a second leg down (LH followed by LL) before declaring reversal. Many "BoS" events are false breaks that snap back.

19. **The reverse applies symmetrically.** In a downtrend, the most recent LH being broken is the warning; a HH after it confirms reversal.

20. **In strong trends, "deep pullbacks" can look like reversals but aren't.** That's why depth alone isn't enough — combine with BoS and volume.

---

## 7. Range vs Trend — Don't Force a Trend on Chop

The single biggest mistake in trend trading is **trading trend strategies in ranges**.

### Range signals

- ADX < 20
- Price bouncing between two parallel horizontal lines
- MAs tangled (MA5/20/60 within 1–2%)
- Bollinger Bands narrow ("squeeze")
- Volume flat or randomly distributed

21. **In a range, switch strategy:** buy near support, sell near resistance, mean-revert. Trend signals (MACD cross, golden cross) chronically lose money here.

22. **A range often ends in a breakout that becomes the new trend.** The transition is hard to see in real time; that's why patient breakout traders wait for the close above the range high (or below the low) with rising volume.

23. **TAIEX and individual stocks can be in different regimes.** Index ranging while a single stock trends, or vice versa. Read both.

---

## 8. Entry Rules — Trading With the Trend

Once you know the trend direction and strength, the rules write themselves:

24. **Enter on pullbacks, not breakouts.** In an uptrend, the best entries are pullbacks to MA20 / MA60 / a prior breakout level (now support). Chasing breakouts gets you in at peak emotion.

25. **Stop below the most recent HL** (in an uptrend) or above the most recent LH (in a downtrend). That's the structural invalidation point — beyond it the trade thesis is wrong.

26. **Trail stops along subsequent HLs.** Each new HL becomes the new stop level. This lets winners run while protecting against giveback.

27. **Size proportional to trend strength.** Full size in clear primary up + secondary up + minor pullback alignment. Half size when frames disagree. Skip when chop or against primary trend.

28. **Never average down in a downtrend.** "Cheap" in a downtrend stays cheap, then gets cheaper. Adds only on confirmed HLs in an uptrend.

---

## 9. TWSE-Specific Notes

29. **Red K = up, Black K = down** (opposite of US/European charts). Calibrate when reading translated TA material.

30. **10% daily price limit** distorts structure analysis. A "limit-up" candle truncates what would be a longer impulse; consecutive limit-ups can mask exhaustion. Look at weekly K for cleaner structure in volatile names.

31. **Monthly revenue release (10th of each month, before 23:59)** creates predictable jumps — both up and down — that aren't pure technical. Don't read a single post-revenue candle as a structural signal; wait for the second day's confirmation.

32. **Ex-dividend dates** create technical gaps that *aren't* real bearish signals. Adjust the chart for dividends (價格還原) or note ex-div days when reading swings. See `tw-stock-data` on dividend adjustment.

33. **First and last 5 minutes of the session** are noisy due to opening / closing call auctions. Intraday traders weight 09:05–13:25 mid-session structure higher.

34. **TAIEX trend filter dominates individual stocks.** When TAIEX is in primary downtrend, ~80% of stocks follow. Lone uptrends exist but are exceptions; default to "wait for TAIEX to turn" unless you have a strong stock-specific thesis.

---

## 10. Common Traps

| Trap | Description | Counter |
|---|---|---|
| **Hindsight trend** | "It was clearly up the whole time" — easy to see after the fact | Decide on the last 30 bars visible *at the moment* |
| **Single-candle reversal call** | One big bear candle ends an uptrend in your head | Wait for BoS + LH confirmation |
| **Trend overfitting** | Drawing 3 trendlines on the same chart to find one that fits | One per timeframe, max |
| **MA worship** | "Price touched MA60, must bounce" | MAs are guides, not laws — combine with structure |
| **Counter-trend hero** | Repeatedly shorting a strong uptrend on RSI > 70 | Saturated indicators in strong trends are normal |
| **Range as trend** | Treating 3 weeks of sideways as the start of a trend | Check ADX < 20; use range tactics |
| **News override** | "Earnings beat, must be uptrend now" | News changes fundamentals; trend needs structural confirmation |
| **Stale trend** | Calling a 6-month-old uptrend "still up" despite a clear BoS 4 weeks ago | Re-read structure on every entry, not from memory |

---

## 11. Pre-Decision Checklist

Before any trade decision, run this top-to-bottom:

- [ ] **TAIEX**: primary direction (above / below MA240, MA240 slope)
- [ ] **Sector index**: aligned with TAIEX or diverging?
- [ ] **Stock weekly K**: HH+HL / LH+LL / overlapping swings?
- [ ] **Stock daily K**: structure direction matches weekly?
- [ ] **MA stack**: bullish / bearish / tangled?
- [ ] **ADX**: > 25 (trade trend) or < 20 (trade range)?
- [ ] **Most recent HL (uptrend) or LH (downtrend)**: where exactly, in $?
- [ ] **Pullback or reversal**: any BoS in the last 10 bars?
- [ ] **Volume on impulse vs pullback**: agree with the trend?
- [ ] **Phase**: accumulation / markup / distribution / markdown?
- [ ] **Entry plan**: chase or wait for pullback?
- [ ] **Stop level**: which HL / LH is the invalidation?
- [ ] **Position size**: full, half, or skip?

If you can't answer all of these, you don't know the trend well enough to size up.

---

## 12. Quick Decision Tree

```
Is ADX > 25?
├── No → range / chop → use range tactics, not trend tactics
└── Yes → there's a trend
    │
    Is MA240 slope up?
    ├── Yes → primary uptrend
    │   │
    │   Is weekly K making HH + HL?
    │   ├── Yes → strong primary uptrend → look for long pullbacks
    │   └── No  → primary up but secondary correction → wait
    │
    └── No → primary downtrend
        │
        Is weekly K making LH + LL?
        ├── Yes → strong primary downtrend → cash / short rallies
        └── No  → primary down but bouncing → counter-trend, small size
```

---

## Related Skills

- [`tw-stock-technical`](../tw-stock-technical/SKILL.md) — indicator details (MACD, RSI, KD, Bollinger) that fill in the strength / saturation columns above
- [`tw-stock-chip`](../tw-stock-chip/SKILL.md) — chip flow confirms or contradicts the price-structure trend
- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — fundamentals are the "why" behind a sustained trend
- [`tw-stock-quant`](../tw-stock-quant/SKILL.md) — momentum / trend-following factors backtested
- [`portfolio-construction`](../portfolio-construction/SKILL.md) — trend strength informs position sizing
- [`rules/trading-discipline.md`](../../rules/trading-discipline.md) — stops, sizing, psychological control
