# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: Cup and Handle Exit Strategy v1
Applies To: Cup and Handle Breakout v1 (rules.md) specifically - the
Pivot and HandleLow definitions below are copied from that entry spec's
Pattern Anchor Detection Steps 1-2, and every threshold (handle-low stop,
8% cap, 11-21 session failed-breakout window, 3.0x/4.0x ATR(22) trail,
20%-in-15-sessions big-winner hold to session 40, 30-session stagnation
stop, 90-session MaxHold) is sized for that setup. Do NOT pair it with a
different entry without re-validating - with any other entry, Pivot and
HandleLow below would describe a pattern that was never there.
Timeframe: Daily (closing price only, no intraday)

---

## Data Availability Note

Only the entry price/date and each stock's own daily OHLCV history (before
and after entry) are available. There is NO Nifty benchmark index data, NO
earnings calendar, NO market-breadth value and NO values from the entry
screener (Pivot, Handle Low, Rank Score etc. are NOT passed in) - anything
the exit needs must be recomputed here from price history. Every rule below
must be computable from OHLCV alone.

---

## Strategy Rationale

Built from `reports/Cup and handle exit rules.md` (project root), which
extends `reports/Cup and handle breakout rules.md`. Read the exit report
before changing any number - it grades every threshold by evidence.

The design is a layered pipeline, because each layer solves a separate
problem:

1. **Initial stop = tighter of handle low and 8%.** Bulkowski: the handle
   low is "a good place to put a stop". O'Neil: never lose more than 7-8%
   from the actual fill. The entry caps handle depth at 12%, so for a
   shallow handle the structural stop governs, and for a deep handle (or an
   entry that gapped high into the buy zone) the 8% cap governs. Rigorous
   studies (Kaminski & Lo; Lo & Remorov) say stops on single stocks cut
   risk and tail losses but do not raise average returns - this stop is
   tail control, not an alpha source.

2. **No exit on a close below the pivot alone.** Bulkowski: 62% of cups
   throw back toward the breakout price, about 10 days for the round trip,
   and 65% of those recover; high-volume breakouts (which the entry's 1.4x
   gate selects) throw back 70% of the time. Horizontal Breakout Exit v1's
   `Close < 0.98 * Pivot` within 10 days would cut many of the best cup
   trades. Instead, a failed breakout is flagged only in sessions 11-21
   (after the normal throwback window), and only for trades that never
   made real progress. This rule is researcher-proposed, not tested.

3. **No move to breakeven.** Bulkowski's test on 2,333 double bottoms:
   moving the stop to breakeven cut winning trades from 1,727 to 1,042 and
   net profit per share from $2.17 to $1.45. Minervini (secondary source)
   does move to breakeven, but in a leveraged quick-profit style that is
   the opposite of this design. The 3x ATR trail passes breakeven on its
   own once a trade is up about 3 ATRs.

4. **Wide chandelier trail: highest close - 3.0 x ATR(22), 4.0x for big
   winners.** LeBeau's chandelier default is 22 periods / 3x ATR.
   Bulkowski's trailing-stop tests improved steadily as stops got wider,
   and trails tighter than ~36% lost money vs buy-and-hold in his
   571-stock test. Nothing tighter than 3x ATR.

5. **Big-winner hold (O'Neil's 8-week rule).** A gain of 20%+ within the
   first 15 sessions (~3 weeks) means hold through session 40 (~8 weeks).
   During that floor the trail cannot exit - only the initial stop or a
   close below the 50-day average on above-average volume can. After
   session 40, the 4.0x trail takes over.

6. **Stagnation stop at session 30.** A trade that never got 10% up and is
   still under +5% after 30 sessions exits. No rigorous evidence exists for
   any time stop; 30 sessions sits beyond Bulkowski's ~21-session throwback
   horizon, and 47% of cups retrace substantially within two months.

7. **MaxHold 90 sessions** - matches the entry's "Trend Trade (1-90 Days)"
   and the Sell tab's hardcoded "/90 trading days".

No profit target and no partial exits in v1. The backtester supports only
one exit per trade, so scaling out (Minervini's half at +2R, IBD's partial
at +20-25%) cannot be built, and Bulkowski's measured-move target needs the
cup low, which can sit beyond the live Sell tab's ~135 rows of history. The
one target-vs-trail backtest found (Arthur Hill, S&P 500, MA-crossover
entry) favoured targets, so a paired variant "Cup and Handle Exit Strategy
v1-T" (full exit at Close >= 1.25 x entry for non-big-winners) is the
planned comparison - do not add it here.

Left out of v1 on purpose: climax-top sells (preconditions rarely met
within 90 sessions, no backtest exists), circuit-lock exit deferral (NSE
lower-circuit lock frequency must first be measured from project data),
and any intraday-low stop trigger.

Backtest caveats: the leaderboard is pre-cost (real NSE delivery round
trips cost ~0.24%, mostly STT), so a rule that trades more often looks
better than it is. Subtract costs from the trades CSV when comparing
variants. Clear `data/backtest_cache/` before trusting dates - those files
predate the jugaad_data date fix and are stamped a day early.

