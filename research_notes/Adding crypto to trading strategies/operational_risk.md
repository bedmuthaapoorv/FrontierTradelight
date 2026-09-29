# Operational and Counterparty Risks in Crypto Trading (as of 2026)

## What major crypto exchange failures, hacks, or frauds have occurred, and what caused them?

### Takeaway
Crypto has a long, continuing history of catastrophic counterparty failures spanning three distinct failure modes — exchange hacks (external theft), fraud/misappropriation (insider theft), and insolvent lending/rehypothecation (business-model failure) — and 2025-2026 set new records for both hack size and hack frequency rather than showing improvement.

### Cited Findings
- Mt. Gox (2014): a breach that began years before detection resulted in the loss of ~850,000 BTC; Mt. Gox handled over 70% of global BTC transaction volume at the time and filed for bankruptcy in February 2014 — [Coldcard: A History of Bitcoin Exchange Failures](https://coldcard.com/learn/self-custody/bitcoin-exchange-failures)
- Celsius (2022): not an exchange but a yield/lending platform; customer deposits were treated as liabilities, lent out and deployed opaquely; froze withdrawals and filed Chapter 11 in July 2022 with a shortfall of over $1 billion — [Coldcard: A History of Bitcoin Exchange Failures](https://coldcard.com/learn/self-custody/bitcoin-exchange-failures)
- FTX (2022): collapsed after it emerged customer funds (~$8 billion) had been transferred to and misappropriated by Alameda Research, an affiliated trading firm under common ownership, to cover Alameda's losses and other activities — [Coldcard: A History of Bitcoin Exchange Failures](https://coldcard.com/learn/self-custody/bitcoin-exchange-failures)
- Bybit (Feb 21, 2025): largest single crypto theft in history, ~$1.4–1.5 billion in ETH stolen. Bybit used a third-party wallet interface to move funds from cold to warm storage via a multi-approval transaction flow; attackers compromised a machine at the third party and injected malicious JavaScript into the signing UI, causing signers to unknowingly approve a transaction redirecting 401,000 ETH to attacker-controlled wallets — [CNBC](https://www.cnbc.com/2025/02/21/hackers-steal-1point5-billion-from-exchange-bybit-biggest-crypto-heist.html); [Cloudskope](https://www.cloudskope.com/breaches/bybit-hack-2025)
- The FBI/IC3 formally attributed the Bybit hack to North Korea, specifically activity it labels "TraderTraitor," linked to the Lazarus Group — [FBI](https://www.fbi.gov/investigate/cyber/alerts/2025/north-korea-responsible-for-1-5-billion-bybit-hack); [IC3](https://www.ic3.gov/psa/2025/psa250226)
- Bybit fully replenished reserves within ~72 hours via emergency loans and large deposits, and launched a recovery bounty of up to 10% of recovered funds — [CNBC](https://www.cnbc.com/2025/02/24/bybit-replenished-reserves-after-record-breaking-1point5-billion-hack.html)
- Nobitex (Iran-based exchange, June 2025): hackers withdrew ~$80–90 million from hot wallets — [The Block](https://www.theblock.co/news/regulation/2026-01-01-biggest-crypto-hacks-2025-380992)
- Across the 10 largest 2025 incidents (spanning centralized exchanges, DeFi protocols, and infrastructure providers), attackers stole an estimated $2.2 billion — [The Block](https://www.theblock.co/news/regulation/2026-01-01-biggest-crypto-hacks-2025-380992)
- Chainalysis 2026 Crypto Crime Report: total stolen funds from hacks reached $3.4 billion in 2025; North Korean state actors alone stole $2.02 billion in 2025 (+51% YoY), bringing their cumulative all-time total to $6.75 billion — [Livebitcoinnews](https://www.livebitcoinnews.com/crypto-crime-hits-154b-in-2026-says-chainalysis-report/); [Stingrai](https://www.stingrai.io/blog/crypto-hacking-statistics-2026)
- 2026 has seen an acceleration, not a slowdown: 164 separate hacking incidents logged through early August 2026, more than any full prior year; on July 30, 2026 attackers drained 1,082.65 BTC (~$70.2M) from 1,196 addresses in 41 minutes — [The Block](https://www.theblock.co/news/regulation/2026-01-01-biggest-crypto-hacks-2025-380992)
- Hong Kong-based exchange CoinEx announced it would shut down on September 15, 2026 — [The Block](https://www.theblock.co/news/regulation/2026-01-01-biggest-crypto-hacks-2025-380992)
- DeFi-side example: KiloEx, a decentralized derivatives exchange, lost ~$7.5 million in an April 2025 cross-chain exploit described publicly as oracle manipulation but attributed more precisely to underlying protocol-logic vulnerabilities — [Hacken/OWASP summary via search](https://hacken.io/discover/flash-loan-attacks/)

### Inferences
- The threat model has shifted from "exchange operator fraud" (Mt. Gox, FTX) toward "state-sponsored external theft targeting operational/signing infrastructure" (Bybit, Nobitex) — the attack surface most relevant to a trading firm is the wallet-signing and key-custody workflow, not just smart-contract code.
- The rate of hacks is increasing both in dollar terms and incident count year over year (2025 → 2026), meaning this is not a maturing/de-risking market; a trading firm should assume the threat is worsening, not improving, over the 2026 planning horizon.
- Even top-tier exchanges (Bybit is a major, ostensibly well-resourced venue) with formal multi-approval signing processes were defeated via supply-chain compromise of a third-party UI — defense-in-depth on the exchange side cannot be assumed to protect assets held there.

### Gaps
- No comprehensive, single primary-source list of every 2024–2026 CEX hack was retrieved (aggregator sites like CoinGecko/Hedge With Crypto were surfaced but not fetched in full); the Bybit, Nobitex, and CoinEx items above are the best-sourced 2025–2026 incidents found.
- Root-cause detail on the WazirX 2024 hack was not fetched (only its Wikipedia page surfaced in search); not included here due to lack of a verified cause summary.

## What custody risk exists when holding crypto assets on an exchange vs self-custody, and what are best practices for a trading firm?

### Takeaway
Exchange-held ("not your keys, not your coins") assets carry counterparty, commingling, and hack risk as shown by FTX/Mt. Gox/Bybit; the institutional best practice is a tiered custody architecture — cold storage for reserves, warm/hot wallets sized to operational need, multi-signature/MPC policy engines with tiered approval thresholds, and use of regulated qualified custodians — rather than either pure self-custody or full exchange reliance.

### Cited Findings
- Core institutional custody architecture combines cold storage, multi-signature wallets, hardware security modules (HSMs), and multi-factor authentication (MFA) to protect against internal and external threats — [BitGo](https://www.bitgo.com/resources/blog/what-to-look-for-in-an-institutional-crypto-custody-provider/)
- Institutional-grade custody platforms offer policy engines with tiered multi-sig approval based on transaction size — example cited: 2-of-3 approval for transfers under $10,000, 3-of-5 for $10,000–$100,000, and 5-of-7 with mandatory time delays for larger transfers — [Cobo](https://www.cobo.com/post/is-your-crypto-custody-institution-ready-a-security-benchmark)
- Split online/offline storage architecture: cold wallets protect against cyber threats while hot/warm wallets enable timely trading; many institutions keep only day-to-day operational balances warm and reserve the bulk of assets in cold storage — [ChainUp](https://www.chainup.com/blog/warm-wallets-multi-sig-crypto-custody/)
- Additional enterprise practices: offline/air-gapped signing for high-value transfers, full audit logging of every API call and signature attempt, geographically distributed backups of key shares/seed phrases for disaster recovery, and address whitelisting restricting outgoing transfers to pre-approved addresses — [Cobo](https://www.cobo.com/post/is-your-crypto-custody-institution-ready-a-security-benchmark)
- For US registered investment advisers subject to SEC Custody Rule 206(4)-2, Anchorage, BitGo, and Coinbase Custody are described as the three native "qualified custodians," while Fireblocks typically operates as the operational/technology layer sitting behind a qualified custodian rather than as a qualified custodian itself — [Restart Fintech via search summary](https://restartfintech.com/blog/institutional-crypto-custody-providers-compared)
- BitGo (OCC trust charter, Dec 2025) and Anchorage Digital (OCC charter since Jan 2021) hold the clearest federal qualified-custodian status; Fireblocks Trust Company and Coinbase Custody operate under NYDFS trust charters, which also confer qualified-custodian status for SEC-regulated clients — [Eco.com](https://eco.com/support/en/articles/15254027-tokenized-rwa-custody-2026-anchorage-bitgo-fireblocks-for-institutions)
- Many institutions adopt multi-custodian strategies to avoid single-provider concentration risk, citing BlackRock's approach of splitting assets across Coinbase and Anchorage as a model — [search synthesis, Spark/Coingape sources](https://www.spark.money/tools/crypto-institutional-custody-comparison)
- The Bybit hack demonstrates that even a formal multi-approval cold-to-warm transfer process can be defeated via compromise of a third-party signing UI/device, redirecting signer intent without their knowledge — [CNBC / Cloudskope](https://www.cloudskope.com/breaches/bybit-hack-2025)

### Inferences
- A trading firm should treat "multi-sig" as necessary but not sufficient: the Bybit incident shows the weak link can be the UI/device used to construct and display the transaction for signing, not the signature scheme itself. Firms should insist on independent transaction verification (e.g., signing-device display of raw calldata, hardware wallet verification) rather than trusting a third-party web UI.
- Splitting custody across multiple qualified custodians (as BlackRock reportedly does) is emerging as a best practice specifically to bound single-provider/single-hack loss, analogous to prime-broker diversification in traditional finance.
- Only a minority of exchange-held balances should be treated as "operational" (hot/warm) capital exposed to exchange counterparty risk at any time; the rest should sit in independently-controlled or qualified-custodian cold storage.

### Gaps
- Specific, named case studies of a trading firm's cold/warm allocation percentages (e.g., "keep X% on exchange for margin") were not found in this pass; general guidance found is qualitative, not quantitative.

## What smart-contract, stablecoin depeg, or DeFi-specific risks exist if strategies touch decentralized exchanges or stablecoins?

### Takeaway
Stablecoins that appear "safe" can depeg sharply on exogenous shocks to their reserve banking relationships (USDC/SVB, March 2023), and DeFi protocols carry a distinct, ongoing class of smart-contract risk (flash-loan-enabled oracle manipulation, reentrancy, protocol-logic bugs) that is formally catalogued by security bodies like OWASP as of 2025.

### Cited Findings
- USDC depegged to $0.87 on March 11, 2023 after Circle disclosed $3.3 billion (8% of USDC's ~$40B reserves) was held at the failed Silicon Valley Bank; the peg was restored on March 13, 2023 after a joint US Treasury/Fed/FDIC deposit guarantee — [arXiv paper on USDC depeg contagion](https://arxiv.org/abs/2606.07442)
- The depeg mechanism was a "bank-run template": backing was real but temporarily inaccessible (frozen at a closed bank), which triggered a rational, self-fulfilling panic sell-off rather than an actual insolvency — [arXiv](https://arxiv.org/html/2606.07442v1)
- Contagion during the USDC depeg propagated differently across assets: USDC-linked stablecoins transmitted the shock mainly via transaction-count/active-node participation, while USDT/WBTC/WETH responded through larger value transfers; on-chain behavior showed a shift from single-asset to multi-asset exposure, including flows from USDC into USDT — [arXiv](https://arxiv.org/html/2606.07442v1)
- OWASP's Smart Contract Top 10 (2025 edition) formally lists Flash Loan Attacks as category SC07:2025 — [OWASP](https://owasp.org/www-project-smart-contract-top-10/2025/en/src/SC07-flash-loan-attacks.html)
- Flash loan attacks exploit blockchain transaction atomicity to borrow large uncollateralized sums within a single transaction, then combine that capital with oracle manipulation, reentrancy, or logic flaws to drain protocol funds or trigger under-collateralized liquidations; recommended mitigation is TWAP or decentralized, manipulation-resistant oracle design — [Hacken](https://hacken.io/discover/flash-loan-attacks/)
- KiloEx (April 2025), a decentralized derivatives exchange, lost ~$7.5 million in a cross-chain exploit publicly framed as oracle manipulation but attributed to deeper protocol-logic vulnerabilities — [search synthesis, referencing Hacken/OWASP coverage]

### Inferences
- Even "fully-collateralized" fiat-backed stablecoins carry real counterparty/banking risk in their reserve structure; a firm using stablecoins for settlement or as a cash proxy should assess reserve bank concentration and issuer transparency, not assume 1:1 backing eliminates risk.
- Any strategy that executes on DEXs or interacts with DeFi lending/derivatives protocols inherits protocol-specific smart-contract risk that is largely uncorrelated with, and additive to, ordinary market risk — this needs separate underwriting (audits, TVL, time-in-production, whether oracle design uses TWAP/decentralized feeds) per protocol touched.

### Gaps
- Did not find a comprehensive list of stablecoin depeg events beyond USDC/SVB (e.g., USDT historical depegs, algorithmic stablecoin failures like UST/Terra) within the tool-call budget — flagged as a gap; UST/Terra (2022) is widely known but was not independently re-verified with a primary source in this pass.
- No detailed 2026-specific DeFi/DEX exploit incident (beyond KiloEx, April 2025) was retrieved with full causal detail.

## What operational risks are specific to 24/7 markets?

### Takeaway
Crypto's always-on trading creates structural risks absent from traditional markets: historically, weekend/holiday liquidity vacuums produced sharp gap risk versus continuously-trading spot; exchanges have suffered outages precisely during peak-volatility events, amplifying losses; and October 2025 produced the largest deleveraging event in crypto market history, exposing both liquidity and exchange-infrastructure fragility simultaneously.

### Cited Findings
- Historically, weekend closures of regulated derivatives markets (e.g., CME bitcoin futures) created gap risk versus the continuously-trading spot market; a ~$10,000 gap in bitcoin futures emerged around the March 2, 2025 announcement of the U.S. Strategic Crypto Reserve — [CoinDesk](https://www.coindesk.com/markets/2026/05/28/bitcoin-s-famous-cme-gaps-are-about-to-disappear-though-three-remain-unresolved)
- Weekend crypto trading volume drops 40–60% versus weekdays as institutional traders, market makers, and automated desks reduce activity or go offline, thinning liquidity precisely when gap risk is highest — [FinanceFeeds](https://financefeeds.com/24-7-crypto-markets-risk-management-experts/)
- CME moved bitcoin futures/options to 24/7 trading in May 2026 (with only a 2-hour Saturday maintenance window) specifically to reduce weekend risk premia and improve institutional hedging — but this is a very recent structural change, and "Monday" processing/settlement mismatches are noted as a new residual risk — [Coinalertnews](https://coinalertnews.com/news/2026/05/28/cme-24-7-crypto-futures-erases-bitcoin-gap); [Cryptonews.net](https://cryptonews.net/news/bitcoin/32928273/)
- October 10, 2025 flash crash: Bitcoin fell from ~$121,000 to intraday lows of $102,000–$110,000; over $19 billion in leveraged positions were liquidated within hours — roughly 9x larger than any prior single-day liquidation total, the largest deleveraging event in crypto market history — [CoinGecko](https://www.coingecko.com/learn/october-10-crypto-crash-explained); [FTI Consulting](https://www.fticonsulting.com/insights/articles/crypto-crash-october-2025-leverage-met-liquidity)
- During the peak liquidation minute (21:15 UTC), $3.21 billion in positions were liquidated in 60 seconds, 93.5% of which was forced selling; liquidation rate accelerated ~86x, from $0.12B/hour pre-cascade to $10.39B/hour during the 40-minute cascade — [Amberdata](https://blog.amberdata.io/how-3.21b-vanished-in-60-seconds-october-2025-crypto-crash-explained-through-7-charts)
- Binance, the largest exchange by volume, suffered intermittent web/API outages between 20:50–22:00 UTC during the crash, including failed order execution, login errors, and price-feed anomalies (some tokens briefly showed near-zero prices); Binance later announced $283 million in compensation to affected users citing system strain from extreme volatility — [CoinGecko](https://www.coingecko.com/learn/october-10-crypto-crash-explained)
- The October 2025 crash was triggered by a geopolitical/macro shock (a Trump administration announcement of a 100% tariff on Chinese imports effective Nov 1), not a crypto-native event — illustrating that crypto's leverage/liquidation structure can massively amplify an exogenous shock within minutes — [CoinGecko](https://www.coingecko.com/learn/october-10-crypto-crash-explained)
- The "weekend problem" also has a settlement dimension distinct from price gap risk: crypto can settle at any hour but linked fiat banking rails operate only on business days, creating trapped liquidity and settlement risk at the fiat on/off-ramp even when the crypto leg is available 24/7 — [Finchtrade](https://finchtrade.com/blog/the-weekend-problem-why-24-7-business-needs-24-7-settlement)

### Inferences
- Exchange infrastructure reliability is inversely correlated with the moments a trading firm needs it most — outages cluster during extreme volatility, meaning risk systems and hedges relying on a single exchange's uptime should be treated as unreliable exactly when they matter most.
- Leverage embedded in the broader market (not the firm's own positions) is itself a risk factor: the October 2025 cascade shows that other participants' forced liquidations can move prices and liquidity independent of a firm's own strategy, and can also cause exchange-side execution/price-feed failures that corrupt marks and fills.
- The shift to 24/7 derivatives trading (CME, May 2026) reduces gap risk but is new enough that its operational track record (Monday processing, maintenance-window behavior) is not yet proven through a full market cycle.

### Gaps
- No data found quantifying how the specific spot exchanges most likely to be used by a quant firm (vs. Binance broadly) performed operationally during October 2025; only Binance's outage was documented in detail.

## Are there notable instances of market manipulation (wash trading, pump-and-dump, spoofing), and how prevalent is it versus regulated equity markets?

### Takeaway
Multiple independent academic and industry studies converge on wash trading representing a majority — in some cases 50–99% — of reported volume on unregulated crypto exchanges, an order of magnitude beyond anything tolerated in regulated equity markets, while spoofing enforcement (SEC/CFTC) is active but comparatively small in scale and case count.

### Cited Findings
- A widely-cited academic study (Cornell/Newcastle/Tsinghua) found wash trades account for over 70% of total trading volume on unregulated exchanges, and ~61% even after controlling for exchange characteristics; one estimate put wash trading at 77.5% of reported volume on unregulated venues (median 79.1%) — [The TRADE News](https://www.thetradenews.com/illegal-wash-trading-accounts-for-up-to-70-of-crypto-volumes-finds-study/); [arXiv: Crypto Wash Trading](https://arxiv.org/abs/2108.10984)
- The same research found wash trading above 53.4% of volume for "Tier-1" exchanges and 81.7% for "Tier-2" exchanges — [arXiv](https://arxiv.org/pdf/2108.10984)
- Regulated exchanges show trading patterns consistent with those observed in traditional regulated financial markets (first-significant-digit distribution, size rounding, transaction-tail distribution tests), while unregulated crypto exchanges show abnormal statistical patterns indicating rampant fabricated volume — [ACM/DL study](https://dl.acm.org/doi/fullHtml/10.1145/3442381.3449824)
- Four independent studies using four different detection methods across seven years put the fake/wash-traded share of reported crypto volume between 51% and 99%, roughly consistent with Wall Street Journal and industry estimates of 67%–99% — [search synthesis of academic literature](https://arxiv.org/pdf/2108.10984)
- SEC spoofing enforcement is active but on a much smaller dollar scale than exchange hacks: e.g., a December 16, 2025 settled SEC action against a trader for a two-year spoofing scheme generating ~$373,885 in illicit gains via non-bona-fide orders in thinly traded stocks; a separate August 11, 2025 settlement addressed options spoofing from 2020–2022 — [Morgan Lewis Securities Enforcement Roundup](https://www.morganlewis.com/pubs/2026/01/securities-enforcement-roundup-december-2025)
- Overall CFTC enforcement action volume fell from 96 cases in 2023 to 58 in 2024, with the commission noting an expected continued downward trend in fraud/spoofing cases outside the crypto space specifically — implying crypto-specific manipulation enforcement is comparatively under-resourced relative to the scale of the problem academic studies identify — [Paul Hastings](https://www.paulhastings.com/insights/client-alerts/cftcs-high-profile-crypto-cases-lead-to-massive-recoveries-but-far-fewer-enforcement-actions)

### Inferences
- Reported crypto trading volume, especially on offshore/unregulated venues, should not be trusted at face value for liquidity or execution-cost modeling — a strategy relying on displayed volume for sizing or slippage estimates risks being calibrated against majority-fabricated data.
- The gap between academic-estimated manipulation prevalence (majority of volume on many venues) and actual regulatory enforcement (a handful of six-figure settled cases per year) suggests manipulation in crypto is far less policed, in relative terms, than in equities — enforcement cannot be relied upon as a deterrent or a backstop the way it functions in regulated equity markets.

### Gaps
- No comparable, recent quantitative estimate of wash-trading/manipulation prevalence in regulated equity markets was retrieved, so the "versus regulated equity markets" comparison in the key question is qualitative/inferential (equities are understood to have negligible wash trading due to surveillance and Reg NMS-era market structure) rather than backed by a directly comparable cited statistic.
- Specific, named pump-and-dump case studies (e.g., on particular tokens) were not retrieved in this pass; only wash-trading prevalence and spoofing enforcement were sourced.

## What insurance or risk-mitigation products exist for institutional/algorithmic crypto traders?

### Takeaway
Insurance coverage exists in two distinct, non-equivalent forms — exchange-run internal reserve funds (e.g., Binance's SAFU) and third-party crime/specie insurance underwritten by traditional (re)insurers such as Lloyd's of London syndicates — but both are narrower in scope than they appear, typically covering only exchange-side hot-wallet theft and excluding user-side losses, phishing, or investment/market losses.

### Cited Findings
- SAFU (Secure Asset Fund for Users) is Binance's self-funded emergency reserve, built from a portion of trading fees, intended to cover losses from platform-side security incidents — [Bitget Academy](https://www.bitget.com/academy/safu-crypto-guide)
- SAFU is explicitly not equivalent to FDIC-style deposit insurance; it is an exchange-established reserve under the exchange's own legal/governance framework, not an independent regulated insurance product. It covers exchange-level hacks, system failures, and technical breaches, but does not cover user-side incidents like phishing, wrong transfers, or investment losses — [HackerNoon](https://hackernoon.com/protection-funds-insurance-and-fdicsipc-what-actually-covers-what)
- Traditional (re)insurance is also available: Lloyd's of London has multiple syndicates offering crypto coverage through specialized managing general agents, including Evertas (Lloyd's-linked, coverage cited up to $360 million) and Canopius (a Lloyd's syndicate offering crypto and digital-asset coverage) — [search synthesis](https://hackernoon.com/protection-funds-insurance-and-fdicsipc-what-actually-covers-what)
- Some exchanges serving US retail/institutional clients (Coinbase, Gemini, Bakkt) carry actual crime insurance policies from underwriters including Lloyd's of London; Coinbase's policy covers a portion of hot-storage assets against theft, hacking, and employee collusion — [search synthesis](https://hackernoon.com/protection-funds-insurance-and-fdicsipc-what-actually-covers-what)

### Inferences
- Insurance coverage at exchanges is typically partial (often limited to a fraction of hot-wallet balances) and should not be relied upon to make a trading firm whole after a major exchange-side incident (as FTX and Mt. Gox customers experienced) — insurance mitigates but does not eliminate exchange counterparty risk.
- A trading firm operating at scale should consider its own dedicated crime/specie insurance policy (via a Lloyd's syndicate or similar underwriter) covering firm-controlled custody infrastructure, rather than relying solely on venue-level protection funds it does not control and cannot audit in real time.

### Gaps
- No pricing, typical coverage limits, or claims-history data for institutional crypto crime insurance policies was retrieved — only that such products exist and which underwriters/MGAs offer them.
- Did not find data on how often SAFU-style funds have actually been triggered/paid out historically, so their practical reliability (versus stated existence) is unverified.
