# Review of the GARP research

Review of [GARP strategy for NSE screener.md](GARP%20strategy%20for%20NSE%20screener.md) and its four notes in `research_notes/GARP strategy for NSE screener/`, done on 2026-10-13. Scope: critique only, no build. Intended direction assumed: Design A (a periodically rebalanced GARP sleeve) with an EODHD/FMP data trial.

## Verdict

The research is sound, well sourced and candid about weak evidence. It correctly concludes that PEG is the least defensible part of GARP and that India's documented premia sit in quality, value, momentum and revisions. Spot-checked figures all trace to the notes: 38% of US stocks qualifying in the FactorResearch test, 19.09% MQVLv 50 CAGR, AAII's 12.9%/yr, 0.92%/month Indian QMJ alpha, 10.96%/yr IIMA momentum, −1.93% Value 50 five-year CAGR to 2020, and EODHD's "often only 6 years / 20 quarters" for non-US firms.

Its main flaw is in synthesis, not sourcing: **the validation plan does not reconcile with the data that will actually exist**, and the report understates how far the current backtest engine is from supporting a sleeve.

## Problems in the report

1. **The walk-forward plan cannot be run as written.** The report asks for test windows covering 2008, the 2018–19 small-cap bear market, 2020 and 2024–25. But:
   - The repo's point-in-time Nifty 500 membership has only 13 snapshots, February 2019 to September 2026, with gaps of 18 and 21 months. Any date before 2019 silently falls back to the 2019 list (`Strategies/Default/historical_universe.py:159-175`).
   - EODHD's non-US history is often only 6 years / 20 quarters for smaller companies.
   - The gates need 5 years of positive EPS plus a 3-year CAGR, which is about a 6-year warm-up before the first valid rebalance.

   The realistic testable window is roughly 2019 or 2021 to 2026.

2. **That window is a value-friendly regime, so a backtest will flatter a tight-valuation GARP.** The report's own data shows Nifty500 Value 50 compounding 34.5% a year over the five years to December 2025, after −1.93% a year over 2015–20. The report discusses regime dependence at length but never connects it to its own data limits. A backtest on the data that is actually obtainable cannot answer "does GARP work in India". It can only show how GARP behaved in one favourable regime, and the write-up of any result should say so up front.

3. **The semi-annual rebalance recommendation rests on a momentum study.** The report cites NSE's 2026 whitepaper (quarterly rebalancing added 20–50% more churn for marginal gain) as if it applied to GARP. The notes carry the caveat that it tested momentum, not GARP; the report drops it. GARP's inputs change mainly at results seasons, so a quarterly cadence timed after filing deadlines may behave differently.

4. **The report's Design A silently differs from the notes' Design A.** The notes specify a quarterly rebalance and a rank-average score that includes PEG. The report switches to the S&P two-step (growth rank, then quality/value rank), semi-annual rebalancing, and PEG only as a sanity cap. The choice is defensible, since S&P's low-PEG volatility finding supports it, but the report should say it overrode the notes' spec and why.

5. **Sector-relative P/E and sector caps need consistent historical sector labels, and the repo doesn't have them.** `membership.csv` switches from NSE's old sector taxonomy (18–19 sectors, e.g. "IT", "SERVICES") to the new one (about 20–21) between the 2020 and 2022 snapshots. `universe_info` also keeps old-style labels for names that dropped out early. The report doesn't mention this.

6. **The survivorship check is underspecified.** The proposed 20-ticker EODHD/FMP trial should deliberately include delisted and merged names: DHFL, Coffee Day, Allahabad Bank, Andhra Bank, Corporation Bank and HDFC Ltd. It should also compare `filing_date` against NSE announcement timestamps. The repo's price cache is already missing several of these names, so survivorship gaps exist on the price side too.

7. **Minor: the tax rates are left "to verify".** Earlier research in this repo already found short-term capital gains at 20% and long-term at 12.5% above ₹1.25 lakh, for sales after 23 July 2024. Whether Budget 2026 changed them is still unchecked.

## Fit with the codebase (understated in the report)

1. **No fundamentals code or data exists** anywhere in `Strategies/`. The only references are disclaimers saying P/E is not computable.

2. **The backtest engine cannot express a sleeve.**
   - `backtest.py` opens an independent fixed ₹100 trade for every passing signal. There's no holdings state, rebalance, target weights, caps, rank buffers or transaction costs.
   - The equity curve carries open positions at cost rather than marking them to market. For 3–12-month holds, max drawdown and the composite score would be badly understated.
   - The leaderboard only records runs over exactly 2021-01-01 to 2026-01-01.

   The report lists a "portfolio-level backtest engine" as a new capability; in practice it is the largest piece of work.

3. **The Gemini compiler path is the wrong home for GARP.**
   - The `evaluate_stock` signature is fixed, and strategy code may not contain loops or helper functions (`generate_screener.py:141-147`).
   - Common Method Library functions may not read files.
   - The library smoke test calls `evaluate_stock` with a fixed argument list and cannot pass fundamentals (`method_library.py:111`).

   Ranking, z-scores, buffers and caps are cross-sectional, portfolio-level operations. A hand-written, deterministic sleeve module outside the compiler fits better than the report's suggested library functions. It also matches the direction of [Replacing Gemini with local models.md](Replacing%20Gemini%20with%20local%20models.md).

4. **Existing blockers a GARP build would hit first:**
   - `method_library.py:9` imports `fcntl`, which doesn't exist on Windows, so `generate_screener.py` fails on import on this machine.
   - `Strategies/Default/rules.md` is missing (it was untracked in commit 84a92b4), so `backtest.py:631` crashes at the end of any run until a rules file is loaded.
   - `membership.csv` contains 10 rows of NSE placeholder tickers (DUMMY…) that need filtering.

## Recommended next step

Make a **data-feasibility gate** the first milestone, before writing any strategy code:

1. Run the EODHD/FMP trial on about 20 tickers spanning large, mid and small caps plus the delisted names above. Confirm 10-year statement depth and `filing_date` accuracy against NSE timestamps.
2. Decide whether point-in-time membership can be extended before 2019 and filled across the two long gaps, from sources whose terms allow it.
3. Fix the realistic backtest window from what steps 1 and 2 deliver, and state its regime bias in advance. Run the tight-cap and loose-cap variants side by side, as the report itself suggests, rather than tuning one.

Only then size the sleeve engine and fundamentals pipeline.
