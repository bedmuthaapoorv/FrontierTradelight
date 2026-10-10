# Stock Selection Rules

## Strategy Metadata

Strategy Name: Trendline Bounce v1
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

The previous "trendline" strategy (Mean Reversion Strategy v5) was never
actually a trendline strategy - its entry approximated "near a trendline"
as "price near its own recent low," which is mean reversion, not a real
sloped support line. It also proved fragile: ~80%+ of its trades were
stopped out shortly after entry, and a real, geometrically valid trendline
was never actually fit or tested.

This version builds a genuine trendline the way it is actually done
algorithmically: detect confirmed swing-low pivots in the price history,
connect two of them with a straight line, and require that line to be
(a) rising, (b) formed from pivots genuinely far enough apart in time to
reflect an established trend (not two adjacent dips), and (c) unbroken
since it formed. The entry signal is a classic trendline-bounce: price
dips down to touch that line and closes back above it the same day -
buying the bounce off a real, validated support line, not just "a low
price."

An earlier draft of this v1 spec picked the two MOST RECENT confirmed
pivots with no minimum spacing between them - which, whenever those two
pivots happened to be close together in time, degenerated back into
exactly the old mistake: "price near its own most recent low," just with
slope arithmetic on top. The `i2 - i1 >= 25 trading days` rule in Rule 1
below exists specifically to close that loophole - see Rule 1's notes.

This is a fresh strategy line, not a v-increment of Breakout Momentum -
it trades a fundamentally different setup (pullback-to-a-rising-line vs.
breakout-to-a-new-high) and is not expected to produce similar trade
counts, win rates, or hold times. Back-test independently before comparing
it to Breakout Momentum v6's numbers.

---

## Swing-Low Pivot Detection (Shared Definition)

A trading day at integer position `i` in the OHLCV history (0 = oldest row)
is a **confirmed swing-low pivot** if and only if:

```
Low[i] < Low[i-1]  AND  Low[i] < Low[i-2]  AND  Low[i] < Low[i-3]
AND
Low[i] < Low[i+1]  AND  Low[i] < Low[i+2]  AND  Low[i] < Low[i+3]
```

i.e. its Low is strictly lower than the Low on each of the 3 trading days
immediately before AND after it (a 7-bar fractal low).

Notes:
- This needs 3 trading days of data AFTER `i` to confirm, so the most
  recent 3 rows of the dataset can never themselves be confirmed pivots
  yet - that is correct and expected, not a bug. A trendline is built from
  already-confirmed history, never from today's still-unconfirmed bar.
- Search for pivots only within the most recent 90 trading days (the
  "pivot lookback window"), excluding the last 3 rows (unconfirmable).
  Older pivots are deliberately ignored - a support line fit from pivots
  many months old is no longer relevant to current price action. This is
  wider than a bare "last 60 days" would be, specifically to give Rule 1's
  minimum-spacing requirement below enough history to find a valid pair in.
- If fewer than 2 confirmed pivots exist in that window, this stock fails
  Rule 1 below (insufficient trendline data) - do not fall back to a
  shorter window or a single point.

---

## Mandatory Filters

All rules below MUST pass, in order (later rules may depend on the
trendline computed while checking Rule 1 - if Rule 1 fails, skip
straight to rejection; do not attempt Rules 2-4).

---

### Rule 1: A Valid, Rising, Unbroken Trendline Exists

Description:
Build the trendline from two confirmed swing-low pivots (see the shared
definition above) that are genuinely far enough apart in time to reflect
an established trend, and validate the line is a real, current, ascending
support line - not a flat, falling, or already-broken one.

Condition (all of the following, computed once per stock per day):

1. Let P2 = (i2, Low[i2]) be the MOST RECENT confirmed swing-low pivot in
   the last 90 trading days (excluding the last 3, unconfirmable rows).
2. Let P1 = (i1, Low[i1]) be the NEAREST confirmed pivot before P2, in the
   same 90-day window, such that `i2 - i1 >= 25` (at least 25 trading days
   before P2 - roughly 5 calendar weeks). Skip over any earlier confirmed
   pivot that is closer than that to P2 - it is too recent to establish a
   real trend, it would just be two adjacent dips.
   If no pivot in the window satisfies `i2 - i1 >= 25`, reject with
   "No valid rising trendline" (insufficient trendline data) - do not
   fall back to a closer pair.
