# Return effects of market holidays and holiday-shortened trading weeks (India focus)

Scope note: about 22 tool calls. Most Indian sources were available only as abstracts or summaries. Effect sizes for the Indian academic papers are therefore mostly missing. Broker and press figures for Diwali are secondary and not from an official dataset. Global evidence is labelled [GLOBAL] or [US].

## 1. The pre-holiday effect: size and decay

### Takeaway
[US/GLOBAL] In the classic US sample (1963–82), pre-holiday returns averaged 9–14 times a normal day's return. Since about 1990 the effect has largely disappeared in large caps and survives mainly in small caps. In India, most index-level studies find no reliable pre-holiday effect. One 2025 paper (FIIB Business Review) is the exception and claims persistence across NSE and BSE indices.

### Cited Findings
- [US] Ariel (1990), *Journal of Finance* 45(5): on the trading day before a holiday, mean returns averaged 9–14 times the mean of the remaining days. More than one third of the market portfolio's total return over 1963–82 was earned on the roughly 8 pre-holiday days each year. — [IDEAS/RePEc](https://ideas.repec.org/a/bla/jfinan/v45y1990i5p1611-26.html)
- [US] Ko & Yang (Critical Finance Review, 2024 replication) confirm Ariel's result in-sample. Over 1983–2019 the pre-holiday effect exists only among small firms. For large firms the difference between pre-holiday and other days became insignificant, especially after 1990. — [Critical Finance Review / nowpublishers](https://nowpublishers.com/article/Details/CFR-0111); [paper PDF](https://cfr.ivo-welch.info/published/papers/ko2021pre.pdf)
- [US] Quantpedia, summarising Hansen & Lunde: pre-holiday returns were more than 10 times normal-day returns. The DJIA pre-holiday daily return was 0.239% (Table 12 of the source paper, 1896–2002), giving about 6.4% a year when combined with cash. Calendar effects diminished from the late 1980s, except in small-cap indices. Maximum drawdown was −13.62%. — [Quantpedia](https://quantpedia.com/strategies/pre-holiday-effect)
- [Spain] Meneu & Pardo (2004), *Journal of Empirical Finance* 11(2): high abnormal returns on the trading day before holidays for the largest Spanish stocks. The effect is not caused by US or German market calendars. — [IDEAS](https://ideas.repec.org/a/eee/empfin/v11y2004i2p231-246.html); [Univ. Valencia record](https://producciocientifica.uv.es/documentos/5eb2d0b329995223401a9bc0?lang=en)
- [GLOBAL] Kim & Park (1994) are cited in secondary sources as finding pre-holiday effects in the US, UK and Japan. I did not retrieve the original paper. — [Search summary of CEE study, MPRA 41625](https://mpra.ub.uni-muenchen.de/41625/1/MPRA_paper_41625.pdf)
- [GLOBAL/CEE] In Central and Eastern European markets the pre-holiday effect was strongest in the early years of market operation and has declined over time, which the authors attribute to improving efficiency. — [MPRA 41625](https://mpra.ub.uni-muenchen.de/41625/)
- [GLOBAL, 20 countries, 2007–2017] Charoenying et al. (2020): developed markets show a significant CAAR only at t−2, before the holiday. Developing markets show significant CAAR across the whole t−1 to t+4 window. The countries are not named, so it is unclear whether India is included. — [WMS Journal of Management](https://so06.tci-thaijo.org/index.php/wms/article/view/245362)
- [INDIA] Lu & Patel (2016), *Economics Bulletin* 36(2): the pre-holiday effect was "completely missing" on BSE indices. — [IDEAS](https://ideas.repec.org/a/ebl/ecbull/eb-16-00286.html)
- [INDIA, 1992–2018] Agarwal, Dahiya & Gupta (SRCC Business Analyst, 2019): no pre-holiday effect in India (or Singapore). No holiday showed significant pre-holiday returns, even at the 10% level. — [SRCC](https://www.srcc.edu/node/3960)
- [INDIA, 2002–2014; Nifty, Sensex and the 500 indices] An inflibnet thesis found weekday returns and volatility higher than on pre- and post-holiday days. It concludes there is no holiday effect in any period or index. — [Inflibnet](https://sgbeta.inflibnet.ac.in/items/1960e11b-8db2-4cda-abc2-0605ba4cf29b)
- [INDIA] Tadepalli, Jain & Metri (2025), *FIIB Business Review* 14(2): ARIMAX on all major NSE and BSE market-cap and sectoral indices, with dummies for days before exchange holidays. They find the anomaly "significantly persistent among most of the Indian market indices", including after market reforms. The abstract gives no sample period or effect sizes. — [IDEAS](https://ideas.repec.org/a/sae/fbbsrw/v14y2025i2p173-183.html)

### Inferences
- The Indian evidence conflicts: 3 studies find no pre-holiday effect and 1 (2025, ARIMAX) finds persistence. Differences in method (OLS dummies vs ARIMAX), sample and index choice probably explain the split. No study I found shows a large, robust pre-holiday premium on Nifty or Sensex after 2010.
- Global evidence suggests that any residual effect is more likely in small and mid-cap indices than in Nifty 50.

### Gaps
- Lakonishok & Smidt (1988), DJIA 1897–1986: I could not retrieve their exact pre-holiday versus normal-day numbers from a source here.
- I found no exact Indian pre-holiday return in basis points per day for 2010–2026. I could not obtain the FIIB paper's sample period or coefficients (full text at journals.sagepub.com/doi/10.1177/23197145211016894).

## 2. The post-holiday effect

### Takeaway
In India, the post-holiday effect appears more often than the pre-holiday effect, which reverses the US pattern. It was strong on BSE indices around the global financial crisis, appears mainly as a New Year effect over 1992–2018, and for 2020–22 is concentrated after Hindu and Sikh holidays. [US] Days after a holiday tend to show low returns.

### Cited Findings
- [INDIA] Lu & Patel (2016): "very strong" post-holiday effects in most BSE indices, which became stronger during the financial crisis. The sample period and magnitudes were not available in the abstract. — [IDEAS](https://ideas.repec.org/a/ebl/ecbull/eb-16-00286.html)
- [INDIA, 1992–2018] Agarwal et al.: the only significant holiday effect was a post-New-Year effect, at 5% significance. — [SRCC](https://www.srcc.edu/node/3960)
- [INDIA, July 2020–Dec 2022, Sensex and Nifty 50, GARCH/PGARCH/ARIMAX] Sing, Ropuii & Singh (2025), *Indian Journal of Finance* 19(3):
  - Christian and Jain holidays show significant pre-holiday returns.
  - Hindu and Sikh holidays show stronger post-holiday effects.
  - Islamic holidays show no significant effect.
  - Volatility clustering differs by holiday.

  The page gives no coefficients. — [Indian Journal of Finance](https://indianjournalofentrepreneurship.com/index.php/IJF/article/view/174848)
- [US, 1990–2020, DJIA, S&P 500, Russell 2000, NASDAQ] Dumitriu & Stefanescu (2020): returns are low on days t+1 and t+2 after holidays. The effect is clearer in calm periods and strongest in small caps. — [MPRA 100463](https://mpra.ub.uni-muenchen.de/100463)

### Inferences
- In India, a tilt toward buying ahead of or shortly before major Hindu festival closures and holding through the post-holiday days fits the 2020–22 GARCH result. However, the sample is short (2.5 years) and has no reported magnitudes, so it needs in-house backtesting.

### Gaps
- I found no Indian study giving post-holiday returns in basis points by holiday (Holi, Eid, Independence Day, Republic Day) for 2010–2026.

## 3. Holiday-shortened weeks (four-day weeks vs five-day weeks)

### Takeaway
[US only] Practitioner data show S&P 500 holiday weeks averaging about 0.38% since 2000, against 0.06% for full weeks. The gain comes from weeks where Friday is the holiday, not Monday. I found no Indian study of whole holiday-shortened weeks, so this is a gap the project could fill with its own data.

### Cited Findings
- [US] Schaeffer's Research (2023): since 2000 the S&P 500 averaged +0.38% in holiday-shortened weeks versus +0.06% in full weeks. The outperformance comes from weeks with Friday off. Weeks with Monday off did not outperform five-day weeks. Presidents' Day week (Monday off) has averaged −0.24% since 2000, with 52% of weeks positive. — [Schaeffer's 2023](https://www.schaeffersresearch.com/content/analysis/2023/02/15/buy-these-20-stocks-presidents-day-week)
- [US] Schaeffer's earlier figure, since 1971: short weeks averaged 0.34% against 0.13% for typical weeks. — [Schaeffer's 2018](https://www.schaeffersresearch.com/content/analysis/2018/02/14/25-stocks-to-buy-this-week)
- [US] Schaeffer's, July 4 weeks: the S&P 500 did best when the holiday fell on a Monday, averaging +0.81% for the week. This partly contradicts the Friday-off finding above. — [Schaeffer's 2016](https://www.schaeffersresearch.com/content/analysis/2016/06/29/indicator-of-the-week-will-stocks-boom-after-independence-day)
- [US] Dumitriu & Stefanescu (2020), "extended holiday effect": high abnormal returns 3–4 trading days before public holidays and low returns 1–2 days after. Most of the effect falls within the shortened week, before the holiday. — [MPRA 100463](https://mpra.ub.uni-muenchen.de/100463)

### Inferences
- If the US pattern carries over, an Indian four-day week whose holiday falls late in the week (Thu or Fri) may outperform, while one whose holiday falls on Monday may not. The day of the week of the holiday should be a variable in any NSE backtest.
- Schaeffer's figures are not peer-reviewed and use small samples (a few holiday weeks per year).

### Gaps
- I found no Indian (NSE/BSE) study comparing cumulative returns of four-day and five-day weeks.

## 4. India-specific: Diwali, Muhurat trading, the Samvat year and festival sentiment

### Takeaway
The Muhurat session (one hour) is usually slightly positive against the previous close: about 8 of 10 sessions in 2015–2024, with an average of about 0.5% and typical moves of 0.1–0.9%. However, Nifty almost always gaps up at the open and then closes below its open (13 of 14 sessions in 2008–2021), so buying at the Muhurat open has lost money. Academic tests (1992–2018) find no significant pre- or post-Diwali effect. Samvat-year returns are simply annual returns and carry no special signal.

### Cited Findings
- Agarwal et al. (India, 1992–2018): Diwali returns were insignificant at the 5% and 10% levels, both before and after the holiday. — [SRCC](https://www.srcc.edu/node/3960)
- Forum table of Nifty Muhurat sessions, 2008–2021 (unverified; a commenter flagged data errors):
  - 13 of 14 sessions gapped up versus the previous close.
  - 13 of 14 sessions closed below their open (red candle). 2008 was the only green candle.
  - Close versus previous close was positive in 10 of 14 sessions.
  - Diwali-to-Diwali was negative in 3 of 14 years (2008: −55.7%, 2011: −17.5%, 2015: −2.0%).

  — [TradingQnA](https://tradingqna.com/t/nifty-always-forms-a-daily-red-candle-from-last-14-years-on-muhurat-session/138281)
- Muhurat session returns by year (secondary sources):

  | Year | Return |
  |---|---|
  | 2008 | ~+6.35% |
  | 2009 | −0.01% |
  | 2010 | +0.49% |
  | 2011 | +0.20% |
  | 2012 | −0.29% |
  | 2013 | +0.48% |
  | 2014 | +0.23% |
  | 2015 | +0.54% |
  | 2016 | −0.14% |
  | 2017 | −0.63% |
  | 2018 | +0.65% |
  | 2023 | +0.52% |

  The average over the last decade is about 0.53%, with 8 of 10 green for 2015–2024. — [Groww](https://groww.in/blog/muhurat-trading-over-the-last-decade); [Share.Market](https://share.market/buzz/insights/muhurat-trading-2025-date-timings-nifty-50-performance-analysis); [IANS](https://ianslive.in/diwali-2024-muhurat-trading-date-time-and-history--20241030180006)
- 2005–2024 summary: Muhurat closed higher in 14 of 20 years, with typical moves under 1%. Nifty 12 months later was positive in 17 of 20 years, but 6-month results were scattered. The session has no reliable predictive power for the next six months. — [5paisa](https://5paisa.com/blog/can-stock-markets-sustain-diwali-rallies-heres-what-history-indicates); [Angel One](https://www.angelone.in/news/personal-finance/what-does-history-say-about-muhurat-trading)
- Samvat-year returns:
  - Nifty averaged about 12.5% a year over Samvat 2072–2081. — [PL Capital](https://www.plindia.com/blogs/diwali-muhurat-trading-2025-pl-capital-guide/)
  - Samvat 2081 (Diwali 2024 to Diwali 2025) returned about 6% according to IANS, or about 4% for Nifty (3% for Nifty 500) according to Business Standard. The sources conflict. — [IANS](https://ianslive.in/nifty-sensex-end-samvat-2081-on-strong-note-with-6-pc-return--20251020181107); [Business Standard](https://www.business-standard.com/markets/news/diwali-2025-bse-ge-vernova-surged-over-60-in-each-of-last-3-samvat-years-125101400592_1.html)
  - In the five Samvats to 2018, only 2 delivered double-digit Sensex returns: 2014 (+26.4%) and 2017 (+16.6%). — [Business Standard 2018](https://www.business-standard.com/amp/article/markets/only-2-of-past-5-samvats-gave-double-digit-returns-2074-was-lackluster-118110700031_1.html)
- "Is There Any Diwali Effect?" (*Indian Journal of Finance*): paired t-test over 8 days before and 7 days after Muhurat on S&P CNX Nifty, plus EGARCH. I could not retrieve the findings. — [i-scholar](https://mail.i-scholar.in/index.php/ijf/article/view/202341)
- Hindu and Sikh holidays show post-holiday effects in 2020–22; Islamic holidays (Eid) show none. — [Indian Journal of Finance 2025](https://indianjournalofentrepreneurship.com/index.php/IJF/article/view/174848)

### Inferences
- The Muhurat "effect" is mostly a symbolic gap-up at the open followed by intraday fading. Long-only positioning before Diwali captures the small gap, not the session. The 12-month positive rate (17 of 20) matches Nifty's base rate of positive years, so it is not a Diwali signal.
- Which Indian effects survive after 2010: the evidence is weak. Post-holiday effects (BSE during the crisis; Hindu and Sikh holidays in 2020–22) and the FIIB persistence claim are the only candidates. Diwali-specific effects are not significant.

### Gaps
- I found no study isolating Holi, Independence Day or Republic Day returns with effect sizes. Eid is covered only as "Islamic holidays: not significant" (2020–22).
- I found no NSE, BSE, RBI or SEBI research publication on holiday effects. Zerodha Varsity and Capitalmind did not surface with holiday-return data.
- An official, complete Muhurat table (2019, 2021, 2022, 2024, 2025) is not verified.

## 5. Cross-section: large vs small caps and sectors in India

### Takeaway
I found no Indian evidence that separates large-cap from small-cap holiday effects with numbers. [US] evidence consistently shows that the remaining pre-holiday and extended-holiday effects sit in small caps.

### Cited Findings
- [US] After 1990 the pre-holiday effect exists only in small firms. — [CFR / Ko & Yang](https://nowpublishers.com/article/Details/CFR-0111)
- [US] The extended holiday effect is strongest in the Russell 2000 (small caps). — [MPRA 100463](https://mpra.ub.uni-muenchen.de/100463)
- [GLOBAL] Calendar effects persist mainly in small-cap indices after the late 1980s. — [Quantpedia / Hansen & Lunde](https://quantpedia.com/strategies/pre-holiday-effect)
- [INDIA] The FIIB 2025 paper covers sectoral and market-cap indices and says most show persistence. The abstract does not say which. — [IDEAS](https://ideas.repec.org/a/sae/fbbsrw/v14y2025i2p173-183.html)

### Inferences
- Any NSE strategy should test Nifty Smallcap 250 and Midcap 150 separately from Nifty 50.

### Gaps
- I found no Indian results by sector or by size.

## 6. Explanations

### Takeaway
The main explanations are four:
- holiday mood and optimism;
- short-sellers closing positions before the market closes;
- small investors' reluctance to buy before holidays, which leaves order flow dominated by buyers (Meneu & Pardo);
- low liquidity.

The evidence is suggestive rather than conclusive.

### Cited Findings
- Meneu & Pardo (2004, Spain): the effect is linked to small investors' reluctance to buy on pre-holiday days, which raises the average size of bid orders. — [IDEAS](https://ideas.repec.org/a/eee/empfin/v11y2004i2p231-246.html)
- Short-sellers closing risky positions before holidays, and better investor mood raising optimism, are the commonly cited behavioural explanations. Lower liquidity on pre-holiday days also contributes. — [Quantpedia](https://quantpedia.com/strategies/pre-holiday-effect)
- Investor optimism and liquidity needs are the two main explanations in the literature. — [MPRA 41625](https://mpra.ub.uni-muenchen.de/41625/)
- Ariel (1990) tested possible causes ("Existence and Evidence on Possible Causes"). The full text was not retrieved. — [IDEAS](https://ideas.repec.org/a/bla/jfinan/v45y1990i5p1611-26.html)

### Inferences
- In India, the post-holiday tilt could reflect news (global markets and corporate disclosures) that builds up during closures. This is plausible, especially when Indian holidays do not coincide with US ones, but I found no source testing it.

### Gaps
- I found no Indian test of the information-accumulation or short-covering explanations. Indian short-selling in the cash market is limited (SLB), so short-covering is likely less relevant. This is an inference, not a sourced claim.

## 7. Tradability after costs (India)

### Takeaway
A one-day Nifty pre- or post-holiday trade must clear a round trip of roughly 0.2% of value for delivery (STT of 0.1% on each side alone). The documented Indian effects are either absent or unquantified, and Muhurat gains average about 0.5%. Cash-delivery holiday trades therefore look marginal at best. Index futures are much cheaper to trade, though STT rose in October 2024 and possibly again in 2026.

### Cited Findings
- Equity delivery STT is 0.1% on both buy and sell. Intraday STT is 0.025% on the sell side. Brokerage for delivery at Zerodha is zero. — [Zerodha Z-Connect](https://zerodha.com/z-connect/?p=391776); [Upstox](https://upstox.com/?p=33)
- From 1 October 2024, futures STT rose from 0.0125% to 0.02% and options STT from 0.0625% to 0.1% of premium. Futures exchange transaction charges fell to 0.00173%. — [Zerodha bulletin](https://zerodha.com/marketintel/bulletin/391488/revision-in-transactions-charges-from-1st-october-2024)
- A third-party calculator lists Budget 2026 STT at 0.05% (futures, sell side) and 0.15% (options). This is not verified against an official source. — [sum.money](https://sum.money/in/brokerage-calculator/)
- [US] Quantpedia's indicative pre-holiday strategy return is about 6.4% a year (DJIA, 1896–2002), with the effect diminished since the late 1980s. — [Quantpedia](https://quantpedia.com/strategies/pre-holiday-effect)

### Inferences
- With about 15 NSE trading holidays a year and costs of roughly 0.2% round trip in delivery, a delivery-based holiday strategy needs about 3% a year in gross edge just to break even. That is implausible given the Indian evidence. Index futures cost roughly 0.02–0.05% STT plus impact, so they are the only realistic vehicle.

### Gaps
- I found no Indian study that reports holiday-strategy returns net of STT and brokerage.
- The 2026 STT rates need confirmation from official Budget documents.
