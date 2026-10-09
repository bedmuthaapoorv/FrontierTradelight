# Stock Selection Rules

## Strategy Metadata

Strategy Name: Cup and Handle Breakout v1
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: Trend Trade (1-90 Days)

---

## Data Availability Note

Only the following data is available to this strategy: each stock's own
daily OHLCV (open/high/low/close/volume) history (~400 trading days), a
`SectorRank` value (1 = best-performing sector by recent average return,
higher = weaker), and a `MarketBreadth` value (0-100: percentage of the
entire universe currently trading above its own 50-day moving average) -
both computed once per day from OHLCV data across the universe. There is NO
Nifty benchmark index data, NO earnings/fundamental data and NO IBD-style
Relative Strength rating available. Every rule below must be computable
from OHLCV + SectorRank + MarketBreadth alone.

---

## Strategy Rationale

A fresh strategy line, not a v-increment of Horizontal Breakout Momentum.
Both buy a breakout, but this one requires a specific, long base structure
(a rounded cup followed by a short, shallow handle) before the breakout
counts, so trade counts, hold times and win rates are not expected to match
Breakout Momentum's. Back-test it independently before comparing.

All thresholds come from `reports/Cup and handle breakout rules.md` (project
root), which grades each one by evidence. Read that report before changing
any number. Points that shaped this spec:

- Most geometry thresholds (30% prior advance, 12-35% cup depth, handle in
  the upper half, handle depth <= 12%, 1.4x breakout volume, 5% chase limit)
  are O'Neil/IBD convention, confirmed through practitioner and secondary
  sources only. None has a rigorous cup-specific validation.
- The only rigorous large-sample study (O'Neil Global Advisors, "Breakouts:
  Pump up the Volume", May 2022, ~197,000 US breakouts 1995-2021) found the
  hit rate flat at ~57% across every breakout-volume bucket, while average
  gain and alpha rose with volume. So the 1.4x volume rule is kept as a
  validity gate (doctrine), and volume magnitude is the largest ranking
  weight - it predicts move size, not odds.
- Bulkowski's widely quoted 5% failure rate / 54% average rise come from
  hand-picked "perfect trades" measured to a hindsight ultimate high. They
  are NOT a benchmark for this automated detector. A realistic baseline is
  roughly 57% winners before costs.
- There is no Indian-market evidence for this pattern at all. The first NSE
  backtest is the first real test.
- MarketBreadth and SectorRank are ranking weights in v1, NOT hard gates.
  The evidence for a regime gate on this pattern is vendor-level and
  ex-post only, and a gate cuts sample size. Testing a hard
  `MarketBreadth >= 45` gate (as Breakout Momentum uses) is the intended
  v2 experiment.
- Deliberately excluded from v1: cup-without-handle, cheat/low-cheat
  entries, deep-cup (bear-market) allowance, base-count (late-stage base)
  penalty, and delivery %. Each is either a separate trigger with its own
  risk profile or rests on unverified numbers.
- Fix every threshold before the first backtest. Use any later sensitivity
  grid only to check robustness, not to pick the best-looking parameters.

---

## Signal-Day Convention (READ FIRST - applies to every rule)

- `df` holds one row per completed trading session, oldest first. The
  signal day **T is the LAST row of `df`** (position `len(df) - 1`). It is a
  completed session: its Close and Volume are final and MUST be used.
- All positions below are integer row positions in `df` (0 = oldest row),
  NOT pandas index labels. Write `Close[T]` as `df['close'].iloc[T]`,
  `High[C]` as `df['high'].iloc[C]`, and so on.
- `[x, y]` means the inclusive range of positions x through y.
  `(x, y)` means exclusive of both ends.
- Use only rows at positions <= T. Never use a centered rolling window,
  centered smoother, or any function that looks at rows after the bar it is
  labelling. Do NOT use `scipy.signal.argrelextrema` for any anchor in this
  spec - every anchor below is defined by explicit windows that are already
  fully confirmed by day T.
- `SMA(x, n)` at position p means the simple mean of x over positions
  [p - n + 1, p].
- If `len(df) < 250`, reject immediately with "Insufficient data (< 250
  sessions)".

---

## Pattern Anchor Detection (Shared Definition)

Locate the five anchor points in this exact order. Each yields exactly one
position per stock per day. If any step says "reject", stop and return
`Passed = False` with that reason - do not evaluate the Mandatory Filters,
since there is no pattern to test.

