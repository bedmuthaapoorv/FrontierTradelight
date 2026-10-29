# Failure modes of shorting 12-1 momentum losers open-to-close, and candidate filters (NSE)

Scope and caveats. Evidence is from ~14 web searches (search-result summaries, not full-paper reads). Numbers marked (sec) come from secondary summaries and should be checked in the original. Many Indian-practitioner sources are broker/blog content. Not personalized investment advice. The user's own validation notes warn against adding untested filters; the ranking at the end of the first section is by plausibility and cheapness of back-test on own data.

## 1. Short-term reversal, loser rebounds, momentum crashes: do losers bounce after up days, and should the last 1-5 day return be a filter?

### Takeaway
Momentum crashes are academically documented and are driven by the loser leg (high-beta losers rebounding in sharp market rallies after declines/high volatility). The evidence on conditioning on the last 1-5 day return is mixed: classic work says 1-week/1-month returns reverse (a prior up-day loser would tend to fall back, favouring the short), but newer work says reversal depends on turnover and that high-turnover stocks show short-term continuation, which would hurt a short. So "skip after a strong up day" is not supported by a clean literature result; it is an empirical question for the user's own data.

### Cited Findings
- Daniel and Moskowitz (JFE 2016): momentum crashes occur in "panic" states (after market declines, high volatility) and coincide with market rebounds; following declines the loser decile's beta can exceed 3 while winners fall below 0.5, so a long-winner/short-loser book has a large conditional negative beta when the market rebounds. Dynamic scaling roughly doubles alpha and Sharpe. — [NBER w20439](https://www.nber.org/papers/w20439); [Chicago Booth Review](https://www.chicagobooth.edu/review/understanding-momentum-crashes)
- Daniel and Moskowitz describe loser payoffs as option-like in panic states (high premium on past losers), i.e. losers are most dangerous to be short right after a drawdown, when a rebound is violent. — [NBER w20439](https://www.nber.org/papers/w20439)
- Barroso and Santa-Clara (JFE 2015): momentum risk is highly variable and predictable; scaling by trailing realized volatility of daily momentum returns (126-day window; robust 126-252 days) virtually eliminates crashes and nearly doubles the Sharpe ratio. Weights ranged 0.13 to 2.0, mean 0.90. — [paper abstract](https://ciencia.ucp.pt/en/publications/momentum-has-its-moments/); [etf.com summary](https://www.etf.com/node/94292.md); [R-bloggers replication](https://www.r-bloggers.com/2015/09/hypothesis-driven-development-part-iv-testing-the-barrososanta-clara-rule/)
- Medhat and Schmeling (RFS 2022): sorting on last month's return and turnover, low-turnover stocks show reversal while high-turnover stocks show short-term momentum (continuation); strongest in large, liquid, widely covered stocks (US plus 22 developed markets). A high-turnover loser that is "going up" is thus NOT expected to mean-revert, while a high-turnover loser going down tends to keep going down. — [CEPR DP15857](https://repec.cepr.org/repec/cpr/ceprdp/DP15857.pdf); [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/interaction-of-short-term-stock-momentumreversal-and-turnover/)
- Gutierrez and Kelley (JF 2008): after extreme weekly returns there is a brief reversal followed by continuation lasting about a year. — [IDEAS](https://ideas.repec.org/a/bla/jfinan/v63y2008i1p415-447.html)
- Indian evidence is mixed and dated: Michello and Chowdhury (1991-2006) found 1-1 short-term reversals for all winner-loser combinations and no medium-term momentum overall; Dhankar and Maheshwari (NSE 1997-2013) report short-term momentum and long-term overreaction; Sharma and Mehta (CNX 500) report momentum in 3-12 month horizons. — [IJFM summary page](https://www.publishingindia.com/archive/ijfm/a-study-of-contrarian-and-momentum-profits-in-indian-stock-market); [IIMB repository](https://repository.iimb.ac.in/handle/2074/18321?mode=full) (abstract-level; full papers not read)
- Jegadeesh and Titman (2001) report momentum persisted in the 1990s (not data snooping) and reversals only 4-5 years out; a Quantpedia piece reports momentum failing in 1999-2012 samples (secondary). — [NBER w7159](https://www.nber.org/papers/w7159); [Quantpedia](https://quantpedia.com/has-momentum-lost-its-momentum/)

### Inferences
- The strategy here is not the academic one: academics hold a month and rank on 12-1 returns; the rules short the bottom 5% for one session. Academic momentum evidence says little about the open-to-close leg (see Q2), so crash literature is relevant mainly for regime risk (market rebounds), not the single-day edge.
- KEC (a stock rising >1.5% on two straight days while a 12-1 loser) is exactly the Medhat-Schmeling worry case if volume was high: high-turnover up moves tend to continue. Candidate: skip shorts when the stock's last-1 or last-2 day return is strongly positive AND relative volume is high; keep shorts when the up-move was on low volume (noise reversal). Testable from OHLCV.
- A market-rebound gate (Daniel-Moskowitz) needs a market series; the user said the rules have breadth data. Candidate: skip or halve exposure when breadth has jumped sharply (e.g. % above 50-DMA up by a large amount in 3-5 days) or when trailing market drawdown was deep and breadth is turning. Plausible, cheap to test, but the threshold is a free parameter (overfit risk).
- Vol scaling (Barroso-Santa-Clara) on the strategy's own trailing daily P&L is computable from the user's own trade log and is the best-evidenced risk filter; for a 1-day strategy it would act as a position-size reducer after volatile losing stretches.

### Gaps
- No Indian study found that conditions open-to-close loser-short returns on the prior 1-5 day return. No paper found testing "skip a short after an up day" directly.
- Full texts not read; Medhat-Schmeling magnitudes differ between summaries.

## 2. Overnight vs intraday returns and gap conditioning

### Takeaway
Lou-Polk-Skouras show momentum profits accrue overnight, with the intraday leg of momentum being flat to opposite-signed, which implies an open-to-close loser short captures little of the documented momentum premium and is exposed to the intraday reversal of it. Gap-conditioning evidence is thin: one smaller-journal US study supports gap-up fade; no solid NSE study found.

### Cited Findings
- Lou, Polk and Skouras (JFE 2019): across 14 strategies, profits are earned either entirely overnight or entirely intraday, typically with opposite signs; momentum abnormal returns occur overnight while other anomalies earn intraday; stronger in large-cap, high-price stocks; argued to be an institution-vs-individual trading tug of war. — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/87481); [Polk paper PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- When momentum activity is low or institutions need to rebalance, momentum returns are even larger overnight and reverse more strongly intraday. — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/87481)
- Alpha Architect reports its own backtests found no intraday momentum result, and cites Cooper, Cliff and Gulen that essentially all stock returns accrue overnight. — [Alpha Architect](https://alphaarchitect.com/2015/02/overnight-momentum-vs-intraday-momentum/) (practitioner)
- Kudryavtsev (Dow Jones stocks): open-to-close returns tend to be lower, mostly negative, when the opening return is above average/median, i.e. gap-up fade. US large caps, minor journal. — [ULBS paper](https://magazines.ulbsibiu.ro/eccsf/articole/vol73/735kudryavtsev.pdf)
- Tripathi and Aggarwal (Delhi University, high-frequency NSE data): returns reverse within minutes after extreme moves; Indian investors push prices up quickly after unjustified falls but take longer to push down after unjustified rises. Minute-scale, not gap-specific. — [IJFM i-scholar](https://www.i-scholar.in/index.php/ijfm/article/view/84877) (abstract only)
- A Nifty overnight-vs-intraday blog argues open-to-close contributes little over long periods (index-level, not peer reviewed). — [multibagg.ai](https://www.multibagg.ai/market-pulse/articles/nifty-overnight-intraday-returns-study-cmquu8ofy9pn1nz0j1dln1abo)

### Inferences
- Because the momentum premium is concentrated overnight, an intraday-only short earns the "wrong" window; a ~0.2% gross edge per trade is plausibly a reversal/noise effect or bid-ask/auction effect rather than momentum, and so is fragile. Worth testing which of overnight (prev close to open) or intraday (open to close) drives the user's historical P&L; the user's strategy enters at the open, so gap is already realized.
- Candidate filter: skip shorts when the stock has gapped up at the open (open vs prior close) above some threshold (e.g. > +1%, or > 0.5 ATR), since a gap-up against the short may be news-driven. Counter-hypothesis from the gap-fade evidence: gap-up on a loser is a better short. Direction is genuinely ambiguous, so test both. Note: the entry at the open means the gap is known only at the open; if the rules compute signals pre-open, the gap must be read at order time (needs the open print; daily OHLCV of the same day, so it is look-ahead only if used pre-entry).

### Gaps
- No NSE study of open-to-close return conditional on gap size for individual stocks found.

## 3. News, earnings, announcement effects with only price data

### Takeaway
I did not retrieve sources on PEAD or announcement-day jump magnitudes in this session (searches returned nothing on that topic), so this section is mostly reasoning. The practical price-only proxies are abnormal true range/volume on the prior day and a results-season calendar skip; none is evidence-backed in my sources.

### Cited Findings
- None retrieved with citable numbers on earnings jumps or PEAD in India. (One search conflated with 52-week-high papers and returned nothing on Chan-Jegadeesh-Lakonishok.)

### Inferences (uncited, from general knowledge; treat as hypotheses)
- Indian companies report quarterly in fixed windows (roughly mid-Jan to mid-Feb, mid-Apr to mid-May, mid-Jul to mid-Aug, mid-Oct to mid-Nov), so skipping or down-sizing shorts in those windows is a calendar rule that needs no earnings feed. It removes many trades, so cost-benefit must be tested; the date today (late October) lies inside the Q2 results window.
- Price-only proxies computable from daily OHLCV: previous-day true range / ATR(14) above e.g. 2x; previous-day volume / 20-day average above e.g. 2-3x; prior-day gap size above a threshold. Each flags a likely news day, after which the next session often carries continuation (PEAD-like) or noise. Direction for a loser short after a positive news jump is unfavourable to a short.
- KEC-type case: two consecutive >1.5% up days on a 12-1 loser is compatible with positive news flow (order wins are frequent for this sector); a "no two consecutive up closes" check is cheap to test.

### Gaps
- No evidence retrieved on PEAD magnitude in India or intraday behaviour on results days. Should be searched separately (e.g. Indian PEAD papers, NSE results calendars).

## 4. Sector and relative-strength conditioning

### Takeaway
Industry momentum is well documented (Moskowitz and Grinblatt, 1999) and later work says factor momentum subsumes it; but nothing found tests shorting losers inside strong vs weak industries on a one-day horizon. The prior is that a loser in a strong sector is the more rebound-prone short.

### Cited Findings
- Moskowitz and Grinblatt (JF 1999): industry effects account for much of individual-stock momentum; individual-stock momentum profits shrink after controlling for industry; industry momentum stays profitable after controlling for size, B/M, stock momentum. — [IDEAS](https://ideas.repec.org/a/bla/jfinan/v54y1999i4p1249-1290.html); [AQR](https://www.aqr.com/Insights/Research/Journal-Article/Do-Industries-Explain-Momentum?aqrPDF=1)
- Arnott, Clements, Kalesnik and Linnainmaa (2018): factor momentum subsumes industry momentum (as reported in search summary). — [Osuva](https://osuva.uwasa.fi/bitstream/10024/11757/2/Osuva_Grobys_Kolari_2019.pdf) (secondary)
- Novy-Marx (2012) argues momentum comes mainly from returns 12-7 months back ("echo"), not recent returns (secondary summary; I did not see the paper). — [search summary only](https://hedgefundalpha.com/strategies/industry-momentum-the-role-of-time-varying-factor-exposures-and-market-conditions/)

### Inferences
- The strategy already has a sector rank; a clean test is: restrict shorts to stocks whose sector is in the bottom half/third (both stock and sector weak = the Moskowitz-Grinblatt-consistent short) and compare to shorts in top-half sectors. Cheap (one column), few free parameters if using terciles. Moderate plausibility, no direct one-day evidence.
- Because the 5% bottom includes a lot of sector-clustered names (e.g. a sector selloff), a cap of 1-2 names per sector reduces correlated losses on a single bad sector day. Zero look-ahead, easily tested.

### Gaps
- No study found on sector-conditioned loser shorts at daily horizon or in India.

## 5. Volume, volatility, proximity conditioning (relative volume, ATR/price, 52-week low, MA distance)

### Takeaway
Turnover conditioning has the best academic support (Medhat-Schmeling); 52-week-high proximity is a well-known momentum predictor (George-Hwang) and offers a natural variant (prefer shorts far from the 52-week high); other items (ATR/price, MA distance) have only practitioner-level support in my sources, none retrieved.

### Cited Findings
- George and Hwang (JF 2004): nearness to the 52-week high explains a large share of momentum profits and dominates past-return measures; long near-high/short far-from-high earns about 0.45% abnormal per month (US; sec). Out-of-sample checks mixed. — [Alpha Architect](https://alphaarchitect.com/2014/11/the-secret-to-momentum-is-the-52-week-high); [academic newsletter summary](https://academicnewsletter.sufe.edu.cn/info/361244)
- Medhat-Schmeling: turnover regime changes sign of short-horizon predictability (see Q1). — [CEPR DP15857](https://repec.cepr.org/repec/cpr/ceprdp/DP15857.pdf)
- Daniel and Moskowitz / Barroso-Santa-Clara: volatility regime (market and momentum-portfolio volatility) predicts momentum crashes (see Q1).
- Tripathy et al. (India): volatility persistence is stronger in loser portfolios than winners (abstract-level, via search summary). — [IJFM](https://www.publishingindia.com/archive/ijfm/a-study-of-contrarian-and-momentum-profits-in-indian-stock-market)

### Inferences (hypotheses, no direct source for loser-short success)
- Relative volume (volume/20d average) on the last day: high-volume up days on a loser are likely information, so skip; high-volume down days may favour continuation. Medium plausibility, cheap, one threshold.
- ATR/price: a very high ATR/price loser with a 1x ATR stop gets stopped by noise; a very low one gives small moves relative to costs. Test deciles of ATR/price versus win rate and net-of-cost expectancy instead of picking cutoffs. Because the 1x ATR stop on an intraday trade is tight, stop-hit frequency might be the main driver of the 41% losers; check stop-hit vs close-loss split.
- Distance from 52-week low: stocks sitting on or within a few percent of a fresh 52-week low (still falling) are more consistent with continuation; stocks that have bounced 20%+ off the low are the junk-rally candidates. Prefer a "within X% of 52-week low" or "close below 20-DMA and 50-DMA" condition. Plausible, needs only OHLCV; two parameters.
- Near 20/50-day MA: a loser that has recovered to its 20- or 50-day MA is in the bounce state; requiring close < 20-DMA is a cheap one-parameter downtrend confirmation (the existing 200-DMA filter is too slow to detect a rebound).
- Existing ranking 0.7*momentum + 0.3*liquidity puts the biggest, most liquid, deepest losers first. Deepest losers are the most extreme/high-beta (Daniel-Moskowitz), so "rank 1-3" may be the most rebound-prone. A test of whether win rate is monotonic in rank (rank-bucket analysis) is zero-parameter and informative.

### Gaps
- No source found quantifying win rates of loser shorts by volume, ATR, MA distance. Everything marked inference needs own back-test.

## 6. India shorting costs and constraints

### Takeaway
Retail can short cash stocks only intraday (naked short selling is prohibited for settlement, so no overnight carry without SLB borrowing, which retail largely lacks); STT on intraday equity is 0.025% on the sell side, plus brokerage/exchange/GST costs, so round-trip cost is roughly 3-6 bps against a ~20 bps gross edge, a material but not dominating drag. There is conflicting information on 2025-26 changes; verify with primary documents.

### Cited Findings
- SEBI's January 2024 framework: naked short selling not permitted; all investors must honour delivery at settlement; retail may short intraday in the cash segment and cover before close; carrying overnight requires borrowed shares via SLB; institutions cannot square off intraday and must disclose shorts upfront while retail can disclose by day-end. — [Business World](https://businessworld.in/article/sebi-regulates-short-selling-trades-prohibits-naked-short-selling-504909); [Taxmann](https://taxmann.com/post/blog/sebi-strengthens-short-selling-norms-tightening-norms-particularly-for-institutional-investors); [TradingQnA](https://tradingqna.com/t/sebis-latest-circular-on-framework-for-shortselling-jan-2024/158642) (secondary; check SEBI circular directly)
- A Bigul page claims only F&O stocks are eligible for short selling; this conflicts with other sources and the 2024 framework, so treat as unreliable. — [Bigul](https://bigul.co/policy/short-selling); contradicted by [Business World](https://businessworld.in/article/sebi-regulates-short-selling-trades-prohibits-naked-short-selling-504909)
- Zerodha: intraday shorts cannot be held overnight; failure to deliver leads to auction and penalties; SLB not available to retail in the equity segment per a community answer (2021 CEO post said it was working on offering SLB to all customers; rollout not confirmed); overnight shorts are done mostly via futures. — [Zerodha Z-Connect](https://zerodha.com/z-connect/trending/shorting-and-indian-capital-markets); [Zerodha support](https://support.zerodha.com/category/trading-and-markets/trading-faqs/articles/what-is-short-delivery-and-what-are-its-consequences); [YourStory](https://yourstory.com/2021/01/shorting-indian-capital-markets-zerodha)
- Short delivery risk arises when an intraday short cannot be covered due to illiquidity or an upper circuit (a risk for stocks that gap up to circuit). — [Zerodha support](https://support.zerodha.com/category/trading-and-markets/trading-faqs/articles/what-is-short-delivery-and-what-are-its-consequences)
- Costs (Zerodha): equity intraday STT 0.025% sell side only, unchanged after the April 2026 F&O rate change; brokerage 0.03% or Rs 20 per order whichever lower; NSE transaction charge about 0.003% (versions differ: 0.00297-0.00322%); SEBI fee Rs 10/crore; GST 18% on brokerage+SEBI+transaction charges; stamp duty 0.003% on the buy side. — [Zerodha STT article](https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/how-is-the-securities-transaction-tax-stt-calculated); [Zerodha charges](https://zerodha.com/charges)
- 2025-26 F&O regulation: SEBI Sept 1, 2025 circular on intraday position limits for index derivatives (effective Oct 1, 2025), expiry-day measures; one source says Budget 2026-27 raised futures STT to 0.05% and options to 0.15% (single source, unverified). These concern derivatives, not the cash intraday short. — [Value Research](https://www.valueresearchonline.com/stories/224848/sebi-rewrites-fo-rules-to-curb-expiry-day-speculation/); [Business Standard](https://www.business-standard.com/markets/capital-market-news/sebi-raises-surveillance-measures-to-check-volatility-in-f-o-segment-125090301114_1.html); [Zerodha STT article](https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/how-is-the-securities-transaction-tax-stt-calculated)
- Single weak source claims a closing auction session from 3 August 2026 moved auto square-off timings; unverified. — [strike.money](https://www.strike.money/stock-market/stbt)

### Inferences
- Approximate cost arithmetic (own calculation, using the above rates; ignores slippage): sell-side STT 2.5 bps + brokerage up to 3 bps per leg only if the percent option applies (flat Rs 20 order cap is typically smaller for larger tickets) + exchange fees about 0.7 bps round trip + stamp 0.3 bps + GST on fees. Order of magnitude 4-8 bps round trip before slippage; slippage at the open and a 1x ATR stop in mid-cap names can easily add 5-15 bps. A ~20 bps gross edge may be cut by a third to a half, so filters that raise gross edge by only a few bps are not worth the trade-count loss. Confirm with the user's actual broker contract note.
- Because the rules require an open entry and the circuit risk applies, excluding stocks within one daily price band of upper circuit (and stocks in ASM/GSM lists) is a reasonable hard constraint; ban lists are not derivable from OHLCV.
- F&O availability is not required for cash intraday shorts, but F&O stocks have deeper liquidity and cheaper hedging; restricting to F&O-eligible names is a liquidity proxy, not a regulatory necessity (per the 2024 framework sources).

### Gaps
- Primary SEBI/NSE documents not opened; no confirmation of any 2025-26 change to cash-segment short-selling rules; Zerodha's present SLB availability unconfirmed.

## 7. Statistical reasoning: streaks, small samples

### Takeaway
At a 59% win rate, a 41% loss probability makes two consecutive losing trades on a specific name (16.8% if independent) and 3+ losers out of 5 trades in a week (33%) routine events. One miss on one name cannot justify a rule change; require out-of-sample, count-based evidence.

### Cited Findings
- All figures below are own binomial arithmetic with p(loss) = 0.41, independence assumed; no external source.

### Inferences
- Two consecutive losers on the same name: 0.41 x 0.41 = 16.8% (about 1 in 6) per pair of days; but losses on the same name on adjacent days are positively correlated (persistent news/regime), so true probability is probably higher.
- Five trades in a week: P(5 losers) = 0.41^5 = 1.2%; P(at least 4 losers) = 9.5%; P(at least 3 losers) = 33%.
- Fifteen trades (3 per day for 5 days): mean losers 6.15, SD about 1.9; normal approximation: P(at least 8 losers) about 24%, P(at least 9) about 11%, P(at least 10) about 4%. Weekly outcomes are also correlated through the market, so weeks with 9+ losers in 15 will occur more often than independence predicts (the Daniel-Moskowitz rebound weeks).
- Over many opportunities, streaks are guaranteed: the longest run of losers in n trades is about log(n)/log(1/0.41) = 1.12 x ln(n): for n=100 about 5 in a row; for 250, about 6.
- Confidence interval for a win rate near 59% (normal approx): half-width about 13.6 points at n=50, 9.6 at n=100, 6.8 at n=200, 4.8 at n=400. Hence 59% versus a 50% null needs n of roughly 100+ to be distinguishable from coin-flip, and a filter that moves win rate by 3-5 points cannot be detected with fewer than several hundred trades in each arm.
- Rule of thumb: do not adopt a filter unless (a) it has a prior mechanism, (b) its sample shows an effect in both halves of the data (split by time), (c) it removes no more than about 20-30% of trades while improving net expectancy (not just win rate) and (d) the effect is monotonic across buckets rather than a single cutoff. With k filters tried, expect about 5% to pass a naive 5% test by luck; use a Bonferroni-style stricter threshold or pre-register a short list.
- Effects can be wiped out because win rate and expectancy differ: a 59% win rate with 1x ATR stop and close exit may have asymmetric payoffs; measure average win/loss and stop-hit share first.

### Gaps
- Actual sample size, per-trade payoff distribution and day-to-day clustering of the user's trades unknown, so the probabilities above are indicative only.

## Candidate filters ranked (plausibility x cheapness x overfit risk)

| # | Candidate | Mechanism | Evidence quality | OHLCV only | Overfit risk |
|---|---|---|---|---|---|
| 1 | Rank-bucket / win-rate-by-rank diagnostic (no new rule) | Deepest losers are highest beta/rebound prone | Inference from Daniel-Moskowitz (academic) | Yes | None (diagnostic) |
| 2 | Cap names per sector (1-2) and/or prefer weak sectors | Correlated sector rebounds; industry momentum | Moskowitz-Grinblatt (academic, monthly horizon) | Yes (sector rank exists) | Low |
| 3 | Last-1/2-day return and relative volume gate (skip high-volume up days) | High-turnover short-term continuation; news days | Medhat-Schmeling (academic); thresholds are inference | Yes | Medium (2 thresholds) |
| 4 | Gap/true-range spike skip (open vs prior close, prior TR/ATR) | News/announcement proxy; direction ambiguous | Kudryavtsev (US, minor); LPS (academic) | Yes | Medium (direction ambiguity) |
| 5 | Breadth-jump or vol-scaling gate | Market rebound / momentum crash regime | Daniel-Moskowitz, Barroso-Santa-Clara (top-tier academic, monthly) | Yes with breadth series | Medium (threshold); vol-scaling on own P&L is low |
| 6 | Close below 20-DMA (and 50-DMA), near 52-week low | Excludes bounce state | George-Hwang for 52wk (academic, long horizon); MA rule is practitioner | Yes | Medium |
| 7 | Results-season calendar skip | Announcement jumps | No evidence retrieved | Yes (calendar) | Medium; large trade loss |
| 8 | ATR/price band | Stop noise vs cost | No evidence retrieved | Yes | Medium-high |
| 9 | Exclude circuit-band/ASM names | Short-delivery auction risk | Zerodha support (primary broker doc) | Partly (circuit proxy) | Low |

Note: academic momentum evidence (monthly holding periods, developed markets) does not transfer cleanly to a single-session open-to-close trade, and Lou-Polk-Skouras suggest that leg is not where the momentum premium lives; the strategy's own edge may largely be microstructure/reversal and should be diagnosed before filtering.
