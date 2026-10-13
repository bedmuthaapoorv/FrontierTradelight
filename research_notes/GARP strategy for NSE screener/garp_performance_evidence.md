# GARP Performance Evidence: Global Context and India (NSE) Focus

Scope note: per a mid-task scope update, these notes cover all GARP formulations, including ones that use trailing growth, analyst forward estimates, earnings revisions, and longer holding periods, not only what the user's current tool supports. Numbers taken from NSE index dashboards and factsheets were downloaded directly as PDFs from niftyindices.com and text-extracted. All index returns are Total Return Index (TRI). Returns up to 1 year are absolute; longer periods are CAGR.

## 1. What does academic and practitioner research show about GARP / PEG / combined growth+value screens?

### Takeaway
There is very little rigorous, peer-reviewed evidence that PEG-sorted portfolios beat the market. The best public test, FactorResearch's US study for CFA Institute (1989–2018), found that GARP's outperformance depends on the start date and mostly disappears once loss-making stocks are excluded. Practitioner screens (AAII) show large backtested outperformance, but those screens also add momentum and earnings-acceleration filters. The academic analyst-expectations literature (La Porta 1996, BGLS 2019) is a warning against trusting forward long-term growth (LTG) estimates in the PEG denominator.

### Cited Findings
**FactorResearch / CFA Institute Enterprising Investor, "GARP Investing: Golden or Garbage?" (Nicolas Rabener, March 2019), US only**
- Method: universe of US stocks with market cap above $1bn. PEG = trailing-12-month P/E ÷ 3-year EPS growth, with PEG < 1 counted as GARP. Rebalanced monthly, cap-weighted, 10 bps cost per trade. Value was proxied by P/B and P/E, Growth by 3-year sales and earnings growth — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- On average about 38% of US stocks had a PEG below 1, so the screen is not very selective — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- GARP stocks had earnings growth "significantly above" the market's and lower median P/Es — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- GARP "outperformed substantially" from 1989, but much of the outperformance disappeared when stocks with negative earnings were excluded — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- From 1989 to 2001, GARP and Growth both beat Value, especially in the 1999–2001 tech bubble. After the bubble, GARP behaved like Value. Starting the backtest in 2000, pure Value would have done better. Starting in 2010, the broad market had the highest annual returns, especially with negative-earnings stocks excluded — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- The author concludes GARP "can generate enviable results" but the size of the result depends on the observation window. Its main benefit may be giving a systematic framework for buying growth at reasonable valuations. Exact CAGR, Sharpe and drawdown figures appear only in charts I could not read — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)

