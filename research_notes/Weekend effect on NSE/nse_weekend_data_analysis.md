# Weekend and day-of-week effects on NSE: analysis of the local price cache and what they mean for the app

How the numbers were produced. Every number here comes from the user's cached NSE daily OHLCV: 692 files `SYMBOL_2019-11-28_2026-01-01.csv` in `Strategies/Default/data/backtest_cache`. Each file was loaded through `backtest._load_symbol_history`, which drops the 8 Muhurat and special-DR-session bars via `market_calendar.drop_special_sessions`. That leaves 1,508 trading dates, including 3 full Saturday sessions (1 Feb 2020, 20 Jan 2024, 1 Feb 2025). Point-in-time Nifty 500 membership comes from `historical_universe.members_as_of(day)`, giving a median of 495 members with data per day. No web data was used.

The window is Dec 2019 to Dec 2025, with sub-periods 2020 (Dec 2019 to Dec 2020), 2021–23 and 2024–25. Scripts and raw outputs are in the scratchpad `C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/`:
- Scripts: `wk_load.py`, `wk_main.py`, `wk_app.py`, `wk_extra.py`.
- Outputs: `wk_results.txt`, `wk_results_app.txt`, `wk_results_extra.txt`.

The day-classification and breakout logic reuse `main.py` and `brk.py` from the holiday-shortened-weeks study.

Definitions used throughout:
- **Returns.** For each stock and day: close-to-close (CC) = close / previous own-row close − 1. Gap = open / previous close − 1. Open-to-close (OC) = close / open − 1.
- **Equal-weight (EW) series.** The cross-sectional mean over point-in-time members.
- **Clean days.** A Monday counts as clean if it follows a normal weekend (Fri → Mon, no holiday). Tue–Fri count as clean if they follow a normal overnight. In both cases the day must not be the day before a holiday.
- **Relative volume.** The stock's volume divided by its trailing 50-row median, then the median across members.
- **Volatility.** The time-series SD of the daily EW return, plus the mean cross-sectional |CC|.

Caveats that apply to every section:
- **Survivorship.** The cache covers symbols that were Nifty 500 members at some snapshot. Some delisted names could not be fetched. Membership has only 13 snapshots, so it is approximate between them.
- **Adjustment.** Prices are adjusted only for splits and bonuses, by a heuristic that back-adjusts moves of more than about 35%. Dividends are not adjusted, so ex-dividend days show up as small negative gaps. Any stock-day with |CC|, |gap| or |OC| above 35% was dropped as a likely artefact. A real crash of more than 35% is therefore also dropped, and corporate-action moves under 35% (some demergers, rights issues) remain as false "gaps".
- **Daily bars only.** Pre-open auction mechanics and intraday paths cannot be measured.
- **Multiple testing.** Roughly 150 hypothesis tests were run across all sections. At that count, a Bonferroni bar is p < 0.0003, about |t| > 3.6. Any single p of 0.01–0.05 here is suggestive at best.

## 1. Weekday pattern: is Monday different, and is the difference in the weekend gap or in Monday's trading?

### Takeaway
Over the full Dec 2019–Dec 2025 window, Monday is the only weak weekday. Its EW close-to-close return was −0.09% on clean Mondays against about +0.12% on Tue–Fri, a gap of −0.21 pp with p = 0.04. The shortfall comes from Monday's trading session (open-to-close −0.27%), not from the weekend gap, which is positive (+0.19%) and not significantly smaller than other nights' gaps.

The return difference is fragile:
- It is driven by a few crash Mondays in 2020.
- It disappears when 2020 is excluded (p = 0.26), when Feb–May 2020 alone is excluded (p = 0.15), or when returns are winsorised (p = 0.16; Mann–Whitney p = 0.66).
- The median Monday is positive (+0.24%).

Two Monday features do hold up in every period: the weekend gap is larger in absolute size (about 0.82% against 0.65%, p < 0.001), and Monday volatility is higher.