Notation: A = left rim, B = cup low, C = right rim (handle high),
D = handle low, K = base of the prior advance.

### Step 1: Right rim C

Let C be the position with the highest `High` in the window [T - 22, T - 5].
On ties, take the LATEST such position.

Then require `High[C] >= max(High over [C + 1, T - 1])`, i.e. no later bar
before the signal day traded above C's high. If this fails, reject with
"No handle structure (higher high after right rim)".

Notes:
- Requiring C <= T - 5 makes C a confirmed high (at least 4 lower-or-equal
  sessions follow it) AND sets the 5-session handle minimum in one rule. Do
  not add a separate pivot detector for C - a coarse pivot (e.g. order 10)
  would silently force a 10-day minimum handle.

### Step 2: Handle low D

D is the position with the lowest `Low` in [C + 1, T - 1]. On ties, take
the LATEST such position.

D is not a pivot. It is simply "the lowest low since the right rim,
excluding the signal day", recomputed every day.

### Step 3: Left rim A

Search positions i in [max(10, C - 250), C - 30], from the MOST RECENT
(i = C - 30) backwards to the oldest. Take the FIRST i that satisfies both:

1. i is a swing high of half-width 10:
   `High[i] >= max(High over [i - 10, i + 10])`
2. Nothing between i and C traded higher:
   `High[i] >= max(High over [i, C - 1])`

That i is A. If no i qualifies, reject with "No left rim found".

Notes:
- Every candidate i is at most C - 30, so i + 10 <= T - 25: the swing-high
  test uses only rows far before T. No look-ahead.
- Do NOT add any price tolerance here (e.g. "within X% of C"). Rim
  alignment is judged only by the Mandatory Filters. A tolerance in the
  search would skip candidates the filter would accept.
- "Most recent qualifying" keeps the chosen A stable from day to day.

### Step 4: Cup low B

B is the position with the lowest `Low` in the open range (A, C), i.e.
[A + 1, C - 1]. On ties, take the LATEST such position.

### Step 5: Prior-advance base K

K = the lowest `Low` over [max(0, A - 120), A - 1].

If fewer than 60 rows exist before A (i.e. A < 60), reject with
"Unverifiable prior trend (< 60 sessions before left rim)". Do not
silently pass.

### Derived values (used by the rules below)

- `CupBars = C - A`
- `HandleBars = T - C` (sessions from the right rim up to the day before
  the signal day, counting C itself)
- `CupDepth = (High[A] - Low[B]) / High[A]`
- `HandleDepth = (High[C] - Low[D]) / High[C]`
- `Pivot = High[C]`
- `HandleLow = Low[D]`
- `VolRatio = Volume[T] / SMA(Volume, 50) at position T - 1` (the 50-day
  average volume EXCLUDING the signal day)

---

## Mandatory Filters

Evaluate ALL rules below (once anchors are found) and record every failure,
so near-miss analysis can see which rules blocked a stock.

---

### Rule 1: Minimum Liquidity Floor

Description:
Same turnover-based safety floor validated for Breakout Momentum v8 -
reject illiquid stocks so breakout volume is meaningful and exits are
executable without slippage.

Condition:

SMA(Volume * Close, 20) at T >= 50000000
AND
Close[T] >= 50

Notes:
- Turnover (Volume x Close, in Rupees), not raw share count. Rs. 5
  crore/day was checked against this project's cached universe data.

---

### Rule 2: Prior Uptrend Into the Base

Description:
A cup-and-handle is a continuation pattern - the left rim must sit at the
top of a real prior advance. Without this, the detector accepts
dead-cat-bounce shapes inside downtrends.

Condition:

High[A] >= 1.30 * K

Notes:
- O'Neil's 30% minimum prior advance (secondary sources). If NSE backtests
  show this is too restrictive, relax toward 1.15 (canslimTechnical's
  value) in a later version rather than dropping the rule.

---

### Rule 3: Cup Length

Description:
The base must be long enough to be a genuine base (at least 7 weeks,
handle included), and the cup must fit in the available history.

Condition:

30 <= CupBars <= 250
AND
(T - A) >= 35

Notes:
- 7-week (35-session) minimum includes the handle (TraderLion). With A at
  most C - 30 and C at most T - 5, the second clause always holds once
  anchors are found - keep it as an explicit check anyway.
- 250-session cap is set by the ~400-day data budget (cup + 120-bar prior
  advance lookback + handle). Bulkowski's 65-week maximum does not fit.

---

