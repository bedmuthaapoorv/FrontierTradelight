# Price-Based Risk Exits for Long-Horizon Value / Quality / GARP Stock Portfolios

Context: the user's Nifty 500 GARP strategy holds the top 25 names for about 6 months (rebalances on 15 Jun and 15 Dec). The only other exit is a catastrophic stop at close <= 0.75 x entry. That stop fired 36 times in 246 trades (14.6%) over 2021-2026. Any v2 rule must use only the entry price and date plus the stock's own daily OHLCV.

Note on evidence quality: almost no published study tests stops *inside a value/quality/GARP portfolio specifically*. Most evidence is on (a) random-entry individual stocks, (b) momentum portfolios, or (c) indices or futures (asset-class level). Each finding below says which of these it covers.

## 1. Fixed vs trailing stop-losses: what the academic studies find, and do stops hurt mean-reverting value strategies?

### Takeaway
On individual stocks, stop-losses do not reliably raise returns. At best they cut volatility, drawdown and left-tail risk, and trailing stops do this better than fixed stops. Stops add return only when returns have momentum (positive serial correlation), so they help momentum strategies most. Theory says they hurt in a random-walk or mean-reverting setting, which is the risk for a value/GARP book that buys temporarily depressed stocks.

### Cited Findings
- **Kaminski & Lo, "When do stop-loss rules stop losses?"** (J. Financial Markets 2014, 18:234-254). Under a random walk, a simple 0/1 stop-loss rule always lowers expected return. When prices have momentum, stop-loss rules can add value. The published version uses daily *index futures* (asset-class level, not single stocks) and finds that at longer sampling frequencies some stop policies raise expected return and substantially reduce volatility. — [MIT DSpace](https://dspace.mit.edu/handle/1721.1/114876); [PDF](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf)
- The 2008 working-paper version used monthly US equity *market* data from 1950-2004, switching to long-term Treasuries on a stop. It found certain stop rules add 50-100 bp per month during stop-out periods, explained by "flight-to-quality" regime switching. This is index level, not individual stocks. — [Kaminski & Lo summary via search of MIT/SIFR records](https://swopec.hhs.se/sifrwp/abs/sifrwp0063.htm); [quant-investing.com summary](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe)
- **Lo & Remorov, "Stop-loss strategies with serial correlation, regime switching, and transaction costs"** (J. Financial Markets 2017, 34:1-15) is the most relevant study for individual stocks. It covers US common stocks with daily data from 1964 to 2014 and a 0.2% half-spread cost. Tight stops (daily -0% to -6%) "generally underperform buy-and-hold in a mean-variance framework due to excessive trading costs". Outperformance is possible only for stocks with high serial correlation. Wide stops on 10-day returns (0% to -14%) gave lower raw returns, roughly matched buy-and-hold risk-adjusted, and consistently raised skewness and cut maximum drawdown. Autocorrelation of individual stocks was positive in the first half of the sample and significantly *negative* in the second half. The authors conclude that recent individual-stock behaviour "is not conducive to use of tight stop-losses". Selling at the next day's close rather than the signal close was marginally better, and much better for tight stops, because prices revert during the delay. — [CXO Advisory summary](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth); [MIT DSpace](https://dspace.mit.edu/handle/1721.1/107017)
- **Lei & Li, "The value of stop loss strategies"** (Financial Services Review 2009, 18(1)) tested NYSE/AMEX stocks from 1970 to 2005 with random buy dates. Holding periods were 3, 6 and 12 months, the same order as the GARP 6-month hold. Stops were set at 5, 10 and 20 daily standard deviations, fixed or trailing. Over the full sample, neither fixed nor trailing stops differed statistically from buy-and-hold on returns. Trailing stops reduced the standard deviation of returns. Fixed stops reduced risk only in the 1970s and 1990s, and helped returns in some subperiods and for high-volatility stocks, but that predictability faded over time. In simulations, neither type changed returns whether daily returns were i.i.d., autocorrelated or trending. — [Journal abstract](https://openjournals.libs.uga.edu/fsr/article/view/4933); [CXO summary](https://www.cxoadvisory.com/technical-trading/using-trailing-stop-losses-to-reduce-risk)
- A similar Taiwan-market study found that stop-losses "neither reduce the losses nor increase the return" but significantly reduce risk. — [NTU record](https://scholars.lib.ntu.edu.tw/entities/publication/96b82085-4c76-4de3-b8d4-33812f98bdb8)
- **Han, Zhou (& Zhu), "Taming momentum crashes: a simple stop-loss strategy"** studied US NYSE/AMEX/NASDAQ stocks from 1926 to 2011. The strategy is long-short decile momentum on 6-month returns, rebalanced monthly, with a 10% stop per stock and cash until month-end. The worst equal-weighted monthly loss fell from -49.79% to -11.34%. Mean monthly return rose from 1.01% to 1.73%, and the Sharpe ratio from 0.166 to 0.371. Gross of costs, it needs daily monitoring, and the positions are *momentum* (trending) stocks, not value stocks. Summaries differ slightly on the exact figures. — [Alpha Architect](https://alphaarchitect.com/2016/08/taming-the-momentum-roller-coaster-fact-or-fiction/); [quant-investing.com table](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe)
- **Snorrason & Yusupov (2009, Lund)** tested OMX Stockholm 30 stocks from 1998 to Apr 2009 with quarterly entries and cash until the next quarter after a stop. Buy-and-hold cumulative return was 1.29% (0.80% mean per quarter, variance 1.54%). A 15% trailing stop returned 73.9% cumulative and a 20% trailing stop 63.6% (1.71% per quarter). The best traditional (fixed-from-entry) stop was 10-15%, at 57.1% and 53.3%. A 5% trailing stop underperformed buy-and-hold. Stops of 25-55% added progressively less, converging toward buy-and-hold. Caveats: 30 large-cap stocks and one period dominated by two crashes (2000-02, 2008). — [quant-investing.com](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe)
- **Clare, Seaton, Smith & Thomas, "Breaking into the blackbox"** (J. Asset Management 2013) studied the S&P 500 *index* from 1988 to 2011. Simple rules, including the 200-day MA, dominated passive buy-and-hold. This is index level only. — [City Research Online](https://openaccess.city.ac.uk/17842); [Alpha Architect](https://alphaarchitect.com/trend-following-the-sp-500-some-practical-advice/)
- A related study (summarised by CXO) covered 117 SMA timing strategies on 39 futures series from 2000 to 2012. Stops of 5x the standard deviation of returns reduced maximum drawdown by about 17%, had little effect on average drawdown or recovery time, and were "a drag on the best-performing strategies". This is asset-class level. — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/higher-measurement-frequency-and-stop-losses-for-trend-followers)

### Inferences
- The theory (Kaminski-Lo) says a stop adds value only when the losers keep losing (momentum). Value and GARP portfolios are long stocks whose cheapness partly comes from past underperformance and that rely on mean reversion. A tight stop in that setting is expected to sell near local lows and give up the rebound. This is not directly tested for value portfolios. It follows from the random-walk/mean-reversion result plus Lo-Remorov's finding of negative short-horizon autocorrelation in recent individual-stock data.
- The consistent message across studies is that only *wide* stops (about 15-25% on a trailing or multi-day basis) are not harmful. Tight stops (<=10% fixed, or daily-checked) lose to costs and whipsaw. The current 25% catastrophic stop sits at the wide end. The open question is whether a *trailing* version, or a stop that needs confirmation, does better than a fixed-from-entry version.
- The 36/246 stop rate (14.6% of trades hitting -25% within about 6 months) is high next to US-style volatility. Nifty 500 mid/small caps over 2021-2026 are volatile, so a fixed-% stop would fire far more often in India than in the US studies. This supports volatility-scaled thresholds (Section 2).

### Gaps
- No study found tests stop-losses applied inside a value, quality, or GARP-sorted stock portfolio, comparing the same portfolio with and without stops. The "stops hurt value" claim rests on theory plus indirect evidence.
- Could not access full texts of Lo-Remorov or Lei-Li to quote exact return and drawdown numbers.
- "Han, Zhou & Zhu": search results confirmed Han and Zhou only. The third author could not be verified from the sources retrieved.

## 2. Stop distances for individual stocks: fixed % vs ATR or volatility-scaled; whipsaw costs

### Takeaway
Evidence favours wide stops. For individual stocks, 15-20% trailing worked best in the one stock-level grid search found (Stockholm). Volatility-scaled stops (multiples of daily standard deviation, or 10x ATR in Wilcox-Crittenden) are the academically used form. Tight stops (5%, or daily checks of a few percent) consistently lose to whipsaw and trading costs.

### Cited Findings
- Lei & Li scale stops in units of daily return standard deviation (5, 10, 20 SD), which builds in volatility scaling. Even so, there was no return benefit, only risk reduction from trailing versions. — [CXO](https://www.cxoadvisory.com/technical-trading/using-trailing-stop-losses-to-reduce-risk)
- Lo-Remorov: tight daily stops (0 to -6%) underperform after a 0.2% half-spread. Large bid-ask spreads tend to coincide with crashes, which raises the cost of stopping out exactly when stops trigger. Quick re-entry helped tight stops. — [CXO](https://www.cxoadvisory.com/equity-premium/stop-losses-on-stock-positions-in-depth)
- Stockholm OMXS30 grid (1998-2009): 5% trailing was worse than buy-and-hold. The optimum was a 15% trailing stop (73.9% cumulative vs 1.29% buy-and-hold). Benefits shrank steadily from 25% upward. — [quant-investing.com](https://www.quant-investing.com/blog/truths-about-stop-losses-that-nobody-wants-to-believe)
- **Wilcox & Crittenden (2005), "Does trend following work on stocks?"** covered more than 24,000 US stocks over 22 years, including delisted names. Entry was at an all-time high and exit on a trailing stop of 10 x ATR that is never lowered. It found positive expectancy. The 2025 update (Zarattini, Pagani, Wilcox; about 66,000 trades, 1950-2024) reports that fewer than 7% of trades drive profitability, so cutting the right tail is costly. Secondary sources disagree on the exact exit definition (one describes it as roughly a 20% decline). — [Original PDF](https://www.cis.upenn.edu/~mkearns/finread/trend.pdf); [Quantpedia](https://quantpedia.com/strategies/trend-following-effect-in-stocks); [Concretum 2025 update](https://concretumgroup.com/does-trend-following-still-work-on-stocks/); conflicting description: [Niederhoffer](https://dailyspeculations.com/vic/trend.html)
- The futures-level study used 5 x return standard deviation and reset the stop every 6 months. It reduced maximum drawdown about 17% but hurt the best strategies. — [CXO](https://www.cxoadvisory.com/technical-trading/higher-measurement-frequency-and-stop-losses-for-trend-followers)

### Inferences
- In OHLCV terms: 10 x ATR(10-20) or 5-10 x daily return SD comes to roughly 15-30% for a typical Nifty 500 stock with 2-3% daily SD. That brackets the current 25% fixed stop, so a volatility-scaled version would mainly *redistribute* stops: tighter on low-volatility quality names, wider on high-volatility mid-caps. That reduces whipsaw on volatile names.
- Checking the stop on a close basis, or on multi-day closes, rather than intraday lows, and executing at the next day's close, is supported by Lo-Remorov's finding that delayed execution helps.
- Whipsaw cost matters more than usual here, because a stopped-out position sits in cash until the next semi-annual rebalance. The cost of a false stop is up to about 6 months of missed recovery. A re-entry rule (for example, re-enter if the close recovers above the stop level or above the 50-day MA) would reduce this, and Lo-Remorov found quick re-entry beneficial.

### Gaps
- No study found that directly compares fixed %, ATR multiple, and SD-scaled stops head-to-head on the same individual-stock sample with costs.
- No ATR-stop evidence specific to Indian stocks.

## 3. Value-trap avoidance with the stock's own price: 200-DMA, 6-12 month return, value + momentum

### Takeaway
Strong evidence that value and momentum are negatively correlated and complementary at portfolio level (AMP 2013). Practitioner research supports removing cheap stocks with very poor momentum as a value-trap filter. No study was found that tests a *post-entry* 200-DMA or momentum *exit* inside a value portfolio. The evidence is mainly about selection at formation, not intra-period exits.

### Cited Findings
- **Asness, Moskowitz & Pedersen, "Value and Momentum Everywhere"** (J. Finance 2013) covers multiple asset classes, including individual stocks in the US, UK, Europe and Japan. Value-momentum correlation averages about -0.49 within asset classes and about -0.60 for stocks. An equal-weighted combination has a much higher Sharpe ratio and, in every region, less than half the volatility of either alone. — [Swedroe/ETF.com](https://www.etf.com/sections/index-investor-corner/swedroe-close-look-value-momentum); [CXO](https://cxoadvisory.com/value-premium/combining-value-and-momentum-across-asset-classes); [Paper PDF](https://www.johnhcochrane.com/s/Value-and-Momentum-Everywhere.pdf)
- **Research Affiliates, "Active Value Investing: Avoiding Value Traps"** (Feb 2024) used 32 years of US equities. Low quality and "sentiment-driven momentum" are common features of value traps. Removing them improved results in most valuation groups, most in the two cheapest quintiles, with an estimated +5.2% per year value premium (a projection). On book-to-market alone, the cheapest quintile was no better than the second-most-expensive one, with higher volatility. — [Advisor Perspectives reprint](https://www.advisorperspectives.com/commentaries/2024/02/29/active-value-investing-avoiding-traps)
- **Validea practitioner research** found that avoiding stocks with strong negative momentum worked very well in screens built to limit value traps. The reasoning given: if momentum is among the worst in the market, the odds are higher something has gone wrong with the business. — [Validea blog](https://blog.validea.com/?p=29725)
- AAII also reports that eliminating low-quality and poor-momentum stocks helps sidestep value traps (title-level finding; full text not retrieved). — [AAII](https://www.aaii.com/journal/article/212021-eliminating-low-quality-and-poor-momentum-stocks-helps-sidestep-value-traps)
- A CBS master thesis on the Russell 3000 (1997-2019) found that value-trap risk can also be reduced by controlling for fundamental quality. Quality may substitute partly for a momentum filter. — [CBS thesis](https://research-api.cbs.dk/ws/portalfiles/portal/62174175/879725_Master_Thesis_Final.pdf)
- **Indian evidence on stocks' own price signals:**
  - Raju (arXiv 2302.13245) studied Indian equities from Oct 2004 to Aug 2023. Stocks near their 52-week high have higher returns and Sharpe ratios, even after controlling for size. The effect is described as a robust anomaly with more stable alpha and weaker long-term reversal than academic 12-1 momentum. — [arXiv](https://www.arxiv.org/pdf/2302.13245); [Quantpedia](https://vvv.quantpedia.com/?p=31439)
  - Sehgal & Jain (2011) found momentum profits in India, stronger for 6-6 than 12-12 formation/holding, not explained by CAPM or Fama-French. — [Emerald](https://emerald.com/insight/content/doi/10.1108/03074351211193730/full/html); [IDEAS](https://ideas.repec.org/a/eme/jamrpp/v8y2011i1p99-122.html)
  - Maheshwari & Dhankar found momentum profits on NSE from 1997 to 2013, robust to controls for size, value and volume. — [arXiv review](https://www.arxiv.org/pdf/2302.13245)
- At index level, Clare et al. found the 200-day MA rule dominated buy-and-hold for the S&P 500 index from 1988 to 2011. This is *not* individual stocks. — [City Research Online](https://openaccess.city.ac.uk/17842)

### Inferences
- Momentum is a documented, persistent effect in India (6-month horizon and 52-week-high proximity). A GARP stock that falls into the bottom of its own price distribution after entry (for example, far below its 52-week high, or with a deeply negative 6-month return) is statistically more likely to keep underperforming. Kaminski-Lo's theory also says stops add value exactly when momentum is present. Together these give the best theoretical case for a v2 trend-confirmed exit, rather than a pure fixed-% stop.
- Without cross-sectional data, the exit function cannot rank a stock's momentum against the market. It can only use absolute own-price proxies: return since entry, return over the last 126 days, distance below the 200-DMA or 52-week high, and the 50/200-DMA relationship. These are weaker than cross-sectional momentum.
- A combined rule fits the evidence best: exit only when the price is below a moving average *and* drawdown from entry exceeds X. This targets "trend broken and losing" positions and avoids exiting on mild dips that are mean-reversion opportunities.

### Gaps
- No study found that tests a post-entry 200-DMA exit (or absolute 6-12 month return exit) inside a value, quality or GARP portfolio. The user would need to backtest it.
- Could not retrieve the Alpha Architect "Using momentum to find value" article (HTTP 403), Asness (1997) "The Interaction of Value and Momentum Strategies" (connection failure), or the Research Affiliates PDF, so I have no exact sort-level numbers.

## 4. Time-based exits and "dead money" rules

### Takeaway
I found no rigorous study of "exit if flat after N months" for value or quality stocks. The holding period is the main time-exit lever, and the GARP strategy already uses a fixed 6-month time exit.

### Cited Findings
- Lei & Li tested 3-, 6- and 12-month holding horizons with stops. The stop-vs-buy-and-hold conclusion (no return benefit, trailing reduces risk) held across horizons. — [CXO](https://www.cxoadvisory.com/technical-trading/using-trailing-stop-losses-to-reduce-risk)
- Indian momentum is stronger at 6-6 than 12-12 formation/holding (Sehgal & Jain). This suggests price trends in India persist over about 6 months, which argues against cutting flat positions early on price alone. — [IDEAS](https://ideas.repec.org/a/eme/jamrpp/v8y2011i1p99-122.html)

### Inferences
- With a 6-month holding window, a "dead money" exit (for example, flat after 3 months) saves at most about 3 months. Since proceeds go to cash, not to another GARP pick, it is unlikely to add return unless cash yield exceeds the expected return of a flat GARP name. Low priority for v2.

### Gaps
- No academic or quality practitioner backtest of dead-money or time-stop rules on individual value or quality stocks was found.

## 5. Profit-taking: does capping winners (+50%) help or hurt?

### Takeaway
Evidence argues against hard profit caps. Momentum and underreaction mean winners tend to keep winning, the disposition effect (selling winners early) is costly, and long-only stock trend returns are dominated by a few big winners.

### Cited Findings
- **Frazzini (2006, J. Finance), "The disposition effect and underreaction to news"**: investors' tendency to realize gains and ride losses causes underreaction to news. Post-announcement drift is strongest when capital gains and news share the same sign. An event strategy built on this earned monthly alphas above 200 bp (summaries differ on the exact magnitude). This implies winners with good news keep drifting up. — [AQR](https://www.aqr.com/Insights/Research/Journal-Article/The-Disposition-Effect-and-the-UnderReaction-to-News); [IDEAS](https://ideas.repec.org/a/bla/jfinan/v61y2006i4p2017-2046.html)
- In Wilcox-Crittenden's 2025 update, fewer than 7% of trades drive profitability in long-only stock trend following. Capping the right tail removes most of the edge. — [Concretum](https://concretumgroup.com/does-trend-following-still-work-on-stocks/)
- In India, stocks near their 52-week high outperform (Raju, 2004-2023). A GARP winner up +50% will often be near its 52-week high, which is a positive signal, not a reason to sell. — [arXiv](https://www.arxiv.org/pdf/2302.13245)

### Inferences
- Do not add a +50% profit cap. If protecting gains is wanted, a *trailing* stop that only activates after a large gain (for example, after +30-40%, trail at 2-3x the normal stop width from the peak close) keeps the right tail while limiting give-back. Lei-Li's finding that trailing stops reduce risk supports this. It is not tested on GARP specifically.

### Gaps
- No study directly tests a profit-target exit on value or GARP portfolios.

## 6. Gap-down / earnings-shock exits

### Takeaway
US evidence: large price drops that come *with* information (news, analyst revisions) are followed by continued drift down. Drops *without* news tend to reverse. Indian PEAD evidence is mixed but leans toward negative drift after bad earnings. An OHLCV-only proxy for "information" (gap at the open plus very high volume) is plausible but untested.

### Cited Findings
- **Chan (2003, J. Financial Economics)**, US headlines data: strong drift after bad public news, while extreme moves without news reverse. The effects are concentrated in smaller, less liquid stocks. — [MIT DSpace](https://dspace.mit.edu/handle/1721.1/28248); [abstract](https://academicnewsletter.sufe.edu.cn/info/357702)
- **Savor (2012, J. Financial Economics), "Stock returns after major price shocks"**, uses analyst reports as the information proxy. Price shocks with information drift. No-information shocks reverse. Drift occurs only when the price move and the analyst-recommendation change have the same sign. — [UPenn repository](https://repository.upenn.edu/handle/20.500.14332/34495)
- Govindaraj, Livnat, Savor & Zhao: large price changes followed immediately by analyst revisions show momentum. Those without revisions show short-term reversals (liquidity or noise). — [Alpha Architect](https://alphaarchitect.com/2013/03/follow-the-trend-and-the-sell-side/)
- **India**:
  - An event study (Nottingham) found negative post-earnings drift for over a week after bad earnings news, especially in 2009-2010. — [Nottingham eprints](https://eprints.nottingham.ac.uk/26569)
  - IIMB work finds drift lasting up to about 2 months after surprises. — [IIMB repository](https://repository.iimb.ac.in/handle/2074/17935)
  - Contradicting these, a study of 100 NSE firms from 2014 to 2018 found the market efficient with respect to earnings announcements, with liquidity-dependent heterogeneity. — [VUT Trends journal](https://journals.vutbr.cz/index.php/trends/article/view/541)
- Frazzini: drift after bad news is strongest when holders have losses. That is the situation of a GARP position already down from entry when the shock hits. — [AQR](https://www.aqr.com/Insights/Research/Journal-Article/The-Disposition-Effect-and-the-UnderReaction-to-News)

### Inferences
- A ">10% one-day drop on volume more than 3x the 50-day average" rule approximates an "information-driven" shock. Earnings and news days usually carry abnormal volume, while noise drops often do not. Under Chan and Savor this subset should drift rather than reverse. The volume threshold is my inference, not a tested parameter.
- Because no-news shocks reverse, a gap rule *without* a volume or information filter could sell exactly the reversals. The volume condition is essential.
- Waiting 1-2 days for confirmation (for example, still below the shock-day low after 2 sessions) is consistent with the drift persisting for over a week to about 2 months in Indian studies. It also lowers the chance of selling a no-news reversal.

### Gaps
- No study found isolates OHLCV-only gap-down plus volume events on NSE stocks and measures subsequent returns. The user would need an event study on their own data.

## 7. India-specific evidence on stop-losses / trend filters for NSE stocks

### Takeaway
I found no rigorous academic study of stop-loss rules or 200-DMA filters on individual NSE stocks. Indian evidence is limited to momentum and 52-week-high anomalies (supportive of trend-based exits), mixed PEAD results, and index-level MA studies.

### Cited Findings
- Momentum in India: Sehgal & Jain 2011 (6-6 stronger), Maheshwari & Dhankar (NSE 1997-2013, robust to size, value and liquidity), and Ansari & Khan 2012 (not explained by CAPM or Fama-French). — [arXiv review](https://www.arxiv.org/pdf/2302.13245); [Emerald](https://emerald.com/insight/content/doi/10.1108/03074351211193730/full/html)
- 52-week-high effect in India from 2004 to 2023 is robust and more stable than 12-1 momentum. — [arXiv 2302.13245](https://www.arxiv.org/pdf/2302.13245)
- A JIER paper backtests SMA/EMA rules on the NIFTY 50 *index* from 2010 to 2023 (results not retrieved). — [JIER](https://jier.org/index.php/journal/article/download/3254/2626/5883)
- Practitioner content (broker blogs, a GitHub NSE backtester with ATR trailing stops and a long-term MA filter) provides tools but no reported results. — [GitHub nse-backtester](https://github.com/Arnav-Y/nse-backtester); [Goodwill blog](https://www.gwcindia.in/blog/trailing-stop-loss-strategies-that-protect-profits-in-nse-trades/)

### Inferences
- Candidate v2 rules (all computable from the stock's own OHLCV plus entry price and date), ranked by evidential support:
  1. **Volatility-scaled trailing catastrophic stop** in place of the fixed 25%. For example, exit if close <= peak close since entry minus k x ATR(20), with k of about 8-10, floored at -15% and capped at -30% from entry, executed at the next day's close. Support: Lei-Li (trailing reduces risk), Wilcox-Crittenden (10 ATR), Stockholm grid (15-20% trailing best), Lo-Remorov (wide stops help, delayed execution helps).
  2. **Trend-confirmed loss exit**: exit if close < 200-DMA, the 200-DMA is falling, *and* the position is down more than about 12-15% from entry, confirmed over N (for example 5-10) consecutive closes. Support: momentum in India, Kaminski-Lo (stops help only under momentum), value-trap literature. Not directly tested.
  3. **Information-shock exit**: one-day close-to-close drop >= 10% (or a gap-open of 7% or more) with volume >= 3x the 50-day average, *and* no recovery above the shock-day midpoint within 2-3 sessions. Support: Chan 2003, Savor 2012, Indian PEAD (mixed). Not tested on NSE with OHLCV only.
  4. **No profit cap.** At most a wide trailing give-back stop after large gains.
  5. **Low priority**: dead-money time exits.
- Any rule should be backtested against the existing v1 on the same 246 trades. Report (a) how many of the 36 catastrophic stops it catches earlier and at what average saving, (b) how many non-stopped trades it exits that later recovered (whipsaw cost), and (c) portfolio CAGR, maximum drawdown and Sharpe after realistic NSE costs. With only about 10 rebalances in 2021-2026, overfitting risk is high, so prefer parameters drawn from the literature over tuned ones.

### Gaps
- No Capitalmind or Marcellus published backtests with data on stop-losses for Indian stocks were found within the search budget.
- No Indian academic study of stop-loss rules on individual stocks was found.