### Cited Findings
- **Clean days, Dec 2019–Dec 2025:**

  | Day | n | CC mean | CC median | Gap | OC | \|gap\| | % up | Rel. vol | SD of EW CC | Mean stock \|CC\| |
  |---|---|---|---|---|---|---|---|---|---|---|
  | Mon | 264 | −0.089% | +0.244% | +0.187% | −0.273% | 0.821% | 47.5 | 0.986 | 1.57% | 1.88% |
  | Tue | 271 | +0.132% | +0.210% | +0.328% | −0.192% | 0.625% | 49.3 | 1.002 | 1.03% | 1.64% |
  | Wed | 272 | +0.241% | +0.362% | +0.273% | −0.028% | 0.601% | 51.3 | 1.001 | 0.98% | 1.61% |
  | Thu | 264 | +0.103% | +0.181% | +0.207% | −0.103% | 0.661% | 48.9 | 0.999 | 1.11% | 1.60% |
  | Fri | 265 | −0.012% | +0.108% | +0.162% | −0.165% | 0.695% | 45.9 | 1.019 | 1.06% | 1.64% |

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **Monday against Tue–Fri, clean days:**
  - CC: diff −0.21 pp, t = −2.03, p = 0.043, bootstrap 95% CI [−0.41, −0.01] pp.
  - Gap: −0.06 pp, p = 0.39.
  - OC: −0.15 pp, p = 0.048.
  - |gap|: +0.18 pp, t = 3.49, p = 0.001.
  - % up: p = 0.36. Relative volume: −1.9%, p = 0.16.
  - Mean stock |CC|: +0.25 pp, t = 4.02, p < 0.001.
  - Levene variance test: p < 0.001.
  - Across all five weekdays: ANOVA on CC p = 0.012, Kruskal–Wallis p = 0.028.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **All sessions, including holiday-adjacent days (Mon n = 301, Tue–Fri n = 1,201):**
  - Monday CC −0.105% against Tue–Fri: diff −0.24 pp, p = 0.013.
  - OC diff −0.17 pp, p = 0.017.
  - Gap diff −0.07 pp, p = 0.26.
  - |gap| +0.17 pp, p < 0.001.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **Wednesday is the strongest day.** On clean days its CC is +0.24%, against others: +0.21 pp, p = 0.003; OC p = 0.024. Friday's clean CC is −0.01%, p = 0.14. — [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **The Monday return gap is not robust:**
  - 2021–2025 only: Monday−other CC −0.10 pp, p = 0.26; OC −0.03 pp, p = 0.69. The |gap| difference stays: +0.18 pp, t = 4.02.
  - Excluding Feb–May 2020: CC p = 0.15.
  - 5% winsorised: p = 0.16. Mann–Whitney: p = 0.66.
  - The five worst clean Mondays were 23 Mar 2020 (−11.96%), 16 Mar 2020 (−5.44%), 12 Apr 2021 (−5.07%), 21 Dec 2020 (−4.81%) and 31 Aug 2020 (−4.14%).
  - Share of days with positive EW return: Monday 58.7%, Tue–Fri 60.6%.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **Cross-reference to the holiday study (weekends of different lengths), reopen-day averages:**

  | Reopen type | n | Gap | \|gap\| | OC | CC | % up |
  |---|---|---|---|---|---|---|
  | Normal overnight | 1,140 | +0.25% | 0.65% | −0.11% | +0.13% | 49.1 |
  | Normal weekend (Mon) | 277 | +0.18% | 0.82% | −0.28% | −0.11% | 47.4 |
  | Long weekend | 36 | +0.56% | 0.97% | −0.14% | +0.42% | 54.2 |
  | After a mid-week holiday | 43 | +0.20% | 0.76% | −0.36% | −0.16% | 43.6 |

  - Long weekend against normal weekend: signed gap +0.38 pp, p = 0.018; |gap| p = 0.20; CC +0.53 pp, p = 0.058.
  - The Friday before a long weekend: CC +0.59%, n = 16, against −0.02% (n = 276) for Fridays before a normal weekend.
  - These match the earlier [holiday notes](file:///D:/git-repos/FrontierTradelight/research_notes/Holiday%20shortened%20weeks%20on%20NSE/nse_data_analysis.md), sections 3–4. Small differences arise because Muhurat bars are now dropped, so post-Muhurat days are re-labelled as long weekends.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)

### Inferences
- **What "Monday effect" means here.** In this cache, Monday is a higher-variance day: |gap| is about 27% larger, and EW SD is about 1.5x that of other days. Its mean return is pulled down by a few crisis Mondays, mostly from 2020. It is not a reliable negative drift. The gap itself is not negative. All the weakness on Monday is in the cash session, and that weakness is concentrated in 2020.
- **Intraday fade.** Every weekday has a positive average gap and a negative-or-flat average OC. That is the general overnight-up, intraday-down pattern already noted in the holiday study. Monday's OC (−0.27%) is the most negative, but in 2021–25 it is not distinguishable from the other days.
- **Wednesday strength** (p = 0.003) is the kind of result to expect by chance at least once among about 150 tests. It does not survive a multiple-testing bar.

### Gaps
- There is no index-level (Nifty 50 or Nifty 500 index) series in the cache. All results are for an equal-weight stock average, which over-weights small members compared with the cap-weighted index.
- Daily bars cannot show whether the Monday OC weakness comes in the first hour (a "gap fade") or later.

## 2. Does the pattern differ by size, by volatility, or by Friday's return?

### Takeaway
- **Size and volatility.** The Monday shortfall points the same way in every turnover and volatility tercile, with similar size (CC −0.18 to −0.26 pp against Tue–Fri). It is a little stronger, and borderline significant, in the smallest-turnover (p = 0.026) and highest-volatility (p = 0.042) terciles. Monday volume is relatively lighter only in the largest names (relative volume 0.94).
- **Friday's return** matters much more than size. After an up Friday, Monday averaged +0.24% (53% of stocks up). After a down Friday it averaged −0.49% (41% up), a difference with t = 3.97. Both the gap and the session contribute.
- **Monday-specific continuation.** On other days, the prior day's direction carries into the next gap but then reverses intraday. On Mondays the continuation persists through the session. That holds at index level and, much more strongly, at stock level.

### Cited Findings
- **Turnover terciles** (60-day average traded value, ranked point in time; clean days; Monday against Tue–Fri):
  - Smallest: CC −0.22 pp (p = 0.026), gap −0.02 pp (p = 0.72), OC −0.19 pp (p = 0.009).
  - Middle: CC −0.18 pp (p = 0.11).
  - Largest: CC −0.19 pp (p = 0.094), OC −0.10 pp (p = 0.21).
  - Monday gap by tercile, small to large: +0.26%, +0.19%, +0.12%.
  - Monday OC by tercile, small to large: −0.35%, −0.25%, −0.20%.
  - Monday relative volume by tercile, small to large: 1.07, 0.99, 0.94.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **Volatility terciles** (60-day SD of daily returns; Monday against Tue–Fri):
  - Low: CC −0.13 pp (p = 0.12).
  - Middle: −0.19 pp (p = 0.076).
  - High: −0.26 pp (p = 0.042), OC −0.18 pp (p = 0.075).
  - Monday CC by tercile, low to high: −0.04%, −0.07%, −0.14%.
  - Monday OC by tercile, low to high: −0.18%, −0.27%, −0.35%.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **Monday after an up Friday (n = 146) against a down Friday (n = 130), EW market, normal weekends:**
  - CC: +0.24% against −0.49% (t = 3.97, p < 0.001).
  - Gap: +0.33% against +0.01% (p = 0.007).
  - OC: −0.09% against −0.50% (p = 0.004).
  - % up: 53.1 against 41.1 (p < 0.001).
  - Correlation of Friday CC with Monday: gap 0.18, OC 0.15, CC 0.23.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **The same split for Tue–Fri (prior day up, n = 660, against down, n = 412):**
  - Gap: +0.30% against +0.15% (p = 0.001).
  - OC: no difference (p = 0.43).
  - Correlations with the prior day's CC: gap 0.19, OC −0.06, CC 0.07.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **Stock level.** Each stock's own prior-session return sign was compared against its next-session return, demeaned by date, as winners minus losers:
  - Mondays: gap +0.112 pp (t = 6.63), OC +0.010 pp (t = 0.39), CC +0.124 pp (t = 4.20).
  - Tue–Fri: gap +0.056 pp (t = 8.92), OC −0.069 pp (t = −5.65), CC −0.013 pp (t = −1.06).

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)

