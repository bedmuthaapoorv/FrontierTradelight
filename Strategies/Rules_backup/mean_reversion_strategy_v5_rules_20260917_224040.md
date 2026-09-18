# Stock Selection Rules

## Strategy Metadata

Strategy Name: Mean Reversion Strategy v5
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: Swing Trade (5-40 Days)

---

## Data Availability Note

Only the following data is available to this strategy: each stock's own
daily OHLCV (open/high/low/close/volume) history, a `SectorRank` value
(1 = best-performing sector by recent average return, higher = weaker), and
a `MarketBreadth` value (0-100: percentage of the entire universe currently
trading above its own 50-day moving average) - both computed once per day
from OHLCV data across the universe. There is NO Nifty benchmark index
data and NO earnings calendar available. Every rule below must be
computable from OHLCV + SectorRank + MarketBreadth alone.

---

## Strategy Rationale

v1 detected a trendline using a single rigid 100-day window, required an
exact fit (any single point could invalidate the whole line), and
disqualified a line forever if price ever broke below it at any point in
the lookback - even if price later reclaimed it. This missed trendlines
that were only visible "zooming out" to a longer window, and treated a
resolved break-and-reclaim the same as an active breakdown.

v2 fixes this with three changes, each targeting one specific failure:

1. **Multiple lookback windows, not one.** Tries 250/150/100/60 trading
   days (longest first) and keeps whichever window reveals a qualifying
   line with the most touches - a trendline only visible over 6+ months
   is no longer invisible just because a rigid 100-day box happened not
   to contain it.
2. **Robust, outlier-tolerant fitting.** Instead of requiring every pivot
   to lie exactly on the line, iteratively drops up to ~20% of pivots
   that sit egregiously below the candidate line before finalizing the
   fit - the same way a chartist mentally discounts one outlier wick
   instead of throwing out an otherwise-clean trendline.
3. **Current-structure-only breakdown check.** Only the most recent 3
   trading days are checked for a breakdown, not the entire lookback - a
   break from weeks ago that price has since reclaimed no longer
   permanently disqualifies the line.

v2's 3-year backtest returned +15.88% total / +5.06%/yr CAGR, but a
Deep-Dive-style year-by-year and leave-one-year-out analysis of that
backtest showed the return was fragile and the risk was real: excluding
2024 alone flips the whole result from +5.06% CAGR to -3.13% CAGR (one
year carried the entire strategy), and the max drawdown was -20.6%,
concentrated in a sustained slide from Aug 2024 through the end of the
backtest - 139 trades were entered during that window, only a 30.2% win
rate, and 133 of those 139 (96%) exited via the trailing stop rather than
working. That's the signature of the entry admitting weaker setups than
it should, not an exit-side problem.

v3 responds by tightening the trendline quality bar - the two changes in
Rule 3 step 4 (outlier tolerance cut from 20% to 10% of pivots) and step
6 (minimum touches raised from 3 to 4) - trading some of v2's broader
detection for higher-conviction lines, in direct response to that
drawdown evidence. Everything else (bounce confirmation trigger, RSI
pullback zone, trend context, sector/breadth filters) carries over
unchanged - the core "passive filter + active trigger" design already
proved out; only the trendline detection's tolerance for weak lines
needed tightening.

