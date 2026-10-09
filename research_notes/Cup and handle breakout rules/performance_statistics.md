# Cup-and-Handle Breakout Performance Statistics: Which Pattern Features Predict Success

Evidence-quality legend used throughout:
- **[RIGOROUS]** = large sample, documented methodology (e.g. OGA ~197k breakouts, survivorship-free universe).
- **[PRACTITIONER-SYSTEMATIC]** = large hand/semi-automated sample by a respected practitioner, methodology partly documented, not peer reviewed (Bulkowski).
- **[VENDOR/BLOG]** = non-peer-reviewed, methodology opaque or marketing-adjacent; treat as hypothesis only.
- **[UNVERIFIED]** = snippet/secondary only; primary not read in this session.

Almost all evidence is **US equities**. No Indian/NSE-specific quantitative study was found (see Q5).

---

## Q1. Bulkowski's headline statistics for cup-with-handle (bull market, up breakouts)

### Takeaway
Bulkowski ranks the cup-with-handle 3rd of 39 bull-market patterns: 5% break-even failure rate, 54% average rise, 61% hit the measured-move target, 62% throwback rate, on 913 "perfect trade" samples (US stocks). His newer 300-pattern trading study (1990–Mar 2024) is far less rosy: 47% retraced substantially within two months and 23% rose no more than 15% before declining.

