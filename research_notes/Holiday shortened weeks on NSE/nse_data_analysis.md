# Holiday-shortened weeks on NSE: analysis of the local price cache and what it means for the engine

Scope and provenance. Every number below comes from the user's own cached NSE daily OHLCV data (`Strategies/Default/data/backtest_cache`, 692 files named `SYMBOL_2019-11-28_2026-01-01.csv`). That is the cache `backtest.py` loads through `_load_symbol_history()` / `load_universe_history()`. No web data was used. The longest window the cache supports is 28 Nov 2019 to 1 Jan 2026. Statistics use Dec 2019 to Dec 2025 (called "FULL") and 2021–2025 separately. ("2021–2026" adds only one 2026 row, 1 Jan 2026.) The analysis scripts and raw outputs are in the scratchpad: `C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/` (`load.py`, `cal.py`, `main.py`, `brk.py`, `eng.py`, `mech.py`, and `results.txt`, `results_brk.txt`, `results_eng.txt`).

Data caveats that apply to every section:
- **Survivorship.** The cache holds every symbol that was a Nifty 500 member at any snapshot overlapping the window (`symbols_between`). Membership was applied point in time with `historical_universe.members_as_of()`, giving about 488 members with data per day. There are only 13 membership snapshots, so membership between snapshots is approximate. Stocks whose history could not be fetched (some delistings) are missing, so some survivorship bias remains.
- **Adjustment.** Prices are only split/bonus-adjusted, using a heuristic: any day-over-day move beyond about 35% is back-adjusted (`nse_utils.adjust_for_splits_and_bonuses`). Dividends are not adjusted, so ex-dividend drops show up as small negative returns and gaps. I dropped any stock-day with |return|, |gap| or |open-to-close| above 35% as a likely artefact.
- **Dates.** Raw cache timestamps read `YYYY-MM-DD 18:30:00`. I checked that the naive date is the true NSE trading date for this cache: known holidays are absent (22 Jan 2024, 20 May 2024, 20 Nov 2024, 15 Aug 2025), and known special sessions are present (Budget Saturdays 1 Feb 2020 and 1 Feb 2025, Saturday 20 Jan 2024, Muhurat Sunday 12 Nov 2023). So the +1-day correction in `nse_utils.fetch_stock_history` is already reflected in the cached files.
- **Inference.** Tests are Welch t-tests with percentile bootstrap 95% CIs (4,000 resamples) unless stated. For breakouts I used date- or week-clustered bootstraps. I ran about 60 tests, so treat any single p ≈ 0.01–0.05 as suggestive, not established. A Bonferroni-style bar would be p < 0.001.

## 1. NSE trading calendar, weekday holidays, and week labels

### Takeaway
The cache contains 1,516 trading dates. Over Dec 2019–Dec 2025 there are 86 weekday non-sessions or Muhurat-only days, and about 24% of weeks are shortened: 66 four-session weeks and 10 three-session weeks, against 241 five-session weeks. The cache also contains 8 "abbreviated" sessions (Muhurat and special live sessions) and 3 full Saturday sessions, and the engine treats all of these as ordinary bars.

