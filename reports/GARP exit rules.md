# Widen the stop, then fix the engine

The best replacement for "GARP Rebalance Exit v1" is a small change to the exit, not a new one. **GARP Rebalance Exit v2 should keep the sale at the next semi-annual rebalance close, widen the catastrophic stop from 0.75 x entry to 0.70 x entry, and add no trailing stop, moving-average exit, profit cap or time stop.** On the 2021-2026 backtest none of those price rules beat the plain rebalance sale. The fixed -25% stop already looks slightly harmful: it sells near the bottom of market-wide selloffs, and the cash then sits idle until the next rebalance. A -30% stop is about neutral on return (11.19% vs 11.13% CAGR in a replay of the engine) and keeps a tail cap that "no stop" lacks (worst held trade -48.5%). The larger gains are outside the exit file. Not selling and re-buying stocks that are re-selected at the same rebalance is worth about +0.7 pp CAGR before costs, and much more after costs and Indian short-term capital gains tax: 117 of 185 funded rebalance sales were bought back at the next morning's open. That change needs the engine. So do the other fixes: a floating-point bug that leaves a slot unfunded on 4 of 10 rebalance days, positions valued at cost rather than marked to market, and the lack of costs and tax. Fix the funding bug and the valuation first, because until then the leaderboard cannot fairly rank any exit variant. All of these numbers come from one 5-year window with 10 cohorts, 5 of them June. The exit recommendation therefore leans on parameters from the published literature, not on whichever variant scored best.

## The exit sees one stock's prices and nothing else

The exit contract limits what v2 can do. `resolve_exit(entry_price, entry_date, signal_history_df, future_df)` receives two OHLCV frames for one symbol. Row 0 of `future_df` is the entry day, with entry at that day's open. The frame stops at the backtest end date, 2026-01-01. Returning `None`, or raising an exception, closes the trade at the last close in range with the tag `RangeEnd` ([backtest.py L280-308](../Strategies/Default/backtest.py)). No fundamentals, Rank Score, other stocks, index or breadth data are passed in. **The exit therefore cannot know whether a stock will be re-selected at the next rebalance.** The top-25 cut is cross-sectional, and the fundamentals snapshot goes only to `evaluate_stock` ([backtest.py L427-436](../Strategies/Default/backtest.py); [diagnosis A4](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)). The engine supports one exit per trade, so trims and scale-outs are impossible. It also lets several simultaneous trades be open in the same symbol ([backtest.py L25-26](../Strategies/Default/backtest.py)).

That last point rules out the most tempting exit-only idea. In the engine, holding a winner past the rebalance (for example, deferring the sale until it qualifies for long-term capital gains) does not keep the existing position. If the stock re-signals, the engine opens a **duplicate trade in a second slot**. With 25 slots, a 12-month hold also blocks most of the December cohort, so the strategy becomes a June-only annual portfolio: 125-132 funded trades instead of about 250 ([diagnosis A2](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)). Holding to the second rebalance did lift the replayed CAGR to 13.3-14.0%. But the result rests on one cohort, Jun-2023 at +68%, and on a worst trade of -59% that the at-cost equity curve hides. Treat it as a calendar artefact, not a finding.

Live use adds two constraints. The Sell tab calls the same function, but with the entry-day bar in both frames and only about 200 calendar days of history before entry ([sell_screener.py L66-108](../Strategies/Default/sell_screener.py)). Any indicator needing a 200-day SMA would be fragile live for a fresh holding. The Sell tab also reads only the `describe_state` keys `TrailingStop`, `DistanceToStopPct`, `DaysHeld` and `DaysToMaxHold`, and it hard-codes "/90 trading days" ([sell_screener.py L161-185](../Strategies/Default/sell_screener.py)). That text is already wrong for GARP, but it is a UI issue, not something the exit spec can fix.

## The -25% stop sells regime lows that mostly recover

Over the 246 funded trades, rebalance exits earned a mean of **+12.5%** (185 trades). The 36 catastrophic stops lost a mean of **-26.7%**, and 7 of them gapped through to worse than -27% (worst: INDUSINDBK at -34.5%). The stops clustered in two broad drawdowns, Dec-2021 (9 stops) and Dec-2024 (6 funded, 26 of 70 signals). Holding the stopped names to the rebalance would have lost less: a mean of **-22.2%** instead of -26.7%. The stopped names rose a mean +6.2% between the stop and the rebalance, though only 1 of 36 got back to its entry price ([diagnosis B1](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)). The exception matters. In Dec-2021, holding would have been much worse, with MANAPPURAM falling another 30.6% after its stop. A stop is insurance that paid out once in the eight cohorts with funded stops, and cost money in the other six or seven.

