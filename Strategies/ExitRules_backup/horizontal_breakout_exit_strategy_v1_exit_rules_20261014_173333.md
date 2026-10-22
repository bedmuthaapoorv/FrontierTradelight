# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: Horizontal Breakout Exit Strategy v1
Applies To: Horizontal Breakout Momentum (O'Neil Volume) (rules.md)
specifically - every threshold below (the 10-day failed-breakout window,
the 8% hard stop, the 3.0x/4.0x ATR trailing multipliers, the 20%-in-15-
days big-winner override, the 90-day MaxHold) is sized for THIS entry's
setup (a breakout to a new 20-day high on a volume surge, 1-90 day
intended hold) and its own stated risk/reward shape. Do NOT assume these
numbers transfer to a differently-shaped entry (e.g. a pullback-to-
support entry like Trendline Bounce v1, which already has its own paired
exit strategy) without re-validating via this project's usual N-sweep +
multi-slot backtest protocol.
Timeframe: Daily (closing price only, no intraday)

---

## Data Availability Note

Only the entry price/date and each stock's own daily OHLCV history (before
and after entry) are available. There is NO Nifty benchmark index data and
NO earnings calendar available - do not condition any exit logic on either.
Every rule below must be computable from OHLCV alone.

---

## Strategy Rationale

Built from a dedicated research pass (see
`research_notes/Horizontal breakout exit rules/` and
`reports/Horizontal breakout exit rules.md` in the project root) across
four angles: O'Neil/CANSLIM sell discipline, ATR/Chandelier-style
volatility trailing stops, failed-breakout fast-exit detection, and
profit-taking vs. let-winners-run mechanics. The design below is a
layered pipeline, not a single rule, because the research consistently
showed these are separate problems with separate best-evidenced
solutions - a fast structural check for early failures, a hard percentage
backstop against catastrophic loss, a volatility-scaled trailing stop to
manage winners, and a "big winner" override so a proven trend isn't
clipped too early:

1. **Failed Breakout (structural, days 1-10):** Bulkowski's pattern
   statistics show ordinary post-breakout throwbacks (price dipping back
   toward the breakout level without truly failing) resolve within 3-10
   days in the large majority of cases (53-66% of breakouts throw back at
   all). A close that's still meaningfully below the breakout pivot
   inside that same window is a materially different, and much more
   likely genuinely-failed, signal - so this project cuts it fast rather
   than waiting for the wider ATR trailing stop to eventually catch it.

2. **Hard Stop-Loss (O'Neil 7-8% rule):** The single best-evidenced,
   most specific number found across all four research angles - William
   O'Neil's rule of capping every breakout trade's loss at 7-8% from the
   actual entry price, never from a moving average or the pivot. The
   rationale (recovering from an 8% loss needs an 8.7% gain; recovering
   from a 25% loss needs a 33% gain) is pure loss-recovery asymmetry, not
   specific to any one market. This project uses 8% (the looser end of
   O'Neil's 7-8% band) since Rule 6 of the entry already screens out
   stocks that have run up more than 25% in 20 days, so entries here tend
   to be earlier-stage than a fully mature O'Neil pivot buy.

3. **ATR Trailing Stop (Chandelier-style, ratchets up only):** Once a
   trade is not an early failure and hasn't hit the hard stop, this
   project lets it run under a volatility-scaled trailing stop rather
   than a fixed target - a 105,708-trade systematic backtest (Setup4Alpha,
   cited in the profit-taking research notes) found fixed-percentage
   profit targets were the WORST-performing exit style for trend-
   following equity trades, while trailing/calendar-style exits were the
   best. 3.0x ATR sits in the middle of the practitioner-consensus range
   (2x-4x) for swing/position trades (vs. 1.5x-2x for day trading) found
   across Chandelier Exit, Turtle Trading, and SuperTrend sources.

4. **Big-Winner Override (O'Neil's 8-week-hold rule, adapted):** O'Neil's
   rule states that a stock gaining 20%+ within 3 weeks of its breakout
   should be held a MINIMUM of 8 weeks regardless of normal sell signals,
   because these disproportionately become the market's biggest winners.
   This project cannot suspend the risk-management exits entirely (that
   would remove downside protection from what might still reverse), so
   it implements the same intent mechanically: widen the ATR trailing
   multiplier from 3.0x to 4.0x once a trade has gained 20%+ within its
   first 15 trading days (~3 weeks), giving a confirmed big winner
   meaningfully more room to breathe instead of clipping it with the
   same tight stop used on an ordinary trade.

5. **Maximum Holding Period:** Set to 90 trading days, matching this
   entry's own stated "Trend Trade (1-90 Days)" holding period in
   rules.md exactly (unlike the Mean Reversion exit strategy's 90-day
   backstop, which was a deliberate mismatch against that entry's shorter
   5-40 day horizon - here the two are meant to agree).

No fixed take-profit exists anywhere in this exit strategy, on purpose -
this matches rules.md's own v5 rationale (a trend-following entry's edge
comes from a few large winners paying for many small losers, and a fixed
cap on gains destroys that asymmetry) and the profit-taking research's
finding above. Re-run this project's usual N-sweep + multi-slot backtest
protocol against the live entry before trusting any of these five
threshold numbers blindly - they are research-grounded starting points,
not values already validated against this specific backtester.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the
signal day.