### Inferences
- **Mid-week.** A stock that rose yesterday tends to open higher and then give it back intraday, so there is no net continuation.
- **Over a weekend.** Friday's winners open about twice as far ahead, and the intraday give-back does not happen, so the continuation persists for the full Monday session. For a long-only breakout (a Friday up-day by construction), that suggests Monday-filled entries pay a larger gap but avoid the usual entry-day fade. Section 4 confirms this.
- **Index level.** The weak average Monday is mostly what Mondays after down Fridays look like. Conditioning on Friday explains more than the weekday label does.
- **Size.** Small and high-volatility names show the most negative Monday OC, which fits retail-heavy names fading after the open. The tercile-level t-stats (about 2) do not clear a multiple-testing bar.

### Gaps
- Turnover is a proxy for size. No market-cap data was used.
- There is no sector or F&O-eligibility split. F&O stocks could behave differently because of derivatives hedging.

## 3. Has the pattern changed over time, and did T+1 settlement or the expiry-day move matter?

### Takeaway
- **Over time.** The Monday return shortfall is a 2020 phenomenon: CC −0.69 pp and OC −0.72 pp against Tue–Fri (OC p = 0.005). It is small and not significant in 2021–23 (−0.12 pp, p = 0.31) and in 2024–25 (−0.07 pp, p = 0.62). The larger Monday |gap| holds in every period.
- **T+1 settlement** (fully live 27 Jan 2023) shows no measurable change in the Monday-minus-other difference. The difference-in-differences CI includes zero for CC, gap, OC and |gap|.
- **Expiry days.** Under the Thursday regime, Nifty weekly expiry days had slightly lower cross-sectional |CC| (1.63% against 1.73%, p = 0.028). Returns and cash-market relative volume were no different. Monthly expiry days carried about 7% more relative volume (p = 0.023).
- **After the move to Tuesday** (1 Sep 2025), only 18 expiries are available. Nothing is significant.