The alternatives tested on the same trades point the same way. All were close-only, and the portfolio replay uses the engine's own 25-slot funding logic with the float bug fixed:

| Exit variant (6-month hold) | Mean per funded trade % | Worst trade % | Replay CAGR % | Replay MaxDD (at cost) % |
|---|---|---|---|---|
| v1: rebalance + stop at -25% | 5.66 | -34.5 | 11.13 | -14.8 |
| No stop | 6.31 | -48.5 | 12.48 | -15.8 |
| Stop at -30% | 5.77 | -34.5 | 11.19 | -15.9 |
| Stop at -20% | 5.50 | -34.5 | 10.81 | -12.8 |
| Stop at -15% | 4.87 | -34.5 | 10.39 | -11.6 |
| Trailing 25% from highest close | 5.13 | -34.5 | 10.06 | -14.0 |
| Trailing 20% from highest close | 4.19 | -34.5 | 8.18 | -13.6 |
| Close < 200-day SMA + stop at -25% | 3.59 | -24.8 | 9.68 | -8.5 |
| Close < 0.90 x 200-day SMA + stop at -25% | 5.29 | -26.7 | 12.95 | -12.5 |

Source: [diagnosis B2](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md), pre-cost, Rs 1 lakh start, open positions valued at cost.

A plain 200-day SMA exit fires almost at once, because **35% of GARP entries already close below their 200-day SMA** on the signal day. A GARP screen buys reasonably priced companies, and many of them are out of favour. Percentage trailing stops behave like the fixed stop: they sell regime dips that later recover. The 0.90 x SMA200 band is the only rule that beats v1 at portfolio level, yet its mean per trade is below v1's. Its gain comes from cash recycling into different funded names (256 funded instead of 250), which is exactly the kind of path-dependent result that does not repeat. Record it as a hypothesis to retest, not as the v2 rule.

