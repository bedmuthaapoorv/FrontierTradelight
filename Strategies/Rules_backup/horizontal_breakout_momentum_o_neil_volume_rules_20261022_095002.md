# Stock Selection Rules

## Strategy Metadata

Strategy Name: Horizontal Breakout Momentum (O'Neil Volume)
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: Trend Trade (1-90 Days)

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

v3 was a pullback-to-support strategy (buy near a recent low, in an
uptrend). Backtesting showed ~80%+ of v3 trades were stopped out shortly
after entry regardless of stop width, while the rare trades that survived
to the max holding period were consistently profitable. This points to a
mismatch: buying near a recent low is more often a failing bounce than a
genuine trend resumption, which is exactly what a wide ATR trailing stop
chops up. v4 flipped the entry philosophy to a breakout: buy stocks pushing
to new short-term highs on strong volume, in a confirmed uptrend.

v5 removed the fixed take-profit from the exit strategy (see
exit_rules.md) so winning trades aren't capped - trend-following systems
earn their edge from a few large winners paying for many small losers, and
a fixed take-profit destroys that asymmetry. This flipped the 3-year
backtest from net negative to slightly net positive, but the win rate
stayed stuck around 35% regardless of entry tuning.

v6 adds a market-breadth filter: pause new entries when the broader
universe itself is broad-based weak (few stocks above their own 50-day
average), since even a good individual breakout setup tends to fail when
the overall market is correcting. This is a stand-in for the Nifty-based
market-regime filter real trend traders use, built entirely from data this
pipeline already has.

v7 loosens Rule 4's volume confirmation. Analyzing v6's near-misses (the
Missed Opportunities tab, stocks that failed exactly one mandatory rule)
found Volume Confirmation was by far the single largest blocking reason -
6,654 of 10,669 near-misses (62%) over the 5-year benchmark range, more
than 4x the next largest category. Those blocked stocks still averaged a
+1.49% 20-day forward return at a 54% win rate - not a standout number,
but not a red flag either, and notably better than v6's own actual funded
trades (+Rs.1.54 mean profit at only a 39% win rate). The day-over-day
clause (`Volume[-1] > Volume[-2]`) is the more likely culprit: it rejects
a stock on an already-elevated, above-average volume day just because
yesterday happened to be even higher - two strong volume days in a row is
arguably a BETTER breakout signal than one, not a worse one. v7 drops that
clause, keeping only the absolute 1.3x-average bar, which is the part of
the rule actually measuring "is volume elevated."

**v7 backtested worse, not better**: CAGR +8.00%/yr (vs v6's +10.03%),
MaxDD -24.0% (vs -18.1%), Composite 0.24 (vs 0.55). More signals fired as
expected (2,197 vs 1,300 evaluated, 408 vs 383 funded), but the extra
volume diluted returns and worsened drawdown rather than adding clean
incremental trades - competition for the fixed 10 position slots also
got markedly worse (1,789 vs 917 skipped for lack of capital). The
near-miss methodology that motivated v7 measures a naive fixed 20-day
hold, which misses two things the real backtest captures: the ATR
trailing stop can exit an admitted trade early on a whipsaw before a
20-day window would show a profit, and every extra signal competes with
the existing ones for the same limited slots rather than being purely
additive. Kept as a recorded, honest negative result - not reverted here,
since v8 tests a second, independent hypothesis on top of it (below); if
v8 doesn't recover v6's performance, Rule 4's day-over-day clause should
go back in a future version.

v8 fixes Rule 1's liquidity floor, which has the exact same defect just
fixed in Trendline Bounce Confirmation v4: a flat `MA(Volume, 20) >=
100000` share-count threshold, unexamined since v1, with no recorded
justification for the number. Raw share count is the wrong unit for a
liquidity floor - 100,000 shares/day means very different things for a
Rs.50 stock and a Rs.5,000 stock, even though both pass the identical
threshold. Replaced with the same turnover floor already validated for
Trendline v4 (MA(Volume * Close, 20) >= Rs. 5 crore/day, checked against
this project's actual cached universe data - even the weakest 5% of
stocks by turnover clear ~Rs. 110 crore/day, ~20x this floor). This is an
independent hypothesis from v7's Rule 4 change - if v8 backtests worse
than v6 as well, that's evidence the Rule 4 change (not the liquidity
floor) is the actual problem; if v8 recovers or beats v6's numbers, the
liquidity fix was worth keeping regardless of Rule 4's outcome.

v9 tests a third, independent hypothesis on Rule 4, this time tightening
rather than loosening it, based on O'Neil Global Advisors' "Breakouts:
Pump Up the Volume" (May 2022), a quantitative study of ~197,000 O'Neil
pattern breakout events across the U.S. market, 1995-2021. That study
measured volume as the percent change over a 50-day average volume
baseline (not 20-day), and found the relationship was NOT a fewer-false-
breakouts effect: hit rate was flat at ~57% across every volume bucket,
even ticking down slightly at the highest bucket. What actually scaled
with volume was the SIZE of the move in both directions - average gain
rose from 12.91% (volume change <50%) to 19.90% (volume change >=150%,
i.e. volume >= 2.5x the 50-day average), while average loss also grew
(-11.42% to -14.53%) - and because the gain grew faster than the loss,
cumulative alpha over the following 63 trading days rose from 0.67% to
2.79%, a 4x increase. v9 changes Rule 4 to match that exact threshold and
window (50-day average, >=2.5x) to test whether this project's own
backtest shows the same "bigger moves, not more of them" pattern, given
this strategy's Rank Score already weights Volume_Score at 30% - which,
if the O'Neil mechanism holds here too, is the right lever (ranking the
biggest-volume breakouts highest for the limited position slots) rather
than expecting Rule 4 alone to raise the win rate. This is a materially
different change from v7's (loosening the multiplier while keeping the
20-day window) - v7's result does not predict v9's, since v7 never tested
a wider averaging window or a threshold in the direction the O'Neil data
actually supports.

