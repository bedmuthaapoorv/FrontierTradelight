# Cup-and-Handle Breakout Trade Management (entry, confirmation, stops, targets, failed breakouts)

Context: a daily-bar NSE system that enters at the signal day's close, and an existing horizontal-breakout exit (10-day failed-breakout check, 8% hard stop, 3.0x/4.0x ATR trails, 20%-in-15-days big-winner override, 90-day max hold). Source quality note: investors.com, williamoneil.com and marketsmithindia.com either blocked fetching or did not resolve from this environment. IBD-rule wording below therefore comes from search-result snippets and secondary sites (LuxAlgo, Fidelity, Motley Fool forum, MarketSmith India snippets) that restate IBD. Bulkowski figures were fetched directly from thepatternsite.com.

## 1. Buy point / pivot, buy zone, and earlier (cheat) entries

### Takeaway
The O'Neil/IBD pivot for a cup-with-handle is the handle's intraday high plus $0.10. The buy zone runs up to 5% above that pivot. Beyond 5% the stock counts as "extended" and is not bought. Minervini's "cheat" entries are earlier pivots inside the cup. Their position is set by where the pause forms: the lower third of the base is a "low cheat", the middle third a "cheat", and the upper third is the normal handle.

### Cited Findings
- Buy point = 10 cents above the handle's intraday high, provided breakout-day volume is at least 40% above the 50-day average — [search snippets citing IBD methodology, e.g. Nasdaq/IBD "Chart Reading Basics" article](https://www.nasdaq.com/articles/chart-reading-basics-how-find-correct-buy-point-leading-stocks-2017-10-02) (the page timed out on fetch, so this is from the snippet only)
- "Buying range up to 5% above the ideal pivot point"; more than 5% above the pivot counts as extended / beyond the proper buying range — [search summary of IBD-derived sources incl. TraderLion and MarketSmith India](https://www.traderlion.com/technical-analysis/the-cup-and-handle-pattern/) (403 on direct fetch)
- LuxAlgo, restating IBD, gives the buy point as "the handle's high plus a small margin". It says entry should fall in a small zone above the handle high: not inside the handle and not well past the pivot. The handle must form in the upper half of the base, drift down on "notably light volume", and last a week or more. Upward-sloping handles and handles deeper than about the low teens in percent should be avoided — [LuxAlgo: Cup-with-handle base](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- Bulkowski's identification rules: cup lasts 7 to 65 weeks; handle is at least 1 week with no maximum and forms in the upper half of the cup; the cup is U-shaped, not V-shaped. Handles shorter than the median of 22 days show better post-breakout performance — [Bulkowski, thepatternsite.com Cup with Handle](https://www.thepatternsite.com/cup.html)
- StockCharts: the handle can retrace up to 1/3 of the cup's advance and ideally finishes within 1 to 4 weeks. Ideal cup depth is a retracement of 1/3 or less of the prior advance, 1/3 to 1/2 is acceptable in volatile markets, and 2/3 is the maximum — [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Minervini's "cup completion cheat" (3-C) is a cup-with-handle variant in which the pause/handle forms in the lower or middle third of the base. He "would go in early" on a pivot that forms inside the base before a proper handle. Three pivot classes: low cheat (lower third), cheat (middle third), handle (upper third). The pattern must show VCP (volatility contraction) traits — [summary of IBD Live interview with Minervini, lilys.ai notes](https://lilys.ai/en/notes/notebooklm-20251211/minervini-favorite-chart-cheat) (secondary AI summary of a video; corroborated by [elibook.vn on 3-C](https://elibook.vn/2019/10/21/mau-hinh-3-c-cua-phu-thuy-mark-minervini-diem-mua-som-truoc-mau-hinh-chiec-coc-tay-cam/))

### Inferences
- For a close-based system on INR prices, "$0.10 above" has no direct equivalent. A small percentage (for example 0.1-0.5% above the handle high), or simply close > handle high, is the practical proxy.
- Because entry is at the signal-day close, a breakout day that closes more than 5% above the pivot should be rejected as extended, or at least flagged. Gap/thrust days can otherwise produce entries outside the O'Neil buy zone.
- A cheat entry sits closer to the cup low, which gives a lower entry price and a tighter natural stop (below the pause low). It also means buying before the stock has proven it can retake the old high, so it would need its own trigger definition: close above the high of a low-volatility pause in the lower or middle third of the cup.
- Entering on a break of the handle's downtrend line is an earlier variant that practitioners discuss. I found no primary source giving a precise definition (see Gaps).

### Gaps
- I could not fetch the primary investors.com article that states the exact "handle high + 10 cents" and "5% buy zone" wording. Both are consistently restated in snippets, but not quoted from a fetched IBD page.
- No sourced definition of a "handle downtrend-line" entry, and no performance data for it.
- I found no primary (book) quote for Minervini's cheat stop placement or exact depth thresholds.

## 2. Breakout volume confirmation, and close vs intraday

### Takeaway
IBD's long-standing rule of thumb is breakout-day volume at least 40-50% above the 50-day average. O'Neil Global Advisors' 2022 quant brief found that all breakouts produced alpha, but those with volume more than 150% above average (roughly 2.5x) did significantly better. That is evidence-based but is a performance gradient, not a validity cutoff. Bulkowski adds that high-volume breakouts throw back more often.

### Cited Findings
- On breakout day, volume should be at least 40%-50% above the stock's 50-day average, showing institutional buying — [search summary of IBD-derived sources](https://www.luxalgo.com/library/concept/cup-with-handle-base/); LuxAlgo: a valid breakout needs "volume around 40 to 50 percent above average" — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- O'Neil Global Advisors research brief "Breakouts: Pump up the Volume" (webinar on May 31, 2022): all breakouts from O'Neil patterns led to alpha, but breakouts with sharp volume increases significantly outperformed, and "volume rates in excess of 150%" were a key level — [William O'Neil + Co. PANARAY knowledge center (search snippet)](https://www.williamoneil.com/research-pages/panaray/tags/alerts) (the page did not resolve on fetch; the study covered breakouts from O'Neil base patterns generally, not cup-with-handle alone)
- StockCharts only requires a "substantial increase in volume on the breakout above the handle's resistance", with no numeric threshold — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Bulkowski: high-volume breakouts (above the 30-day average) throw back 70% of the time, against 58% for all upward breakouts — [Bulkowski, Throwbacks](https://ThePatternSite.com/throwbacks.html)

### Inferences
- "Volume rate 150%" in O'Neil/MarketSmith terms means 150% *above* average, which is 2.5x the 50-day average. A 40-50% threshold is 1.4-1.5x. A sensible design is to use 1.4x as the minimum validity filter and treat 2.5x or more as a quality score or priority ranking, rather than discarding everything below 2.5x.
- Close versus intraday: IBD alerts trigger intraday at the pivot. A daily-close system naturally needs close > pivot, which is stricter and avoids intraday fakeouts, but it may enter higher in the buy zone. Pair it with the 5% extension cap.
- Higher-volume breakouts throw back more often (Bulkowski), so a strict volume filter will not reduce throwback frequency. The failed-breakout logic must tolerate a normal throwback.

### Gaps
- I did not find the exact OGA outperformance numbers (alpha by volume bucket), the sample period, or whether cup-with-handle was broken out separately.
- No primary source states explicitly whether IBD requires a *close* above the pivot. IBD buy alerts are intraday-based.

## 3. Stop-loss conventions

### Takeaway
There are two dominant conventions. IBD/O'Neil uses a hard 7-8% stop below the buy price "regardless of chart structure". Bulkowski and general TA sources use the handle low as the structural stop. The handle low is pattern-specific: because about 58-62% of breakouts throw back, a stop just under the pivot is very likely to be hit even on a successful trade. Handle depth usually sits within single digits to low teens, so the two stops are often close together.

### Cited Findings
- IBD practice caps the loss at 7-8% below the buy point "regardless of chart structure", on the logic that correctly bought breakouts from sound bases should not fall that far — [LuxAlgo restating IBD](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- "The handle low (point C) is a good place to put a stop" — [Bulkowski, Cup with Handle](https://www.thepatternsite.com/cup.html)
- Chase: investors may consider a stop-loss order just below the handle — [Chase, Using a cup and handle pattern](https://www.chase.com/personal/investments/learning-and-insights/article/using-a-cup-and-handle-pattern)
- Cup-with-handle throwback rate is 62% — [Bulkowski](https://www.thepatternsite.com/cup.html). Across 10,305 upward breakouts since 2000 the rate is 58%, and the throwback peak averages 8% above the breakout (most fall in the 4-10% range) — [Bulkowski, Throwbacks](https://ThePatternSite.com/throwbacks.html)
- Handle depth: LuxAlgo/IBD-style guidance avoids handles deeper than about the low teens in percent — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/); StockCharts allows the handle to retrace up to 1/3 of the cup's advance — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)

### Inferences
- A recommended composite: stop = max(handle low × (1 − small buffer), entry × 0.92), which means using whichever stop is tighter. When the handle is shallow (for example 5%), the handle-low stop is tighter than 8%. When the handle is deep, the 8% cap governs.
- An alternative is to reject setups where the entry-to-handle-low distance is more than 8-10%, which limits the screener to tight-risk handles.
- Because entry is at the close and may be up to 5% above the pivot, the distance from entry to handle low can exceed handle depth by up to about 5 points. That is another reason to keep the 8% cap.
- ATR stops are not a pattern-specific convention in the sources found. They are a generic volatility alternative; the existing 3.0x/4.0x ATR trails can carry over as *trailing* stops.

### Gaps
- No source found that backtests handle-low stops against 7-8% stops for cup-with-handle specifically.
- I found no authoritative ATR-multiple convention tied to this pattern.

## 4. Profit-taking: 20-25% rule, 8-week hold rule, measured move, trailing

### Takeaway
IBD takes at least partial profits at a 20-25% gain. The exception is the 8-week hold rule: a gain of 20% or more within 3 weeks of breakout means holding at least 8 weeks unless a clear sell signal appears. Bulkowski's measured move (cup depth added to the breakout price) is reached 61% of the time. His average rise is 54%, but 23% of cups rise no more than 15% before dropping.

### Cited Findings
- Take at least some profits at a 20-25% gain from the buy point. O'Neil created the rule in 1961 after observing that breakouts from well-formed bases tend to run 20-25% before correcting — [search snippet of IBD "When To Take Profits In Stocks" via Yahoo Finance](https://hk.finance.yahoo.com/m/b4d8c322-9da9-3ad0-85c2-d97f2a8e897a/when-to-take-profits-in.html) (403 on fetch; snippet only)
- 8-week hold rule: if a stock gains 20% or more within three weeks of breaking out of a proper base, hold it for 8 weeks unless there is a clear sell signal. IBD research says many such stocks go on to double or triple. Pullbacks to or just below the 10-week moving average during that period are normal. After 8 weeks, reassess — [MarketSmith India "Use This Rule to Never Miss Big Profits" (snippet)](https://blog.marketsmithindia.com/use-rule-never-miss-big-profits/); [Motley Fool forum, IBD 8-week Hold Rule](https://discussion.fool.com/t/ibd-8-week-hold-rule/112549)
- Measured move: cup depth (right rim to bottom) added to the breakout — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle); [Fidelity](https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/cup-with-handle)
- Bulkowski (913 "perfect" trades): 61% meet the price target; average rise 54%; break-even failure rate 5%; performance rank 3 of 39 patterns — [Bulkowski](https://www.thepatternsite.com/cup.html)
- Bulkowski: "47% of the cup with handle patterns dropped substantially within two months of the breakout" and "almost a quarter (23%) ... see price rise no more than 15% before dropping" — [Bulkowski](https://www.thepatternsite.com/cup.html)
- A stock falling below its 50-day moving average is cited as an important sell signal in the IBD framework — [search snippet, Motley Fool "Trading IBD Stocks" thread](https://discussion.fool.com/t/trading-ibd-stocks/104584?page=17) (forum restating IBD; lower reliability)

### Inferences
- The existing "20% in 15 trading days" big-winner override maps almost exactly onto IBD's 20%-within-3-weeks trigger (3 weeks ≈ 15 NSE sessions). The natural change is to make it a hold floor: when it triggers, hold until about 40 trading days (8 weeks) from breakout, exiting early only on a catastrophic signal such as a close below the 50-DMA or below the pivot, not on ATR trail noise.
- If the 20-25% rule is used, a partial (for example 50%) exit at +20-25% with the remainder trailed fits IBD better than a full exit.
- The Bulkowski numbers (54% average rise, 61% target hit) are "perfect trade" figures, meaning bought at the breakout and sold at the ultimate high. They overstate what a mechanical exit captures. Treat the measured move as an optional target or partial-exit level, not a hard take-profit.
- Bulkowski's figure that 47% drop substantially within 2 months is an argument for some profit-protection mechanism (trail or 20-25% partial) rather than holding blindly to the 90-day maximum.
- Trailing with the 50-DMA / 10-week MA is the IBD-style trail for longer holds. The ATR trails already in place serve the same purpose. A 50-DMA close-break could be added as an alternative exit after the 8-week hold window.

### Gaps
- Unverified detail: whether IBD counts the breakout week as week 1 of the 8 weeks. Commonly stated, but not confirmed from a fetched primary page.
- I found no Bulkowski data on days to the ultimate high for cup-with-handle, which would calibrate the max-hold period.

## 5. Failed-breakout signals and normal throwback timing

### Takeaway
Throwbacks are the norm. Bulkowski's cup-with-handle throwback rate is 62% (58% across all patterns). A throwback takes about 10 days on average from breakout back to the breakout price, inside a 30-calendar-day window. After returning to the breakout price, 35% keep falling into or below the pattern. Trades that hold at or above the breakout price during the throwback average a 40% rise, against 29% for those that drop below it. A close back under the pivot is therefore informative but not conclusive. A close under the handle low is the structural failure.

### Cited Findings
- Throwback convention: occurs within 30 calendar days of breakout. 58% of 10,305 upward breakouts since 2000 threw back. The throwback peak comes about 6 days after breakout, and the full return to the breakout price takes about 10 days. After returning, 35% continue below the pattern and 65% recover. A subsequent rise averages 40% if price stays at or above the breakout price during the throwback, and 29% if it drops below — [Bulkowski, Throwbacks](https://ThePatternSite.com/throwbacks.html)
- Cup-with-handle-specific throwback rate is 62% — [Bulkowski](https://www.thepatternsite.com/cup.html)
- Forum restatement of IBD guidance: about 40% of breakouts come back to the buy point. A normal pullback usually happens within days, not weeks, of the breakout, with a gradual decline on weaker volume to or just below the buy point. A harsher decline warrants cutting the position — [Motley Fool "Trading IBD Stocks" thread (snippet)](https://discussion.fool.com/t/trading-ibd-stocks/104584?page=17) (low-reliability secondary source; the 40% figure conflicts with Bulkowski's 58-62%, possibly because definitions differ: "back to the buy point" versus a 30-day throwback window)
- Failure risk factors per IBD-style guidance: V-shaped cup, handle in the lower half, upward-wedging handle, excessive depth, weak breakout volume, wide weekly swings — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- Weak markets: many textbook cups fail in weak general markets, which O'Neil's method handles by gating buys on market direction — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)

### Inferences
- The existing 10-day failed-breakout check lines up with Bulkowski's 10-day average time to complete a throwback. A pattern-specific version could read: within about 10-15 trading days, *close below the handle low* means failed, exit. A close below the pivot alone should not trigger an exit, since that is a common throwback. Optionally, two or more consecutive closes below the pivot on rising volume could mean failed.
- A milder rule: if price has not closed at least X% above the pivot by day N and is back below the pivot, exit. This captures the "40% vs 29%" degradation without exiting on every intraday dip.
- Over the 30-calendar-day throwback window (about 20-21 NSE sessions), a close below the pivot carries more weight. Beyond that window, rely on the stop and trail.

### Gaps
- No Bulkowski cup-with-handle-specific days-to-throwback figure; the 10-day figure is from his all-pattern study.
- No source quantifies how often a close below the handle low after breakout precedes total failure for this pattern.

## 6. Market-condition filters and position sizing

### Takeaway
O'Neil's "M" rule says to buy breakouts only in a "confirmed uptrend", which IBD dates from a follow-through day. The stated reason is that roughly 3 of 4 stocks follow the general market. For OHLCV-only systems, index trend (for example Nifty above its 50/200-DMA) and breadth proxies are the usual stand-ins.

### Cited Findings
- During a "Market in Correction", about three of four stocks fall regardless of earnings. A follow-through day signals a "confirmed uptrend" in which buying base breakouts is appropriate. Follow-through days are best on day 4 or later of a rally attempt, on heavy-volume index gains — [Motley Fool IBD FTD discussion threads restating IBD](https://discussion.fool.com/t/ibd-follow-through-day-ftd/36704) (secondary)
- Many textbook cups fail in weak general markets, which is why the methodology gates buys on market direction — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- Acceptable cup depth widens in volatile markets (1/3 to 1/2, up to 2/3) — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)

### Inferences
- OHLCV-only proxies: Nifty 50/500 close above its 50-DMA and 50-DMA rising; percentage of universe stocks above their 50-DMA greater than some threshold; a computed follow-through day (index up 1.25%+ or so on volume above the prior day, on day 4 or later of a rally attempt). The FTD percentage threshold varies by source and is not cited here. The repo already has research notes on low market breadth that can be reused.
- Position sizing: with a stop at the handle low or 8% from entry, risk-based sizing (fixed % of equity / stop distance) naturally sizes up tight-handle setups.

### Gaps
- No primary-source FTD percentage threshold was retrieved.
- No evidence found quantifying the cup-with-handle success rate by market regime (Bulkowski has bull/bear splits in his book, but they were not on the fetched page).

## 7. What should differ from the generic horizontal-breakout exit

### Takeaway
Most of the existing exit transfers. The main changes are: (a) add a structural stop at the handle low, capped at 8%; (b) the failed-breakout check should key on a close below the handle low rather than below the breakout level, because 62% of cups throw back; (c) turn the big-winner override into an IBD 8-week (about 40-session) hold floor; (d) cups are longer bases (7-65 weeks), so the 90-day max hold is roughly the right order. It could be extended for 8-week-rule winners.

### Cited Findings
- Cup duration 7-65 weeks; handle at least 1 week; median handle 22 days; shorter handles perform better — [Bulkowski](https://www.thepatternsite.com/cup.html)
- Handle low as the stop — [Bulkowski](https://www.thepatternsite.com/cup.html); 7-8% IBD cap — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- 62% throwback rate; about 10 days to complete a throwback — [Bulkowski cup](https://www.thepatternsite.com/cup.html), [Bulkowski throwbacks](https://ThePatternSite.com/throwbacks.html)
- 8-week rule: 20%+ within 3 weeks means hold 8 weeks — [MarketSmith India](https://blog.marketsmithindia.com/use-rule-never-miss-big-profits/)

### Inferences
- Proposed paired exit (for a backtest to evaluate, not established doctrine):
  1. Initial stop: close below max(handle_low × 0.99, entry × 0.92).
  2. Failed breakout (days 1 to 15): close below the handle low, which is already covered by the stop. Optionally, a close below the pivot on day 10 or later while the max gain so far is under 5%.
  3. Big winner: if the gain is 20% or more within 15 sessions of entry, suppress the ATR trail exits until session 40. During that time exit only on the hard stop or a close below the 50-DMA.
  4. Otherwise: 3.0x/4.0x ATR trail as now. Optionally a partial exit at +20-25%.
  5. Max hold of 90 days, or up to about 120 for 8-week-rule winners.
- The entry screener should reject a close more than 5% above the pivot and require volume of at least 1.4x the 50-day average, with 2.5x or more as a priority flag.

### Gaps
- None of these hybrid rules has published cup-with-handle backtest evidence. They need validation on NSE data.