v4 fixes Rule 1's liquidity floor, which was a flat `MA(Volume, 20) >=
100000` share-count threshold carried over unexamined since v1, with no
justification ever recorded for the number (unlike, say, Rule 8's
MarketBreadth cutoff). A raw share count is the wrong unit for a liquidity
floor: 100,000 shares/day means very different things for a Rs.50 stock
and a Rs.5,000 stock, even though both would pass the identical threshold.
Replaced with a turnover floor (MA(Volume * Close, 20), i.e. average daily
traded value in Rupees) - see Rule 1 for the actual number and how it was
derived from this project's cached universe data, not assumed. No other
rule changed from v3.

v5 is a rename only, no rule changed from v4. "Trendline Bounce
Confirmation" described the entry's mechanism (find a trendline, confirm
a bounce off it) but not its underlying character: Rule 5's RSI 35-55
band, Rule 6's cap on chasing a bounce that's already run, and the
matching exit strategy's fixed target at the prior swing high are all
mean-reversion patterns, not trend-continuation ones - the entry only
takes this mean-reversion-style bounce when Rule 2's uptrend context is
already confirmed, so this is a trend-following pullback strategy using
a mean-reversion trigger, not unconditional/countertrend mean reversion.
"Mean Reversion Strategy" names it by that character instead of by
mechanism.

---

## Mandatory Filters

All rules below MUST pass.

---

### Rule 1: Minimum Liquidity Floor (v4 - turnover-based)

Description:
Reject illiquid stocks so signals are meaningful and exits are executable
without slippage.

Condition:

MA(Volume * Close, 20) >= 50000000
AND
Close >= 50

Where:
MA(Volume * Close, 20) = the 20-day average of daily traded value in
Rupees (each day's Volume times that day's Close, averaged over the last
20 trading days) - i.e. turnover, not raw share count.

Notes:
- v3 and earlier used a flat `MA(Volume, 20) >= 100000` share-count floor,
  unexamined since v1 with no recorded justification for the number.
  Turnover (Volume x Close), not raw share count, is what actually
  determines whether a position can be entered/exited without slippage -
  a flat share-count floor treats a Rs.50 stock trading 200k shares/day
  the same as a Rs.5,000 stock trading 200k shares/day, even though the
  second one has 100x the actual Rupee liquidity.
- Rs. 5 crore/day (50000000) was checked against this project's actual
  cached universe data, not assumed: even the weakest 5% of stocks by
  turnover clear roughly Rs. 110 crore/day in that data, ~20x this floor -
  consistent with the original share-count version's intent ("should
  rarely bind, it's a safety floor"), just expressed in units that mean
  the same thing across different price levels.
- Close >= 50 is kept as a separate floor against low-priced/penny-stock
  noise, not a liquidity proxy - a stock can clear the turnover bar above
  while still being a sub-Rs.50 stock with erratic tick-level behavior.

---

### Rule 2: Uptrend Context

Description:
A pullback to support only means something if the stock is actually in an
uptrend. Requires price above a rising medium-term average.

Condition:

Close > MA(100)
AND
MA(100) > MA(100)[-10]

Notes:
- MA(100)[-10] means the 100-day moving average's value 10 trading days
  ago - requiring the current MA to be higher than that confirms the
  average itself is rising, not flat or falling.

---

### Rule 3: Ascending Trendline Detection

Description:
Find a genuine rising support trendline under the stock's recent price
action - not a placeholder, and not an overly rigid geometric search
either. A real trendline is often only visible when you zoom out, and a
single exact-fit line that any one pullback can invalidate is not how a
chartist reads a chart. This rule requires: trying multiple lookback
windows (not committing to one arbitrary window), a fit that tolerates a
minority of points as noise instead of requiring every point to lie
exactly on the line, and a breakdown check based on CURRENT structure
(is the line broken right now?) rather than "was it ever broken at any
point in the lookback." This is the core, most failure-prone rule in this
strategy: implement the actual algorithm below exactly, do not substitute
a fixed/hardcoded distance value for any part of it.

Algorithm (implement exactly):

1. Try lookback windows of 250, 150, 100, and 60 trading days, longest
   first (skip any window longer than the available history). For each
   window, run steps 2-7 below; keep whichever window produces a
   qualifying line with the most touches (a longer window that reveals a
   trendline invisible in a shorter one should win).

2. Within the window, find pivot lows: a day is a pivot low if its `low`
   is less than or equal to the `low` of the 4 trading days before AND
   the 4 trading days after it (scipy.signal.argrelextrema with order=4,
   or equivalent standard local-extrema detection). Skip this window if
   fewer than 3 pivot lows are found.

3. Fit an initial line (slope, intercept) via ordinary least-squares
   regression (day-index vs. low price) using ALL pivot lows in the
   window as points.

4. Robust refinement (tolerate a small amount of noise, not a lax fit):
   repeat up to `ceil(0.1 * number_of_pivots)` times - find the pivot low
   with the most negative residual (furthest BELOW the current line). If
   that residual is worse than -1.0x ATR(14), drop that pivot and refit
   the line on the remaining pivots; otherwise stop early (no more
   meaningful outliers). This lets a single anomalous dip get excluded
   rather than distorting or invalidating the whole line, the same way a
   chartist mentally discounts one outlier wick - but only one, not up to
   a fifth of all the pivots found. (v2 allowed dropping up to 20% of
   pivots here; backtesting showed this was letting through lines with
   real conviction problems - most of the resulting trades got stopped
   out quickly rather than working. 10% keeps the "tolerate one outlier"
   benefit without diluting the line's overall quality.)

5. Discard this window if the final slope is non-positive (must be
   ascending).

6. Count how many pivot lows (from the original full set in step 2, not
   just the ones kept after step 4's trimming) lie within 1.0x ATR(14) of
   the final line's projected value at their day-index - these are the
   line's "touches." Require at least 4 (raised from v2's 3 - a fourth
   confirmed touch is meaningfully more evidence of genuine, repeated
   support than three; this is a general tightening in response to v2's
   Deep Dive analysis showing a long, mostly-stopped-out drawdown, not a
   claim that 3-touch lines specifically were the failures - that
   per-touch breakdown wasn't measured). If fewer than 4, this window
   doesn't qualify.

7. Breakdown check - CURRENT structure only, not lifetime history: look
   only at the most recent 3 trading days in the window (i.e. up to and
   including today). If ALL 3 of those days' closes are more than 1.5x
   ATR(14) below the line's projected value on their respective day, the
   trendline is considered currently broken and this window doesn't
   qualify. A breakdown earlier in the window that price has since
   reclaimed does NOT disqualify the line - only an active, ongoing break
   does.

Condition:

TrendlineTouches >= 3
AND
TrendlineSlope > 0
AND
NOT CurrentlyBrokenBelowLine(last 3 trading days, tolerance = 1.5x ATR(14))

Notes:
- ATR(14) should be computed once (today's value) and used as the unit of
  distance throughout steps 4, 6, and 7 - not recomputed per pivot or per
  window.
- If none of the four windows produce a qualifying line, this rule fails
  for the stock - it has no ascending trendline on any timeframe tried.
- The overall insufficient-data check at the top of the function must be
  `if len(df) < 60`, NOT `< 250`. 250 is only the longest of the four
  window sizes tried, not a blanket minimum - a stock with, say, 120 days
  of history should still be evaluated (it just won't be able to try the
  250 or 150 windows, only 100 and 60). Requiring 250 days unconditionally
  would incorrectly reject every stock that can only use the shorter
  fallback windows, defeating the entire point of trying multiple windows.
- Coordinate system: if you slice a window as `subset = df.iloc[-window:]`
  and reset its index to 0..window-1 (or otherwise fit the line using
  index positions local to that slice), then "today" in that line's own
  coordinate system is `window - 1`, NOT `len(df) - 1`. This matters for
  Rule 4 (which evaluates the trendline "today") and for the
  ClosenessScore's distance-from-trendline term: both must project the
  line at `window - 1`, using the SAME window that produced the winning
  line - using the full dataframe's global index instead silently
  misprojects the line whenever a fallback window shorter than the full
  history is the one that qualified. (If instead you keep pivot/day
  indices in the FULL dataframe's global coordinate system throughout -
  i.e. never reset the sliced window's index - this concern doesn't
  apply, as long as you are consistent about it everywhere: fitting,
  touch-counting, breakdown-checking, and "today"'s projection must all
  use the same coordinate system.)

Reference implementation (implement this exactly - variable names matter,
they disambiguate the single most common mistake made when implementing
this rule):

```python
# pivot_indices: the array positions (within `window`) of every pivot low
# found in step 2. This is the ONLY array ever used for touch-counting in
# step 6 below. Never substitute subset['low'].values (every day in the
# window) for pivot_indices when counting touches - that counts ordinary
# days drifting near the line as "touches," which is a different, far
# weaker rule than requiring genuine reversal points to touch the line.
pivot_indices = ...  # from argrelextrema, step 2