---

## Mandatory Filters

All rules below MUST pass.

---

### Rule 1: Minimum Liquidity Floor (v8 - turnover-based)

Description:
Reject illiquid stocks so volume signals are meaningful and exits are
executable without slippage.

Condition:

MA(Volume * Close, 20) >= 50000000
AND
Close >= 50

Where:
MA(Volume * Close, 20) = the 20-day average of daily traded value in
Rupees (each day's Volume times that day's Close, averaged over the last
20 trading days) - i.e. turnover, not raw share count.

Notes:
- v7 and earlier used a flat `MA(Volume, 20) >= 100000` share-count floor,
  unexamined since v1 with no recorded justification for the number -
  the same defect already fixed in Trendline Bounce Confirmation v4.
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
  noise, not a liquidity proxy.

---

### Rule 2: Trend Structure (Moving Average Stack)

Description:
Confirm the stock is in a genuine multi-timeframe uptrend using a moving
average stack.

Condition:

Close > MA(20)
AND
MA(20) > MA(50)
AND
MA(50) > MA(126)

Notes:
- This is the core trend filter: price above a rising short-term average,
  which is above a rising medium-term average, which is above a rising
  long-term (6-month) average.

---

### Rule 3: Daily RSI Range (Strength Zone)

Description:
Stock must show strong (not merely neutral) momentum - breakout entries
need real strength behind them, unlike a pullback entry which wants
neutral RSI.

Indicator:
RSI(14) on Daily timeframe

Condition:

55 <= Daily_RSI <= 75

Notes:
- Raised from the neutral 40-65 band used in the prior pullback version.
  A genuine breakout is accompanied by RSI pushing into the upper range,
  not sitting at neutral.
- 75 as a ceiling avoids the most extreme, likely-to-mean-revert overbought
  readings while still allowing strong momentum through.
- Reverted a v4.1 tightening to 60 that shrank the sample to a
  statistically meaningless size (29 trades over 3 years) without proving
  beneficial - back to the wider band that produced a real sample (760
  trades over 3 years) to test against.

---

### Rule 4: Volume Confirmation (Breakout Volume) (v9 - O'Neil 50-day/2.5x threshold)

Description:
A breakout without volume is a weak/fakeout signal. Require a real
volume surge, not just mild acceleration.

Condition:

Volume[-1] >= 2.5 * MA(Volume, 50)

Where:
MA(Volume, 50) = the 50-day average of daily traded share volume (not the
20-day window used in v7/v8).

Notes:
- v9 replaces v7/v8's `Volume[-1] >= 1.3 * MA(Volume, 20)` with the exact
  window and threshold O'Neil Global Advisors' "Breakouts: Pump Up the
  Volume" (May 2022) found produced the strongest, monotonically-best
  alpha bucket in their 1995-2021 U.S. study: volume percent change over a
  50-day average of >=150% (i.e. volume >= 2.5x that average). See the
  Strategy Rationale section above for the full comparison and why this is
  a materially different change from v7's (which loosened a 20-day-window
  rule, not tightened a 50-day one).
