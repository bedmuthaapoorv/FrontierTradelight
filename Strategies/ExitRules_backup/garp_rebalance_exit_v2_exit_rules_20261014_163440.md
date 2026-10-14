# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: GARP Rebalance Exit v2
Applies To: GARP Semi-Annual v1 (rules.md) - holds each position until the
next semi-annual rebalance day. Not meant for technical entries.
Timeframe: Daily (closing price only)

---

## Data Availability Note

Only the entry price/date and the stock's own daily OHLCV (before and after
entry) are available. No fundamentals, ranks, index or breadth data are
available to the exit - the next rebalance re-applies the fundamental screen
instead. This exit uses only `entry_price`, `entry_date` and the `close`
column of `future_df`. `signal_history_df` is not used. Volume is not used.

---

## Strategy Rationale

The paired entry buys only on a rebalance day (first trading day on or after
15 June / 15 December). This exit sells every position at the close of the
next rebalance day, so capital is free for that day's new list (the
backtester processes exits before entries; new entries fill at the next
day's open).

v2 changes v1 in one way: the catastrophic stop moves from 0.75 x entry to
0.70 x entry. Evidence (2021-2026 backtest, 246 funded trades): the -25% stop
fired 36 times, mostly in two market-wide selloffs, and the stopped names
were on average 6% higher at the next rebalance than at the stop. In a
portfolio replay, -25% gave 11.13% CAGR, -30% 11.19%, no stop 12.48% but a
-48.5% worst trade. -30% is a wide stop within the range the stop-loss
literature finds not harmful; it is kept as tail insurance (Dec-2021, where
holding stopped names would have been much worse), not as a source of
return. Trailing stops, 200-day SMA exits and profit caps all reduced
returns on this data and are deliberately NOT used.

Leaderboard results are pre-cost (about 0.22% explicit cost per NSE delivery
round trip plus slippage) and value open positions at cost, so drawdowns are
understated. One 5-year window, 10 cohorts: do not tune these parameters on
it.

---

## Entry Reference

Entry Price: `entry_price` as passed in (the opening price on the trading
day after the signal day). `future_df` row 0 is the entry day in both the
backtest and the live Sell tab.

---

## Data Conventions (READ FIRST)

- Use positional access (`.iloc`). Session s = row s - 1 of `future_df`;
  session 1 is the entry day and its close IS checked.
- Compare calendar dates, not timestamps: for each row use
  `d = pd.Timestamp(future_df.index[i]).date()` (bars may carry a time such as
  18:30). Convert `entry_date` the same way.
- If a row's close is NaN, skip that row (no exit can fire on it) but still
  count it as a session.
- Trigger and fill both use the session's close. Never use intraday high/low.
- Do not raise. Return None if `future_df` is empty.

---

## Pre-Trade Calculation (Computed Once at Entry)

Let E = pd.Timestamp(entry_date).date().

Next_Rebalance = the earliest of these dates that is strictly AFTER E:
15 June of E's year, 15 December of E's year, 15 June of the next year.

Stop_Level = 0.70 * entry_price

LTCG_Date = E + 366 calendar days (informational only; used in
describe_state, never for exits).

---

## Daily State Variables

None.

---

## Daily Update Logic

None. For each session s = 1, 2, 3, ... (row s - 1 of `future_df`), check
the exit conditions at that session's close, in priority order.

---

## Exit Conditions

Evaluate in this order; exit on the first that fires. ExitDate is the
session's index label and ExitPrice is its close.

### Condition 1: Catastrophic Stop

If Close <= Stop_Level:
    EXIT at that session's close.
    Reason Tag: "CatastrophicStop"

### Condition 2: Rebalance

If the session's date d >= Next_Rebalance:
    EXIT at that session's close.
    Reason Tag: "Rebalance"

Notes:
- This is the first trading day on or after the next 15 June / 15
  December - the same day the entry rules treat as the next rebalance day.

### Condition 3: Maximum Holding Period (safety net)

If s >= 150:
    EXIT at that session's close.
    Reason Tag: "MaxHold"

Notes:
- Should never fire (a half-year is about 125 sessions); it only guards
  against a data gap.

---

## Exit Priority Order

1. CatastrophicStop
2. Rebalance
3. MaxHold

---

## Fallback

If no condition fires before `future_df` ends, return None. The backtester
then holds the trade to the end of the date range ("RangeEnd"); do not
implement that here.

---

## State Inspection (For HOLD Explanations, Not Used By The Backtester)

Also implement describe_state(entry_price, entry_date, signal_history_df,
future_df), returning a dict for the last row of `future_df` (None if
`future_df` is empty). LastClose = the last non-NaN close in `future_df`.

- TrailingStop          (Stop_Level; the stop is fixed, the key name is kept
                         for the Sell tab)
- DistanceToStopPct     ((LastClose - Stop_Level) / LastClose * 100)
- DaysHeld              (number of rows in future_df)
- DaysToMaxHold         (calendar days from the last row's date to
                         Next_Rebalance, floored at 0)
- NextRebalance         (ISO date string)
- RebalanceDue          (True if the last row's date >= Next_Rebalance)
- LastClose
- ReturnSinceEntryPct   ((LastClose - entry_price) / entry_price * 100)
- StopPctFromEntry      (-30.0)
- LTCGDate              (ISO date string of LTCG_Date)
- DaysToLTCG            (calendar days from the last row's date to
                         LTCG_Date, floored at 0)
