# Stops and Failed-Breakout Exit Rules for Long Base Breakouts (Cup-and-Handle Focus)

Context: daily-bar, long-only NSE system, entry at breakout-day close. Builds on earlier findings (O'Neil 7-8% stop; Bulkowski handle-low stop; cup throwback 62%; throwbacks return to breakout after ~10 days; 35% keep falling; above-breakout trades rose 40% vs 29%; high-volume breakouts throw back 70%). Those are not repeated here except where needed for context.

Grading key: **rigorous** = peer-reviewed or large systematic sample with stated method; **practitioner** = systematic but non-peer-reviewed (e.g., Bulkowski's own databases); **secondary-only** = restatement of a source I could not read directly; **anecdotal** = forum posts, single-chart commentary, vendor blogs.

## 1. Quantitative evidence comparing stop types (fixed %, structural, volatility, none)

### Takeaway
Rigorous academic work says stops reduce risk (drawdown, left-tail, volatility) but generally do not raise returns on individual stocks, and tight stops lose money after costs because single-stock returns have been mean-reverting at short horizons. Stops add value mainly when returns trend (momentum/serial correlation). Bulkowski's practitioner data agrees: tight stops get hit very often and remove the best trades, while structural stops placed further back are hit much less.

### Cited Findings
- **Kaminski & Lo (rigorous, theory + US index data 1950-2004).** Under a random walk, simple 0/1 stop-loss rules always lower expected return. Stops can add value only if returns have momentum, or (in regime-switching models) if the low-mean regime returns less than the risk-free rate — [dailyspeculations summary](https://dailyspeculations.com/wordpress/?p=14247); [BSIC](https://bsic.it/how-to-define-a-stop-loss/). Empirically, some stop rules applied to US equities (switching into long-term bonds) added 50-100 bp/month during stop-out periods — same sources. A 10% stop rule: equities beat bonds 70% of the time the rule was invested, but only 30% of the time during stopped-out periods — [quant-investing.com](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe) (secondary). Caveat: this is an asset-allocation stop on a market index using monthly returns, not a single-stock breakout stop. Paper PDF: [MIT DSpace](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf) (could not fetch; numbers come from summaries).
- **Lo & Remorov, "Stop-Loss Strategies with Serial Correlation, Regime Switching, and Transaction Costs" (rigorous, US common stocks 1964-2014).** On a large sample of individual US stocks, tight stop-losses underperform buy-and-hold on a mean-variance basis because of trading costs. Outperformance is possible only for stocks with high enough serial correlation — [MIT DSpace](https://dspace.mit.edu/handle/1721.1/107017); [CXO Advisory](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth). Stops tested: daily 0% to -6%; 10-day cumulative 0% to -14%. Costs: half-spread of 0.2% in simulations. "Wide 10-day stop-losses generally perform about as well as buy-and-hold" and "consistently increase return skewness and reduce maximum drawdown." Negative stock autocorrelation in recent decades made tight stops unattractive — [CXO Advisory](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth).
- **Han, Zhou & Zhu, "Taming Momentum Crashes: A Simple Stop-Loss Strategy" (rigorous, US momentum 1926-2011).** A 10% stop on each long leg (sell, hold cash until month-end) cut the worst monthly loss of equal-weighted momentum from -49.79% to -11.34%, and of value-weighted from -65.34% to -23.69%. Average returns and Sharpe ratios more than doubled — [Crossing Wall Street](https://www.crossingwallstreet.com/?p=28384). Equal-weighted: mean monthly return 1.01% to 1.73%, SD 6.07% to 4.67%, Sharpe 0.166 to 0.371 — [quant-investing.com](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe) (secondary). Alpha Architect questioned whether the result holds up ("fact or fiction") — [Alpha Architect](https://alphaarchitect.com/2016/08/taming-the-momentum-roller-coaster-fact-or-fiction/). That page returned HTTP 403, so I could not verify the critique's content. A common concern with such studies is that they assume fills exactly at the stop price (see section 6).
- **"Do initial stop-losses stop losses?" (Bangor/Bond University; rigorous, but I could not read the full text).** Traditional and trailing stops "neither reduce nor increase investors' losses relative to buy-and-hold." Trailing stops reduce risk by 28.66%-47.08% for some stock categories — summary via search snippets of [Bangor research portal](https://research.bangor.ac.uk/en/publications/do-initial-stop-losses-stop-losses/) / [Bond research portal](https://research.bond.edu.au/en/publications/do-initial-stop-losses-stop-losses/) (secondary-only; the page fetch failed).
- **Snorrason & Yusupov (Lund University master's thesis, OMX Stockholm 30, 1998-2009; practitioner/academic-lite).** Stops tested from 5% to 55%. 15-20% trailing stops did best (20% trailing: 1.71% mean quarterly return; 15% trailing: 73.91% cumulative). A 5% trailing stop did worst (-8.14% cumulative). A 10% traditional stop gave 57.10% cumulative — [quant-investing.com](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe); [Lund](https://www.lunduniversity.lu.se/publication/1474565).
- **Bulkowski, "Can Stops Hurt?" (practitioner; 571 stocks, 2003-2008, buy on the first trading day of each month, exit at month-end).** Trailing stops tested from 1% to 60%, plus 100% (buy-and-hold). "If you place a trailing stop closer than 36% below the current high price, you'll lose money." Buy-and-hold made the most, about $15/trade, because tight stops "take you out of the most profitable trades" — [thepatternsite CanStopsHurt](https://thepatternsite.com/CanStopsHurt.html). Caveat: entries were random monthly, not pattern breakouts.
- **Bulkowski volatility stop (practitioner; about 100 of his own trades, 2003-2005).** Best parameters: 2x the average daily high-low range over a 22-bar lookback. Average give-back from the peak before stop-out was 6.88%. It improved trade profitability only 48% of the time. "All of the stop methods tended to take you out of the best performing trades prematurely" — [thepatternsite stops](https://thepatternsite.com/stops.html).
- **Bulkowski, structural vs. volatility (practitioner; 3,068 upward breakouts).** "A tight stop placed 2 cents below the breakout day's low, followed by a trailing volatility stop, works better than a volatility stop alone" — [thepatternsite Stops2](https://www.thepatternsite.com/Stops2.html) (as summarized in search snippet).

### Inferences
- For single-stock breakout trades, the evidence argues against tight fixed stops (under about 4-5%) and for structural stops wide enough to sit outside normal post-breakout noise. Expect a stop to cut tail losses, not to raise average return.
- The positive Han/Zhou/Zhu result comes from a trending (momentum) context. Breakouts are momentum-like entries, which is the case where Kaminski & Lo's theory says stops can help. But Lo & Remorov's negative single-stock autocorrelation is a warning that daily-close stops on noisy NSE mid/small caps could whipsaw.
- No study found directly compares fixed %, handle-low, and ATR stops on cup-and-handle breakouts. The NSE backtest itself should run that comparison.

### Gaps
- No peer-reviewed study of stop type specifically on chart-pattern breakouts.
- Could not read the Alpha Architect critique of Han et al. (HTTP 403) or the full Kaminski & Lo / Bangor papers.
- No ATR-multiple stop study specific to breakouts beyond Bulkowski's small personal-trade sample.

## 2. Buffer below handle low / pivot; stops just below the pattern vs further away

### Takeaway
Bulkowski's largest stop study shows stop-hit rates fall sharply the further back the reference low is: 61.5% for the breakout-day low, 41% for the prior day's low, about 15% for the lowest low of the prior 10 days. His recommended buffer is only "a penny / few pennies" below the structural low. The handle low usually sits 5-15% below the pivot, which is near or beyond O'Neil's 7-8%.

### Cited Findings
- **Bulkowski Stops2 (practitioner; 3,068 upward breakouts from ascending triangles, double bottoms, and rectangles; 1,099 stocks; July 1991-July 2008).** Stop placed 2 cents below the lowest low from N days before breakout through breakout day; hit rate within the following month and average loss — [thepatternsite Stops2](https://thepatternsite.com/Stops2.html):

  | Reference low | % hit | Avg loss |
  |---|---|---|
  | Breakout day | 61.5% | 2.19% |
  | 1 day prior | 41.0% | 4.29% |
  | 2 days prior | 33.2% | 5.21% |
  | 3 days prior | 28.2% | 5.77% |
  | 10 days prior | 14.9% | 7.53% |

- Same study: a stop less than 4% below the breakout price was hit 48% of the time within a month. For an 8% stop, "75% drop less than 8%." Average post-breakout drop was 5.3% (median 4.2%). "Half the time it will take 8 days before the stock returns to the breakout price" — [thepatternsite Stops2](https://thepatternsite.com/Stops2.html). Cup-and-handle was not in this sample.
- **Bulkowski buffer convention (practitioner, qualitative):** stops "a penny," "a nickel," or "a few pennies" below pattern extremes. A stop placed at a 67% retrace "will work two-thirds of the time" (broadening patterns) — [thepatternsite Stoplocate](https://thepatternsite.com/Stoplocate.html); [thepatternsite stops](https://thepatternsite.com/stops.html).
- **Cup-specific:** "The handle low (point C) is a good place to put a stop. Raise the stop as price rises." 47% of cups "dropped substantially within two months of the breakout"; 23% rise no more than 15% before dropping; break-even failure rate 5% — [thepatternsite cup](https://thepatternsite.com/cup.html).
- Practitioner restatements: the standard stop is just below the handle low, with some traders using the cup low instead — [sponser.co.il PDF / search summary](https://www.sponser.co.il/forumfiles/6910Cup%20With%20Handle.pdf) (anecdotal/secondary).

### Inferences
- The table implies that a stop must sit below a meaningful multi-day swing low to avoid being hit most of the time. The handle low is that kind of low (it typically spans 1-4+ weeks), so its hit rate should be closer to the "10 days prior" row (about 15%, about 7.5% loss) than the tight rows. This is an extrapolation.
- With 1-day-prior stops hit 41% of the time, a close-based rule near the pivot (e.g., "close below pivot") will fire frequently. That is consistent with the earlier finding of 62% cup throwbacks.
- Practical rule candidate: stop = min(handle low minus a small buffer such as 0.5-1% or 0.25-0.5 ATR, entry x (1 - max_loss)). The max_loss cap (8-10%) handles deep handles. The buffer size is a judgment call; no study pins it beyond "pennies."

### Gaps
- No Bulkowski hit-rate table for cup-handle-low stops specifically, and none for percentage buffers (e.g., 1% vs 3% below the low).
- No data on how often winners (trades that later hit target) first violate the handle low.

## 3. Failed-breakout definitions with numbers

### Takeaway
Bulkowski's quantitative definition of a "busted" pattern is: breaks out, moves no more than 10%, then reverses through the opposite side of the pattern (for a cup, below the handle/cup low). Busted patterns often move strongly the other way. IBD/O'Neil defines failure loosely as a fall back below the buy point / into the base, with a hard 7-8% loss cap. IBD also says normal pullbacks to the buy point happen within days. No rigorous data defines an optimal "close X% below pivot" threshold.

### Cited Findings
- **Bulkowski busted pattern (practitioner):** "breaks out in the expected direction, moves no more than 10% in that direction before reversing," then breaks out the other side. The 10% is "arbitrary," and the test used "no time limit" — [thepatternsite BustedPatterns](https://www.thepatternsite.com/BustedPatterns.html); [thepatternsite Busted](https://thepatternsite.com/Busted.html).
- After busting, moves in the new direction are often larger than non-busted moves. Ascending triangle: busted 51% vs non-busted 43%. Descending triangle: 54% vs 38%. Adam-and-Eve double: 52% vs 43% — [thepatternsite BustedPatterns](https://www.thepatternsite.com/BustedPatterns.html). Implication for longs: a busted bullish breakout can lead to a large decline, so exiting on the bust matters. (Cup-with-handle busted stats were not on the page.)
- 23% of cups rise no more than 15% before dropping — [thepatternsite cup](https://thepatternsite.com/cup.html).
- **O'Neil/IBD (secondary-only; investors.com not accessed):** a breakout that reverses 7-8% below the buy point is sold "without debate." Breakout volume should be at least about 40% above average — [LuxAlgo O'Neil base analysis](https://www.luxalgo.com/library/concept/oneil-base-analysis/) (secondary). "If the stock clears the buy point, then crashes back below on volume, it's a failed breakout" — [beehiiv fake-breakouts post](https://beginners-in-stock-trading-ddb2b0.beehiiv.com/p/avoiding-fake-breakouts-how-to-identify-traps-before-you-buy-b8a4) (anecdotal). IBD-follower restatements: "about 40% of breakouts come back to the buy point." A normal pullback usually happens "within days rather than weeks," on lighter volume, to or just below the buy point. Never let a gain of more than 10% turn into a loss — [Motley Fool "Trading IBD Stocks" thread](https://discussion.fool.com/t/trading-ibd-stocks/104584) (anecdotal). Later-stage bases (third and beyond) fail more often per IBD studies — [LuxAlgo](https://www.luxalgo.com/library/concept/oneil-base-analysis/) (secondary).
- Bulkowski also suggests a trendline along the handle peaks as an alternative entry/exit reference — [thepatternsite cup](https://thepatternsite.com/cup.html).

### Inferences
- A layered failure definition is consistent with the sources. (a) A soft failure is a close back below the pivot on above-average volume. The data says this is common (40-62% of breakouts) and often recovers, so it is a warning or position-trim signal, not an automatic exit. (b) A hard failure is a close below the handle low, which is near Bulkowski's "bust" condition (exits the opposite side of the near-term structure). (c) An absolute cap is a close more than 7-8% (O'Neil) or about 10% below entry.
- Because high-volume breakouts throw back 70% of the time (earlier research), a "close below pivot = exit" rule would hit most of the best breakouts too. Avoid it unless tested.

### Gaps
- No primary IBD text accessed (investors.com likely blocked). The "40% return to buy point" figure is an unverified forum restatement.
- No quantitative study of "close X% below pivot" thresholds (e.g., 2%, 3%, 5%) vs subsequent performance.

## 4. Time stops for breakouts

### Takeaway
I found no rigorous or systematic evidence for a specific time stop on breakouts. The nearest quantitative anchors are Bulkowski's throwback/pullback timing (decline about 6 days, return to breakout in about 8-11 days) and the fact that 47% of cups drop substantially within two months. A time stop shorter than about 2 weeks would cut normal throwbacks.

### Cited Findings
- "Half the time it will take 8 days before the stock returns to the breakout price" (after a dip) — [thepatternsite Stops2](https://thepatternsite.com/Stops2.html).
- Pullbacks after downward breakouts (mirror case): price moves against the breakout for 6 days on average and completes the round trip in 11 days. The average excursion is 9% (most 4-10%). 58% of 8,765 patterns had pullbacks, and 47% of those resumed against the breakout — [thepatternsite pullbacks](https://thepatternsite.com/pullbacks.html). These are downward breakouts; earlier research has the upward (throwback) figures.
- 47% of cups "dropped substantially within two months of the breakout" — [thepatternsite cup](https://thepatternsite.com/cup.html).
- Minervini/IBD practitioners hold that a properly supported stock "should perform well after the breakout point"; if not, "the chart isn't as good as it appeared" — [lilys.ai notes on Minervini](https://lilys.ai/de/notes/notebooklm-20251211/mark-minervini-market-wizard) (anecdotal; AI-generated notes of interviews). No numeric day count was found.
- Lo & Remorov's 10-day cumulative-return stop (a hybrid of time and price) increased skewness and reduced max drawdown on US stocks — [CXO Advisory](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth) (rigorous, but not breakout-specific).

### Inferences
- A defensible candidate (to be tested, not evidence-backed): if the close is not at least X% (e.g., 3-5%) above entry after 15-20 trading days, exit or tighten to the handle low. The window should exceed the about 10-11 day throwback round trip.
- A time stop should be treated as a backtest parameter for the NSE system and swept (e.g., 10/15/20/30 days), not imported as a known rule.

### Gaps
- No Bulkowski "time stop" study and no IBD numeric rule (e.g., the "2-3 weeks" folklore) could be verified.
- No study of whether breakouts that fail to gain Y% in Z days underperform later.

## 5. Trailing the stop to breakeven

### Takeaway
The one systematic test found (Bulkowski, 2,333 double bottoms) shows that moving the stop to breakeven when price reaches halfway to target hurt results substantially. That matches the evidence that throwbacks are common and that tight stops remove winners. IBD folklore ("never let a >10% gain become a loss") is the opposing view, without data.

### Cited Findings
- **Bulkowski, "Adjusting Stops" (practitioner; 463 stocks, 2,333 double bottoms, bear markets excluded).** Benchmark stop a penny below the lowest valley vs. raising to breakeven at 50% of target. Winning trades 1,727 vs 1,042. Win/loss ratio 74% vs 45%. Net profit/share $2.17 vs $1.45. Total net $5,071 vs $3,372. Raising the stop to the pattern midpoint also underperformed. "Tests show that raising the stop hurts performance" — [thepatternsite QStopAdjust](https://www.thepatternsite.com/QStopAdjust.html).
- Contradicting practitioner rule (no data): IBD followers sell any stock up more than 10% before its profit disappears — [Motley Fool thread](https://discussion.fool.com/t/trading-ibd-stocks/104584) (anecdotal). Bulkowski's cup page says "Raise the stop as price rises" without specifying how — [thepatternsite cup](https://thepatternsite.com/cup.html).
- Tight trailing stops lose money vs buy-and-hold in Bulkowski's monthly-entry test (closer than 36%) — [thepatternsite CanStopsHurt](https://thepatternsite.com/CanStopsHurt.html). Snorrason & Yusupov: a 5% trailing stop was the worst performer — [quant-investing.com](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe).

### Inferences
- Default to not moving to breakeven early. If a ratchet is used, move the stop to a recent structural swing low or a wide volatility stop after a substantial advance (e.g., more than 15-20%, beyond the 23% of cups that stall at 15% or less). Test this rather than using a fixed +X% breakeven trigger.
- The double-bottom sample is not cups; transferability is plausible but unverified.

### Gaps
- No breakeven-stop study on cup-and-handle or IBD-style bases.

## 6. Gap-down risk and close-based vs intraday-low stop modeling

### Takeaway
Stops are slipped asymmetrically: gaps open beyond the stop in the losing direction, so a backtest that fills at the stop price understates the worst losses. For a system that only sees daily closes, the honest model is: signal on the close, fill at the next open (or the same close, if executing on the close), with the gap included. Lo & Remorov found that delayed execution (prior-day signal) did marginally better than immediate execution for tight stops, because of short-term reversal.

### Cited Findings
- Standard backtest convention: if price gaps through the stop between bars, the stop fills at the next bar's open, not the stop level — [arXiv 1412.5558, "Backtest of Trading Systems on Candle Charts"](https://arxiv.org/pdf/1412.5558); [AlgoTest blog](https://algotest.in/blog/backtests-sl-mismatch/) (practitioner, India-focused).
- "Stop-loss slippage is asymmetric — gaps tend to blow through the stop in the losing direction... a backtest that assumes exact stop fills systematically understates the size of the worst losses." Recommendation: rerun with added slippage, and "if a strategy only works with perfect fills, it does not work" — [MQL5 blog](https://www.mql5.com/en/blogs/post/775565) (practitioner/anecdotal).
- Lo & Remorov: execution using the prior-day signal worked marginally better than immediate execution, especially for tight stops, due to return reversion. Costs of 0.2% half-spread materially hurt tight stops — [CXO Advisory](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth) (rigorous).
- Bulkowski's Stops2 average losses (2.19%-7.53%) are measured to the stop price and ignore gaps — [thepatternsite Stops2](https://thepatternsite.com/Stops2.html). Real losses would be larger.

### Inferences
- For this system (daily closes only, enter at close): use **close-based triggers** (close < stop level), with the exit filled at that day's close if executable near the close, otherwise at the next day's open. This avoids intraday wicks, which matters given Bulkowski's high hit rates on tight lows, but it means realized losses will regularly exceed the planned stop distance.
- Intraday-low triggers (low < stop) assume information the system doesn't act on, and fills exactly at the stop ignore gaps. Both bias backtests optimistically on the loss side.
- NSE specifics to model: earnings/news gaps, circuit-limit days (a stock locked at lower circuit cannot be exited, so the exit should be deferred to the next tradable close), and STT/brokerage/impact costs. Report the distribution of realized loss divided by planned loss (the "R-multiple slippage"), and cap position size on planned risk times a gap multiplier.

### Gaps
- No rigorous study quantifying the average gap-through-stop slippage for breakout trades, either in the US or on NSE. This should be measured directly in the backtest.
- No source directly compares close-based vs intraday-low stop triggers on the same breakout sample.
