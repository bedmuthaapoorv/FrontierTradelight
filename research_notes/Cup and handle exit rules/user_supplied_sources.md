# User-Supplied Sources: Stop-Loss Theory, the Han/Zhou/Zhu Critique, and Minervini's Rules

These three documents were blocked to web research (HTTP 403 or not fetched). The user supplied them as PDFs. Text was extracted, and all three were read in full. Page numbers are the PDF page numbers, which match the printed page numbers in the Kaminski & Lo preprint. For each finding, the note says whether it **confirms**, **contradicts** or **refines** a claim in `reports/Cup and handle exit rules.md` or in the earlier notes (`stops_and_failed_breakouts.md`, `profit_taking_and_trailing.md`).

Local copies:
- Kaminski & Lo: `C:\Users\apoorv.bedmutha.MEDIASSISTINDIA\Downloads\Lo_When Do Stop-Loss.pdf` (42 pp.; same file as [MIT DSpace](https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf))
- Vogel / Alpha Architect: `C:\Users\apoorv.bedmutha.MEDIASSISTINDIA\Downloads\Taming the Momentum Investing Roller Coaster_ Fact or Fiction_ - Alpha Architect.pdf` (9 pp. browser print, 6 Oct 2026; [web](https://alphaarchitect.com/taming-the-momentum-roller-coaster-fact-or-fiction/))
- TraderLion / Celeste: `C:\Users\apoorv.bedmutha.MEDIASSISTINDIA\Downloads\Mark Minervini's Risk Management Wins The 2021 U.S. Investing Championship With A 334% Return _ TraderLion.pdf` (14 pp. browser print; [web](https://traderlion.com/investing-champions/mark-minervinis-risk-management/))

---

## 1. Kaminski & Lo, "When Do Stop-Loss Rules Stop Losses?" (preprint submitted to *Journal of Financial Markets*, 28 June 2013)

**Grade: rigorous** (analytical theory plus an empirical illustration). **Applicability to single-stock breakout exits: indirect.** It is a portfolio-level asset-allocation overlay on an index, not a per-trade stop on an individual stock.

### 1.1 The exact rule analysed
- **Definition 1, the "simple stop-loss policy" S(γ, δ, J)** (p.9). This is a 0/1 switch between the portfolio P and a safe asset F:
  - **Exit** (move 100% to F) when the J-period cumulative return R_{t-1}(J) < −γ while invested.
  - **Re-enter** (move 100% back to P) when the *single-period* return r_{t-1} ≥ δ while stopped out.
  - Otherwise stay in, or stay out.
  - Cumulative return is the *sum* of simple returns over the last J periods (eq. 1, p.8, fn. 8). The trigger is a rolling-window drawdown, **not** a loss measured from an entry price, and not a trailing stop from a peak.
- The exit and re-entry rules are asymmetric on purpose. Exit uses the cumulative return, re-entry uses the one-period return. The authors motivate this by loss aversion / the disposition effect and a "snake-bite" reluctance to re-enter (pp.9-10).
- **Transaction costs are set to zero** (κ = 0) throughout. The cost term is defined in eq. 7 (pp.11-12) but never used.
- The rule is a heuristic and is not derived as optimal (p.14). The authors note that such rules "can be implemented security-by-security" (p.14), but **they do not test that**.

### 1.2 Theoretical results
- **"Stopping premium"** Δμ = E[r_st] − E[r_t] = p_o (r_f − E[r_t | s_t = 0]), where p_o is the probability of being stopped out. **"Stopping ratio"** = Δμ / p_o (Definition 2, p.10). By the authors' own definition, a stop "stops losses" if and only if Δμ > 0 (p.12).
- **Random walk (Proposition 1, pp.16-17):** Δμ = −p_o·π ≤ 0, where π is the risk premium. The stop **always lowers expected return**. It can lower volatility if p_o is large enough and π small enough: Δσ² = −p_o σ² + p_o(1−p_o)π² (eq. 13c). **Confirms** the report's random-walk claim.
- **AR(1) momentum / mean reversion (Proposition 2, pp.19-20):** Δμ/p_o ≈ −π + ρσ + η, with η ≥ 0 for ρ > 0 and "reasonable" parameters. Mean reversion (ρ < 0) hurts. Momentum (ρ > 0) can help. **Sufficient condition: ρ ≥ π/σ, the Sharpe ratio measured at the same frequency as ρ** (eq. 18). Worked example: an annual Sharpe of 1.00 equals a monthly Sharpe of about 0.29, so ρ would need to be ≥ 0.29 at monthly frequency (p.20). This is a high bar.
- **Regime switching (Proposition 3, pp.22-24):** in a two-state Markov model, a stop can add value **only if the low-mean regime's expected return is below the safe asset's return (μ₂ < r_f)**, *and* the stop is accurate enough: P(low regime | stopped out) ≥ (μ₁ − r_f)/(μ₁ − μ₂) (eq. 25). If equities beat the safe asset in both regimes, the stop always lowers expected return, however accurate it is (p.24). The required accuracy falls as the spread between the regime means widens (p.24).
- **Variance:** the stop reduces unconditional variance when it switches into a lower-volatility asset (p.4; Definition 3, p.13). The authors decline to use the Sharpe ratio as their primary yardstick for dynamic strategies (p.13), but they report Sharpe changes empirically anyway.

### 1.3 Empirical setting
- **Data: daily futures, 5 Jan 1993 to 7 Nov 2011** (p.25). The risky asset is the **IMM S&P 500 futures contract**. The safe asset is the **10-year CBT Treasury-note futures contract**, described in the conclusion as "U.S. long-term bonds futures" (p.28). Correlation is −17.29% (p.25).
- Table 1 (p.35): S&P futures 7.295% annualised mean, 19.499% SD, Sharpe 0.37, max drawdown 26.62%. 10-year note futures 1.181% mean, 6.331% SD. *Note:* the table's ρ column shows −0.06 for the S&P, but the text says "net positive serial autocorrelation" (p.25). This internal inconsistency is not resolved in the paper.
- Rolling 75- and 150-day autocorrelation is time-varying, alternating between momentum and mean-reverting periods (p.25; Figs. 1-2, pp.30-31). The fitted two-state model gives a good regime of +22.3% mean / 10.3% vol and a bad regime of −39.0% mean / 33.0% vol (Table 2, p.36).
- **Parameter grid (p.26):** monitoring frequencies of daily (1), weekly (5), monthly (20) and quarterly (60) days. Stopping windows J are 3, 5 and 10 × the frequency, giving pairs (3,1), (5,1), (10,1), (15,5), (25,5), (50,5), (60,20), (100,20), (200,20), (180,60), (300,60), (600,60). The figures also show (360,120), (600,120) and (1200,120). Exit threshold γ runs from −1.5 to −0.5 SD. Re-entry δ runs from −0.5 to +1 SD.
- **Results (pp.26-27):**
  - **Short-horizon stops (daily and weekly windows) have negative stopping premiums over large parameter ranges.**
  - Stops at **monthly and longer** frequencies "perform better and can achieve positive stopping premiums", with lower volatility and higher Sharpe (Figs. 3-5, pp.32-34).
  - The exit threshold matters more than the re-entry threshold (p.27).
- **Magnitude (p.5):** "in one calibration, using stop loss over monthly intervals in daily data can increase the return by 1.5% and decrease the volatility by 5% causing an increase in the Sharpe Ratio by as much as 20%." The paper does not specify the calibration's parameters. The units are presumably annualised percentage points.
- The authors attribute the gain to "conditional momentum effects following periods of losses in equities" and to flight-to-safety momentum in long-term bonds (pp.5, 7, 28).

### 1.4 What it does NOT say (important for this project)
- **Nothing about individual stocks, breakouts, chart patterns, gaps, intraday fills, trailing stops, profit targets or time stops.** The only asset tested is a diversified US index future.
- The stop is a rolling-window drawdown with automatic re-entry. The backtester's exit is a one-shot trade exit with no re-entry, unless the entry screener signals again.
- There are **no transaction costs** (κ = 0). The positive results at monthly-plus frequency come partly from earning the bond-futures return while stopped out, and the bond leg had its own momentum in that sample. A stopped-out NSE trade sits in cash at zero return, because `backtest.py` books no cash yield. That removes the main source of the paper's premium.
- It gives no NSE or emerging-market evidence.

### 1.5 Confirms / contradicts / refines
- **Confirms (report, "The handle-low stop caps risk…"):** under a random walk a stop always lowers expected return, and momentum is a route to positive value (pp.3, 16-20).
- **Refines:** the report says stops add value "only when returns have momentum". The paper gives **two** routes: momentum with ρ ≥ the per-period Sharpe, **or** a regime-switching process where the bad regime earns less than the safe asset and the stop identifies it accurately enough (pp.19-24).
- **Refines (report intro, "Rigorous studies say stops cut risk rather than raise returns"):** in *this* paper, on index futures at monthly-plus horizons, some stops raised return *and* cut volatility (p.5, pp.26-27). The "risk not return" conclusion holds for the **single-stock** studies (Lo & Remorov; Dai et al.), not for Kaminski & Lo's index result. The report should scope the claim.
- **Contradicts the earlier notes' description of the empirical setting.** `stops_and_failed_breakouts.md` and `profit_taking_and_trailing.md` say "monthly US equities 1950-2004, switching to bonds, 50-100 bp/month during stop-out periods", and quote a quant-investing.com statistic: "equities beat bonds 70% of the time… only 30% during stopped-out periods". **None of these numbers appear in the supplied 2013 version.** They probably come from an earlier working-paper version (summarised by dailyspeculations / BSIC / quant-investing). Treat them as unverified secondary figures from a different version. The verified setting is daily S&P futures vs 10-year T-note futures, 1993-2011.
- **Supports, weakly, the report's "wider is better" stance.** Hair-trigger stops on short windows lost expected return (pp.26-27). This is an index-level analogy, not evidence about ATR multiples on stocks.
- **Supports the report's evaluation framing:** judge the stop on drawdown, volatility and skew as well as CAGR. The authors themselves evaluate return *and* volatility (pp.4, 12-13).

---

## 2. Jack Vogel (Alpha Architect, 10 Aug 2016), "Taming the Momentum Investing Roller Coaster: Fact or Fiction?"

**Grade: practitioner** (industry research blog from an SEC-registered adviser). It is a critique plus a limited replication of **Han, Zhou & Zhu (HZZ), "Taming Momentum Crashes: A Simple Stop-Loss Strategy"** (rigorous; working paper, Jan 1926 to Dec 2013 sample per its abstract quoted on p.7).

### 2.1 HZZ's rule and headline result, as reported
- Rules (p.2): rebalance the long and short books monthly. If a **long position declines by 10% (or 5%)**, sell it and hold cash/RF until month-end. If a **short position rises 10% (or 5%)**, cover it and hold cash until month-end.
- HZZ abstract (p.7): at a 10% stop, the worst monthly loss falls **from −49.79% to −11.36% (equal-weighted)** and **from −64.97% to −23.28% (value-weighted)**, "while the Sharpe ratios are more than doubled".
  - **Correction:** the report and notes say −11.34%. The figure in HZZ's abstract and table is −11.36%. The notes' value-weighted figures (−65.34% → −23.69%, via Crossing Wall Street) come from an earlier 1926-2011 version. The 1926-2013 version says −64.97% → −23.28%.
- **HZZ Table 1** (embedded image, p.2), equal-weighted monthly figures:

| Portfolio | Avg ret % | SD % | Sharpe | Skew | Min % |
|---|---|---|---|---|---|
| Winners, no stop | 1.24 | 7.75 | 0.160 | −0.29 | −33.06 |
| Winners, 10% stop | 1.27 | 6.02 | 0.211 | 0.69 | −12.87 |
| Winners, 5% stop | 1.53 | 4.80 | 0.319 | 1.45 | −8.48 |
| Winners, 15% stop | 1.05 | 6.71 | 0.156 | 0.25 | −16.82 |
| Losers, no stop | 0.24 | 8.81 | 0.027 | 1.17 | −39.50 |
| Losers, 10% stop | −0.42 | 5.90 | −0.071 | −1.35 | −39.27 |
| WML, no stop | 0.99 | 6.01 | 0.165 | −1.18 | −49.79 |
| WML, 10% stop | 1.69 | 4.58 | 0.369 | 1.83 | −11.36 |
| WML, 5% stop | 2.35 | 4.21 | 0.558 | 2.24 | −8.94 |
| WML, 15% stop | 1.20 | 4.77 | 0.252 | 1.34 | −15.01 |

- **Reading of the table (my inference, from HZZ's own numbers):**
  - On the **long (winners) leg alone**, a 10% stop barely changes average return (1.24% → 1.27%), but cuts SD by about 22%. It lifts Sharpe 0.160 → 0.211 (+32%, not "doubled"), flips skew from negative to positive, and cuts the worst month from −33.06% to −12.87%.
  - **Most of the WML return gain comes from the short leg.** The stop turns losers from +0.24% into −0.42%, which is a gain for a short seller.
  - "Sharpe more than doubled" is a **long-short** result.
  - The 15% stop *hurt* the winners leg (1.05% vs 1.24%; Sharpe 0.156 vs 0.160).
  - The 5% stop was best on the winners leg.
- *Vogel's text error:* Vogel says the 15% rule gave 1.20% for winners (p.3). In the table, 1.20% is the WML figure. The winners figure is 1.05%. His point (15% is worse) holds either way.

### 2.2 Vogel's critique (p.3)
- The strategy needs **daily monitoring of every position**, which is hard for an ordinary investor (p.3).
- On the winners leg, the 10% stop is about equal to no stop (1.27% vs 1.24%). Only the 5% rule clearly helps the winners leg (1.53%) (p.3).
- HZZ's universe includes **micro-caps (~50% of stocks)**, which raise liquidity and implementation problems (p.3).

### 2.3 Vogel's replication (pp.3-5)
- **Universe:** US common stocks above the **NYSE 40th percentile** of market cap (mid/large caps). **Long leg only**, because shorting is impractical (pp.3-4).
- **Portfolios (p.4):**
  - MOM 10 EW Monthly: top decile on 12-month momentum skipping the last month, equal-weighted, rebalanced monthly.
  - The same with a **daily 10% stop**: if any position is down 10% during the month, sell on the trigger day and hold cash to month-end.
  - The same with a **daily 5% stop**.
  - Benchmark: S&P 500 equal-weighted.
- **Period 1/1/1927 to 12/31/2013. Gross returns, no fees or transaction costs** (p.5).
- **Findings (p.5):** the **simple, no-stop portfolio has higher CAGR and higher Sharpe**. The 5% and 10% stop portfolios have **lower drawdowns and higher Sortino ratios**.
  - **The results table itself did not survive the browser print.** Only a logo image is embedded on p.5, so the exact CAGR, Sharpe and MaxDD figures are not available.
  - [Unverified] The exact numbers should be taken from the live web page if needed.
- **Costs (pp.5-6):** the stop portfolios add daily intra-month trading. Vogel suggests anyone considering the strategy "would probably want to take 300-600bps off" (especially back to 1927), which "might eliminate all the benefits of the risk management strategy". This is a judgement, not a computed cost model.
- **Verdict (p.6):** "stop-loss rules can help with drawdowns, but will cause more trading, thus adding expense and reducing performance… the devil is clearly in the details."

### 2.4 What Vogel did NOT examine
- He does **not** discuss **look-ahead bias**, whether the stop is filled at the stop price or at the close, intraday vs close triggers, or gap-through fills. "Sell the security on the day the rule is triggered" (p.4) leaves the fill price unspecified, both for him and, as reported, for HZZ.
- He gives no monthly vs daily monitoring comparison beyond noting that the stop requires daily checks.
- He gives no explicit cost modelling: the 300-600 bp figure is a rule of thumb.
- He gives no sub-period or out-of-sample split, and no test of the 15% stop.

### 2.5 Confirms / contradicts / refines
- **Contradicts the report's framing of HZZ as "the one strongly positive result."** The doubled Sharpe is a long-short, micro-cap-inclusive, gross result. For a long-only, mid/large-cap implementation, which is the analogue of buying NSE breakouts, Vogel finds the stop **lowers CAGR and Sharpe** before costs. It still improves drawdown and Sortino (p.5). HZZ's own winners-leg numbers show a much smaller benefit than the headline (table above). The report must stop presenting HZZ as evidence that stops raise risk-adjusted returns on a long book.
- **Confirms the report's central claim:** the stop's job is to bound the left tail (drawdown, skew, Sortino), not to raise CAGR. Both HZZ's winners leg and Vogel's long-only replication show the tail benefit.
- **Refines:** it adds a cost warning that applies directly. The leaderboard is pre-cost. Rules that trade more (tight stops) will look better in the leaderboard than they are, which is the report's own point, now with a practitioner magnitude.
- **Tension to record (no rule change):** HZZ's 5% stop beat 10% on the winners leg (1.53% vs 1.27%), which on its face favours a *tighter* stop than the report's up-to-8% cap. Do not act on it:
  1. It is a portfolio with monthly re-entry into fresh winners, not a single-trade exit.
  2. It is gross and micro-cap-inclusive, with an unspecified fill price.
  3. Vogel's mid/large-cap long-only replication found that neither 5% nor 10% beat no-stop on CAGR or Sharpe.
  4. Lo & Remorov found that tight single-stock stops underperform once a 0.2% half-spread is charged.
  5. Bulkowski's breakout data shows tight stops get hit far more often.

---

## 3. TraderLion (Craig Celeste, 31 Aug 2024), "Mark Minervini's Risk Management Wins The 2021 U.S. Investing Championship With A 334% Return"

**Grade: secondary.** It is a vendor-blog paraphrase of Minervini's statements, with no data, no sample and no test. The 334% contest return (p.2) is a single-account outcome, not evidence for any individual rule. This replaces the earlier "secondary-only, from a search snippet" status: the article has now been read, but it remains secondary.

### 3.1 Every risk-management rule the article states, with numbers where given
- **Stop size:** an illustrative "normal stop loss is 5%". If gains are not large enough to offset that risk, "something has to change". In weak markets, "take quicker profits and smaller losses" (p.3). **No maximum loss per trade, as % of equity or of price, is stated.**
- **Leverage and size:** Minervini uses leverage and large position sizes. With a leveraged position he tightens stops and "demand[s] a gain immediately intraday" (p.3). **No position-size percentage or risk-per-trade percentage is given.**
- **Quick profit-taking:** "Once the stock is up, Mark locks in gains. The sacrifice is losing out on the longer-term trade." He compounds small wins on large positions rather than holding through intermediate corrections (pp.3-4).
- **Progressive exposure:** small test positions first. Size up and add trades only when they work, and wait when they get stopped out (p.5).
- **Sell into strength:** "he is always trying to sell out as the stock is making new highs", to smooth the equity curve (p.5).
- **"Improve the worst-case scenario" (p.6):** once the stock gives positive feedback, he (a) moves the stop up to **breakeven**, and (b) **sells half "when the stock is at a gain equal to the original stop"** (i.e., at +1R). The next sentence gives a different version: "The best way to manage a trade is to **sell half when the gain is double the original stop** and move your stop up to break even" (i.e., at +2R). **The article is internally inconsistent: it gives 1R in one sentence and 2R in the next.**
- **Summary rule:** "Sell into strength at a multiple of your risk to ensure your averages are asymmetrical to the upside" (p.10).
- **Know your averages:** average gain, average loss and batting average must align. Plan the profit target relative to the stop (p.9). **No numeric gain/loss ratio or win rate is given.**
- **Trailing stop:** **none specified.**
- **2021 market context:** a "Pop and Drop" theme in which breakouts rose for a couple of days, then rolled over (p.6). Trade examples: SCHW (gap-up entry, exit if the gap reverses), PYPL (held through a weak close because the original stop was not violated, then sold into strength), NUE (breakout with no follow-through) (pp.7-8). These are anecdotes, not statistics.

### 3.2 What it does NOT contain
- It does **not** contain the "minimum 2x, generally 2-3x your risk, or above your average gain" phrasing that the earlier notes attributed to this page from a search snippet. Nor does it contain "sell a third to a half". The article gives **half at 1R or 2R**. The 2-3R / one-third wording rests only on the Stock Trading Approach Substack.
- It does not mention the 10%/20% breakeven thresholds or the "never let a 2-3R gain become a loss" rule. Those remain unverified, as `profit_taking_and_trailing.md` already says.

### 3.3 Confirms / contradicts / refines
- **Refines (report, "Profit targets and scaling out"):** the report says "sell a third to a half at 2-3R and trail the rest". The supplied article says **sell half at +1R or +2R (inconsistent), plus a stop moved to breakeven**. Both still need partial exits, which `backtest.py` cannot do. The executable substitute ("move the stop to breakeven at +2R") is now confirmed as part of Minervini's stated method, at secondary grade.
- **Contradicts, in style, the report's big-winner design.** Minervini's 2021 method deliberately "lock[s] in gains quickly… miss[ing] the longer move" (pp.3-4). That is the opposite of O'Neil's 8-week hold and of the report's wide-trail philosophy. The two practitioners disagree, and the article frames Minervini's approach as tied to leverage and a choppy 2021 market.
- **Contradicts Bulkowski on breakeven** (as the report already notes). Bulkowski's double-bottom test (n = 2,333) found breakeven moves cut profit. Minervini (secondary, no data) recommends them. The data-backed side still wins for v1.
- **Confirms** that the stop should be defined before entry and that profit-taking should be expressed in R-multiples. R reporting is already in the report's `describe_state` plan.

---

## 4. Net effect on the recommended exit rules

**No recommended rule changes.** The reasons, rule by rule:
- **Initial stop `max(0.99 × HandleLow, 0.92 × entry)`.** HZZ's winners-leg 5% result is the only new number pointing tighter. It is gross, portfolio-level and micro-cap-inclusive, and Vogel's long-only mid/large replication does not reproduce a return benefit. Kaminski & Lo show short-window stops destroy expected return. The stop stays as it is, justified as tail control.
- **No breakeven move.** Minervini's breakeven rule is now confirmed from the article, but it is secondary with no data and is tied to a leveraged quick-profit style. Bulkowski's data still opposes breakeven moves. Keep "none". "Breakeven at +2R" stays an optional paired variant, not v1.
- **Trail, big-winner floor, targets, time stop, max hold.** None of the three documents test these, so nothing changes.
- **What does change:**
  - **Evidence grades and wording.** HZZ is no longer cited as the strong positive result. The Kaminski & Lo setting is corrected. Minervini's rule is restated as half at 1-2R plus breakeven.
  - **The expectation-setting.** All three sources now point the same way. A stop on a long book buys smaller drawdowns and better skew at a cost in CAGR, Sharpe and turnover, unless the returns trend strongly enough.

## 5. Remaining gaps
- Bulkowski's *Encyclopedia of Chart Patterns* "Cup With Handle" chapter ([sponser.co.il PDF](https://www.sponser.co.il/forumfiles/6910Cup%20With%20Handle.pdf)) is still unread in full.
- "Do initial stop-losses stop losses?" (Bangor/Bond) is still unread. Only search-snippet claims are available.
- Vogel's replication table (exact CAGR, Sharpe, MaxDD, Sortino) did not survive the PDF print.
- HZZ's fill-price assumption (stop price vs close) is unknown. The full HZZ paper has not been read.
- The Kaminski & Lo "monthly 1950-2004, 50-100 bp/month" figures from an earlier version remain unverified.
