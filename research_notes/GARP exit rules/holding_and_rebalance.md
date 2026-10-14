# Holding Period, Rebalance Frequency, Rank Buffers and Sell Discipline for GARP / Quality-Value Portfolios

Context: GARP Semi-Annual v1 (NSE Nifty 500, top 25 by growth+quality+PEG, rebalanced about 15 Jun / 15 Dec, sells everything at the next rebalance, plus a 0.75 x entry catastrophic stop). Research date 2026-10-14.

Research limits: niftyindices.com methodology PDFs, the FAJ "Smart Rebalancing" paper, QuantPedia and Alpha Architect all timed out or returned 403/429 errors, so some numbers below come from search-engine summaries of those pages and are marked that way. NSE's exact buffer thresholds for Quality 30 and Value 30/50 could NOT be confirmed. See Gaps.

## 1. Optimal holding period, rebalance frequency and signal decay

### Takeaway
Value and quality signals decay slowly, much more slowly than momentum or investment. The one cross-market decay study found puts the best rebalance interval at about 3-4 months for value and 4-5 months for quality before costs. Index providers mostly pick semi-annual or annual for value and quality to keep turnover down. Semi-annual is a reasonable gross choice. Net of Indian taxes, a hold past 12 months has a clear structural advantage (see section 5).