### Cited Findings
- **How the calendar was built.** It is the union of dates across all 692 cached symbols. Every date has at least 558 symbols trading, so no date is spurious. Weekdays break down as Mon 302, Tue 305, Wed 300, Thu 305, Fri 297 rows. There are 7 weekend rows. — [chk.py / cal.py output](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/cal.py)
- **Abbreviated sessions.** These were detected as days when the median member's volume was below 0.45x its trailing 50-row median. They are: Sat 14 Nov 2020 (0.23x), Thu 4 Nov 2021 (0.17x), Mon 24 Oct 2022 (0.17x), Sun 12 Nov 2023 (0.17x), Sat 2 Mar 2024 (0.07x), Sat 18 May 2024 (0.11x), Fri 1 Nov 2024 (0.14x) and Tue 21 Oct 2025 (0.17x). They match the Diwali Muhurat sessions and the 2024 Saturday special live sessions. Full-volume weekend sessions are 1 Feb 2020, 20 Jan 2024 and 1 Feb 2025. — [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **Weekday holidays found per year.** These are weekdays with no regular session; * marks a Muhurat-only day:
  - 2019 (Dec only): 25-Dec.
  - 2020 (12): 21-Feb, 10-Mar, 02-Apr, 06-Apr, 10-Apr, 14-Apr, 01-May, 25-May, 02-Oct, 16-Nov, 30-Nov, 25-Dec.
  - 2021 (14): 26-Jan, 11-Mar, 29-Mar, 02-Apr, 14-Apr, 21-Apr, 13-May, 21-Jul, 19-Aug, 10-Sep, 15-Oct, 04-Nov*, 05-Nov, 19-Nov.
  - 2022 (13): 26-Jan, 01-Mar, 18-Mar, 14-Apr, 15-Apr, 03-May, 09-Aug, 15-Aug, 31-Aug, 05-Oct, 24-Oct*, 26-Oct, 08-Nov.
  - 2023 (15): 26-Jan, 07-Mar, 30-Mar, 04-Apr, 07-Apr, 14-Apr, 01-May, 29-Jun, 15-Aug, 19-Sep, 02-Oct, 24-Oct, 14-Nov, 27-Nov, 25-Dec.
  - 2024 (17): 22-Jan, 26-Jan, 08-Mar, 25-Mar, 29-Mar, 11-Apr, 17-Apr, 01-May, 20-May, 17-Jun, 17-Jul, 15-Aug, 02-Oct, 01-Nov*, 15-Nov, 20-Nov, 25-Dec.
  - 2025 (14): 26-Feb, 14-Mar, 31-Mar, 10-Apr, 14-Apr, 18-Apr, 01-May, 15-Aug, 27-Aug, 02-Oct, 21-Oct*, 22-Oct, 05-Nov, 25-Dec.
  - Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **Sessions per year.** Total rows per year: 2020 252, 2021 248, 2022 248, 2023 246, 2024 249, 2025 249. Regular weekday sessions only: 245–250 per year. — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Week labels.** Weeks run Mon–Sun and a session counts only if it is a regular weekday session; Muhurat days count as holidays. Of 317 complete weeks, 241 have 5 sessions, 66 have 4 and 10 have 3. None have fewer than 3. The 3-session weeks are: Apr 6 2020, Mar 29 2021, Nov 1 2021 (Diwali), Apr 11 2022, Oct 24 2022 (Diwali), Apr 3 2023, Jan 22 2024, Mar 25 2024, Apr 14 2025 and Oct 20 2025 (Diwali). — [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **Stock-specific gaps.** 1.30% of member stock-days on regular sessions (9,651 of 743,689) have no row for that stock, from suspensions or fetch gaps. — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)

### Inferences
- About one week in four is shortened. Shortened weeks are therefore a routine condition that any session-counted rule meets every month, not an edge case.
- Holiday names are not in the data. My identifications (Holi, Diwali, Republic Day, the 2024 election and Ram Mandir holidays, and so on) come from my own knowledge and are not verified against an NSE circular.

### Gaps
- There is no official NSE holiday list in the repo to cross-check against. The data-derived calendar cannot tell a market holiday from a day when the whole cache failed to fetch, but no low-count dates were found.
- Only about 6 years are available, which gives 76 shortened weeks.

## 2. Shortened versus normal weeks: return, volatility, volume, turnover, dispersion

### Takeaway
Shortened weeks show no robust difference in return, volatility, volume or turnover. Volatility and dispersion per session are statistically the same, and raw cross-sectional dispersion is lower in shortened weeks only because they have fewer sessions. In 2021–2025 the average shortened week's equal-weight return was lower: –0.40% for 4-session weeks against +0.54% for 5-session weeks, p = 0.038. That difference does not hold per session or in the full sample, so it should not be traded on.

### Cited Findings
FULL sample, Dec 2019–Dec 2025 (cross-sectional equal-weight average of point-in-time members):

