# Codebase Exit Mechanics: What a Cup-and-Handle exit_rules.md Must Respect

Read-only investigation of `D:\git-repos\FrontierTradelight`, 2026-10-06.
Paths are relative to `Strategies/Default/` unless stated otherwise. The US
backend (`Strategies/US/`) uses the same exit contract: `generate_exit_strategy.py`
is byte-identical, `backtest.py` uses the same entry/exit code, and `sell_screener.py`
differs only in its data source.

---

## 1. Pipeline overview

```
exit_rules.md --(Gemini, generate_exit_strategy.py)--> generated_exit_strategy.py
     |                                                     |
     |                                    backtest.py (_open_and_resolve_trade)  -> resolve_exit()
     |                                    sell_screener.py (evaluate_holding)    -> resolve_exit() + describe_state()
     +-- saved via UI -> previous version backed up to Strategies/ExitRules_backup/
```

- Compiler: `generate_exit_strategy.py:12-122` sends the markdown to
  `gemini-3.1-flash-lite` at temperature 0.0 (lines 106-113), strips code
  fences and writes `generated_exit_strategy.py` (lines 140-141). It is a small
  "flash-lite" model, so the spec must be explicit: name exact row positions,
  exact formulas, and exact priority order.
- The UI button runs `generate_exit_strategy.py` with cwd=APP_DIR
  (`api/routers/jobs.py:47-49`). Saving `exit_rules.md` backs up the previous
  content (`api/routers/markdown_files.py:48-60`, `backup_utils.py:31-41`).
- The exit is global. Only one `generated_exit_strategy.py` exists, and every
  backtest trade uses it (`backtest.py:57, 289`). "Active Strategy" is only a label
  copied from the entry result into the trade row (`backtest.py:452, 319`;
  set by the router in `generate_screener.py:343`). It does NOT route to
  different exits.
- Live holdings can each pin a saved exit version: the `ExitRule` column in
  `data/holdings.csv` holds an `ExitRules_backup/` filename, compiled on
  demand into `generated_exit_strategies/<name>.py` (`sell_screener.py:34-63`,
  `api/routers/holdings.py:16-25`).

## 2. Required structure of exit_rules.md

There is no exit-specific guide. `RULES_GUIDE.md` and `PLUGIN_GUIDE.md` cover
entry rules and plugins only. `BACKTEST_GUIDE.md:70-103` is the only
documentation of the exit flow. The parser itself needs very little:

- **The only line the code parses:** `Exit Strategy Name: <name>` on a single line. It is read
  by regex `Exit Strategy Name:\s*(.+)` (`backup_utils.py:8-13`, called from
  `backtest.py:635-637`). This name is half of the leaderboard key
  `(Strategy Name, Exit Strategy Name)` in `data/strategy_stats.csv`
  (`stats_utils.py:39-74`) and also sets the backup filename slug
  (`backup_utils.py:16-28`). Use a new, distinct name, e.g.
  `Cup and Handle Exit Strategy v1`.
- **Everything else is convention.** Both existing specs use this layout, and
  copying it gives the LLM the most predictable result:
  (`exit_rules.md`, `ExitRules_backup/mean_reversion_exit_strategy_v1_exit_rules_20260927_155105.md`):
  1. `# Exit Strategy Rules`
  2. `## Strategy Metadata` (Exit Strategy Name, Applies To, Timeframe)
  3. `## Data Availability Note` (OHLCV only, no index, no earnings)
  4. `## Strategy Rationale`
  5. `## Entry Reference` (states the entry price convention)
  6. `## Pre-Trade Calculation (Computed Once at Entry)`
  7. `## Daily State Variables`
  8. `## Daily Update Logic` (Step 1..n, run BEFORE the exit checks)
  9. `## Exit Conditions` (Condition 1..n, each with a `Reason Tag: "..."`)
  10. `## Exit Priority Order`
  11. `## Fallback` (tells the LLM NOT to implement RangeEnd; see
      `generate_exit_strategy.py:96-99`)
  12. `## State Inspection (For HOLD Explanations, Not Used By The Backtester)`
      (asks for `describe_state()`; see section 3.2)
