# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: Calendar Seasonality ATR-Based Exit v2
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

v1 of this exit (Calendar Seasonality Fixed-Horizon Exit v1) used a flat 3%
stop-loss / 4% take-profit. Diagnosing Calendar Seasonality v1's worst
drawdown (-32.9% over Feb 2024-Sep 2025) found the strategy's Market
Breadth filter was NOT the cause - tightening it (v2 of rules.md, breadth
>=55) barely reduced how many trades fired during that exact window and
left win rate just as bad, while cutting CAGR nearly in half. That ruled
out "trading in a broadly weak market" as the mechanism.

The next candidate is the exit itself: a flat 3% stop is the same absolute
distance for a quiet, low-volatility stock and a genuinely choppy one. If
that 19-month window was simply choppier than average - normal single-day
noise moving 3%+ without the eventual seasonal thesis actually failing - a
flat stop gets whipsawed out of trades a wider, volatility-adjusted stop
would have stayed in. This version replaces the fixed percentages with
ATR-based ones, so the stop/target distance scales to each stock's own
recent volatility instead of being the same 3%/4% for every stock in every
regime. Everything else (checked once per day at close, same priority
order, same 6-trading-day max hold) is unchanged from v1.

This is a genuine hypothesis, not a guaranteed fix, the same way v2 of
rules.md's breadth tightening was a reasonable hypothesis that the data
ended up rejecting - it needs to be backtested and compared before trusting
it, not assumed to work because the reasoning sounds plausible.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the signal
day.

---

## Pre-Trade Calculation (Computed Once at Entry)

ATR_Period = 14
ATR_Entry = ATR(14) calculated using price history up to and including the
signal day (the day before entry) - never using data from entry day onward.

Stop_Price = EntryPrice - (1.5 * ATR_Entry)
Target_Price = EntryPrice + (2.0 * ATR_Entry)

Notes:
- 1.5x ATR for the stop keeps this meaningfully tighter than the
  multi-week swing strategies' 2.5x ATR trailing stop (this is still a
  short 3-8 day thesis, not a multi-week trend to give wide room to), while
  no longer being a single fixed percentage regardless of the stock's own
  volatility.
- 2.0x ATR for the target gives a ~1.33:1 reward:risk ratio (2.0 / 1.5),
  slightly favorable, without being a "let winners run" trend-following
  target - this remains a short-horizon setup, not one expected to
  compound into a large multi-week winner.
- If ATR_Entry cannot be computed (insufficient history), do not open this
  trade - treat it as no exit condition available and let the caller skip
  it, rather than opening a trade with no stop-loss.
- Unlike ATR Trailing Stop, Let Winners Run v5, this stop is FIXED at
  entry, not trailing/ratcheting - a 3-8 day thesis doesn't need a
  multi-week ratchet mechanism, and a fixed level is simpler to reason
  about for a strategy already reporting Days Until Seasonal Expiry.

---

## Exit Conditions

Check ONCE PER DAY at market close, using that day's closing price.
Evaluate in this priority order; exit on the first condition that fires.

### Condition 1: ATR Stop-Loss

If Close <= Stop_Price:
    EXIT.
    Reason Tag: "SL"

---

### Condition 2: ATR Take-Profit

If Close >= Target_Price:
    EXIT.
    Reason Tag: "TP"

---

### Condition 3: Maximum Holding Period (Seasonal Window Expiry)

If TradingDaysSinceEntry >= 6:
    EXIT at that day's close.
    Reason Tag: "SeasonalExpiry"

Notes:
- Unchanged from v1 - 6 trading days deliberately extends past the ~3-4
  trading day turn-of-month window itself, and this is the primary,
  expected exit path for a trade that hits neither the stop nor the
  target, not a rare backstop.

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

Replays the same exit conditions as resolve_exit() (same Stop_Price and
Target_Price, computed identically from the ATR at entry) but for a trade
that has NOT exited - returns the exit logic's internal state as of the
last available day instead of an exit event.

Return a dict with:
- StopPrice            (as computed in Pre-Trade Calculation)
- TargetPrice          (as computed in Pre-Trade Calculation)
- LastClose            (most recent close in future_df)
- DistanceToStopPct    ((LastClose - StopPrice) / LastClose * 100)
- DistanceToTargetPct  ((TargetPrice - LastClose) / LastClose * 100)
- DaysHeld             (trading days since entry)
- DaysToSeasonalExpiry (6 - DaysHeld, floored at 0)

Return None if state cannot be computed (e.g. insufficient history).

The backtester never calls this - only the live Sell tab does, to build a
richer explanation for holds.
