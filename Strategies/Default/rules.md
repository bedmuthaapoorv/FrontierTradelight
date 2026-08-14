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
action, using pivot lows over the last 100 trading days - not a
placeholder or approximation. This is the core, most failure-prone rule in
this strategy: implement the actual geometry below, do not substitute a
fixed/hardcoded distance value for any part of it.

Algorithm (implement exactly):

1. Over the last 100 trading days of `low` prices, find pivot lows: a day
   is a pivot low if its `low` is less than or equal to the `low` of the
   4 trading days before AND the 4 trading days after it (a local minimum
   using a window of 4 on each side). Standard local-extrema detection
   (e.g. scipy.signal.argrelextrema with order=4) is the expected
   implementation - do not hand-roll a simplified/dummy version.
2. For every pair of pivot lows that are at least 10 trading days apart,
   fit a straight line through them (slope and intercept over the pivot's
   day-index within the 100-day window).
3. Discard any candidate line with a non-positive slope (must be
   ascending).
4. Count how many OTHER pivot lows also lie within 1.0x ATR(14) of that
   line's projected value at their day-index - these are the line's
   "touches" (including the two anchor points).
5. Keep the candidate line with the most touches. Require at least 3
   touches total. If no candidate qualifies, this rule fails for the
   stock - it has no ascending trendline.
6. Reject if any close price in the 100-day window fell more than 1.5x
   ATR(14) below the line's projected value at that day - that is a
   breakdown, meaning the "support" didn't actually hold.

Condition:

TrendlineTouches >= 3
AND
TrendlineSlope > 0
AND
NoBreakdownBelowLine(100 days, tolerance = 1.5x ATR(14))

Notes:
- ATR(14) should be computed once (today's value) and used as the unit of
  distance throughout steps 4 and 6, not recomputed per pivot.
- If fewer than 100 days of history are available, or fewer than 4 pivot
  lows exist, this rule fails (insufficient data for a reliable line, not
  an error).

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
