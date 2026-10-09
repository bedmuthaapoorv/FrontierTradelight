# Cup-and-Handle Pattern Geometry: Canonical Numeric Specs for a Daily-OHLCV Screener

Scope note: investors.com (IBD) blocks automated fetching, as do the IBD reprints on Yahoo Finance, pdfcoffee and the sponser.co.il PDF (all returned 403). The MarketSmith India blog did not resolve. So the O'Neil/IBD numbers below come from secondary sources that summarise IBD material (LuxAlgo, AAII, Amphibian Trading, search-result excerpts of IBD articles). Where a number comes only from a search-engine summary and not from a page I fetched, it is marked **[search-summary only]**. The Bulkowski and StockCharts numbers come from the primary pages, which I fetched. Conversion used throughout: 1 week = 5 NSE trading days.

## 1. O'Neil / IBD canonical spec

### Takeaway
O'Neil's core numbers are consistent across secondary sources: a prior advance of at least 30%, a base of at least 7 weeks, cup depth of 12-33% (up to roughly 40-50% in bear markets), a U-shaped bottom, and a handle of at least 1 week. The handle should drift down on light volume, sit in the upper half of the base and above the 10-week MA, and stay shallow (about 10-12%, flawed beyond the low teens). The pivot is the handle high plus 10 cents, and breakout volume should be at least 40-50% above average. The 65-week upper bound on cup length is Bulkowski's figure (section 2). Some secondary sources credit it to O'Neil, but I could not confirm that against an O'Neil text.

