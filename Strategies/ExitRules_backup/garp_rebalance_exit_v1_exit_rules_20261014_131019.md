# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: GARP Rebalance Exit v1
Applies To: GARP Semi-Annual v1 (rules.md) - holds each position until the
next semi-annual rebalance day. Not meant for technical entries.
Timeframe: Daily (closing price only)

---

## Data Availability Note

Only the entry price/date and the stock's own daily OHLCV (before and after
entry) are available. No fundamentals are available to the exit - the next
rebalance re-applies the fundamental screen instead.

---

## Strategy Rationale

The paired entry buys only on a rebalance day (first trading day on or after
15 June / 15 December). This exit sells every position at the close of the
next rebalance day, so capital is free for that day's new top-25 list (the
backtester processes exits before entries, and new entries fill at the next
day's open). A stock that still qualifies is simply bought again.

A catastrophic stop at -25% from entry is the only other exit, as suggested
in the GARP research (practitioner convention, untested).

---

## Entry Reference

Entry Price: `entry_price` as passed in (the opening price on the trading
day after the signal day). `future_df` row 0 is the entry day.

---

## Pre-Trade Calculation (Computed Once at Entry)

Let E = the date of `entry_date`.

Next_Rebalance = the earliest of these dates that is strictly AFTER E:
15 June of E's year, 15 December of E's year, 15 June of the next year.

Stop_Level = 0.75 * entry_price

---

## Daily State Variables

None.

---

## Daily Update Logic

None. For each session s = 1, 2, 3, ... (row s - 1 of `future_df`), check
the exit conditions at that session's close.

---

## Exit Conditions

Evaluate in this order; exit on the first that fires. ExitDate is the
session's index label and ExitPrice is its close.

### Condition 1: Catastrophic Stop

If Close <= Stop_Level:
    EXIT at that session's close.
    Reason Tag: "CatastrophicStop"

### Condition 2: Rebalance

If the session's date >= Next_Rebalance:
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
`future_df` is empty):

- TrailingStop        (Stop_Level)
- DistanceToStopPct   ((LastClose - Stop_Level) / LastClose * 100)
- DaysHeld            (number of rows in future_df)
- DaysToMaxHold       (calendar days from the last row's date to
                       Next_Rebalance, floored at 0)
- NextRebalance       (ISO date string)
- LastClose
