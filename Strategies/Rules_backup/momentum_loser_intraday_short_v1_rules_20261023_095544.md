# Stock Selection Rules

## Strategy Metadata

Strategy Name: Momentum Loser Intraday Short v1
Market: India (NSE)
Timeframe: Daily signals, intraday execution
Direction: Short
Holding: Intraday (MIS - short at the open, square off by the close, never held overnight)

---

## Data Availability Note

Only the following data is available to this strategy: each stock's own
daily OHLCV history, a `SectorRank` value, a `MarketBreadth` value (0-100:
percentage of the universe trading above its own 50-day moving average),
and a `momentum_ranks` value per stock (the cross-sectional "12-1"
momentum percentile, see Rule 1). There is NO intraday data, NO index data
and NO earnings calendar. Every rule below must be computable from these
alone.

---

## Strategy Rationale

Short the weakest momentum stocks for one trading session only. Retail
traders can't hold shorts in Indian cash stocks overnight, so MIS
(intraday) is the natural way to trade the short side of momentum.

The rules below are exactly the configuration validated before this
strategy was built (Dec 2020 - Dec 2025, point-in-time Nifty 500,
thresholds chosen on 2021-2023 and confirmed on 2024-2025): about +0.22%
gross per trade out-of-sample with a 1x ATR stop, ~59% win rate. Roughly
two thirds of that is the general tendency of liquid NSE stocks to drift
down from open to close; the momentum selection adds about +0.09% on top.
Results are GROSS - trading costs are handled separately. There is NO
market-breadth gate: this is an intraday (open-to-close) short, so a weak or
narrow market must still produce candidates. An earlier version required
"breadth >= 40", which silently blocked every weak-breadth day. Breadth is
still reported as an output column for information only.

Do not add or tighten filters without re-running that validation - every
untested extra rule risks fitting to noise.

---

## Mandatory Filters

All rules below MUST pass. Let `T = len(df) - 1` be the position of
today's (the signal day's) row.

### Rule 1: Among the Weakest Momentum Stocks

`momentum_rank = (momentum_ranks or {}).get(symbol)`. It is this stock's
12-1 momentum percentile across the whole universe today (return from 252
trading days ago to 21 trading days ago; 100 = strongest, near 0 =
weakest).

Condition: `momentum_rank` is not None AND `momentum_rank <= 5.0`
(bottom 5% of the universe).

### Rule 2: In a Long-Term Downtrend

Requires at least 253 rows of history (fail with "Insufficient history"
otherwise).

Condition (both):
- `Close[T] < SMA(Close, 200)[T]` (today's close below its 200-day simple
  moving average)
- `Close[T] / Close[T-252] - 1 < 0` (negative 12-month return)

### Rule 3: Market Breadth (informational only - never fails the stock)

Do NOT filter on `market_breadth`; the stock passes this rule at any breadth
value (including very low readings). Only report it in the output columns.

### Rule 4: Liquid Enough for Intraday Shorting

Condition: `avg_traded_value(df, 20) >= 25e7` - the 20-day average of
Close x Volume is at least Rs 25 crore (use the library method
`avg_traded_value`).

---

## Ranking Rules (Rank Score)

Only computed for stocks that pass every rule; 0 otherwise.

- `momentum_score = max(0, 100 - momentum_rank * 20)` (rank 0 -> 100,
  rank 5 -> 0: the weaker, the better)
- `liquidity_score = min(100, avg_traded_value / 1e9 * 100)` (Rs 100 crore
  or more -> 100)
- `Rank Score = 0.7 * momentum_score + 0.3 * liquidity_score`

ClosenessScore = Rank Score.

---

## Output Columns

- Company Name: from `universe`
- Sector: from `universe`
- Current Price: `Close[T]`
- Momentum Rank (pct): `momentum_rank`
- 12M Return (%): `(Close[T] / Close[T-252] - 1) * 100`
- SMA200: `SMA(Close, 200)[T]`
- Avg Traded Value (Rs Cr): `avg_traded_value(df, 20) / 1e7`
- Market Breadth: `market_breadth`
- ATR(14): `ATR(14)[T]`
- Indicative Stop (above next open): "next open + ATR(14)" - also report
  the number `Close[T] + ATR(14)[T]` as "Stop If Opening Flat"
- Rank Score: as defined above