- Unlike v6's dropped `Volume[-1] > Volume[-2]` day-over-day clause (v7),
  this is a single absolute threshold against a longer, smoother baseline
  - a 50-day average is less noisy than a 20-day one, so this should
  actually fire on genuinely elevated days, not on a temporarily low
  average distorted by a quiet recent stretch.
- Expect this to cut the funded-trade count substantially versus v7/v8's
  1.3x/20-day bar - that is the point of the test, not a flaw: the O'Neil
  study's edge came from being more selective, not less.
- Ignore today's incomplete session volume throughout.
- Stocks with missing volume data should be rejected.

---

### Rule 5: Breakout Proximity to Short-Term High

Description:
Price should be pushing to a new short-term high (a breakout entry) rather
than sitting well below it. This replaces trendline touch-point/slope
detection, which generated code cannot reliably compute from raw OHLCV.

Condition:

Close >= 0.98 * Highest_Close(20)
AND
Close > Close[-1]

Where:
Highest_Close(20) = the highest closing price over the last 20 trading
sessions (including today).

Notes:
- "Within 2% of the 20-day high" while still passing Rule 2's uptrend
  stack is the breakout-in-an-uptrend setup this strategy is built around.
- Close > Close[-1] (today closed higher than yesterday) confirms today is
  an up day, not a stall/reversal day at the highs.
- Reverted a v4.1 tightening to 0.995 that shrank the sample to a
  statistically meaningless size without proving beneficial.

---

### Rule 6: Not Already Extended Too Far

Description:
Avoid chasing a stock that has already run up too much very recently -
prefer the early stage of a breakout over a multi-week extended move.

Condition:

Close <= 1.25 * Close[-20]

Notes:
- Price no more than 25% above where it was 20 trading days ago. This
  excludes stocks in the middle/late stage of a parabolic run, while still
  allowing genuine fresh breakouts through.

---

### Rule 7: Sector Strength

Description:
Stock must belong to a top-performing sector, using the SectorRank already
computed by the backtester/screener (ranked by each sector's average
30-day return - no Nifty-relative or fundamental data involved).

Condition:

SectorRank <= 10

Notes:
- With only ~15 sectors in the Nifty universe, Top 10 is a meaningful cut
  without being so tight it starves the strategy of trades.
- Reverted a v4.1 tightening to Top 5 that shrank the sample to a
  statistically meaningless size without proving beneficial.

---

### Rule 8: Market Breadth Filter (v6)

Description:
Pause new entries when the broader market is itself broad-based weak, even
if this individual stock's setup looks fine in isolation. A good breakout
setup is more likely to fail when most other stocks are simultaneously
breaking down - this is a systemic risk no single-stock filter can catch.

Condition:

MarketBreadth >= 45

Notes:
- MarketBreadth is the % of the entire universe trading above its own
  50-day moving average, computed once per day (not specific to this
  stock) - use the market_breadth parameter directly, do not compute it
  from this stock's own data.
- 45 was chosen from the historical distribution of this metric over the
  backtest period (mean ~57, median ~58, 10th percentile ~28): a cutoff of
  45 excludes roughly the weakest 30% of trading days (broad corrections)
  while still allowing the large majority of days through.

---

## Rejection Rules

Reject stock if ANY mandatory filter fails.

---

## Ranking Rules

After filtering, rank candidates.

### Rank Score

Score =
30% Sector_Strength_Score
+
30% Volume_Score
+
25% Breakout_Quality_Score
+
15% RSI_Strength_Score

Where:

Sector_Strength_Score = max(0, 100 - (SectorRank - 1) * 10)
(Rank 1 = 100, declining 10 points per rank)

Volume_Score = min(100, (Volume[-1] / MA(Volume, 50)) * 40)
(2.5x average volume = 100 points, matching Rule 4's new baseline window)

Breakout_Quality_Score = max(0, 100 - ((Highest_Close(20) - Close) / Highest_Close(20) * 100) * 30)
(Close exactly at the 20-day high = 100 points, 2% below it = ~40 points)

RSI_Strength_Score = max(0, 100 - abs(Daily_RSI - 65) * 4)
(Rewards RSI closest to 65, the middle of the strength zone; 0 points at
RSI 40 or 90)

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
- Volume[-2]
- 50D Average Volume
- Volume[-1] / 50D Avg (ratio)
- 20-Day High
- Distance From 20-Day High (%)
- Close vs Close[-20] (%)
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