### Cited Findings
- **Clean-day Monday against Tue–Fri, by period:**

  | Period | n Mon / other | CC diff (p) | Gap diff (p) | OC diff (p) | \|gap\| diff (p) |
  |---|---|---|---|---|---|
  | 2020 | 46 / 199 | −0.69 pp (0.081) | +0.02 pp (0.94) | −0.72 pp (0.005) | +0.19 pp (0.31) |
  | 2021–23 | 129 / 531 | −0.12 pp (0.31) | −0.08 pp (0.19) | −0.04 pp (0.65) | +0.15 pp (<0.001) |
  | 2024–25 | 89 / 342 | −0.07 pp (0.62) | −0.05 pp (0.65) | −0.01 pp (0.92) | +0.23 pp (0.020) |

  - Monday EW SD in 2020 was 2.54%, against 1.1–1.8% on other days.
  - In 2024–25, Friday was the weakest day: CC −0.20%, against others −0.29 pp, p = 0.023. Wednesday was the strongest: +0.30%, p = 0.010.

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **T+1 split.** The pre-T+1 window runs from 1 Jan 2021 to 26 Jan 2023; the post-T+1 window from 27 Jan 2023 to 31 Dec 2025.
  - Pre-T+1, Monday against Tue–Fri: CC −0.064% against +0.115% (diff p = 0.26). |gap| 0.81% against 0.66%.
  - Post-T+1: CC +0.031% against +0.078% (p = 0.67). |gap| 0.70% against 0.50%.
  - Difference-in-differences (post minus pre) of Monday−other: CC +0.13 pp [−0.24, +0.51]; gap +0.09 pp [−0.14, +0.32]; OC +0.04 pp [−0.26, +0.33]; |gap| +0.05 pp [−0.10, +0.22].

  Source: [wk_results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results.txt)
