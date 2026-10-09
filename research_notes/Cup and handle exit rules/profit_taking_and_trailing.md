# Upside Exit Management for Base Breakouts (Cup-and-Handle): Profit-Taking, Trailing Stops, Sell Signals, Letting Winners Run

Grading key: **rigorous** (peer-reviewed/large-sample systematic study), **practitioner** (large-sample practitioner backtest or the originator's own published rules), **secondary-only** (rule reported via a secondary source, primary not verified), **anecdotal** (examples/opinion).

Source-access notes: investors.com, alphaarchitect.com and traderlion.com returned 403; blog.marketsmithindia.com failed DNS. O'Neil rules below come via AAII (an O'Neil-authored/excerpted article) and secondary sources. Minervini rules are secondary-only. Earlier findings (IBD 20-25% rule, 8-week rule, 61% measured-move hit, 47%/23% give-back stats, OGA 2022) are not repeated except where needed for context.

## 1. O'Neil/IBD sell rules for winners beyond 20-25% (climax tops, 50-day/10-week breaks, late-stage)

### Takeaway
O'Neil's climax-top signals are well defined qualitatively but only partly numeric: biggest daily point gain since breakout, widest weekly range of the run, exhaustion gap, 7-8 up days out of 10 (or a 2-3 week rapid run-up), all after a run of many months. The 50-day MA rule needs heavy volume and no recovery (by week's end, or within the next day). The "65-100%+ above the 200-day" extension figures are secondary-only and not confirmed as O'Neil's own numbers.

### Cited Findings
- **Profit-taking baseline (O'Neil):** "sell many of your stocks when they are up 20% to 25% from your purchase price"; cut losses at 7-8%. 8-week exception: hold at least 8 weeks from the breakout buy point if the stock gains 20% within 1-3 weeks on good volume. [practitioner] — [AAII, O'Neil "When to Sell and Nail Down Your Profits"](https://www.aaii.com/journal/article/when-to-sell-and-nail-down-your-profits-while-you-still-have-them)
- **Climax-top signals (O'Neil, via AAII), all to be read after a run of many months:** [practitioner]
  - Largest daily gain: one of the climax days "will show the biggest point gain since the stock broke out".
  - Widest weekly spread: the week's low-to-high range is wider than in any prior week of the run.
  - Exhaustion gap: the stock opens on a gap above the prior close (example given: closes at $70, opens at $75).
  - Consecutive up days: "Many will run up seven or eight of 10 days in a row".
  - Channel line: breaking above an upper channel line means "75% to 80% of the time you're near a top".
  - Also: P/E expanding more than 100% from where the move began; RS rating falling below 70; excessive splits (3-for-1 or larger).
  — [AAII](https://www.aaii.com/journal/article/when-to-sell-and-nail-down-your-profits-while-you-still-have-them)
- **Climax-run definition:** leaders often top by "suddenly advancing at a much faster rate for one or two weeks after an advance of many months", often ending in an exhaustion gap on heavy volume. Sell if there is a rapid run-up for 2-3 weeks on the weekly chart, or 7 of 8 / 8 of 10 days up on the daily chart. Heaviest daily volume of the run is also a warning. [secondary-only] — [Nasdaq/Zacks, "SMCI: Shades of QCOM in 99'?"](https://www.nasdaq.com/articles/smci:-shades-of-qcom-in-99)
- **Extension figures (not confirmed as O'Neil's):** a secondary article on climax runs gives these signs: stock "over 65%" above its 200-day MA, more than 100% above it in extreme cases (Taser example), a 25-50% gain over 2-3 weeks, and 7 of 8 or 8 of 10 up days. The article cites O'Neil and Minervini generally but attributes none of these numbers directly. [secondary-only / anecdotal] — [TinTin Trading Substack](https://tintintrading.substack.com/p/how-to-identify-signs-of-climax-runs). I could not verify the commonly quoted "70-100% above 200-day MA" rule from a primary source.
- **50-day MA break, IBD version:** if a stock breaks below its 50-day MA on heavy volume "and can't rally back above it by week's end", buying demand is drying up and the run may be ending. The rule is framed around institutional distribution after a long advance. [secondary-only; summarises an IBD/WSJ-type article] — [StockCharts ChartWatchers, "One Key Signal That It's Time to Sell"](https://articles.stockcharts.com/article/articles-chartwatchers-2021-02-one-key-signal-that-its-time-t-215/)
- **50-day MA violation, O'Neil-disciple version (Morales/Kacher style):** "Stocks that do not show a tendency to hold above the 10-day MA for at least 7 weeks should be sold on a breach of the 50-day MA." A breach is when the stock breaks the 50-day MA and then "continues to trade below the breach-day low the next day". No volume threshold is given. The implied corollary is that stocks which held the 10-day for 7+ weeks get a looser trail. [secondary-only] — [TradingView, Rules of violation of the 50-day MA](https://in.tradingview.com/chart/VNINDEX/AgmKyPf9-Vnindex-Apr-2022-Rules-of-violation-of-the-50-day-MA)
- **10-week line, IBD:** IBD guidance is to hold through the first couple of pullbacks to, or slightly below, the 10-week line. A first pullback to the 50-day/10-week line is considered normal. [anecdotal; forum summarising IBD] — [Motley Fool discussion board, IBD 8-week hold rule](https://discussion.fool.com/t/ibd-8-week-hold-rule/112549)

### Inferences
- A daily-bar climax rule could be coded as: holding for 60+ trading days (a "many months" proxy) AND (largest 1-day % gain since entry, OR 7 of the last 8 / 8 of the last 10 closes up, OR an exhaustion gap-up open above the prior high, OR a 25%+ gain in the last 10-15 sessions), then exit fully or partly at that close. Every threshold except 7/8 and 8/10 is an interpretation, so they need testing on NSE data.
- 50-day exit for a daily strategy: close below SMA50 on volume above its 50-day average, then a close below that day's low (or no close back above the 50-day within 5 sessions). Apply it only after the trade has run (for example 20%+ gain, or 7+ weeks above the 10-day/21-day EMA). Before that, the initial stop governs.
- The 20-25% profit-take and the "let winners run via 50-day" rule conflict. O'Neil reconciles them with the 8-week rule, so a coded strategy needs an explicit branch: a fast 20% gain means hold; a slow 20% gain means take profit.

### Gaps
- I could not reach investors.com primary articles to confirm the exact volume threshold IBD uses for a "heavy volume" 50-day break (commonly cited as 40-50% above average, unverified).
- No primary source found for the "late-stage base (3rd/4th stage) → sell" timing rule with numbers. It is widely repeated, but I did not verify it this session.
- I found no systematic backtest of O'Neil climax-top signals.

## 2. Trailing-stop methods for trend/breakout trades (ATR chandelier, %, MA, SAR); does a wider trail help?

### Takeaway
Wider trails consistently beat tight ones in the breakout and stock data I found. Bulkowski found 10-day lowest-low trails beat 0-5 day trails, and percentage trails tighter than about 36% underperformed buy-and-hold in his 2003-08 test. Academic work shows trailing stops mainly reduce volatility and tail risk rather than raise raw returns. I found no rigorous head-to-head ranking of chandelier vs MA vs SAR exits for breakout trades. The chandelier default is 22-period, 3x ATR (LeBeau).

### Cited Findings
- **Bulkowski trailing-stop study** (upward breakouts from ascending triangles, double bottoms and rectangles; 1,099 stocks; 7/1991-7/2008; 3,068 samples). Trailing the stop below the lowest low of the prior N days gave these average results: N=0 2.42%, N=1 2.68%, N=2 2.85%, N=3 3.05%, N=4 3.37%, N=5 3.73%, N=6 3.92%, N=7 4.21%, N=8 4.42%, N=9 4.71%, N=10 5.66%. A volatility stop equalled the 5-day lowest-low result (3.73%). [practitioner, large sample] — [Bulkowski, Stops2](https://thepatternsite.com/Stops2.html)
  - The return rises monotonically with the lookback, so wider trails do better within the 0-10 day range. Caveat: the averages are small (2-6%). Short trails like these are exiting during normal noise, and nothing wider than 10 days was reported.
  - Bulkowski also found that a stop just below the breakout-day low, switching to a trailing volatility stop once that stop rises above the initial stop, worked better than a volatility trail alone. [practitioner] — [Bulkowski, Stops2 (via search summary)](https://thepatternsite.com/Stops2.html)
- **Bulkowski "Can stops hurt?"** (571 stocks, 12/2003-11/2008, percentage trailing stops from 1% to 60% vs buy-and-hold). Trails tighter than about 36% produced losses, with the worst result near 8%. A 60% trail was about equal to buy-and-hold, which was best (about $15/trade). Conclusion: "the stop takes you out of the most profitable trades". [practitioner; note the window includes the 2008 crash and has a small trade count] — [Bulkowski, CanStopsHurt](https://thepatternsite.com/CanStopsHurt.html)
- **Bulkowski's cup-with-handle-specific advice:** put the stop at the handle low and "raise the stop as price rises". [practitioner] — [Bulkowski, Cup with handle](https://www.thepatternsite.com/cup.html)
- **Dai, Marshall, Nguyen & Visaltanachoti** (25,997 US stocks, 1926-2016; 1%, 5%, 10% and 20% trailing stops). Trailing stops have "lower average gross returns but also lower volatilities than buy-and-hold". They beat buy-and-hold on a risk-adjusted basis for typical risk aversion and suppress tail risk well. They are most effective for stocks later delisted, volatile, liquid, low book-to-market stocks, and in declining markets. Results are gross; trading frictions would reduce them. [rigorous] — [CXO Advisory summary](https://www.cxoadvisory.com/technical-trading/trailing-stop-loss-effectiveness-for-stocks)
- **Kaminski & Lo, "When Do Stop-Loss Rules Stop Losses?":** under a random walk, stop-loss rules always reduce expected return. When momentum is present, they can add value. Empirically (monthly US equities, 1950-2004, switching to bonds when stopped out), some rules added 50-100 bp/month during stop-out periods. [rigorous; index level, not single stocks] — [MIT DSpace](https://dspace.mit.edu/handle/1721.1/114876)
- **Clare, Seaton, Smith & Thomas (2013, J. Asset Management):** on the S&P 500, simple trend rules (SMA 10-450 days, crossovers, 10-450 day channel breakouts, including the 200-day MA) dominate long-only buy-and-hold. They also tested adding stop-losses and the effect of measurement frequency. I could not retrieve the detailed stop-loss results (Alpha Architect returned 403). [rigorous; index, not single-stock breakouts] — [City Research Online](https://openaccess.city.ac.uk/id/eprint/17842); [IDEAS/RePEc](https://ideas.repec.org/p/yor/yorken/12-11.html)
- **Chandelier exit:** LeBeau recommended a 22-period lookback and 3x ATR below the highest high. Wider multiples exit later; tighter ones get shaken out more often. [practitioner/secondary] — [Incredible Charts](https://www.incrediblecharts.com/indicators/chandelier_exits.php); [CFI](https://corporatefinanceinstitute.com/resources/knowledge/tradinginvesting/chandelier-exit/)

### Inferences
- For daily NSE breakouts, the evidence favours a wide trail: chandelier 3-4x ATR(22), or a 10-week (50-day) MA close rule, rather than a 5-10% trail or a 10-day low. The tightest trail worth testing is about a 10-day lowest low or a 21-day EMA close, used only after a climax or an extended run.
- A staged approach fits all the evidence: (a) initial stop at the handle low or breakout-day low; (b) at about +1-2R or +10%, raise the stop to breakeven or a chandelier 3x; (c) let the 50-day or chandelier 3-4x ATR govern thereafter; (d) tighten to a 10/21-day trail only on climax signals.
- Indian mid/small caps have higher ATR, so ATR-based trails are preferable to fixed percentages because they adapt to each stock's volatility.

### Gaps
- I found no rigorous study ranking chandelier vs 10/21/50-day MA vs Parabolic SAR exits for single-stock base breakouts. A study across ATR multiples of 2.5x, 3x and 4x on breakout trades was not found either. This must be tested in-house.
- Faith's "Way of the Turtle" exit studies were not retrieved this session.

## 3. Fixed profit targets vs letting winners run; scaling out vs all-in/all-out

### Takeaway
The conventional view is that trend-followers should trail, because targets cap the right tail. But the one quantitative stock backtest I found (Arthur Hill, S&P 500, 20 years) showed an 8x ATR or 20% profit target beating a 4x ATR chandelier trail on CAR at similar drawdown, and combining the two was worst. Bulkowski's data (47% of cups retrace significantly within 2 months; only 39% of patterns reach the ultimate high within the pattern's width) also supports harvesting some profit. The evidence is mixed, so targets vs trails is an empirical question for the NSE universe.

### Cited Findings
- **Arthur Hill, StockCharts SystemTrader** (S&P 500 stocks, 4/1997-5/2017; entry when the 5-day EMA crosses above the 50-day EMA; base exit when the 50-day EMA crosses below the 200-day EMA). [practitioner]
  - Base system: CAR 7.73%, max drawdown 19.34%, 427 trades.
  - Chandelier (22, 4x ATR) trailing stop: CAR below 7%, drawdown about 19%, lower win rate, better avg gain/loss ratio.
  - 8x ATR(22) profit target: CAR 8.99%, drawdown about 19%, much higher win rate.
  - Combined trail plus target: the worst of the three.
  - The 8x ATR target on the S&P 1500 gave CAR 9.27% and drawdown 18.69% (best on the mid-cap 400, worst on the small-cap 600).
  - A 20% fixed profit target averaged CAR about 9.5%, drawdown about 19.5%, win rate about 54% across indices.
  - Hill's conclusion: "the profit target works better than the stop-loss".
  — [StockCharts, Trailing Stops vs Profit Targets](https://articles.stockcharts.com/article/articles-arthurhill-2017-05-systemtrader---trailing-stops-versus-profit-targets-for-a-moving-average-crossover-system/)
- **Conventional reasoning:** trend systems usually trail because a preset target caps the right tail. Mean-reversion systems prefer targets because the expected move is bounded. [practitioner opinion] — [LuxAlgo trailing method taxonomy](https://www.luxalgo.com/library/concept/trailing-method-taxonomy.md)
- **Cup-with-handle give-back** (supports partial harvesting): average rise 54% on 913 perfect trades, but 47% retrace significantly within two months and 23% rise no more than 15% before dropping. Throwback rate is 62%, and throwbacks hurt performance. Handles shorter than the median 22 days perform better. [practitioner] — [Bulkowski, Cup with handle](https://www.thepatternsite.com/cup.html)
- **Minervini-style scaling out:** sell into strength once the gain is a multiple of initial risk (minimum 2x, generally 2-3x, or above your average gain). Consider selling half and moving the stop on the rest to breakeven. [secondary-only] — [TraderLion (search snippet; page 403)](https://traderlion.com/investing-champions/mark-minervinis-risk-management/); [Stock Trading Approach Substack, Selling into Strength](https://stocktradingapproach.substack.com/p/selling-into-strength-a-strategy)

### Inferences
- The Hill result comes from an MA-crossover entry on large caps, not cup-with-handle breakouts. Large caps have a thinner right tail than NSE small/mid-cap leaders, so it should not be over-generalised. Still, it is real evidence that a target near 20% or 8x ATR can beat a 4x ATR trail on CAR.
- A hybrid is worth testing: sell 1/3-1/2 at +20-25% (or 2-3R), trail the rest with a 50-day close or 3-4x ATR chandelier. The O'Neil 8-week rule is an override: a 20% gain within 15 sessions means no partial sale for 40 sessions. Hill's finding that "combined was worst" applies to all-in/all-out trail+target, not to a partial scale-out, so the two do not directly contradict.
- I found no rigorous study isolating scale-out vs all-out effects on expectancy. Mathematically, scaling out reduces both variance and the right tail, and Sharpe can rise while CAGR falls.

### Gaps
- No peer-reviewed study of partial profit-taking vs all-out on breakout trades was found.
- Van Tharp-style R-multiple distribution studies were not retrieved.

## 4. Bulkowski: timing of the ultimate high after upward breakouts; retracement after the peak

### Takeaway
The ultimate high is defined as the highest high before a 20% decline, so by construction price retraces at least 20% from the peak. Only 39% of upward-breakout patterns peak within a time equal to the pattern's width, and 61% take longer. Fibonacci-level time or price clustering was absent. There is no clean "peak at day X" figure on which to anchor a max-hold.

### Cited Findings
- **Definition:** the ultimate high is the highest high before price drops 20%. Trades measured to it are "perfect trades", not replicable, but a consistent yardstick. [practitioner] — [Bulkowski, Time to ultimate high](https://www.thepatternsite.com/Time.html)
- **Time-to-peak study** (23,342 patterns, 40 pattern types, 1,000+ stocks, 7/1991-6/2008). For upward breakouts, 39% reached the ultimate high within the pattern's width and 61% took longer. For downward breakouts, 55% reached the ultimate low within the width. "I do not see anything significant here at all"; there were no peaks at Fibonacci extensions. [practitioner, large sample] — [Bulkowski, Time](https://www.thepatternsite.com/Time.html)
- **Cup duration:** cups run 7-65 weeks, and the handle forms in the upper half of the cup with a minimum of 1 week. Pattern width is therefore typically months, so "within pattern width" for a cup means roughly 2-15 months. [practitioner] — [Bulkowski, Cup with handle](https://www.thepatternsite.com/cup.html)
- **Average rise:** in Bulkowski's broader 45-pattern study (1,275 stocks, 1991-2006), upward breakouts averaged 33-35% rises to the ultimate high. [practitioner] — [Bulkowski, QConsecutive](https://www.thepatternsite.com/QConsecutive.html)

### Inferences
- Because 61% of upward breakouts peak later than the pattern width, a tight time-stop (for example 63 days) would truncate many big winners. A time-stop is better used as a "no progress" exit (for example, under +5-10% after N weeks) than as a hard cap on winners.
- Retracement after the peak is at least 20% by definition, so a trail tighter than about 20% (or about 3-4x ATR for typical NSE volatility) is what captures part of the move before the ultimate-high reversal completes.

### Gaps
- I did not find a Bulkowski table of the median days from breakout to ultimate high specifically for cup-with-handle (his book "Encyclopedia of Chart Patterns" has it; it was not online in the fetched pages).
- No data was found on the typical total decline after the ultimate high beyond the 20% definitional floor.

## 5. Minervini / SEPA-style sell rules

### Takeaway
All secondary-only. The rules found are: sell into strength once the gain is 2-3x initial risk (minimum 2x) or above your average gain; sell half and move the rest to breakeven; once there is a decent profit, protect breakeven or at least raise the stop.

### Cited Findings
- Minimum gain before selling into strength is 2x risk. If profit exceeds your average gain and is a multiple of risk (generally 2-3x), consider trailing a stop or selling half and raising the stop. Consider selling half and moving the stop on the rest to breakeven. [secondary-only] — [TraderLion (snippet)](https://traderlion.com/investing-champions/mark-minervinis-risk-management/); [Stock Trading Approach Substack](https://stocktradingapproach.substack.com/p/selling-into-strength-a-strategy)
- "Once you have a decent profit in a stock, protect your breakeven point, or at least raise your stop to reduce risk." [secondary-only, book summary] — [Shortform summary of Think & Trade Like a Champion](https://www.shortform.com/summary/think-trade-like-a-champion-summary-mark-minervini)
- He is described as emphasising selling into strength and capturing profits on the way up rather than selling into weakness. [secondary-only] — [ShareScope, "What can we learn from Mark Minervini"](https://knowledge.sharescope.co.uk/2022/06/24/the-trader-what-can-we-learn-from-mark-minervini/)

### Inferences
- Codable rule set: initial risk R = entry minus the stop (handle low). At +2R, sell 1/3-1/2 and move the stop to breakeven. At +3R or more, trail the rest (for example, a 50-day close or a chandelier).

### Gaps
- I could not verify from a primary source the often-quoted Minervini rules: "never let a gain of 2-3x your stop turn into a loss", the 10% / 20% gain-to-breakeven thresholds, or his specific climax-run day counts.

## 6. Maximum holding period conventions for base breakouts

### Takeaway
I found no evidence-based max-hold rule for winners. Practitioners rely on the 8-week minimum hold for fast movers (O'Neil) and on trend/MA exits, not time caps. Bulkowski's time-to-peak data argues against short time caps.

### Cited Findings
- O'Neil's 8-week rule sets a minimum hold (from the breakout buy point) for stocks up 20% in 1-3 weeks, not a maximum. [practitioner] — [AAII](https://www.aaii.com/journal/article/when-to-sell-and-nail-down-your-profits-while-you-still-have-them)
- 61% of upward breakouts take longer than the pattern width to reach the ultimate high. [practitioner] — [Bulkowski, Time](https://www.thepatternsite.com/Time.html)
- In the disciples' 50-day rule, stocks holding the 10-day MA for 7+ weeks graduate to a 50-day exit, which implies multi-month holds for leaders. [secondary-only] — [TradingView](https://in.tradingview.com/chart/VNINDEX/AgmKyPf9-Vnindex-Apr-2022-Rules-of-violation-of-the-50-day-MA)

### Inferences
- Suggested structure (for testing, not evidence-backed): (a) a stagnation time-stop at about 4-6 weeks (20-30 sessions) if the gain is under 5% and the stock has not made a new high since entry; (b) no hard cap on winners, which are governed by trail and climax rules; (c) an optional safety cap of about 250 sessions to bound the backtest.

### Gaps
- I found no study measuring expectancy vs max-hold length for cup-with-handle breakouts. This needs an in-house sweep (for example 40/63/126/252 sessions vs no cap).
