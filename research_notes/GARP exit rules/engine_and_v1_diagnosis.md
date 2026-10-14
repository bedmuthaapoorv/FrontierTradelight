# Backtest Engine Exit Contract and GARP v1 Exit Diagnosis

Scope: local code reading of `Strategies/Default` and analysis of `Strategies/Default/data/backtest_trades.csv` (GARP Semi-Annual v1 + GARP Rebalance Exit v1, 2021-01-01 to 2026-01-01, 620 signals, 246 funded), re-simulated on the cached prices in `Strategies/Default/data/backtest_cache/{SYMBOL}_2019-11-28_2026-01-01.csv` (the cache `backtest.py` reads through `_load_symbol_history`).

Sources are local files. "Scratch analysis" means the script `C:/Users/APOORV~1.MED/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/garp_exit_diag.py` (plus `port2.py` and `p3.py` in the same folder), with its output in `garp_exit_diag.json`. The script reproduces all 246 funded baseline trades exactly (same exit date; return within 0.05 pp), and its copy of `simulate_portfolio` reproduces the engine's final equity (Rs 161,986) from the CSV. No project files were changed and `backtest.py` was not run.

**Approximation warning.** The "trade-level" alternatives in B2 re-run each trade's exit on its own price path and ignore slot funding (which signals would have got capital). The "portfolio replay" numbers re-run the engine's own `simulate_portfolio` logic (25 slots, equal weight, priority by ClosenessScore) on the modified trade list, so they do capture slot interaction. They are still estimates: they are before costs, they value open positions at cost (as the engine does), and they come from one 5-year history with 10 cohorts.

---

## A1. What is the exact resolve_exit contract (inputs, ExitPrice, None / RangeEnd)?