- **How expiry days were labelled.** These are rule-based dates, not taken from NSE's expiry list:
  - Weekly expiry is the last session on or before Thursday until 31 Aug 2025, and on or before Tuesday from 1 Sep 2025. 13 pre-Sep-2025 expiries rolled to Wednesday because of a Thursday holiday.
  - Monthly expiry is the last Thursday of the month, or the last Tuesday from Sep 2025, rolled back over holidays.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **Thursday regime (to Aug 2025), expiry (n = 300) against non-expiry (n = 1,119) days:**
  - CC +0.12% against +0.08% (p = 0.60).
  - OC −0.10% against −0.17% (p = 0.22).
  - Mean stock |CC| 1.63% against 1.73% (p = 0.028).
  - Median stock relative volume 1.003 against 1.008 (p = 0.73).
  - Monthly expiry (n = 69): relative volume 1.07 against 1.00 (p = 0.023); CC p = 0.55.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **Tuesday regime (Sep–Dec 2025), expiry (n = 18) against non-expiry (n = 65):**
  - CC −0.04% against +0.05% (p = 0.55).
  - Relative volume 0.99 against 0.95 (p = 0.33).
  - |CC| p = 0.35.
  - Monthly expiry: n = 4, relative volume 1.14 (p = 0.19).
  - In this window Thursdays (now non-expiry) had OC −0.39% and relative volume 0.93; Tuesdays had OC −0.17% and relative volume 1.00. Each cell has only 15–17 days.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)

### Inferences
- **Size of the effect.** Excluding 2020, the day-of-week return pattern is economically tiny: the Monday shortfall is about 0.1 pp per day, not significant. It is far below round-trip costs of about 0.22% explicit (per the GARP exit_rules note).
- **The stable feature** is that Mondays carry a larger absolute overnight move. That is a risk and slippage feature, not an alpha source.
- **Expiry.** Under the Thursday regime nearly every Thursday was an expiry, so "expiry effect" and "Thursday effect" cannot be separated before Sep 2025. Neither shows a return effect. Cash-market stock volume does not respond to weekly index expiry and responds only modestly to monthly expiry, which is also the single-stock F&O expiry.

### Gaps
- Expiry dates are inferred from rules supplied in the brief, not from an exchange list. No futures or options volume data is in the cache.
- The post-Sep-2025 sample (about 4 months) is far too small for any conclusion about the Tuesday expiry.
- T+1 is confounded with the 2023–25 market regime. A DiD on about 3 years per side cannot isolate it.

## 4. App implications: entry-day effect, weekend gap risk for stops, and delaying or skipping Friday signals

### Takeaway
- **(a) Entry-day effect.** Breakout signals fired on Friday and filled at Monday's open performed in line with Mon–Thu signals over 5, 10 and 20 sessions. Excess return over 10 sessions differed by −0.13 pp, t ≈ −0.75. The Monday entry day itself is better: the entry-day open-to-close excess was +0.13% for Friday signals against −0.12% to −0.34% for other days, a difference of +0.34 pp with t ≈ 5.3, and the gap persists in all three periods. The weakest signal day is Monday (filled Tuesday): xf10 −0.79%, but only t ≈ −1.9 against Tue–Fri, and not significant in 2021–25.
- **GARP v1 trades in `backtest_trades.csv`.** These cluster in 22 entry dates, about 10 real cohorts, so entry weekday is confounded with cohort and cannot be tested.
- **(b) Weekend gap risk.** A stock's Monday open is about 3x as likely as a normal overnight to gap at least 5% below Friday's close: 92 against 32 per 10,000 stock-days. For −10% the ratio is 18 against 4.7. More than half of Monday's −5% events come from two days (7 Apr 2025 and 23 Mar 2020). Excluding those, Monday is still about 1.7–2.2x overnight, and on calm-market days 1.4–2.3x. Gaps of −20% or more are rare everywhere (about 0.4–0.6 per 10,000).
- **(c) Delaying or skipping Friday signals.**
  - Delaying a Friday-signal entry to Monday's close gains nothing: about 0.0 pp.
  - For Mon–Thu signals, delaying to the next close improves raw 5–20 session returns by about +0.4 pp. Friday signals are the exception where the next-open fill is not penalised.
  - Skipping Friday signals changes the average breakout trade by at most 0.07 pp and removes about 20% of trades.
  - Neither change is worth making for Friday specifically.