---

## Pre-Trade Calculation (Computed Once at Entry)

ATR_Period = 14
ATR_Entry = ATR(14) calculated using price history up to and including the
signal day (the day before entry) - never using data from entry day onward.

Pivot = Highest_Close(20) calculated using price history up to and
including the signal day (the same 20-day-high breakout level Rule 5 of
rules.md required Close to be within 2% of on the signal day).

Initial_SL = EntryPrice - (3.0 * ATR_Entry)

Notes:
- If ATR_Entry or Pivot cannot be computed (insufficient history), do not
  open this trade - treat it as no exit condition available and let the
  caller skip it, rather than opening a trade with no stop-loss.
- Pivot is fixed at entry and never recalculated during the trade - it
  represents the specific breakout level this trade is betting held as
  support, not a rolling 20-day high recomputed daily (which would drift
  upward as the trade itself makes new highs).

---

## Daily State Variables

Trailing_SL     : Starts at Initial_SL. Updated daily. Never decreases.
Highest_Close   : Peak closing price since entry. Starts at EntryPrice.
ATR_Multiplier  : Starts at 3.0. Widens (once, irreversibly) to 4.0 if the
                  Big-Winner Override below fires.

---

## Daily Update Logic

Run at market close, BEFORE checking exit conditions, using only OHLCV data
available up to and including that day.

### Step 1: Update Highest Close

If Close > Highest_Close:
    Highest_Close = Close

### Step 2: Check Big-Winner Override (Widen ATR Multiplier)

If TradingDaysSinceEntry <= 15 AND Close >= 1.20 * EntryPrice:
    ATR_Multiplier = 4.0

Notes:
- Checked every day up through day 15, but once it fires, ATR_Multiplier
  stays at 4.0 for the rest of the trade even if price later dips back
  below the 20% threshold - the override is about recognizing a trade
  that PROVED itself early, not about the current day's exact gain.
- If the 20%-within-15-days condition never fires, ATR_Multiplier simply
  stays at 3.0 for the trade's entire life - this is the ordinary case,
  not a penalty.

### Step 3: Ratchet Trailing Stop Upward Only

Recompute ATR(14) using price history up to and including today.

Candidate_SL = Highest_Close - (ATR_Multiplier * ATR_Today)

If Candidate_SL > Trailing_SL:
    Trailing_SL = Candidate_SL
Else:
    Trailing_SL remains unchanged.

Notes:
- The stop only ever moves up, never down, regardless of what today's ATR
  or ATR_Multiplier computes to. This locks in gains progressively as the
  trade moves in profit and never gives back protection already earned.
- Widening ATR_Multiplier from 3.0 to 4.0 (Step 2) can only ever raise or
  hold Candidate_SL relative to what a stale 3.0x figure would have given
  on a day where Highest_Close hasn't moved - it cannot suddenly lower an
  already-ratcheted Trailing_SL, because of the "never decreases" rule
  here in Step 3.

---

## Exit Conditions

Check ONCE PER DAY at market close, AFTER the daily update logic above runs.
Evaluate in this priority order; exit on the first condition that fires.

### Condition 1: Failed Breakout

If TradingDaysSinceEntry <= 10 AND Close < (0.98 * Pivot):
    EXIT at that day's close.
    Reason Tag: "FailedBreakout"

Notes:
- Mirrors entry Rule 5's own 2% breakout-proximity buffer (Close >= 0.98 *
  Highest_Close(20)) so the exit uses the same tolerance the entry used to
  define "at the breakout level" in the first place - a symmetric band,
  not an arbitrarily different one.
