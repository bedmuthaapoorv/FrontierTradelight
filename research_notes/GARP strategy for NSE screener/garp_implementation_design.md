# GARP Implementation Design for a Daily-Bar NSE Swing Screener (Nifty 500)

Scope: how best to implement a fundamental Growth-at-a-Reasonable-Price (GARP) strategy for Nifty 500 stocks, judged on its own merits. The user's existing technical swing system (5–40 day holds, OHLCV rules, sector rank, breadth regime filter, SL/TP/trailing exits) is treated as **one possible host, not a constraint**. New data feeds, holding periods and rebalancing mechanics can be built.

Four implementation archetypes are compared throughout:
- **(A) Pure GARP portfolio:** quarterly or semi-annual rebalance, fundamental sell rules.
- **(B) GARP watchlist + technical entry/exit:** CAN SLIM / SEPA / quantamental style, holds of weeks to months.
- **(C) Event-driven GARP:** entries around quarterly results, with holds of about 1 results cycle.
- **(D) GARP filter bolted onto the existing 5–40 day swing system.**

India evidence is unlabelled; global evidence is labelled [Global]. Research cut-off: October 2026. The tool budget was limited (about 18 calls), so several primary papers were seen only through abstracts or secondary summaries; this is flagged where relevant.

## 1. Hybrid designs: GARP universe filter + technical entry (CAN SLIM, SEPA, quantamental), and evidence that timing helps

### Takeaway
The standard practitioner design is to refresh a fundamental watchlist (earnings/sales growth, valuation, quality) every quarter and enter only on technical triggers (trend template, breakout, pullback, relative strength). Academic support for the combination comes indirectly from value+momentum and F-score+momentum research. That support is positive but modest, sensitive to the sample period, and mostly gross of costs. There is little rigorous evidence specific to CAN SLIM or SEPA.