The literature supports this reading. Kaminski and Lo show that under a random walk a stop-loss rule always lowers expected return, and that stops help only when returns have momentum ([MIT DSpace](https://dspace.mit.edu/handle/1721.1/114876)). Lo and Remorov, using US stocks from 1964 to 2014 with costs, find that tight stops underperform buy-and-hold. Wide stops roughly matched buy-and-hold on a risk-adjusted basis while cutting maximum drawdown. Recent single-stock autocorrelation turned negative, which is "not conducive to use of tight stop-losses" ([CXO Advisory](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth)). Lei and Li found no return difference from fixed or trailing stops over 3-12 month holds of NYSE/AMEX stocks; trailing stops only reduced volatility ([CXO Advisory](https://www.cxoadvisory.com/technical-trading/using-trailing-stop-losses-to-reduce-risk)). None of these studies tests stops inside a value or GARP portfolio. But a value-tilted book that buys out-of-favour stocks is the case where the theory predicts stops hurt most. Profit caps have even less support. Long-only stock trend returns are driven by fewer than 7% of trades ([Concretum](https://concretumgroup.com/does-trend-following-still-work-on-stocks/)), and Indian stocks near their 52-week high go on to outperform ([arXiv 2302.13245](https://www.arxiv.org/pdf/2302.13245)).

The choice of 0.70 x entry rather than "no stop" is a judgment, and the reasoning should be explicit. Removing the stop scored best (+1.35 pp CAGR in the replay). But that edge comes from one path in which most selloffs recovered within six months. It leaves a -48.5% worst trade over six months, and the at-cost valuation flatters it. A -30% stop sits at the wide end of the range where the evidence says stops are harmless, and it was not chosen as the best point of a sweep. On this data it fires 22 times instead of 36 and is return-neutral. That is the honest claim for v2: **it removes a rule that measured slightly harmful and keeps insurance against a Dec-2021-style collapse, without claiming an edge.** Close-based checking stays, because Lo and Remorov found delayed or close-based execution better than intraday triggers for individual stocks.

## Overfitting risk dominates everything below 1 pp of CAGR

The backtest covers one window (2021-2026) with 10 rebalance cohorts. Only 9 ran a full six months, because the Dec-2025 cohort ends at the range end after about two weeks. It contains 36 funded stops, most of them in two episodes. It is also a value-friendly regime for India, and the earlier review warned that a GARP result here cannot show how the strategy behaves elsewhere ([GARP review](GARP%20strategy%20for%20NSE%20screener%20review.md)). Against that, the gaps between exit variants are small. The -25%, -30% and no-stop stops are within 1.4 pp of CAGR of each other. The float bug alone moves final equity by about 2%, and choosing rounded or unrounded returns flips the funded count by one ([diagnosis A2](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)). Funding order matters more than the exit: unfunded rebalance exits averaged +17.0% against +12.5% for the funded ones, so the ClosenessScore priority picked below-average names over this window ([diagnosis B4](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)).

Three rules follow from this. First, no exit parameter in v2 is tuned on this data. -30% is a literature-range value that also happens not to hurt here. Second, challengers should be **pre-registered** before the engine fixes land and compared once: no stop, the 0.90 x SMA200 band, and the untested ideas from the literature (a trend-confirmed loss exit, which sells only when close is below a falling 200-day SMA and the position is down 12-15% for several closes; and an information-shock exit, which sells after a 10% or larger drop on at least 3x 50-day volume that does not recover) ([price-based risk exits note](../research_notes/GARP%20exit%20rules/price_based_risk_exits.md)). Third, report each variant by cohort and by stop count, not only by Composite Score. The score is computed from the at-cost equity curve, so it rewards exits that realise losses less often ([diagnosis A2](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)).

## Engine fixes come first, and the rank buffer pays the most

Five changes fall outside the exit file, and they should be done in this order.

**1. Slot-funding rounding bug (first, smallest).** After 24 equal-size buys, `cash` equals `size` to within float error, and `if size <= cash` sometimes fails. That happened on 2021-12-16, 2022-12-16, 2024-06-19 and 2024-12-17, even with 37-74 signals waiting ([backtest.py L535-541](../Strategies/Default/backtest.py)). Comparing with a small tolerance (for example `size <= cash + 1e-6`) funds 250 trades instead of 246. It is a one-line correctness fix, and without it every A/B comparison carries about 2% of noise.

**2. Mark-to-market valuation (second).** Equity is `cash + sum(open allocations)`, so CAGR, MaxDD, Sharpe and Composite Score move only on exit dates ([backtest.py L535, L556](../Strategies/Default/backtest.py); [backtest_runner.py](../Strategies/Default/backtest_runner.py)). For six-month holds this hides the very drawdowns a stop exists to limit: the no-stop variant shows -15.8% MaxDD while one of its trades lost 48.5%. Until open positions are valued at each day's close, the leaderboard cannot judge stop-vs-no-stop, or any 12-month or hold-through design.

**3. Costs and tax (third).** A delivery round trip costs about 0.22% in explicit charges (0.1% STT each side and 0.015% stamp duty on the buy) plus slippage ([Zerodha STT](https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/how-is-the-securities-transaction-tax-stt-calculated); [StockCalc](https://stockcalc.in/blog/zerodha-brokerage-charges-2026-full-breakdown)). Gains realised within 12 months are taxed at 20% STCG, against 12.5% LTCG above Rs 1.25 lakh a year ([Business Standard](https://www.business-standard.com/amp/markets/news/budget-2024-hikes-ltcg-tax-rate-to-12-5-stcg-to-20-stt-on-f-o-also-up-124072300553_1.html); [TaxGuru](https://taxguru.in/?p=1052279)). A per-trade cost deduction and a post-tax CAGR column are needed before the buffer's benefit can be seen. Before costs, a sell-and-rebuy is free in the engine.

**4. Hold-through for re-selected stocks (the largest economic lever).** 117 of 185 funded rebalance exits (63%) were re-bought at the next open. In December cohorts it was 18-21 of about 24 names, because annual fundamentals barely change between June and December ([diagnosis B3](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)). In `simulate_portfolio`, when a funded position's symbol re-signals on its exit date, the engine should extend the position rather than close it and open a duplicate. The entry already emits about 37-74 qualifying names per rebalance for 25 slots, so "hold if still qualifying" is in effect a 2x buffer. That matches NSE's convention of keeping an existing constituent while it ranks within twice the target count ([Nifty100 Low Volatility 30](https://www.niftyindices.com/Factsheet/Nifty100_LowVolatility30.pdf); [Nifty High Beta 50](https://www.niftyindices.com/Methodology/Method_Nifty_High_Beta_50.pdf)). Novy-Marx and Velikov call a buy/hold spread "the single most effective simple cost mitigation strategy" ([NBER w20721](https://nber.org/papers/w20721)). In the replay it added about +0.7 pp CAGR before costs (11.83% vs 11.13%). Most of the gain came from not resetting the stop, since the overnight gap averaged only +0.19% ([diagnosis B2](../research_notes/GARP%20exit%20rules/engine_and_v1_diagnosis.md)). With stops measured from the original entry, the -30% stop in v2 then becomes a stop on the whole holding, which is the intended meaning.

**5. LTCG-aware holding (last, only after step 4).** With hold-through in place, a rule such as "do not sell a profitable holding before day 366 unless it has dropped out of the qualifying list" becomes possible without duplicate trades or blocked December slots. On a position up 20%, STCG at 20% costs 4.0% of value, against 2.5% at the 12.5% LTCG rate ([holding and rebalance note](../research_notes/GARP%20exit%20rules/holding_and_rebalance.md)). It has to be an engine or entry rule because it depends on re-selection, which the exit cannot see.

The order reflects dependency, not size. Steps 1 and 2 are measurement fixes: without them, every later comparison, this exit's included, is unreliable. Step 3 makes visible the costs that step 4 removes. Step 4 is where the money is. Each step should be re-run with the v2 exit held fixed, so the exit and engine effects are not confounded.

## Recommended GARP v2 exit specification

The block below is ready to save as `exit_rules.md`. It follows the section template of the existing exit files ([v1 exit rules](../Strategies/ExitRules_backup/garp_rebalance_exit_v1_exit_rules_20261014_131019.md); [Cup and Handle exit rules](../Strategies/ExitRules_backup/cup_and_handle_exit_strategy_v1_exit_rules_20261014_131140.md)). The reason tags are unchanged from v1, so `backtest_trades.csv` stays directly comparable.

````markdown
# Exit Strategy Rules

## Strategy Metadata

Exit Strategy Name: GARP Rebalance Exit v2
Applies To: GARP Semi-Annual v1 (rules.md) - holds each position until the
next semi-annual rebalance day. Not meant for technical entries.
Timeframe: Daily (closing price only)

---

## Data Availability Note

Only the entry price/date and the stock's own daily OHLCV (before and after
entry) are available. No fundamentals, ranks, index or breadth data are
available to the exit - the next rebalance re-applies the fundamental screen
instead. This exit uses only `entry_price`, `entry_date` and the `close`
column of `future_df`. `signal_history_df` is not used. Volume is not used.

---

## Strategy Rationale

The paired entry buys only on a rebalance day (first trading day on or after
15 June / 15 December). This exit sells every position at the close of the
next rebalance day, so capital is free for that day's new list (the
backtester processes exits before entries; new entries fill at the next
day's open).

v2 changes v1 in one way: the catastrophic stop moves from 0.75 x entry to
0.70 x entry. Evidence (2021-2026 backtest, 246 funded trades): the -25% stop
fired 36 times, mostly in two market-wide selloffs, and the stopped names
were on average 6% higher at the next rebalance than at the stop. In a
portfolio replay, -25% gave 11.13% CAGR, -30% 11.19%, no stop 12.48% but a
-48.5% worst trade. -30% is a wide stop within the range the stop-loss
literature finds not harmful; it is kept as tail insurance (Dec-2021, where
holding stopped names would have been much worse), not as a source of
return. Trailing stops, 200-day SMA exits and profit caps all reduced
returns on this data and are deliberately NOT used.

Leaderboard results are pre-cost (about 0.22% explicit cost per NSE delivery
round trip plus slippage) and value open positions at cost, so drawdowns are
understated. One 5-year window, 10 cohorts: do not tune these parameters on
it.

---

## Entry Reference

Entry Price: `entry_price` as passed in (the opening price on the trading
day after the signal day). `future_df` row 0 is the entry day in both the
backtest and the live Sell tab.

---

## Data Conventions (READ FIRST)

- Use positional access (`.iloc`). Session s = row s - 1 of `future_df`;
  session 1 is the entry day and its close IS checked.
- Compare calendar dates, not timestamps: for each row use
  `d = pd.Timestamp(future_df.index[i]).date()` (bars may carry a time such as
  18:30). Convert `entry_date` the same way.
- If a row's close is NaN, skip that row (no exit can fire on it) but still
  count it as a session.
- Trigger and fill both use the session's close. Never use intraday high/low.
- Do not raise. Return None if `future_df` is empty.

---

## Pre-Trade Calculation (Computed Once at Entry)

Let E = pd.Timestamp(entry_date).date().

Next_Rebalance = the earliest of these dates that is strictly AFTER E:
15 June of E's year, 15 December of E's year, 15 June of the next year.

Stop_Level = 0.70 * entry_price

LTCG_Date = E + 366 calendar days (informational only; used in
describe_state, never for exits).

---

## Daily State Variables

None.

---

## Daily Update Logic

None. For each session s = 1, 2, 3, ... (row s - 1 of `future_df`), check
the exit conditions at that session's close, in priority order.

---

## Exit Conditions

Evaluate in this order; exit on the first that fires. ExitDate is the
session's index label and ExitPrice is its close.

### Condition 1: Catastrophic Stop

If Close <= Stop_Level:
    EXIT at that session's close.
    Reason Tag: "CatastrophicStop"

### Condition 2: Rebalance

If the session's date d >= Next_Rebalance:
    EXIT at that session's close.
    Reason Tag: "Rebalance"

Notes:
- This is the first trading day on or after the next 15 June / 15
  December - the same day the entry rules treat as the next rebalance day.

### Condition 3: Maximum Holding Period (safety net)

If s >= 150:
    EXIT at that session's close.
    Reason Tag: "MaxHold"

Notes:
- Should never fire (a half-year is about 125 sessions); it only guards
  against a data gap.

---

## Exit Priority Order

1. CatastrophicStop
2. Rebalance
3. MaxHold

---

## Fallback

If no condition fires before `future_df` ends, return None. The backtester
then holds the trade to the end of the date range ("RangeEnd"); do not
implement that here.

---

## State Inspection (For HOLD Explanations, Not Used By The Backtester)

Also implement describe_state(entry_price, entry_date, signal_history_df,
future_df), returning a dict for the last row of `future_df` (None if
`future_df` is empty). LastClose = the last non-NaN close in `future_df`.

- TrailingStop          (Stop_Level; the stop is fixed, the key name is kept
                         for the Sell tab)
- DistanceToStopPct     ((LastClose - Stop_Level) / LastClose * 100)
- DaysHeld              (number of rows in future_df)
- DaysToMaxHold         (calendar days from the last row's date to
                         Next_Rebalance, floored at 0)
- NextRebalance         (ISO date string)
- RebalanceDue          (True if the last row's date >= Next_Rebalance)
- LastClose
- ReturnSinceEntryPct   ((LastClose - entry_price) / entry_price * 100)
- StopPctFromEntry      (-30.0)
- LTCGDate              (ISO date string of LTCG_Date)
- DaysToLTCG            (calendar days from the last row's date to
                         LTCG_Date, floored at 0)
````

## Conclusion

The exit file is not where the GARP strategy's remaining edge is. After testing stop levels, trailing stops, moving-average exits and longer holds, the most defensible exit is the one closest to v1, with a slightly wider stop. Every rule that looked better was either a calendar artefact (12-month holds), a funding-path accident (the 0.90 x SMA200 band) or a bet that the 2021-2026 recoveries will repeat (no stop). The useful finding is structural. A GARP portfolio rebuilt from annual fundamentals turns over mostly to itself in December, and an exit cannot see that, so it cannot avoid it. The `LTCGDate`, `DaysToLTCG` and `RebalanceDue` keys in v2 give a human using the Sell tab what the backtester cannot yet act on.

The practical sequence is: ship v2, fix funding and mark-to-market, add costs and tax, then build hold-through for re-selected stocks. Only then revisit the stop question, comparing the pre-registered challengers on a mark-to-market, after-cost leaderboard. If the Nifty 500 history can be extended before 2021, test them on that out-of-sample period first.
