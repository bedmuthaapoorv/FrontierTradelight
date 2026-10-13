# NSE Fundamental Data Sources for a GARP Screener/Backtester (as of Oct 2026)

Note: research was capped at about 15 tool calls. Several vendor-specific facts (EODHD/FMP India coverage, exact prices) could not be confirmed from primary pages and are listed under Gaps. Prices and terms change often, so re-check them before buying.

## Which sources provide NSE fundamental data, and how (fields, history, cost, API vs scraping, ToS, reliability)?

### Takeaway
No free, ToS-clean, programmatic source covers 10+ years of NSE fundamentals. Free routes (yfinance, scraping Screener.in, Moneycontrol or NSE) are either shallow (yfinance gives about 4 years) or forbidden by the site terms (NSE and Screener.in). Official XBRL filings on NSE/BSE are the authoritative raw source, but bulk automated download from nseindia.com is prohibited without written consent. Paid global APIs (EODHD, FMP) say they have global fundamentals, but I could not confirm their India depth or quality. Institutional databases (CMIE Prowess, Capitaline, Ace Equity, LSEG, Bloomberg) are the reliable route, and they are priced for institutions.

### Cited Findings
**Official: NSE / BSE filings (XBRL)**
- Under SEBI circular SEBI/HO/CFD/CFD-PoD-2/CIR/P/2024/185 (31 Dec 2024), listed companies file an "Integrated Filing (Financial)". It applies to quarters ending 30 Jun 2025 onward. — [MSEI circular, 04 Aug 2025](https://www.msei.in/SX-Content/Company-Circulars/2025/August/EXCHANGE-04-AUG-2025-IMPLEMENTATION-OF-RECOMMENDATIONS-OF-THE-EXPERT-COMMITTEE-FOR-FACILITATING-EASE-OF-DOING-BUSINESS-FOR-LISTED-ENTITIES---INTEGRATED-FILING.pdf)
- BSE requires equity issuers to submit financial results in XBRL using the "Integrated Filing – Financial" utility, on the same date as the PDF results. NSE's matching circular is NSE/CML/2025/02 (2 Jan 2025). — [BSE Circular 02.04.2025](https://ca2013.com/wp-content/uploads/2025/04/BSE-Circular_02.04.2025.pdf); [NSE listed-company circulars](https://www.nseindia.com/companies-listing/circular-for-listed-companies-equity-market)
- Example integrated-financial filings sit on the NSE archive. — [NSE archive example (DSML, Feb 2026)](https://nsearchives.nseindia.com/corporate/DSML_14022026190347_Integrated_Filing__Financial_docx.pdf); [HINDUJAVEN May 2025](https://nsearchives.nseindia.com/corporate/HINDUJAVEN_02052025174547_Integrated_Financial.pdf)
- A QuantInsti community answer points users to NSE's corporate-filings "Financial Results" pages as a parseable source for NSE fundamentals. — [QuantInsti community](https://quantra.quantinsti.com/community/t/where-can-we-get-fundamental-data-for-nse-stocks-data-sources-mentioned-mostly-cater-for-us-market/26320)
- **ToS warning:** NSE's Terms of Use say that all website and app content, including real-time information, is NSE's exclusive property. — [NSE Terms of Use](https://www.nseindia.com/static/nse-terms-of-use)
- **ToS warning:** NSE's data-portal terms bar "systematic or automated data collection, including scraping" without express written consent. — [NSE dotexdata Terms of Use PDF](https://dotexdata.nseindia.com/TermsAndConditions/TermsofUse.pdf)
- An older (2015) quote of NSE's main-site terms also prohibits scraping, data mining and harvesting without written consent. This is secondhand. — [R-help mailing list 2015](https://stat.ethz.ch/pipermail/r-help/2015-August/431607.html)
- A forum post says a SEBI-mandated website security policy prohibits scripted downloads from NSE, and that NSE blocks many server-side or cloud requests (for example, nsepython failing on AWS or GCP). This is an unverified forum claim. — [Unofficed forum](https://forum.unofficed.com/t/nsepython-not-working-in-aws-google-cloud-and-webservers/670)
- A user claim on a forum says public display of NSE data requires buying it from NSE or a registered vendor. — [TradingQnA](https://tradingqna.com/t/need-api-for-nse-data/104916)
- India has no statute specifically on web scraping. Liability turns on contract (accepted terms), copyright and IT law. — [LawRato](https://lawrato.com/indian-kanoon/civil-law/is-web-scraping-legal-in-india-what-a-business-can-and-cannot-collect-3192)

**Free / low-cost aggregators**
- **Screener.in** (Mittal Analytics Pvt Ltd): the terms (last updated 1 Aug 2018) grant a licence "for personal, non-commercial transitory viewing only". They forbid copying or modifying the materials, using them commercially or for public display, and mirroring them on another server. The terms do not mention scraping or bots explicitly. — [Screener.in Terms](https://www.screener.in/guides/terms)
- Screener advertises "10+ years of data", and screens run on 10 years of financials. Excel export is a premium feature. — [Screener features](https://screener.in/features); [Screener support: export](https://support.screener.in/article/28-export-screen-results)
- One third-party review puts Screener Premium at about ₹4,999/yr. This is unconfirmed against the official pricing page. — [Strike.money review 2026](https://www.strike.money/reviews/screener-in)
- Screener.in and Tickertape show restated or latest numbers rather than as-originally-reported figures, which creates look-ahead bias in backtests. This comes from a June 2026 forum post by a user who was promoting their own point-in-time product. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)
- Moneycontrol is cited only as a scraping target. No official API was identified. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)
- The `bsedata` PyPI package gives BSE price quotes, not fundamentals, and does not cover NSE-only listings. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)
- Alpha Vantage reportedly dropped NSE/India fundamentals (2023 user report). — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)
- Trendlyne: third-party comparison sites say it has no public API. Its tiers include GuruQ at about ₹1,890/yr and StratQ at about ₹5,900/yr. This is unverified against Trendlyne. — [FindMyMoat comparison](https://www.findmymoat.com/vs/tiingo-vs-trendlyne)

**yfinance (`.NS` tickers)**
- Users report that yfinance gives at most about 4 years of statement data for Indian stocks. A yfinance-based MCP tool describes its Indian financials as "last 4 years" of annual income statement, balance sheet and cash flow. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292); [FinMCP GitHub](https://github.com/Prem07a/FinMCP)
- Usage is `Ticker("X.NS").financials` and `.balance_sheet`. Empty DataFrames are common, and the usual fix is upgrading the library. yfinance is unofficial and not endorsed by Yahoo, so its schema and coverage can change without notice. — [QuantInsti community](https://quantra.quantinsti.com/community/t/where-can-we-get-fundamental-data-for-nse-stocks-data-sources-mentioned-mostly-cater-for-us-market/26320); [marketcalls yfinance guide](https://www.marketcalls.in/python/mastering-yfinance-the-ultimate-guide-to-analyzing-stocks-market-data-in-python.html)

**Paid global APIs**
- **EODHD:** offers annual and quarterly balance sheet, income statement and cash flow, plus an Earnings section and "Earnings Trend" analyst estimates (earningsEstimateAvg/Low/High, revenue estimates, EPS revisions). Non-US history goes back to 2000, but minor companies often have only the last 6 years and 20 quarters. Each report entry carries both a `date` and a `filing_date`. Fundamentals calls cost 10 API calls each. The free tier is 20 calls/day. Paid plans start at $19.99/mo, and pages show fundamentals plans "from $59.99/mo". Bulk fundamentals requires the Extended Fundamentals plan. The only point-in-time data is S&P 500 index membership. — [EODHD fundamentals docs](https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds); [EODHD listing page](https://eodhd.com/financial-summary/INDH.US)
- I could not confirm EODHD's NSE coverage from its docs. The exchange list is fetched via `/api/exchanges-list/`. — [EODHD exchanges](https://eodhd.com/financial-apis/list-supported-exchanges)
- **FMP:** advertises 70,000+ stocks across global exchanges, quarterly and annual statements, and up to 30 years of history. I found no FMP page confirming the depth of its NSE (`.NS`) fundamentals. — [FMP vendor profile](https://creandaccelera.getproven.com/vendor/financial-modeling-prep); [FMP consensus-estimates article](https://site.financialmodelingprep.com/education/analyst/best-apis-for-consensus-estimates-price-targets-and-analyst-forecasts)

**Institutional databases**
- **CMIE Prowess / ProwessIQ:** covers about 37,780 to 51,500+ Indian companies (figures vary by source). It is web-based and mostly sold to institutions and universities. Pricing is not published (IndiaMART lists only "Get Best Price"). — [IIM Indore user guide](https://iimidr.ac.in/wp-content/uploads/2025/10/User-Guide-CMIE-prowess-IQ.pdf); [IIM Calcutta library](https://library.iimcal.ac.in/cmie-prowessiq/); [Wikipedia: CMIE](https://en.wikipedia.org/wiki/Centre_for_Monitoring_Indian_Economy); [IndiaMART](https://m.indiamart.com/company/9088923)
- Bloomberg and FactSet are named as paid options for NSE fundamentals. — [QuantInsti community](https://quantra.quantinsti.com/community/t/where-can-we-get-fundamental-data-for-nse-stocks-data-sources-mentioned-mostly-cater-for-us-market/26320)

### Inferences
- **Practical ranking for a solo Python backtester:**
  1. EODHD or FMP, after a trial to verify NSE depth. This is the cheapest legal API, but it is restated and not point-in-time.
  2. Screener.in Premium Excel export for manual or semi-manual personal research. Automating it is likely outside "personal, non-commercial transitory viewing" and it may not be mirrored.
  3. Building your own XBRL archive from exchange filings. This is the authoritative as-reported data, but bulk scripted download from nseindia.com breaches NSE's terms without written consent, so use a licensed vendor or ask NSE/BSE for permission.
  4. CMIE Prowess, Capitaline or Ace Equity if budget allows (institutional, contact sales).
- yfinance's roughly 4-year depth is enough for a live screener (current trailing EPS, P/E, recent growth) but not for a multi-year backtest.
- Moneycontrol, Tickertape and Trendlyne are the same ToS category as Screener: website products with no public fundamentals API, so treat scraping them as ToS-risky.
- **ToS risk flag:** scraping NSE (explicitly prohibited), Screener.in (licence limited to personal viewing; copying and mirroring prohibited), and the other aggregators all carry contractual risk. The risk is especially high if the user's fund-website project would publicly display or commercially use the data.

### Gaps
- I could not confirm whether EODHD's or FMP's NSE fundamentals are complete across the Nifty 500, or how far back they go. Test with RELIANCE.NSE / RELIANCE.NS.
- I did not verify pricing or terms for Tickertape, Moneycontrol, Capitaline, Ace Equity, LSEG/Refinitiv or Bloomberg.
- I did not check MCA21 XBRL (annual statutory filings, paid per-document on the MCA portal) or BSE's API or data-licensing products.
- I did not read the current full text of NSE's main-site scraping clause. The retrieved page was truncated, so only the data-portal terms and the 2015 quote are confirmed.

## Which sources offer point-in-time / as-reported history, and what is the workaround?

### Takeaway
No affordable, documented point-in-time (PIT) NSE fundamentals vendor was found. EODHD's only PIT dataset is S&P 500 membership, but its per-report `filing_date` field can approximate the date the data became known. The standard workaround is to use the first-reported figures, or restated figures as a proxy, and make each quarter's data available only after the SEBI filing deadline (45 or 60 days) or after the actual filing date if you have it.

### Cited Findings
- EODHD's only point-in-time dataset is index membership (S&P 500 only, reliable from April 2012). Each financial report entry carries a `date` and a `filing_date`. — [EODHD fundamentals docs](https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds)
- A forum poster (June 2026) offers "as-reported" point-in-time Indian fundamentals as a commercial sample/notebook. This is self-promotion and unverified. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)
- Screener.in and Tickertape figures are restated or latest, not as-reported. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)
- Exchange XBRL "Integrated Filing (Financial)" documents are timestamped in the filename (for example `DSML_14022026190347_...`, which is 14 Feb 2026 19:03:47). That makes them inherently as-reported with a known availability time. — [NSE archive example](https://nsearchives.nseindia.com/corporate/DSML_14022026190347_Integrated_Filing__Financial_docx.pdf)

### Inferences
- **Recommended lag rule for the backtest:** make fiscal-quarter data visible on `max(actual filing_date if known, quarter_end + 45 days)` for Q1 to Q3, and `quarter_end + 60 days` for Q4/annual. For a March year-end that means Q1 on 14 Aug, Q2 on 14 Nov, Q3 on 14 Feb and Q4/annual on 30 May. A conservative alternative is a single 60-day lag for all quarters, or 90 days to absorb late filers.
- Where a vendor provides `filing_date` (EODHD), prefer it, with the deadline as a fallback cap. Spot-check its accuracy against NSE announcement timestamps.
- Restated data plus the lag still leaks restatements, survivorship and consolidation changes. This leak is modest for GARP ratios built on EPS growth, but you should acknowledge it in backtest reports.
- The Nifty 500 universe must also be point-in-time (historical constituents). Otherwise survivorship bias outweighs the fundamentals issue. No source was found for this in this sub-topic.

### Gaps
- No pricing was found for any as-reported Indian PIT dataset. CMIE Prowess may keep historical versions, but I could not confirm that.
- I did not verify how reliable EODHD's `filing_date` is for Indian tickers.

## Indian reporting timelines (SEBI LODR) for lagging fundamentals

### Takeaway
Under LODR Regulation 33, as carried into the 2025 "Integrated Filing (Financial)", quarterly results are due within 45 days of quarter-end for Q1 to Q3. Q4 and annual audited results are due within 60 days of financial-year end. Consolidated results are required where the company has subsidiaries.

### Cited Findings
- SEBI circular (31 Dec 2024) on Integrated Filing (Financial): due within 45 days of quarter-end other than the last quarter, and within 60 days for the last quarter and financial year. The Governance filing is due within 30 days. It applies from the quarter ending 30 Jun 2025. — [MSEI circular, 04 Aug 2025](https://www.msei.in/SX-Content/Company-Circulars/2025/August/EXCHANGE-04-AUG-2025-IMPLEMENTATION-OF-RECOMMENDATIONS-OF-THE-EXPERT-COMMITTEE-FOR-FACILITATING-EASE-OF-DOING-BUSINESS-FOR-LISTED-ENTITIES---INTEGRATED-FILING.pdf)
- NSE's compliance calendar says the same: 45 days for quarterly (other than the last quarter) and 60 days from FY-end for yearly. — [NSE compliance calendar](https://cmsuat.nseindia.com/companies-listing/compliance-information-compliance-calendar-debt)
- Audited annual standalone results are due within 60 days of FY-end, with the audit report. Audited consolidated results are also due where subsidiaries exist. — [TaxGuru: LODR financial results](https://taxguru.in/sebi/sebi-listing-regulations-financial-results-annual-reportinformation.html); [KPMG 2023 LODR summary](https://assets.kpmg.com/content/dam/kpmg/in/pdf/2023/01/vor-sebi-lodr-regulations-icai-mutual-funds.pdf)
- Practical dates for a March FY: Q1 by 14 Aug, Q2 by 14 Nov, Q3 by 14 Feb, annual by 30 May. — [Patron Accounting glossary](https://www.patronaccounting.com/glossary/accounting/sebi-financial-reporting-timelines)
- Conflict: a Taxmann compliance calendar lists a 15 May due date for Q4. This appears to be the older or incorrect framing, and the regulation and exchange calendars say 60 days. — [Taxmann calendar](https://www.taxmann.com/post/blog/compliance-calendar-for-the-listed-entities-under-sebi-lodr-norms/)
- COVID-era extensions (for example, FY20 results allowed until 31 Jul 2020) were temporary. — [LegalMantra 2020](https://legalmantra.net/blog-detail/SEBI-EXTENDED-TIMELINE-FOR-SUBMISSION-OF-FINANCIAL-RESULTS-ENDED-ON-31ST-MARCH2020-TILL-31ST-JULY-2020)

### Inferences
- **Backtest caveat:** in 2020 and 2021, SEBI granted COVID extensions, so a fixed 45/60-day lag would be too early for those quarters. Use actual filing dates, or a longer lag (for example 90 days) for the FY20 Q4 to FY21 window.
- Most large Nifty 500 companies report well before the deadline, so a deadline-based lag is conservative. It slightly delays signals but avoids look-ahead.

### Gaps
- I did not check the May 2026 NSE "single filing system" circular for any change to the deadlines.
- I did not compile the full list of COVID-period extension dates from SEBI circulars.

## Analyst consensus EPS forecasts for Indian stocks

### Takeaway
Consensus EPS for Indian stocks is available from Trendlyne's Forecaster (about 900 companies, which roughly covers the Nifty 500, but web UI only with no confirmed API). EODHD's "Earnings Trend" estimates endpoint may also have it, but India coverage is unverified. Institutional terminals (Bloomberg, LSEG I/B/E/S, FactSet) are the only well-documented historical consensus sources.

### Cited Findings
- Trendlyne Forecaster aggregates analyst earnings estimates (quarterly and annual EPS, target price, recommendations) for about 900 companies. An older FAQ says about 3,000. Smaller companies are excluded. — [Trendlyne help: forecaster estimates](https://help.trendlyne.com/support/solutions/articles/84000383175-what-are-forecaster-or-analyst-estimates-); [Trendlyne FAQ (older)](https://faq.trendlyne.com/support/solutions/articles/84000391872-what-are-forecaster-or-analyst-estimates-); [Trendlyne target price](https://help.trendlyne.com/support/solutions/articles/84000396870-what-is-the-analyst-price-target-)
- Trendlyne is listed as having no public API. — [FindMyMoat comparison](https://www.findmymoat.com/vs/tiingo-vs-trendlyne)
- EODHD fundamentals include Earnings Trend estimates (EPS and revenue avg/low/high, revisions). Coverage per ticker is not stated, and "Not every company reports every data point." — [EODHD fundamentals docs](https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds)
- FMP and Intrinio market consensus-estimate APIs, but nothing found covers India specifically. — [FMP article](https://site.financialmodelingprep.com/education/analyst/best-apis-for-consensus-estimates-price-targets-and-analyst-forecasts)

### Inferences
- Historical consensus (needed to backtest a forward-PEG) is effectively unavailable cheaply for India. Use a trailing PEG (P/E divided by trailing 3- to 5-year EPS CAGR) for the backtest, and use forward consensus only in the live screener, where a snapshot is fine.
- Consensus is thin or absent for the lower half of the Nifty 500, so the screener must handle missing forecasts gracefully.

### Gaps
- No costs were found for I/B/E/S, FactSet or Bloomberg India estimates.
- Trendlyne's API or data-licensing terms are unconfirmed.

## Practical data issues (standalone vs consolidated, splits/bonuses, negative EPS, banks/NBFCs, corporate actions)

### Takeaway
Use consolidated figures where available, and fall back to standalone. Adjust EPS history for splits and bonuses. Exclude or separately score negative-EPS stocks and financials. Most of these handling rules are standard practice rather than sourced findings here.

### Cited Findings
- Where a company has subsidiaries, LODR requires audited consolidated results in addition to standalone results. — [TaxGuru: LODR financial results](https://taxguru.in/sebi/sebi-listing-regulations-financial-results-annual-reportinformation.html)
- EODHD fundamentals include splits and dividends data alongside statements. — [EODHD listing page](https://eodhd.com/financial-summary/INDH.US)
- Screener.in and Tickertape present restated or latest numbers. Restatements, such as consolidation-scope changes, alter history. — [TradingQnA thread](https://tradingqna.com/t/what-are-api-for-getting-fundamental-data-for-stocks-trading-in-nse-india-free-or-paid/145292)

### Inferences
These are general practice and not individually sourced in this research.
- **Standalone vs consolidated:** Indian companies with subsidiaries (for example holding companies, Reliance, Tata group firms) can differ a lot between standalone and consolidated figures. Pick consolidated consistently, and record which basis each row uses.
- **Splits and bonuses:** bonuses are very common in India. Reported EPS is not retroactively adjusted in the original filing, so divide historical EPS by the cumulative adjustment factor. You can derive the factor from NSE corporate-actions data or from the price adjustment factor already implied in the user's OHLCV cache. P/E must use EPS and price on the same share basis.
- **Negative or near-zero EPS:** P/E and PEG are undefined or meaningless. Exclude them, or require EPS > 0 and growth > 0 for the PEG calculation. Cap growth rates, for example at 50 to 100%, to avoid base effects from low prior EPS.
- **Banks, NBFCs and insurers:** these follow different formats (Schedule III Division III for NBFCs under Ind AS, and the bank format under the Banking Regulation Act). They have no "revenue" or "debt/equity" in the usual sense, and ROCE is not meaningful. Use NII or total income, ROA/ROE and GNPA instead, or exclude financials from the GARP screen.
- **Corporate actions:** mergers and demergers break EPS continuity, and so do rights issues, which create a price adjustment factor that is not a split. Flag discontinuities, for example when the share count changes by more than 20% without a split or bonus.
- **Fiscal year:** almost all Indian companies use an April to March fiscal year, but a few use a calendar year, so align TTM by quarter-end dates, not by FY labels.

### Gaps
- I found no sources specific to how EODHD, FMP or yfinance handle the choice between standalone and consolidated for Indian tickers. This needs empirical testing.
- I did not source the bank and NBFC statement-format specifics (RBI and Schedule III Division III).
