---
name: tw-stock-options
description: >
  Options basics for the Taiwan market — calls and puts, the Greeks
  (Delta / Gamma / Theta / Vega), common strategies (covered call,
  protective put, spreads, straddles), TAIEX options (TXO) contract specs,
  and risk management for retail investors.
category: finance
tags: [stock, taiwan, options, derivatives, strategy]
keywords: [TXO, TAIEX, Delta, Gamma, Theta, Vega, covered call, protective put, IV crush]
related: [tw-stock-fundamental, tw-stock-technical, portfolio-construction]
---

# Taiwan Options Basics

> An option is a right, not an obligation. The buyer pays a premium for "the right to choose"; the seller takes a premium and accepts "the obligation to be exercised against".

## When to Use This Skill

- Want to hedge a stock holding (protective put)
- Want extra income from a stock holding (covered call)
- Want to learn options basics and how to read quotes
- Want directional exposure with small capital
- Want to understand why options "go to zero"

---

## Basics

### Calls and Puts

| | Buyer (holder) | Seller (writer) |
|-|----------------|------------------|
| **Call** | Right to buy the underlying at the strike before expiry | Obligation to sell at the strike if exercised |
| **Put** | Right to sell the underlying at the strike before expiry | Obligation to buy at the strike if exercised |

### Four basic positions

| Position | View | Max profit | Max loss |
|----------|------|------------|----------|
| **Long Call** | Bullish | Unlimited | Premium |
| **Short Call** | Not bullish | Premium | Unlimited |
| **Long Put** | Bearish | Strike − premium | Premium |
| **Short Put** | Not bearish | Premium | Strike − premium |

1. **Buyers have limited risk (premium) and big upside.** But low win rate (time isn't on your side).
2. **Sellers have limited profit (premium) but potentially huge risk.** Higher win rate but a single loss can be enormous.
3. **Beginners: start as buyers.** Selling needs more capital and risk-management skill.

---

## TAIEX Options (TXO) Contract Spec

| Item | Spec |
|------|------|
| Underlying | Taiwan Capitalization Weighted Stock Index (TAIEX) |
| Multiplier | NT$50 per index point |
| Expiry | Third Wednesday of each month |
| Style | European (settled at expiry only) |
| Settlement | Cash settled |
| Trading hours | 08:45–13:45 |

### Quote example

```
TXO 20000 Call (Feb)   quote 150 pts
→ Premium = 150 × 50 = NT$7,500
→ One Call costs NT$7,500
→ Break-even at expiry = 20000 + 150 = 20150
→ TAIEX > 20150 at expiry → profit
→ TAIEX < 20000 at expiry → premium goes to zero (loss = NT$7,500)
```

---

## The Greeks

| Greek | What it measures | Why buyers care |
|-------|------------------|-----------------|
| **Delta (Δ)** | Premium change per 1-point move in underlying | Call delta 0–1, Put delta 0 to −1 |
| **Gamma (Γ)** | Rate of change of delta | Largest near at-the-money |
| **Theta (Θ)** | Time-value decay per day | **The buyer's enemy** — losing a bit every day |
| **Vega (ν)** | Premium change per 1% move in implied vol | Higher IV → higher premium |

### Practical points

4. **Theta is the buyer's biggest cost.** The closer to expiry, the faster the decay. Don't buy too short-dated.
5. **Delta ≈ probability of finishing in-the-money.** Delta 0.3 Call ≈ 30% chance of winning.
6. **Vega matters most before big events (earnings, elections).** IV spikes pump premiums.

---

## Common Strategies

### Beginner

| Strategy | Construction | Use when |
|----------|--------------|----------|
| **Covered Call** | Long stock + short call | Stock is sideways; earn extra income |
| **Protective Put** | Long stock + long put | Worried about a drop, don't want to sell |
| **Long Call** | Buy call | Bullish, limited risk |
| **Long Put** | Buy put | Bearish, limited risk |

### Intermediate

| Strategy | Construction | Use when |
|----------|--------------|----------|
| **Bull Call Spread** | Long lower-strike call + short higher-strike call | Mildly bullish, lower cost |
| **Bear Put Spread** | Long higher-strike put + short lower-strike put | Mildly bearish, lower cost |
| **Straddle** | Long call + long put (same strike) | Big move expected, direction unclear |
| **Strangle** | Long call + long put (different strikes) | Like straddle, cheaper, needs bigger move |
| **Iron Condor** | Short call spread + short put spread | Sideways expected; sell time |

7. **Spreads are the best intermediate strategy for retail.** Both risk and reward are bounded and controllable.

---

## Risk Management

8. **Total options exposure ≤ 5–10% of capital.** Cap monthly premium spend.
9. **Don't sell naked calls.** The risk is theoretically unlimited. Use a spread.
10. **Time stops for buyers.** With a week to go and no clear direction, consider cutting — the last week's theta accelerates.
11. **Know the max loss before you trade.** Every strategy: compute the worst case before placing the order.
12. **Don't go heavy the day before a big event.** IV is already priced in; after the event IV collapses (IV crush) and premiums shrink fast.

---

## Common Traps

| Trap | Note | Counter |
|------|------|---------|
| **Buying deep OTM** | Cheap, but > 90% chance of going to zero | Buy ≥ Delta 0.2 |
| **Ignoring Theta** | Lose time value daily | Don't buy too close to expiry |
| **IV crush** | Post-event IV drop, premium collapses | Pre-event favors sellers |
| **Naked call risk** | Selling naked into a rally | Use a spread to bound the loss |
| **Over-leverage** | Buying too many contracts | Single strategy < 5% of capital |
| **Settlement surprise** | Forgetting expiry day | Set reminders; decide before close |

---

## Pre-Trade Checklist

Before opening an options trade:

- [ ] I know the max loss
- [ ] Premium spend < 5% of capital
- [ ] Delta > 0.2 (not deep OTM)
- [ ] At least 2–4 weeks to expiry (avoid theta acceleration)
- [ ] No imminent event likely to cause IV crush
- [ ] Clear exit plan (target, stop, time stop)
- [ ] I understand TXO is European-style and cash-settled

---

## Related Skills

- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — fundamentals for direction
- [`tw-stock-technical`](../tw-stock-technical/SKILL.md) — technicals for timing and strike
- [`portfolio-construction`](../portfolio-construction/SKILL.md) — options' role in the portfolio
- [`rules/trading-discipline`](../../rules/trading-discipline.md) — money management
