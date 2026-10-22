# Weekend Effects on Market Microstructure, Volatility and Derivatives Pricing (India / NSE focus, as of Oct 2026)

Note on method: about 17 search and fetch calls. Several primary pages (nseix.com, the India VIX paper) timed out, so some points rest on search-result summaries of abstracts rather than full texts. These are flagged where they occur. Evidence labelled **[US/Global]** is not India-specific.

## Weekend variance: why weekend close-to-open variance is far below three days of trading variance, and the size of the Monday gap

### Takeaway
**[US/Global]** French & Roll (1986) found that volatility comes mostly from trading itself, mainly the release of private information, rather than from calendar time. A weekend therefore adds far less variance than three trading days. No source found gives NSE-specific statistics on the size of the Monday gap compared with ordinary weekday overnight gaps. That has to be computed from NSE OHLC data.

### Cited Findings
- **[US]** French & Roll (1986, JFE), "Stock Return Variances: The Arrival of Information and the Reaction of Traders". Returns are much more volatile during exchange trading hours than during non-trading hours. As summarised in search results, open-to-close variance on an average day is more than six times the weekend close-to-open variance, although the weekend is roughly eleven times longer. — [French & Roll 1986 PDF](https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf)
- **[US]** French & Roll weigh three explanations: public information, private information, and pricing errors/noise. Exchange closures on weekdays with an unchanged public-news flow (the 1968 NYSE Wednesday closures) still reduce volatility, so public news is not the main driver. Pricing errors play a small part, and they conclude that private information revealed through trading is the main source. — [French & Roll 1986 PDF](https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf); [EFMA 2006 paper citing it](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2006-Madrid/papers/689152_full.pdf)
- **[US]** Using variance ratios and autocorrelations, French & Roll estimate that only about 4–12% of daily return variance comes from noise trading (mispricing that later reverses). — [EFMA 2006 paper](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2006-Madrid/papers/689152_full.pdf)
- **[US/Global]** Later work (Zdorovtsov, EFMA 2006) argues that its results also support the public-information hypothesis, so French & Roll's dismissal of public information is disputed. — [EFMA 2006 paper](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2006-Madrid/papers/689152_full.pdf)
- **[US]** Boston Fed working paper 98-6, "Weekends can be rough: revisiting the weekend effect in stock prices", is a follow-up on weekend return effects. — [Boston Fed WP 98-6](https://www.bostonfed.org/-/media/Documents/Workingpapers/PDF/wp98_6.pdf); [IDEAS listing](https://ideas.repec.org/p/fip/fedbwp/98-6.html)
- **[US]** Overnight versus intraday: Lou, Polk & Skouras (JFE 2019, "A tug of war") show that across 14 strategies, profits are earned either entirely overnight (momentum, reversal) or entirely intraday, usually with opposite signs. They link this to institutions that trade during the day against momentum. The overnight–intraday spread varies by about 2% per month. — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/87481); [Working-paper PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- **[US]** Cliff, Cooper & Gulen (study covering 1993–2006) find that US equity returns accrue mostly in non-trading hours. AP coverage reported that holding stocks overnight was more profitable than holding them during the day. A related finding: QQQQ's geometric close-to-open premium for 1999–2006 was about +23.7%, against about −23.3% open-to-close. — [AP/KSL coverage](https://www.ksl.com/article/7287966); [Kelly & Clark 2011, J. Asset Mgmt](https://ideas.repec.org/a/pal/assmgt/v12y2011i2d10.1057_jam.2011.2.html); [Alpha Architect summary](https://alphaarchitect.com/2015/02/overnight-momentum-vs-intraday-momentum/)
- **[India]** An NSE-hosted research paper (Paper 39) split Nifty returns for 1999–2001 into daytime and overnight components to study volatility spillover between Nifty and NASDAQ. Overnight Nifty moves partly reflect US trading. — [NSE Research Paper 39](https://nsearchives.nseindia.com/content/research/Paper39.pdf)
- **[India]** A pre/post rolling-settlement study of Nifty 50 found a significant "open jump effect" and a persistent end-of-session effect in intraday returns. — [i-scholar abstract](https://i-scholar.in/index.php/Ajm/article/view/179374)
- **[India]** No source found gives Monday-specific Nifty gap statistics. The nearest is a TradingQnA post: over 20+ years, Nifty opened down more than 1% on 82 occasions (Bank Nifty 218), with an average 0.32% return from going long at the open. It has no day-of-week breakdown. — [TradingQnA](https://tradingqna.com/t/trading-the-gap-how-does-one-trade-nifty-bank-nifty-during-gap-down-and-gap-up-days/78838)

### Inferences
- If weekend variance were proportional to calendar time, a Friday-close to Monday-open move would carry about 3x the variance of a weekday overnight gap. The French & Roll evidence implies the true multiple is much smaller. In Indian markets Gift Nifty and US Friday trading carry part of the weekend's information, yet nothing trades on Saturday or Sunday, so news from those two days lands entirely in Monday's opening auction.
- Overnight drift (Cliff/Cooper/Gulen; Lou/Polk/Skouras) suggests weekend gaps also have a mean component, not only variance. Whether this holds for Nifty has not been verified.

### Gaps
- No primary NSE study measuring the ratio of Monday-open gap variance to Tuesday–Friday overnight gap variance. The repository's own data (Friday close to Monday open versus other close-to-open moves) is the obvious way to fill this.
- The commonly quoted French & Roll figure (weekend variance only about 10–11% above a single weekday's) could not be checked against the full text here.
- Claims on Indian blogs that "Nifty returns come overnight" (e.g. multibagg.ai) were found but are not peer-reviewed and were not verified.

## Friday and Monday volume and volatility patterns in India

### Takeaway
The best NSE evidence (Badhani & Kavidayal, 1995–2005) shows Monday volume significantly lower and Monday volatility consistently higher. Day-of-week return effects are unstable across sample periods and largely disappeared after T+2 rolling settlement. India VIX shows a positive Monday effect, meaning implied volatility rises at the start of the week.

### Cited Findings
- **[India]** Badhani & Kavidayal (2008, *Finance India*), NSE 1995–2005: "On Monday the average trading volume is significantly low and the price volatility is high consistently across the entire sample period." Monday and Tuesday returns were low but not statistically different in the recent sub-period. — [Inflibnet handle](https://gnanaganga.inflibnet.ac.in:8443/jspui/handle/123456789/10797)
- **[India]** Srinivasan & Kalaivani (2013), GARCH models on NSE and BSE for 1997–2012, find day-of-week effects in both returns and volatility, with positive Monday and Wednesday return effects. — [MPRA 46805](https://mpra.ub.uni-muenchen.de/46805)
- **[India]** Sen (Nifty, GARCH-M): the day-of-week return effect disappears after T+2 rolling settlement, but a significant effect on conditional volatility remains, especially on Tuesday. — [publishingindia PDF](https://www.publishingindia.com/storage/PDFBrochures/1824.pdf)
- **[India]** Kothari, Singh & Patra (2017; NSE and BSE indices, 2005–2014): Monday volatility was significant only for the BSE small-cap index, and ANOVA found no day-of-week difference across indices. — [Management Prudence Journal](https://publishingindia.com/archive/mpj/the-calendar-anomalies-in-indian-stock-market-a-special-reference-to-nse)
- **[India]** India VIX studies (around 2014–2015) find a strong positive Monday effect and negative Tuesday/Thursday (or Wednesday) effects in India VIX, so expected volatility tends to rise on Monday and ease later in the week. — [VGTU BTP: "The behavior of option's implied volatility index: a case of India VIX"](https://journals.vilniustech.lt/index.php/BTP/article/view/8279); [IUP "Day-of-the-Week Effect in Fear Gauge"](https://www.iupindia.in/1701/Applied%20Finance/Day_of_the_Week_Effect.html)
- **[India]** A 2018 study of Nifty indices found strong evidence of a positive weekend effect and a negative Tuesday effect in volatility. — reported in search summary alongside [Zenodo record 817228](https://zenodo.org/records/817228) (full text not verified)

### Inferences
- The India VIX Monday rise fits the mechanics: weekend-depressed IV (see options section) gets re-marked on Monday, and Monday's realised volatility is higher because two days of news are incorporated at the open.
- All of these studies predate weekly-expiry dominance (2019 onward) and the move to Tuesday expiry (Sept 2025). Monday is now "expiry eve" for Nifty, which very likely changes Monday volume patterns in F&O; equity cash volume may still follow the old pattern.

### Gaps
- No recent (post-2020) published study of NSE Friday and Monday volumes, and no data on Monday-morning intraday volume or volatility profiles specifically. Volume per day of week could be computed from NSE bhavcopy data.
- No source on whether Friday volume is lower in India (the US literature reports this; I did not find an Indian equivalent).

## Weekend news flow in India and global weekend events: Saturday results, weekend Budgets, and the Monday reaction

### Takeaway
Several large Indian companies, notably HDFC Bank, regularly report on Saturdays, and the Union Budget has been presented on weekends (Saturday 2015 and 2025; Sunday 1 Feb 2026). For weekend Budgets NSE holds a special live session, so the weekend news trades the same day. For Saturday results the full reaction comes at Monday's open, and moves of 2–5% in a Nifty heavyweight follow.

### Cited Findings
- **[India]** HDFC Bank reported Q1 FY27 results on Saturday 18 July 2026 (profit about ₹19,060 cr, up about 5% YoY; NIM at a record-low 3.26%). On Monday the shares fell up to 5.41% intraday to ₹777.50 and were down 4.41% in morning trade. — [Kotak Neo](https://www.kotakneo.com/news/stocks/hdfc-bank-q1-results-shares-fall-after-earnings/); [Upstox](https://upstox.com/news/market-news/stocks/hdfc-bank-q1-results-trigger-5-5-selloff-analysts-highlight-key-positives-and-concerns/article-197184/); [Univest](https://univest.in/blogs/hdfc-bank-share-price-falls-q1-results-20-july-2026)
- **[India]** Earlier HDFC Bank weekend results produced Monday rises: over 2% after the July 2025 results, and over 2% to a one-year high after Q4 FY26 (April 2026). — [The Week, July 2025](https://www.theweek.in/wire-updates/business/2025/07/21/dcm4-biz-stocks-hdfc-bank.html); [Outlook Business](https://www.outlookbusiness.com/markets/hdfc-bank-shares-climb-over-2-after-q4-earnings)
- **[India]** Union Budget 2026 was presented on Sunday 1 February 2026 at 11 am. NSE and BSE ran a full live session (pre-open 9:00–9:08, normal 9:15–15:30) with equity, F&O and commodity derivatives open. BSE did not run its T+0 or auction sessions. Reports describe this as the first Sunday Budget since 2000. — [ETV Bharat](https://www.etvbharat.com/en/business/stock-market-update-bse-nse-to-conduct-regular-trading-session-on-budget-day-enn26013103011); [IANS](https://ianslive.in/indian-stock-exchanges-to-remain-open-on-sunday-for-union-budget-2026--20260116180042); [Swastika](https://www.swastika.co.in/big-budget-day/budget-2026-special-trading-session-what-investors-must-know-about-the-rare-sunday-market)
- **[India]** Budget 2025 (1 Feb 2025) was presented on a Saturday, and so was Budget 2015, both with special sessions. Sources disagree on Budget-2026 settlement: one says settlement was on 2 February. — [Swastika](https://www.swastika.co.in/big-budget-day/stock-market-open-on-1-february-2026-what-union-budget-2026-day-means-for-investors); [Jainam guide](https://www.jainam.in/blog/special-trading-session-on-union-budget/)
- **[India/Global]** Nifty's overnight returns have been shown to reflect US (NASDAQ) daytime trading (1999–2001 data). After the NSE close on Friday the US session still trades, so its move is reflected in Nifty only at Monday's open, or partly in Gift Nifty's Friday night session. — [NSE Research Paper 39](https://nsearchives.nseindia.com/content/research/Paper39.pdf)

### Inferences
- Weekend Budget sessions remove the "weekend" for that event. The market prices the Budget live, and Monday then behaves more like a normal second day.
- Saturday results concentrate single-stock gap risk into Monday's pre-open auction (9:00–9:08). Because HDFC Bank is a top Nifty and Bank Nifty weight, its Saturday results also feed into index gaps.
- US Friday moves (US close is about 1:30–2:30 am IST Saturday) fall partly inside Gift Nifty's second session, which ends around 2:45 am IST, so Gift Nifty's Friday-night print captures most of the US Friday session.

### Gaps
- No systematic count of how many NSE-listed companies report on weekends, and no event study of Monday reactions to weekend results compared with weekday results.
- No compiled data on government policy announcements timed for weekends (e.g. GST Council or RBI weekend actions) or on Nifty's average Monday reaction to them.
- Market reaction on Budget 2025 (Saturday) and Budget 2026 (Sunday) sessions and the following Mondays was not retrieved.

## Gift Nifty (NSE IX): hours, weekend status, and how well it predicts Monday's open

### Takeaway
Gift Nifty trades about 21 hours on weekdays in two sessions and does not trade on Saturday or Sunday. Its Friday late session runs past the US close, so it captures US Friday news. No rigorous large-sample study measures its accuracy in predicting Nifty's open, Monday's in particular. One small academic study claims about 95% directional agreement but is internally inconsistent.

### Cited Findings
- **[India]** Most sources give two sessions: 6:30 am–3:40 pm IST and 4:35 pm–2:45 am IST (next day), about 21 hours. No trading on weekends or NSE IX holidays. — [Kotak Securities](https://www.kotaksecurities.com/indices/global-indices/sgx-niftysgx-nifty); [Rupeezy](https://rupeezy.in/blog/what-is-gift-nifty); [Upstox](https://upstox.com/gift-nifty)
- **[India] Conflicting:** MNCL gives Session 1 as 6:30 am–11:30 pm and Session 2 as 11:30 pm–4:00 am IST, also about 21 hours, Monday–Friday, and states "NSE IX does not trade on Saturdays or Sundays." NSE IX holidays may differ from NSE's. — [MNCL](https://www.mnclgroup.com/gift-nifty-trading-hours). The official nseix.com page could not be fetched (timeout), so the exact split is unverified. The 6:30–15:40 / 16:35–02:45 schedule is the most widely cited.
- **[India]** Indian resident retail investors generally cannot trade Gift Nifty because of LRS (Liberalised Remittance Scheme) restrictions. — reported in search results summarising [Kotak / Sahi explainers](https://www.sahi.com/blogs/sgx-nifty-gift-nifty-explained)
- **[India]** IMDR Journal 2023-24: claims Gift Nifty "determines" the Nifty 50 spot open about 95% of the time, but its sample is only Jan–Jun 2023, it also reports that the correlation is inconsistent, and it notes much inconsistency between gap-ups and gap-downs. — [IMDR Journal p.269](https://imdr.edu/public/IMDR_JOURNAL_2023_24_Updated/files/basic-html/page269.html)
- **[India] Practitioner view:** Gift Nifty is a probability indicator, not a deterministic one. Divergence comes from different hours, a different participant mix, and domestic news. Implied gaps under about 50 points are effectively flat, and the signal is most reliable when the implied gap is large. — [IPS News](https://ipsnews.net/business/2025/12/16/gift-nifty-vs-nifty-50-what-it-signals-before-the-market-opens-and-what-it-doesnt/?amp=1); [MNCL guide](https://www.mnclgroup.com/how-gift-nifty-predicts-nifty-50-opening); [Belong blog](https://getbelong.com/blog/gift-nifty-as-an-early-indicator/)
- **[India]** A TradingQnA thread suggests testing this by comparing the 9:00 am Gift Nifty print with the Nifty open. Historical intraday Gift Nifty data is harder to obtain. — [TradingQnA](https://tradingqna.com/t/gift-nifty-vs-nifty-open/176497)

### Inferences
- On a normal weekday, Gift Nifty's 6:30 am session sees Asian markets and the overnight US close before Nifty's 9:15 open. For Monday, Gift Nifty's last print is Friday night (about 2:45 am Saturday) and it reopens at 6:30 am Monday. Saturday/Sunday news (HDFC results, weekend policy, geopolitical events) therefore reaches Gift Nifty only about 2h45m before NSE's open, giving a shorter price-discovery window than weekday overnights. **Recommendation for analysis:** test Gift Nifty's Friday-late close against Monday's Nifty open, and compare that with its Monday 9:00 am print. The gap between the two measures the pure weekend-news component.
- Gift Nifty prices include a futures basis (cost of carry plus the contract roll), so a raw "Gift Nifty minus Nifty close" overstates the implied gap by the basis.

### Gaps
- No published accuracy statistics for Friday-close Gift Nifty against Monday's Nifty open.
- Official NSE IX session times could not be verified (site timeout). Confirm on nseix.com.

## Options: weekend theta, Friday premium selling, Friday IV, and the weekend in the Tuesday-expiry cycle

### Takeaway
Indian practitioners (Sensibull) describe sellers "pre-pricing" weekend decay: IV and premiums are pushed down into Friday, so a Friday-afternoon seller captures roughly one day of theta, not three, and gives part back on Monday when IV rebounds. **[US]** Jones & Shemesh (JF 2018) show that equity option returns are significantly negative over weekends, consistent with option prices that do not fully account for low weekend variance. With Nifty expiring on Tuesday since 1 Sep 2025, the weekend now sits immediately before Monday "expiry eve", which is when theta and gamma are largest.

### Cited Findings
- **[India]** Sensibull, "The Weekend Effect": sellers try to collect decay over three nights (Fri, Sat, Sun). Heavy selling pushes option prices and IV down into the weekend, and IV usually recovers close to normal on the next trading day. — [Sensibull](https://blog.sensibull.com/2017/12/26/the-weekend-effect/)
- **[India]** Sensibull worked example (Nifty Dec-2017 10500 PE, Fri 22 Dec to Tue 26 Dec, a Christmas long weekend, Nifty futures +1 pt): the premium fell 46 to 36.25 (−9.7). Theta of about 5.1/day over about 3.75 days implied −19.1, but IV rose 2.3 points × vega 4.4 = +10.1, giving about −9.1, plus about −0.5 from the index move = −9.6, matching the actual −9.7. The seller captured only about two days of theta. — [Sensibull](https://blog.sensibull.com/2017/12/26/the-weekend-effect/)
- **[India]** Sensibull conclusion: selling on Friday evening captures about one day of theta, not three, because the market has already priced the weekend. Sell ATM for maximum theta, and straddle-style for direction neutrality. — [Sensibull](https://blog.sensibull.com/2017/12/26/the-weekend-effect/)
- **[India]** Practitioner sources note that non-trading days still contribute theta and describe weekend decay as "three calendar days of theta compressed into one gap at Monday's open". — [INDmoney](https://www.indmoney.com/learn/fno/theta-in-options); [Alice Blue](https://aliceblueonline.com/blog/what-is-theta-in-options-trading-time-decay-explained-with-examples)
- **[India]** Expiry change: SEBI's consultation (March 2025) proposed limiting equity derivative expiries to Tuesday or Thursday, which led NSE to drop its planned April 2025 move to Monday. SEBI approved Tuesday for NSE and Thursday for BSE (BSE moving from Tuesday), effective 1 Sep 2025. — [Business Standard](https://www.business-standard.com/amp/markets/news/nse-defers-switching-to-monday-expiry-after-sebi-s-consultation-paper-125032800183_1.html); [Business Today](https://www.businesstoday.in/amp/markets/stocks/story/nse-receives-sebi-nod-for-tuesday-expiry-bse-thursday-480736-2025-06-17); [Bajaj Finserv](https://www.bajajfinserv.in/nse-revises-nifty-expiry-day). (One report said monthly contracts expire on the last Thursday from 1 Sep 2025; this conflicts with NSE's move of all its index expiries to Tuesday and is probably an error. Verify against NSE's circular.)
- **[India]** Under Tuesday expiry, Monday is the new "expiry eve" with steep decay, and practitioners advise closing positions a day before expiry to avoid gamma risk. — [Navia](https://navia.co.in/blog/weekly-fo-expiry-insights/); [Raahi Bhushan Substack](https://raahibhushan.substack.com/p/adjustments-of-option-positions)
- **[India]** Day-versus-night asymmetry in Nifty index option returns (NSE 2017–2020): the study compares intraday selling (open to close) with overnight selling (close to next open). — [vLex abstract, "The asymmetry in day and night option returns: Evidence from an emerging market"](https://law-journals-books.vlex.com/vid/the-asymmetry-in-day-1115554990)
- **[US]** Jones & Shemesh (JF 2018, "Option Mispricing around Nontrading Periods"): option returns are significantly lower over nontrading periods, mostly weekends. They attribute this to persistent mispricing from incorrect treatment of variance during closures, not to risk. In the working version (US equity options 1996–2007), the average Friday–Monday return was −0.62% while every other day was positive, with little effect in S&P 500 index options. — [IDEAS/JF](https://ideas.repec.org/a/bla/jfinan/v73y2018i2p861-900.html); [SUFE summary](https://academicnewsletter.sufe.edu.cn/info/359500)
- **[US]** Related: "The Impact of Overnight Periods on Option Pricing" (JFQA 2007) and Muravyev & Ni (JFE 2020), "Why do option returns change sign from day to night?" — [IDEAS JFQA 2007](https://ideas.repec.org/a/cup/jfinqa/v42y2007i02p517-533_00.html); [OptionMetrics blog](https://optionmetrics.com/blog/2022_examining_anomalies_what_is_the_best_day_to_buy_stocks_and_options/)

### Inferences
- Calendar-day versus trading-day theta: if the market priced a calendar-day clock (as Black-Scholes with calendar time does), weekend decay would be large. Because weekend variance is low (French & Roll), a trading-day clock (or a weighted clock in which weekend days count as about 0.1–0.3 of a trading day) is more realistic. Sensibull's observation that IV is marked down on Friday and rebounds on Monday is what you see when quoted IV is computed with calendar time while the market prices trading time: the falling IV is the weekend "variance holiday" showing up in the IV number. "IV drops on Friday afternoon" is therefore partly a measurement artefact of the calendar-day convention.
- In the Tuesday-expiry cycle, an option sold Friday has 2 trading days (Mon, Tue) and 4 calendar days left. The weekend can be a large share of remaining calendar time, so the gap between calendar-day and trading-day pricing is at its largest in the week. Short-premium positions carried over the weekend into expiry eve run maximum gamma against a Monday gap.
- Jones & Shemesh suggest that, at least in the US, option buyers systematically overpay for weekends. If the same holds for Nifty weeklies, weekend short-premium earns a premium but with fat-tailed gap risk. No Indian replication was found.

### Gaps
- No Indian quantitative study of intraday IV on Friday afternoons (e.g. India VIX or ATM IV from 2pm to 3:30pm on Fridays).
- No practitioner or academic analysis specific to the post-Sep-2025 Tuesday cycle and the weekend. Searches returned only general expiry-day articles.
- SEBI's Nov-2024 F&O measures (one weekly expiry per exchange, bigger contract sizes, upfront premium collection, removal of calendar-spread margin benefit on expiry day, extra ELM on expiry day) were not retrieved from primary sources. None appears to address weekends directly, but their effect on weekend carry (e.g. margin on short options held over the weekend into Monday) is unstudied.

## Risk: weekend gaps and stop-losses

### Takeaway
On NSE a stop-loss trigger guarantees no exit price. SL-M orders fill at market after a gap, while SL-limit orders may not fill at all if the open gaps past the limit. Forum reports describe SL-M orders being rejected after a gap. No data was found on how often stops fill beyond the stop price after weekends compared with weekdays.

### Cited Findings
- **[India]** Zerodha: an SL (limit) order executes only within its limit band. If the market moves past the band, the order can stay open and losses grow. — [Zerodha Support: stop-loss orders](https://support.zerodha.com/category/trading-and-markets/charts-and-orders/order/articles/what-are-stop-loss-orders-and-how-to-use-them); [Zerodha: SL-L as SL-M](https://support.zerodha.com/category/trading-and-markets/product-and-order-types/order/articles/how-to-use-sl-l-order-like-a-sl-m-order)
- **[India]** Zerodha staff on the Kite forum say stop-loss orders are queued at the exchange, not at the broker. — [Kite forum](https://kite.trade/forum/discussion/comment/21555/)
- **[India]** A trader reports an after-market SL-M order (Jindal Steel) rejected when the stock opened below the trigger. Zerodha's explanation was that it was invalid against the LTP. This is a user report, not documented policy. — [TradingQnA](https://tradingqna.com/t/gap-downs-causes-sl-m-order-to-get-rejected/69221)
- **[India]** Secondary source: a trigger is not a guaranteed exit, SL-M guarantees an exit but not a price, and SL-L guarantees a price but not a fill. — [OneTradeJournal](https://onetradejournal.com/glossary/stop-loss-order)
- **[US]** SPY gap statistics since 1993: small up-gaps (0.1–0.25%) filled the same day 78% of the time and within 5 sessions 91% of the time, while larger gaps often kept running. — [thetrading.tools](https://www.thetrading.tools/gap-analysis)

### Inferences
- Monday combines the largest information backlog (2 days of news, Saturday results, the full US Friday session and weekend geopolitics) with the shortest Gift Nifty discovery window. Weekend positions held with resting stops are therefore most exposed to fills beyond the stop at Monday's 9:15 open, after the 9:00–9:08 pre-open auction sets the price.
- For backtests (relevant to this repo's strategies): a Friday-held position with a stop should be modelled as exiting at min(stop, Monday open) for longs, not at the stop price. Treating stops as filled at the stop understates weekend tail losses.

### Gaps
- No public data on the frequency or size of stop slippage after weekends compared with weekday overnights on NSE. This could be estimated from the repo's OHLC data by counting Monday opens beyond a Friday-defined stop level (e.g. Friday low minus k×ATR) against the same for other days.
- Current NSE/broker handling of SL-M orders on a gapped open (rejection versus market fill), and the effect of SEBI/NSE limits on market orders in F&O (SL-M was discontinued for F&O at some brokers), was not verified.