### Rule 4: Cup Depth

Description:
The cup must be a meaningful correction but not a collapse.

Condition:

0.12 <= CupDepth <= 0.35

Notes:
- Measured off the left-rim high (O'Neil convention). Do NOT mix with
  StockCharts' "fraction of prior advance" convention.
- 12-35% per TraderLion (O'Neil's 12-33% via secondary sources). No
  deep-cup / bear-market allowance in v1.

---

### Rule 5: Rounded (U-Shaped) Cup Bottom

Description:
A cup is a rounded base, not a V-shaped spike-and-recovery. Tested three
ways: overall parabola shape, balanced sides, and time spent near the
bottom.

Condition (all must hold):

5a. Parabola fit. Fit `y = a*x^2 + b*x + c` by ordinary least squares
(`numpy.polyfit(x, y, 2)`) to y = Close over positions [A, C], with
x = (position - A) / (C - A), so x runs from 0 to 1. Require:

    a > 0
    AND
    R_squared >= 0.60
    AND
    0.25 <= (-b / (2 * a)) <= 0.75

where `R_squared = 1 - SS_res / SS_tot` of that fit.

5b. Balanced sides:

    (B - A) >= 0.25 * CupBars
    AND
    (C - B) >= 0.25 * CupBars
    AND
    (B - A) >= 20

5c. Time near the bottom. Let
`BottomZone = Low[B] + 0.25 * (min(High[A], High[C]) - Low[B])`. Require:

    (count of positions p in [A, C] with Close[p] <= BottomZone)
      >= 0.15 * (CupBars + 1)

Notes:
- Fit on Close, not High/Low - one long wick distorts a quadratic fit.
- R² 0.60 is the lenient end of the practitioner range (Abiroid default
  0.75). 5b already catches most V-bottoms. 5c is a researcher-proposed
  metric with no published default.

---

### Rule 6: Rim Alignment

Description:
The right rim must recover close to the left rim's level, but must not
already be well above it (that would mean the breakout already happened).

Condition:

High[C] >= High[A] - 0.20 * (High[A] - Low[B])
AND
High[C] >= 0.85 * High[A]
AND
High[C] <= 1.02 * High[A]

---

### Rule 7: Handle Shape

Description:
The handle is a short, shallow, orderly pullback in the upper part of the
base, holding above its key moving averages and drifting down or sideways
(not wedging up).

Condition (all must hold):

    5 <= HandleBars <= 22
    AND
    HandleDepth <= 0.12
    AND
    Low[D] > (High[A] + Low[B]) / 2
    AND
    Close[D] >= SMA(Close, 50) at D
    AND
    Low[D] > SMA(Close, 200) at D
    AND
    HandleSlope <= 0

where `HandleSlope` is the slope from `numpy.polyfit(x, Low, 1)` over
positions [C + 1, T - 1], with x = 0, 1, 2, ... for those positions.

Notes:
- HandleBars is in [5, 22] by construction of Step 1. Keep the check.
- Handles shorter than the 22-day median performed better (Bulkowski).
- "Low[D] above the base midpoint" is the upper-half rule.
- Close >= 50-day SMA is the "above the 10-week MA" rule. Low[D] above the
  200-day SMA follows TraderLion's "the pattern should form above the
  200dma", applied to the handle low.
- HandleSlope > 0 means a wedging (upward-drifting) handle, a known faulty
  base. The numeric test is researcher-proposed.

---

### Rule 8: Handle Volume Dry-Up

Description:
Selling pressure should fade during the handle - volume during the handle
should be below normal.

Condition:

mean(Volume over [C + 1, T - 1]) < SMA(Volume, 50) at C

Notes:
- Doctrine says "contracting volume" with no number; the 1.0x threshold is
  researcher-proposed.

---

### Rule 9: Breakout Close Above the Pivot

Description:
The signal day must close decisively above the handle high. Close-based
(not intraday) because close-based signals do not repaint, and the signal
is only known after the session ends - the backtester enters at the NEXT
session's open (Open[T + 1]), not at Close[T].

Condition:

Close[T] > 1.001 * Pivot

Notes:
- O'Neil's "handle high + 10 cents" has no INR equivalent; 0.1% is the
  proxy.
- "First breakout only" needs no extra check: Step 1 guarantees no High in
  [C + 1, T - 1] exceeds Pivot, so no earlier close can have broken out.
  Likewise no close in the handle can sit below Low[D], since D is the
  lowest low there.

---

### Rule 10: Breakout Volume

Description:
The breakout needs real participation. Volume does not raise the odds of
success (OGA 2022: hit rate ~57% in every volume bucket) but it scales the
size of the move, and very low-volume breakouts are doctrine-invalid.

Condition:

VolRatio >= 1.4

Notes:
- 40-50% above the 50-day average (TraderLion / IBD). The average
  excludes the signal day (computed at T - 1).

---

### Rule 11: Not Extended Beyond the Buy Zone

Description:
A signal day that already closed far above the pivot is a chase: the
backtester's fill (next session's open) will be at least that extended, and
beyond 5% the stop distance to the handle low exceeds the 8% risk cap.