### Cited Findings
- [Global] CAN SLIM: the only forward test I could find in a journal (Lutey & Rayome, 2022, *Journal of Accounting and Finance*) paper-traded the method from July 2014 to February 2017. It outperformed the S&P 500 by 20%, the Nasdaq by 9% and the Dow by 17% over that window. The window is short and the authors stopped tracking in 2017. — [Live Out of Sample Testing of CAN SLIM](https://mail.articlegateway.com/index.php/JAF/article/view/5134)
- [Global] AAII's CAN SLIM screen, backtested from end-1997, averaged 24.4% a year (third-best of its screens). It used equal-weight portfolios rebalanced monthly with **no transaction costs**, and AAII says the results are not achievable by individuals. The revised screen returned 23.8% a year from 1998 to 2007, against a cumulative 51.3% for the S&P 500. — [AAII CAN SLIM screen](https://www.aaii.com/journal/article/a-can-slim-screen-with-no-float-but-plenty-of-lift); [AAII CAN SLIM Revised](https://www.aaii.com/journal/article/investing-in-proven-growth-using-can-slim-revised)
- [Global] IBD claims about 20.7% a year for CAN SLIM, but without audited evidence. A critic blog calls the AAII backtests outdated. — [Liberated Stock Trader](https://www.liberatedstocktrader.com/what-is-canslim/)
- [Global] A WPI student project (2008, not peer reviewed) backtested 559 CAN SLIM stocks with five technical entry set-ups: Donchian, Keltner, Bollinger, MA crossover and volume breakout. It shows that "fundamental list + technical entry" is a common design. — [WPI MQP](https://digitalcommons.wpi.edu/mqp-all/3168)
- Minervini SEPA (secondary summaries only), as a reference template for a hybrid filter:
  - Trend Template: price above the 150-day and 200-day MAs, 150 > 200, 200-day MA rising for at least 1 month (ideally 4–5), 50-day MA above both, price at least 25–30% above the 52-week low and within 25% of the 52-week high.
  - Fundamentals: quarterly EPS growth of 20%+ with acceleration, and sales growth around 20%+.
  - Risk: hard stop 7–8% below entry, often tighter. One summary describes selling half at +8%, moving the stop to breakeven, and trailing the rest on the 20-day MA.
  - Thresholds vary between summaries. — [finermarketpoints SEPA guide](https://www.finermarketpoints.com/post/what-is-mark-minervini-s-trading-strategy-the-complete-sepa-vcp-guide); [TradingView Trend Template script](https://in.tradingview.com/script/OXLVw8Bx-Minervini-Trend-Template-EMA); [TradingView SEPA script](https://in.tradingview.com/script/kcihs4Hp-Minervini-SEPA-System)
- [Global] Value and momentum (Asness, Moskowitz & Pedersen, *JF* 2013): both earn positive premia and are negatively correlated, with an average within-asset-class correlation of −0.49 and about −0.60 for stocks. A simple combination therefore lies much closer to the efficient frontier than either alone. Momentum's monthly turnover cost is acknowledged. — [Value and Momentum Everywhere (NYU)](https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf); [Swedroe/ETF.com](https://www.etf.com/sections/index-investor-corner/swedroe-close-look-value-momentum)
- [Global] F-score with momentum:
  - A UK thesis (Vaasa, 2024) found only minor alpha and a higher Sharpe ratio for an F-score value portfolio filtered by momentum. It was concentrated in small caps, rebalanced annually, and ignored costs and taxes. — [Vaasa thesis](https://osuva.uwasa.fi/handle/11111/11654)
  - Walkshäusl (2020) found that F-score did *not* predict returns within high book-to-market stocks out of sample. He attributes Piotroski's original result largely to its 1976–96 sample. — [Walkshäusl 2020](https://epub.uni-regensburg.de/44019/1/Walksh%C3%A4usl2020_Article_PiotroskiSFSCOREInternationalE.pdf)
  - CXO Advisory reports value+momentum+F-score results that are gross of costs. — [CXO Advisory](https://www.cxoadvisory.com/fundamental-valuation/concentrating-the-value-premium-and-momentum-with-fscore/)
- India "quantamental" index precedent: NSE's Nifty500 Multicap Momentum Quality 50 (launched September 2024).
  - Composition: 50 stocks, fixed at 10 large, 15 mid and 25 small caps.
  - Momentum: 6- and 12-month price return, adjusted for volatility.
  - Quality: ROE, debt/equity and 5-year EPS growth variability.
  - Weighting and rebalance: weights blend the score with free-float market cap, are capped at 5%, and are rebalanced semi-annually. — [NSE press release](https://nsearchives.nseindia.com/web/sites/default/files/2024-09/ind_prs04092024.pdf); [Business Standard](https://www.business-standard.com/amp/markets/capital-market-news/nse-launches-new-multicap-momentum-quality-50-index-124090500335_1.html)
  - The June/December rebalance months come only from a third-party source (Axis Max Life) and are unverified. — [Axis Max Life](https://www.axismaxlife.com/blog/investments/what-is-nifty-500-multicap-momentum-quality-50-index)
- [India] Momentum is very strong in Indian equities: the IIMA four-factor library (Agarwalla, Jacob & Varma) reports the momentum factor averaging about 21–22% a year over 1993–2013. Value (HML) averaged about 6% and size about −0.8%. — [IIMA four-factor WP](https://web.iima.ac.in/~iffm/legacy/four-factors-India-90s-onwards-IIM-WP-Version-original-Sep13.pdf); [IIMA publication page](https://www.iima.ac.in/publication/four-factor-model-indian-equities-market)

### Inferences
- Within hybrid designs, the most common pattern is a **two-layer pipeline**. It is one option alongside a pure quarterly GARP portfolio (Section 2) and event-driven entries (Section 4):
  1. A quarterly-refreshed GARP watchlist: PEG < 1 to 1.5, positive TTM EPS, EPS/sales growth above a threshold, ROE/leverage quality screens.
  2. The existing technical entries (trendline bounce, breakout, MA pullback), plus a trend-template or RS gate, the sector rank and the breadth regime.

  In India, where momentum is the dominant premium and value is weaker, the GARP filter should be treated as a *quality and valuation guardrail* that removes junk momentum. It should not be expected to be the alpha source by itself.
- Asness et al.'s negative value–momentum correlation argues that a GARP (valuation) filter combined with momentum/trend entries should diversify drawdowns relative to pure momentum. That is a premise to test, not a proven result for NSE swing horizons.

### Gaps
- I found no peer-reviewed India study that directly tests "fundamental screen + technical entry timing" against "fundamental screen bought and held".
- I found no rigorous long-horizon academic test of CAN SLIM or SEPA, and I did not verify Minervini rules against his books.
- I could not retrieve the full NSE methodology PDF for the MQ50 index (factsheet fetch timed out), so liquidity filters and exact rebalance months are not confirmed.

## 2. Pure GARP portfolio mechanics: holdings, weighting, rebalancing, sell rules, turnover

### Takeaway
Systematic GARP products typically screen on PEG (TTM P/E divided by multi-year EPS growth, PEG < 1, positive earnings only), hold 25–50 names with weight caps, and rebalance semi-annually (index products) or monthly (research backtests). GARP's edge over the market depends heavily on the period and shrinks once loss-making firms are excluded.

### Cited Findings
- [Global] FactorResearch study (via CFA Institute):
  - Method: GARP defined as PEG < 1, where PEG = TTM P/E ÷ 3-year EPS growth. US stocks above $1bn market cap, cap-weighted, rebalanced monthly, 10 bp costs.
  - Universe: about 38% of US stocks qualify.
  - Sector mix: financials and consumer discretionary are over-represented; utilities, telecom and real estate are under-represented.
  - Returns: GARP outperformed since 1989, but much of the edge came from negative-earnings stocks and shrinks a lot when they are excluded. GARP behaved like Value after 2001. The result depends on the start date: Value was better from 2000, and the market was better from 2010.
  - The author's view is that GARP's main benefit may be the discipline it imposes. — [CFA Institute Enterprising Investor: GARP Investing: Golden or Garbage?](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- [Global] S&P/Global X GARP index: screens growth first, then quality, then valuation. It is reviewed semi-annually (June and December, or April and October for the Australian version so reviews line up with the earnings cycle). It adds or drops names that fail the growth, value or quality tests, and applies weight caps. — [Global X: Inside GARP methodology](https://www.globalxetfs.com.au/insights/post/inside-garp-methodology-rules-based-strategy/)
- [India] NSE MQ50: 50 stocks, score × free-float-cap weighting, 5% cap, semi-annual rebalance (see Section 1). — [NSE press release](https://nsearchives.nseindia.com/web/sites/default/files/2024-09/ind_prs04092024.pdf)
- [India] A public Screener.in "GARP" screen exists as a retail template (not a methodology document). — [Screener.in GARP screen](https://screener.in/screens/1952561/garp-shankarnath)
- [India] Mary Auxilia (2019, IJRISS) studied NSE mid-cap IT stocks. PEG was computed before investment from EPS CAGR and P/E, and returns were tracked for 5 years. PEG < 1 stocks gave "remarkably higher returns" than the market. The study covers a single sector, and the abstract gives no sample size or significance tests, so it is weak evidence. — [RePEc: IJRISS 2019](https://ideas.repec.org/a/bcp/journl/v3y2019i1p81-83.html)
- [India] A practitioner guide notes that Indian fast growers routinely trade at PEG > 1. It also notes that trailing, 1-year-forward and 3–5-year-CAGR growth give very different PEGs for the same stock, so the definition must be fixed and documented. — [onetradejournal PEG guide](https://onetradejournal.com/glossary/peg-ratio)
- [India] NSE factor indices (Nifty200 Momentum 30, Nifty200 Value 30): 30 stocks, score × free-float-cap tilt, weight cap of min(5%, 5× the cap weight). Rebalanced semi-annually in June and December on data to the end of May and November. — [Nifty200 Momentum30 factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf); [Nifty200 Value30 factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Value30.pdf); [NSE reconstitution calendar](https://niftyindices.com/resources/index-rebalancing-schedule)
- [India] NSE's 2026 momentum whitepaper tested quarterly vs semi-annual rebalancing:
  - Quarterly produced about 20–50% more annual churn.
  - Semi-annual showed "a slight performance edge over longer periods"; quarterly helped only marginally in some short windows.
  - NSE concluded that semi-annual is the more efficient balance. (This applies to momentum, not GARP.) — [NSE momentum strategy whitepaper 2026](https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf)
- [Global] General rebalancing research: Vanguard (summarised by Kitces) found no material difference between monthly and annual rebalancing on a rolling basis. A Netspar study found that cutting transaction costs outweighs the benefit of frequent rebalancing. — [Kitces](https://www.kitces.com/blog/best-opportunistic-rebalancing-frequency-time-horizons-vs-tolerance-band-thresholds/); [Netspar](https://www.netspar.nl/kennisplein/rebalancing-for-long-term-investors/)

### Inferences
- On its own merits, archetype **(A), a pure GARP portfolio, is the most natural home for GARP**. Fundamentals change only quarterly, the premium accrues over months, and Indian taxes and STT reward lower turnover.
- **Rebalance cadence.** A quarterly rebalance timed after the results deadlines lets the portfolio use new fundamentals. Given NSE's momentum evidence that quarterly adds churn for little gain, a good compromise is:
  - a **quarterly fundamental refresh with rank buffers**, where a name is sold only when it falls well below the cutoff or breaks a hard rule; or
  - a semi-annual full rebalance plus quarterly exception-based sells.
- Reasonable defaults for a pure-GARP portfolio on the Nifty 500:
  - 20–30 names.
  - Equal weight or score-tilted weights with a 5% cap.
  - Sector cap of about 25–30%, because financials are over-represented under PEG screens (the global finding above; Indian index skews point the same way).
  - Rebalance quarterly, about 2–3 weeks after the 45- and 60-day result deadlines (Section 5).
- Plausible sell rules (practitioner convention; I found no source testing them):
  - PEG rising above about 1.5–2.
  - TTM EPS growth falling below threshold for 2 consecutive quarters.
  - Earnings turning negative.
  - Falling out of the top N on the composite score, using a buffer (for example, hold until rank > 2N) to cut turnover.
  - An optional catastrophic stop or 200-day MA break.
- Exclude negative or near-zero EPS before computing PEG, since the CFA study shows these drive spurious outperformance.

### Gaps
- I could not find smallcase's published GARP or quality-momentum methodology. The search returned no smallcase-specific document.
- I found no published turnover figures for GARP indices or for the NSE MQ50.

## 3. Holding period: over what horizon does GARP's edge play out? Does it survive 5–40 day holds?

### Takeaway
Fundamental (value and growth-at-a-price) premia are slow and are usually studied with monthly to annual rebalancing. Their edge accrues over months, and over any 5–40 day window it is swamped by price noise. The parts that do work on shorter horizons are price momentum (very strong in India) and the earnings-announcement drift, which runs over about 60 trading days.

Implications by archetype:
- **(A) Pure GARP:** holds of 3–12 months, matching how the premia are measured.
- **(C) Event-driven:** about 1 results cycle (roughly 60 trading days).
- **(B) Watchlist + technical:** open-ended holds governed by trailing stops plus fundamental re-qualification.
- **(D) 5–40 day swing:** the GARP filter acts only as a quality guardrail, and most of the per-trade edge must come from the technical signal.

### Cited Findings
- [Global] PEAD (Bernard & Thomas, 1989/1990):
  - The top-minus-bottom SUE decile spread was positive in 41 of 48 quarters (1974–85).
  - Secondary sources put it at about 4.2% over 60 trading days, or about 2% each for the long and short sides. Another blog figure of 8–9% per quarter is unverified.
  - Canadian replication: more than 6% over 60 days using analyst-based SUE. — [Wikipedia: PEAD](https://en.wikipedia.org/wiki/Post%E2%80%93earnings-announcement_drift); [Fink 2020 WP](https://static.uni-graz.at/fileadmin/sowi/Working_Paper/2020-04_Fink.pdf); [Freeport Logbook](https://freeportlogbook.substack.com/p/post-earnings-announcement-drift); [Canadian study](https://research.monash.edu/en/publications/is-trading-on-earnings-surprises-a-profitable-strategy-canadian-e/)
- [India] IIMB (Kudalkar & Chandra, 2014) defines PEAD as drift lasting up to about 2 months and finds it present in Indian markets. SUE with absolute-value bucketing worked best as the surprise measure. — [IIMB repository 2074/20501](https://repository.iimb.ac.in/handle/2074/20501)
- [India] A second IIMB study (120-day window) found drift plus pre-announcement price movement, meaning surprises are partly priced in beforehand. — [IIMB repository 2074/17935](https://repository.iimb.ac.in/handle/2074/17935)
- [India] Value premium: the IIMA HML factor averaged about 6% a year against about 21% for momentum (1993–2013). — [IIMA four-factor WP](https://web.iima.ac.in/~iffm/legacy/four-factors-India-90s-onwards-IIM-WP-Version-original-Sep13.pdf)
- [India] The momentum factor used by IIMA and NSE is built on 6–12 month formation and is rebalanced monthly or semi-annually, not daily. — [IIMA](https://www.iima.ac.in/publication/four-factor-model-indian-equities-market); [NSE press release](https://nsearchives.nseindia.com/web/sites/default/files/2024-09/ind_prs04092024.pdf)
- [Global] Value and momentum need monthly or longer rebalancing, and momentum turnover is costly. — [Value and Momentum Everywhere](https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf)

### Inferences
- A 5-day hold captures almost none of a GARP premium. A 20–40 day hold aligns with PEAD (about 60 trading days) and with the short end of momentum.
- Ranking of designs by fit to where the evidence says the edge lives: (A) ≈ (B) > (C) > (D).
  - **(B) Watchlist + technical:** keep a protective initial stop. Use no fixed take-profit; trail with a 50-day MA or ATR, and re-qualify fundamentals at each results release.
  - **(C) Event-driven:** enter after a strong result, and hold to the next result date unless stopped out.
  - **(D) Swing:** if kept, replace fixed TP with a trailing stop for GARP-qualified names and allow holds beyond 40 days.
- Running GARP as a **separate, slower sleeve** next to the swing strategies is likely to work better than forcing it into the 5–40 day framework, and it diversifies the overall book. This is consistent with the negative value–momentum correlation (Section 1).

### Gaps
- I found no study measuring a GARP or PEG premium specifically at 1–8 week horizons, in India or globally.
- I could not access the original Bernard & Thomas papers to confirm the 60-day magnitudes.

## 4. Event timing: quarterly results (earnings surprise, PEAD) as GARP entry triggers in India

### Takeaway
Indian evidence on PEAD is mixed:
- Older IIMB and event studies find drift, especially after *bad* news (asymmetric).
- A 2021 NSE study (2014–18, 100 firms) finds no exploitable drift and no consistent value–glamour edge, with results that vary by liquidity.

Use results as a *catalyst filter and timing anchor* (for example, a gap-up or breakout on results day with strong YoY growth), not as a standalone edge. Use bad-news drift mainly as an exit or avoid signal.

### Cited Findings
- [India] Nottingham event study: the market reacts efficiently to good news, but bad news produces negative drift lasting more than a week, most visible in the 2009–10 bull market. — [Nottingham eprints 26569](https://eprints.nottingham.ac.uk/26569)
- [India] Gupta & Dhusia (2021, *Trends Economics and Management*):
  - Sample: 100 NSE firms, 2014–18, 1,130 observations.
  - Finding: the market is efficient around earnings announcements and there are no excess returns. Value–glamour strategies do not deliver consistent superior returns, and results vary by liquidity. — [VUT journal](https://journals.lib.vutbr.cz/index.php/trends/article/view/541); [econstor](https://www.econstor.eu/handle/10419/308924?locale=de)
- [India] Kudalkar & Chandra (IIMB 2014): PEAD present, lasting up to about 2 months, with SUE as the best measure. — [IIMB](https://repository.iimb.ac.in/handle/2074/20501)
- [India] IIMB: pre-announcement price movement exists. — [IIMB](https://repository.iimb.ac.in/handle/2074/17935)
- [India] An *Journal of Contemporary Accounting & Economics* (2009) paper on earnings surprise and sophisticated investor preferences in India exists; I did not review its findings. — [RePEc](https://ideas.repec.org/a/eee/jocaae/v5y2009i1p1-19.html)

### Inferences
- Practical trigger without analyst-consensus data, which most Indian retail data feeds lack: a time-series SUE proxy.
  - Formula: (EPS_q − EPS_{q−4}) ÷ std of the last 8 seasonal differences.
  - Combine it with the results-day price reaction (an earnings-announcement return such as gap% or 2-day abnormal return vs Nifty 500) and volume of at least 2× the 50-day average.
  - Enter on day 1–3 after results, or on the first pullback or base breakout within the following 2–6 weeks.
- Because of the bad-news drift asymmetry: exit or block entries in held names that post negative surprises.
- Because of pre-announcement drift and the efficiency finding for large liquid names: expect any edge to be concentrated in less-liquid mid and small caps, where costs and slippage are higher (Section 6).

### Gaps
- I found no recent (2020+) India PEAD study covering the Nifty 500 with costs. The most recent one (2014–18, 100 firms) is small.
- I found no Indian source for exact result-announcement timing behaviour (for example, intraday vs after-hours filing shares).

## 5. Backtesting a hybrid correctly: point-in-time data, reporting lags, Indian costs, overfitting

### Takeaway
The biggest risks are look-ahead bias from using fundamentals before they were public, survivorship in Nifty 500 membership, and underestimating Indian delivery costs. STT alone is 0.1% each side, so the minimum is about 0.25–0.3% per round trip before slippage. Align fundamental data to *filing date*, not quarter-end. Lag rebalances past the SEBI deadlines.

### Cited Findings
- [India] SEBI LODR Reg 33 deadlines:
  - Quarterly standalone results within **45 days** of quarter-end for Q1–Q3. The calendar due dates are about 14 August, 14 November and 14 February.
  - Q4 and annual audited results within **60 days** (about 30 May; one calendar shows 15 May for Q4 standalone if filed separately).
  - Consolidated annual results required where subsidiaries exist.
  - C&AG-audited PSUs have special timelines.
  - Regulations are amended often, so check the current text. — [Taxmann compliance calendar](https://www.taxmann.com/post/blog/compliance-calendar-for-the-listed-entities-under-sebi-lodr-norms/); [KPMG LODR note](https://assets.kpmg.com/content/dam/kpmg/in/pdf/2023/01/vor-sebi-lodr-regulations-icai-mutual-funds.pdf); [TaxGuru](https://taxguru.in/sebi/sebi-listing-regulations-financial-results-annual-reportinformation.html)
- [India] Delivery trade costs (third-party 2026 figures):
  - Brokerage: ₹0 at discount brokers.
  - STT: 0.1% on buy plus 0.1% on sell.
  - NSE transaction charge: about 0.00322%.
  - Stamp duty: 0.015% on buys.
  - GST: 18% on brokerage and exchange charges.
  - Zerodha's charge list also shows the investor protection fund levy. Verify on the broker page. — [StockCalc 2026](https://stockcalc.in/blog/stock-broker-charges-india-2026); [Zerodha charges](https://zerodha.com/charges)
- [Global] Cost-free backtests overstate results. AAII's CAN SLIM backtests and the Vaasa and CXO F-score studies exclude costs, and the FactorResearch GARP test assumed 10 bp. — [AAII](https://www.aaii.com/journal/article/a-can-slim-screen-with-no-float-but-plenty-of-lift); [Vaasa](https://osuva.uwasa.fi/handle/11111/11654); [CFA](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)
- [Global] Fundamental-anomaly results are sample-period dependent. F-score's edge largely disappears outside 1976–96 (Walkshäusl), and GARP's ranking vs Value and the market flips with the start date (FactorResearch). — [Walkshäusl](https://epub.uni-regensburg.de/44019/1/Walksh%C3%A4usl2020_Article_PiotroskiSFSCOREInternationalE.pdf); [CFA](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)

### Inferences
- **Point-in-time rule.** Stamp each fundamental record with its exchange filing date (from NSE/BSE corporate announcements) and make it usable from the next trading day. If filing dates are unavailable, use conservative fixed lags: quarter-end + 45 days for Q1–Q3 and + 60 days for Q4. Lagging to the deadline avoids look-ahead bias but discards the early-filer PEAD signal.
- **Restatements.** Use as-first-reported figures where possible. Screener-style databases often overwrite history with restated or consolidated numbers.
- **Survivorship.** Use historical Nifty 500 constituent lists, which change with NSE's semi-annual reconstitutions, and include delisted stocks.
- **Costs.** Model about 0.25% fixed per round trip (STT 0.2% + stamp + exchange + GST), plus slippage scaled to liquidity: about 0.05–0.1% for large caps and 0.2–0.5%+ for small caps. These slippage figures are my assumptions, not sourced. A 5–10 day strategy with an average gain of 2–3% loses roughly 10%+ of its edge to costs. Longer GARP holds amortise costs better.
- **Taxes.** Short-term capital gains (under 12 months) are taxed higher than long-term; the post-July-2024 rates are 20% STCG vs 12.5% LTCG from my training data and should be verified. This structurally favours multi-month GARP holds over short swings for a taxable account.
- **Overfitting controls.**
  - Use coarse threshold grids (for example, PEG ≤ 1.0, 1.5 or 2.0; EPS growth ≥ 15%, 20% or 25%) and require stability across neighbouring values.
  - Use walk-forward or rolling out-of-sample windows that span regimes (2008, 2015–16 small-cap correction, 2018–19 small-cap bear market, 2020 crash, 2024–25 small-cap correction).
  - Report results by market-cap bucket and sector.
  - Compare against simple benchmarks: Nifty 500 TRI, and the same technical entries without the GARP filter. This isolates the filter's contribution.

### Gaps
- I found no authoritative 2026 source confirming current STT rates or capital-gains tax rates. Verify against Income Tax / Finance Act 2024–26 and the broker page.
- I did not identify a free point-in-time Indian fundamentals source. CMIE Prowess (used by IIMA) is commercial.

## 6. Indian-market specifics: SEBI rules, Nifty 500 mid/small-cap liquidity, sector skew, regimes

### Takeaway
Liquidity in the Smallcap 250 segment is a binding constraint for scale, and fundamentally screened growth names often sit there. Size positions by ADV and cap sector exposure. Regimes matter: small-cap bear markets and the post-2024 SEBI scrutiny of mid/small-cap froth both argue for keeping the breadth regime filter on GARP entries.

### Cited Findings
- [India] Since March 2024, SEBI requires monthly mid/small-cap mutual fund stress-test disclosures (days to liquidate 25% or 50% of the portfolio), driven by concern over heavy inflows. Example figures:
  - SBI Small Cap: about 58–60 days for 50%.
  - Nippon Small Cap: 27–29 days.
  - Quant Small Cap: 22–30 days.
  - Quant Mid Cap: 10 days. — [Business Standard](https://www.business-standard.com/finance/personal-finance/explained-should-small-cap-funds-stress-test-results-worry-you-124031800197_1.html); [Angel One](https://www.angelone.in/news/mutual-funds/sebi-mutual-fund-stress-test-results); [Outlook Money](https://www.outlookmoney.com/invest/mutual-funds/mf-stress-tests-show-mid-cap-small-cap-schemes-improving-liquidity-know-results-of-largest-funds)
- [India, secondary/unverified] A report citing SEBI's FY26 annual report says that in March 2026 the top-10 small-cap schemes averaged 38 days to liquidate 50%, against 17 days for mid-cap schemes. — [askfuzz](https://askfuzz.ai/discover/news/mutual-funds/small-cap-funds-face-valuation-challenges-in-2026)
- [India] Liquidity affects whether earnings-announcement drift exists on NSE (Gupta & Dhusia found heterogeneity by liquidity). — [VUT journal](https://journals.lib.vutbr.cz/index.php/trends/article/view/541)
- [India] NSE factor indices handle size and sector concentration with fixed cap-bucket quotas and 5% single-stock caps. MQ50 forces 25 of 50 names from the Smallcap 250. — [NSE press release](https://nsearchives.nseindia.com/web/sites/default/files/2024-09/ind_prs04092024.pdf)
- [India] PEAD inefficiency was most visible in the 2009–10 bull market. — [Nottingham](https://eprints.nottingham.ac.uk/26569)
- [Global] PEG screens over-weight financials and consumer discretionary. — [CFA](https://rpc.cfainstitute.org/blogs/enterprising-investor/2019/garp-investing-golden-or-garbage)

### Inferences
- **Financials.** P/E-based PEG and debt/equity screens are poorly suited to banks and NBFCs. Either exclude financials from the GARP filter or use sector-specific metrics: P/B vs ROE, loan growth, gross/net NPA. Without this, the watchlist skews toward lenders.
- **Liquidity gates.** Apply a minimum median 20-day traded value (for example, ₹5–10 crore a day for small caps; my assumption) and cap position size at about 1–5% of ADV.
- **Circuit limits.** Watch price bands and ASM/GSM surveillance lists, since stocks under surveillance have trade restrictions.
- **Regime.** Keep the existing breadth regime filter on GARP entries, and consider a separate small-cap breadth or trend filter (Nifty Smallcap 250 above its 200-day MA). Small-cap drawdowns dominate hybrid-strategy losses.
- **New data/infrastructure needed for any GARP archetype** (my inference):
  - Quarterly P&L and balance-sheet history, stamped with filing dates.
  - A results-calendar feed (NSE board-meeting intimations and financial-results announcements).
  - Point-in-time Nifty 500 constituents.
  - A portfolio-level rebalancer (target weights, buffers, caps), as opposed to per-signal SL/TP trades.
- **Pure-GARP (A) reference spec:**
  - Universe: Nifty 500, liquidity-gated, financials scored separately.
  - Score: rank-average of PEG (lower is better), EPS and sales growth, ROE, low D/E.
  - Portfolio: top 25–30, equal weight, 5% name cap, about 25% sector cap.
  - Rebalance: quarterly about 2 weeks after the 45/60-day deadlines, with a rank buffer.
  - Sells: falling out of the top 2N, PEG > 2, EPS turning negative or growth below threshold for 2 quarters, or an optional 200-day MA or −25% catastrophic stop.
  - Regime: optionally move to cash or reduce the small-cap share when breadth is risk-off.
- **Hybrid (B/D) composite architecture for the screener**:
  1. **Quarterly (post-deadline) GARP watchlist:**
     - Positive TTM EPS.
     - TTM EPS growth ≥ 15–20% and sales growth ≥ 10–15%.
     - PEG ≤ 1.5 (non-financials).
     - ROE ≥ 12–15%, D/E ≤ 1.
     - Optional: no EPS growth deceleration across 2 quarters.
  2. **Daily technical gate:** trend template (above the 50/150/200-day MAs, near the 52-week high), RS/sector rank in the top tercile, breadth regime on.
  3. **Entry triggers:** the existing trendline bounce or breakout, a pullback to the 20/50-day MA, or a results-day gap/volume event (SUE proxy > 0).
  4. **Risk:** initial ATR- or 7–8% stop, position size by risk, ADV caps.
  5. **Exit:**
     - Trailing MA/ATR stop instead of a fixed TP for GARP names.
     - Hard exit on a negative earnings surprise, or on the stock failing the watchlist at the next refresh.
     - Max hold of about 60 trading days or one results cycle, then re-qualify.
  6. **Validation:** walk-forward with point-in-time fundamentals and full Indian costs, compared against the same technical system without the GARP filter.

### Gaps
- I could not verify the 2026 SEBI annual-report stress-test figures from a primary source.
- I found no source quantifying the sector composition of PEG screens on the Nifty 500 specifically.
- I did not research the 2025–26 SEBI changes to mid/small-cap classification or surveillance frameworks (ASM/GSM thresholds) in depth.
