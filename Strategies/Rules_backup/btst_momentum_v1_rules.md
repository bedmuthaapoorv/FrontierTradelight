# Stock Selection Rules

## Strategy Metadata

Strategy Name: BTST Momentum v1
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: BTST (Buy Today, Sell Tomorrow - 1 Trading Day)

---

## Data Availability Note

Only the following data is available to this strategy: each stock's own
daily OHLCV (open/high/low/close/volume) history, a `SectorRank` value
(1 = best-performing sector by recent average return, higher = weaker), and
a `MarketBreadth` value (0-100: percentage of the entire universe currently
trading above its own 50-day moving average) - both computed once per day
from OHLCV data across the universe. There is NO Nifty benchmark index
data, NO earnings calendar, and NO intraday/tick data available. Every
rule below must be computable from end-of-day OHLCV + SectorRank +
MarketBreadth alone.

---

## Strategy Rationale

BTST is a fundamentally different trade from this project's other
strategies, and needs different logic, not a shorter-holding-period
version of a swing strategy. A real BTST desk isn't asking "is this stock
in an uptrend" - it's asking one narrow question: **did today's close show
enough genuine buying conviction that it's likely to continue into
tomorrow's open, before the crowd that saw today's strength gets a chance
to act on it?** That's a well-documented, real effect (close-to-open
drift) driven by a stock closing near its high on strong volume -
late buyers and short-covering push price up into the close, and that
same momentum + information often isn't fully priced in until the next
session opens. The entire edge lives in that one signal, so this strategy
is built around it, not a generic trend/momentum stack:

1. **Closing strength is the core signal, not a supporting one.** Rule 3
   (close within 2% of the day's high) is the single most standard
   quantitative proxy real BTST traders use for "buyers were in control
   into the close." Everything else exists to confirm this signal is
   real, not to replace it.

2. **Volume threshold is higher than this project's swing strategies
   (1.5x vs. 1.3x).** A strong close on merely average volume is easy to
   reverse overnight - BTST has zero time to react if the premise is
   wrong, so the volume confirmation needs to be more demanding than a
   multi-day swing trade that can be exited on the next signal of
   weakness.

3. **A real up-day is required, not just a close near the high.** A stock
   can closed near a *flat* day's high without that meaning anything.
   Rule 5 requires both a genuine daily gain and genuine daily range, so
   the "closed near the high" signal reflects a real move, not noise
   around an unchanged price.

4. **The trend filter is deliberately loose (Rule 2: above the 50-day
   average, not a full moving-average stack).** BTST is opportunistic and
   short-horizon - requiring the same multi-timeframe uptrend confirmation
   a multi-week breakout strategy needs would filter out most valid BTST
   setups (a stock can have a strong single-day close worth trading
   overnight without being in a textbook long-term uptrend). The looser
   filter here exists only to avoid buying into an outright downtrend, not
   to demand trend-following-grade structure.

5. **Market breadth threshold is higher than this project's swing
   strategies (50 vs. 45).** A swing trade entered in a mediocre-breadth
   market can be managed or exited over several days if the market turns.
   A BTST trade is fully exposed to a single overnight gap with no
   intraday opportunity to react - so the tolerance for a weak broader
   market needs to be tighter, not looser, than a strategy with more time
   to course-correct.

**Known limitation, stated plainly:** a real BTST desk enters in the last
20-30 minutes of the session (to capture the overnight move without full
intraday exposure) and would use intraday/tick data to time that entry and
next-morning exit precisely. This pipeline only has end-of-day OHLCV, so
Rule 3-5 use the day's *final* close as a proxy for "bought near the
close" - a standard, necessary simplification for EOD-only data, but it
means this strategy is exposed to the full day's price action, not just
the last half hour, which a live intraday implementation would avoid.

**Known limitation, exit strategy mismatch:** this project's exit logic
(exit_rules.md / generated_exit_strategy.py) is shared across every entry
strategy and is not aware that BTST is, by definition, a 1-trading-day
hold. If exit_rules.md is currently an ATR trailing stop with a long
max-hold (e.g. 90 days), a BTST signal from this strategy could stay open
far longer than intended. This rules.md file only defines entry
selection - if you want to backtest or trade BTST Momentum v1 as intended,
pair it with an exit strategy that force-exits at the next trading day's
open/close, not the shared multi-week ATR trailing stop.

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
the close in the final minutes" (see Strategy Rationale - no intraday
data is available).

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

### Rule 5: Genuine Up-Day With Real Range

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

### Rule 6: Not Already Extended

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

### Rule 7: Sector Strength

Description:
Stock must belong to a top-performing sector, using the SectorRank already
computed by the backtester/screener.

Condition:

SectorRank <= 10

---

### Rule 8: Market Breadth Filter

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

After filtering, rank candidates. Weighted toward the two signals that
actually carry the BTST edge - closing strength and volume conviction -
rather than spreading weight evenly across every filter.

### Rank Score

Score =
40% Closing_Strength_Score
+
30% Volume_Surge_Score
+
15% Day_Move_Score
+
15% Sector_Strength_Score

Where:

Closing_Strength_Score = max(0, 100 - ((High - Close) / High * 100) * 40)
(Close exactly at the high = 100 points, 2.5% below the high = 0 points)

Volume_Surge_Score = min(100, ((Volume[-1] / MA(Volume, 20)) - 1) * 100)
(1.5x average volume = 50 points, 2.5x average volume or more = 100 points)

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
- Distance From High (%)
- Rank Score

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