### Cited Findings
- **Breakouts by signal weekday**, FULL Dec 2019–Dec 2025. A breakout is a close above the prior 20-row high on volume above 1.5x the prior 20-row average, for member stocks only. Entry is at the next row's open. fk = close of the k-th session (entry day = session 1) / entry open − 1. x = excess over the EW of the same measure for all eligible members on the signal date. t-stats come from a date-clustered bootstrap.

  | Signal day (fill day) | Signals | Entry-day OC excess (t) | xf5 (t) | xf10 (t) | xf20 (t) | Raw f10 | Raw f20 | Hit rate xf10 > 0 |
  |---|---|---|---|---|---|---|---|---|
  | Mon (Tue) | 5,241 | −0.34% (−4.3) | −0.71% (−5.6) | −0.79% (−4.7) | −0.77% (−3.6) | −0.10% | +0.84% | 39.7% |
  | Tue (Wed) | 4,947 | −0.21% (−4.1) | −0.41% (−3.8) | −0.44% (−2.9) | −0.40% (−2.1) | +0.56% | +1.79% | 41.8% |
  | Wed (Thu) | 4,798 | −0.15% (−2.7) | −0.49% (−4.7) | −0.46% (−3.3) | −0.43% (−2.3) | +0.34% | +1.60% | 41.2% |
  | Thu (Fri) | 4,948 | −0.12% (−2.4) | −0.32% (−3.0) | −0.21% (−1.4) | −0.06% (−0.3) | +0.74% | +1.85% | 43.7% |
  | Fri (Mon) | 4,921 | +0.13% (+2.3) | −0.59% (−5.0) | −0.61% (−4.0) | −0.74% (−3.7) | +0.42% | +1.32% | 41.3% |

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **Friday-signal minus Mon–Thu-signal** (date-clustered bootstrap; 284 against 1,147 signal dates):
  - Entry-day OC excess: +0.34 pp, t ≈ 5.3, CI [+0.22, +0.46].
  - xf5: −0.10 pp, CI [−0.35, +0.16].
  - xf10: −0.13 pp, CI [−0.45, +0.22].
  - xf20: −0.32 pp, CI [−0.77, +0.12].
  - 2021–25: entry-day OC excess +0.33 pp (t ≈ 4.8); xf10 −0.12 pp (t ≈ −0.7).
  - By period, the entry-day OC advantage is +0.36 pp in 2020 (t ≈ 2.1), +0.37 pp in 2021–23 (t ≈ 4.5) and +0.27 pp in 2024–25 (t ≈ 2.2).
  - Fridays before a long weekend (385 signals, 19 dates) do not differ from normal Fridays (xf10 −0.18 pp, CI [−1.19, +1.04]).

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **Raw entry-day (Monday) OC.** For Friday breakouts it was +0.00%, against −0.28% for the EW universe on normal-weekend Mondays. For Mon–Thu signals the raw entry-day OC was −0.35%. — [wk_results_extra.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_extra.txt)
- **Monday signals (filled Tuesday) against Tue–Fri signals:**
  - FULL: xf5 −0.26 pp (t ≈ −1.9), xf10 −0.36 pp (t ≈ −1.9), xf20 −0.36 pp (t ≈ −1.5). ANOVA of date-mean xf10 across signal weekdays: p = 0.008.
  - 2021–25: xf10 −0.10 pp (t ≈ −0.5); ANOVA p = 0.053.

  Source: [wk_results_extra.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_extra.txt)
