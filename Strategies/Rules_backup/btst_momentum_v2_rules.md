# Stock Selection Rules

## Strategy Metadata

Strategy Name: BTST Momentum v2
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: BTST (Buy Today, Sell Tomorrow - 1 Trading Day)

---

## Data Availability Note

Only the following data is available to this strategy: each stock's own
daily OHLCV (open/high/low/close/volume) history, `delivery_pct` (NSE's
published % of traded volume that settled as delivery rather than
intraday-only churn - same history length as OHLCV, may be `NaN` for
older cached data), a `SectorRank` value (1 = best-performing sector by
recent average return, higher = weaker), and a `MarketBreadth` value
(0-100: percentage of the entire universe currently trading above its own
50-day moving average) - both computed once per day from OHLCV data
across the universe. There is NO Nifty benchmark index data, NO earnings
calendar, NO F&O-eligibility list, NO corporate-actions calendar, and NO
intraday/tick data available. Every rule below must be computable from
end-of-day OHLCV + delivery_pct + SectorRank + MarketBreadth alone.

---

## Strategy Rationale

v1 built the right core idea (closing strength + volume conviction as a
proxy for close-to-open drift) but was missing two real signals research
into how BTST is actually traded turned up:

1. **No RSI filter at all (added in v2).** v1 had no momentum-zone check.
   Research-backed BTST screens consistently use RSI in a 40-65 "bullish
   but not overbought" band (Rule 5) - strong enough to confirm real
   momentum, capped before the move is so extended it's likely to
   mean-revert overnight. This is a different shape than a pullback
   strategy's RSI band (which wants neutral-to-oversold, the opposite
   of what BTST needs).

2. **No momentum-confirmation indicator (added in v2).** v1 relied
   entirely on price/volume shape (close near high, volume surge). Adding
   a MACD bullish crossover (Rule 6) as a second, independent momentum
   confirmation reduces false positives from a single strong day that
   isn't backed by a broader momentum shift - two independent signals
   agreeing is a stronger filter than one signal alone.

3. **Delivery % was available and unused (added in v2).** This is the
   single most useful addition: `delivery_pct` distinguishes a strong
   close driven by intraday speculative churn (likely to unwind
   immediately) from one where real buyers took delivery (a genuine
   signal the move has substance behind it, per Rule 7). v1 didn't use
   this because the pipeline was silently discarding it before it ever
   reached the strategy - this is not a stylistic choice, it required
   plumbing the field through nse_utils/stock_screener.py/backtest.py so
   evaluate_stock actually receives it.

Everything else carries over from v1 unchanged, since it was already
validated against real BTST practice: closing near the day's high as the
core signal (Rule 3), volume surge threshold above what this project's
swing strategies use (Rule 4), a deliberately loose trend filter instead
of a full moving-average stack (Rule 2), a short (5-day, not 20-day)
extension lookback (Rule 9), and a higher market-breadth bar than the
swing strategies (Rule 11) since a BTST trade has zero intraday time to
react if the broader market turns against it overnight.

**What real BTST desks do that this strategy still cannot:** enter in the
last 20-30 minutes of the session using intraday data (this pipeline only
has end-of-day OHLCV, so the day's final close is used as a proxy); check
an F&O eligibility list and a corporate-actions calendar before entering
(no such data source is available to this pipeline - NSE's live
corporate-actions API is the same class of bot-blocked endpoint this
project has hit before for live quotes and index history; an F&O list
would be a new data fetch this pipeline doesn't currently make). These
remain honest, stated gaps, not silently ignored.

**Exit strategy mismatch (unchanged from v1):** this project's exit logic
is shared across every entry strategy. Pair this with an exit strategy
that force-exits at the next trading day's close (not a multi-day ATR
trailing stop) - see BTST Fixed Next-Session Exit v1 in ExitRules_backup/.

---

## Mandatory Filters

All rules below MUST pass.

---

### Rule 1: Minimum Liquidity Floor

Description:
Reject illiquid stocks so tomorrow's exit is executable without slippage -
this matters more for BTST than a multi-day swing trade, since there's no
opportunity to wait for a better exit if liquidity is thin.

Condition:

MA(Volume, 20) >= 100000
AND
Close >= 50

---

### Rule 2: Not in a Downtrend

Description:
Deliberately loose trend filter - excludes outright downtrends without
demanding the multi-timeframe uptrend structure a longer-horizon strategy
would need. A single strong closing day is tradeable BTST even without a
textbook long-term uptrend behind it.

Condition:

Close > MA(50)

---

### Rule 3: Closing Near the Day's High

Description:
The core BTST signal: price closed near its intraday high, indicating
buyers were in control into the close rather than the stock fading from
an intraday peak. This is the proxy this pipeline uses for "bought near
the close in the final minutes" (no intraday data is available).

Condition:

Close >= 0.98 * High

Notes:
- High refers to today's intraday high.
- A close within 2% of the day's high is the standard quantitative
  threshold for "strong close" used across BTST screens.

---

### Rule 4: Volume Confirmation

Description:
A strong close without volume is easy to reverse overnight. Require
clearly elevated participation, higher than this project's swing
strategies, since BTST has no time to react if the signal is wrong.

Condition:

Volume[-1] >= 1.5 * MA(Volume, 20)

Notes:
- Volume[-1] refers to today's volume.
- Ignore today's session if it is still in progress (only use completed
  sessions).
- Stocks with missing volume data should be rejected.

---

### Rule 5: RSI Momentum Zone