3. `Slope = (Low[i2] - Low[i1]) / (i2 - i1)`. Require `Slope > 0`
   (the line must be rising - a flat or falling line is not a support
   line worth buying a bounce off of).
4. Define the trendline's value at any position `j` as:
   `TL(j) = Low[i2] + Slope * (j - i2)`
5. Line must be unbroken since P2 formed: for every trading day `j` from
   `i2 + 1` up to yesterday (today excluded, checked separately in Rule 2),
   require `Close[j] >= TL(j) - (0.75 * ATR(14)[j])`. If Close closed
   more than 0.75x that day's ATR(14) below the line on any day since P2,
   the line is considered broken - reject (a genuinely broken trendline
   is not a valid support line any more, regardless of what price does
   today).

If any of the checks above fails, reject with "No valid rising trendline."

Notes:
- The `i2 - i1 >= 25` minimum spacing is the key difference between this
  being a genuine trendline and just "price bounced off its own most
  recent low" (which is mean reversion wearing a trendline's clothes -
  see the Strategy Rationale). Two swing lows a handful of days apart are
  noise, not a trend; requiring real separation forces the line to reflect
  an actual multi-week pattern of rising lows.
- P1 is chosen as the NEAREST pivot satisfying the spacing rule (not the
  oldest, not a fixed distance) so there is still exactly one deterministic
  candidate line per stock per day - this keeps the same "no ambiguity"
  property the original 2-most-recent-pivots version had, it just adds one
  more condition to which pivot counts as P1.
- The 0.75x ATR tolerance exists so one day of ordinary noise piercing the
  line by a fraction of a percent doesn't invalidate an otherwise-intact
  trendline - it must be a real, ATR-scaled breach to count as broken.

---

### Rule 2: Today Is a Genuine Bounce Off the Trendline

Description:
Price must have actually touched (or come very close to) the trendline
today and closed back above it - the classic trendline-bounce candle,
not a stock merely drifting somewhere near the line.

