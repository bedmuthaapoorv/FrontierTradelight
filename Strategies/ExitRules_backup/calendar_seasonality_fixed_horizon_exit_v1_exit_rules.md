# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: Calendar Seasonality Fixed-Horizon Exit v1
Applies To: Any trade opened by the backtester
Timeframe: Daily (closing price only, no intraday)

---

## Data Availability Note

Only the entry price/date and each stock's own daily OHLCV history (before
and after entry) are available. There is NO Nifty benchmark index data and
NO earnings calendar available - do not condition any exit logic on either.
Every rule below must be computable from OHLCV alone.

---

## Strategy Rationale

Paired with Calendar Seasonality v1 (rules.md), whose entire thesis is a
~3-8 trading day window around the turn of the month - once that window has
passed, the reason for being in the trade has expired, regardless of how
the position is doing. A long-horizon exit like ATR Trailing Stop, Let
Winners Run v5 (built for multi-week trend-following) would hold positions
for months past that point, which doesn't match this entry's actual edge.

This uses a FIXED (non-trailing) stop-loss and take-profit, tighter than
the swing/trend strategies' typical 2.5x ATR stop - the holding period is
short enough that a single bad day matters more, and there's no multi-week
trend to protect with a ratchet. A modest, not-overly-generous take-profit
(4%, smaller than the target-free "let winners run" philosophy used
elsewhere in this project) reflects that this is a short statistical
tailwind, not a trend-following setup expected to compound into a large
winner - the priority is realizing the small, short-lived edge before it
decays, not maximizing a single trade's upside.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the signal
day.

---

## Exit Conditions

Check ONCE PER DAY at market close, using that day's closing price.
Evaluate in this priority order; exit on the first condition that fires.

### Condition 1: Stop-Loss

Close <= EntryPrice * (1 - StopLossPct / 100)

StopLossPct = 3

Reason Tag: "SL"

Notes:
- Tighter than the swing strategies' ~2.5x ATR stop (which typically works
  out closer to 5-8% for these price ranges) - a short-horizon trade has no
  time to recover from a large adverse move the way a multi-week trend
  trade might.

---

### Condition 2: Take-Profit

Close >= EntryPrice * (1 + TakeProfitPct / 100)

TakeProfitPct = 4

Reason Tag: "TP"

Notes:
- Modest by design. This is not a trend-following exit meant to let a
  winner run for weeks - the seasonal edge this strategy trades is small
  and short-lived, so the right response to an early, fast move in its
  favor is to realize it, not to hold out for more.

---

### Condition 3: Maximum Holding Period (Seasonal Window Expiry)

If TradingDaysSinceEntry >= 6:
    EXIT at that day's close.
    Reason Tag: "SeasonalExpiry"

Notes:
- 6 trading days deliberately extends past the ~3-4 trading day
  turn-of-month window itself (see rules.md Rule 3), giving the position a
  short runway beyond entry without holding it long enough that the
  original seasonal rationale has clearly expired. This is the primary,
  expected exit path for a trade that hits neither the stop nor the
  target - not a rare backstop the way MaxHold is in the longer-horizon
  swing exit strategies.

---

## Exit Priority Order

1. SL              <- checked first each day
2. TP              <- checked second
3. SeasonalExpiry   <- backstop once the seasonal window has clearly passed

Only one exit tag is assigned per trade.

---

## Fallback

If no condition above triggers before the available data ends, do not exit -
the backtester itself force-closes any still-open trade at the last
available close, tagged "RangeEnd". Exit strategies never need to implement
this fallback themselves.

---

## State Inspection (For HOLD Explanations, Not Used By The Backtester)

In addition to resolve_exit(), also implement:

describe_state(entry_price, entry_date, signal_history_df, future_df)

Replays the same exit conditions as resolve_exit() (same stop/target/
holding-period thresholds) but for a trade that has NOT exited - returns
the exit logic's internal state as of the last available day instead of an
exit event, so sell_screener.py can explain *why* a holding is still a HOLD
rather than just saying "not met yet."

Return a dict with:
- StopLossPrice       (EntryPrice * (1 - StopLossPct / 100))
- TakeProfitPrice     (EntryPrice * (1 + TakeProfitPct / 100))
- LastClose           (most recent close in future_df)
- DistanceToStopPct   ((LastClose - StopLossPrice) / LastClose * 100)
- DistanceToTargetPct ((TakeProfitPrice - LastClose) / LastClose * 100)
- DaysHeld            (trading days since entry)
- DaysToSeasonalExpiry (6 - DaysHeld, floored at 0)

Return None if state cannot be computed (e.g. insufficient history).

The backtester never calls this - only the live Sell tab does, to build a
richer explanation for holds.