- The existing Horizontal Breakout spec is the current `exit_rules.md` (329
  lines). Its backup `ExitRules_backup/horizontal_breakout_exit_strategy_v1_exit_rules_20260927_155304.md`
  has the same headings (only the "Applies To" strategy name differs).

## 3. Compiled function contract

### 3.1 `resolve_exit(entry_price, entry_date, signal_history_df, future_df)`

The prompt defines this signature (`generate_exit_strategy.py:30-69`):

| Arg | Backtest value | Source |
|---|---|---|
| `entry_price` | `float(future["open"].iloc[0])`, i.e. Open of T+1 | `backtest.py:284` |
| `entry_date` | `future.index[0]`, a pd.Timestamp for T+1 | `backtest.py:283` |
| `signal_history_df` | `full_df` rows with date <= signal day T. **Last row = T.** Includes warm-up history back to `start - 400 calendar days` | `backtest.py:285, 244, 59` |
| `future_df` | rows with T < date <= backtest end date. **Row 0 = entry day T+1** | `backtest.py:279` |

- Columns are lowercase `open, high, low, close, volume`, plus
  `delivery_pct` (it may be NaN in older caches) (`backtest.py:204-227`). The index is
  dates in ascending order. Backtest data is deduped and split/bonus back-adjusted
  (`backtest.py:230-231`).
- The signature has NO other inputs. `evaluate_stock()`'s `Details` dict (Pivot,
  Handle Low, ...) is never passed to the exit. Only `ClosenessScore` and
  "Active Strategy" survive into the trade row (`backtest.py:450-453`). **The exit
  must recompute Pivot / HandleLow from `signal_history_df`.**
- **Return value:** either a dict `{"ExitDate", "ExitPrice", "ExitReason"}` or
  `None` (`generate_exit_strategy.py:51-68`). The caller casts `ExitPrice` to
  float and normalizes `ExitDate` with `pd.Timestamp(...).date()`
  (`backtest.py:293-306`).
- **Error handling:** the generated code must wrap its body in try/except and
  return None on any error (`generate_exit_strategy.py:73-76`). The caller also
  catches exceptions (`backtest.py:288-291`). **None, or an exception, means "held
  to the end of the range": the caller closes at the last close, tagged
  `RangeEnd` (`backtest.py:297-300`).**
- The entry-time indicator rule: compute only from `signal_history_df`, never
  from `future_df` (`generate_exit_strategy.py:41-44, 93-95`).
- **Trigger price:** by default, use the day's close only. Use intraday high/low
  only if the spec explicitly says so (`generate_exit_strategy.py:48-49`). The
  ExitPrice may be "the appropriate trigger price if exit_rules.md specifies one"
  (lines 57-60), and the backtester uses whatever float is returned.
- **pandas_ta:** don't hardcode output column names. `ta.atr` returns a Series
  (`generate_exit_strategy.py:84-92`).

### 3.2 `describe_state(...)`: optional, live Sell tab only

- The compiler prompt never mentions it. It exists only because the spec's own
  "State Inspection" section asks for it (`exit_rules.md:294-329`).
  `sell_screener.py:165-167` uses `getattr`, so if it is missing, the Sell tab
  shows "Exit condition not met yet."
- The backtester never calls it.
- `sell_screener.describe_hold_reason` reads only `TrailingStop`,
  `DistanceToStopPct`, `DaysHeld` and `DaysToMaxHold`
  (`sell_screener.py:177-186`). **It hardcodes "/90 trading days held"**
  (line 184). Other keys (e.g. `AtRiskOfFailedBreakout`) are computed but never
  displayed. If the new exit has no trailing stop, the HOLD text will be
  generic unless it still returns `TrailingStop`/`DistanceToStopPct`, for
  example reporting the active stop level under the `TrailingStop` key.
  A MaxHold other than 90 will be displayed wrongly unless sell_screener is changed.

### 3.3 Current compiled example (reference for the LLM's style)

`generated_exit_strategy.py:17-60`:
- `days_held = i + 1` while iterating `future_df` (line 29). **The entry day is
  day 1 and its close is checked for exits** (an exit on the entry day is possible).
- Pivot is `signal_history_df['close'].rolling(20).max().iloc[-1]` (line 6), so it
  treats the last row of `signal_history_df` as the signal day.