- Only checked in the first 10 trading days, matching the research's 3-10
  day throwback-resolution window - a stock still meaningfully below its
  own breakout pivot 10 days on has moved past an ordinary throwback and
  into a genuine failed-breakout pattern.
- After day 10, a stock trading below Pivot is no longer flagged by this
  condition specifically - by then, either the Hard Stop-Loss or the ATR
  Trailing Stop below will have already caught (or will soon catch) any
  trade that's genuinely deteriorating, without this rule needing to
  double-fire on the same underlying weakness.

---

### Condition 2: Hard Stop-Loss (O'Neil 7-8% Rule)

If Close <= (0.92 * EntryPrice):
    EXIT at that day's close.
    Reason Tag: "HardStop"

Notes:
- Active for the entire trade, not just the first 10 days - this is the
  absolute backstop against a slow bleed that never triggers Condition 1
  (e.g. Pivot sits below EntryPrice, so a decline can pass Condition 1's
  Pivot-relative check while still being a meaningful loss in its own
  right).
- 8% from EntryPrice specifically (not from Highest_Close, not from a
  moving average) - this is O'Neil's rule exactly as researched: the
  measurement point is the actual entry fill, because the rule exists to
  cap realized loss on THIS trade, not to protect unrealized gains (that
  is the Trailing Stop's job, Condition 3 below).

---

### Condition 3: ATR Trailing Stop

If Close <= Trailing_SL:
    EXIT at that day's close.
    Reason Tag: "TSL"

Notes:
- Trailing_SL already incorporates whichever ATR_Multiplier (3.0 or the
  widened 4.0) applies as of today, per the Daily Update Logic above.
- No fixed take-profit exists in this strategy - see the Strategy
  Rationale section for why. The ONLY exit for a winning trade that
  survives Conditions 1 and 2 is this trailing stop eventually giving
  back its multiplier's worth of ATR from the peak.

---

### Condition 4: Maximum Holding Period

If TradingDaysSinceEntry >= 90:
    EXIT at that day's close.
    Reason Tag: "MaxHold"

Notes:
- Matches rules.md's own stated "Trend Trade (1-90 Days)" holding period
  for this entry exactly - unlike the Mean Reversion exit strategy's
  90-day backstop (a deliberate mismatch there against that entry's
  shorter 5-40 day horizon), here the exit's outer bound and the entry's
  own stated horizon are meant to agree.
- Expect this to rarely fire in practice, same as observed for the Mean
  Reversion exit strategy's own 90-day backstop - the Trailing Stop
  (Condition 3) should close the large majority of trades well before
  reaching this backstop. Re-check this assumption against this specific
  entry's actual backtest results rather than assuming it transfers.

---

## Exit Priority Order

1. FailedBreakout  <- checked first each day, only within the first 10 days
2. HardStop        <- 8% loss backstop, active for the whole trade
3. TSL             <- ATR trailing stop (3.0x, or 4.0x after a big-winner override)
4. MaxHold         <- final backstop at 90 trading days

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

This replays the same daily update logic as resolve_exit() (same
Highest_Close tracking, same Big-Winner Override check, same Trailing_SL
ratchet) but for a trade that has NOT exited - it returns the exit logic's
internal state as of the last available day instead of an exit event, so
sell_screener.py can explain *why* a holding is still a HOLD (how far price
is from the trailing stop, how many days until MaxHold, whether the
big-winner override has already widened its stop) rather than just saying
"not met yet."

Return a dict with:
- TrailingStop         (current trailing stop level)
- ATRMultiplier         (3.0 or 4.0, whichever currently applies)
- HighestClose          (peak closing price tracked since entry)
- LastClose             (most recent close in future_df)
- DistanceToStopPct     ((LastClose - TrailingStop) / LastClose * 100)
- DistanceToHardStopPct ((LastClose - (0.92 * entry_price)) / LastClose * 100)
- DaysHeld              (trading days since entry)
- DaysToMaxHold         (90 - DaysHeld, floored at 0)
- BigWinnerOverrideActive (true if ATRMultiplier is currently 4.0)
- AtRiskOfFailedBreakout  (true if DaysHeld <= 10 AND LastClose is within
                          2% above Pivot - i.e. still inside the Failed
                          Breakout condition's window and close to
                          triggering it, so the Sell tab can warn before
                          it actually fires, not just report it after
                          the fact)

Return None if state cannot be computed (e.g. insufficient history).

The backtester never calls this - only the live Sell tab does, to build a
richer explanation for holds.
