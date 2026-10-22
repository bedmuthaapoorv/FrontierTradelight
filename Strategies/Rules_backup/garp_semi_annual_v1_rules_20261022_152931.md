# Stock Selection Rules

## Strategy Metadata

Strategy Name: GARP Semi-Annual v1
Market: India (NSE)
Timeframe: Daily data, semi-annual rebalance
Holding Period: Position (about 6 months, until the next rebalance)

---

## Data Availability Note

This strategy uses each stock's daily OHLCV history (for the rebalance-day
check and a liquidity floor) and the `fundamentals` parameter: annual
company fundamentals as publicly known on the evaluated day (a fiscal year
only counts 60 days after it ends). Use the `fundamentals` parameter
directly - never compute fundamentals from `df`. No sector rank or market
breadth rule is used.

---

## Strategy Rationale

GARP (growth at a reasonable price) buys companies with steady earnings
growth, good returns on capital and moderate debt, at a valuation that is
reasonable relative to that growth. See `reports/GARP strategy for NSE
screener.md` and its review in the project root.

This is an approximation of the research's recommended design (a separate,
semi-annually rebalanced GARP portfolio) built inside the existing
signal-to-trade backtester:

- Fundamentals change about once a year, so a plain fundamentals screen
  would pass every day and the backtester would re-enter daily. Rule 1
  makes a stock eligible ONLY on the first trading day on or after 15 June
  or 15 December - the rebalance day. 15 June falls after the 30 May annual
  results deadline. The paired exit (GARP Rebalance Exit v1) holds each
  position until the next rebalance day, so the portfolio is rebuilt every
  six months.
- Run the backtest with `--max-positions 25`: on each rebalance day the
  top 25 stocks by Rank Score are bought.
- Known gaps vs. the research design: no sector or name caps, no rank
  buffer (holdings that still qualify are sold and re-bought), no costs
  modelled, and the Rank Score is absolute per stock rather than a
  cross-sectional z-score. P/E uses the backtest's heuristically
  split/bonus-adjusted close against Screener's adjusted EPS, so a missed
  small corporate action can distort PEG for that stock.
- 2021-2026 was a strong period for value stocks in India; a GARP result
  over this window is not evidence for other regimes.

---

## Mandatory Filters

All rules below MUST pass. Let `f = fundamentals.get(symbol)` (treat a
missing `fundamentals` parameter as an empty dict).

---

### Rule 1: Rebalance Day

Description:
The stock can only be bought on a rebalance day, so each stock signals at
most once every six months.

Condition:

Let D = the date of the last row of `df` and P = the date of the row before
it. The rule passes if, for T = 15 June of D's year OR T = 15 December of
D's year:

P < T <= D

Notes:
- This means D is the first trading day on or after 15 June or 15
  December.
- Fail if `df` has fewer than 2 rows.

---

### Rule 2: Minimum Liquidity Floor

Description:
Reject illiquid stocks so positions can be entered and exited without
slippage. Same floor as Breakout Momentum v8+.

Condition:

MA(Volume * Close, 20) >= 50000000
AND
Close >= 50

---

### Rule 3: Fundamentals Available

Description:
Every fundamentals rule needs this stock's data.

Condition:

f is not None

Notes:
- If f is None, fail this rule and also report Rules 4-9 as failed.

---

### Rule 4: Consistent Profitability

Description:
At least five consecutive profitable years, so growth is measured on a
real earnings base.

Condition:

f["positive_eps_years"] >= 5

---

### Rule 5: Earnings Growth

Description:
Steady earnings growth, with a ceiling to avoid unsustainable spikes.

Condition:

f["eps_cagr_3y"] is not None
AND
0.05 <= f["eps_cagr_3y"] <= 0.50

---

### Rule 6: Sales Growth

Description:
Earnings growth should be backed by revenue growth, not only margins.

Condition:

f["sales_cagr_3y"] is not None
AND
f["sales_cagr_3y"] >= 0.05

---

### Rule 7: Return on Equity

Description:
Quality filter: the business earns a good return on shareholders' capital.

Condition:

f["roe"] is not None
AND
f["roe"] >= 0.12

---

### Rule 8: Leverage

Description:
Moderate debt for non-financial companies; debt/equity is not meaningful
for banks and other financials, so they are exempt.

Condition:

f["is_financial"] is True
OR
(f["de"] is not None AND f["de"] <= 1.0)

---

### Rule 9: Reasonable Price for the Growth

Description:
The GARP valuation test: price/earnings relative to earnings growth.

Condition:

f["peg"] is not None
AND
0 < f["peg"] <= 1.5

---

## Rejection Rules

Reject stock if ANY mandatory filter fails.

---

## Ranking Rules

### Rank Score

Score =
30% Growth_Score
+
20% Sales_Score
+
25% Quality_Score
+
25% Value_Score

Where (clamp every sub-score to [0, 100]):

Growth_Score = f["eps_cagr_3y"] / 0.30 * 100
(30% EPS CAGR or more = 100 points)

Sales_Score = f["sales_cagr_3y"] / 0.25 * 100
(25% sales CAGR or more = 100 points)

Quality_Score = f["roe"] / 0.30 * 100
(30% ROE or more = 100 points)

Value_Score = (1.5 - f["peg"]) / 1.0 * 100
(PEG 0.5 or lower = 100 points, PEG 1.5 = 0 points)

Higher score is better. If the stock fails any rule, the score is 0.

---

## Output Columns

Return:

- Symbol
- Company Name
- Sector
- Current Price
- Latest FY
- Positive EPS Years
- EPS CAGR 3Y (%)
- Sales CAGR 3Y (%)
- ROE (%)
- Debt/Equity
- P/E
- PEG
- Rank Score

Where the % columns are the fractions times 100, and missing values are
shown as None.

Sort:

Rank Score DESC

Limit:

Top 25 Stocks
