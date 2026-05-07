---
name: tw-stock-data
description: >
  Data engineering for Taiwan-listed stocks — primary data sources (TWSE,
  TPEx, MOPS), key fields, cleaning essentials (dividend adjustment,
  point-in-time, survivorship bias), storage choices, scheduling, and common
  pitfalls. Concept-oriented; APIs and field semantics are language-agnostic.
category: finance
tags: [stock, taiwan, tw-stock, data-engineering, api, pipeline]
keywords: [TWSE, TPEx, MOPS, FinMind, TEJ, point-in-time, dividend adjustment]
related: [tw-stock-fundamental, tw-stock-chip, tw-stock-technical, tw-stock-quant]
---

# Taiwan Stock Data Engineering

> Garbage in, garbage out. Quant return ceiling = data quality ceiling. Spending 80% of your time on data is normal.

## When to Use This Skill

- Building your own Taiwan stock historical database (vs depending on a third-party platform)
- Pulling realtime or daily data for analysis
- Backtesting but unsure which sources to use and how to clean them
- Building an automated data-update pipeline
- Ensuring data quality (dividend adjustment, look-ahead, survivorship)

---

## 1. Taiwan Data Sources

### Official, free

| Source | Site | Provides | Format | Cadence |
|--------|------|----------|--------|---------|
| **TWSE** | twse.com.tw | Listed daily quotes, three-major-institution flow, margin, TDCC | CSV / JSON | Daily |
| **TPEx** | tpex.org.tw | OTC daily quotes, etc. | CSV / JSON | Daily |
| **MOPS** | mops.twse.com.tw | Financial statements, monthly revenue, dividends, insider holdings, material info | HTML / CSV | Monthly / quarterly / annual |
| **TWSE Open API** | openapi.twse.com.tw | RESTful API for some listed data | JSON | Daily |

### Third-party / open-source

| Source | Notes | Caveats |
|--------|-------|---------|
| **FinMind** | Open TW data platform with API + Python package | Free tier rate-limited |
| **TWSE Open Data (gov.tw)** | Government open data | Fields may be incomplete |
| **Yahoo Finance (TW)** | `{code}.TW` (listed), `{code}.TWO` (OTC) | Dividend adjustment quality varies |
| **Google Finance** | Basic quotes | No history download |

### Paid

| Source | Notable | Best for |
|--------|---------|----------|
| **TEJ (Taiwan Economic Journal)** | Academic-grade, includes delisted, point-in-time financials | Quant backtesting (most correct) |
| **CMoney** | Friendly UI, strategy-backtest platform | Non-engineer users |
| **XQ** | Realtime + algo trading | Realtime strategy execution |

---

## 2. Core Data Types and Fields

### 1. Daily quotes (OHLCV)

| Field | Notes | Caveats |
|-------|-------|---------|
| Date | Trading day | TW market: Mon–Fri, exclude holidays |
| Code | 4-digit | Listed and OTC code spaces don't overlap |
| Open | First trade of the day | |
| High | Day high | |
| Low | Day low | |
| Close | Last trade of the day | **Needs dividend adjustment** |
| Volume | Lots traded | 1 lot = 1,000 shares |
| Turnover | Daily traded value | |
| P/E | TWSE-published trailing P/E | Daily refreshed |

### 2. Monthly revenue

| Field | Notes |
|-------|-------|
| Year-month | Revenue's reporting month |
| Revenue | In NT$ thousands |
| MoM | vs previous month |
| YoY | vs same month last year |
| YTD revenue | Cumulative this year |
| YTD YoY | YTD vs prior YTD |

**Note:** monthly revenue is published by the 10th of the following month. January revenue → by Feb 10.

### 3. Quarterly financials

| Field | Notes |
|-------|-------|
| EPS | Earnings per share |
| Revenue | Quarterly revenue |
| Gross margin | |
| Operating margin | |
| Net margin | |
| ROE | Usually trailing 4 quarters |
| ROA | |
| Book value per share | |
| Debt ratio | |
| OCF | Operating cash flow |
| FCF | Free cash flow |

**Release deadlines (critical):**

| Report | Deadline | Earliest usable in backtest |
|--------|----------|------------------------------|
| Q1 | 5/15 | 5/16 |
| Q2 | 8/14 | 8/15 |
| Q3 | 11/14 | 11/15 |
| Q4 + Annual | 3/31 | 4/1 |