### Cited Findings
- Bull market, up breakouts: overall performance rank **3 of 39**; break-even failure rate **5%**; average rise **54%**; throwback rate **62%**; percentage meeting price target **61%**; based on **913 "perfect trades"** [PRACTITIONER-SYSTEMATIC, US stocks; edition/period not stated on page] — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Cup with handle ranks **2 in failure rate** among bull-market up-breakout patterns — [Bulkowski, thepatternsite.com/cup.html (via search summary)](https://thepatternsite.com/cup.html)
- Bulkowski's identification envelope: cup duration **7 to 65 weeks**; handle **≥1 week, no maximum**, forming in the **upper half** of the cup; U-shape preferred to V; rims near the same price; prior uptrend into the cup is a guideline he says he does not "pay much attention to" — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Separate trading-oriented study of **300 patterns, 1990–March 2024**: **47%** experienced substantial retracements within two months post-breakout; **23%** rose no more than 15% before declining — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Bulkowski states "throwbacks hurt performance" (patterns that throw back to the breakout price subsequently rise less) — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Caution on the oft-quoted "95% success rate": it is the complement of the 5% *break-even* failure rate (price moved ≥5% beyond breakout), not a target-hit rate — [liberatedstocktrader.com](https://www.liberatedstocktrader.com/cup-and-handle-pattern/) [VENDOR/BLOG]; corroborated by the definition on [Bulkowski, Chart Pattern Failure page](https://thepatternsite.com/id84.html)

### Inferences
- The "average rise" metric in Bulkowski's encyclopedia is measured from breakout to the ultimate high before a 20% decline (his standard definition), with perfect hindsight exit; it is not a tradeable return. The 300-pattern trading study (47% big retracement within 2 months) is the more realistic baseline for a backtester with fixed exits.
- The 62% throwback rate means most breakouts return to the pivot; a screener/backtester using tight stops just below the pivot should expect frequent stop-outs on otherwise-successful patterns.

### Gaps
- Exact throwback timing (average days to throwback) and the sample period/edition behind the 913-trade table could not be retrieved (the PDF chapter copy was 403-blocked; the website page does not state them). Do not fill from memory.
- Bear-market statistics for cup-with-handle are not shown on the current web page.

---

## Q2. Bulkowski's feature-level findings (depth, length, handle, U/V, volume, gap, yearly range, tall/short)

### Takeaway
The only feature-level finding verifiable on Bulkowski's current site is that **short handles (shorter than the 22-day median) outperform**, and that throwbacks hurt. The detailed encyclopedia tables (tall vs short, yearly-range position, breakout volume, gaps, cup depth) could not be retrieved in this session.

### Cited Findings
- Handles shorter than the **median 22 days** show superior post-breakout performance — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Throwbacks are associated with worse performance — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Secondary (non-Bulkowski) vendor backtest on handle/cup features (10-day forward return; 10 years of data; method = structural detection + embedding similarity; market unspecified, presumably US): handle retracement **<10% of cup depth** best, **>30%** near-random; optimal handle duration **5–15 trading days**; cup depth **<15%: 52% win**, **15–30%: 57% win ("sweet spot")**, **30%+: 50% win** — [Chart Library blog](https://chartlibrary.io/blog/cup-and-handle-pattern-success-rate) [VENDOR/BLOG — opaque methodology, short horizon, self-promotional]
- Same vendor: patterns with all three volume traits (elevated volume forming cup, decline through base, breakout surge) **62% win, +3.8% avg** at 10 days vs **49%** win with flat/erratic volume; overall **56% win, +2.63% avg** at 10 days — [Chart Library blog](https://chartlibrary.io/blog/cup-and-handle-pattern-success-rate) [VENDOR/BLOG]

### Inferences
- Evidence-based thresholds available now: favor handle length ≤ ~22 trading days (Bulkowski) and modest handle retracement (vendor evidence weak). Cup depth evidence suggests a mild inverted-U (moderate depth best) but rests on a vendor blog — treat as a parameter to test, not a rule.
- Bulkowski's general cross-pattern findings (not verified here for cup-with-handle specifically) are that tall patterns and patterns breaking out near the yearly high tend to outperform; these should be tested in the user's own NSE backtest rather than assumed.

### Gaps
- Bulkowski encyclopedia tables for cup-with-handle by: cup depth, cup length, handle depth, U vs V, breakout volume heavy vs light, breakout gap, yearly-range third, tall vs short. Primary source (Encyclopedia of Chart Patterns, 2nd/3rd ed., chapter "Cup with Handle") not accessible; a copy at sponser.co.il returned 403. Recommend the user consult the book directly.

---

## Q3. O'Neil Global Advisors / IBD quantitative studies

### Takeaway
OGA's "Breakouts: Pump up the Volume" (May 4, 2022) is the most rigorous large-sample evidence: ~197,000 daily O'Neil-base breakouts in the US (1995–Sep 2021). All breakouts produced positive alpha (1.1% over 63 days), rising monotonically with breakout-day volume to 2.8% for volume ≥150% above the 50-day average. Crucially, the **hit rate is ~57% in every volume bucket** — higher volume increases the size of wins (and losses), not the probability of winning.

### Cited Findings
- Authors: Timothy Marble, Ronald P. Ognar CFA, Talin Mirzakhanian; dated **May 4, 2022** — [OGA, Breakouts: Pump up the Volume (PDF)](https://www.oneilglobaladvisors.com/documents/FG/oneil/research/617948_OGA_Breakouts-OGA.pdf) [RIGOROUS, US]
- Universe/method: US, **Jan 1995–Sep 2021**, survivorship-bias-free; excludes bottom 20% by price and bottom 50% by liquidity, penny stocks, ADRs, ETFs, corporate events; **~197,000 breakout events**; daily patterns only; bases pooled = cup, cup-with-handle, double bottom, flat base, ascending base, saucer, saucer-with-handle, IPO base; breakout = day's high exceeds pivot (for cup-with-handle, pivot = handle high); excess returns = CAPM alpha vs S&P 500 using a proprietary forward beta — [OGA PDF](https://www.oneilglobaladvisors.com/documents/FG/oneil/research/617948_OGA_Breakouts-OGA.pdf)
- Volume metric: breakout-day volume vs 50-day average volume; 0% = average, 150% = 2.5x average — [OGA PDF](https://www.oneilglobaladvisors.com/documents/FG/oneil/research/617948_OGA_Breakouts-OGA.pdf)
- All breakouts: **1.1% alpha, 3.2% return over 63 trading days**; volume ≥150%: **2.8% alpha, 5.0% return**; relationship monotonic; returns and alpha significant at 99% — [OGA PDF](https://www.oneilglobaladvisors.com/documents/FG/oneil/research/617948_OGA_Breakouts-OGA.pdf)
- Table 1 (63-day stats by volume bucket <50% / 50–100% / 100–150% / ≥150%), as extracted from the PDF (column alignment in text extraction was imperfect; row assignment below follows the row label order):
  - Cumulative log return: 2.61% / 3.01% / 3.12% / 5.04%
  - Cumulative alpha: 0.67% / 0.89% / 1.11% / 2.79%
  - Hit rate (% events with positive return): **57.68% / 56.85% / 57.10% / 56.86%**
  - Average gain: 12.91% / 14.97% / 15.89% / 19.90%
  - Average loss: -11.42% / -12.75% / -13.87% / -14.53%
  - Avg max favorable excursion: 11.11% / 12.50% / 13.34% / 15.65%
  - Avg max adverse excursion: -11.04% / -12.35% / -13.33% / -14.02%
  — [OGA PDF](https://www.oneilglobaladvisors.com/documents/FG/oneil/research/617948_OGA_Breakouts-OGA.pdf)
- The study pools all base types; the authors state they "hope to separate results by base type" in future — i.e. **no cup-with-handle-specific result** in this brief — [OGA PDF](https://www.oneilglobaladvisors.com/documents/FG/oneil/research/617948_OGA_Breakouts-OGA.pdf)
- Base stage: IBD-cited figures of **67% success for third-stage bases, dropping to 20% for fourth-stage bases**; first/second-stage bases "tend to produce larger gains" — no sample size/period/methodology given — [IBD via Dow Jones/itiger, Dec 10 2024](https://www.itiger.com/news/2490440090) [UNVERIFIED methodology — IBD marketing-educational content]
- Base counting convention: first base after a major low = stage 1; count increments when a new base forms ~20% above the prior one; undercutting a prior base low resets the count — [LuxAlgo O'Neil base analysis](https://www.luxalgo.com/library/concept/oneil-base-analysis/) [VENDOR/BLOG summary of IBD rules]

### Inferences
- For ranking: breakout-day volume ratio (vol / 50-day avg vol) is a defensible **magnitude** factor (expected alpha roughly 4x higher at ≥2.5x volume vs <1.5x), but it should **not** be used as a win-probability filter — hit rate is flat ~57%. Higher-volume breakouts also have larger average losses/MAE, so position sizing/stop logic should account for wider swings.
- The 57% baseline hit rate (63-day horizon, positive return) is a sensible prior for what an NSE implementation might achieve before costs; Bulkowski's "95%" is not comparable.
- 63-day alpha of 1.1–2.8% is modest; after Indian round-trip costs (STT, brokerage, impact, ~0.2–0.5% for liquid names) the low-volume buckets' edge could be largely consumed. (Cost estimate is an assumption, not sourced.)
- Base-stage effect is plausible and computable from daily data (count bases since last 52-week-low-type reset), but the cited numbers are not methodologically documented; validate in-sample before weighting.

### Gaps
- No OGA/IBD study isolating cup-with-handle vs other bases was found.
- No OGA study on market-direction (IBD "confirmed uptrend" vs "correction") effects on breakout returns was found in this session.

---

## Q4. Academic studies of cup-and-handle profitability

### Takeaway
Peer-reviewed evidence specifically on cup-and-handle is thin. The landmark Lo-Mamaysky-Wang (2000) study does **not** include cup-and-handle. The closest academic work is template-matching of related "bull flag" heuristics on the NYSE Composite (positive out-of-sample) and a probabilistic-neural-network study finding cup-and-handle profits significant more often for indices than for individual Dow stocks.

### Cited Findings
- Lo, Mamaysky & Wang (2000, J. Finance; NBER w7613) used kernel regression to detect patterns in US stocks 1962–1996 — head-and-shoulders, inverse H&S, broadening, triangle, rectangle, double tops/bottoms; cup-and-handle not among them; found patterns provide incremental distributional information but did not establish trading profits — [NBER w7613](https://www.nber.org/papers/w7613) [RIGOROUS; pattern list from my background knowledge of the paper, page not fetched this session]
- Leigh, Purvis, Ragusa / Leigh, Modani et al. (2002, Expert Systems with Applications; Economics Letters): "bull flag" template recognizer on NYSE Composite Index; out-of-sample trading rules effective, superior to random at 5-day horizon — [Datalearner record of ESWA paper](https://datalearner.com/academic/journal-papers/0957-4174/volumes-and-issues/84/paper-detail/78518); [UCF STARS record](https://stars.library.ucf.edu/facultybib2000/3311) [peer-reviewed, index-level, related pattern not cup-with-handle]
- "Empirical evaluation of price-based technical patterns using probabilistic neural networks" (Algorithmic Finance, IOS Press): cup-and-handle produced statistically significant profits more frequently for **indices than for individual assets**, and was more reliable for indices than Dow Jones components — [IOS Press abstract (via search snippet; full text 403)](https://content.iospress.com/articles/algorithmic-finance/af059) [peer-reviewed; UNVERIFIED details — sample, period, costs not read]
- An SVM-based cup-and-handle classifier paper exists (detection, not profitability) — [ResearchGate](https://www.researchgate.net/publication/379345807_Research_on_Cup_and_Handle_Price_Pattern_Based_on_Svm_Method) [low-impact]
- Open-source replication of MarketSmith cup-with-handle signals (2016–2018, SPY benchmark) — [GitHub HumanRupert/marketsmith_pattern_recognition](https://github.com/HumanRupert/marketsmith_pattern_recognition) [hobbyist, not peer reviewed; results not read]

### Inferences
- No rigorous, cost-adjusted, out-of-sample academic test of cup-and-handle on individual stocks was found. The OGA brief (pooled bases, gross of costs) is the best large-sample proxy.
- The general chart-pattern literature (e.g. Savin, Weller & Zvingelis 2007 on head-and-shoulders, which found conditional excess returns but small economic magnitude) suggests pattern edges are small and fragile; the user's backtester should report results net of costs and on held-out periods. (Savin et al. reference from background knowledge; not fetched.)

### Gaps
- Could not access full text of the IOS Press paper (authors, data, cost treatment unknown).
- No study found reporting cup-and-handle performance decay out of sample or after transaction costs specifically.

---

## Q5. Evidence specific to India (NSE/BSE) or emerging markets

### Takeaway
No quantitative study of cup-and-handle or base-breakout performance on Indian equities was found. Indian sources found are educational/marketing articles and TradingView idea posts with anecdotal examples.

### Cited Findings
- Search results for NSE cup-and-handle studies returned only TradingView ideas and broker educational content; claims such as "works particularly well in IT, Pharma, FMCG, Banking" are unsupported by data — [ICICIdirect article](https://www.icicidirect.com/futures-and-options/articles/understanding-charting-patterns-the-cup-and-handle); [StoxBox](https://stoxbox.in/financial-news-hotbox/cup-and-handle-pattern-guide/); [TradingView India ideas](https://in.tradingview.com/ideas/cupandhandle/) [VENDOR/BLOG, anecdotal]
- MarketSmith India (O'Neil's Indian affiliate) publishes base/breakout educational content but no quantitative breakout study was located — [MarketSmith India blog](https://blog.marketsmithindia.com/tag/fundamental-analysis-tool/)

### Inferences
- The user's own NSE backtest will be the primary evidence; US thresholds should be treated as priors. Structural differences (higher retail share, circuit limits, smaller liquid universe, higher frictions for small caps) may change volume-signal meaning — the OGA "institutional demand" rationale is US-centric.

### Gaps
- No peer-reviewed or large-sample emerging-market study on cup-with-handle found.

---

## Q6. Dependence on market regime (bull vs bear, breadth)

### Takeaway
Bulkowski's headline cup-with-handle figures are explicitly bull-market numbers; regime-conditional evidence for this pattern specifically is limited to a vendor blog showing win rate falling from ~59% (SPY above 50-day MA) to ~47% (market downtrend). No rigorous breadth-conditioned study was found.

### Cited Findings
- Bulkowski's statistics table is labeled "Important Bull Market Results"; bear-market results are not shown on the page — [Bulkowski, thepatternsite.com/cup.html](http://thepatternsite.com/cup.html)
- Vendor backtest: **SPY above 50-day MA: 59% win**; **broader market downtrend: 47% win** (10-day horizon); technology/healthcare outperform utilities/staples — [Chart Library blog](https://chartlibrary.io/blog/cup-and-handle-pattern-success-rate) [VENDOR/BLOG]
- Cup depths up to ~50% are said to appear in bear markets/severe corrections vs 12–33% normally (O'Neil convention, not a performance statistic) — [AlphaEx Capital](https://www.alphaexcapital.com/stocks/technical-analysis-for-stock-trading/price-action-and-chart-patterns/cup-and-handle-pattern-explained) [VENDOR/BLOG]

### Inferences
- A market-regime gate (index above its 50-day MA, or breadth above a threshold) is the cheapest likely improvement; expected effect size (from weak evidence) is ~10 percentage points of win rate. Test using the available breadth series, e.g. bucket breakouts by breadth quintile.
- Because the OGA study reports positive average alpha across all regimes pooled, a hard regime filter may cut sample size more than it improves expectancy; prefer a ranking weight, then compare to a hard gate in backtest.

### Gaps
- No rigorous (large-sample, documented) study of base-breakout returns conditioned on market breadth or IBD market-direction status was found.
- No data on sector-rank conditioning from a rigorous source.