### Cited Findings
- Flint & Vermaak, "Factor Information Decay" (Journal of Portfolio Management; SSRN 3986499) studied value, momentum, quality, investment and low volatility across 12 developed and emerging markets, 2002-2019. Value had the longest information half-life. Momentum and investment decayed fastest. — [Search summary of Alpha Architect, "Information Decay"](https://alphaarchitect.com/information-decay/); [QuantPedia, "How Often Should We Rebalance Equity Factor Portfolios?"](https://quantpedia.com/?p=18634) (pages not directly readable; figures come from search summaries)
- Their suggested rebalance intervals: value about 3-4 months, momentum 3 months, quality 4-5 months, investment 1 month, low volatility 5-6 months. Faster-decaying factors need more frequent rebalancing, which raises turnover and trading costs. — [Alpha Architect summary via search](https://alphaarchitect.com/information-decay/) (verify against the SSRN original)
- FTSE Russell found that value index characteristics (capacity, diversification) hold up across rebalance frequency and timing, but frequency has a big effect on turnover. It chose annual rebalancing because it minimises turnover. — [FTSE Russell value factor paper](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/other/ftse-value-factor-paper.pdf)
- NSE's factor indices are mostly semi-annual. Nifty200 Quality 30 is rebalanced semi-annually. — [Nifty200 Quality 30 factsheet](https://niftyindices.com/Factsheet/Factsheet_NIFTY200_Quality30.pdf). Nifty500 Value 50 is reviewed semi-annually, effective the last working day of June and December. — [Nifty500 Value 50 factsheet](https://www.niftyindices.com/Factsheet/FactsheetNIFTY500Value50.pdf). Nifty Alpha Quality Value Low-Volatility 30 is rebalanced semi-annually. — [2018 factsheet](https://cdn.freefincal.com/wp-content/uploads/2018/07/Factsheet_NIFTY_Alpha_Quality_Value_Low-Volatility_30.pdf). Nifty100 Low Volatility 30 is reviewed quarterly. — [factsheet](https://www.niftyindices.com/Factsheet/Nifty100_LowVolatility30.pdf)
- In June 2026, NSE changed the Alpha-Quality-Value-Low-Vol stock-selection weights from ROCE 20% / PE 30% / PB 30% / DY 20% to E/P, S/P, B/P and DY at 25% each, effective from the next reconstitution. — [NSE press release 10-Jun-2026](https://www.niftyindices.com/Press_Release/ind_prs10062026.pdf) (summary only; effective date not confirmed)
- The more often a factor signal turns over, the more sensitive the portfolio is to "rebalance timing luck", meaning performance differences that come only from which calendar dates are used. — [AlphaLayer, "Timing Luck in Factor Rebalancing"](https://alphalayerai.substack.com/p/timing-luck-in-factor-rebalancing)
- Novy-Marx & Velikov (RFS 2016): most anomalies with one-sided monthly turnover below 50% keep significant net spreads once designed to reduce costs. Higher-turnover strategies mostly fail. Size, value and profitability have the most capacity. — [NBER w20721](https://nber.org/papers/w20721); [paper PDF](https://mysimon.rochester.edu/novy-marx/research/ToAatTC.pdf)

### Inferences
- GARP combines growth, quality and value. All three are slow-decay signals by the Flint & Vermaak ranking, so 6-month refreshes are not obviously too slow. The decay evidence does NOT require selling every holding every 6 months. Holdings that still rank highly carry useful information.
- Quarterly rebalancing might add a little gross alpha (value's suggested interval is 3-4 months). In India, though, it would make every exit short-term for tax and double STT/stamp costs, so it is unlikely to help net. Annual or "semi-annual review with a buffer" is the more defensible direction.
- With only two calendar dates a year, v1 is exposed to timing luck. Staggered tranches (for example, two half-portfolios offset by 3 months) or a buffer reduce this. Both need engine changes.

### Gaps
- No India-specific academic study of GARP/quality/value signal decay or of optimal rebalance frequency was found. Flint & Vermaak include emerging markets, but per-country (India) results were not available.
- The exact half-life numbers (in months) could not be read from the primary paper.

## 2. Rank buffers / hysteresis ("buy top 25, hold until outside top 50")

### Takeaway
Buffers are the single most effective simple cost-mitigation tool in the academic literature (Novy-Marx & Velikov's "buy/hold spread"), and NSE uses them in several factor indices. The common NSE pattern is "retain an existing constituent if it ranks within about 2x the target count" (for example, top 60 for a 30-stock index, top 100 for a 50-stock index). This needs fundamentals or ranks at rebalance time, so it CANNOT be done in a price-only exit function. It needs an engine or entry-rule change.

### Cited Findings
- Novy-Marx & Velikov: "introducing a buy/hold spread, which allows investors to continue to hold stocks that they would not actively trade into, is the single most effective simple cost mitigation strategy." — [NBER w20721](https://nber.org/papers/w20721); [Alpha Architect summary](https://alphaarchitect.com/trading-costs-destroy-factor-investing/)
- Nifty100 Low Volatility 30: an existing constituent ranked within the top 60 on low-vol score is retained (2x buffer on a 30-stock index). Reviewed quarterly. — [Nifty100 LowVolatility30 factsheet](https://www.niftyindices.com/Factsheet/Nifty100_LowVolatility30.pdf)
- Nifty200 Value 30: "a buffer based on Value Score ranks is applied to reduce turnover" (thresholds not shown on the page found). — [Nifty200 Value 30 page](https://niftyindices.com/indices/equity/strategy-indices/nifty200-value-30)
- Nifty200 Momentum 30: "a buffer based on normalized momentum score ranks is applied to reduce turnover." — [Nifty200 Momentum 30 factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf); [UTI fund document](https://doc.utimf.com/uticontainer/UTI%20Nifty%20200%20Momentum%2030%20Index%20Fund-75220221010-220006.pdf)
- NIFTY High Beta 50: "if the existing constituent at the time of the review ranks within the top 100, the same can be retained" (2x buffer on 50). — [Method_Nifty_High_Beta_50](https://www.niftyindices.com/Methodology/Method_Nifty_High_Beta_50.pdf)
- Nifty Dividend Opportunities 50: top 25 by dividend yield are always included, and stocks ranked below 75 are always excluded (an entry/exit band around 50). — [factsheet](https://niftyindices.com/Factsheet/ind_Nifty_Divid_Opp50.pdf)
- Nifty Midcap 100 uses a turnover-rank band: add if ranked in the top 70, remove only if ranked below 130. — [NSE methodology document via search](https://nsearchives.nseindia.com/content/indices/Method_NIFTY_Equity_Indices.pdf)
- No buffer was found in the retrieved pages for Nifty200/Nifty100 Quality 30 or Nifty500 Value 50. — [Nifty200 Quality 30 factsheet](https://niftyindices.com/Factsheet/Factsheet_NIFTY200_Quality30.pdf); [Nifty500 Value 50 factsheet](https://www.niftyindices.com/Factsheet/FactsheetNIFTY500Value50.pdf)
- "Smart Rebalancing" (Financial Analysts Journal, 2024; long-only value, profitability, investment and momentum, 1963-2020): prioritising trades by signal strength (buy the strongest, sell the weakest first) under a turnover cap captures most of the factor premium while cutting turnover. "Priority best" generally beats proportional trading. In the search-engine summary, the value portfolio earned its highest return with turnover capped at only about 20% a year. — [FAJ article](https://www.tandfonline.com/doi/full/10.1080/0015198X.2024.2317323) (403, summary via search); [CFA Institute Enterprising Investor summary](https://rpc.cfainstitute.org/blogs/enterprising-investor/2024/implementation-shortfalls-hamstring-factor-strategies)
- That FAJ study also found that decile returns are "not entirely monotonic" for most signals. Stocks ranked, say, 26-50 often earn about the same as ranks 1-25, which is why holding a slightly lower-ranked name costs little. — [CFA Institute summary](https://rpc.cfainstitute.org/blogs/enterprising-investor/2024/implementation-shortfalls-hamstring-factor-strategies)

### Inferences
- A natural v2 rule, following NSE: buy the top 25; at each rebalance keep any holding still ranked within the top 50 (2x); fill empty slots from the top of the ranking. This is an ENGINE/ENTRY change. The exit function cannot see ranks, so the screener must pass a "still in top-N" set to the exit, or the engine must suppress the rebalance sell.
- The exact turnover reduction for a 25/50 band on Nifty 500 GARP is not in the sources. It should be measured in the backtest by comparing the share of rebalance exits that are re-bought next day (currently 185 rebalance exits).
- Price-only proxy (weak): at a scheduled rebalance, skip the sell if the position is in profit and above its own trend (for example, close > 200-day SMA), and re-evaluate at the next date. This is momentum-like, not a fundamental buffer. Treat it as an experiment, not as evidence-based.

### Gaps
- Exact buffer thresholds for Nifty200 Quality 30, Nifty100 Quality 30, Nifty200 Value 30, Nifty500 Value 50 and Nifty Alpha Quality Value Low-Vol 30 could not be confirmed (niftyindices.com methodology PDF timed out). Check them in Method_NIFTY_Equity_Indices.pdf.
- No published study found that reports turnover-reduction percentages or return effects for a specific "top 20% buy / top 40% hold" rule.

## 3. Practitioner GARP sell discipline (Lynch, O'Shaughnessy, AAII, Indian PMS)

### Takeaway
Practitioner GARP sell rules are mostly about the thesis or fundamentals ("the story changed", growth slowing, PEG far above 1-2). Little independent evidence supports mechanical PEG-based selling. Systematic practitioners (O'Shaughnessy, AAII and Validea screen portfolios) rebalance on a calendar, typically annually, rather than using discretionary sells.

### Cited Findings
- Lynch treats PEG of about 1 as fair. PEG above 2 is commonly described as "priced for perfection", and PEG 1-2 as a grey zone. — [StockAlarm GARP/PEG guide](https://pro.stockalarm.io/blog/peg-ratio-guide); [FastGraphs](https://www.fastgraphs.com/blog/the-peg-ratio-peter-lynchs-secret-to-29-annual-returns-and-how-fast-graphs-makes-it-easy-to-use)
- A secondary "Peter Lynch Playbook" summary lists, by stock category, selling stalwarts after a 30-50% rise, with "PEG <0.5-1x fine, 2x expensive". This is not verified wording from Lynch. — [The Peter Lynch Playbook (PDF)](https://mjbaldbard.wordpress.com/wp-content/uploads/2018/05/the-peter-lynch-playbook.pdf)
- A strict PEG sell rule can force early exits from compounders: after a stock doubles or triples, trailing P/E often pushes PEG well above 1. — [FastGraphs, "The Right Way to Value Growth Stocks Part 3"](https://www.fastgraphs.com/blog/the-right-way-to-value-growth-stocks-part-3)
- Validea's Lynch-model screen portfolio claims +1,621% since 2003 (vendor backtest with its own rebalancing; not independent evidence about selling). — [Validea Peter Lynch](https://www.validea.com/peter-lynch)

### Inferences
- Lynch's own sell reasons (story change, fundamentals deteriorating, fully valued relative to growth) are widely paraphrased but were not verified from his books in this research.
- "Growth deceleration" and "thesis broken" need fundamental data at exit time. That is an ENGINE change: the exit would need access to quarterly fundamentals or to the screen score.

### Gaps
- O'Shaughnessy's "What Works on Wall Street" holding-period and rebalance findings (annual rebalance in his tests), AAII GARP screen sell rules, and Indian PMS/MF (for example, quant PMS) sell commentary were not retrieved. No sources were reached for them.
- No primary Lynch or Fisher quote was retrieved.

## 4. Valuation-based sells (P/E or PEG stretched)

### Takeaway
No independent empirical study was found showing that selling GARP or quality holdings when P/E or PEG becomes stretched improves returns. Practitioner commentary warns it cuts winners early.

### Cited Findings
- No peer-reviewed tests of PEG-based sell rules were found. Available claims are vendor backtests or commentary. — [Validea](https://www.validea.com/peter-lynch); [FastGraphs](https://www.fastgraphs.com/blog/the-right-way-to-value-growth-stocks-part-3)
- PEG definitions vary (trailing or forward P/E, EPS or revenue growth), which changes results materially. PEG is not meant for cyclicals, turnarounds or financials. — [StockAlarm GARP guide](https://pro.stockalarm.io/blog/growth-at-reasonable-price-garp); [Stablebread](https://stablebread.com/peter-lynch-stock-valuation/)
- The FAJ "Smart Rebalancing" result (premium mostly kept even with only about 20% annual value turnover) suggests that letting holdings drift away from the "cheapest" end costs little. — [CFA Institute summary](https://rpc.cfainstitute.org/blogs/enterprising-investor/2024/implementation-shortfalls-hamstring-factor-strategies)

### Inferences
- A valuation sell is in effect a narrow buffer on the value leg. Given non-monotonic decile returns and India's high short-term tax cost, a PEG > 2-3 "hard sell" should only be tested as an optional rule. It needs fundamentals at exit time (ENGINE change).

### Gaps
- No India or US study quantifying the return effect of valuation-triggered sells in quality or GARP portfolios was found.

## 5. Cost of selling and re-buying at rebalance (India) and the 12-month LTCG threshold

### Takeaway
Under Indian rules from 23 July 2024 (still in force for tax year 2026-27 under the Income-tax Act, 2025), a gain realised within 12 months is taxed at 20% (STCG), versus 12.5% LTCG above a Rs 1.25 lakh annual exemption. Explicit trading cost for a delivery round trip is about 0.22% plus a DP fee. The semi-annual design makes every profitable exit STCG. Selling and re-buying the same stock at rebalance crystallises 20% tax and pays costs for no change in exposure. This argues strongly for (a) not selling names that remain in the portfolio and (b) holding winners past 12 months.

### Cited Findings
- STCG on listed equity (Section 111A) is 20%. LTCG (Section 112A) is 12.5% above Rs 1.25 lakh per financial year. Both apply to sales on or after 23 July 2024 (previously 15% / 10% above Rs 1 lakh). — [Business Standard, Budget 2024](https://www.business-standard.com/amp/markets/news/budget-2024-hikes-ltcg-tax-rate-to-12-5-stcg-to-20-stt-on-f-o-also-up-124072300553_1.html); [TaxGuru, tax year 2026-27 under Income-tax Act 2025](https://taxguru.in/?p=1052279)
- 4% health and education cess applies on top. Surcharge applies only above Rs 50 lakh total income. The Rs 1.25 lakh exemption is shared across all equity and equity-MF LTCG in a financial year, and unused amounts do not carry forward. The concessional rates require STT to have been paid. — [TaxGuru](https://taxguru.in/?p=1052279); [IndMoney](https://www.indmoney.com/learn/ipo/ipo-taxation)
- STT on equity delivery is 0.1% on both buy and sell. The April 2026 change to F&O STT did not change delivery or intraday rates. — [Zerodha support: STT](https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/how-is-the-securities-transaction-tax-stt-calculated)
- Zerodha delivery brokerage is Rs 0. Stamp duty on delivery is 0.015%, buy side only. The DP charge is about Rs 13.5 + GST per scrip per sell day. — [StockCalc Zerodha 2026 breakdown](https://stockcalc.in/blog/zerodha-brokerage-charges-2026-full-breakdown); [Chittorgarh](https://www.chittorgarh.com/stockbroker/zerodha/18/?p=4)
- Worked example: Rs 1.40 lakh buy and Rs 1.47 lakh sell incur STT of Rs 287 and stamp duty of Rs 21. — [StockCalc](https://stockcalc.in/blog/zerodha-brokerage-charges-2026-full-breakdown)
- Bid-ask spreads ignore price impact, so they understate costs for larger orders. — [Alpha Architect on Novy-Marx & Velikov](https://alphaarchitect.com/trading-costs-destroy-factor-investing/)

### Inferences
- Explicit round-trip cost is about 0.1% + 0.1% STT + 0.015% stamp = about 0.215%, plus exchange/SEBI/GST fees (not sourced here, typically a few basis points) and slippage. For Nifty 500 mid and small caps, slippage could plausibly be 0.1-0.5% per side, but that range is NOT sourced. At two full turnovers a year, explicit costs alone are about 0.4-0.5% a year of drag.
- Tax drag: on a position up 20% at the 6-month rebalance, STCG of 20% costs 4.0% of position value, versus 2.5% if held past 12 months at 12.5% (before the Rs 1.25 lakh exemption). That is a gap of 1.5% of position value per winning trade. If the same stock is re-bought the next day, all of that tax is paid for nothing. Tax is deferred, not avoided, when holding longer, which adds compounding value.
- Simple price-and-date exit ideas (EXIT-FUNCTION ONLY, no fundamentals needed):
  1. Minimum hold of 12 months + 1 day before a scheduled rebalance sell (that is, skip the first rebalance date and sell at the second, about 12 months later, or at the first rebalance date after 365 days). This becomes an annual-turnover strategy for each position.
  2. "Winners past LTCG": at a rebalance date, if the position is in profit and has been held for fewer than 365 days, defer the sell until day 366 or the next rebalance. Losers can still be sold at the rebalance (STCG losses can be set off against gains).
  3. Keep the 0.75 x entry catastrophic stop. Optionally add a trailing stop for very large winners. Note that a stop inside 12 months triggers STCG.
- Rules needing ENGINE or ENTRY changes: rank buffer (top 25 buy / top 50 hold), "don't sell if the stock is re-selected at the same rebalance", fundamental thesis-break sells (growth deceleration, PEG > threshold), staggered tranches, and turnover-capped priority rebalancing.
- The backtest probably does not model taxes. If so, v1 vs v2 comparisons will understate the benefit of longer holds and buffers. A post-tax CAGR column would be useful (engine change).

### Gaps
- Exchange transaction charge, SEBI fee and GST rates for 2026 were not retrieved from primary sources.
- No sourced estimate of market-impact or slippage for Nifty 500 mid and small caps was found.
- No India-specific study comparing post-tax returns of semi-annual vs annual factor rebalancing was found.
