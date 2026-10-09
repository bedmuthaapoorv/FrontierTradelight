# NSE Execution Realities for a Daily-Bar Long-Only Swing Exit Strategy (1-90 day delivery holds)

Grading key used throughout: **[Official/rigorous]** = exchange/regulator/broker official schedule or peer-reviewed study; **[Practitioner]** = broker education/blog, trade press summarising official material; **[Anecdotal]** = forum posts, illustrative examples.

Research date: 2026-10-06. Several important rule changes landed in 2026 (Closing Auction Session from 3 Aug 2026, pre-open revamp from 7 Sep 2026, F&O STT hike from 1 Apr 2026) and are flagged with dates.

## 1. Price bands / circuit limits and unfillable stops

### Takeaway
Non-F&O NSE stocks have fixed daily bands of 2/5/10/20%. F&O stocks have a dynamic 10% band that flexes in 5% steps, so in practice they do not lock at a circuit. A stop on a non-F&O stock, especially a small-cap or one under surveillance, can be unfillable for one or more sessions. I found no published statistic on how often lower-circuit locks happen, so the backtest has to model the risk explicitly.

### Cited Findings
- Each stock gets a fixed daily price band, usually 2%, 5%, 10% or 20%. The band depends on liquidity, price and surveillance category, not on how the market moves that day. [Practitioner] — [Rupeezy support](https://support.rupeezy.in/support/solutions/articles/21000004845-what-are-circuit-limits-or-price-bands); [Geojit support](https://support.geojit.com/support/solutions/articles/89000007110-what-are-price-bands-and-circuit-breakers-)
- Stocks with derivatives have no fixed band. They get a dynamic band of 10% of the previous close, which is "flexed" by 5% at a time in the direction of the move when the last traded price nears the band. [Practitioner, summarising NSE] — [Rupeezy support](https://support.rupeezy.in/support/solutions/articles/21000004845-what-are-circuit-limits-or-price-bands); NSE's official page is [equity-market-price-bands](https://www.nseindia.com/static/products-services/equity-market-price-bands) (it timed out when I tried to fetch it, so this is not independently verified).
- NSE changes a stock's band based on its trading behaviour, volatility and participation. Triggers include volatility, liquidity, corporate actions, reclassification, and entry to or exit from F&O. [Practitioner] — [Chittorgarh FAQ](https://www.chittorgarh.com/faq_pg/what-is-price-band-change-in-nse/5423/). Daily lists of the 2%/5%/20% band stocks are at [Chittorgarh 2% list](https://www.chittorgarh.com/report/stock-nse-circuit-filters/120/2/) and [5% list](https://www.chittorgarh.com/report/stock-nse-circuit-filters/120/5/).
- Stocks under GSM (Graded Surveillance Measure) trade with a band of 5% or lower at every stage (I-IV). ASM (Additional Surveillance Measure) stages add 100% margin, once-a-week trading, and 5% or 2% bands at higher stages. [Practitioner] — [Groww GSM explainer](https://groww.in/blog/graded-surveillance-measure); [Bajaj Broking ASM/GSM](https://bajajbroking.in/blog/decoding-asm-and-gsm-frameworks-and-stages)
- Market-wide circuit breakers trigger on Nifty 50 or Sensex moves of 10%, 15% or 20%:
  - 10% before 1:00 pm: 45-minute halt plus a 15-minute pre-open call auction.
  - 10% between 1:00 and 2:30 pm: 15-minute halt.
  - 10% at or after 2:30 pm: no halt.
  - 15% before 1:00 pm: 1 hour 45 minutes halt.
  - 15% on or after 2:00 pm: trading halts for the rest of the day.
  - 20% at any time: trading halts for the rest of the day.
  
  [Official] — [BSE MWCB page](https://bseindia.com/static/about/mwcb.htm); [NSE circuit breakers](https://www.nseindia.com/static/products-services/equity-market-circuit-breakers)
- A stock locked at its lower circuit has only sell orders and no buyers, so a sell limit cannot fill and the stock can stay locked all session. A stop-loss whose limit price is inside the band will not execute if the price moves beyond the band. [Practitioner] — [Tradejini](https://www.tradejini.com/blogs/why-your-stoploss-doesnt-work-during-gap-opens); [Kotak Securities support](https://kotaksecurities.com/support/how-is-it-possible-for-the-price-to-hit-the-market-but-the-stop-loss-sl-was-not-triggered)
- On NSE, SL-M (stop-loss market) guarantees execution but not price. SL-L (stop-loss limit) guarantees price but may never execute. [Practitioner] — [OneTradeJournal](https://onetradejournal.com/glossary/stop-loss-order)

### Inferences
- **How to model this in a backtest.** On a day when the bar is locked at the lower circuit (low == high == close == previous close × (1 − band), or very low volume with close at the band floor), assume the stop does **not** fill. Carry the exit to the next day that is not locked, and fill at that day's open, or at the next bar with low > lower band. This needs each stock's historical band per date. If that history is not stored, a fallback is to treat any non-F&O daily bar with a close-to-close drop at or near −5/−10/−20% and open ≈ low ≈ close as locked.
- For F&O stocks, dynamic band flexing means a lock is very unlikely. Stop fills can still be much worse than planned because of overnight gaps (section 2).
- Breakout systems tend to buy small and mid-caps with fresh momentum, which are often non-F&O stocks with 5-20% bands. A universe filter (for example F&O-eligible only, or excluding 2%/5% band stocks and anything in ASM/GSM) removes most of the lock risk.
- Upper-circuit locks also matter for entries. A breakout bar that closes locked at the upper circuit may not have been buyable at the close. The backtest should skip or delay entries on upper-circuit-locked bars.

### Gaps
- I found no published frequency for lower-circuit locks by band or market-cap bucket, and no figure for how many consecutive days locks last on NSE. This would need to be measured from bhavcopy data (count days where close = lower band and high = low).
- I could not verify the exact NSE rules on the official price-band page because the fetch timed out: the default band for a newly listed non-F&O stock, the weekly review cadence, and the criteria that move a stock to a 2% band.

## 2. Overnight gaps and slippage beyond stops

### Takeaway
Overnight gaps are the main reason realised stop losses on NSE end up worse than planned. Results and other news land outside market hours, and the next morning's opening price is set in the 9:00-9:15 call auction. I found **no rigorous published statistics** on NSE stock-level gap-down frequency or average slippage beyond stops; the practitioner sources are qualitative.

### Cited Findings
- The stop trigger price is not a guaranteed exit price. In a gap-down the order fills at the next available price. One illustrative example: buy at ₹500, stop at ₹475 (5% planned risk), stock gaps to ₹430, fill at ₹428, a 14% realised loss. [Anecdotal/illustrative] — [Tradejini](https://www.tradejini.com/blogs/why-your-stoploss-doesnt-work-during-gap-opens)
- Expected fill quality by liquidity tier: large index stocks fill "close to trigger", liquid midcaps see "noticeable slippage", and illiquid small caps see heavy slippage or no fill if locked. These are not quantified. [Practitioner] — [Tradejini](https://www.tradejini.com/blogs/why-your-stoploss-doesnt-work-during-gap-opens); [OneTradeJournal](https://onetradejournal.com/glossary/stop-loss-order)
- The overnight anomaly (most returns earned close-to-open, intraday returns flat or negative) has been tested on Indian indices and stocks. [Practitioner summary] — [Multibagg Nifty overnight study summary](https://www.multibagg.ai/market-pulse/articles/nifty-overnight-intraday-returns-study-cmqxr9lq34t09o20jum5tsveq)
- In decompositions of strategy profits, **all of the abnormal return on momentum strategies accrues overnight**, while other strategies earn theirs intraday. This is US-centric academic work. [Official/rigorous, not India-specific] — [LSE "A tug of war: overnight versus intraday expected returns"](https://researchonline.lse.ac.uk/id/eprint/119010)
- An NSE microstructure study found daytime return variance higher than overnight variance, and opening-return variance higher than closing-return variance. [Official/rigorous, older study] — [Artha Vijnana / i-scholar](https://mail.i-scholar.in/index.php/ArthaVij/article/view/115414)
- Many Indian companies announce results after market hours, so the price reaction happens at the next open. [Practitioner] — [Swastika post-market earnings shock](https://www.swastika.co.in/blog/post-market-earnings-shock-how-after-hours-results-move-stocks-before-opening-bell)

### Inferences
- **Stop fill rule for the backtest.** If the open is below the stop level, fill at the open, not at the stop. If the open is above the stop and the low trades through it, fill at the stop minus an adverse slippage allowance. This is the standard conservative daily-bar rule. Any backtest that fills at the stop price on gap days overstates performance.
- Because momentum returns are earned overnight, exiting before the close to avoid gap risk would also give up much of a breakout strategy's edge. Holding overnight is structural to the strategy, so gap risk should be handled through position sizing (risk per trade that assumes the stop can be overshot) rather than through avoidance.
- Slippage allowances: there is no Indian data to anchor them, so test with 0.1-0.3% for large caps and 0.5-1%+ for small caps on stop exits. This is my judgement, not sourced, and should be sensitivity-tested.

### Gaps
- I found no published distribution of NSE single-stock overnight gaps (for example the share of days with a gap-down beyond −3% or −5% by market cap) and no figure for average slippage beyond stops. Both would need to be measured from the project's own OHLC data, for example open/prev_close − 1 across the Nifty 500 universe, split by results-window vs normal days.

## 3. Pre-open call auction and closing price mechanics (changed in 2026)

### Takeaway
The NSE "close" printed on daily bars is not the last trade. Until 2 Aug 2026 it was the 3:00-3:30 pm VWAP for all stocks. **From 3 Aug 2026, F&O stocks close at a Closing Auction Session (CAS) equilibrium price**, while non-F&O stocks keep the 30-minute VWAP. A backtest that buys or sells "at the close" is assuming a price that a trader could not have hit exactly before 3 Aug 2026, and cannot hit with stop orders in the CAS (they are cancelled).

### Cited Findings
- Before the change, the official close was the volume-weighted average price of all trades from 3:00 to 3:30 pm. If there were no trades in that window, the last traded price was used. [Practitioner, consistent with NSE practice] — [Equities India glossary](https://equitiesindia.com/glossary/closing-price-weighted-average); [TradingQnA](https://tradingqna.com/t/why-is-there-a-difference-between-last-trading-price-and-closing-price-on-nse/3848)
- The **Closing Auction Session (CAS) started on 3 August 2026** for F&O stocks in the cash market:
  - F&O stocks trade continuously until 3:15 pm, then the CAS runs 3:15-3:35 pm.
  - Non-F&O stocks still trade until 3:30 pm.
  - Stock and index F&O contracts trade until 3:40 pm.
  
  [Official/government news] — [All India Radio / NewsOnAir, 2 Aug 2026](https://newsonair.gov.in/nse-to-introduce-new-method-for-closing-price-discovery-through-closing-auction-session-from-tomorrow/); [Goodreturns](https://www.goodreturns.in/news/nse-new-rule-from-today-closing-auction-session-begins-for-f-o-stocks-check-new-closing-price-rule-1525791.html); [Anand Rathi](https://anandrathi.com/blog/nse-extends-trading-hours)
- CAS phases: [Practitioner, detailed; cites SEBI circular HO/47/11/11(3)2025-MRD-POD2/I/2765/2026 dated 16 Jan 2026] — [Sahi CAS guide](https://www.sahi.com/blogs/closing-auction-session-cas-explained-nse-bse-closing-price-rules-2026)

  | Time | What happens |
  |------|--------------|
  | 3:00-3:15 pm | Reference price is built as the VWAP of trades in this window |
  | 3:15-3:20 pm | Reference price is published; no order entry |
  | 3:20-3:25 pm | Market and limit orders accepted |
  | 3:25-3:30 pm | Limit orders only; the session ends at a random time between 3:28 and 3:30 |
  | 3:30-3:35 pm | Orders are matched and the closing price is set |

  Further rules from the same source:
  - Auction orders must sit within **±3% of the reference price**.
  - The closing price is the single price that matches the largest quantity. If no match occurs, the reference price becomes the close.
  - **Stop-loss and iceberg orders are cancelled automatically** in the CAS.
  - The change applies to "Category I" stocks (those with F&O) on NSE, BSE and MSEI. Category II stocks keep the 3:00-3:30 VWAP close.
- The same source says the **pre-open session was restructured from 7 Sep 2026** on the same auction principles: 9:00-9:15 am, with a random close between 9:08 and 9:10. [Practitioner, single source; not independently verified]
- On day one of the CAS, NSE reported strong participation. [Practitioner] — [Angel One](https://www.angelone.in/news/market-updates/nse-reports-strong-participation-on-day-1-of-closing-auction-session-for-f-o-stocks)

### Inferences
- **Before Aug 2026:** a trader could only approximate the official close, for example by executing across 3:00-3:30. A single order at about 3:25 based on a "close above breakout level" signal executes near, but not at, the bar close. Model a small adverse cost (for example 0.05-0.15% for liquid stocks; my assumption) on "at close" fills, or more conservatively use the next day's open.
- **After Aug 2026, F&O stocks:** a trader can actually transact at the official close by placing limit or market orders in the CAS. "Signal on close, fill at close" is now realistic for F&O names, but the signal must be computed from data available at about 3:15-3:25 pm, not from the final close. There is look-ahead risk if the rule depends on the exact closing value or the day's full volume.
- **Stops cannot rest through the CAS**, because SL orders are cancelled. A daily-close-based stop ("exit if close < X") has to be executed as a CAS order or as a next-day open order. A system that relies on resting intraday stops will find them cancelled at 3:15 for F&O stocks.
- Historical data matters. NSE bhavcopy has separate CLOSE and LAST fields, and backtests should use CLOSE consistently. Bars before and after 3 Aug 2026 for F&O stocks are produced by different closing mechanisms, which is a minor structural break.
- The opening price comes from the pre-open call auction. "Fill at open" in a backtest is therefore achievable in principle with a pre-open order (market or limit) placed 9:00-9:08.

### Gaps
- I could not access the NSE CAS circular directly. The ±3% band, the random-close details and the 7 Sep 2026 pre-open change rest on one practitioner source (Sahi), which cites the SEBI circular number. Verify on nseindia.com before treating them as hard rules.
- I found no data on how far the official VWAP close typically differed from the last traded price before Aug 2026.

## 4. Round-trip transaction costs for delivery trades (2026)

### Takeaway
At a zero-brokerage discount broker, a delivery round trip costs about **0.23-0.24%** of trade value in statutory charges for a ₹1-5 lakh position. STT (0.1% on each side) is about 85% of that. Add spread and impact cost of a few basis points for large caps and much more for small caps. A conservative all-in assumption of **0.3% round trip for liquid stocks and 0.5-1% for small/micro caps** is reasonable.

### Cited Findings
- Charges per Zerodha's official charges page for equity delivery: [Official, broker schedule] — [Zerodha charges](https://zerodha.com/charges)

  | Charge | Rate |
  |--------|------|
  | Brokerage | ₹0 |
  | STT | 0.1% on buy and 0.1% on sell |
  | NSE transaction charge | 0.00307% (BSE 0.00375%) |
  | SEBI fee | ₹10 per crore |
  | GST | 18% on brokerage + SEBI fee + transaction charges |
  | Stamp duty | 0.015% on buy only (capped at ₹1,500 per crore) |
  | DP charge | ₹15.34 per scrip per sell day (₹3.5 CDSL + ₹9.5 Zerodha + GST) |

- **Source conflict on the NSE transaction charge:** a third-party calculator lists 0.00322% instead of the 0.00307% on Zerodha's page. [Practitioner] — [StockCalc Zerodha 2026](https://stockcalc.in/blog/zerodha-brokerage-charges-2026-full-breakdown). The difference is immaterial (about 0.0003% per side). Use Zerodha's figure as primary.
- **Budget 2026 left delivery STT unchanged** at 0.1% on buy and sell. Futures STT rose from 0.02% to 0.05%, and options premium STT from 0.1% to 0.15%, both effective 1 Apr 2026. [Practitioner, multiple consistent sources] — [Groww STT](https://groww.in/blog/what-is-stt); [ICICI Direct](https://www.icicidirect.com/ilearn/futures-and-options/articles/stt-changes-in-budget-2026-what-f-o-traders-should-know)
- Liquidity benchmark: Nifty 50 inclusion requires impact cost ≤ 0.50% for a ₹10 crore basket order in at least 90% of observations over six months. [Official] — [NSE Nifty 50 methodology factsheet](https://archives.nseindia.com/content/indices/ind_nifty50.pdf); [Equities India impact cost](https://equitiesindia.com/glossary/impact-cost)

**Worked examples** (my arithmetic from Zerodha's rates):

| Charge | ₹1,00,000 buy + ₹1,00,000 sell | ₹5,00,000 buy + ₹5,00,000 sell |
|--------|-------------------------------|-------------------------------|
| STT | ₹200 | ₹1,000 |
| NSE transaction charge | ₹6.14 | ₹30.70 |
| SEBI fee | ₹0.20 | ₹1.00 |
| GST | ₹1.14 | ₹5.71 |
| Stamp duty | ₹15 | ₹75 |
| DP charge | ₹15.34 | ₹15.34 |
| **Total** | **≈ ₹238 (0.238% of buy value)** | **≈ ₹1,128 (0.226%)** |

The DP charge is a flat ₹15.34 per sell, so it matters more for small trades: about 0.15% extra on a ₹10,000 position.

### Inferences
- In a backtest, model costs as about 0.12% on buy (0.1% STT + 0.015% stamp + ~0.004% exchange charge/GST) and about 0.105% on sell plus ₹15.34 per exit. Add a separate slippage/impact term.
- At about 0.24% plus spread per round trip, short holds and frequent stop-outs are expensive. A rule that produces many 1-3 day trades with average gains under about 1% will be cost-dominated. This argues against very tight stops.
- Impact cost for a retail-sized order (₹1-10 lakh) in Nifty 100 stocks is likely a few basis points. For small caps with thin books it can reach tens of basis points. This is my inference; I found no current NSE-published per-stock figures.

### Gaps
- I did not retrieve current NSE-published impact cost figures per stock or per index (for example average impact cost of Nifty Midcap 150 or Smallcap 250 constituents).
- Other discount brokers' 2026 delivery brokerage was not checked individually (Groww and Upstox may charge a small fee per delivery order).

## 5. Tax treatment (context only)

### Takeaway
For listed equity sold on or after 23 Jul 2024: gains on holdings of 12 months or less are taxed as STCG at 20% (Sec 111A); longer holdings pay LTCG at 12.5% above ₹1.25 lakh a year (Sec 112A). A 90-day maximum hold is always STCG, so tax does not affect holding-period design inside 1-90 days.

### Cited Findings
- From 23 Jul 2024, LTCG on listed equity rose from 10% to 12.5% and the exemption from ₹1 lakh to ₹1.25 lakh. STCG under Sec 111A rose to 20% (from 15%). The holding period for LTCG is more than 12 months. [Practitioner, consistent across many tax sites] — [ClearTax](https://cleartax.in/s/ltcg-sale-stocks); [Quicko 112A](https://learn.quicko.com/ltcg-equity-shares-equity-mutual-funds)

### Inferences
- Tax is a flat 20% on net short-term gains for every trade in the strategy's range, so it does not shape exit rules within 1-90 days. STT is not deductible against capital gains, so it is a true cost.

### Gaps
- I did not check whether Budget 2026 (Feb 2026) changed the capital-gains rates. The sources I found give the July 2024 rates as current, and none mentioned a 2026 change.

## 6. T+1 settlement, BTST short-delivery risk, and surveillance (ASM/GSM)

### Takeaway
With T+1 settlement, shares bought on day T reach the demat account on T+1. Selling them on T+1 (BTST) is possible but carries short-delivery auction risk if the original seller defaults. For a strategy whose stop can trigger the day after entry, this is a small but real risk. ASM/GSM surveillance can impose 100% margin, trade-for-trade settlement, 5%/2% bands and once-a-week trading, which can trap a position.

### Cited Findings
- With a BTST sale you are selling shares not yet in your demat account and relying on the original seller to deliver. If that seller short-delivers, you become a defaulter on your own sale. [Practitioner/official broker] — [Zerodha Z-Connect: consequences of short delivery](https://zerodha.com/z-connect/trending/consequences-of-short-delivery-nse-bse); [Geojit](https://support.geojit.com/support/solutions/articles/89000007767-are-there-risks-involved-in-using-btst-orders-)
- On a default, the exchange runs an auction on T+1 at T-day's closing price with a ±20% limit. The penalty can range from almost nothing to about 20% of the value short-delivered. [Practitioner] — [Zerodha Z-Connect](https://zerodha.com/z-connect/trending/consequences-of-short-delivery-nse-bse); [Motilal Oswal](https://www.motilaloswal.com/learning-centre/2023/7/what-are-the-risks-involved-in-btst)
- GSM stages (5% or lower band at every stage): [Practitioner, summarising NSE circulars] — [Groww GSM](https://groww.in/blog/graded-surveillance-measure); [Zerodha GSM FAQ](https://support.zerodha.com/category/trading-and-markets/trading-faqs/articles/what-does-gsm-mean); NSE surveillance circulars e.g. [SURV60947](https://nsearchives.nseindia.com/content/circulars/SURV60947.pdf)

  | Stage | Restrictions |
  |-------|--------------|
  | I | 100% margin |
  | II | Trade-for-trade settlement; buyers deposit 50% ASD (Additional Surveillance Deposit) |
  | III | Trading only once a week; 100% ASD |
  | IV | As III, with no upward price movement allowed |

- ASM stages add 100% margin, then once-a-week trading, and 5% or 2% bands at higher stages. This is a summary that mixes the long-term and short-term ASM frameworks, so treat it as indicative. [Practitioner] — [Bajaj Broking](https://bajajbroking.in/blog/decoding-asm-and-gsm-frameworks-and-stages)

### Inferences
- In the backtest, block exits on day T+1 or require a minimum two-day hold, or accept the small BTST risk. Short delivery is rare in liquid stocks, so most systematic traders accept it. The bigger practical issue is surveillance-listed stocks.
- **Exclude ASM/GSM stocks from the entry universe.** Breakout candidates with sharp run-ups are exactly the stocks that tend to be put on ASM lists, and once listed the position may become hard to exit (narrow bands, once-a-week trading). The backtest has no point-in-time ASM history, so a proxy filter such as excluding 2%/5% band stocks or very illiquid names is the practical substitute.

### Gaps
- I found no statistic on how often BTST short deliveries occur.
- I did not obtain point-in-time ASM/GSM list archives. NSE publishes daily lists, but historical availability was not checked.

## 7. Results-season effects and pre-results exits

### Takeaway
Indian large caps typically move about 2-3% on results day, measured by options-implied moves for Nifty 50 members. Mid and small caps move more. Results are mostly announced outside market hours, so the move arrives as an overnight gap that a stop cannot protect against. Swing-trading practice is to trim or exit before known catalysts. Without an earnings calendar, the system cannot do this deliberately.

### Cited Findings
- In October 2025, options implied an average **2.3% earnings-day move for Nifty 50 members**, the lowest at the start of an earnings season in Bloomberg data back to 2016. TCS was priced for 3%, against a realised average of 3.2% over its previous eight reports. [Practitioner/financial press, Bloomberg data] — [Bloomberg via BGov, 10 Oct 2025](https://news.bgov.com/international-trade/traders-see-calmest-india-earnings-season-as-they-look-past-tcs)
- Indian event studies of quarterly earnings find positive abnormal returns persisting after good-news announcements, with cumulative abnormal returns rising for several days after the event (post-earnings drift). [Official/rigorous, academic] — [IUP Journal of Applied Finance](https://www.iupindia.in/304/IJAF_Indian_Stock_Prices_React_to_Quarterly_Earnings_37.html)
- Practitioner advice is to trim overnight exposure before known catalysts. [Practitioner] — [Tradejini](https://www.tradejini.com/blogs/why-your-stoploss-doesnt-work-during-gap-opens)
- Results announced after market hours move stocks at the next open. [Practitioner] — [Swastika](https://www.swastika.co.in/blog/post-market-earnings-shock-how-after-hours-results-move-stocks-before-opening-bell)

### Inferences
- Indian quarterly results cluster in fairly predictable windows: about mid-January to mid-February, mid-April to mid-May, mid-July to mid-August, and mid-October to mid-November. SEBI LODR gives 45 days after quarter-end, or 60 days for Q4. A crude seasonal proxy is possible even without an earnings calendar. That proxy could be: widen the slippage assumption on stop exits in these windows, cut position size, or tighten trailing stops into the window. The LODR deadlines are from general knowledge; I did not fetch a source this session.
- A 90-day hold almost always spans one results date. The strategy's gap-risk budget should assume at least one 2-3% (large cap) to 5-10%+ (small cap) overnight move per trade. The small-cap figure is my estimate and unsourced.
- Post-earnings drift after good news suggests exiting every position before results may give up upside. A measured choice would be to reduce size rather than exit fully. This should be tested empirically.

### Gaps
- I found no rigorous data on realised earnings-day move distributions for NSE mid and small caps, or on how often results produce gaps beyond typical stop distances.
- I found no survey data on what share of Indian swing traders exit before results; the evidence is only practitioner advice.