| Week type | n weeks | EW mean | EW median | EW std | Mean per session | Std/√n | Cross-sec. dispersion | Disp/√n | % stocks up | Median rel. volume | Agg. turnover rel. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 sessions | 241 | +0.47% | +0.69% | 2.80% | +0.09% | 1.25% | 4.77% | 2.13% | 51.3 | 1.00 | 1.04 |
| 4 sessions | 66 | –0.16% | +0.15% | 2.78% | –0.04% | 1.39% | 4.45% | 2.23% | 45.6 | 1.03 | 1.08 |
| ≤3 sessions | 10 | +2.46% | +1.50% | 3.40% | +0.82% | 1.96% | 4.22% | 2.43% | 66.7 | 1.01 | 1.08 |

Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)

Tests of shortened weeks (n = 76) against 5-session weeks (n = 241), FULL sample:
- Weekly return: diff –0.28 pp, t = –0.73, p = 0.47, bootstrap CI [–1.05, +0.46] pp.
- Return per session: p = 0.84.
- Variance (Levene test), raw: p = 0.99. Per √session: p = 0.26.
- Dispersion: raw diff –0.34 pp, p = 0.028. Per √session: p = 0.12.
- Relative volume: p = 0.31. Aggregate turnover (relative to trailing 50-session median): +3.6%, p = 0.14.
- Within-week daily EW volatility: p = 0.75.
- Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)

2021–2025 (shortened n = 64, 5-session n = 196):
- EW mean: 4-session –0.40%, 3-session +1.53% (n = 9), 5-session +0.54%.
- Shortened against 5-session: diff –0.67 pp, t = –2.10, p = 0.038, CI [–1.29, –0.04] pp. Mann–Whitney p = 0.027.
- Per session: p = 0.125. % stocks up: 43–45% against 52%, p = 0.063.
- Raw dispersion: 4.12% against 4.54%, p < 0.001. Per √session: p = 0.34.
- Volume and turnover: no difference (p = 0.84 and p = 0.26).
- Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)

### Inferences
- **Volatility.** The raw weekly EW standard deviation is the same (about 2.8%) whether a week has 4 or 5 sessions. In other words, per-session volatility is about 10% higher in shortened weeks (1.39% against 1.25% per √session), but the difference is not significant. Holiday news accumulation could explain it, but the sample cannot confirm that.
- **Dispersion.** Lower raw dispersion is fully explained by having fewer sessions. A rule that thresholds a weekly or N-calendar-day move will see slightly smaller moves in shortened weeks.
- **The ≤3-session bucket.** It has only 10 weeks and is dominated by Diwali weeks and the April 2020 COVID rebound (+10.8% in the week of 6 Apr 2020), so its +2.5% mean is not reliable.

### Gaps
- The sample is small: 76 shortened weeks, 10 of them 3-session weeks.
- Weeks are not separated by holiday type (Diwali, Holi, election) or by market regime, so any effect from a particular festival cannot be told apart from seasonality.

## 3. Pre-holiday day versus normal days

### Takeaway
Pre-holiday days as a whole are no different from normal days. The exception is the session before a long weekend (the Thursday before a Friday holiday, or the Friday before a Monday holiday), which was clearly stronger. Its EW return was +0.63% against +0.08% on normal days (t = 3.06, p = 0.004, n = 32), with 58% of stocks up against 49%. The effect persists in 2021–2025 (+0.52%, p = 0.011, n = 24) but rests on a small sample.

