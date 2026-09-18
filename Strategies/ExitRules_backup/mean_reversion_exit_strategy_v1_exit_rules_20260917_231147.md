# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: Mean Reversion Exit Strategy v1
Applies To: Mean Reversion Strategy v5 (rules.md) specifically - the
30-day early-failure cut (see the section below) was validated against
that entry's actual trade pattern (bounce-off-trendline-support swings)
and its capital-recycling benefit was measured using that entry's
signal frequency. Do NOT assume this same cutoff transfers to a
differently-shaped entry (e.g. Breakout Momentum's trend-continuation
trades) without re-validating - re-run the same protocol (N-sweep +
multi-slot check) against whichever entry is actually live before
trusting these numbers for it.
Timeframe: Daily (closing price only, no intraday)

---

## Data Availability Note

Only the entry price/date and each stock's own daily OHLCV history (before
and after entry) are available. There is NO Nifty benchmark index data and
NO earnings calendar available - do not condition any exit logic on either.
Every rule below must be computable from OHLCV alone.

---

## Mean Reversion Exit Strategy v1: Early-Failure Cut at 30 Days

This is an ATR trailing-stop exit (no fixed profit target - winners run
until the trailing stop gives back 2.5x ATR from the peak) with one
addition: a 30-day early-failure cut for trades still underwater. A
5-day version of this cut was tested first and made things dramatically
worse (196 trades cut at day 5 for still being red averaged -1.89%,
vs -0.21% if left alone) - the "34% recovery chance after 5 flat days"
statistic that motivated it comes from short-horizon mean-reversion
research (next-day/RSI(2)-style systems) and doesn't transfer to this
multi-week swing strategy. Re-tested a sweep of cutoffs (10/15/20/30/
40/45/60 trading days, same "still below entry price" trigger) on the
same benchmark range and entry rules:

