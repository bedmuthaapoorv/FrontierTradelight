# Stock Selection Rules

## Strategy Metadata

Strategy Name: Calendar Seasonality v1
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: Swing Trade (3-8 Days)

---

## Data Availability Note

Only the following data is available to this strategy: each stock's own
daily OHLCV (open/high/low/close/volume) history, a `SectorRank` value
(1 = best-performing sector by recent average return, higher = weaker), and
a `MarketBreadth` value (0-100: percentage of the entire universe currently
trading above its own 50-day moving average) - both computed once per day
from OHLCV data across the universe. There is NO Nifty benchmark index
data, NO earnings calendar, and NO market-holiday calendar available.

This strategy additionally relies on TODAY'S CALENDAR DATE, which is not a
separate data source - it is simply `df`'s own last (most recent) row date,
already present in every stock's OHLCV history. Day-of-month and
trading-day-count-within-the-month (see Rule 3) are both derived entirely
from that same date column - no new data plumbing is required.

Because there is no market-holiday calendar, "N trading days before/after a
specific holiday" (e.g. a Diwali Muhurat session) CANNOT be computed
precisely - this is why the Diwali/Muhurat effect is discussed but not
implemented as a rule below (see Strategy Rationale).

---

## Strategy Rationale

**This is a statistical tailwind, not a sure thing.** Documented calendar
effects in equity markets are real in the sense that they show up
repeatedly in historical data, but they are weak relative to their own
noise, prone to shrinking or disappearing once well-known (published
anomalies get arbitraged away), and never override what price/volume is
actually doing on a given stock. This strategy treats seasonality as one
input among several - never a standalone reason to buy - the same way BTST
Momentum treats a strong closing print as necessary but not sufficient.

**What's implemented: the turn-of-the-month (TOM) effect.** International
academic research (Xu & McConnell; summarized on Quantpedia) finds equity
returns are disproportionately concentrated in a ~4-trading-day window
spanning the last trading day of one month and the first three trading
days of the next, across 31 of 35 countries studied over long samples -
one of the more robust, cross-market-replicated calendar effects in the
literature. More recent work (see Sources) finds the effect persists but
at meaningfully smaller magnitude than in older samples, consistent with
it becoming better-known and partly arbitraged - which is exactly why
Rule 3 below is used as ONE filter among several (liquidity, trend,
volume, sector, breadth), not the sole trigger.

**What was deliberately left out, and why:**
- *Diwali/Muhurat effect* (buy the Samvat New Year session): the single
  most commonly cited Indian seasonal pattern, but a 2000-2020 academic
  study found it is NOT statistically significant, and the effect that IS
  documented (positive in ~8 of the last 10 years, averaging ~0.4-0.5%) is
  measured over a single one-hour session - not a multi-day window this
  daily-bar swing strategy could actually trade. Including it would mean
  hardcoding a specific calendar date this pipeline has no reliable way to
  detect anyway (no holiday calendar - see Data Availability Note).
- *"Sell in May and go away"*: research specific to NIFTY50 found this
  adage does not reliably hold in the Indian market (positive in 6 of the
  last 10 Mays) - Indian markets are dominated by festival-season flows
  and domestic earnings/reform cycles that don't line up with the
  Northern-Hemisphere origin of this pattern. Not included.

---

## Mandatory Filters

All rules below MUST pass.

---

### Rule 1: Minimum Liquidity Floor

Description:
Reject illiquid stocks so the signal is meaningful and the exit is
executable without slippage.

Condition:

MA(Volume, 20) >= 100000
AND
Close >= 50

---

### Rule 2: Uptrend Context

Description:
A seasonal tailwind is a reason to prefer one stock's timing over
another's, not a reason to fight a structural downtrend. Requires price
above a rising medium-term average.

Condition:

Close > MA(100)
AND
MA(100) > MA(100)[-10]

Notes:
- MA(100)[-10] means the 100-day moving average's value 10 trading days
  ago - confirms the average itself is rising, not flat or falling.

---

### Rule 3: Turn-of-the-Month Window

Description:
The core seasonal signal. Passes if today falls within the documented
turn-of-month window: the last ~4 calendar days of a month, OR one of the
first 3 ACTUAL TRADING DAYS of a new month (counted from this stock's own
OHLCV history, so weekends/holidays are automatically skipped - never
assume calendar day 1-3 of the month are trading days).

Condition:

Days_Until_Month_End(Today) <= 3
OR
Trading_Days_So_Far_This_Month(Today) <= 3