### Cited Findings
- **All pre-holiday days (n = 76) against normal days (n = 1,333), FULL sample.**
  - EW return: +0.22% against +0.08% (median +0.30% against +0.23%). Diff +0.14 pp, p = 0.31, CI [–0.13, +0.40] pp.
  - % stocks up: diff +2.6 pp, p = 0.27.
  - Relative volume: 0.98–1.07 against 1.01, p = 0.88.
  - Share of days with positive EW return: 63% against 60%, binomial p = 0.64.
  - Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **Before a long weekend, FULL sample (n = 32).** EW +0.63%, % stocks up 57.8%, relative volume 1.07. Against normal days: return diff +0.56 pp (t = 3.06, p = 0.004); % up diff +9.2 pp (p = 0.005); volume p = 0.29. Against ordinary Fridays before a normal weekend (–0.02%, n = 263): diff +0.65 pp, t = 3.40, p = 0.002. — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Before a long weekend, 2021–2025 (n = 24).** EW +0.52% (diff +0.45 pp, p = 0.011); % up +9.1 pp (p = 0.016); against normal Fridays p = 0.001. — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Before a one-day mid-week holiday (n = 43).** EW –0.09%, % up 46%, relative volume 0.97, all not significant (p = 0.37). For 2021–2025, n = 39 and p = 0.88. — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Session before a Muhurat or special session (n = 11, mostly the pre-Diwali day).** EW +0.50%, p = 0.084. 2021–2025: +0.58%, p = 0.063, with lower volume (0.89x, p = 0.03). — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)

### Inferences
- The well-known "pre-holiday effect" appears here only before long weekends. Given about 60 tests overall, the long-weekend p-values (0.002–0.016) are suggestive, not conclusive.
- The trades this effect could touch are next-open entries after a signal on the day before a long weekend. Those trades miss that day's up-move and enter after the gap, which point 4 shows is also positive.

### Gaps
- The intraday path of the up-move (late-session drift or not) cannot be measured with daily data.

## 4. Post-holiday reopening: overnight gap and open-to-close

### Takeaway
Gap size grows with time away from the market. A normal weekend gap (mean absolute 0.82%) is about 27% larger than a normal overnight gap (0.65%), p < 0.001. A post-holiday reopening behaves like a weekend: its absolute gap (0.76–0.93%) is larger than a normal overnight gap (p = 0.004 pooled) but no larger than a normal Monday. A long weekend is not reliably bigger than a normal weekend. The signed gap after a long weekend was positive: +0.45–0.50% against +0.16–0.18% after normal weekends, p = 0.058 FULL and 0.007 in 2021–2025, n = 24–32. Open-to-close returns are no different after holidays.

### Cited Findings
FULL sample. Gap = cross-sectional mean of open / previous row's close – 1. |gap| = cross-sectional mean of the absolute gap.

| Reopen type | n | Mean gap | Mean \|gap\| | Open→close | Close→close | % up | Rel. volume |
|---|---|---|---|---|---|---|---|
| Normal overnight (Tue–Fri) | 1,140 | +0.25% | 0.65% | –0.11% | +0.13% | 49.1 | 1.01 |
| Normal weekend (Mon) | 275 | +0.18% | 0.82% | –0.28% | –0.11% | 47.3 | 0.99 |
| After a 1-day mid-week holiday | 43 | +0.20% | 0.76% | –0.36% | –0.16% | 43.6 | 1.04 |
| After a long weekend (Fri or Mon holiday) | 32 | +0.50% | 0.93% | –0.11% | +0.40% | 54.1 | 1.04 |
| After a Muhurat or Saturday special session | 11 | +0.14% | 0.59% | –0.53% | –0.40% | 38.8 | 1.05 |

Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)