| Cutoff | CAGR (10 slots) |
|---|---|
| 10 days | 16.88% (worse than no cut) |
| 15 days | 17.48% (worse) |
| 20 days | 18.36% (worse) |
| **30 days** | **20.26% (beats no-cut baseline's 19.38%)** |
| 40 days | 19.70% (converging back to baseline) |
| 45-60 days | ~19.4% (cut rarely/never fires - equivalent to no cut) |

30 trading days is a genuine peak, not noise - the curve is monotonic on
both sides of it. Re-tested at 3 and 6 concurrent position slots (not
just the benchmark's 10) to check the finding wasn't an artifact of one
specific slot count:

| Slots | No-cut CAGR | 30-day-cut CAGR | Improvement |
|---|---|---|---|
| 3 | 10.87% | 11.89% | +1.0 pt |
| 6 | 18.81% | 21.06% | +2.25 pt |
| 10 | 19.38% | 20.26% | +0.9 pt |

Held (and was strongest) at every slot count tested.

Important nuance - WHY this helps is not what it looks like:

Same-trade comparison of the 22 trades the 30-day cut fires on (10-slot
run): left alone, those exact trades averaged +2.31%; cut at day 30,
they averaged -1.46%. The cut trades are NOT rescued by cutting them -
per-trade, cutting is strictly worse. The portfolio-level gain comes
entirely from capital recycling: this backtester runs a capital-
constrained portfolio (a fixed number of position slots; a signal that
fires with no free slot is skipped, not sized down). Cutting 22 stagnant
trades ~60 days sooner than they'd otherwise resolve (via the 90-day
MaxHold or eventually the trailing stop) freed up capital that got
redeployed into signals that would otherwise have been skipped - 10-slot
run funded 257 trades with the cut vs 253 without, from the same 496 raw
signals; 6-slot run funded 171 vs 167.

This means the 30-day cutoff's value is tied to running a capital-
constrained portfolio with more signals than slots most of the time - it
is a capital-efficiency mechanism, not evidence that trades flat after
30 days are individually more likely to fail. If this project ever moves
to sizing every signal (no slot limit) rather than skipping unfunded
ones, re-validate this cutoff rather than assuming it still helps - the
mechanism it relies on won't exist in that setup.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the
signal day.

---

## Pre-Trade Calculation (Computed Once at Entry)

ATR_Period = 14
ATR_Entry = ATR(14) calculated using price history up to and including the
signal day (the day before entry) - never using data from entry day onward.

Initial_SL = EntryPrice - (2.5 * ATR_Entry)

Notes:
- If ATR_Entry cannot be computed (insufficient history), do not open this
  trade - treat it as no exit condition available and let the caller skip
  it, rather than opening a trade with no stop-loss.

---

## Daily State Variables

Trailing_SL   : Starts at Initial_SL. Updated daily. Never decreases.
Highest_Close : Peak closing price since entry. Starts at EntryPrice.

---

## Daily Update Logic

Run at market close, BEFORE checking exit conditions, using only OHLCV data
available up to and including that day.

### Step 1: Update Highest Close

If Close > Highest_Close:
    Highest_Close = Close

### Step 2: Ratchet Trailing Stop Upward Only

Recompute ATR(14) using price history up to and including today.

Candidate_SL = Highest_Close - (2.5 * ATR_Today)

If Candidate_SL > Trailing_SL:
    Trailing_SL = Candidate_SL
Else:
    Trailing_SL remains unchanged.

Notes:
- The stop only ever moves up, never down, regardless of what today's ATR
  computes to. This locks in gains progressively as the trade moves in
  profit and never gives back protection already earned.

---

## Exit Conditions

Check ONCE PER DAY at market close, AFTER the daily update logic above runs.
Evaluate in this priority order; exit on the first condition that fires.

### Condition 1: Trailing Stop-Loss

If Close <= Trailing_SL:
    EXIT.
    Reason Tag: "TSL"

---

### Condition 2: Early-Failure Cut

If TradingDaysSinceEntry >= 30 AND Close < EntryPrice:
    EXIT at that day's close.
    Reason Tag: "EarlyFailure"

Notes:
- See the "v6: Early-Failure Cut, Revisited at 30 Days" section above for
  the full backtest evidence and the important caveat about WHY this
  helps (portfolio-level capital recycling in a slot-constrained
  backtest, not individual trade quality - cutting these specific trades
  is worse per-trade than leaving them alone).
- Checks only the CURRENT day's close against EntryPrice - a trade that
  was red on day 25 but has recovered to breakeven-or-better by day 30
  is unaffected; this only fires if it's still actually underwater at
  the 30-day mark.
- This sits ABOVE MaxHold in priority only because 30 < 90 - a trade
  still red at day 30 will always hit this before it could ever reach
  the day-90 backstop. Both remain distinct, real conditions: a trade
  that's flat/underwater cuts here at 30 days; a trade that's been
  sitting in slight profit without triggering the trailing stop runs on
  to the day-90 MaxHold instead.

---

### Condition 3: Maximum Holding Period

If TradingDaysSinceEntry >= 90:
    EXIT at that day's close.
    Reason Tag: "MaxHold"

Notes:
- NO fixed take-profit in this version (v5). Trend-following/momentum
  strategies earn their edge from a small number of large winners paying
  for many small losers - capping gains at a fixed percentage destroys
  that asymmetry. The ONLY exit for a winning trade is the trailing stop
  itself giving back 2.5x ATR from the peak; there is no ceiling on how
  far a trade can run before that happens.
- Extended from 30 to 90 trading days (~4.5 months) versus earlier
  versions. A real trend needs months, not weeks, to develop into a large
  winner - a 30-day cap was forcing an exit right as a genuine trend might
  start to compound. This is a real backstop against truly stagnant
  capital, not a target.
- Despite rules.md's entry describing itself as a "Swing Trade (5-40
  Days)" strategy, empirically almost no trade ever reaches this 90-day
  backstop either way (5 of 441 in the benchmark backtest) - the trailing
  stop (and now the 30-day early-failure cut above it) is what actually
  closes nearly every trade, well before 90 days in practice. Don't
  assume the stated 5-40 day horizon means this backstop itself should
  be shortened to match it - it's a rarely-hit safety net, not the
  primary exit mechanism.

---

## Exit Priority Order

1. TSL           <- checked first each day
2. EarlyFailure   <- cut at day 30 if still below entry price
3. MaxHold        <- final backstop at 90 trading days

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

This replays the same daily update logic as resolve_exit() (same Trailing_SL
ratchet, same Highest_Close tracking) but for a trade that has NOT exited -
it returns the exit logic's internal state as of the last available day
instead of an exit event, so sell_screener.py can explain *why* a holding is
still a HOLD (how far price is from the trailing stop, how many days until
MaxHold) rather than just saying "not met yet."

Return a dict with:
- TrailingStop        (current trailing stop level)
- HighestClose         (peak closing price tracked since entry)
- LastClose            (most recent close in future_df)
- DistanceToStopPct    ((LastClose - TrailingStop) / LastClose * 100)
- DaysHeld             (trading days since entry)
- DaysToMaxHold        (90 - DaysHeld, floored at 0)
- AtRiskOfEarlyFailure (true if DaysHeld >= 25 AND LastClose < EntryPrice -
                        i.e. within 5 days of the day-30 early-failure
                        cut and still underwater, so the Sell tab can
                        warn before it actually fires, not just report it
                        after the fact)

Return None if state cannot be computed (e.g. insufficient history).

The backtester never calls this - only the live Sell tab does, to build a
richer explanation for holds.
