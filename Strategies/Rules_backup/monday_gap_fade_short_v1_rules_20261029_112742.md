# Stock Selection Rules

## Strategy Metadata

Strategy Name: Monday Gap Fade Short v1
Market: India (NSE)
Timeframe: Daily signals, intraday execution
Direction: Short
Holding: Intraday (MIS - short at Monday's open, square off by the close, never held overnight)

---

## Data Availability Note

Only each stock's own daily OHLCV history is used. No sector rank, market
breadth, momentum rank or fundamentals rule is used. There is NO intraday
data.

---

## Strategy Rationale

A stock that falls hard on Friday and then gaps up at Monday's open tends to
give the gap back during Monday's session. In the point-in-time Nifty 500,
Dec 2019 - Dec 2025, stocks that fell 4% or more on Friday and opened at
least 1% above Friday's close on Monday fell about 1.4% on average from
Monday's open to Monday's close (816 trades, 67% closed below the open).
The same setup on Tuesday-Friday shows no edge, so the weekend matters.
See `reports/Weekend effect on NSE.md` and the follow-up analysis.

This file only finds the Friday candidates. The Monday gap-up condition
can only be checked at Monday's open, so it lives in the paired exit
(Monday Gap Fade Exit v1), which cancels the trade ("NoEntry") when Monday
does not open at least 1% above Friday's close. These thresholds were found
by searching 2020-2025 data; 2026 is the out-of-sample test. Results are
GROSS - trading costs are not modelled.

---

## Mandatory Filters

All rules below MUST pass.

---

### Rule 1: Friday Signal

Description:
The signal day must be a Friday, so the entry is the next session (Monday,
or later if Monday is a holiday - the exit cancels those).

Condition:

The date of the last row of `df` is a Friday (weekday 4, Monday = 0).

Notes:
- Fail if `df` has fewer than 2 rows.

---

### Rule 2: Sharp Friday Fall

Description:
The stock fell at least 4% on the signal day.

Condition:

Let C = the last close and P = the previous row's close.

C / P - 1 <= -0.04

---

## Rejection Rules

Reject stock if ANY mandatory filter fails.

---

## Ranking Rules

### Rank Score

Score = the size of the Friday fall in percent: (1 - C / P) * 100

Higher score is better (a bigger Friday fall gets capital first when there
are more candidates than slots). If the stock fails any rule, the score
is 0.

---

## Output Columns

Return:

- Symbol
- Company Name
- Sector
- Close
- Friday Return (%)   ((C / P - 1) * 100)
- Rank Score

Sort:

Rank Score DESC