**AAII screen tracking (US, hypothetical backtests, price returns only)**
- "Value on the Move – PEG With Estimated Growth" (forward analyst growth): 12.9% a year from its 1998 start to May 31, 2023, versus 5.7% for the S&P 500. The screen also requires positive long-term earnings, quarterly EPS growth and strong relative price strength — [AAII](https://www.aaii.com/journal/article/223803-spotting-value-on-the-move-with-the-peg-ratio)
- A companion "PEG With Historical Growth" version (trailing P/E with 5-year historical EPS growth) is also reported to beat the S&P 500 since 1998. I did not find its annualized figure — [AAII](https://www.aaii.com/journal/article/223803-spotting-value-on-the-move-with-the-peg-ratio)
- AAII's Peter Lynch (GARP) screen: about 8.0% a year since 1998, versus 5.7% for the S&P 500 (undated snapshot) — [AAII via search summary](https://www.aaii.com/stockideas/article/67137-reasonable-growth-with-value-on-the-move)
- AAII's P/E Relative screen: 13.7% compound annual price gain from January 1998 to August 2023, versus 6.0% for the S&P 500 — [AAII](https://www.aaii.com/latest/article/87473-pe-relative-screening-approach)

**Analyst forward-growth estimates (relevant to forward-PEG variants), US**
- La Porta (1996, Journal of Finance 51(5):1715–42): stocks with the most optimistic analyst long-term EPS growth forecasts earned lower subsequent returns than those with the most pessimistic forecasts, because analysts extrapolate and are too optimistic about fast growers — [vLex abstract](https://law-journals-books.vlex.com/vid/expectations-crosssection-stock-returns-855607301)
- Bordalo, Gennaioli, La Porta and Shleifer (2019, Journal of Finance; NBER w23863) confirm that the finding still holds. Firms with the most optimistic LTG forecasts have grown fast in the past, but their growth then reverts to the mean — [NBER](https://nber.org/papers/23863); [Harvard](https://shleifer.scholars.harvard.edu/publications/diagnostic-expectations-and-stock-returns-0)
- Bradshaw (2004, The Accounting Review 79(1):25–50): over 1994–98, analysts' recommendations were positively related to PEG/LTG heuristics and negatively related to residual-income value estimates. In other words, sell-side recommendations lean on PEG — [SUFE newsletter summary](https://academicnewsletter.sufe.edu.cn/info/416180)
- Easton (2004, The Accounting Review) compares the expected-return estimates implied by PE and PEG heuristics with a model-based estimate. PEG uses short-term growth forecasts — [SUFE newsletter summary](https://academicnewsletter.sufe.edu.cn/info/416195)
- Damodaran: there is "no basis" for assuming a firm is undervalued just because its P/E is below its expected growth rate. PEG ignores risk, payout and growth duration — [NYU Stern](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/lectures/peg.htm)

**Earnings revisions (an alternative or complement to forward PEG)**
- See Section 4 for S&P DJI's Pan-Asia/India revision study.

### Inferences
- Plain PEG < 1 on trailing data mostly works as a value tilt plus a filter that excludes losses. In the US it has not shown a robust premium independent of value once losses are removed.
- Practitioner screens that look good (AAII PEG at 12.9% vs 5.7%) stack momentum and earnings-acceleration filters on top of PEG. The excess return probably comes partly from those filters, not from PEG alone. They are also price-only, survivor-unaudited backtests.
- A PEG built on forward analyst LTG may be systematically biased. The stocks with the lowest forward PEG often have the most optimistic LTG, which is exactly the group that La Porta and BGLS show underperforms. Short-horizon (FY1/FY2) estimates or revisions are probably safer inputs than 3–5-year LTG.

### Gaps
- I found no peer-reviewed paper reporting Sharpe ratios or maximum drawdowns for PEG-sorted portfolios. Peters (1991, JPM, "Valuing a Growth Stock") is often cited as showing that low-PEG stocks outperform, but I could only confirm that citation through secondary sources.
- I did not retrieve AQR, Research Affiliates or MSCI research quantifying a GARP or "growth + value" composite. MSCI's GARP-style indices were not checked.
- The CFA/FactorResearch numeric results (CAGR, alpha) are in charts only.

## 2. India-specific evidence: academic studies, NSE factor indices, GARP-mandate funds

### Takeaway
No large-scale academic study of PEG/GARP on the full NSE universe was found. Indian evidence is strong for value, momentum and quality separately (IIMA factor library; Jacob–Pradeep–Varma quality paper), and NSE's index data from 2005 onwards gives usable proxies. As of 30 Sep 2026, the cheap-valuation indices (Nifty500 Value 50, Nifty200 Value 30) lead on 3-year and 5-year CAGR (about 20–23%, versus about 6% for Nifty 50 and about 9–10% for Nifty 500). The new Nifty500 Growth 50 (launched Aug 2026; growth score from 3-year PAT growth, 3-year sales growth and 1-year risk-adjusted return) is the closest NSE analogue to the "growth" leg, and it shows a 5-year CAGR of 15.9% and 18.5% since its 2005 base. There is no official NSE "GARP" index.

### Cited Findings
**Academic: Indian factor premia**
- IIMA Indian Fama-French-Momentum data library (Agarwalla, Jacob, Varma), October 1993 to December 2025: equity risk premium 5.63%/yr (volatility 21.44%, max drawdown -77%, 11.3 years). Value (HML) 6.86%/yr (volatility 15.09%, max drawdown -64%, peak Dec 1994 to trough Feb 2000, 7.6 years). Momentum (WML) 10.96%/yr (volatility 17.30%, max drawdown -62%, March 2000 to March 2005). Size (SMB) -4.01%/yr (max drawdown about -87%, not yet recovered) — [IIMA data library](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/drawdown.php)
- The IIMA methodology uses CMIE Prowess data, excludes illiquid firms so that portfolios are investible, and corrects for survivorship because many Indian listed companies disappeared — [IIMA working paper](https://web.iima.ac.in/~iffm/legacy/four-factors-India-90s-onwards-IIM-WP-Version-original-Sep13.pdf)
- Quality factor in India (Jacob, Pradeep, Varma, 2022; sample April 1995 to March 2021). QMJ long-short four-factor alpha was 0.92%/month (above 10% annualized, about twice the US estimate). The long-only quality portfolio had a 0.69%/month alpha and a mean of 2.12%/month, versus 1.62%/month for momentum and 1.33%/month for the market. Value's mean monthly return was "marginally negative" in this sample. The top quality decile had a 1.73%/month value-weighted excess return versus 0.17% for the bottom decile. Average drawdown was 9.76% for QMJ and 7.99% for long-only quality, versus 12.13%/14.52% for momentum. Quality did better in weak markets, and the alpha is driven by profitability and payout — [Quantpedia summary](https://quantpedia.com/performance-of-factor-strategies-in-india/); [IIMA](https://www.iima.ac.in/publication/four-factor-model-indian-equities-market)
- Note the conflict: IIMA's HML is +6.86%/yr for 1993–2025, while the Jacob et al. sample (1995–2021) shows value "marginally negative". The difference comes from the sample window and the value-factor construction.
- PEG in India: P. A. Mary Auxilia (2019, IJRISS 3(1):81–83) studied NSE mid-cap IT stocks only. She computed PEG from P/E and EPS CAGR before investment, held the stocks for 5 years, and found that PEG < 1 stocks gave "remarkably higher returns" than the market. The sample is tiny and limited to one sector — [IDEAS/RePEc](https://ideas.repec.org/a/bcp/journl/v3y2019i1p81-83.html)
- Index-level PEG: Stable Investor (2012) estimated the Indian market PEG at about 0.97 (P/E 16.7 ÷ 18-year average growth of 17.1%). This is a valuation snapshot, not a returns test — [Stable Investor](https://stableinvestor.com/2012/01/nifty-stocks-and-peg-ratios.html)

**NSE factor indices: NSE Index Dashboard, 30 September 2026 (TRI; 1Y absolute, 3Y/5Y CAGR; 1Y volatility; P/E)** — [NSE Index Dashboard Sep 2026](https://www.niftyindices.com/Index_Dashboard/Index_Dashboard_SEP2026.pdf)

| Index | 1Y | 3Y | 5Y | Vol 1Y | Beta | P/E |
|---|---|---|---|---|---|---|
| Nifty 50 | -7.09 | 6.06 | 6.38 | 13.46 | 1.00 | 19.36 |
| Nifty 500 | -2.03 | 9.52 | 9.04 | 14.21 | 1.03 | 21.77 |
| Nifty500 Value 50 | 6.89 | 20.13 | 22.26 | 16.07 | 0.93 | 9.92 |
| Nifty200 Value 30 | 7.89 | 21.22 | 22.91 | 16.83 | 1.00 | 8.86 |
| Nifty50 Value 20 | -9.51 | 4.24 | 6.20 | 12.23 | 0.84 | 13.99 |
| Nifty500 Growth 50 | 9.42 | 18.26 | 15.89 | 20.88 | 1.32 | 40.63 |
| Nifty200 Quality 30 | -5.42 | 6.64 | 6.40 | 13.58 | 0.86 | 25.66 |
| Nifty500 Quality 50 | -1.14 | 11.29 | 9.77 | 15.79 | 0.98 | 24.49 |
| Nifty Midcap150 Quality 50 | -2.55 | 7.44 | 6.29 | 15.45 | 0.98 | 29.65 |
| Nifty200 Momentum 30 | -0.47 | 9.21 | 9.28 | 18.63 | 1.18 | 23.21 |
| Nifty500 Momentum 50 | 5.08 | 11.39 | 12.38 | 18.74 | 1.16 | 29.38 |
| Nifty Alpha 50 | 11.44 | 14.63 | 12.03 | 19.23 | 1.17 | 27.55 |
| Nifty200 Alpha 30 | 6.01 | 13.92 | 13.62 | 19.17 | 1.18 | 17.92 |
| Nifty500 Multifactor MQVLv 50 | -5.04 | 11.41 | 12.07 | 14.31 | 0.93 | 13.34 |
| Nifty Alpha Quality Value Low-Vol 30 | -6.17 | 12.01 | 12.90 | 11.79 | 0.80 | 15.71 |
| Nifty Growth Sectors 15 | -7.64 | 3.99 | 7.46 | 14.51 | 0.86 | 24.57 |
| Nifty500 Low Volatility 50 | -3.52 | 12.20 | 11.51 | 11.77 | 0.79 | 20.76 |

- Same indices at 31 December 2025, for comparison (1Y / 3Y / 5Y): Nifty 50 11.88/14.32/14.68. Nifty 500 7.76/16.71/16.88. Nifty500 Value 50 16.93/31.73/34.50. Nifty200 Value 30 20.30/33.94/34.81. Nifty200 Quality 30 4.68/16.40/13.73. Nifty200 Momentum 30 -4.57/17.95/19.00. Nifty Alpha 50 -10.17/19.98/21.25. MQVLv 50 5.40/24.76/22.31. Alpha Quality Value Low-Vol 30 6.96/25.20/21.13 — [NSE Index Dashboard Dec 2025](https://www.niftyindices.com/Index_Dashboard/Index_Dashboard_DEC2025.pdf)
- Nifty500 Growth 50 factsheet (as of 30 Sep 2026): launched 26 Aug 2026, with a backtested base of 1 Apr 2005. Since-inception TRI CAGR is 18.53%, with 23.59% standard deviation and beta 1.00 since inception, and 5-year standard deviation of 20.17%. It is tilt-weighted (growth score × free-float market cap), with stock caps of min(5%, 5× FF-mcap weight), a 30% sector cap, and semi-annual rebalancing in June and December. The growth score uses 3-year PAT growth, 3-year sales growth and 1-year risk-adjusted return. There is no valuation screen, and its P/E is 40.6 — [NSE factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500_Growth_50.pdf); [NSE press release 26 Aug 2026](https://www.niftyindices.com/Press_Release/ind_prs26082026.pdf)
- Nifty500 Multifactor MQVLv 50 (momentum, quality, value, low-vol; launched 6 Feb 2025, base 1 Apr 2005; as of 30 Sep 2026): 19.09% TRI CAGR since inception, with 17.24% standard deviation and beta 0.72 since inception. 5-year CAGR is 12.07% and 1-year is -5.04% — [NSE factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500MultifactorMQVLv50.pdf)
- Nifty500 Quality 50 (launched 20 Dec 2024, base 1 Apr 2005; as of 30 Sep 2026): 16.37% TRI CAGR since inception, 18.16% standard deviation, beta 0.78; 5-year CAGR is 9.77% — [NSE factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500Quality50.pdf)
- Nifty 50 (as of 30 Sep 2026): 12.12% TRI CAGR since Nov 1995, 22.39% standard deviation; 5-year CAGR is 6.38% and YTD -12.61% — [NSE factsheet](https://www.niftyindices.com/Factsheet/ind_nifty50.pdf)
- The Nifty200 Quality 30 had calendar-year returns of +21.11% (2020), +26.37% (2021) and -8.23% (2025), per a third-party tracker I could not verify against NSE — [Wright Research](https://www.wrightresearch.in/track/index/nifty-200-quality-30/)

**GARP-mandate funds and products in India**
- There is no SEBI "GARP" category. Kotak Flexicap's factsheet labels its style as "Value / GARP / Growth" across market caps — [Kotak MF factsheet](https://www.kotakmf.com/factsheet/feb_2026/kotak/Download_pdf/KOTAK%20FLEXICAP%20FUND.pdf)
- Fort Capital "India Multi Cap – GARP" holds 15–25 stocks, benchmarked to Nifty 50 TRI, with a stated target of beating it by 5–10% a year on 3-year rolling periods. It had no performance record (about 1.6 years old) on the APMI listing — [APMI](https://apmiindia.org/apmi/IaInsight.htm?IAID=1696)
- "Composite India GARP Fund" (PMS) is about 49% small cap and about 21% large cap, which shows that GARP-labelled Indian products can be heavily small-cap — [Business Today PMS](https://www.businesstoday.in/pms/composite-india-garp-fund-119)
- Franklin India Flexi Cap describes "growth stocks at fair valuations" and has a maximum historical drawdown of 37.7% (Arthgyaan, Sep 2026). The Value Research piece crediting it with beating its benchmark since 2021 is an advertorial — [Value Research](https://www.valueresearchonline.com/stories/222195/flexi-cap-funds-performance-analysis); [Arthgyaan](https://arthgyaan.com/fund/compare/franklin-india-flexi-cap-fund-direct-growth-vs-bank-of-india-flexi-cap-fund-direct-growth/118535-vs-148404)
- VanEck's US-listed GLIN ETF (India) markets itself as GARP, using EPS/sales growth plus reasonable valuation. I could not retrieve its performance data — [VanEck](https://www.vaneck.com/cl/en/news-and-insights/blogs/emerging-markets-equity/indias-garp-investing-edge-overcome-valuation-hurdles/); [Seeking Alpha](https://seekingalpha.com/article/4718524-glin-indias-year-of-the-garp)

### Inferences
- In India, the value leg did most of the work in 2020–2026. Value indices compounded at about 22–35%/yr over 5 years to Dec 2025, while quality indices compounded at about 13–14%. A GARP screen with a meaningful valuation cap would likely have tracked value-like returns in this window. A screen tilted toward growth or quality would have lagged.
- The Growth 50 index (no valuation filter, P/E about 41, beta 1.32) and the MQVLv/AQVLv multifactor indices are good off-the-shelf benchmarks for a home-built GARP. The multifactor indices give similar long-run CAGR with much lower beta (0.72 since 2005).
- Indian quality has a stronger academic premium than in the US, so a GARP variant of "quality + growth + valuation cap" has better Indian theoretical support than a pure PEG.

### Gaps
- No published academic test of PEG / GARP on the Nifty 500 universe was found, and no IIM working paper on PEG specifically.
- I could not retrieve current factsheets for Nifty200 Quality 30, Nifty200 Momentum 30 or Nifty500 Value 50, so since-2005 CAGR, standard deviation and max drawdown are missing for those. The Value 50 factsheet available online is stale (July 2020). The dashboards give only 1Y/3Y/5Y figures, without 10Y or drawdown.
- No AMFI or Value Research dataset was found that isolates "GARP-mandate" mutual funds with 3/5/10-year returns against Nifty 50/500.
- I did not find a Nifty 50 TRI CAGR from April 2005, so the Growth 50 / MQVLv since-2005 CAGRs cannot be compared on a like-for-like start date (the Nifty 50's 12.12% CAGR is since 1995).

## 3. Regime dependence: when does GARP work or fail? How did it do in India 2020–2026?

### Takeaway
GARP results depend on the regime. In the US it behaved like growth during the 1999–2001 bubble and like value afterwards, and its "best strategy" ranking flips with the start date. In India, value's long-run premium came with very deep, multi-year drawdowns (the Nifty500 Value 50 had a 5-year CAGR of -1.9% to July 2020, then about 22–35% after). 2025–2026 was a broad drawdown year in which value and growth/momentum (high-beta) outperformed, while quality and low-volatility lagged.

### Cited Findings
- US: GARP and Growth beat Value in 1989–2001, especially in 1999–2001. After 2001 GARP behaved like Value. With a 2000 start, Value won. With a 2010 start, the market won — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- India value cycle: the Nifty500 Value 50 factsheet as of 31 July 2020 shows TRI returns of -19.56% for 1 year and -1.93% CAGR for 5 years (10.28% since April 2005), with 1-year standard deviation of 33.84% — [NSE factsheet (July 2020 version)](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500_Value50.pdf). By 31 Dec 2025, its 5-year CAGR was 34.50% and 3-year 31.73% — [NSE Dashboard Dec 2025](https://www.niftyindices.com/Index_Dashboard/Index_Dashboard_DEC2025.pdf)
- IIMA value factor (HML) worst drawdown was -64% (Dec 1994 to Feb 2000, during the late-1990s tech boom) and took 7.6 years. Momentum's worst drawdown was -62% in 2000 — [IIMA](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/drawdown.php)
- Quality in India "delivers higher returns in weaker market conditions", has a lower beta, and shows smaller and shorter drawdowns than value, momentum and the market (1995–2021) — [Quantpedia / Jacob et al.](https://quantpedia.com/performance-of-factor-strategies-in-india/)
- 12 months to 30 Sep 2026 (Nifty 50 at -7.09%): Nifty Alpha 50 +11.44%, Nifty500 Growth 50 +9.42%, Nifty200 Value 30 +7.89%, Nifty500 Value 50 +6.89%. Laggards were Nifty200 Quality 30 at -5.42%, MQVLv 50 at -5.04% and Nifty Quality Low-Vol 30 at -6.38% — [NSE Dashboard Sep 2026](https://www.niftyindices.com/Index_Dashboard/Index_Dashboard_SEP2026.pdf)
- Calendar 2025 (1Y to 31 Dec 2025): value led at +16.9% to +20.3%, versus +11.88% for Nifty 50. Momentum (-4.57%) and Alpha 50 (-10.17%) fell. Quality 30 rose +4.68% — [NSE Dashboard Dec 2025](https://www.niftyindices.com/Index_Dashboard/Index_Dashboard_DEC2025.pdf)
- Market P/E context: the Nifty 50 P/E fell from 22.75 (Dec 2025) to 19.36 (Sep 2026). Quality index P/Es were about 25–33, while value indices stayed at about 9–10 — [NSE Dashboards](https://www.niftyindices.com/Index_Dashboard/Index_Dashboard_SEP2026.pdf)
- Revision signals in India behaved differently by regime. Stocks with poor EPS revisions were penalized more in down and neutral markets, and actually outperformed in up-trends (2005–2016) — [S&P DJI Indexology](https://www.indexologyblog.com/2018/02/21/do-earnings-revisions-matter-in-india/)

### Inferences
- Expect GARP built with a hard valuation cap (e.g., PEG < 1 or P/E < sector median) to look like value in India. It should be strong in 2021–2025 and weak in 2015–2020 and in momentum-led bubbles.
- Loosening the valuation cap (PEG 1–2) moves GARP toward the Growth 50 / momentum profile: higher beta (about 1.2–1.3), higher volatility (about 19–21%), and better relative performance in 2026's narrow rally than in 2025.
- Interest-rate regime: no India-specific source tied GARP or factor returns to RBI rate cycles (see Gaps).

### Gaps
- No source quantified GARP or factor performance in India by interest-rate regime (high versus low repo rate), or by FII-flow regime.
- No 2020–2026 calendar-year table for every factor index was retrieved. Only the two dashboard snapshots (Dec 2025 and Sep 2026) and the July 2020 Value 50 factsheet were available.
- No direct measure exists of a "PEG-screen India" portfolio across 2020–2026.

## 4. PEG-based screens versus simpler alternatives (low P/E, high growth, quality, momentum, revisions)

### Takeaway
No head-to-head Indian test of PEG against single factors was found. The indirect evidence ranks simpler or better-documented signals above PEG. In India, momentum (about 11%/yr long-short, 1993–2025), quality (about 0.7–0.9%/month alpha, 1995–2021) and low P/E / value (HML about 6.9%/yr, with recent index CAGRs of about 20%+) each have strong documented premia. Earnings revisions produced 4.6–8.1%/yr excess returns in India (2005–2016, equal-weighted). Pure growth with no valuation cap has done well on NSE indices since 2005 but with high beta.

### Cited Findings
- US: excluding negative-earnings stocks removes most of GARP's edge, and over 2000+ pure value beat GARP — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- India long-short factor CAGRs, 1993–2025: momentum 10.96%, value 6.86%, size -4.01% — [IIMA](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/drawdown.php)
- India quality: growth of INR 100 from 1995 to 2021 was 9,345 for QMJ versus 6,988 for momentum. QMJ has negative value exposure and positive momentum exposure — [Quantpedia / Jacob et al.](https://quantpedia.com/performance-of-factor-strategies-in-india/)
- India earnings revisions (S&P DJI; Dec 2005 to Dec 2016; 3-month change in consensus EPS and 3-month revision diffusion). Equal-weighted top quintiles earned excess CAGR over the universe of 8.1% (diffusion) and 4.6% (EPS change). India was among the three strongest of seven Asian markets. Size bias was not the driver, but sector bias was high, turnover was high, and the effect largely lost significance under cap-weighting. The results are hypothetical backtests — [S&P DJI Indexology](https://www.indexologyblog.com/2018/02/21/do-earnings-revisions-matter-in-india/); [S&P DJI Asia](https://www.indexologyblog.com/2018/02/08/earnings-revision-strategies-in-asia/)
- NSE indices since April 2005 (backtest plus live, as of 30 Sep 2026). TRI CAGR: Nifty500 Multifactor MQVLv 50 19.09% (standard deviation 17.24%), Nifty500 Growth 50 18.53% (23.59%), Nifty500 Quality 50 16.37% (18.16%). Value 50 was 10.28% to July 2020 (27.22% standard deviation) — [NSE factsheets](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500_Growth_50.pdf); [MQVLv](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500MultifactorMQVLv50.pdf); [Quality 50](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500Quality50.pdf); [Value 50 (2020)](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500_Value50.pdf)
- Low P/E at index level (blog-level evidence): buying the Nifty when P/E was below 12 produced average 3-year and 5-year returns of 39.5% and 29% (absolute). This is a holding-period P/E result, not PEG — [Stable Investor](https://stableinvestor.com/2013/08/latest-pe-ratio-analysis-of-indian-stock-markets.html)
- The forward-PEG variant (AAII, US) at 12.9%/yr versus 5.7% for the S&P 500 (1998–May 2023) was the best of the AAII PEG/Lynch screens found. The trailing Lynch GARP screen made 8.0%/yr — [AAII](https://www.aaii.com/journal/article/223803-spotting-value-on-the-move-with-the-peg-ratio)

### Inferences
- For India, a "GARP" signal is probably best built as a composite rather than a ratio. For example: growth (3-year PAT and sales growth, possibly plus FY1 revisions), a valuation cap (P/E or EV/EBIT relative to sector), and a quality gate (ROE/ROCE, leverage). This mirrors the MQVLv-style multifactor index, which had the best since-2005 CAGR per unit of risk among those retrieved.
- The ratio form of PEG is unstable. Small or negative growth denominators produce extreme values, and growth measured over 1 year, 3 years or 5 years changes rankings a lot — [OneTradeJournal](https://onetradejournal.com/glossary/peg-ratio). Rank-based composites avoid this.
- Adding momentum or revisions to GARP (as AAII does) is supported by the Indian evidence: revisions and momentum are strong in India.

### Gaps
- No head-to-head PEG versus low P/E versus growth versus quality backtest on NSE stocks was found.
- I found no India-specific study of forward (analyst-consensus) PEG. Indian analyst coverage is thin below the Nifty 200, a practical limit not quantified here beyond Morgan Stanley's 2018 note that India had more than 2,000 EM stock estimates — [Business Standard](https://www.business-standard.com/amp/article/markets/india-tops-emerging-markets-in-negative-earnings-revision-morgan-stanley-118090900644_1.html)

## 5. Known pitfalls in GARP backtests

### Takeaway
The main documented pitfalls are: (a) how negative and low earnings are handled, which can create or erase the GARP edge; (b) survivorship bias, which is severe in India because many listed firms disappeared; (c) illiquidity and small-cap concentration; (d) turnover and costs for revision- and momentum-augmented variants; (e) weighting choice, since equal-weighted edges shrink under cap-weighting; (f) start-date sensitivity; and (g) look-ahead and data-vintage problems with fundamentals and analyst estimates.

### Cited Findings
- Negative-earnings handling: GARP's US outperformance since 1989 was "substantially" smaller once loss-makers were excluded — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- Start-date sensitivity: the ranking of GARP, Value and the market flips with 1989, 2000 or 2010 start dates — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- Survivorship and illiquidity in India: the IIMA factor study corrects returns for survival bias ("many Indian public companies have disappeared") and excludes illiquid firms so that portfolios are investible — [IIMA working paper](https://web.iima.ac.in/~iffm/legacy/four-factors-India-90s-onwards-IIM-WP-Version-original-Sep13.pdf)
- The size factor in India was negative (-4.01%/yr, about -87% drawdown, 1993–2025), so small-cap concentration from GARP screens is not a free premium in India — [IIMA](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/drawdown.php)
- GARP-labelled Indian products can be about 49% small cap — [Business Today PMS](https://www.businesstoday.in/pms/composite-india-garp-fund-119)
- Turnover and weighting: earnings-revision strategies in India had high turnover, and their excess returns became "much less pronounced" and lost significance when cap-weighted — [S&P DJI Indexology](https://www.indexologyblog.com/2018/02/21/do-earnings-revisions-matter-in-india/)
- Costs used in the US GARP test were 10 bps per trade with monthly rebalancing — [CFA Institute](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- Backtested indices: NSE's Growth 50 (launched 2026), MQVLv 50 (2025) and Quality 50 (2024) all have backtested history from April 2005. Most of each record is therefore pre-launch and subject to design-selection bias — [NSE factsheets](https://www.niftyindices.com/Factsheet/Factsheet_Nifty500_Growth_50.pdf)
- AAII screen returns are hypothetical, price-only and unaudited — [AAII](https://www.aaii.com/journal/article/223803-spotting-value-on-the-move-with-the-peg-ratio)
- Analyst long-term growth estimates are systematically over-optimistic for high-growth firms (La Porta 1996; BGLS 2019), which biases forward PEG — [NBER](https://nber.org/papers/23863)
- PEG values for the same stock vary "wildly" depending on whether growth is trailing, 1-year forward or a 3–5-year CAGR — [OneTradeJournal](https://onetradejournal.com/glossary/peg-ratio)

### Inferences
- Look-ahead bias: Indian annual results are reported up to about 60 days after quarter or year end, and data vendors often store restated figures. A backtest should lag fundamentals by at least the filing deadline and use point-in-time (as-first-reported) data. Analyst-estimate backtests need point-in-time consensus snapshots (e.g., an I/B/E/S-style history), not current estimates applied backwards. This is a standard best practice; no India-specific source quantifying the bias was found.
- For a Nifty 500 universe, use historical index membership at each rebalance date, not current constituents. Otherwise the survivorship bias flagged by IIMA re-enters.
- Use realistic Indian round-trip costs (STT, brokerage, impact) in place of the 10 bps US assumption, especially for monthly rebalancing or revision variants. No sourced Indian cost figure was gathered here.
- Longer holding periods (semi-annual rebalancing like NSE's indices, or the 5-year holds in Auxilia 2019) cut turnover and costs, and fit slow-moving GARP signals better than monthly rebalancing.

### Gaps
- No study was found that quantifies how much look-ahead or restatement bias inflates Indian fundamental-factor backtests.
- No sourced Indian transaction-cost or impact-cost estimate for Nifty 500 mid/small caps was gathered.
- No source quantified Indian analyst-coverage breadth by index tier.
