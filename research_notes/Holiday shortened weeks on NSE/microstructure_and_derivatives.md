# Holiday-Shortened Weeks on NSE: Microstructure and Derivatives Behaviour

Research date: 22 Oct 2026. India (NSE) evidence comes first; US or global evidence is labelled **[US/Global]**. Coverage is limited: this researcher used about 16 search and fetch calls. Several items rest on broker or blog sources rather than primary NSE or SEBI documents, and each such item says so.

## 1. Volatility and gaps across closures (French & Roll; NSE evidence)

### Takeaway
**[US]** French & Roll (1986) showed that variance per hour is far lower while exchanges are closed. A one-day holiday or long weekend therefore adds much less than its calendar length in variance, which implies a modest extra gap rather than one scaled by √(calendar days). The literature found here says Indian holiday effects show up mainly after holidays rather than before. However, no NSE study was found that directly compares open-to-close and close-to-open variance after holidays.

### Cited Findings
- **[US]** French & Roll (1986), "Stock Return Variances: The Arrival of Information and the Reaction of Traders", *Journal of Financial Economics* 17, pp. 5–26. Secondary summaries report that open-to-close variance on an average day is more than six times the weekend close-to-open variance, even though the weekend is about eleven times longer. Per hour, variance during trading is 13 to 100 times larger than when the market is closed. — [French & Roll PDF (U. Toronto)](https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf); summaries via [search results incl. aabri.com](https://w.aabri.com/manuscripts/213505.pdf)
- **[US]** French & Roll used exchange holidays as a natural experiment, since public news flow continues on those days. Their holiday results point to private information revealed through trading as the main source of trading-hour variance, not public news. Pricing errors account for an estimated 4–12% of daily variance. — [French & Roll PDF](https://www-2.rotman.utoronto.ca/~kan/3032/pdf/AssetPricingAnomalies/French_Roll_JFE_1986.pdf)
- **India:** Lu & Patel (2016), "Festivity Anomaly in Indian Stock Market", *Economics Bulletin* 36(2): 851–856. Most BSE indices show "very strong post-holiday effects", the pre-holiday effect is absent, and the post-holiday effect strengthened during the financial crisis. The abstract does not say whether this applies to returns or volatility; it appears to be returns. — [IDEAS/RePEc](https://ideas.repec.org/a/ebl/ecbull/eb-16-00286.html)
- **India:** Agarwal, Dahiya & Gupta (India vs Singapore, 1992–2018), as summarised in search results. The pre-holiday effect was absent in both countries and replaced by a post-holiday effect. In India this appeared only as a New Year effect, at the 5% level. Diwali produced no significant returns before or after the holiday. — [Publishing India PDF](https://publishingindia.com/storage/PDFBrochures/1795.pdf) (attribution from the search summary; full text not verified)
- **India:** Another Indian calendar-anomaly study found weekday mean returns and volatility higher than on pre- and post-holiday days, but its OLS regressions found no significant holiday effect in any sub-period. — [INFLIBNET/Shodhganga](https://sgbeta.inflibnet.ac.in/items/1960e11b-8db2-4cda-abc2-0605ba4cf29b)

### Inferences
- Take French & Roll's ratio as a rough guide: a 2-day non-trading period has about 1/6 of a trading day's variance spread over about 11 times the hours. On that basis, a one-day mid-week holiday would add only a small fraction of a trading day's variance to the reopening close-to-open gap, perhaps roughly 0.1–0.3 of a normal day's variance. A long weekend of 3–4 calendar days would add slightly more than a normal weekend. Scaling the gap by calendar days would overstate it. This is extrapolated from US data, not measured on NSE.
- **India caveat:** NSE has an important exception. On an India-only holiday, global markets (US, Europe, Asia, GIFT Nifty) keep trading, so public information still accumulates and is priced elsewhere. The reopening gap should then behave more like a catch-up to global moves, close to the variance of a trading day abroad, than like a French & Roll closed-market night. Section 3 covers this.
- Post-holiday effects being stronger than pre-holiday effects in India fits a catch-up gap on reopening.

### Gaps
- No NSE or Nifty study was found that splits close-to-open and open-to-close variance specifically after holidays. A practical next step is to compute it from Nifty OHLC data: the ratio of overnight to intraday variance on post-holiday days versus normal days, separating India-only holidays from joint global holidays.
- The full texts of the Indian studies were not read, so their volatility-specific (GARCH) holiday results are unverified.

## 2. Volume and liquidity (pre/post holiday, Muhurat, concentration in shortened weeks)

### Takeaway
No rigorous NSE data on holiday turnover or bid-ask spreads was found. The evidence on Muhurat trading is mostly descriptive. It describes a one-hour symbolic session, retail-dominated and lower-volume, with activity clustered in part of the hour and average moves of about +0.4–0.5%.

### Cited Findings
- Muhurat 2021 session, one hour: 2,017 securities traded, 65.35 lakh trades, ₹11,552.24 cr turnover. — [Tickertape](https://www.tickertape.in/blog/?p=5636)
- Muhurat volumes are described as lower and dominated by retail investors, with trades settling on regular days. This is qualitative. — [Outlook Business](https://www.outlookbusiness.com/news/the-significance-and-trends-of-muhurat-trading-at-bse-nse-on-diwali-news-232208)
- Volume is reported to rise sharply in part of the Muhurat hour, roughly 6:30–7:00 pm in the cited year. — [Tickertape](https://www.tickertape.in/blog/?p=5636)
- Average Nifty and Sensex gains in the Muhurat session are about 0.4–0.5%. — [Angel One](https://oga-prod.angelone.in/news/market-updates/muhurat-trading-2025-cultural-significance-and-historical-returns)
- **Muhurat 2026:** Most sources say the session is on **Sunday, 8 November 2026** (Laxmi Pujan), with timings to be announced by NSE circular. One source (Angel One) gives 21 Oct 2026, which conflicts with the others and is likely wrong. The 2022 session ran 6:15–7:15 pm after a pre-open. — [Sahi](https://sahi.com/blogs/nse-trading-holidays-2026-complete-list-of-stock-market-holidays); [Angel One holiday list](https://www.angelone.in/nse-holidays); [Tickertape](https://www.tickertape.in/blog/?p=5636)
- A brokerage article says pre-holiday trading often sees higher volume and volatility as traders hedge. It cites no data, so treat it as commentary. — [Jainam](https://jainam.in/?p=5601)
- **2026 NSE weekday equity and F&O holidays** (broker compilation, not the NSE circular): 26 Jan, 3 Mar, 26 Mar, 31 Mar, 3 Apr, 14 Apr, 1 May, 28 May, 26 Jun, 14 Sep, 2 Oct, 20 Oct (Dussehra), 10 Nov (Diwali Balipratipada), 24 Nov (Guru Nanak Jayanti), 25 Dec. Festivals on 15 Feb, 21 Mar, 15 Aug and 8 Nov fall on weekends. — [Sahi](https://sahi.com/blogs/nse-trading-holidays-2026-complete-list-of-stock-market-holidays)
- **[US]** The day after Thanksgiving is traditionally among the lightest US sessions of the year. — [Bloomberg](https://www.bloomberg.com/news/articles/2022-11-25/stock-market-has-a-black-friday-tradition-low-trading-volume)

### Inferences
- Late March 2026 had three holidays in about 6 trading days (26, 31 Mar and 3 Apr). November 2026 has two holiday weeks (10 and 24 Nov) plus the Sunday Muhurat session. These are the main shortened-week clusters for testing whether volume concentrates.
- Weekly Nifty options expire every week, and shortened weeks move expiry earlier (Section 4). Expiry-day volume therefore probably drives most of the week's derivatives turnover. Whether total weekly volume is concentrated or just lower is an empirical question.

### Gaps
- No source quantified NSE bid-ask spreads or market depth before or after holidays, or during Muhurat sessions.
- No study was found on volume concentration in shortened weeks on NSE. NSE bhavcopy or turnover data would be needed.

## 3. Global holidays: India open/others closed, and India closed/others open

### Takeaway
No India-specific quantitative evidence was found. Mechanically, GIFT Nifty (NSE IX, trading about 21 hours a day) serves as the overnight price-discovery venue. When India is closed, it carries global moves that Nifty must catch up to at its next open. When the US is closed, GIFT Nifty still trades but loses its usual overnight US cue.

### Cited Findings
- On a US Thanksgiving, Indian pre-market notes still reported the GIFT Nifty level as the opening indicator, while noting that US markets were closed. — [DSIJ](https://insights.dsij.in/dsijarticledetail/top-things-you-must-know-before-the-market-opens-id008-44476)
- **[US]** NYSE and Nasdaq close on Thanksgiving and close early the following Friday. Thanksgiving week historically has thinner volume. — [Benzinga](https://benzinga.com/z/35930411); [Bloomberg](https://www.bloomberg.com/news/articles/2022-11-25/stock-market-has-a-black-friday-tradition-low-trading-volume)
- **[US]** In November–December, US volumes average about 4.6–5.9% below the 50-day moving average. — [Bespoke](https://www.bespokepremium.com/free-home/page/464/)

### Inferences
- **India closed, world open:** By French & Roll's logic, information keeps arriving and is priced on GIFT Nifty and abroad, so the reopening gap should be larger than after a joint closure. The overnight return on GIFT Nifty during an NSE holiday is the natural predictor of the reopening gap. This should be tested, not assumed.
- **India open, US closed** (e.g. Thanksgiving, Good Friday when India is open): FII desks, whose risk is often managed from the US or EU, are likely less active. No overnight US cue reaches the Indian open, so the opening gap is likely smaller. Intraday trading may be driven more by domestic flows. These are hypotheses only.

### Gaps
- No NSDL/NSE data on FII cash or F&O volume on US-holiday days was found.
- No data was found on GIFT Nifty liquidity, spreads or basis during US holidays or NSE holidays.

## 4. Derivatives: expiry shifts, SEBI 2024–2026 changes, theta/IV across holidays, margins

### Takeaway
As of October 2026, **NSE's only weekly index contract is Nifty 50, expiring every Tuesday.** All NSE monthly contracts expire on the last Tuesday of the month. **BSE uses Thursday** (Sensex weekly). If an expiry day is a holiday, the contract expires on the **previous trading day**. Option decay is priced in calendar days, so holidays and weekends are worth less theta than calendar-day models imply. In practice, market makers price this in before the closure, through IV and premium falling in the last session.

### Cited Findings
- **SEBI circular, 1 Oct 2024:** each exchange may offer weekly expiry on only one benchmark index, effective 20 Nov 2024. Minimum index derivative contract size rose from ₹5 lakh to ₹15 lakh. An extra 2% Extreme Loss Margin applies to short options on expiry day, also from 20 Nov 2024. Intraday position-limit monitoring uses at least 4 random snapshots, from 1 Apr 2025. — [Zerodha Z-Connect](https://zerodha.com/z-connect/updates/sebis-new-rules-on-weekly-index-derivatives-expiry); [law.asia](https://law.asia/sebi-index-derivatives-framework/)
- NSE kept weekly options only on Nifty 50. The last weekly expiries were Bank Nifty on 13 Nov 2024, Nifty Midcap Select on 18 Nov 2024 and FinNifty on 19 Nov 2024. BSE kept only the Sensex weekly and dropped Bankex and Sensex 50 weeklies. — [Motilal Oswal](https://www.motilaloswal.com/learning-centre/2024/10/nse-discontinues-weekly-derivatives-on-bank-nifty-nifty-midcap-select-and-finnifty); [Business Today](https://www.businesstoday.in/amp/markets/story/after-sebis-new-fo-rules-bse-discontinues-weekly-index-derivatives-contracts-on-sensex-50-bankex-448626-2024-10-03)
- In March 2025, NSE deferred a planned switch to Monday expiry after SEBI issued a consultation paper. — [Business Standard](https://www.business-standard.com/amp/markets/news/nse-defers-switching-to-monday-expiry-after-sebi-s-consultation-paper-125032800183_1.html)
- **SEBI circular, 26 May 2025** (SEBI/HO/MRD/MRD-TPD-1/P/CIR/2025/76): all of an exchange's equity derivatives must expire on either Tuesday or Thursday. Each exchange keeps one weekly benchmark index option on its chosen day. Other contracts must have a minimum tenor of one month and expire in the last week of the month. Exchanges need prior SEBI approval to change expiry days. The stated rationale is to avoid "expiry day hyperactivity". — [Taxmann](https://www.taxmann.com/post/blog/sebi-fixes-equity-derivatives-expiry-to-either-tuesday-or-thursday); [Business Standard](https://www.business-standard.com/amp/markets/news/sebi-limits-equity-derivatives-expiry-to-tuesdays-and-thursdays-125052601285_1.html)
- **From 1 Sep 2025** (one source says 2 Sep), NSE moved all expiries from Thursday to Tuesday and BSE moved to Thursday. Current NSE setup: Nifty weekly every Tuesday; Nifty, Bank Nifty, FinNifty, Midcap Select and Next 50 monthly on the last Tuesday. BSE: Sensex weekly every Thursday; Bankex and Sensex 50 monthly on the last Thursday. Secondary sources describe this as still current in July–October 2026. — [AlgoTest](https://algotest.in/blog/all-index-expiry-day/); [5paisa](https://www.5paisa.com/index.php/news/sebi-reshuffles-equity-derivatives-expiry-days-to-streamline-trading); [Sahi](https://sahi.com/blog/options-trading/nse-nifty-expiry-day)
- **Holiday rule:** "If an expiry day is a market holiday, the contract expires on the previous trading day." If that day is also a holiday, expiry moves back again. Exchanges announce each shift by circular. NSE used the same rule for its earlier Tuesday FinNifty expiries (2021 circular). — [AlgoTest](https://algotest.in/blog/all-index-expiry-day/); [Zerodha bulletin 2021](https://zerodha.com/marketintel/bulletin/307755/changes-in-expiry-day-and-discontinuation-of-weekly-futures-contracts-of-finnifty)
- **Upcoming 2026 holiday-shifted NSE expiries** (blog calendar, not an NSE circular):
  - **Mon 19 Oct** (from 20 Oct, Dussehra): Nifty weekly.
  - **Mon 9 Nov** (from 10 Nov, Diwali Balipratipada): Nifty weekly.
  - **Mon 23 Nov** (from 24 Nov, Guru Nanak Jayanti): Nifty weekly and **all NSE monthly** contracts.
  - **Calendar error:** The source labels 19 Oct as a Monday. In 2026, 20 Oct is a Tuesday, so the previous trading day is **Monday 19 Oct**, which matches.

  — [AlgoTest](https://algotest.in/blog/all-index-expiry-day/)
- **Theta convention:** Most brokers and models count time decay in calendar days to expiry, so weekends and holidays count. For India, Rupeezy also says decay follows calendar days, not trading hours. — [Rupeezy support](https://support.rupeezy.in/support/solutions/articles/21000005304-what-is-time-decay-theta); [SpotGamma, US](https://support.spotgamma.com/hc/en-us/articles/15249846531219-Weekend-Theta)
- **[Global]** ICE's example: if a Monday is a holiday, Friday's theta includes four days of decay. — [ICE help](https://idd.ice.com/CM/CMHelp/Content/FM/Theta_.htm)
- **[US]** Market makers block easy Friday-to-Monday theta collection by letting IV fall into Friday's close. Relative to a roughly 251-trading-day model, a calendar-day model must show higher IV on Mondays. — [Moontower Meta](https://moontowermeta.com/weekend-theta/)
- **India:** Weekend decay is priced in by Friday, which is why premiums often look to drop sharply on Monday. — [Choice India](https://choiceindia.com/blog/time-decay-options); [DSIJ](https://insights.dsij.in/dsijarticledetail/do-options-lose-value-over-the-weekend-31500)

### Inferences
- **Effect of a holiday-shortened expiry week:** The weekly Nifty contract has one fewer trading session but expires a calendar day earlier. If the week's realised variance stays roughly constant per trading day, as French & Roll's logic suggests, a calendar-day model will show a lower IV for the shortened week. Trading-day IV is the more comparable measure. Traders comparing IV across weeks should convert to trading-day variance, for example by giving holidays and weekends a weight of about 0.1–0.3 of a trading day.
- **Holiday the day before Tuesday expiry:** If Monday is a holiday, the Tuesday expiry keeps its day, but gamma risk builds over a 3-day close (Fri→Tue). Expect Friday premium to fall as the closure is priced in, and the expiry-morning gap to carry 3 days of global news.
- **Holiday on Tuesday:** Expiry moves to Monday, so the series is effectively one day shorter. The new weekly series lists after Monday's expiry and has a holiday on its first day.
- **Margins:** The 2% expiry-day ELM on short options applies on the actual (shifted) expiry day. The larger ₹15 lakh lot size and upfront premium collection raise the capital needed to hold short options over long closures.

### Gaps
- No Sensibull or Opstra article on IV and holidays was found, and Zerodha Varsity's theta chapter did not appear in results. The practitioner India evidence here is thin (Rupeezy, Choice, DSIJ).
- No NSE circular PDF for the Tuesday move or for the 2026 holiday expiry shifts was fetched directly. The rule is consistent across many secondary sources, but the exact dates should be checked against NSE circulars.
- Other items from the Oct 2024 package, such as removing calendar-spread margin benefit on expiry day and intraday monitoring details, were not verified in this session.
- No India data was found on how Nifty weekly IV (e.g. India VIX or ATM IV) behaves before and after holidays.

## 5. Settlement: T+1 and holidays, settlement holidays vs trading holidays

### Takeaway
NSE counts settlement days in working days and skips bank holidays, NSE holidays and weekends. A **settlement holiday**, often a Maharashtra bank holiday, is a day when trading runs normally but clearing, depositories and banks do not settle. Trades from the day before settle on the next business day, often with several settlements bunched together.

### Cited Findings
- NSE's settlement-cycle page says that "For arriving at the settlement day all intervening holidays, which include bank holidays, NSE holidays, Saturdays and Sundays are excluded." Under T+1, obligations are provisional on T, final by 8:30 am on T+1, and settled on T+1. — [NSE settlement cycle](https://www.nseindia.com/static/products-services/equity-market-settlement-cycle) (from search snippet; the direct fetch timed out)
- NSE Clearing issues a circular for each holiday-driven schedule change. For example, a September 2024 holiday on 18 Sep meant "multiple settlements have been scheduled on September 19, 2024". A January 2026 circular revised the schedule so that there was no trading or settlement in T+1 settlement no. 2026011 and T+0 no. 2026511. — [NSE Clearing circular CMPT63955](https://nsearchives.nseindia.com/content/circulars/CMPT63955.pdf); [NSE circular CMPT72278](https://nsearchives.nseindia.com/content/circulars/CMPT72278.pdf)
- **Example: 26 Aug 2026 (Wednesday, Id-E-Milad) settlement holiday.** NSE and BSE trade normally across equity, equity derivatives and currency derivatives. Clearing corporations, NSDL/CDSL and clearing banks do not operate. Trades of 25 Aug settle on 27 Aug, with sale proceeds credited and bought shares delivered then. Shares bought on 25 Aug cannot be sold for delivery until credited on 27 Aug. Withdrawals requested after 4 pm on 25 Aug are processed by 27 Aug. — [Groww](https://groww.in/blog/settlement-holiday-on-26-august-2026)

### Inferences
- In practice a settlement holiday turns T+1 into T+2 for trades on the day before. Traders get delayed delivery and fund credit, and selling those shares for delivery becomes awkward. Two days of obligations settle together, which raises the funding needs of brokers and clearing members on the next business day.
- F&O settlement is also pushed back, so daily MTM and premium pay-in from the holiday's previous session move to the next settlement day. The Groww article did not detail F&O mechanics.

### Gaps
- The NSE settlement-cycle page could not be fetched in full (timeout), so its wording comes from a search snippet.
- No source detailed how F&O MTM and premium settlement and margin calls work on settlement holidays, or whether short-delivery auctions move.

## 6. Intraday patterns in shortened weeks

### Takeaway
No documented research was found on intraday patterns specific to NSE's holiday-shortened weeks. The only intraday-timing evidence concerns the Muhurat session.

### Cited Findings
- Muhurat volume reportedly clusters in part of the one-hour session, around 6:30–7:00 pm in the cited year. — [Tickertape](https://www.tickertape.in/blog/?p=5636)
- Indian day-of-week GARCH studies on Nifty report that all weekday returns are positive and significant. They do not model holidays. — [OUCI listing](https://ouci.dntb.gov.ua/en/works/4KB2Rqo7)
- Regular NSE session: pre-open 9:00–9:08, continuous trading 9:15–15:30, closing session 15:40–16:00. — [Rupeezy NSE holidays](https://rupeezy.in/share-market-holiday/nse)

### Inferences
- The Tuesday weekly expiry concentrates intraday gamma activity, especially in the final hour. When Tuesday is a holiday, that pattern likely moves to Monday, which then combines a post-weekend gap with expiry-day hedging flows. This is a hypothesis to test with intraday data.

### Gaps
- No academic or practitioner study was found on U-shaped intraday volume or volatility changes in holiday weeks on NSE. Answering this requires NSE tick or minute data.