- ATR is recomputed daily by concatenating `signal_history_df` with
  `future_df[:i+1]` (line 39).
- Checks run in the priority order the spec gives, and the first hit returns (lines 46-56).

## 4. Backtest execution facts (backtest.py)

| Topic | What the code does | Cite |
|---|---|---|
| Entry fill | **Next trading day's OPEN after the signal day T**, not Close[T] | `backtest.py:16, 265, 279-284`; `BACKTEST_GUIDE.md:17` |
| Exit trigger and fill | Entirely up to `resolve_exit`: the date and price it returns. Default is close-based (prompt) | `backtest.py:293-296`; `generate_exit_strategy.py:48-60` |
| Stop evaluation | Close-based unless the spec explicitly asks for intraday low | `generate_exit_strategy.py:48-49` |
| Same-day exit (entry day close) | Supported. Portfolio sim closes same-day round trips correctly | `backtest.py:540-549` |
| Fallback | Last close in range, tag `RangeEnd`, applied by the caller | `backtest.py:297-300` |
| Max hold | Not enforced by the backtester. Only the exit code enforces it (count rows of `future_df`) | `backtest.py:264-320` |
| Partial exits / scale-out | **NOT supported.** One dict per trade: one ExitDate, one ExitPrice, one ExitReason | `backtest.py:293-320`; `generate_exit_strategy.py:53-63` |
| Pyramiding / adding | **NOT supported** | same |
| Overlapping trades, same symbol | Allowed. Every signal opens an independent trade | `backtest.py:25-26` |
| Trade P&L | `(exit - entry)/entry*100` on a flat Rs.100 stake | `backtest.py:307` |
| Transaction costs / slippage / STT | **None modeled** | `backtest.py:307`; `BACKTEST_GUIDE.md:181-183` |
| Position sizing | Equal weight: `total_equity / max_concurrent_positions`, recomputed at each entry. The exit cannot influence sizing (no risk-based sizing) | `backtest.py:473-538` |
| Slots | `--max-positions`, default 10 (the UI passes its own value). Excess signals on a day are ranked by `ClosenessScore` descending; the rest are unfunded | `backtest.py:521-538, 599`; `api/routers/backtest.py:45-60` |
| Capital recycling | Exits are processed before entries on the same date | `backtest.py:512-519` |
| Equity curve | `cash + sum(allocated cost of open positions)`, **i.e. open positions held AT COST, not marked to market**. Rows exist only on entry/exit dates | `backtest.py:511, 551` |
| Trading-day counting | Rows of `future_df` (calendar gaps and missing bars are skipped) | `generated_exit_strategy.py:28-29` |
| Trade CSV columns | Symbol, SignalDate, EntryDate, EntryPrice, ExitDate, ExitPrice, ExitReason, ClosenessScore, ProfitRs, Active Strategy, Funded, AllocatedCapital | `backtest.py:457-461, 553-554` |

### Metrics and leaderboard (backtest_runner.py, stats_utils.py)

- `compute_metrics` (`backtest_runner.py:56-83`) computes:
  - CAGR from the equity curve's first and last dates.
  - MaxDD from `cummax` of the at-cost equity curve.
  - Sharpe as `mean/std` of `pct_change` between consecutive equity-curve rows
    (irregular dates), annualized by sqrt(252).
  - **Composite Score = (CAGR/100 x Sharpe) / |MaxDD/100|.**
- Because positions are held at cost, unrealized drawdowns on open trades are
  invisible. An exit that holds losers longer is not penalized in MaxDD until
  the loss is realized.
- Stats are recorded only if the run used exactly the benchmark range
  2021-01-01 to 2026-01-01 (`constants.py:10-11`; `backtest_runner.py:49-53,
  86-101`).
- `strategy_stats.csv` columns are: Strategy Name, Exit Strategy Name, CAGR
  (%/yr), Max Drawdown (%), Number of Trades (funded count), Composite Score,
  Rules Content Hash, Last Updated (`stats_utils.py:22`;
  `backtest_runner.py:119-131`). Upserts are keyed by the (entry, exit) name pair
  (`stats_utils.py:39-74`).

## 5. Live Sell screener (sell_screener.py)