### Takeaway
`resolve_exit(entry_price, entry_date, signal_history_df, future_df)` gets two OHLCV frames for one stock and nothing else. `future_df` row 0 is the entry day (entry = that day's open), and the frame runs only to the backtest end date (2026-01-01), never beyond. The returned `ExitPrice` is used as is to compute the trade's % return. Returning `None` (or raising an exception) makes the engine close the trade at the last close in range, tagged `RangeEnd`.

### Cited Findings
- `future = full_df[(full_df.index.date > signal_day) & (full_df.index.date <= end_date)]`. `entry_date = future.index[0]`, `entry_price = future["open"].iloc[0]`, and `signal_history = full_df[full_df.index.date <= signal_day]`. So row 0 of `future_df` is the entry day, the frame is capped at the backtest `end_date`, and `signal_history_df` ends on the signal day (the day before entry) and includes about 400 calendar days of warm-up (`WARMUP_DAYS = 400`) — [backtest.py L60, L280-286](Strategies/Default/backtest.py)
- An exception or a `None` return both lead to `exit_date = future.index[-1]`, `exit_price = future["close"].iloc[-1]` and `exit_reason = "RangeEnd"`. `ExitPrice` is cast to float. `ExitDate` is normalised with `pd.Timestamp(exit_date).date()`. `ProfitRs = (exit_price - entry_price) / entry_price * 100` (a flat Rs 100 stake) — [backtest.py L288-308](Strategies/Default/backtest.py)
- The engine models no costs or slippage, and it fills any `ExitPrice` the function returns. The Gemini prompt says ExitPrice should be "the close price on that date (or the appropriate trigger price if exit_rules.md specifies one)", and that daily `close` is the default trigger, with no intraday high/low unless the rules say so — [generate_exit_strategy.py L45-63](Strategies/Default/generate_exit_strategy.py)
- The Gemini prompt tells the model to ignore any fallback described in exit_rules.md, to return None when nothing fires, to never raise, and to compute entry-time indicators only from `signal_history_df` — [generate_exit_strategy.py L65-99](Strategies/Default/generate_exit_strategy.py)
- Cached bars carry a time of `18:30:00` (for example `2026-01-01 18:30:00`). The engine slices on `.index.date`. Comparisons such as the generated exit's `idx >= next_rebalance` (midnight timestamp) still work because the bar time is later than midnight on the same date — [backtest_cache/KNRCON_2019-11-28_2026-01-01.csv](Strategies/Default/data/backtest_cache/KNRCON_2019-11-28_2026-01-01.csv); [generated_exit_strategy.py L35](Strategies/Default/generated_exit_strategy.py)
- In live use, the Sell tab calls the same function, with different frames: `signal_history = full_df[date <= entry_date]` and `future = full_df[date >= entry_date]`, so the entry-day bar is in both frames. It fetches only about 200 calendar days before entry (`lookback_days=200`), may append a typed-in live price as a bar with no volume, and has no RangeEnd fallback — [sell_screener.py L66-79, L82-108, L111-147](Strategies/Default/sell_screener.py)
- The Cup and Handle exit spec handles this backtest/live difference explicitly: it locates the signal day as the last row strictly before `entry_date`, and de-duplicates the combined history with `keep="last"` — [cup_and_handle_exit_strategy_v1_exit_rules_20261014_131140.md "Data Conventions"](Strategies/ExitRules_backup/cup_and_handle_exit_strategy_v1_exit_rules_20261014_131140.md)
- The current GARP exit sells at the first bar dated on or after the next 15 Jun / 15 Dec, sells at close <= 0.75 x entry, and has a 150-session MaxHold safety net. MaxHold never fired: the 620 trades split into 477 Rebalance, 81 CatastrophicStop and 62 RangeEnd — [generated_exit_strategy.py](Strategies/Default/generated_exit_strategy.py); [backtest_trades.csv](Strategies/Default/data/backtest_trades.csv)

### Inferences
- An exit cannot look past 2026-01-01 in the benchmark run. Every Dec-2025 entry ends as RangeEnd (about 2 weeks held), and any rule that holds longer than 6 months truncates the Jun-2025 cohort at range end.
- Because only one exit per trade is supported (no partial exits), "trim" or "scale-out" rules cannot be built.
- Any new GARP exit must work with only about 200 days of pre-entry history when it runs live. A 200-DMA needs `signal_history_df` plus `future_df` combined, and on a fresh holding that may be too short live, even though the backtest has about 400 days.

### Gaps
- None for the contract itself.

---

## A2. How does simulate_portfolio handle exits, entries, slots and valuation, and how would longer holds interact with funding?

### Takeaway
On each date, exits are processed before entries, so a position sold at a rebalance-day close frees its slot for entries. New entries happen on the next trading day (signal on day R, entry at the R+1 open), so a stock sold at the R close can be re-bought at the R+1 open as a new, separate trade. Positions are valued at cost until they close, so the equity curve, MaxDD and Sharpe only move on exit dates. Holding past a rebalance blocks slots: with 25 slots, a 12-month hold turns the strategy into a June-only annual portfolio (125-132 funded trades instead of about 250).

### Cited Findings
- Exits are processed before entries on each date ("so freed capital is available for same-day reinvestment"). New positions are sized at `(cash + sum(open allocations)) / max_concurrent_positions`. Signals beyond free slots are marked unfunded, in ClosenessScore order. Same-day round trips are closed straight after opening — [backtest.py L516-554](Strategies/Default/backtest.py)
- Equity is `cash + sum(open_positions.values())`, i.e. open positions are held at their allocated cost, with no mark-to-market — [backtest.py L535, L556](Strategies/Default/backtest.py)
- CAGR, MaxDD, Sharpe and the leaderboard Composite Score (CAGR x Sharpe / |MaxDD|) are computed from that at-cost equity curve — [backtest_runner.py `compute_metrics`](Strategies/Default/backtest_runner.py)
- Each signal opens its own independent trade, and "Multiple simultaneous trades on the same symbol are allowed" — [backtest.py L25-26](Strategies/Default/backtest.py)
- The GARP run used 25 slots. rules.md says to run with `--max-positions 25`, and the funded allocations per entry date are equal, with 24-25 positions per cohort — [rules.md L41-42](Strategies/Default/rules.md); [backtest_trades.csv](Strategies/Default/data/backtest_trades.csv)
- **Floating-point funding defect.** On 4 of 10 rebalance entry days (2021-12-16, 2022-12-16, 2024-06-19, 2024-12-17), only 24 of 25 empty slots were funded, although 37-74 signals were available. After 24 buys, `cash` equals `size` to within float rounding, and `if size <= cash` sometimes fails. Adding a 1e-6 tolerance in the replay funds 250 trades instead of 246 (final equity Rs 161,546 vs 161,986). Feeding unrounded instead of 2-dp-rounded returns into the unchanged engine logic changes the result to 245 funded and Rs 158,919. That is about a 2% swing in final equity from rounding noise alone — scratch analysis (`portfolio_replay`, `portfolio_replay_epsfix`); [backtest.py L535-541](Strategies/Default/backtest.py)
- Off-cycle signals: 12 of the 620 signals fall on non-rebalance days (for example 2023-06-21, which returned +179.7%), presumably because the stock had no bar on the rebalance day. None was funded, because all slots were full — [backtest_trades.csv](Strategies/Default/data/backtest_trades.csv)
- Holding to the second rebalance (portfolio replay, with the float tolerance): with the -25% stop, 132 trades were funded. Cohorts funded were Jun-21 25, Dec-21 3, Jun-22 25, Dec-22 1, Jun-23 24, Dec-23 2, Jun-24 23, Dec-24 2, Jun-25 24, Dec-25 3. With no stop, 125 trades were funded, all from June cohorts. The December cohorts are almost entirely skipped because their slots are still occupied — scratch analysis (`p3.py`)

### Inferences
- Because positions are valued at cost, the leaderboard's MaxDD and Sharpe favour exits that sell less often. A stop realises a loss into the curve, while an unrealised loss of the same size held to the rebalance is invisible until the sale. For example, the no-stop variant shows a MaxDD of -15.8%, while its worst single trade is -48.5%. Exit variants should not be ranked on Composite Score alone.
- Cash freed by a mid-period stop sits idle until the next rebalance. There are almost never fundable off-cycle signals, and the proceeds of a stop (about 0.75 x slot) are smaller than a new slot size. A tighter stop therefore costs exposure as well as realising a loss.
- A "hold through re-selection" rule cannot be built inside `resolve_exit`. Even if the exit held, the re-signal would open a duplicate trade in the same symbol (duplicates are allowed), using a second slot. A rank buffer needs an engine change, for example in `simulate_portfolio`: when a funded position's symbol re-signals on its exit date, extend it instead of closing and reopening.
- The float defect should be fixed before comparing exit variants on the leaderboard. A 1-slot difference in 4 cohorts is about as large as some exit effects (around 0.1-0.4 pp CAGR).

### Gaps
- Mark-to-market drawdowns were not computed. The replay copies the engine's at-cost curve.

---

## A3. What format must a new exit_rules.md follow (sections, describe_state keys, conventions)?

### Takeaway
RULES_GUIDE.md covers only rules.md (entries) and says nothing about the exit-file format. The de-facto template comes from the existing exit files in `Strategies/ExitRules_backup/`. Their common sections are: Metadata (with `Exit Strategy Name:`), Data Availability Note, Rationale, Entry Reference, Pre-Trade Calculation, Daily State Variables, Daily Update Logic, Exit Conditions (each with a `Reason Tag`), Exit Priority Order, Fallback (return None, never RangeEnd), and State Inspection (`describe_state`).

### Cited Findings
- RULES_GUIDE.md is titled "How to Write `rules.md`". Its only exit-related advice is that slow fundamental strategies should add a rebalance-day entry rule "and pair it with an exit that holds until the next one" — [RULES_GUIDE.md L1-8, L56-61](Strategies/Default/RULES_GUIDE.md)
- The Gemini prompt passes the whole exit_rules.md text and requires `resolve_exit` only. It does not mention `describe_state`, so that function gets generated only because the exit_rules.md "State Inspection" section asks for it — [generate_exit_strategy.py L22-104](Strategies/Default/generate_exit_strategy.py)
- The strategy name recorded in backtest metadata comes from the `Exit Strategy Name` field — [backtest.py L650-652](Strategies/Default/backtest.py)
- Saved exit versions in `ExitRules_backup/` are compiled on first use into `generated_exit_strategies/<name>.py` for holdings whose `ExitRule` names them — [sell_screener.py L34-63](Strategies/Default/sell_screener.py)
- `describe_state` is optional (`getattr`). The Sell tab reads only `TrailingStop`, `DistanceToStopPct` (shown as "Trailing stop at X (Y% below current price)"), `DaysHeld` and `DaysToMaxHold`, and it hardcodes the text `"{DaysHeld}/90 trading days held"` — [sell_screener.py L161-185](Strategies/Default/sell_screener.py)
- The Mean Reversion exit's describe_state returns TrailingStop, HighestClose, LastClose, DistanceToStopPct, DaysHeld, DaysToMaxHold (90 - DaysHeld) and an AtRiskOfEarlyFailure flag. It also documents its evidence (cutoff sweeps and slot-count checks) inside the file, and notes that its 30-day cut helps only through capital recycling in a slot-limited portfolio — [mean_reversion_exit_strategy_v1_exit_rules_20260927_155105.md](Strategies/ExitRules_backup/mean_reversion_exit_strategy_v1_exit_rules_20260927_155105.md)
- The Cup and Handle exit adds a "Data Conventions (READ FIRST)" section: use `.iloc` positions, session s = `future_df` row s-1 (session 1 is the entry day and its close is checked), de-duplicate the combined history, treat NaN volume as condition-not-met, and use the close for both trigger and fill. Its `TrailingStop` key is the "effective stop that would actually trigger today", and it lists extra state keys. It also says leaderboard results are pre-cost (~0.24% per NSE delivery round trip) and that the old backtest cache was stamped a day early — [cup_and_handle_exit_strategy_v1_exit_rules_20261014_131140.md](Strategies/ExitRules_backup/cup_and_handle_exit_strategy_v1_exit_rules_20261014_131140.md)
- The GARP v1 exit follows the same skeleton. Its DaysToMaxHold means calendar days to the next rebalance, and it reports NextRebalance and LastClose — [exit_rules.md L113-125](Strategies/Default/exit_rules.md)

### Inferences
- Template for a new GARP exit:
  1. Metadata: `Exit Strategy Name`, `Applies To`, `Timeframe`.
  2. Data Availability Note: OHLCV only; no fundamentals, index or breadth.
  3. Rationale, with the evidence behind each threshold.
  4. Entry Reference: entry = next-day open; `future_df` row 0 = entry day.
  5. Data Conventions: session numbering, `.iloc`, combined-history de-duplication for indicators, NaN-volume handling, close-only fills.
  6. Pre-Trade Calculation.
  7. Daily State Variables.
  8. Daily Update Logic.
  9. Exit Conditions, each with a precise condition and a `Reason Tag`.
  10. Exit Priority Order.
  11. Fallback: return None, do not implement RangeEnd.
  12. State Inspection: `describe_state`, returning at least `TrailingStop` (the effective stop), `DistanceToStopPct`, `DaysHeld`, `DaysToMaxHold`, `LastClose`, plus strategy-specific keys; None only if `future_df` is empty.
- The Sell tab's "/90 trading days" text does not fit a rebalance exit. It already shows the wrong text for GARP v1, where DaysToMaxHold is calendar days to the rebalance. That is a UI issue, not an exit-spec issue.

### Gaps
- No written guide for exit_rules.md exists in the repo, so the template above is inferred from the existing exit files and the generator prompt.

---

## A4. Can the exit know whether a stock would be re-selected at the next rebalance?

### Takeaway
No. `resolve_exit` and `describe_state` receive only the entry price, entry date and two price frames for one stock. Fundamentals, Rank Score and the other stocks are never passed in, and the top-25 cut is cross-sectional.

### Cited Findings
- The call is `generated_exit_strategy.resolve_exit(entry_price, entry_date, signal_history, future)`, and both frames are slices of one symbol's OHLCV history — [backtest.py L280-290](Strategies/Default/backtest.py)
- Fundamentals (`fundamentals_snapshot(...)`) and sector/breadth values are passed only to `evaluate_stock` through `call_evaluate_stock` — [backtest.py L427-436](Strategies/Default/backtest.py)
- The GARP exit spec itself says "No fundamentals are available to the exit - the next rebalance re-applies the fundamental screen instead" — [exit_rules.md L12-16](Strategies/Default/exit_rules.md)
- rules.md lists "no rank buffer (holdings that still qualify are sold and re-bought)" as a known gap — [rules.md L43-46](Strategies/Default/rules.md)

### Inferences
- Generated Python could in theory import the fundamentals module itself. That breaks the contract, risks look-ahead, cannot reproduce the cross-sectional top-25 cut, and the engine would still open a duplicate trade on the re-signal (see A2). Hold-through for re-selected stocks is an engine or portfolio feature, not an exit_rules.md feature.

### Gaps
- None.

---

## B1. How are GARP v1 returns distributed by ExitReason, and would holding the 36 CatastrophicStop trades have been better?

### Takeaway
Rebalance exits earned a mean of +12.5% per funded trade (185 trades). The 36 funded CatastrophicStop trades lost a mean of -26.7%, with 7 gapping through to below -27%. Holding those 36 to the next rebalance would have lost less (-22.2% mean): the stopped stocks were, on average, 6% higher at the rebalance than at the stop. Only 1 of 36 got back to its entry price, and in the Dec-2021 cohort holding would have been much worse.

### Cited Findings (scratch analysis on backtest_trades.csv and the price cache)
| Funded (n=246) | n | mean % | median % | win % | worst % | sum (pp) |
|---|---|---|---|---|---|---|
| All funded | 246 | 5.66 | 2.18 | 52.4 | -34.54 | 1,391.6 |
| Rebalance | 185 | 12.53 | 6.56 | 62.7 | -22.55 | 2,318.0 |
| CatastrophicStop | 36 | -26.71 | -25.81 | 0.0 | -34.54 | -961.6 |
| RangeEnd (Dec-25 cohort, about 2 weeks) | 25 | 1.41 | 0.15 | 52.0 | -9.35 | 35.1 |

| All signals (n=620) | n | mean % | median % | win % | worst % |
|---|---|---|---|---|---|
| All | 620 | 8.28 | 4.53 | 57.4 | -37.53 |
| Rebalance | 477 | 15.26 | 9.91 | 68.3 | -23.56 |
| CatastrophicStop | 81 | -26.94 | -25.86 | 0 | -37.53 |
| RangeEnd | 62 | 0.59 | -0.24 | 48.4 | -19.92 |

- Unfunded signals did better than funded ones (Rebalance mean 17.0% for unfunded vs 12.5% for funded). The ClosenessScore priority picked below-average names over this window.
- The 36 funded stops, compared with holding to the next rebalance close:
  - Return at the stop: mean -26.71%. Holding to the rebalance instead: mean -22.21%, median -22.92%, worst -48.53%, best +13.4%.
  - The move from the stop price to the rebalance close was a mean +6.16% (median +3.99%). The rebalance close was above the stop exit price in 26 of 36 cases, but only 1 of 36 recovered to the entry price.
  - The lowest close after a stop was -48.8% vs entry.
  - Median time to the stop: 86 calendar days after entry.
  - Gap-through: 7 of 36 stops filled below -27%. The worst was INDUSINDBK at -34.54% (Dec-2024 cohort).
- All 81 stops (funded and unfunded): holding to the rebalance gives a mean of -20.05% vs -26.94% at the stop. The rebalance close was above the stop exit price in 57 of 81 cases, and 5 of 81 recovered to entry.
- Stops by cohort (funded): Jun-21 5, Dec-21 9, Jun-22 2, Dec-22 6, Jun-23 2, Dec-23 3, Jun-24 0, Dec-24 6, Jun-25 3, Dec-25 0. Stops cluster in market-wide drawdowns: Dec-24 had 26 of 70 signals stopped, and Dec-21 had 13 of 37.
- Stop-to-rebalance move by funded cohort (mean): Dec-21 -10.5% (MANAPPURAM -30.6%, VAIBHAVGBL -25.3%, ISEC -22.2% further after the stop); Jun-25 -2.0%. All other cohorts recovered after the stop: Dec-22 +14.3%, Jun-23 +14.6%, Dec-23 +24.6%, Dec-24 +18.2% (IIFL +54.2%, which would have finished +13.4% vs entry).

### Inferences
- At -25%, the stop mostly sells close to the bottom of a broad selloff (it is "regime-correlated"). In 6 of the 8 cohorts with funded stops, the stopped names bounced back. In 2021-12, holding would have cost much more.
- At the trade level, the stop cost about 4.5 pp per stopped trade on average (sum about 162 pp over 36 trades). It did cap the tail, from -48.5% held to -34.5% at the stop.

### Gaps
- Behaviour after a stop is from one 5-year path. The sample of 36 is small and dominated by two drawdown episodes.

---

## B2. How would simple alternative exits have done on the same trades (trade-level and portfolio replay)?

### Takeaway
Within the 6-month hold, no price-based exit tested beat the baseline by much at the trade level. Removing the stop was best on mean and sum (+0.65 pp mean per funded trade) but widened the worst trade to -48.5%. Tighter stops, trailing stops and a plain 200-DMA exit all reduced returns. A plain 200-DMA exit fires almost immediately because about 35% of GARP entries are already below their 200-DMA. Holding to the second rebalance (about 12 months) raised per-trade returns and portfolio CAGR (13.3-14.0% vs 11.1%), but in practice it becomes a June-only annual strategy whose result rests on one cohort (Jun-2023, +68%).

### Cited Findings (scratch analysis; all variants close-only; "+stop25" keeps the 0.75 x entry stop)
Trade-level, funded trades (n=246, slot funding ignored):

| Variant | mean % | median % | win % | worst % | sum (pp) | mean days | exits |
|---|---|---|---|---|---|---|---|
| Baseline (stop -25%, sell at 1st rebalance) | 5.66 | 2.19 | 52.4 | -34.54 | 1,391.5 | 152 | Reb 185 / Stop 36 / RangeEnd 25 |
| (1) No stop | 6.31 | 2.57 | 52.8 | -48.53 | 1,553.4 | 165 | Reb 221 / RangeEnd 25 |
| (2) Stop -15% | 4.87 | -1.09 | 47.6 | -34.54 | 1,197.2 | 133 | Stop 74 |
| (2) Stop -20% | 5.50 | 1.80 | 51.2 | -34.54 | 1,352.7 | 146 | Stop 48 |
| (2) Stop -30% | 5.77 | 2.19 | 52.4 | -34.54 | 1,419.8 | 157 | Stop 22 |
| (3) Trail 20% from highest close, no fixed stop | 4.19 | -0.37 | 48.4 | -34.54 | 1,029.8 | 130 | Trail 99 |
| (3) Trail 25% from highest close, no fixed stop | 5.13 | 1.95 | 51.2 | -34.54 | 1,261.7 | 146 | Trail 57 |
| (4) Close < SMA200 (any time) + stop25 | 3.59 | -1.48 | 33.7 | -24.82 | 883.0 | 63 | DMA 181 |
| (4b) SMA200 break only after a close above it since entry + stop25 | 3.59 | -1.54 | 43.5 | -34.54 | 882.7 | 99 | DMA 136 / Stop 17 |
| (4c) Close < 0.90 x SMA200 + stop25 | 5.29 | -1.71 | 42.3 | -26.67 | 1,302.5 | 102 | DMA 114 / Stop 3 |
| (5) Hold to 2nd rebalance + stop25 | 12.20 | 5.05 | 57.7 | -34.54 | 3,001.1 | 265 | Reb 142 / Stop 57 / RangeEnd 47 |
| (5) Hold to 2nd rebalance, no stop | 14.01 | 6.50 | 60.6 | -59.38 | 3,445.9 | 312 | Reb 196 / RangeEnd 50 |

- All 620 signals rank the variants the same way. Mean per trade: baseline 8.28; no stop 9.18; stop -15% 7.13; stop -20% 8.03; stop -30% 8.68; trail 20% 6.76; trail 25% 7.83; SMA200 3.68; SMA200 band 5.94; 2nd rebalance + stop 16.54; 2nd rebalance, no stop 18.49 (worst -68.76%).
- At signal time, 35.4% of funded entries closed below their 200-day SMA, which is why the plain 200-DMA exit fired on 181 of 246 funded trades.
- (6) Hold-through for re-selected stocks:
  - Trade level: 83 chains of consecutive funded trades in the same symbol (rebalance exit followed by re-buy within a week); 67 had 2 legs, and 16 had 3-6 legs.
  - Chain results: compounding the actual sell-and-rebuy legs gives a mean +17.93% (median 7.04). A continuous hold from the first entry gives a mean +20.74% (median 9.23) with the -25% stop measured from the original entry (it fired in 18 chains), or a mean +31.29% (median 16.36, worst -62.87%) with no stop.
  - Most of the gain comes from the stop no longer resetting or firing, not from the overnight sell-close/buy-open gap, which averaged only +0.19%.
- Portfolio replay (engine `simulate_portfolio` logic, 25 slots, float tolerance fixed, at-cost valuation, pre-cost, Rs 1 lakh start):

| Variant | Final Rs | CAGR % | MaxDD (at cost) % | Funded |
|---|---|---|---|---|
| Baseline (float fixed) | 161,543 | 11.13 | -14.80 | 250 |
| No stop | 170,690 | 12.48 | -15.76 | 250 |
| Stop -15% | 156,709 | 10.39 | -11.55 | 250 |
| Stop -20% | 159,426 | 10.81 | -12.76 | 250 |
| Stop -30% | 161,951 | 11.19 | -15.94 | 250 |
| Trail 20% | 142,927 | 8.18 | -13.58 | 250 |
| Trail 25% | 154,567 | 10.06 | -13.95 | 250 |
| SMA200 + stop25 | 152,159 | 9.68 | -8.48 | 257 |
| SMA200 cross-after-above + stop25 | 147,892 | 8.99 | -11.97 | 254 |
| 0.90 x SMA200 + stop25 | 173,955 | 12.95 | -12.50 | 256 |
| Hold to 2nd rebalance + stop25 | 176,489 | 13.31 | -17.43 | 132 |
| Hold to 2nd rebalance, no stop | 181,223 | 13.98 | -10.53 | 125 |
| Hold-through if re-signalled (stop -25% per leg) | 166,241 | 11.83 | -14.17 | 104 new + 141 extensions |

- The engine-as-is (unfixed float, CSV returns) replay gives Rs 161,986 / 11.20% CAGR / -16.49% MaxDD / 246 funded, which matches `backtest_portfolio.csv` — [backtest_portfolio.csv](Strategies/Default/data/backtest_portfolio.csv)
- Hold to 2nd rebalance, by funded cohort: no stop — Jun-21 -10.5%, Jun-22 +8.8%, Jun-23 +67.9%, Jun-24 +6.0%, Jun-25 +4.6% (to range end); with stop — Jun-21 -6.6%, Jun-22 +6.4%, Jun-23 +67.6%, Jun-24 +5.5%, Jun-25 +5.5%.

### Inferences
- With 25 slots and roughly 60 qualifying stocks per rebalance, the 6-month window is short, and the -25% stop on its own looks slightly harmful (about -1.3 pp CAGR vs no stop in the replay). A -30% stop is about neutral. Tight stops (-15%/-20%) and percentage trails cut returns. Like the stop, a percentage trail mostly sells regime dips that later recover.
- The "0.90 x SMA200" result (12.95% CAGR) is an outlier, and it looks fragile. Its per-trade mean is below baseline, yet it gains at portfolio level through earlier cash recycling into cohorts and different funding (256 funded). Treat it as a hypothesis, not a finding.
- The 12-month result is mostly a calendar effect (June-only annual rebalancing) plus one great cohort. On 5 annual observations it is not robust, and its at-cost MaxDD understates risk (worst no-stop trade -59%).
- A rank buffer (hold-through if re-signalled) adds about +0.7 pp CAGR before costs, and more after costs (A2/B3). It needs engine support.
- Leaderboard caveat: CompositeScore uses the at-cost curve, so variants with fewer realised exits look less risky than they are.

### Gaps
- No transaction costs were applied. At about 0.24% per round trip (figure from the Cup and Handle file), each rebalance that turns over all 25 slots costs about 0.24% of equity.
- Mark-to-market MaxDD and Sharpe were not computed.
- Robustness to slot count (for example 15 or 20) and to rebalance dates was not tested.

---

## B3. How many funded trades were sold at a rebalance and immediately re-bought?

### Takeaway
117 of the 185 funded Rebalance exits (63%) were re-bought as a funded position at the next morning's open, and 142 of 185 (77%) re-signalled that day. That is 117 needless round trips out of 246 funded trades, concentrated in the December rebalances.

### Cited Findings (scratch analysis)
- Funded Rebalance exits: 185. Same symbol signalled on the exit (rebalance) day: 142. Re-bought as a funded trade within 7 days (in practice at the next open): 117.
- Re-buys by entry cohort: Dec-21 18, Jun-22 1, Dec-22 18, Jun-23 8, Dec-23 18, Jun-24 6, Dec-24 21, Jun-25 7, Dec-25 20. December rebalances re-buy 18-21 of about 24 names, while June rebalances re-buy 1-8. This fits annual fundamentals that change mainly once a year (screen inputs refresh after the 30 May results deadline).
- Sell-at-close to re-buy-at-next-open gap on the 117 re-buys: mean +0.19%, median +0.04%, worst -1.07%, best +5.88%.

### Inferences
- The December rebalance is mostly turnover: about 75-85% of the book is sold and re-bought. In the engine (no costs) that costs nothing, but in live trading it is about 117 x ~0.24%, roughly 28 pp of slot-returns over 5 years, or about 1.1% of total equity at 1/25 per slot. It also adds tax events in India (short-term vs long-term capital gains at 12 months), which a 12-month or hold-through design would help with.

### Gaps
- Tax effects (STCG/LTCG thresholds) were not quantified.

---

## B4. How did each 6-month rebalance cohort perform?

### Takeaway
Funded results by cohort ranged from -15.3% (Dec-2021) to +31.7% (Jun-2023). The portfolio beat a rough equal-weight universe reference mainly in the falling cohorts (Dec-2024, Jun-2025) and lagged it in strong ones (Jun-2022, Dec-2022, Dec-2023, Jun-2024). That pattern is consistent with a defensive GARP tilt rather than an exit problem.

### Cited Findings (scratch analysis)
The universe reference ("Univ") is the equal-weight average over all cached symbols (580-668 per cohort): entry-day open to next-rebalance close. It includes stocks that were Nifty 500 members at any time in 2021-2026, so it is not point-in-time membership and is a rough reference only.

| Cohort (signal) | Funded n | mean % | median % | win % | worst % | best % | stops | Univ mean % | Univ median % | All-signals n / mean % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021-06-15 | 25 | 6.49 | 6.56 | 60.0 | -29.48 | 55.94 | 5 | 13.63 | 6.69 | 45 / 10.62 |
| 2021-12-15 | 24 | -15.34 | -18.05 | 8.3 | -32.81 | 28.56 | 9 | -11.87 | -16.09 | 37 / -12.36 |
| 2022-06-15 | 25 | 6.65 | -1.11 | 48.0 | -26.67 | 83.64 | 2 | 21.19 | 15.43 | 74 / 13.35 |
| 2022-12-15 | 24 | -0.64 | 0.06 | 50.0 | -31.50 | 42.60 | 6 | 7.20 | 4.25 | 63 / 8.03 |
| 2023-06-15 | 25 | 31.68 | 27.29 | 88.0 | -26.29 | 109.45 | 2 | 32.35 | 22.73 | 68 / 28.09 |
| 2023-12-15 | 25 | 18.80 | 22.25 | 68.0 | -25.86 | 113.95 | 3 | 23.61 | 18.36 | 60 / 22.64 |
| 2024-06-18 | 24 | 1.88 | -1.88 | 37.5 | -21.01 | 49.15 | 0 | 7.21 | 0.73 | 72 / 1.02 |
| 2024-12-16 | 24 | 1.19 | 5.70 | 58.3 | -34.54 | 38.75 | 6 | -5.21 | -7.13 | 70 / -3.94 |
| 2025-06-16 | 25 | 3.03 | 2.90 | 52.0 | -26.15 | 33.23 | 3 | -3.82 | -5.29 | 58 / 2.27 |
| 2025-12-15 (to range end) | 25 | 1.41 | 0.15 | 52.0 | -9.35 | 19.21 | 0 | 0.99 | 0.18 | 60 / 0.34 |

### Inferences
- Exits mattered most in Dec-2021 (9 stops, and holding would have been worse) and in Dec-2024/Dec-2022 (stops that later recovered). Elsewhere the cohort result is driven by selection and market regime, not by the exit.
- The funded top-25 trailed the full signal list in 5 of 10 cohorts (2021-06, 2021-12, 2022-06, 2022-12, 2023-12) and led it in the other 5. Over all trades, though, unfunded Rebalance exits averaged +17.0% vs +12.5% for funded ones. So the ranking (ClosenessScore priority) is a separate lever, possibly larger than the exit. It is outside this note's scope.

### Gaps
- No Nifty or benchmark index data is available in the project, so the universe average is only a proxy.
- Cohort-level statistical significance was not assessed (n=10).