Where:
Days_Until_Month_End(Today) = the number of calendar days between today's
date and the last calendar day of today's month (0 if today IS the last
calendar day of the month). Use Python's calendar/datetime month-length
logic - do not hardcode 30/31 for every month.

Trading_Days_So_Far_This_Month(Today) = count how many rows in this
stock's own OHLCV history have a date in the same calendar month and year
as today, up to and including today (i.e. today's position within this
month's actual trading sessions, 1-indexed).

Notes:
- This is a calendar-arithmetic approximation of "last trading day of the
  month," not an exact one (no holiday calendar is available to know for
  certain whether the actual last trading day is the 28th, 29th, 30th, or
  31st) - a 3-calendar-day buffer before month-end is intentional slack
  for this.
- Trading_Days_So_Far_This_Month is exact (computed from the stock's own
  real trading history, not calendar guesswork), unlike the month-end side
  of this rule.

---

### Rule 4: Volume Confirmation

Description:
A seasonal window without real participation is a weak signal - require
volume at least in line with its recent average, so the entry isn't a
low-conviction drift that happens to fall in the right calendar window.

Condition:

Volume[-1] >= 1.0 * MA(Volume, 20)

Notes:
- Volume[-1] refers to today's (most recently completed) session.
- Deliberately looser than the swing-momentum strategies' 1.3x threshold -
  this strategy's edge is timing-based, not a volume breakout, so it only
  needs to rule out clearly dead/no-conviction days rather than demand a
  surge.

---

### Rule 5: Sector Strength

Description:
Prefer stocks in currently strong sectors - a seasonal tailwind is more
likely to matter for a stock that already has some momentum behind it.

Condition:

SectorRank <= 15

Notes:
- Looser than the breakout/trend strategies' Top 10 cut, since this
  strategy's core edge is timing rather than sector rotation - the goal is
  only to exclude clearly the weakest sectors, not to concentrate in the
  top few.

---

### Rule 6: Market Breadth Filter

Description:
Even a real seasonal tailwind is more likely to fail when the broader
market is itself broadly weak.

Condition:

MarketBreadth >= 40

Notes:
- MarketBreadth is the % of the entire universe trading above its own
  50-day moving average, computed once per day - use the market_breadth
  parameter directly, do not compute it from this stock's own data.
- Deliberately looser than Breakout Momentum v6's 45 cutoff - this
  strategy's holding period is short (3-8 days), so it needs to avoid only
  clearly broad-based weak days, not filter as aggressively as a
  multi-week trend strategy would.

---

## Rejection Rules

Reject stock if ANY mandatory filter fails.

---

## Ranking Rules

After filtering, rank candidates.

### Rank Score

Score =
30% TOM_Strength_Score
+
25% Volume_Score
+
25% Sector_Strength_Score
+
20% Trend_Strength_Score

Where:

TOM_Strength_Score = 100 if today is the single closest trading day to the
exact month boundary among the qualifying window (i.e. Days_Until_Month_End
= 0, or Trading_Days_So_Far_This_Month = 1), tapering linearly to 40 at the
edges of the qualifying window (Days_Until_Month_End = 3, or
Trading_Days_So_Far_This_Month = 3). This rewards proximity to the exact
turn of the month, where the documented effect is strongest, over the
edges of the window.

Volume_Score = min(100, (Volume[-1] / MA(Volume, 20)) * 60)
(Volume at the 20-day average = 60 points, 1.67x average or more = 100)

Sector_Strength_Score = max(0, 100 - (SectorRank - 1) * 7)
(Rank 1 = 100, declining ~7 points per rank, reaching 0 around rank 15)

Trend_Strength_Score = max(0, min(100, ((Close - MA(100)) / MA(100)) * 1000))
(Rewards being meaningfully, not just marginally, above the 100-day
average; caps at 100 so an extreme outlier doesn't dominate the score)

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
- Days Until Month End
- Trading Days So Far This Month
- Daily RSI(14)
- Volume[-1]
- 20D Average Volume
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

---

## Exit Strategy Note

This strategy's edge is a short calendar window (~3-8 trading days), not a
multi-week trend. Pairing it with a long-horizon exit like ATR Trailing
Stop, Let Winners Run v5 (built for multi-week trend-following) would hold
positions well past the point where the seasonal rationale for being in
the trade has expired. A short, fixed-horizon exit (e.g. force-exit ~5-7
trading days after entry, well past the end of the TOM window, with a
tighter stop-loss than the swing strategies use) would fit this strategy's
actual holding thesis better - not built here, since exit_rules.md is
edited/generated separately from rules.md in this app.
