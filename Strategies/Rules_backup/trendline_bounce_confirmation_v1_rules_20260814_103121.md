# Stock Selection Rules

## Strategy Metadata

Strategy Name: Trendline Bounce Confirmation v1
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

The prior trendline strategy in this project ("Trendline Support
Momentum") failed - both because a placeholder value stood in for the
actual trendline geometry, and because even after fixing that, the
underlying idea was too weak: it treated "price is near a rising
trendline" as a signal by itself. It isn't. A trendline only tells you
where a stock *might* find support - it says nothing about whether it
actually will. Buying every touch of a support line, with no confirmation
that the bounce is real, is buying into every attempt at a bounce,
including the ones that fail and break down through it.

This version treats the trendline as a *passive filter* (a location worth
paying attention to) and requires a separate *active trigger* (evidence
the bounce is actually happening) before entering - the same separation a
discretionary trader would make between "watching a level" and "taking the
trade." Four design choices follow from that:

1. **Multiple touches, not two.** Two touches can define a line through
   almost any two points; three or more spaced-apart touches is what
   distinguishes a real trendline from a line that happens to fit noise.
2. **ATR-normalized proximity, not a flat percentage.** A 3% band means
   something very different for a low-volatility large-cap than a
   volatile mid-cap. Measuring proximity in ATR units instead keeps the
   "how close counts as a touch" threshold consistent across different
   stocks' volatility.
3. **A bounce confirmation trigger.** Price must be near the trendline
   *and* today must show an actual reversal - an up day on above-average
   volume - before this counts as a signal. This is the single biggest
   change from the failed version: it turns a passive "is it near
   support" check into an active "is it bouncing right now" check.
4. **Trend context.** Support only means something inside an existing
   uptrend. This requires price above a rising 100-day average, so the
   line being traded is a pullback within a trend, not a dead-cat bounce
   inside a longer decline that happens to have a rising line under it.

---

## Mandatory Filters

All rules below MUST pass.

---

### Rule 1: Minimum Liquidity Floor

Description:
Reject illiquid stocks so signals are meaningful and exits are executable
without slippage.

Condition:

MA(Volume, 20) >= 100000
AND
Close >= 50

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

4. Robust refinement (tolerate outliers instead of requiring a perfect
   fit): repeat up to `ceil(0.2 * number_of_pivots)` times - find the
   pivot low with the most negative residual (furthest BELOW the current
   line). If that residual is worse than -1.0x ATR(14), drop that pivot
   and refit the line on the remaining pivots; otherwise stop early (no
   more meaningful outliers). This lets one or two anomalous dips get
   excluded rather than distorting or invalidating the whole line, the
   same way a chartist mentally discounts a single outlier wick.

5. Discard this window if the final slope is non-positive (must be
   ascending).

6. Count how many pivot lows (from the original full set in step 2, not
   just the ones kept after step 4's trimming) lie within 1.0x ATR(14) of
   the final line's projected value at their day-index - these are the
   line's "touches." Require at least 3. If fewer than 3, this window
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
  history is the one that qualified.

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
today's day-index.

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
- Daily RSI(14)
- Volume[-1]
- 20D Average Volume
- Trendline Touches
- Distance From Trendline (ATR units)
- Rank Score

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
