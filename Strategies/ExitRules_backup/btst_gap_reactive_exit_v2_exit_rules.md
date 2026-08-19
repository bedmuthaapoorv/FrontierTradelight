# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: BTST Gap-Reactive Exit v2
Applies To: BTST Momentum v2 (any strategy with a 1-trading-day hold)
Timeframe: Daily (uses the entry day's own Open/High/Low/Close, no
intraday/tick data)

---

## Data Availability Note

Only the entry price/date and each stock's own daily OHLCV history (before
and after entry) are available. There is NO Nifty benchmark index data,
NO earnings calendar, and NO intraday/tick data available - specifically,
there is no way to know the ORDER in which the entry day's high and low
were reached, only that both happened at some point during the session.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the signal
day (the backtester's fixed entry convention). For a BTST signal, this
next-day-open entry already *is* "tomorrow" in BTST terms, so the entire
BTST cycle - entry and exit - collapses into this single entry day, same
as v1.

---

## Strategy Rationale

v1 (BTST Fixed Next-Session Exit) was unconditional: exit at the entry
day's close, always, regardless of what price did. Real BTST practice
does not work that way - traders react to the next-day open and the
day's own price action rather than blindly selling at the close: if the
stock gaps toward target, a pre-placed order lets it fill near target
instead of waiting for the close; if it gaps down past a stop level, they
exit immediately rather than riding it down further; only a genuinely
flat/inconclusive day gets held to the close. This version replicates
that decision tree using the entry day's own Open/High/Low/Close - the
target/stop levels ARE fully computable from daily OHLCV, no new data
source is required for this part.

**Deliberately optimizing for hit rate, not CAGR.** This project's other
exit strategies (e.g. the swing strategies' ATR trailing stop) size their
stop tighter than their potential upside, chasing a favorable risk:reward
because they're meant to compound returns on their own. BTST's role in
this project's strategy suite is different: it is meant to be a
high-accuracy supporting strategy, not the CAGR engine. That means this
exit is deliberately built the opposite way - a SMALL, easily-reachable
target and a WIDE stop that rarely triggers on ordinary daily noise. This
trades away a favorable risk:reward ratio (a stop-out costs more than a
target-hit pays) for a materially higher win rate, on purpose. Judge this
strategy on WinRatePct in the backtest output, not on ProfitRs or CAGR.

**What real BTST desks do that this still cannot:** react to the first
15-30 minutes of the next session specifically (this pipeline only has
the day's full-session OHLC, not intraday timing, so "did it gap up and
hold" is approximated by the day's High touching target rather than
observing the actual first-30-minute price path) - this remains an
honest, stated gap that would require a genuine intraday/minute-level
data source to close, not just a rules.md change.

---

## Pre-Trade Calculation (Computed Once at Entry)

Target_Price = EntryPrice * 1.01   (a 1% gain - deliberately small/easy to
reach, favoring hit rate over reward size)

Stop_Price = EntryPrice * 0.975    (a 2.5% loss - deliberately wide, so
ordinary intraday noise on the entry day doesn't trigger it; a stop-out
here should mean a genuinely bad day, not noise)

---

## Exit Conditions

Check exactly once: the entry day itself (there is no second day - see
Entry Reference above).

### Condition 1: Stop Hit (checked first)

If Low <= Stop_Price:
    EXIT at Stop_Price.
    Reason Tag: "Stop"

### Condition 2: Target Hit

If High >= Target_Price:
    EXIT at Target_Price.
    Reason Tag: "Target"

### Condition 3: End-of-Day Fallback (flat/inconclusive day)

If neither of the above fired:
    EXIT at the entry day's Close.
    Reason Tag: "EOD"

Notes:
- Stop is checked BEFORE target. Daily OHLCV cannot tell us which was
  touched first intraday, so on a day where both the stop and target
  levels were crossed, this deliberately assumes the worse case (stop
  first) rather than assuming the trade got the best possible outcome -
  do not change this priority order, it exists specifically to avoid
  optimistic look-ahead bias.
- Condition 3 (plain Close) only fires when the day's range never reached
  either level - this is the "flat/inconclusive day, hold to close"
  case from real BTST practice.

---

## Exit Priority Order

1. Stop   - checked first, exits at Stop_Price if the day's Low breached it
2. Target - checked second, exits at Target_Price if the day's High reached it
3. EOD    - fallback, exits at Close if neither level was reached

Only one exit tag is assigned per trade.

---

## Fallback

Not applicable - Condition 3 always fires if Conditions 1-2 don't, so
there is never a trade left open for the backtester's RangeEnd fallback
to catch.