### Cited Findings
- Prior uptrend: "a gain of about 30 percent or more before the base begins." — [LuxAlgo, Cup-with-Handle Base](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Prior uptrend: "prices should have advanced at least 30% from the last intermediate low." The same source cautions that a more mature, larger prior trend gives "less chance that the pattern marks a continuation." — [AAII, Wayne A. Thorp, Dec 2015](https://www.aaii.com/journal/article/the-cup-with-handle-pattern)
- Prior uptrend "at least 30%" and minimum cup length "7 weeks", attributed to O'Neil. — [Amphibian Trading](https://amphibiantrading.substack.com/p/the-cup-with-handle)
- Base duration: "generally spans at least about seven weeks", with the handle lasting "a week or more". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Cup depth: "12 to 33 percent from the left-side high in normal market conditions" and "deeper in bear markets". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Cup depth: in bear markets, "deeper cups, up to 40-50%, can be forgiven only when they form during severe bear-market corrections." **[search-summary only]** — [Charting with KR substack](https://chartingwithkr.substack.com/p/technical-analysis-guide-p3-the-cup)
- Conflicting depth figure: Amphibian Trading gives "20% - 35%, can be as deep as 50% in severe bear markets". The 12-33% range is the more widely cited O'Neil figure. — [Amphibian Trading](https://amphibiantrading.substack.com/p/the-cup-with-handle)
- For IBD cup-type bases generally, the correction "generally shouldn't be more than 40% to 50% from peak to trough." **[search-summary only, attributed to an IBD double-bottom article]** — [Yahoo/IBD, double bottoms](https://finance.yahoo.com/news/watch-top-stocks-forming-double-213000510.html)
- Handle position: "in the upper half of the base". Handle depth: "retracing only modestly", with handles "deeper than roughly the low teens in percent" treated as flawed. Handle volume: "drifting downward on contracting volume". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- One summary, attributed to O'Neil, gives these handle figures: depth 10%-12%, formed in the upper half of the base, and the handle peak "within 15% of old high on left side of cup". It also describes the handle as a pullback "usually 8–15% or less" lasting "1–4 weeks". **[search-summary only; the second-hand sources mix these numbers]** — [Charting with KR](https://chartingwithkr.substack.com/p/technical-analysis-guide-p3-the-cup); [pro.stockalarm.io](https://pro.stockalarm.io/blog/cup-and-handle-pattern)
- A handle "should also form above the stock's 10-WMA," and breakouts from handles below the 10-week line are failure-prone, like handles below the base midpoint. **[search-summary only, wording consistent with IBD columns]** — [LuxAlgo cup-with-handle-base](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- Handle midpoint rule: "Midpoint of handle is greater than midpoint of base." — [Amphibian Trading](https://amphibiantrading.substack.com/p/the-cup-with-handle)
- Pivot/buy point: "the handle's high plus a small margin". O'Neil used 10 cents. — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md); 10-cent figure **[search-summary only]** via [Nasdaq/IBD chart-reading basics, 2017](https://www.nasdaq.com/articles/chart-reading-basics-how-find-correct-buy-point-leading-stocks-2017-10-02) (the fetch timed out)
- Breakout volume: "around 40 to 50 percent above average". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Stop: "7 to 8 percent below the purchase price". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Volume and quality cues in the base: "big volume on up days and weeks, and overwhelming volume on the breakout", plus "tight closes in the base, a symmetrical shape". — [Amphibian Trading](https://amphibiantrading.substack.com/p/the-cup-with-handle)

### Inferences
- Conversions to trading days: a 7-week minimum base is about 35 days. A 1-week minimum handle is about 5 days. A 1-4 week handle is about 5-20 days. The 10-week MA is roughly the 50-day SMA (a common practitioner equivalence; daily bars allow either a true weekly 10-period MA or a 50-day SMA).
- Handle depth limits come in two forms. One is about 10-12% in normal markets, with anything beyond the low teens being flawed. The other is structural: the handle low must be above the base midpoint, (left high + cup low)/2. Both are computable, and the screener should apply both.
- "Handle high plus 10 cents" is a fixed US-dollar increment. For NSE, a percentage buffer (for example 0.1% above the handle high) or one or two price ticks are reasonable proxies. This is my design suggestion, not a sourced rule.
- A 7-8% stop and a handle depth capped near 10-12% fit together: a buy at the pivot with a stop below the handle low keeps risk within O'Neil's loss limit.

### Gaps
- I could not retrieve O'Neil's own book text or any investors.com page, so the exact wording from *How to Make Money in Stocks* (for example the handle-depth sentence and the bear-market depth limit) is unverified at primary level.
- No source I fetched states an O'Neil maximum cup length. "65 weeks" is Bulkowski's guideline (section 2). Treating it as O'Neil's is unconfirmed.
- I found no numeric definition of "light volume" in the handle, for example handle average volume below the 50-day average volume.
- CAN SLIM inputs (EPS and sales growth, institutional sponsorship, IBD Relative Strength vs. all stocks) are **not computable** from OHLCV. Practitioners proxy RS with the stock's own trailing price performance ranked against the universe, often over 6-12 months. The exact IBD RS weighting was not verified in this research. The available sector-rank value is a partial proxy for O'Neil's "leading industry group" requirement.

## 2. Bulkowski's identification guidelines (thepatternsite.com)

### Takeaway
Bulkowski is deliberately looser than O'Neil. He sets no cup-depth rule, no handle-depth number and no prior-uptrend requirement ("I don't pay much attention"). His hard criteria are: a U-shaped cup lasting 7-65 weeks, a handle of at least 1 week (no maximum) in the upper half of the cup, and roughly equal rims. He reports better performance for handles shorter than the 22-day median.

### Cited Findings
- Price trend: "Price rises into the start of the cup, but I don't pay much attention to this guideline." — [Bulkowski, thepatternsite.com/cup.html](https://thepatternsite.com/cup.html)
- Shape: "The cup should be U-shaped, not V-shaped, but allow variations." — [Bulkowski](https://thepatternsite.com/cup.html)
- Handle required: "The cup must have a handle on the right." — [Bulkowski](https://thepatternsite.com/cup.html)
- Cup duration: "From 7 to 65 weeks (allow variations)." — [Bulkowski](https://thepatternsite.com/cup.html)
- Handle: "1 week minimum with no maximum, forming in the upper half of the cup." — [Bulkowski](https://thepatternsite.com/cup.html)
- Rims: "Cup rims should be near the same price level but be flexible." — [Bulkowski](https://thepatternsite.com/cup.html)
- Handles shorter than the median of 22 days show better post-breakout performance. — [Bulkowski](https://thepatternsite.com/cup.html)
- Statistics (913 trades): rank 3 of 39 patterns, break-even failure rate 5%, average rise 54%, throwback rate 62%, price target met 61% of the time. — [Bulkowski](https://thepatternsite.com/cup.html)
- The page I fetched gives no numeric value for cup depth, handle retrace percentage, handle slope, rim-height difference or volume trend. — [Bulkowski](https://thepatternsite.com/cup.html)

### Inferences
- In trading days: the cup lasts 35-325 days, the handle at least 5 days, and the 22-day median handle is about 4.5 weeks. Bulkowski's finding suggests capping the handle at about 22 days as a quality filter.
- Differences from O'Neil: Bulkowski has no 30% prior-uptrend requirement, no depth bounds, no 10-week MA rule, no handle-depth cap and no volume rule. He shares the U-shape and upper-half-handle rules.

### Gaps
- Bulkowski's *Encyclopedia of Chart Patterns* has detailed tables (performance by cup depth, by handle retrace, and by rim-height difference). They were not available online, so I have no numeric rim tolerance from him.
- Search-result claims that Bulkowski says handles should retrace "no more than 12-15%" came from aggregators (LuxAlgo blog, TradingView posts) and are unverified. Do not attribute them to him.

## 3. Cross-check definitions (StockCharts ChartSchool, AAII)

### Takeaway
StockCharts and AAII define depth as a fraction of the prior advance, not as a percentage off the high. Ideal depth is no more than 1/3 of the prior advance, 1/3-1/2 in volatile markets, and at most 2/3 in extreme cases. The handle retraces at most 1/3 of the cup's advance, within the upper half or third of the cup, over 1-4 weeks. This is a different measurement convention from O'Neil's 12-33% off the high.

### Cited Findings
- Prior trend: "a few months old". Overly mature trends have less upside. — [StockCharts ChartSchool](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Cup duration: "can last from one to six months, sometimes longer on weekly charts". — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Depth: "Ideally, the depth of the cup should retrace 1/3 or less of the previous advance. However, the retracement could range from 1/3 to 1/2 with volatile markets and over-reactions. In extreme situations, the maximum retracement could be 2/3." — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Rims: "The perfect pattern would have equal highs on both sides, but this is not always the case." — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Handle: "can last from one week to many weeks and is ideally completed within one to four weeks". It "can retrace up to 1/3 of the cup's advance, but usually not more". — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- Target: the distance from the right peak of the cup to the bottom of the cup, projected upward from the breakout. — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- AAII adds that the handle should fall only into "the upper half or third of the cup". Warning signs: a V-shaped cup, a retreat exceeding "50% from the high of the left side", a handle in "the lower half", and no volume confirmation. — [AAII](https://www.aaii.com/journal/article/the-cup-with-handle-pattern)

### Inferences
- In trading days: a 1-6 month cup is about 21-126 days, and a 1-4 week handle is about 5-20 days.
- The 50%-from-left-high hard cap (AAII) fits as an outer bound with O'Neil's 33% normal and roughly 40-50% bear-market depth.

### Gaps
- None material beyond those noted.

## 4. Variations: cup without handle, high handle, lower-half handle, double bottom with handle, cheat entries

### Takeaway
A cup without a handle is a valid IBD pattern, bought at the left-side high plus 10 cents. A double bottom (with or without a handle) is valid, bought at the middle peak of the W, or at the handle high if a handle exists. A handle in the lower half of the base is a flaw in O'Neil's framework. Minervini's "cup completion cheat" (3C) and "low cheat" deliberately enter on a pause in the lower or middle third of the cup, before the classic handle. They are early, higher-risk entries, not faulty bases.

### Cited Findings
- Cup without handle: the buy point is "10 cents above the peak in the left side of the pattern." **[search-summary only, IBD article]** — [Yahoo/IBD, "Cup Patterns Without Handles Can Still Go On To Be Winners"](https://finance.yahoo.com/news/cup-patterns-without-handles-still-182000010.html)
- Cups without handles use the left-side high as the pivot. — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Double bottom: the buy point is 10 cents above the middle peak of the W, unless a handle forms, in which case it is 10 cents above the handle high. **[search-summary only, IBD]** — [Yahoo/IBD double-bottom early buy point](https://finance.yahoo.com/news/spot-early-buy-point-double-195200041.html)
- Cup completion cheat: a cup-with-handle variant where the entry handle forms "in the lower or middle one-third of the base", often called a "low cheat". 3C is "the earliest possible time you can take a position". Visually it is like a cup with two handles. **[search-summary only]** — [lilys.ai notes on Minervini/IBD Live](https://lilys.ai/en/notes/notebooklm-20251211/minervini-favorite-chart-cheat); [Glasp, IBD Live video](https://glasp.co/youtube/p/mark-minervini-s-favorite-chart-setup-the-cheat-ibd-live)
- VCP: successive contractions shrink, for example about 20% then 10% then 5%, or 18% then 12% then 6%, typically over 2-4 contractions. The final contraction is often 3-5% or less on a daily chart. Volume dries up during the pullbacks, and the pivot is the high of the final tight area. **[secondary, not Minervini's own text]** — [Finer Market Points](https://www.finermarketpoints.com/post/vcp-criteria-complete-checklist); [TraderLion](https://traderlion.com/technical-analysis/volatility-contraction-pattern/)

### Inferences
- How the variants differ numerically:
  - **Classic handle:** handle low above the base midpoint, typically in the upper third. Handle high within about 15% of the left high (one secondary source).
  - **Cheat or low cheat:** a pause or tight area whose high sits in the lower or middle third of the cup range. The entry is the high of that pause, well below the left high.
  - **Cup without handle:** the price recovers to the left high with no pullback of at least 5 days. The pivot is the left high.
  - **Double bottom:** two lows separated by a middle peak. Practitioners usually want the second low to undercut the first slightly, which is unverified here.
- "High handle" (a handle forming close to the left high, with the cup largely complete) was not found in the sources I could access with a numeric definition. See Gaps.

### Gaps
- No numeric definition of "high handle" was retrieved. I could not confirm IBD's minimum length for a high-handle setup or its required prior run-up.
- Minervini's exact numeric definitions from *Trade Like a Stock Market Wizard* (for example the cheat's position as a fraction of base depth, or tightness thresholds) were not available from primary text. The secondary numbers above are illustrative, not rules.
- I did not verify whether a double bottom requires the second low to undercut the first, or by how much.

## 5. Faulty-base characteristics

### Takeaway
IBD and O'Neil flag the following as faulty or failure-prone:
- a handle in the lower half of the base, or below the 10-week MA
- a wedging handle, where lows drift up instead of down, often on light volume
- a V-shaped cup with no time at the bottom
- excessive depth for the market environment
- a base shorter than the minimum length
- a late-stage base (3rd or 4th base in an advance)
- a breakout on weak volume

### Cited Findings
- "Stocks with wedging handles have a higher failure rate and often are seen in late-stage bases, the bases of laggard stocks or the bases of very active leaders that have become too widely followed." **[search-summary only, attributed to IBD "A Faulty Handle Spells Trouble; Is It Too Low? Does It Wedge Up?"]** — [Yahoo/IBD](https://finance.yahoo.com/news/faulty-handle-spells-trouble-too-195200814.html) (direct fetch returned 403)
- A handle that cannot form in the upper half shows weakness. Handles that sag into the lower half, or that wedge steeply upward instead of drifting, are flaws. **[search-summary only]** — [Yahoo/IBD](https://finance.yahoo.com/news/faulty-handle-spells-trouble-too-195200814.html); [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)
- Listed defects: "V-shaped lows, handles in the lower half, upward-wedging handles, excessive depth relative to market conditions, and breakouts on weak volume". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Base count: the first or second cup-with-handle in a new uptrend has the best odds. By the third and especially the fourth base, failure rates climb sharply. **[search-summary only]** — [TraderLion](https://traderlion.com/technical-analysis/cup-and-handle-pattern/); [New Trader U](https://www.newtraderu.com/2021/03/29/cup-and-handle-pattern/)
- Handles below the 10-week line are failure-prone. **[search-summary only]** — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base/)

### Inferences (OHLCV operationalisation, my design, not sourced rules)
- **Wedging handle:** over the handle window, the regression slope of daily lows (or of the sequence of handle swing lows) is greater than 0. Equivalently, the handle low is made in its first half and later lows are higher, with the handle high not exceeding the left rim. A valid handle should show flat-to-down highs and lows.
- **V-shape test:** require a minimum number of days with closes within the lower 1/4 or 1/3 of the cup range (for example at least 10-15% of the cup's duration). Alternatively, require that the decline leg and the recovery leg each take at least about 3 weeks (15 days). No canonical number was found.
- **Base count:** this is computable from OHLCV. Count prior bases (consolidations of at least 5-7 weeks and at least 8-12% deep) since the last major low, where a "reset" is a base that undercuts the prior base's low. IBD's base-count reset rule was not verified in this research.
- **Weak-volume breakout:** volume on the breakout day must be at least 1.4-1.5x its 50-day average (from the 40-50% figure).

### Gaps
- No quantitative threshold for "V-shaped" exists in the sources I reached.
- IBD's exact base-counting and reset rules were not retrieved.

## 6. Rim alignment

### Takeaway
No source I reached gives a firm numeric tolerance. Bulkowski says rims should be "near the same price level but be flexible". StockCharts and AAII say equal highs are ideal but not required. One secondary O'Neil summary says the handle peak should be within 15% of the left-side high.

### Cited Findings
- "Cup rims should be near the same price level but be flexible." — [Bulkowski](https://thepatternsite.com/cup.html)
- "The perfect pattern would have equal highs on both sides, but this is not always the case." — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- AAII: ideally "roughly equal high prices on both sides of the cup". — [AAII](https://www.aaii.com/journal/article/the-cup-with-handle-pattern)
- Handle peak "within 15% of old high on left side of cup" (attributed to O'Neil). **[search-summary only]** — [Charting with KR](https://chartingwithkr.substack.com/p/technical-analysis-guide-p3-the-cup)

### Inferences
- A practical screener rule: right rim (handle high) between about 85% and 102-105% of the left-rim high. The lower bound is the 15% figure above. A right rim well above the left rim means the stock has already broken out, which makes the pattern invalid or a different setup.
- Common practice in IBD charting (unverified here) prefers the handle high to be within about 5-10% of the left high, so that the breakout clears overhead supply. If the handle high is far below the left high, the pivot is far from the old high and the stock must work through supply between them.

### Gaps
- Bulkowski's book tables on rim-height difference were not accessible, and no authoritative numeric tolerance was found.

## 7. Volume characteristics (cup, handle, breakout)

### Takeaway
Volume should contract as the cup bottoms, increase on up days in the right side, dry up in the handle, and expand at least 40-50% above average on the breakout. Only the breakout figure has a documented number.

### Cited Findings
- Handle drifts down "on contracting volume". Breakout volume "around 40 to 50 percent above average". — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- "big volume on up days and weeks, and overwhelming volume on the breakout". — [Amphibian Trading](https://amphibiantrading.substack.com/p/the-cup-with-handle)
- "There should be a substantial increase in volume on the breakout above the handle's resistance." — [StockCharts](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/chart-patterns/cup-with-handle)
- VCP literature: volume contracts with price, with a clear dry-up near the end. — [Finer Market Points](https://www.finermarketpoints.com/post/vcp-criteria-complete-checklist)

### Inferences (OHLCV proxies, my design)
- **Cup bottom dry-up:** average volume over the days around the cup low (for example plus or minus 5-10 days) is below the 50-day average volume measured at the left rim.
- **Right-side accumulation:** within the right side, up-day volume is greater than down-day volume (an up/down volume ratio above 1). This is a common practitioner metric, not verified as an IBD numeric rule.
- **Handle dry-up:** the handle's average volume is below the 50-day average volume (for example under 1.0x, with stronger setups under about 0.7-0.8x). There is no canonical number.
- **Breakout:** the close is above the pivot and volume is at least 1.4x the 50-day average.

### Gaps
- No source gave numeric thresholds for cup-bottom or handle volume dry-up.

## 8. Data feasibility: trading-day equivalents and the 400-day history limit

### Takeaway
The longest cups (65 weeks, about 325 days) plus a 30% prior-uptrend check plus warm-up for the 50-day MA do not fit within about 400 days. Practical coverage is cups up to about 40-50 weeks (200-250 days), which covers the large majority of the O'Neil range.

### Cited Findings
- Cup duration 7-65 weeks (Bulkowski). — [Bulkowski](https://thepatternsite.com/cup.html)
- Minimum base about 7 weeks (O'Neil per secondary sources). — [LuxAlgo](https://www.luxalgo.com/library/concept/cup-with-handle-base.md)
- Prior uptrend at least 30% from the last intermediate low. — [AAII](https://www.aaii.com/journal/article/the-cup-with-handle-pattern)

### Inferences
| Parameter | Weekly spec | Trading days |
|---|---|---|
| Minimum base/cup | 7 wk | ~35 |
| Maximum cup (Bulkowski) | 65 wk | ~325 |
| Handle minimum | 1 wk | ~5 |
| Handle ideal range | 1-4 wk | ~5-20 |
| Bulkowski median handle | 22 days | 22 |
| 10-week MA | 10 wk | ~50-day SMA |
| StockCharts cup range | 1-6 months | ~21-126 |

- Budget for a 400-day history: the 30% prior uptrend usually needs about 40-120+ days before the left rim, and the 50-day MA needs 50 days of warm-up. Cup plus handle can therefore be at most about 230-310 days. A practical cap is a cup of about 250 days (50 weeks). Longer cups should be flagged "unverifiable prior trend" rather than silently accepted.
- Market regime: O'Neil allows deeper cups in bear markets. With no index data, the breadth value (% of the universe above its 50-day MA) can switch the depth cap, for example 33% normally and up to 40-50% when the base formed during low breadth. The breadth thresholds are a design choice, not sourced.

### Gaps
- No source I found addresses applying these specs to NSE stocks specifically, or to markets with different volatility (for example whether Indian small caps need wider depth bands).