### 4. Institutional flow

| Field | Notes |
|-------|-------|
| Foreign net (lots) | FINI (institutional) + FIDI (individual) |
| Trust net (lots) | Domestic investment trusts |
| Dealer net (lots) | Split into "proprietary" and "hedging" |
| Three-institution total | Sum of the above |

### 5. Margin trading

| Field | Notes |
|-------|-------|
| Margin balance (lots) | After-close balance |
| Margin change | vs previous day |
| Short balance (lots) | After-close short balance |
| Short change | |
| Short/margin ratio | Short / margin |

### 6. TDCC shareholder concentration

| Field | Notes |
|-------|-------|
| Holding tier | 1–999 shares, 1,000–5,000 shares, ..., ≥ 1,000 lots |
| Holders | # of holders per tier |
| Shares | Total shares per tier |
| % of vault | Percentage |

**Cadence:** updated each Saturday for the prior Friday's snapshot.

---

## 3. Data Cleaning Essentials

### 1. Dividend adjustment (most important)

When TW stocks go ex-dividend the price is adjusted:
- **Cash dividend:** Price − cash dividend per share
- **Stock dividend:** Price / (1 + stock dividend per share / 10)

**The problem if you don't adjust:** a 5%-yield name will appear to have lost 25% over 5 years even though investors actually made money.

**Adjustment methods:**
- **Forward-adjusted:** scale historical prices up; current price unchanged. Good for technical analysis.
- **Back-adjusted:** keep history, adjust forward. Good for return calculation.
- **Adjustment-factor method:** compute a factor at each ex-dividend, multiply cumulatively.

### 2. Point-in-time

**Rule: at any backtest date, you can only use data that was *already published* by that date.**

Common mistakes:
- Using Q1 financials on April 1 (Q1 is published by May 15)
- Using "the latest" revenue when backtesting a past date
- Using "restated" instead of "originally reported" financials

**Fix:** add a `published_date` column to every record; backtests filter `published_date <= backtest_date`.

### 3. Survivorship bias

Only using currently-listed names = automatically excluding delisted/bankrupt companies = inflated backtest returns.

**Fix:** the database must include all stocks ever listed, with delisted dates and reasons.

### 4. Missing values