---

## Entry Reference

Entry Price: Opening price on the trading day immediately after the
signal day (Open[T + 1]). This is `entry_price` as passed in. `future_df`
row 0 is that entry day.

Notes:
- The entry can gap ABOVE 1.05 x Pivot or BELOW 0.99 x HandleLow; the
  screener cannot see the next open. If it gaps below HandleLow, the
  initial stop sits above entry_price and Condition 1 fires on session 1's
  close unless price recovers by then. That is intended - the structure
  failed before the trade began. Do NOT add a guard against it.

---

## Data Conventions (READ FIRST)

- Both `signal_history_df` and `future_df` have a DatetimeIndex and
  lowercase columns `open`, `high`, `low`, `close`, `volume`.
- Use integer positions (`.iloc`) for every row reference, never index
  labels.
- **Session numbering:** session s (s = 1, 2, 3, ...) is `future_df` row
  s - 1. Session 1 is the entry day, and its close IS checked for exits.
  `SessionsHeld` on session s is s.
- **Combined history for indicators on session s:**
  `combined = pd.concat([signal_history_df, future_df.iloc[:s]])`, then
  drop duplicate index labels keeping the LAST occurrence
  (`combined = combined[~combined.index.duplicated(keep="last")]`). The
  live Sell tab passes the entry-day bar in BOTH frames - without this
  de-duplication, ATR and SMA values double-count that bar.
- **Volume may be NaN** on the most recent bar in live use (a typed-in live
  price has no volume). Any condition that requires a volume comparison is
  treated as NOT met when either side is NaN.
- Trigger and fill are both on the daily close: when a condition fires on
  session s, return `ExitDate` = that row's index label and `ExitPrice` =
  that row's `close`. Never use intraday high/low for triggering or fills.

---

## Pre-Trade Calculation (Computed Once at Entry)

### Step 1: Locate the signal day T

T is the LAST row of `signal_history_df` whose date is strictly before
`entry_date` (compare normalized dates:
`signal_history_df.index.normalize() < pd.Timestamp(entry_date).normalize()`).
Let p be T's integer position in `signal_history_df`.

Notes:
- In the backtest every row of `signal_history_df` is before entry_date,
  so T is simply the last row. In the live Sell tab `signal_history_df`
  ends ON the entry date, so "strictly before" is what makes this work in
  both places. Do not just take the last row.

### Step 2: Recompute Pivot and HandleLow (entry spec Steps 1-2)

Using `signal_history_df` rows only, with p from Step 1:

- C = the position with the highest `high` in the window [p - 22, p - 5]
  (inclusive). On ties, take the LATEST such position.
- `Pivot = high` at position C.
- D = the position with the lowest `low` in [C + 1, p - 1] (inclusive). On
  ties, take the LATEST such position.
- `HandleLow = low` at position D.

If p < 23 (not enough rows for the window) or any value is NaN, set
`Pivot = None` and `HandleLow = None`. Do NOT return None and do NOT skip
the trade - fall back as described in Step 3.

### Step 3: Initial stop and risk unit

- If HandleLow is available:
  `InitialStop = max(0.99 * HandleLow, 0.92 * entry_price)`
- Otherwise: `InitialStop = 0.92 * entry_price`

`R = entry_price - InitialStop` (used only for state reporting; may be
negative if the entry gapped below the handle low).

---

## Daily State Variables

Trailing_SL    : Starts at InitialStop. Updated daily. Never decreases.
Highest_Close  : Highest close since entry, including the current session.
                 Starts at entry_price before session 1 is processed.
ATR_Multiplier : Starts at 3.0. Becomes 4.0 (once, irreversibly) when the
                 big-winner flag fires.
BigWinner      : False at entry. Becomes True (once, irreversibly) per
                 Step 2 below.

---

## Daily Update Logic

For each session s = 1, 2, 3, ... (row s - 1 of `future_df`), run these
steps at the close, BEFORE checking exit conditions, using only data up to
and including that session.

### Step 1: Update Highest Close

If Close > Highest_Close:
    Highest_Close = Close

### Step 2: Big-Winner Flag

If s <= 15 AND Close >= 1.20 * entry_price:
    BigWinner = True
    ATR_Multiplier = 4.0

Once set, both stay set for the rest of the trade even if price falls
back below +20%.

### Step 3: Ratchet the Trailing Stop

ATR_Today = ATR(22) (`pandas_ta.atr(high, low, close, length=22)`, last
value) computed on the de-duplicated `combined` frame for session s.

If ATR_Today is a valid number:
    Candidate_SL = Highest_Close - (ATR_Multiplier * ATR_Today)
    If Candidate_SL > Trailing_SL:
        Trailing_SL = Candidate_SL

Trailing_SL never decreases. If ATR_Today cannot be computed, leave
Trailing_SL unchanged (it is never below InitialStop, so the trade stays
protected).