Notes on what this rule cannot catch: the screener only sees day T, so a
gap at Open[T + 1] above 1.05 x Pivot (or below Low[D]) still gets filled.
That is a known limitation of next-open entry, not something this rule can
fix.

Condition:

Close[T] <= 1.05 * Pivot

Notes:
- IBD's 5% buy zone (secondary sources only).

---

## Rejection Rules

Reject the stock if anchor detection rejects (Steps 1-5), or if ANY
Mandatory Filter fails. When anchors are found, evaluate all eleven rules
and report every failure, not just the first.

---

## Ranking Rules

After filtering, rank candidates. Clamp every sub-score to [0, 100] before
weighting.

### Rank Score

Score =
25% Breakout_Volume_Score
+
20% Handle_Tightness_Score
+
15% Cup_Quality_Score
+
15% Market_Breadth_Score
+
15% Relative_Strength_Score
+
10% Sector_Strength_Score

Where:

Breakout_Volume_Score = (VolRatio - 1.4) / (2.5 - 1.4) * 100
(1.4x = 0 points, 2.5x or more = 100 points - OGA's strongest bucket)

Handle_Tightness_Score =
0.5 * ((22 - HandleBars) / 17 * 100)
+ 0.5 * ((0.12 - HandleDepth) / 0.12 * 100)
(each half clamped to [0, 100] before adding; shorter, shallower handles
score higher)

Cup_Quality_Score =
0.5 * ((R_squared - 0.60) / 0.40 * 100)
+ 0.5 * (100 if 0.15 <= CupDepth <= 0.30 else 50)
(R_squared from Rule 5a; the 15-30% depth sweet spot is a vendor finding,
so it only nudges ranking)

Market_Breadth_Score = MarketBreadth
(already 0-100; use the market_breadth parameter directly)

Relative_Strength_Score = (P - 0.70) / 0.30 * 100,
where P = Close[T] / max(High over the last min(252, len(df)) rows,
including T)
(a stock at its 52-week high = 100 points, 30% or more below it = 0;
OHLCV proxy for IBD Relative Strength)

Sector_Strength_Score = max(0, 100 - (SectorRank - 1) * 10)
(Rank 1 = 100, declining 10 points per rank; same formula as the other
strategies in this project)

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
- Ideal Exit Price
- Initial Stop
- Pivot
- Handle Low
- Cup Depth (%)
- Cup Bars
- Handle Bars
- Handle Depth (%)
- Cup R²
- Breakout Volume Ratio (VolRatio)
- % Above Pivot
- Market Breadth
- Rank Score

Where:

Ideal Entry Price Low = Pivot
Ideal Entry Price High = 1.05 * Pivot
(the buy zone; the backtester itself enters at the next session's open,
Open[T + 1])

Ideal Exit Price = Pivot + 0.61 * (High[C] - Low[B])
(Bulkowski's measure rule: right-rim-to-cup-low height scaled by his 61%
target-hit rate, added to the breakout price - a reference level only, not
a fixed target)

Initial Stop = max(0.99 * HandleLow, 0.92 * Close[T])
(the tighter of a structural stop just under the handle low and an 8% cap
below entry - matches the planned paired exit strategy. This is an
ESTIMATE using Close[T] as a stand-in for entry: the real entry is
Open[T + 1], and the exit strategy recomputes the stop from that price)

% Above Pivot = (Close[T] / Pivot - 1) * 100

Notes:
- Entry band, Ideal Exit Price and Initial Stop are display-only
  suggestions for manual order placement. Do NOT use them to change entry
  logic anywhere else (Mandatory Filters, Ranking Rules, backtester).
- Pivot and Handle Low MUST be reported - the paired exit strategy
  recomputes them with the same definitions (Steps 1-2) and they should
  match.

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