# fit_indices / fit_lows: the working set used ONLY for fitting the line
# (step 3-4). This set shrinks as outliers get dropped in step 4.
fit_indices = pivot_indices.copy()
fit_lows = lows_at(pivot_indices)
# ... robust refinement loop mutates fit_indices/fit_lows, NOT pivot_indices ...
slope, intercept = final fitted line from fit_indices/fit_lows

# Step 6 - touches: iterate pivot_indices (the ORIGINAL full set from step
# 2), never fit_indices (already-trimmed) and never every day in the
# window.
touches = 0
for i in pivot_indices:               # <-- pivot_indices, not fit_indices,
                                       #     not subset['low'].values / range(window)
    projected = slope * i + intercept
    if abs(low_at(i) - projected) <= 1.0 * atr14:
        touches += 1
```

---

### Rule 4: Bounce Confirmation (Active Trigger)

Description:
A stock sitting near its trendline is not a signal on its own - this rule
requires evidence the bounce is actually happening today, not just that
the stock is in the right location. This is what separates this strategy
from the failed prior version, which had no confirmation trigger at all.

Condition:

Low <= TrendlineProjectedValueToday + (1.0 * ATR(14))
AND
Close > Close[-1]
AND
Volume[-1] >= 1.2 * MA(Volume, 20)

Where:
TrendlineProjectedValueToday = the trendline found in Rule 3, evaluated at
today's day-index (see the Coordinate system note in Rule 3).

Notes:
- "Low <= trendline + 1x ATR" means today's low came within one ATR of the
  trendline (a touch or near-touch), using the SAME trendline and ATR
  computed in Rule 3 - do not re-detect the trendline independently here.
- Close > Close[-1] (today closed higher than yesterday) is the minimum
  bar for "this looks like a bounce, not a breakdown."
- The volume requirement (today's volume >= 1.2x its 20-day average)
  screens out low-conviction, low-volume drifts that happen to close up.

---

### Rule 5: RSI Pullback Zone

Description:
Confirms this is a genuine pullback within an uptrend (neutral-to-mildly-
weak momentum), not a stock that's already extended or one that's broken
down into oversold territory.

Indicator:
RSI(14) on Daily timeframe

Condition:

35 <= Daily_RSI <= 55

Notes:
- Deliberately below-neutral, unlike a breakout strategy's RSI band -
  a pullback to support should show cooled-off, not strong, momentum
  right before the bounce.
- Below 35 is excluded because RSI that oversold more often signals a
  genuine breakdown in progress than a healthy pullback.

---

### Rule 6: Not Already Extended Off the Low

Description:
Avoid entering after the bounce has already happened - this strategy wants
the start of a bounce off support, not a stock that already ran 10-15% off
its recent low before the signal fired.

Condition:

Close <= 1.15 * Close[-10]

---

### Rule 7: Sector Strength

Description:
Stock must belong to a top-performing sector, using the SectorRank already
computed by the backtester/screener.

Condition:

SectorRank <= 10

---

### Rule 8: Market Breadth Filter

Description:
Pause new entries when the broader market is itself broad-based weak, even
if this individual stock's setup looks fine in isolation.

Condition:

MarketBreadth >= 45

Notes:
- MarketBreadth is the % of the entire universe trading above its own
  50-day moving average, computed once per day - use the market_breadth
  parameter directly, do not compute it from this stock's own data.

---

## Rejection Rules

Reject stock if ANY mandatory filter fails.

---

## Ranking Rules

After filtering, rank candidates.

### Rank Score

Score =
30% Trendline_Quality_Score
+
25% Bounce_Strength_Score
+
20% Sector_Strength_Score
+
15% RSI_Pullback_Score
+
10% Proximity_Score

Where:

Trendline_Quality_Score = min(100, TrendlineTouches * 20)
(3 touches = 60 points, 5+ touches = 100 points)

Bounce_Strength_Score = min(100, (Volume[-1] / MA(Volume, 20)) * 50)
(1.2x average volume = 60 points, 2.0x or more = 100 points)

Sector_Strength_Score = max(0, 100 - (SectorRank - 1) * 10)
(Rank 1 = 100, declining 10 points per rank)

RSI_Pullback_Score = max(0, 100 - abs(Daily_RSI - 45) * 5)
(Rewards RSI closest to 45, the middle of the pullback zone)

Proximity_Score = max(0, 100 - (DistanceFromTrendlineInATR * 100))
(Touching the line exactly = 100 points, a full ATR away = 0 points)

Higher score is better.

---

## Output Columns

Return:

- Symbol
- Company Name
- Sector
- Sector Rank
- Current Price
- Ideal Entry Price Low
- Ideal Entry Price High
- Daily RSI(14)
- Volume[-1]
- 20D Average Volume
- Trendline Touches
- Distance From Trendline (ATR units)
- Rank Score

Where:

Ideal Entry Price Low = Close
Ideal Entry Price High = Close * 1.01

This mirrors what the backtester actually does (enters at Close on the
signal day) while giving a small band, since a real fill a moment after
the signal is rarely at the exact closing tick. Do not use this band to
change entry logic anywhere else (Mandatory Filters, Ranking Rules,
backtester) - it is a display-only suggestion for manual order placement.

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