Condition (using `TL(today)` from Rule 1, where `today` is the most
recent row's position):

```
Low[today]   <= TL(today) * 1.02      (today's low actually tested the line)
AND
Close[today] >= TL(today)             (closed back at/above the line)
AND
Close[today] >  Open[today]           (an up/bounce candle, not a stall)
AND
Close[today] <= TL(today) * 1.06      (still close to the line - not
                                        chasing a move that already ran
                                        well away from it)
```

Notes:
- `Low[today] <= TL(today) * 1.02` allows the day's low to have undershot
  the line very slightly (ordinary intraday noise / a small false break)
  while still counting as a genuine touch.
- The `1.06` ceiling on Close keeps entries close to the actual support
  test - if price already closed 6%+ above the line, the bounce already
  happened and this is a chase, not a bounce entry.

---

### Rule 3: Broader Trend Backdrop Still Intact

Description:
The trendline bounce should be a pullback WITHIN an intact intermediate/
long-term uptrend, not a bounce inside a stock that has already turned
down structurally. Deliberately does NOT require Close > MA(20), since a
genuine pullback to a rising trendline routinely dips below the 20-day
average - that is the whole point of a pullback entry.

Condition:

```
Close > MA(126)
AND
MA(50) > MA(126)
```

Notes:
- Confirms the medium-term average is still above the long-term average
  and price is still above its 6-month average - the bigger trend is
  intact even though price has pulled back short-term.

---

### Rule 4: Momentum Is in a Pullback Zone, Not Crashing or Still Extended

Description:
RSI should reflect a genuine pullback - cooled off from overbought, but
not in a momentum crash. This is a different RSI zone from a breakout
entry (which wants RSI already elevated) precisely because this is the
opposite setup: buying weakness within a trend, not buying strength.

Condition:

```
35 <= Daily_RSI(14) <= 55
```

Notes:
- Below 35 risks catching a genuine breakdown rather than a routine
  pullback; above 55 means the stock has not meaningfully pulled back at
  all and this would just be chasing continued strength (that setup is
  what Breakout Momentum v6 already covers).

---

### Rule 5: Minimum Liquidity Floor

Description:
Same liquidity safety floor used by every strategy version in this
project - reject illiquid stocks so exits are executable without slippage.

Condition:

```
MA(Volume, 20) >= 100000
AND
Close >= 50
```

---

### Rule 6: Sector Strength

Description:
Same sector filter used by every strategy version in this project.

Condition:

```
SectorRank <= 10
```

---

### Rule 7: Market Breadth Filter

Description:
Pause new entries when the broader market is itself broad-based weak,
even if this individual stock's trendline setup looks valid in isolation.

Condition:

```
MarketBreadth >= 40
```

Notes:
- Set slightly looser than Breakout Momentum v6's 45: a pullback-to-
  support entry is inherently a lower-momentum, counter-trend-within-a-
  trend setup, so it does not need quite as strong a broad-market backdrop
  as a breakout-to-new-highs entry does. Re-validate this threshold
  against this strategy's own backtest results rather than assuming it
  transfers from Breakout Momentum's number.

---

## Rejection Rules

Reject stock if ANY mandatory filter fails. Rule 1 must be evaluated
first; if it fails, do not evaluate Rules 2-4 (there is no trendline to
check a bounce or backdrop against).

---

## Ranking Rules

After filtering, rank candidates.

### Rank Score

Score =
30% Trendline_Quality_Score
+
25% Sector_Strength_Score
+
25% Bounce_Precision_Score
+
20% RSI_Pullback_Score

Where:

Trendline_Quality_Score = `min(100, Slope_As_Pct_Per_Day * 4000)`, where
`Slope_As_Pct_Per_Day = Slope / Low[i2]` (the trendline's slope expressed
as a % of price per trading day, so it is comparable across stocks at
different price levels).
(A very shallow/flat rising line scores low; a moderately steep, healthy
uptrend line scores higher, capped at 100 so an extreme/unsustainable
slope does not dominate the score.)

Sector_Strength_Score = max(0, 100 - (SectorRank - 1) * 10)
(Rank 1 = 100, declining 10 points per rank)

Bounce_Precision_Score = `max(0, 100 - ((Close[today] - TL(today)) / TL(today) * 100) * 25)`
(Close exactly at the trendline = 100 points, 4% above it = 0 points -
rewards a tighter, more precise bounce over one that already ran further
from the line.)

RSI_Pullback_Score = `max(0, 100 - abs(Daily_RSI - 45) * 4)`
(Rewards RSI closest to 45, the middle of the pullback zone; 0 points at
RSI 20 or 70.)

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
- Swing Duration (Days)
- Trendline Value (Today)
- Trendline Slope (% per day)
- Daily RSI(14)
- 20D Average Volume
- Rank Score

Where:

Ideal Entry Price Low = Trendline Value (Today) (buying right at the
support line is the ideal fill - matches what the setup is actually
betting on).

Ideal Entry Price High = Close (today's signal close - the realistic
worst-case fill, since the backtester itself enters at this exact close
price).

Ideal Exit Price = Ideal Entry Price Low + 2.5 * ATR(14) (an illustrative
target matching the trailing-stop distance used by this entry's paired
exit strategy - the actual exit has no fixed take-profit and lets the
trailing stop run winners further, so this is a "reasonable swing target"
for display, not a cap).

Swing Duration (Days) = "5-40" (the Holding Period range from this
strategy's metadata above - a real trade's actual exit day is whatever
the ATR trailing stop / 30-day early-failure cut in exit_rules.md
produces, this column is only the expected planning range for manual
order placement).

Notes:
- Unlike Breakout Momentum v6's entry range (which spans UP TOWARD a
  ceiling being broken), this range spans from the ideal support-line
  fill UP TO today's actual close, because a bounce entry's best-case
  price is the line itself and its worst case is wherever price already
  closed today.
- Do NOT use this band, the Ideal Exit Price, or the Swing Duration to
  change entry/exit logic anywhere else (Mandatory Filters, Ranking
  Rules, backtester) - they are display-only suggestions for manual
  order placement, same as in prior strategy versions.

Sort:

Rank Score DESC

Limit:

Top 20 Stocks