- State available: only `Symbol, EntryPrice, EntryDate, CurrentPrice
  (optional manual live price), ExitRule (optional version)`
  (`api/routers/holdings.py:16`; `sell_screener.py:25-31`). There is no signal
  date, Pivot or HandleLow column.
- History: `fetch_stock_history` from `entry_date - 200 calendar days` to today
  (`sell_screener.py:66-79`). That is **about 135 trading rows before entry**,
  so anything needing more (e.g. SMA200, or re-detecting the left rim A, which can
  sit up to 250+ bars back) cannot be computed live. resolve_exit then returns
  None, which shows as a silent HOLD.
- Live data is NOT split-adjusted or deduped (no `_adjust_for_splits_and_bonuses`
  call). Volume is renamed, but `DELIVERY %` is not.
- **The slicing differs from the backtest** (`sell_screener.py:120-121`):
  - `signal_history = rows with date <= EntryDate`, so its **last row is the
    ENTRY day, not the signal day**.
  - `future = rows with date >= EntryDate`, so the entry-day bar appears in
    both frames.
  - Consequence 1: an exit that locates the signal day as
    `signal_history_df.iloc[-1]` lands on T in the backtest, but in live it lands on
    the holding's EntryDate. That is T+1 if the user follows the backtest
    convention (buy at next open), which shifts every window by one bar.
  - Consequence 2: if the user records EntryDate = T (bought at the signal
    close, as the entry spec assumes), the live `signal_history` last row = T (it
    matches), but `future_df` row 0 = T, so day counts run one higher than in the
    backtest and T's close is tested for exits.
- `apply_live_price` (`sell_screener.py:82-107`) appends a synthetic bar for
  today with open=high=low=close=CurrentPrice and **no volume (NaN)**, or folds
  the price into today's bar.
- A SELL is reported if `resolve_exit` returns any exit anywhere since entry
  (`sell_screener.py:141-150`), so an exit that fired days ago still shows as SELL.

## 6. Date off-by-one (jugaad_data 18:30 UTC)

- **Fixed in code:** `nse_utils.fetch_stock_history` adds `+1 day` to
  `DATE` (`nse_utils.py:28-45`). The fix landed in commit `3d862b2`
  (2026-09-29).
- **But the backtest reads its on-disk cache first** (`backtest.py:202-209`), and
  the cache never expires. All 100 files in `data/backtest_cache/` are
  `*_2024-08-21_2026-09-25.csv`, written 2026-09-25, BEFORE the fix. Their
  dates are uncorrected: for example, `ABB_2024-08-21_2026-09-25.csv` contains 105
  "Sunday" rows and about 1 Friday (verified by day-of-week count), and its rows are
  stamped `YYYY-MM-DD 18:30:00`.
- Impact on exits: none on the relative logic. Signal, entry and exit are all
  shifted equally, and bars are counted by row. Calendar labels (SignalDate,
  EntryDate, ExitDate) are one day early, and `members_as_of(day)` is looked
  up one day early.
- The benchmark range (2021-2026) is not in this cache, so a benchmark run
  fetches fresh, corrected data. Mixing old and new cache files for the same
  range would misalign cross-sectional snapshots (`backtest.py:420` requires
  `dates[p] == day`). Recommend clearing `data/backtest_cache/` before relying on
  dates.
- `sell_screener` always fetches fresh, so its dates are correct
  (`sell_screener.py:69`).

## 7. Cup-and-handle specifics: recomputing Pivot and HandleLow in the exit

The entry spec is
`Strategies/Rules_backup/cup_and_handle_breakout_v1_rules_20261006_133828.md`.
It defines:
- C = latest position of max `High` over [T-22, T-5] (lines 100-104)
- `Pivot = High[C]` (line 163)
- D = latest position of min `Low` over [C+1, T-1] (lines 115-118)
- `HandleLow = Low[D]` (line 164)
- The entry requires len(df) >= 250 (lines 85-86)
- It says the exit "recomputes them with the same definitions (Steps 1-2)"
  (lines 523-525)

**Locating T from the exit inputs:**
- **In the backtest**, T is the last row of `signal_history_df` (n-1), because
  `signal_history = full_df[date <= signal_day]` (`backtest.py:285`). With n =
  len(signal_history_df), in pandas:
  - `Pivot = signal_history_df['high'].iloc[n-23 : n-4].max()` (positions T-22..T-5)
  - C = the last position in that slice where high == Pivot
  - `HandleLow = signal_history_df['low'].iloc[C+1 : n-1].min()` (positions C+1..T-1)
  - About 23 rows are needed, always available in the backtest (the entry required 250).