Description:
Confirms real momentum without being extended into overbought territory.
This is a "bullish but not overbought" band, the opposite shape from a
pullback strategy's RSI filter.

Indicator:
RSI(14) on Daily timeframe

Condition:

40 <= Daily_RSI <= 65

Notes:
- Below 40 does not show enough momentum to support a BTST continuation
  thesis.
- Above 65 risks the move already being extended enough that next-session
  profit-booking is more likely than continuation.

---

### Rule 6: MACD Bullish Crossover

Description:
A second, independent momentum confirmation on top of the price/volume
shape above. MACD(12,26,9) crossing bullish today means the broader
momentum picture agrees with today's strong close, not just today's price
action in isolation.

Condition:

MACD_Line > MACD_Signal_Line (today)
AND
MACD_Line <= MACD_Signal_Line (yesterday)

Where:
MACD_Line = EMA(12) - EMA(26) of Close.
MACD_Signal_Line = EMA(9) of MACD_Line.

Notes:
- This requires the crossover to happen TODAY specifically (was below or
  equal yesterday, is above today) - not merely "MACD line is currently
  above the signal line," which could have been true for many days
  already and wouldn't represent fresh momentum.
- Reject if insufficient history to compute MACD(12,26,9) (need at least
  ~35 sessions).

---

### Rule 7: Delivery Confirmation

Description:
Distinguishes a strong close backed by genuine buying (investors taking
delivery) from one driven by intraday-only speculative churn that's more
likely to reverse before tomorrow's open.

Condition:

DeliveryPct >= 30

Notes:
- DeliveryPct is NSE's published delivery percentage for the day - use
  the delivery_pct column directly, it is already provided per day, do
  not attempt to compute or estimate it from OHLCV.
- If delivery_pct is NaN/missing for a stock (e.g. older cached history
  fetched before this field was tracked), reject the stock rather than
  treating missing data as passing.

---

### Rule 8: Genuine Up-Day With Real Range

Description:
Confirms today was an actual move, not a flat/noisy day that happened to
close near an unchanged high. Both a meaningful gain and a meaningful
intraday range are required.

Condition:

Close >= 1.01 * Close[-1]
AND
((High - Low) / Low) >= 0.02

Notes:
- Close[-1] is yesterday's close.
- The range condition excludes stocks that drifted narrowly all day and
  merely closed at the top of that narrow range - real conviction shows
  up as real range, not just a marginal new high.

---

### Rule 9: Not Already Extended

Description:
Avoid chasing a stock that has already run up sharply over the last few
sessions - a large existing gain increases the odds of next-session
profit-booking overwhelming any overnight continuation.

Condition:

Close <= 1.10 * Close[-5]

Notes:
- Close[-5] is the closing price 5 trading days ago - a much shorter
  lookback than this project's swing strategies use, since BTST cares
  about very recent extension, not a multi-week run.

---

### Rule 10: Sector Strength

Description:
Stock must belong to a top-performing sector, using the SectorRank already
computed by the backtester/screener.

Condition:

SectorRank <= 10

---

### Rule 11: Market Breadth Filter

Description:
Pause new entries when the broader market is broad-based weak. Set higher
than this project's swing strategies (50 vs. 45) because a BTST trade is
fully exposed to a single overnight gap with no time to react if the
market turns against it overnight.

Condition:

MarketBreadth >= 50

Notes:
- MarketBreadth is the % of the entire universe trading above its own
  50-day moving average, computed once per day - use the market_breadth
  parameter directly, do not compute it from this stock's own data.

---

## Rejection Rules

Reject stock if ANY mandatory filter fails.

---

## Ranking Rules

After filtering, rank candidates. Weighted toward the signals that
actually carry the BTST edge - closing strength, volume conviction, and
delivery confirmation - rather than spreading weight evenly.

### Rank Score

Score =
25% Closing_Strength_Score
+
25% Volume_Surge_Score
+
20% Delivery_Score
+
15% RSI_Momentum_Score
+
10% Day_Move_Score
+
5% Sector_Strength_Score

Where:

Closing_Strength_Score = max(0, 100 - ((High - Close) / High * 100) * 40)
(Close exactly at the high = 100 points, 2.5% below the high = 0 points)

Volume_Surge_Score = min(100, ((Volume[-1] / MA(Volume, 20)) - 1) * 100)
(1.5x average volume = 50 points, 2.5x average volume or more = 100 points)

Delivery_Score = min(100, ((DeliveryPct - 30) / 40) * 100)
(30% delivery = 0 points, 70% delivery or more = 100 points)

RSI_Momentum_Score = max(0, 100 - abs(Daily_RSI - 55) * 4)
(Rewards RSI closest to 55, the middle of the momentum zone; 0 points at
RSI 30 or 80)

Day_Move_Score = min(100, ((Close / Close[-1]) - 1) * 100 * 20)
(1% daily gain = 20 points, 5% or more = 100 points)

Sector_Strength_Score = max(0, 100 - (SectorRank - 1) * 10)
(Rank 1 = 100, declining 10 points per rank)

Higher score is better.

---

## Output Columns

Return:

- Symbol
- Company Name
- Sector
- Sector Rank
- Current Price
- Day's High
- Day's Low
- Close vs Close[-1] (%)
- Volume[-1]
- 20D Average Volume
- Volume[-1] / 20D Avg (ratio)
- Delivery %
- Daily RSI(14)
- Distance From High (%)
- Rank Score

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