- **Signal rate by weekday** (% of member stock-days): Mon 3.61, Tue 3.37, Wed 3.31, Thu 3.40, Fri 3.45. — [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **(c) Delaying entry to the next session's close**, raw mean returns, FULL. "Same-length" holds k sessions from the delayed entry. "Same-exit" keeps the original exit date.
  - Friday signals (k = 5 / 10 / 20):
    - Next open: −0.22 / +0.42 / +1.32%.
    - Next close, same length: −0.23 / +0.46 / +1.34%.
    - Next close, same exit: −0.21 / +0.40 / +1.33%.
  - Mon–Thu signals (k = 5 / 10 / 20):
    - Next open: −0.17 / +0.38 / +1.51%.
    - Next close, same length: +0.26 / +0.85 / +1.94%.
    - Next close, same exit: +0.19 / +0.73 / +1.89%.
  - Delay gain for Friday minus Mon–Thu signals: −0.43 pp (t ≈ −2.6) at k = 5, −0.44 pp (t ≈ −2.4) at k = 10, −0.38 pp (t ≈ −2.2) at k = 20.
  - 2021–25: −0.45, −0.45 and −0.53 pp, with t from −2.7 to −3.5.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **(c) Skipping Friday signals**, FULL (24,895 → 19,974 signals):
  - Mean f5: −0.18% → −0.17%.
  - Mean f10: +0.39% → +0.38%.
  - Mean f20: +1.47% → +1.50%.
  - Excess f20: −0.48% → −0.42%.
  - 2021–25: f20 +1.35% → +1.39%.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **(b) Gap-through frequency**, member stock-days per 10,000. The open is measured against the previous close; |gap| above 35% is excluded.

  | Reopen | Stock-days | Gap ≤ −5% | Gap ≤ −10% | Gap ≤ −20% | Low touches −5% | Share of −5% touches already through at open | Share for −10% | Gap ≥ +5% |
  |---|---|---|---|---|---|---|---|---|
  | Normal overnight | 556,712 | 32.3 | 4.7 | 0.59 | 361 | 9.0% | 10.9% | 31.9 |
  | Normal weekend (Mon) | 135,349 | 91.6 | 18.4 | 0.37 | 706 | 13.0% | 19.5% | 47.5 |
  | Long weekend | 17,509 | 40.6 | 2.3 | 0.57 | 524 | 7.7% | 6.3% | 108.5 |
  | After a mid-week holiday | 21,047 | 25.7 | 4.8 | 0.48 | 498 | 5.2% | 12.3% | 42.3 |

  - The mean gap, given a gap of −5% or worse, is −8.0% overnight and −8.5% on Mondays.
  - For high-volatility-tercile stocks: Monday 129 per 10k (≤ −5%) and 30 per 10k (≤ −10%), against 50 and 6.8 overnight.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **(b) Concentration of large Monday gaps:**
  - The Mondays with the most stocks gapping ≤ −5% were 7 Apr 2025 (375 stocks) and 23 Mar 2020 (342). Together these account for 57.8% of all Monday ≤ −5% events.
  - Excluding the top two days in each group: Monday 38.9 against overnight 23.1 per 10k at −5%, and 5.1 against 2.3 at −10%.
  - On calm-market days (EW gap above −1%): Monday 18.3 against 13.0 per 10k at −5%, and 4.4 against 1.9 at −10%.
  - 2021–25: Monday 62.0 per 10k (29.2 excluding 7 Apr 2025) against overnight 15.3.
  - A date-level test of the ≤ −5% rate, Monday against overnight, gives p = 0.14, because the effect sits in a few days.

  Source: [wk_results_extra.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_extra.txt); [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt)
- **GARP v1 trades** (`backtest_trades.csv`; 620 trades, 250 funded; the strategy column is blank):

  | Entry weekday | Trades | Entry dates | Mean return | Hit rate |
  |---|---|---|---|---|
  | Mon | 61 | 2 | +22.9% | 70% |
  | Tue | 191 | 6 | −0.5% | 48% |
  | Wed | 119 | 4 | +4.9% | 52% |
  | Thu | 117 | 7 | +6.9% | 48% |
  | Fri | 132 | 3 | +18.4% | 79% |

  - Entries are concentrated on rebalance cohorts, for example 18 Dec 2023 (Mon, 60 trades, +22.6%) and 16 Jun 2023 (Fri, 68 trades, +28.1%).
  - The Tuesday group includes all 61 RangeEnd trades: the 2024–25 cohorts were still open at the end of the data.

  Source: [wk_results_app.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/wk_results_app.txt); [backtest_trades.csv](file:///D:/git-repos/FrontierTradelight/Strategies/Default/data/backtest_trades.csv)
- **Engine mechanics.**
  - Entry is always at the open of the first row after the signal day.
  - Intraday strategies use only that row and square off at its close.
  - Exits come from `generated_exit_strategy.resolve_exit`.
  - The current GARP exit is close-only (the CatastrophicStop fills at the close), so an open gap cannot "gap through" a GARP stop. The loss is taken at that day's close.

  Source: [backtest.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/backtest.py); [exit_rules.md](file:///D:/git-repos/FrontierTradelight/Strategies/Default/exit_rules.md)

### Inferences
- **Entry-day effect.** The weekday a signal fires does not need special handling for multi-day holds. Friday-signal trades are statistically indistinguishable from others at 5, 10 and 20 sessions. They have a better first day, because Monday's intraday session continues Friday's winners instead of fading them (section 2), but they give that back later. The weaker Monday-signal (Tuesday-fill) cohort is borderline in the full sample and not significant in 2021–25.
- **The fill convention matters more than the weekday.** Across all simple breakouts, entering at the next open costs about 0.4 pp against entering at the next close, because of the post-gap intraday fade. Monday-fill (Friday-signal) trades are the one case that does not pay that cost. If the user wants to test a delayed-entry variant, the evidence favours "next close for Mon–Thu signals", not a Friday-specific change.
  - These are pre-cost raw breakouts, not the user's actual strategy filters.
  - The pattern is consistent with the holiday study's overnight-up / intraday-down finding.
- **Intraday strategies.** For the Momentum Loser intraday short (enter at open, square off at close), Monday is on average the most negative OC day (−0.27% EW clean). Within that, Mondays after a down Friday are much worse (OC −0.50%) and stocks that rose on Friday hold up on Monday. That favours shorting Monday opens of Friday losers. But the 2021–25 Monday OC is not different from other days, so this is not a reliable edge.
- **Stops and weekend gaps.**
  - Any stop rule evaluated on the close (as GARP's is) is unaffected by gaps in the sense of "price jumps through the level": the exit simply happens at the close.
  - If a future exit rule uses intraday lows or stop-at-level fills, the backtester must fill at min(open, stop) on gap days. Otherwise it will understate losses most on Mondays. About 13–20% of Monday −5%/−10% touches are already through the level at the open, against 9–11% overnight. The conditional gap is about −8.5%.
  - Weekend gap risk is largely systemic (crash Mondays). It cannot be diversified across positions, which matters for a portfolio of concurrent long positions.
- **GARP.** No weekday conclusion is possible. Any differences in the table reflect which semi-annual cohort happened to enter on that weekday.

### Gaps
- `backtest.py` was not run, as instructed. Breakout results use a simplified definition, not Horizontal Breakout v9 or the other generated rules, and ignore costs, slippage and position limits. Strategy-level P&L effects are inferred, not measured.
- Only GARP v1 trades were available in `backtest_trades.csv`. No technical strategy's trade list was available to split by entry weekday.
- Gap-risk counts cannot separate a real price gap from an unadjusted corporate action below the 35% heuristic threshold, such as a demerger. Ex-dividend gaps are included because dividends are not adjusted.