- **Gap tests, FULL sample.**
  - |gap| after a long weekend against overnight: +0.28 pp, p = 0.026. Against a normal weekend: +0.11 pp, p = 0.41.
  - |gap| after a mid-week holiday against overnight: +0.11 pp, p = 0.072. Against a normal weekend: p = 0.41.
  - Signed gap after a long weekend against a normal weekend: +0.33 pp, p = 0.058, CI [+0.01, +0.67] pp.
  - Open-to-close after any holiday against a normal weekend: p = 0.80.
  - Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **2021–2025.**
  - |gap|: normal overnight 0.57%, normal weekend 0.74%, after a mid-week holiday 0.71%, after a long weekend 0.71%.
  - Signed gap after a long weekend: +0.45%, against +0.16% after a normal weekend (p = 0.007, n = 24).
  - Relative volume on any post-holiday day: +5.6% against a normal Monday (p = 0.008).
  - Open-to-close: no difference (p = 0.30–0.77).
  - Source: [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **Large holiday gaps.** The biggest all come from 2020 or tariff-period 2025: Tue 7 Apr 2020 |gap| 3.73% (gap +3.62%); Mon 4 May 2020 2.57% (–2.34%); Fri 11 Apr 2025 2.10% (+2.05%); Tue 15 Apr 2025 1.62% (+1.61%); Thu 3 Oct 2024 1.36% (–1.33%). — [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt)
- **Muhurat and abbreviated sessions.** All 8 had a positive EW close-to-close return, from +0.53% to +1.09%, nearly all of it in the gap; open-to-close ranged from –0.18% to +0.32%. Median relative volume was 0.07–0.23x. The next regular session's EW return was mixed, from –1.57% to +1.00%. — [results.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results.txt); [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)

### Inferences
- **Entry at the next open.** The engine always enters at the next row's open. After a holiday or weekend that fill carries a gap about 0.1–0.3 pp larger in absolute terms than a normal overnight gap. With a flat Rs.100 stake and no slippage model, this mainly adds noise, not bias. The exception is long weekends, where the signed gap has been positive, so long entries fill higher.
- **Open-to-close is negative in every category** (on average –0.1% to –0.4%), while gaps are positive. That is a general overnight-up / intraday-down pattern in this cache, not a holiday effect. It matters for the Momentum Loser intraday short, which enters at the open and squares off at the close.
- **Muhurat entries.** A signal on the session before Diwali opens its trade at the Muhurat session's open, a roughly one-hour, thin session.

### Gaps
- Daily bars only. Pre-open auction mechanics, the time of the post-holiday open, and spreads cannot be checked.
- n = 24–43 per holiday category, and Muhurat n = 8.

## 5. Breakouts (close above the prior 20-session high on more than 1.5x the 20-session average volume)

### Takeaway
Breakouts are slightly less frequent in shortened weeks (3.17% against 3.50% of stock-days, t ≈ –1.0, not significant). They follow through no worse: excess return over the following 5 sessions from a next-open entry differs by –0.09 pp, CI [–0.42, +0.25] pp. A holiday inside the holding window does not hurt either. A separate finding: breakouts in this simple definition underperform the equal-weight universe after a next-open entry in every group, by about –0.5% over 5 and 10 sessions.

### Cited Findings
FULL sample. Signal-day classification. "Excess" = the stock's return from next open to close of row +k, minus the EW mean of the same measure across members on that date. Standard errors from a date-clustered bootstrap.

| Group | Stock-days | Signals | Rate | Excess 5-session (t) | Excess 10-session (t) | Raw 5-session | Hit rate (excess 5 > 0) |
|---|---|---|---|---|---|---|---|
| 5-session weeks | 585,165 | 20,456 | 3.50% | –0.50% (–8.8) | –0.51% (–6.6) | –0.23% | 41.1% |
| Shortened weeks | 144,258 | 4,577 | 3.17% | –0.58% (–4.5) | –0.53% (–3.0) | +0.02% | 39.2% |
| Pre-holiday day | 42,526 | 1,370 | 3.22% | –0.42% (–1.8) | –0.24% (–0.7) | +0.14% | 41.8% |
| Post-holiday day | 39,638 | 1,444 | 3.64% | –0.37% (–1.4) | –0.48% (–1.5) | +0.26% | 39.3% |
| Muhurat or abbreviated day | 3,948 | 13 | 0.33% | –1.03% | –1.64% | — | 23% |

Source: [results_brk.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_brk.txt)

- **Shortened weeks minus 5-session weeks** (week-clustered bootstrap, 75 against 237 weeks):
  - Signal rate: –0.32 pp, CI [–0.95, +0.32].
  - Excess 5-session: –0.09 pp, CI [–0.42, +0.25].
  - Excess 10-session: –0.02 pp, CI [–0.47, +0.41].
  - 2021–2025: rate –0.30 pp (t ≈ –1.0); excess 5-session +0.00 pp; excess 10-session –0.03 pp.
  - Source: [results_brk.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_brk.txt)
- **Signals whose next 5 sessions span more than 7 calendar days** (a holiday inside the window, n = 5,199): excess 5-session –0.38% (t = –3.5), against –0.55% (t = –9.6) for windows with no holiday. A holiday inside the window does not hurt follow-through. — [results_brk.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_brk.txt)
- **Muhurat bars inside volume averages.** A Muhurat or abbreviated bar inside the trailing 20-row average lowers that average by about 4.4% (incl/excl ratio 0.956 median) for the next 20 sessions. That alone adds 3.8% more volume-qualified breakouts over those sessions: 3,492 against 3,363 signals, 129 of them extra. The breakout rate in the 20 sessions after an abbreviated session is 4.42%, against 3.33% otherwise. Most of that gap is post-Diwali market behaviour, not the mechanical effect. — [mech.py output](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/mech.py); [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)

### Inferences
- Shortened weeks do not need special treatment for breakout signals in the user's strategies.
- Muhurat bars do need handling, because they distort volume averages and can create spurious up-days or new highs on almost no volume.
- The negative excess return after a next-open entry on simple breakouts fits the overnight-gap pattern in point 4: buyers pay the gap and then suffer the intraday fade. It applies to any breakout rule that uses this engine's fill convention, not only around holidays.

### Gaps
- This is a deliberately simplified breakout definition. It does not include the user's actual Horizontal Breakout v9 filters (2.5x the 50-session volume, uptrend, breadth), and it has no costs.

## 6. Engine and strategy implications: where holidays and shortened weeks matter

### Takeaway
The engine counts rows of each stock's own data, not market sessions or calendar days. This keeps it consistent for MA lengths and max-hold rules. The concrete risks are four:
1. Muhurat and special 1-hour sessions are treated as full bars.
2. Week and month translations assume 5 sessions per week, and "5 sessions = 1 week" fails about 25% of the time.
3. A few labels mix calendar days and sessions.
4. A stock's missing rows stretch its own lookbacks.

GARP's calendar-date rebalance handles holidays correctly. No code resamples to weekly bars or assumes 5 sessions per week.

### Cited Findings
- **Trading calendar.** `run_backtest` builds `all_dates` as the union of every loaded symbol's dates and evaluates a stock only if it has a row that day (`dates[p] == day`). So weekend special sessions and Muhurat sessions are simulated days, and a stock missing a row is skipped. — [backtest.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/backtest.py)
- **Fills.** Entry is always "the next trading day's open" (`future.index[0]`). For intraday strategies, `future = future.iloc[:1]` and the trade squares off at that row's close. A signal on the day before a Muhurat session therefore enters and, for intraday, exits inside the Muhurat session. — [backtest.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/backtest.py)
- **Near-miss scoring.** It uses `NEAR_MISS_HOLDING_DAYS = 20` rows ahead. In the cache, 20 rows span 25–35 calendar days (median 29). — [backtest.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/backtest.py); [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Calendar span of N rows in the cache:**

  | Rows | Calendar days (min / median / max) |
  |---|---|
  | 5 | 5 / 7 / 12 |
  | 20 | 25 / 29 / 35 |
  | 35 | 46 / 51 / 59 |
  | 50 | 70 / 73 / 81 |
  | 90 | 126 / 132 / 138 |
  | 126 | 177 / 185 / 191 |
  | 150 | 212 / 221 / 224 |
  | 252 | 365 / 371 / 375 |

  Only 75.1% of 5-row windows span exactly 7 calendar days; 23.4% span more and 1.5% less (weekend sessions). — [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Weeks converted to sessions at 5 per week in rules and exits:**
  - Cup and handle entry: "at least 7 weeks … (35-session)", and "Bulkowski's 65-week maximum" replaced by a 250-session cap.
  - Cup and handle and horizontal breakout exits: O'Neil's "20%+ within 3 weeks → hold 8 weeks" coded as 15 sessions and 40 sessions.
  - Trendline Bounce: `i2 - i1 >= 25` trading days described as "roughly 5 calendar weeks".
  - Sources: [cup_and_handle_breakout_v1_rules](file:///D:/git-repos/FrontierTradelight/Strategies/Rules_backup/cup_and_handle_breakout_v1_rules_20261006_133828.md); [cup_and_handle_exit_strategy_v1](file:///D:/git-repos/FrontierTradelight/Strategies/ExitRules_backup/cup_and_handle_exit_strategy_v1_exit_rules_20261014_131140.md); [horizontal_breakout_exit_strategy_v1](file:///D:/git-repos/FrontierTradelight/Strategies/ExitRules_backup/horizontal_breakout_exit_strategy_v1_exit_rules_20261006_144834.md); [trendline_bounce_v1_rules](file:///D:/git-repos/FrontierTradelight/Strategies/Rules_backup/trendline_bounce_v1_rules_20261022_093941.md)
- **Session-counted max holds:**
  - 90-session MaxHold (horizontal breakout, mean reversion and cup and handle exits).
  - Cup and handle: 30-session stagnation stop and FailedBreakout window in sessions 11–21.
  - GARP: 150-session MaxHold.
  - All count rows of `future_df`; the GARP exit uses `session_num = i + 1`.
  - Sources: [generated_exit_strategy.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/generated_exit_strategy.py); [mean_reversion_exit_strategy_v1](file:///D:/git-repos/FrontierTradelight/Strategies/ExitRules_backup/mean_reversion_exit_strategy_v1_exit_rules_20260927_155105.md)
- **GARP rebalance (calendar date).**
  - The entry rule is `P < T <= D`, where D is the last row and P the stock's previous row, for T = 15 Jun or 15 Dec. The exit fires on the first row with `d >= Next_Rebalance`.
  - In the cache, 15 Jun 2024 (a Saturday) mapped to Tue 18 Jun 2024, because Mon 17 Jun was a holiday. 15 Dec 2024 and 15 Jun 2025 (Sundays) mapped to the following Mondays.
  - The number of sessions between rebalances is 122–129, well below the 150-session MaxHold.
  - Sources: [generated_rules.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/generated_rules.py); [exit_rules.md](file:///D:/git-repos/FrontierTradelight/Strategies/Default/exit_rules.md); [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Mixed units in the GARP exit's `describe_state`.** `DaysHeld` is a row count, while `DaysToMaxHold` is calendar days to the next rebalance. The latter is not related to the 150-session MaxHold despite its name. `LTCG_Date` is entry + 366 calendar days. — [generated_exit_strategy.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/generated_exit_strategy.py)
- **Warm-up and lookback windows are calendar days, converted to rows.**
  - Backtest `WARMUP_DAYS = 400` gives 269–276 rows before a start date. That covers the 253 rows needed for the 12-1 momentum rank (`lookback=252, skip=21` in `calculate_momentum_ranks`), with a margin of only about 16–23 rows. A stock with more than about 16 missing rows in that year gets no momentum rank early in a backtest.
  - `sell_screener.fetch_history(lookback_days=200)` gives 133–141 rows.
  - `stock_screener.fetch_data(days=400)` gives about 270 rows.
  - Sources: [backtest.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/backtest.py); [nse_utils.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/nse_utils.py); [sell_screener.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/sell_screener.py); [stock_screener.py](file:///D:/git-repos/FrontierTradelight/Strategies/Default/stock_screener.py); [results_eng.txt](file:///C:/Users/apoorv.bedmutha.MEDIASSISTINDIA/AppData/Local/Temp/claude/D--git-repos-FrontierTradelight/3a82b646-45e4-46f0-a082-e044ceba7faa/scratchpad/results_eng.txt)
- **Rules with one-bar comparisons or volume averages:**
  - Horizontal Breakout v9: `Volume[-1] >= 2.5 * MA(Volume, 50)`, `Close > Close[-1]`, "within 2% of 20-day high", and "no more than 25% above 20 trading days ago". Its `Volume[-1] > Volume[-2]` clause was dropped in v7.
  - Trend Continuation and Trendline Bounce use `MA(Volume, 20)` and `MA(Volume * Close, 20)` turnover floors.
  - Sources: [horizontal_breakout v9 rules](file:///D:/git-repos/FrontierTradelight/Strategies/Rules_backup/horizontal_breakout_momentum_o_neil_volume_rules_20261022_095002.md); [trend_continuation rules](file:///D:/git-repos/FrontierTradelight/Strategies/Rules_backup/trend_continuation_pullback_mean_reversion_strategy_rules_20261022_094318.md)
- **No weekly logic.** No code in `backtest.py`, `generated_rules.py`, `generated_exit_strategy.py` or `nse_utils.py` resamples to weekly bars or references weekdays. A grep for `week`, `weekday`, `dayofweek`, `resample` and `holiday` found only rule-text conversions and a comment in `nse_utils.py` about the 14 Sep 2026 holiday used to validate the date fix. — [grep over Strategies/Default and backups](file:///D:/git-repos/FrontierTradelight/Strategies/Default)

### Inferences
- **Muhurat and special live sessions are the main holiday-related engine issue.** There are 8 in the cache, 4 of them on weekdays the exchange treats as holidays. Each is a roughly one-hour bar with 0.07–0.23x normal volume that has closed up every time (EW +0.5–1.1%). The engine treats each one as a full session, which has several effects:
  - **(a) Volume averages.** The bar depresses `MA(Volume, 20)` and `MA(Volume, 50)` and turnover floors for the next 20–50 sessions, by about 4% for 20 rows. That inflates volume-ratio passes (about +4% signals) and Volume_Score ranks.
  - **(b) Muhurat-day signals.** On the Muhurat day itself, `Close > Close[-1]` and new-high checks can pass on almost no volume. Volume rules usually block a signal, but rules without a volume gate would fire.
  - **(c) Intraday entries.** Intraday (MIS) strategies whose signal falls on the pre-Diwali session trade the Muhurat hour. Liquidity and the auction-driven price make that fill unrealistic.
  - **(d) Session counts.** Each such bar counts as a session toward MaxHold, time stops and the near-miss 20-row horizon.

  A simple fix would be to tag rows whose cross-sectional relative volume is below about 0.45x (or a hard-coded Muhurat list), then exclude them from volume averages and from entry and exit fills.
- **"N weeks = 5N sessions" undercounts calendar time.** With about 246–250 sessions per year (about 4.75–4.8 per week), 35 sessions averages about 7.3 calendar weeks (46–59 days), and 40 sessions about 8.3 weeks. "3 weeks = 15 sessions" covers 3 to about 3.4 calendar weeks. This is harmless for pattern rules, but the O'Neil 3-week and 8-week rules are calendar-based in the original source. Session counts make them slightly longer in holiday-heavy months (Oct–Nov, Mar–Apr). Any rule described as "5 days" or "1 week" should state whether it means sessions or calendar days. In this engine it always means rows, and a 5-row window spans more than 7 calendar days 23% of the time.
- **Session-counted rules are internally consistent across holidays.** MA lengths, 252/21 momentum and MaxHold all count rows, so a holiday simply stretches the calendar span: 252 rows is 365–375 days and 150 rows is 212–224 days. GARP's 150-session safety net is never at risk, with at most 129 sessions between rebalances.
- **Per-stock missing rows are a quieter risk than market holidays.** 1.3% of member stock-days have no row. Rolling windows count the stock's own rows, so a stock with gaps has longer lookbacks. Such a stock is also not evaluated on its missing days. Under GARP's `P < T <= D` rule it would signal on its first available row after the rebalance date, which is a late entry, not a missed one.
- **The overnight gap and next-open fill matter more than week length.** Post-weekend and post-holiday gaps average 0.7–0.9% in absolute size, against 0.57–0.65% for normal nights. Long-weekend gaps have been positive. Open-to-close is negative on average. Together these mean next-open entries after long weekends pay up, and same-day open-to-close MIS shorts gain from the general intraday fade.

### Gaps
- `backtest.py` was not run and no strategy-level backtest was split by holiday, as instructed. Effects on actual strategy P&L are inferred, not measured.
- The rules files for all generated strategies were sampled by grep, not read in full. The Momentum Loser intraday rules were read only in part, so I did not confirm how its compiled code handles a Muhurat entry day.
- `historical_universe` snapshots are sparse (13), so point-in-time membership is approximate.
