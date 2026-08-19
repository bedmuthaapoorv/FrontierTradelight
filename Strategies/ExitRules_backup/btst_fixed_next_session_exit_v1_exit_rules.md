# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: BTST Fixed Next-Session Exit v1
Applies To: BTST Momentum v1 (any strategy with a 1-trading-day hold)
Timeframe: Daily (closing price only, no intraday)

---

## Data Availability Note

Only the entry price/date and each stock's own daily OHLCV history (before
and after entry) are available. There is NO Nifty benchmark index data,
NO earnings calendar, and NO intraday/tick data available.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the signal
day (this is the backtester's fixed entry convention - it enters every
strategy at the next trading day's open, not intraday).

---

## Strategy Rationale

BTST is defined by a single-session hold - the entire thesis is a
close-to-open drift captured overnight, fully realized (or invalidated)
within one trading session. This is not an ATR trailing stop with a short
lookback; it is a completely different kind of exit: **unconditional,
scheduled, and unrelated to price action**.

This pipeline enters every trade at the next trading day's open after the
signal fires. For a BTST signal, that next-day-open entry already *is*
"tomorrow" in BTST terms - so "sell tomorrow" maps to exiting at the close
of that same entry day, not a day later. Holding into a second day would
turn a BTST trade into an overnight swing trade with a completely
different, unintended risk profile.

There is deliberately no trailing stop, no target, and no other
condition. Two reasons:

1. **The thesis has a hard time limit, not a price limit.** BTST doesn't
   fail because price moved against you by X% - it fails because the
   overnight drift didn't happen or reversed. Once the entry day's session
   ends, the trade is over regardless of where price is, because holding
   longer is a different bet entirely.
2. **No intraday data is available to react mid-session anyway.** Since
   this pipeline only has daily OHLCV, the earliest and only observable
   exit point after entry is that same day's close - there's no
   information available to condition an earlier or later exit on.

---

## Exit Conditions

Check exactly once: the entry day itself.

### Condition 1: End-of-Day Exit (the only condition)

EXIT at the entry day's Close - the first (and only) day in the future
data.

Reason Tag: "EOD"

Notes:
- This always fires, unconditionally, on the entry day. There is no
  scenario where this exit strategy holds past one trading day.
- Do not implement a trailing stop, fixed stop-loss, target, or any
  multi-day holding logic - all of those belong to swing-trade exit
  strategies, not BTST.

---

## Exit Priority Order

1. EOD - the only exit condition, always fires on the entry day.

---

## Fallback

Not applicable - Condition 1 always fires on the entry day itself, so
there is never a trade left open for the backtester's RangeEnd fallback to
catch.