| Situation | Handling |
|-----------|----------|
| Trading halt for a day | Carry the previous close, set volume to 0 |
| Missing financials | Exclude that stock (don't interpolate — that creates fake data) |
| New listing | Drop the first N days if your strategy needs them (e.g., MA60 needs 60 days) |

### 5. Data consistency checks

After every update:

- [ ] Trading days are continuous (no gaps after holidays)
- [ ] Close is within ±10% of prior (price-limit sanity)
- [ ] Days with volume = 0 are explained (halt, not loss of data)
- [ ] Monthly revenue sum ≈ annual revenue (< 1% error)
- [ ] Ex-dividend days have a corresponding price gap

---

## 4. Storage Options

### Personal (small scale)

| Option | Pros | Cons |
|--------|------|------|
| **CSV files** | Simple, readable from any language | Slow queries, no joins |
| **SQLite** | Single-file DB, supports SQL, zero config | No concurrent writes |
| **DuckDB** | Vectorized analytical DB, fast on CSV / Parquet | Newer, ecosystem still growing |
| **Parquet files** | Columnar, well compressed, fast for analytics | Needs code to read |

**Recommendation:** start with **SQLite or Parquet**. Use CSV only as a transit / interchange format.

### Suggested schema

```
stocks (master)
├── code           TEXT PK   -- ticker
├── name           TEXT
├── market         TEXT      -- TSE / OTC
├── industry       TEXT
├── listed_date    DATE
└── delisted_date  DATE      -- NULL = still listed

daily_prices
├── code           TEXT FK
├── date           DATE
├── open           REAL
├── high           REAL
├── low            REAL
├── close          REAL      -- raw close
├── close_adj      REAL      -- dividend-adjusted close
├── volume         INTEGER   -- lots
└── PK(code, date)

monthly_revenue
├── code           TEXT FK
├── year_month     TEXT      -- "2024-03"
├── revenue        BIGINT    -- NT$ thousands
├── yoy            REAL      -- YoY %
├── published_date DATE      -- for point-in-time
└── PK(code, year_month)

quarterly_financials
├── code           TEXT FK
├── year           INTEGER
├── quarter        INTEGER   -- 1..4
├── eps            REAL
├── roe            REAL
├── gross_margin   REAL
├── ... (other ratios)
├── published_date DATE
└── PK(code, year, quarter)

daily_institutional
├── code           TEXT FK
├── date           DATE
├── foreign_buy_sell INTEGER -- + buy / − sell
├── trust_buy_sell   INTEGER
├── dealer_buy_sell  INTEGER -- proprietary
├── dealer_hedge     INTEGER -- hedging
└── PK(code, date)

daily_margin
├── code           TEXT FK
├── date           DATE
├── margin_balance INTEGER   -- lots
├── short_balance  INTEGER   -- lots
└── PK(code, date)

weekly_shareholders
├── code           TEXT FK
├── date           DATE      -- each Friday
├── level          TEXT      -- "1-999", "1000+"
├── holders        INTEGER
├── shares         BIGINT
├── percentage     REAL
└── PK(code, date, level)
```

---

## 5. Scheduling

### Daily (after close, suggested 15:30–17:00 local)

| Data | Source | Delay |
|------|--------|-------|
| Daily quotes | TWSE / TPEx | ~30 min after close |
| Three-institution flow | TWSE / TPEx | ~1 hr after close |
| Margin / short | TWSE / TPEx | ~1 hr after close |
| Securities-lending shorts | TWSE | ~2 hr after close |

### Monthly

| Data | Source | When |
|------|--------|------|
| Monthly revenue | MOPS | Days 1–10 of next month |

### Quarterly

| Data | Source | When |
|------|--------|------|
| Quarterly financials | MOPS | Per legal deadlines |
| Dividend proposal | MOPS | After board approval |

### Weekly

| Data | Source | When |
|------|--------|------|
| TDCC shareholder concentration | TDCC / MOPS | Each Saturday |

### Scheduling notes

1. **TWSE has rate limits.** Too-frequent requests get blocked. Use 3–5s spacing.
2. **Retry on failure.** Official sites have occasional maintenance. Use exponential backoff.
3. **Log every fetch.** Success/fail/skip — for tracking gaps.
4. **Run consistency checks after each fetch.**

---

## 6. Common Traps

| Trap | Note | Counter |
|------|------|---------|
| **Yahoo Finance dividend adjustment is unreliable** | Occasional misses or delays | Compute your own factor, or use TEJ |
| **TWSE CSV format changes** | Columns added/removed, encoding shifts | Validate format after fetch |
| **New listings have no price limit for the first 5 days** | Wild moves | Exclude the first listing week |
| **ETFs mixed in with stocks** | 00xx codes are ETFs | Add a stock_type column, separate handling |
| **Capital reduction creates a non-dividend gap** | Price moves but it's not ex-dividend | Mark "abnormal gap"; backtest filters them |
| **Code change on OTC-to-listed transitions** | History fragments | Use a unified code-mapping table |
| **KY shares (foreign issuers in TW)** | Different filing format | Special-case or exclude |

---

## 7. Quality Checklist

When building or updating the database:

- [ ] Source includes both listed and OTC
- [ ] Includes delisted names (no survivorship bias)
- [ ] Close is dividend-adjusted
- [ ] Financials carry `published_date` (point-in-time)
- [ ] Monthly revenue keyed by published date (not reporting month)
- [ ] First N days of new listings flagged
- [ ] ETFs separated from individual stocks
- [ ] Halt days handled (carry close, volume = 0)
- [ ] Update job has retry + error notifications
- [ ] Consistency checks run after each update

---

## Related Skills

- [`tw-stock-fundamental`](../tw-stock-fundamental/SKILL.md) — fundamentals (uses financials)
- [`tw-stock-chip`](../tw-stock-chip/SKILL.md) — chip flow (uses institutional, margin, TDCC)
- [`tw-stock-technical`](../tw-stock-technical/SKILL.md) — technicals (uses OHLCV)
- [`tw-stock-quant`](../tw-stock-quant/SKILL.md) — quant strategies (uses everything)