### Step 4: Big-winner hold status

HoldFloorActive = (BigWinner AND s <= 40)

---

## Exit Conditions

Check once per session at the close, AFTER the daily update logic. Evaluate
in this order and exit on the first condition that fires.

### Condition 1: Initial Stop

If Close <= InitialStop:
    EXIT at that session's close.
    Reason Tag: "InitialStop"

Notes:
- Active every session, including session 1 and during the big-winner
  hold floor.
- Close-based on purpose: an overnight gap below the stop is realized at
  that session's close, which already includes the gap. Never fill at the
  stop price itself.

---

### Condition 2: Failed Breakout

If 11 <= s <= 21
AND Pivot is available
AND Close < Pivot
AND Highest_Close < 1.05 * entry_price:
    EXIT at that session's close.
    Reason Tag: "FailedBreakout"

Notes:
- Deliberately does NOT fire in sessions 1-10: an ordinary throwback below
  the pivot is the most common post-breakout behaviour for this pattern.
- The progress test spares a trade that already ran 5%+ and is now
  retesting the pivot.
- If Pivot is unavailable (Pre-Trade Step 2 fallback), this condition
  never fires.

---

### Condition 3: Big-Winner 50-Day Break

If HoldFloorActive
AND Close < SMA(close, 50)
AND Volume > SMA(volume, 50):
    EXIT at that session's close.
    Reason Tag: "BigWinner50DMA"

Where both SMAs are the 50-row simple means on the de-duplicated
`combined` frame for session s, ending at session s (inclusive). If either
SMA cannot be computed, or Volume is NaN, this condition is NOT met.

---

### Condition 4: ATR Trailing Stop

If NOT HoldFloorActive
AND Trailing_SL > InitialStop
AND Close <= Trailing_SL:
    EXIT at that session's close.
    Reason Tag: "TSL"

Notes:
- `Trailing_SL > InitialStop` keeps the tags clean: until the trail has
  risen above the initial stop, Condition 1 is the stop that applies.
- Suppressed during the big-winner hold floor (sessions up to 40 for
  big winners); the trail keeps ratcheting during the floor, it just
  cannot exit. From session 41 it applies again, at 4.0x.
- There is no profit target - this trail is the only exit for a winning
  trade outside the hold floor.

---

### Condition 5: Stagnation (Time) Stop

If s >= 30
AND Close < 1.05 * entry_price
AND Highest_Close < 1.10 * entry_price:
    EXIT at that session's close.
    Reason Tag: "TimeStop"

Notes:
- A "no progress" exit, not a cap on winners: a trade that ever closed 10%+
  above entry is never stopped by this rule.

---

### Condition 6: Maximum Holding Period

If s >= 90:
    EXIT at that session's close.
    Reason Tag: "MaxHold"

---

## Exit Priority Order

1. InitialStop     <- every session, including during the hold floor
2. FailedBreakout  <- sessions 11-21 only, no-progress trades only
3. BigWinner50DMA  <- only while the big-winner hold floor is active
4. TSL             <- chandelier trail, suppressed during the hold floor
5. TimeStop        <- session 30+, no-progress trades only
6. MaxHold         <- session 90

Only one exit tag is assigned per trade.

---

## Fallback

If no condition fires before `future_df` ends, return None. The backtester
then holds the trade to the end of the date range and closes it at the last
available close, tagged "RangeEnd" - do NOT implement RangeEnd here.
Returning None means "still open / hold to range end", never "skip this
trade". Every missing-data path above already falls back to a defined stop
(0.92 x entry_price), so never return None just because Pivot, HandleLow,
ATR or an SMA could not be computed.

---

## State Inspection (For HOLD Explanations, Not Used By The Backtester)

In addition to resolve_exit(), also implement:

describe_state(entry_price, entry_date, signal_history_df, future_df)

It runs exactly the same Pre-Trade Calculation and Daily Update Logic as
resolve_exit() over every row of `future_df`, but does not exit - it
returns the state as of the last row.

Let EffectiveStop = InitialStop if (HoldFloorActive or Trailing_SL <=
InitialStop) else Trailing_SL.

Return a dict with:
- TrailingStop          (EffectiveStop - the stop that would actually
                         trigger today; the Sell tab displays this key)
- DistanceToStopPct     ((LastClose - EffectiveStop) / LastClose * 100)
- DaysHeld              (number of rows in future_df)
- DaysToMaxHold         (90 - DaysHeld, floored at 0)
- LastClose             (last close in future_df)
- HighestClose          (Highest_Close)
- InitialStop
- Pivot                 (None if unavailable)
- HandleLow             (None if unavailable)
- ATRMultiplier         (3.0 or 4.0)
- BigWinner             (true/false)
- HoldFloorActive       (true/false)
- InFailedBreakoutWindow (true if 11 <= DaysHeld <= 21 and
                          Highest_Close < 1.05 * entry_price)

Return None only if `future_df` is empty.

The backtester never calls this - only the live Sell tab does.
