# ATR-Based and Volatility-Scaled Trailing Stop Techniques

## What is the exact formula for a Chandelier Exit, and what multiplier values are commonly recommended, and why?

### Takeaway
The Chandelier Exit trails a stop from the highest high (or lowest low) since entry/lookback, offset by a multiple of ATR; the canonical default is a 22-period lookback with a 3.0x ATR multiplier, with 2x–3x cited as the common working range. It was designed to keep a trader in a trend by giving room proportional to current volatility, rather than exiting on ordinary noise.

### Cited Findings
- Formula: Chandelier Exit (Long) = Highest High − ATR × Multiplier; Chandelier Exit (Short) = Lowest Low + ATR × Multiplier — [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit)
- Default setting is a 22-period lookback for the highest high/lowest low, with an ATR multiplier of 3.0; "common multipliers range from 2 to 3" — [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/technical-indicators-and-overlays/technical-overlays/chandelier-exit)
- The Chandelier Exit was developed by Charles Le Beau and popularized in Alexander Elder's books; it is explicitly designed "to keep traders in a trend and prevent an early exit as long as the trend extends," with the ATR component adjusting automatically to avoid premature exits during normal price swings — [Benzinga](https://www.benzinga.com/money/chandelier-exit-forex)
- A specific formulation citing Highest High(22) − 3.0×ATR(22) for longs and a symmetric short version — [StratBase.ai](https://stratbase.ai/en/blog/average-true-range-trailing-stop) (secondary aggregator; corroborates but does not independently source Le Beau/Elder's original text)
- A backtest of an EMA-crossover BTC/USDT strategy comparing exit methods found a Chandelier Exit (22, 3.0) produced a 1.61 profit factor vs. 1.28 for a fixed 10% trailing stop and 1.09 for a fixed 5% trailing stop — [quant-signals.com](https://quant-signals.com/atr-stop-loss-take-profit/) (single strategy/asset backtest, not a controlled multi-market study; treat as illustrative, not generalizable)

### Inferences
- The wide but bounded "2x–3x" convention across independent sources suggests this range is a genuine practitioner consensus for daily-bar swing/position systems, rather than one source's idiosyncratic default.
- Because the Chandelier Exit only needs daily H/L/C, it is fully computable from daily OHLCV with no intraday dependency.

### Gaps
- No primary source (Le Beau's original writing) could be directly retrieved; all Chandelier Exit descriptions found are secondary (StockCharts, Benzinga, blogs). The exact rationale Le Beau gave for choosing 3x specifically (vs. 2x or 2.5x) was not found — only "gives more breathing room" framing from secondary sources.

## What is the Turtle Trading system's N-based stop-loss and pyramiding/exit approach, and what were its historical results/known weaknesses?

### Takeaway
The Turtles defined volatility as "N" (a 20-day ATR), sized positions so that 1N of adverse move equaled a fixed fraction of account risk, placed a hard stop at 2N from entry, and exited System 1 (20-day breakout entries) on a 10-day low/high and System 2 (55-day breakout entries) on a 20-day low/high; the approach produced spectacular multi-year returns (average ~80%/yr over the 1983–1988 experiment) but is structurally vulnerable to prolonged whipsaws in range-bound markets.

### Cited Findings
- Entries: System 1 triggers on a breakout of the prior 20 trading days' high/low; System 2 triggers on a breakout of the prior 55-day high/low — [TrendSpider](https://trendspider.com/learning-center/richard-dennis-turtle-trading-strategy/)
- Stop-loss: "a volatility-based stop loss which is called 2N stop and it is determined by doubling the 20-day Average True Range (ATR)... Every unit had a stop placed 2N from the entry price, and combined with the sizing formula, a 2N loss equals roughly 2% of the account per unit" — [TrendSpider](https://trendspider.com/learning-center/richard-dennis-turtle-trading-strategy/)
- Exit rules: System 1 exits longs on a 10-day low breakdown; System 2 exits on a 20-day low breakdown (mirrored for shorts) — [TrendSpider](https://trendspider.com/learning-center/richard-dennis-turtle-trading-strategy/)
- "The system profited because its losses were structurally small (2N stops, volatility-normalized units) while its wins were structurally unlimited (no targets, wide trailing exits, pyramided positions)" — [TrendSpider](https://trendspider.com/learning-center/richard-dennis-turtle-trading-strategy/)
- Historical results: over the first four years of the Turtle experiment the group earned an aggregate of over $100 million; "the average annual compound return of the group was approximately 80% over five years," with several individual Turtles exceeding 100–200% annualized in certain years; Dennis made $80 million in 1986 alone but lost more than half his assets between 1987 and 1988 — [Altrady](https://www.altrady.com/blog/crypto-trading-strategies/overview-historical-performance)
- Known weaknesses: "This type of trading system will generate losses in periods when the market is rangebound, often for months at a time, and profits during large market moves"; "the 20-day breakout (S1) gives faster, more frequent signals, but it produces more whipsaws in choppy markets" — [IG International](https://www.ig.com/en/trading-strategies/turtle-trading--what-is-it-and-what-are-the-rules--180904) / [PickMyTrade blog](https://blog.pickmytrade.trade/understanding-the-turtle-trading-strategy-the-s1-system/)
- General system character: "many trades, only a few of which turned into big winners. Many others were small losses" (classic trend-following low-win-rate/large-payoff profile) — [Medium (Trading Dude)](https://medium.com/@trading.dude/discipline-over-prediction-why-the-turtle-trading-rules-still-matter-f0f1d400d58d)

### Inferences
- The 2N initial stop combined with a much tighter trailing exit (10-day or 20-day low) means the Turtle system's effective risk after the trade moves favorably is far tighter than the initial hard stop — the "stop" and "exit" are two separate distances, which is a useful pattern to replicate mechanically (wide catastrophic stop + narrower trend-following trailing exit).
- The specific dollar/return figures ($100M, 80%/yr, $80M in 1986) come from popularized retellings rather than an audited track record; treat exact numbers as approximate/anecdotal rather than rigorously verified performance statistics.

### Gaps
- Could not find the original Curtis Faith "Way of the Turtle" primary text or an official public Turtle Rules PDF within the tool budget; all figures here are from secondary retellings that may compound rounding/exaggeration from the original source.
- No precise, source-backed decomposition of win rate vs. average win/loss size for the Turtle system was found (only qualitative "few big winners, many small losses" framing).

## How does Wilder's original ATR trailing stop work, and what does Wilder recommend for the multiplier?

### Takeaway
Wilder's Volatility System (from *New Concepts in Technical Trading Systems*, 1978) sets a stop by subtracting (for longs) or adding (for shorts) a multiple of ATR from the "significant close" — the most favorable close reached since the trade began — and secondary sources report Wilder's original calculation used a multiplier of roughly 2.8–3.1 applied to a 7-day ATR, though this could not be verified against the primary text.

### Cited Findings
- "The Average True Range (ATR) was first introduced by J. Welles Wilder in his 1978 book 'New Concepts in Technical Trading Systems'" — [multiple aggregator sources, e.g. GitHub stock-indicators discussion](https://github.com/facioquo/stock-indicators-dotnet/discussions/724)
- The Wilder Volatility Stop "calculates the long stop by subtracting an ATR multiple from the 'significant close' in the lookback period. In an uptrend the 'significant close' is located at the highest close since the start of the trend" — [LizardIndicators](https://www.lizardindicators.com/volatility-stop/)
- Wilder refers to the significant close as "the extreme favorable close price reached while in a trade" — [LizardIndicators](https://www.lizardindicators.com/volatility-stop/)
- "Welles Wilder's calculation used a multiplier of 2.8-3.1 applying it to an ATR with a period of 7" — [search-result synthesis citing LuxAlgo/optimusfutures-type sources](https://www.luxalgo.com/library/concept/volatility-stop/) (could not confirm this figure directly against Wilder's original book text; flagged lower-confidence)
- "The multiplier proposed by Wilder is meant for use in higher timeframes than 60 minutes, or on daily charts" — [LizardIndicators](https://www.lizardindicators.com/volatility-stop/)
- Published multipliers for ATR-based systems generally "commonly fall between 2 and 3.5, but no constant is canonical" — [search synthesis, general sourcing across ATR articles]

### Inferences
- Wilder's original system uses the *close* (not the high/low) as the reference price for the trailing stop's anchor point, which is a meaningful distinction from the Chandelier Exit (which anchors to the highest high/lowest low). This makes Wilder's version slightly less aggressive/tighter in practice since the close is typically inside the day's high-low range.
- A 7-day ATR is notably shorter than the 14/20/21/22-day periods common in modern Chandelier/SuperTrend implementations, implying Wilder's original system was tuned to be more reactive than most present-day derivatives.

### Gaps
- Direct/primary confirmation of Wilder's exact recommended multiplier (2.8–3.1) and 7-day ATR period was not obtainable from the original book text within this research; all findings here trace back to secondary paraphrases (LizardIndicators, LuxAlgo-style aggregators) rather than a page/quote from "New Concepts in Technical Trading Systems" itself. This should be flagged as moderate-confidence, not verified against primary source.

## What are the tradeoffs between a tighter vs. wider ATR multiplier, ideally with quantitative backtest data comparing multipliers?

### Takeaway
Tighter multipliers (1.5x–2x) lock in profit sooner and reduce giveback but incur materially higher whipsaw/stop-out rates in normal volatility, while wider multipliers (3x–4x) survive noise better but give back much more open profit before triggering; the few quantitative comparisons found favor roughly 2x ATR for profit-factor-optimized systems, but sample sizes and methodology transparency in these sources are limited.

### Cited Findings
- "The average profit factor across all 2.0x strategies reached 1.16, compared to 1.08 for 1.5x and 1.01 for 3.0x multipliers, indicating that 2x ATR performed best among those tested. Additionally, 2.0x ATR multiplier delivered the best overall performance with 1.26 average profit factor across a broader backtest" — [QuantVPS](https://www.quantvps.com/blog/atr-stop-loss) (methodology/sample details not disclosed in the retrievable content; treat as lower-confidence, vendor-blog-style claim)
- "BTCUSD using a 2x ATR stop loss generated a 1.72 profit factor with only 4.6% maximum drawdown" — [QuantVPS](https://www.quantvps.com/blog/atr-stop-loss) (single-asset result; not generalizable)
- "By trading style, day traders typically use 1.5x to 2x, swing traders generally work with 2x to 3x, and position traders and trend followers often extend to 3x to 4x" — [QuantVPS](https://www.quantvps.com/blog/atr-stop-loss)
- "Smaller multipliers reduce dollar risk but increase whipsaws relative to normal volatility, while larger multipliers require reducing position size to keep total risk under control" — [QuantVPS](https://www.quantvps.com/blog/atr-stop-loss)
- A volatilitybox.com article presented a table purportedly from "200 S&P 500 swing setups (2020–2024)" showing Fixed $3 Stop (38.2% win rate, +$0.41 expectancy, -18.4% max DD, 47% premature stop-out at VIX>25) vs. ATR 2.0x (47.6%, +$0.72, -11.7%, 21%) vs. Chandelier Exit 22/3x (51.3%, +$0.81, -10.2%, 16%) vs. Keltner Lower Band (44.8%, +$0.66, -13.1%, 24%), concluding volatility-adjusted stops "reduced premature stop-outs by 34% compared to fixed-dollar stops" — [Volatility Box](https://volatilitybox.com/research/volatility-adjusted-stop-losses/) — **flagged low-confidence**: no methodology, data source, or author credentials disclosed; the precision of the figures (e.g., "+$0.81") without underlying position-sizing context, combined with a generic content-farm-style URL structure, suggests this may be an illustrative/synthetic example rather than a genuine, reproducible backtest. Should not be treated as a validated empirical result.

### Inferences
- Across sources, there is directional agreement (tighter multiplier → higher win rate/lower drawdown but more whipsaw exposure; wider multiplier → fewer whipsaws but larger giveback), which matches basic volatility-stop theory. However, none of the available sources are academically rigorous or independently reproducible — all are trading-education/vendor blogs.
- Given the consensus "trend follower/position trader" range of 3x–4x ATR from multiple independent style-segmented sources (QuantVPS's style breakdown, Chandelier's 2-3x default, Wilder's ~3x), a mechanical breakout exit system aiming to "let winners run" (per the strategy's own naming convention referenced in the user's repo, e.g. atr_trailing_stop_let_winners_run) is better served by multipliers in the 2.5x–3.5x band rather than <2x, consistent with the position-trading segment.

### Gaps
- No peer-reviewed or independently reproducible quantitative study directly comparing 2x vs 2.5x vs 3x vs 4x ATR trailing stops on a standardized trend-following system/universe was found. All available "backtest" data comes from marketing-adjacent blog content with undisclosed methodology; this is a significant gap for anyone wanting statistically robust guidance. Recommend treating the "2x optimal" claims as directional signal only, not as validated fact.

## Are there known best practices for combining a trailing stop with a time-based stop for breakout entries, and what N values are typically used?

### Takeaway
Time-based stops (exit a trade that hasn't produced a profit — or hasn't hit either the stop or a target — within N bars/days) are a recognized, low-curve-fit complement to volatility trailing stops, most commonly documented in intraday opening-range-breakout contexts; documented daily-bar N values for swing/position breakout systems specifically were not found in reputable sources.

### Cited Findings
- "A time stop exits if price re-enters the box and sits there for N bars," commonly used with opening range breakout (ORB) strategies — [ForexTester](https://forextester.com/blog/opening-range-breakout-trading-strategies/)
- A specific ORB example: "exit at 3:30 PM ET if neither the profit target nor the stop loss has been hit, ensuring all positions are closed before the final 30 minutes of trading" — [Options Cafe](https://options.cafe/blog/0dte-opening-range-breakout-strategy-spy-backtested-results/) (this is an explicitly intraday, close-out-by-time-of-day rule — not directly transferable to a daily-bar-only system, since it depends on intraday time-of-day data)
- "Time exits work well when used in conjunction with a profit target exit and a stop-loss exit, giving the trade a certain fixed amount of time to either hit the profit target or the stop-loss; if not, the trade exits" — [Medium/Jakub Polec, "Stop-Loss, Take-Profit, Triple-Barrier & Time-Exit"](https://medium.com/@jpolec_72972/stop-loss-take-profit-triple-barrier-time-exit-advanced-strategies-for-backtesting-8b51836ec5a2) — this describes the "triple-barrier method" (profit target, stop-loss, and time barrier), a technique with more rigorous quantitative-finance grounding (associated with Marcos López de Prado's *Advances in Financial Machine Learning*, though that specific attribution was not independently re-confirmed in this search pass)
- "If you backtest a signal and find the results are not significantly different than your control group over defined holding periods or 'time stops,' this is a clear sign that the trading signal is not valid... A time-based exit after a set number of periods or days is very simple and often underrated, as it limits time in the market and reduces drawdown without a lot of curve fitting" — [KJ Trading Systems](https://kjtradingsystems.com/algo-trading-exits.html)

### Inferences
- The "triple-barrier" framing (profit target / stop-loss / time limit, whichever hits first) is the most conceptually rigorous version of combining a volatility trailing stop with a time stop, and it generalizes cleanly to a purely daily-OHLCV system since the time barrier is simply "N trading days since entry," not tied to intraday clock time.
- No source gave a specific, backtested N (e.g., "exit after 10 days if no profit") for a daily-bar swing/position breakout system; the concrete N values found (3:30pm ET same-day) are for intraday ORB and are not applicable to a daily-close system.

### Gaps
- Could not find a reputable, quantitative source specifying a particular N-day threshold (e.g., 5, 10, 20 days) for a "no profit yet → exit" time stop on daily-bar breakout trades. This is a genuine gap in the available literature (or at least in what surfaced in this search pass) — most concrete N values found are intraday/time-of-day based and not directly reusable for a daily-close-only mechanical system.

## What are best practices for ATR lookback period (14 vs 20 vs 21), and is there literature showing sensitivity to this choice?

### Takeaway
ATR(14) is treated as the widely-used default/baseline; ATR(20)/ATR(21) are common alternatives (21 specifically used by StockCharts) associated with smoother, less noise-reactive stops suited to longer average hold times; guidance is largely qualitative/heuristic (e.g., match ATR period to typical trade duration) rather than backed by rigorous sensitivity backtests.

### Cited Findings
- "ATR(14) sits in the middle, responsive enough for active markets and stable enough for routine use. ATR(14) is the most widely used baseline for stop losses across stocks, forex, and crypto. A 14-period ATR with a 2x multiplier on a daily chart is a robust baseline" — [search synthesis of ATR guidance articles, e.g. LuxAlgo/quantstock-style sources](https://www.luxalgo.com/blog/average-true-range-dynamic-stop-loss-levels/)
- "In the StockCharts platform, the ATR is set to 21 days" — [general ATR sourcing]; Chandelier Exit / SuperTrend defaults commonly cite 20 or 22-day lookbacks (see Chandelier Exit section above)
- "Longer periods smooth out volatility readings and work well for position traders who hold for weeks or months, with a 20 or 30-period ATR filtering short-term noise" — [search synthesis]
- Practical rule of thumb: "If your average trade lasts 5 days, use a 10-14 period ATR; if you hold for 20 days, consider a 20-30 period ATR. If you trade fast intraday moves, ATR(10) can react quicker, while ATR(20) can smooth noise for swing trades" — [search synthesis of ATR stop-loss guides]

### Inferences
- The recommendation to match ATR lookback to expected holding period is a consistent heuristic across sources, suggesting it's genuine practitioner consensus even though it isn't derived from a controlled sensitivity study.
- Because ATR(14), ATR(20), ATR(21), and ATR(22) all appear as "defaults" in different widely-used tools/platforms (Wilder's original 14-day ATR for RSI-era indicators, StockCharts' 21-day, Chandelier's 22-day, Turtle's 20-day N), the specific choice within this 14–22 day band is probably a second-order effect compared to the multiplier choice — no source claimed a strong performance difference specifically from period choice within this range.

### Gaps
- No quantitative backtest was found that isolates ATR period choice (holding multiplier and strategy constant) and reports a performance delta between e.g. ATR(14) vs ATR(20) vs ATR(21). All available guidance is heuristic/rule-of-thumb rather than empirically demonstrated sensitivity analysis. This is a real gap — the literature does not show much (if any) rigorous quantitative sensitivity testing on this specific parameter, only informal convention-matching-to-holding-period advice.

## Supplementary: SuperTrend and Parabolic SAR (related volatility-scaled stop/reversal systems)

### Takeaway
SuperTrend is a band-based ATR stop-and-reverse indicator (bands = midpoint ± multiplier×ATR, commonly ATR(10) or ATR(14) with a 3.0 multiplier) that flips direction on a close through the band; Parabolic SAR is Wilder's original stop-and-reverse system using an accelerating step factor (starting at 0.02, incrementing 0.02 per new extreme, capped at 0.2) — both are computable from daily OHLC and require no intraday data, though SAR's acceleration mechanic makes it more aggressive/tightening over time than a constant-multiplier ATR stop.

### Cited Findings
- SuperTrend formula: Upper Band = (High + Low)/2 + (Multiplier × ATR); Lower Band = (High + Low)/2 − (Multiplier × ATR); "Most charting platforms use ATR Period 10 and Multiplier 3.0 as defaults," though "Default settings (ATR 14, Multiplier 3) work well for most assets" per other platforms — [search synthesis, TrendSpider/LuxAlgo-style sources](https://trendspider.com/learning-center/supertrend-indicator-a-comprehensive-guide/)
- "A bullish trend is signaled when the price closes above the SuperTrend line, while a bearish trend is triggered when the price falls below it" (i.e., SuperTrend is a stop-and-reverse system, not merely a one-directional trailing stop) — [search synthesis]
- Parabolic SAR formula: Uptrend PSAR = Previous PSAR + AF×(EP − Previous PSAR); Downtrend PSAR = Previous PSAR − AF×(Previous PSAR − EP), where EP is the extreme price (highest high in uptrend / lowest low in downtrend) — [QuantInsti](https://blog.quantinsti.com/parabolic-sar/)
- "The AF starts at .02 and increases by .02 whenever the extreme point makes a new high, with a maximum value of .20... Wilder recommends using an initial factor of 0.02, which increases by 0.02 with each new bar until it reaches a maximum value of 0.2" — [QuantInsti](https://blog.quantinsti.com/parabolic-sar/) / [TradingSim](https://www.tradingsim.com/blog/parabolic-sar)
- "In an uptrend, the dot is never allowed to move above the lows of the previous two periods; if the formula tries to place it there, the platform uses the lower of those two lows instead" — [search synthesis]

### Inferences
- Both SuperTrend and Parabolic SAR are fully computable from daily OHLC (no intraday data dependency), making them viable for a daily-close-only mechanical system, same as Chandelier/Wilder ATR stops.
- Parabolic SAR's accelerating factor means it trails progressively tighter the longer a trend persists (up to the 0.2 cap), which is a structurally different behavior from a constant-multiplier ATR/Chandelier stop that maintains the same relative distance throughout the trade — worth noting as a design choice (constant vs. accelerating tightening) for a mechanical exit rule set.

### Gaps
- Kase (Dr. Cynthia Kase's volatility-based stop system) was in the original research scope but no source specific to Kase's exact formula or multiplier recommendations was retrieved in this pass — this is a gap; would need a dedicated follow-up search (e.g., "Kase DevStop formula" or Kase Statware documentation) to cover it properly.
- No quantitative comparison was found between SuperTrend/Parabolic SAR and Chandelier/Wilder ATR stops on a standardized backtest.