- **In live** (`sell_screener.py:120`), the last row is the EntryDate (see section 5).
  A rule that works in both modes is: **"T = the last row of
  `signal_history_df` whose date is strictly before `entry_date`"**:
  - Backtest: every row qualifies, so T = the last row, which is correct.
  - Live: correct if the holding's EntryDate is the actual fill day T+1 (the
    backtest convention).
  - It is wrong only if the user records EntryDate = T. The spec should tell users
    to record the fill day (T+1).
  - Write this into the spec explicitly. Otherwise the LLM will use `iloc[-1]`,
    as the current generated code does (`generated_exit_strategy.py:6`).
- Pivot and HandleLow need only about 23 bars, so live's ~135 bars are enough. Do not make
  the exit depend on A, B, K or SMA200, which may be uncomputable live.
- **Entry spec mismatch:** the entry spec says the backtester enters at Close[T]
  (Rule 9 lines 366-368, Rule 11 lines 404-406, Output lines 506-515). **The code
  enters at Open[T+1]** (`backtest.py:283-284`). Implications for the exit:
  - Anchor every percentage stop to `entry_price` (= Open[T+1]), not Close[T].
  - Open[T+1] can gap above 1.05 x Pivot (the 5% chase limit is checked only on
    Close[T]), so the HandleLow stop can sit more than 8% below the entry. The
    `max(0.99*HandleLow, 0.92*entry)` design handles this.
  - Open[T+1] can gap below Pivot or even below 0.99 x HandleLow. The initial
    stop would then be above the entry price, and a close-based check fires on
    day 1's close. Decide whether that is intended or needs a guard.
- The entry also needs its Rank Score returned as `ClosenessScore` for slot
  priority (`backtest.py:521-525`). That is an entry concern, not an exit one.

## 8. Hard constraints for the new exit spec

These rules CANNOT be implemented without code changes:
1. **No partial exits / scale-outs** (e.g. "sell 1/3 at +20%", "sell half at the
   measured move"). There is one exit per trade. Any "take partial profits"
   idea must become a full exit or be dropped.
2. **No adding to winners / pyramiding.**
3. **No access to the entry screener's Details** (Pivot, Handle Low, Initial
   Stop, Rank Score). They must be recomputed from OHLCV.
4. **No position sizing by risk** (e.g. "risk 1% per trade to the stop"). Sizing is
   fixed equal-weight slots.
5. **No index or earnings data** (`exit_rules.md:22-25`). There is no breadth input
   to the exit either: `MarketBreadth`/`SectorRank` go only to `evaluate_stock`.
6. **No transaction cost modeling.** An exit that trades more often looks
   relatively better than it would net of costs.
7. **No "do not open this trade" from the exit.** Returning None means "hold to
   RangeEnd", not "skip". Both existing specs wrongly claim None lets the caller skip
   (`exit_rules.md:124-126`; mean-reversion backup lines 103-106). Contrast
   `backtest.py:297-300`. Every failure path should be avoided or should fall back
   to a defined stop. For example: if Pivot is not computable, use only the 8% hard
   stop.
8. **MaxHold other than 90** works in the backtest, but the Sell tab text is
   hardcoded to "/90" (`sell_screener.py:184`).
9. **Next-day-open exits** are technically returnable (any date/price in
   `future_df`). But if the trigger is on the last row there is no next bar
   (the trade falls to RangeEnd), and live SELL would be delayed a day. Prefer
   "decide at close, fill at close".

These CAN be done:
- Close-based or explicit intraday-low stops. For an intraday stop, the spec must
  say so and define the fill, e.g. `min(open, stop)` on a gap-down.
- Fixed or ATR trailing stops that ratchet upward.
- Time-based rules (count `future_df` rows: entry day = day 1).
- Breakeven moves, structural levels from pre-entry history (Pivot, HandleLow), and
  measured-move targets (as a full exit).
- Multiple tagged reasons with a priority order.
- `describe_state` for the Sell tab.
