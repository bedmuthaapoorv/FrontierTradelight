# KEC in "Momentum Loser Intraday Short v1" top 3: local code-and-data diagnosis

Sources (all local, read-only): rules file `Strategies/Rules_backup/momentum_loser_intraday_short_v1_rules_20261022_094804.md`; exit rules `Strategies/ExitRules_backup/mis_short_stop_and_square_off_v1_exit_rules_20261029_112718.md`; `Strategies/Default/nse_utils.py` (`calculate_momentum_ranks`, `calculate_market_breadth`, `calculate_sector_strength`); `common_methods/avg_traded_value.py`; `data/stock_report.csv` (mtime 2026-10-26 15:41); `data/market_breadth.json`; `data/universe_cache.json`; `data/backtest_cache/<SYM>_2024-11-27_2026-10-28.csv` (fresh, ends 2026-10-28; the 2019-2026-01-01 files are stale and unused). Scripts: scratchpad `load.py`, `a1.py`, `a2.py`, `a3.py` (nothing written into the repo). Where I say "recomputed" I truncated each symbol's history at the signal day and called the repo's own `calculate_momentum_ranks`, `calculate_market_breadth` and `avg_traded_value`, plus pandas_ta ATR(14). Active-strategy caveat: `generated_rules.py` and `exit_rules.md` currently hold a different strategy (a Friday-signal / Monday-gap-fade one), so I implemented the momentum-loser rules from the rules .md. Rules in the .md are fully specified, so the recompute is faithful.

## Q1. What were the last sessions, and what did KEC do?

### Takeaway
Latest data row is Wed 2026-10-28 (409 of 410 loaded symbols end there). The last two sessions are Tue 10-27 and Wed 10-28. KEC rose more than 1.5% close-to-close only on 10-28 (+1.96%) and on 10-26 (+2.76%); on 10-27 it fell 1.53%. So "up more than 1.5% on both days" fits the pair (10-26, 10-28) or the signal-day moves, not the pair (10-27, 10-28). The one clear MIS short loss is entry 10-28.

### Cited Findings
KEC daily bars, `KEC_2024-11-27_2026-10-28.csv`. Dates are real IST dates (the cache applies the +1-day fix in `fetch_stock_history`; 10-20 is absent, a market holiday). Gap, c2c and o2c are on the entry day; the short's gross P&L is the negative of o2c unless the stop is hit.

| Session | Open | High | Low | Close | Prior close | Gap % | C2C % | O2C % | Volume |
|---|---|---|---|---|---|---|---|---|---|
| Fri 10-23 | 331.15 | 331.95 | 317.25 | 327.75 | 331.95 | -0.24 | -1.27 | -1.03 | 1.62M |
| Mon 10-26 | 339.00 | 348.25 | 328.60 | 336.80 | 327.75 | +3.43 | +2.76 | -0.65 | 6.19M (3.3x 20d avg) |
| Tue 10-27 | 334.00 | 341.60 | 330.25 | 331.65 | 336.80 | -0.83 | -1.53 | -0.70 | 1.07M |
| Wed 10-28 | 331.05 | 340.95 | 329.45 | 338.15 | 331.65 | -0.18 | +1.96 | +2.14 | 0.90M |

- Entry 10-26 (signal 10-23): KEC gapped up 3.43% and rallied 2.76% c2c, but opened near the high and sold off, so o2c was -0.65% (short gains +0.65%). Stop was 339.00+12.22 = 351.22 and the high was 348.25, so not hit. KEC was rank 4 that day (`stock_report.csv` and recompute), not top 3.
- Entry 10-27 (signal 10-26): KEC rank 2. Short gross +0.70% (o2c -0.70%). Stop 346.81 vs high 341.60, not hit. KEC was a winner while the list as a whole lost (see Q3).
- Entry 10-28 (signal 10-27): KEC rank 2. Entry 331.05, close 338.15, o2c +2.14%, short gross -2.14%. Stop 331.05+12.71 = 343.76 vs high 340.95, NOT hit, so the loss is the full -2.14% (no stop protection; stop is 1x ATR = 3.8% wide).
- Today (10-29) is not in the data (cache ends 10-28). I did not fetch it.

### Inferences
- Probably the user's perception comes from the signal-day price: the screen viewed on 10-27 shows KEC 336.80 after a +2.76% day, the screen viewed on 10-28 shows 331.65, and on 10-28 the stock then rose +1.96%. Please confirm which two sessions the user means.
- Only 10-28 was a real KEC loss in repo data. A 1.96% close-to-close rise needs no conflict with the rules: the rules never look at direction around the signal.

### Gaps
- Could not verify which two sessions the user means; no data for 10-29.

## Q2. Rule inputs and Rank Score for KEC

### Takeaway
KEC passes every rule with wide margins and ranks 2nd of 13-14 passers on the 10-26 and 10-27 signal days (4th on 10-22 and 10-23 signals). The rank score is high because (a) momentum rank is bottom 1% and (b) liquidity (Rs 78 Cr) adds ~23 points. Top 3 = top 3 of only 13-14 names.

### Cited Findings
Recomputed with repo functions (universe 409 symbols with >=253 rows of 410 loaded; `stock_report.csv` used 426 symbols and is slightly different, see gaps).

| Signal day | momentum_rank | Close | SMA200 | 12M ret | 20d avg TV (Rs Cr) | ATR(14) | Rank Score | KEC rank / passers |
|---|---|---|---|---|---|---|---|---|
| 10-22 | 1.00 | 331.95 | 520.38 | -61.12% | 69.44 | 12.03 | 76.80 | 4 / 15 |
| 10-23 | 1.00 (report: 0.985) | 327.75 | 518.35 | -61.81% | 69.01 | 12.22 | 76.67 (report: 76.91) | 4 / 15 |
| 10-26 | 0.249 | 336.80 | 516.35 | -60.71% | 77.64 | 12.81 | 89.80 | 2 / 14 |
| 10-27 | 0.748 | 331.65 | 514.32 | -61.10% | 78.67 | 12.71 | 83.13 | 2 / 14 |

- Rank score arithmetic, 10-26: momentum_score = 100 - 0.249*20 = 95.01; liquidity_score = 77.64; 0.7*95.01 + 0.3*77.64 = 66.51 + 23.29 = 89.80. 10-27: momentum_score = 85.04, liquidity 78.67, 59.53 + 23.60 = 83.13.
- All four rules: Rule 1 (rank <= 5) pass with rank <1; Rule 2 close is 36% below SMA200 (336.80 vs 516.35) and 12M return -60.7%; Rule 4 Rs 77.6 Cr vs 25 Cr minimum; Rule 3 (breadth) never fails a stock.
- Top 3 on each day (recomputed). 10-26: KPITTECH 93.02, KEC 89.80, FIRSTCRY 86.01. 10-27: KPITTECH 96.51, KEC 83.13, RPOWER 77.90.
- 12-1 window for KEC on the 10-27 signal: 2025-10-15 close 852.5 to 2026-09-23 close 402.4 = -52.8% (`calculate_momentum_ranks`: `close.iloc[-1-252]` to `close.iloc[-1-21]`). KEC fell from about 857 to about 392 within that window; bottom ~1%.
- Quantization: with ~409 ranked names, 1 position = 0.244 percentile points, so bottom 5% is ~12-20 stocks; only 13-15 pass all rules. "Top 3" = top 3 of 13-14.
- The liquidity term gives KEC 23 of its 83-90 points regardless of direction (rules file: `liquidity_score = min(100, atv/1e9*100)`, weight 0.3).

### Inferences
- The rank score is not noisy or buggy for KEC; it is a deterministic function of long-run loser status plus liquidity. With only 13-14 passers and score spread (e.g. 10-27: 96.5, 83.1, 77.9, 77.7, 66.2, 65.1, 61.6, 47.6...) a name with Rs 70-80 Cr turnover and a bottom-1% rank lands in the top 3 most days.
- KEC appears every day: 117 appearances in the 220 backtestable signal days (since 2026-08-27 it has been in the list nearly daily; top 3 on 29 of them).

### Gaps
- `stock_report.csv` was generated 2026-10-26 15:41 on data ending 10-23 (its Current Price for KEC is 327.75, the 10-23 close; `market_breadth.json` as_of 2026-10-26T15:40:59, breadth 11.7 over 426 stocks). So it holds the momentum-loser output but for the 10-23 signal (KEC rank 4 of 16 flagged Passed, score 76.91). I recomputed 10-26 and 10-27 myself. Differences vs the report (momentum rank 1.00 vs 0.985, score 76.67 vs 76.91) come from the 409 vs 426 symbol sets (universe_cache has 430 symbols, 410 have a fresh cache file, 409 have >=253 rows; the report covered 426) and one-position rank steps.
- Possible one-day staleness risk: a screener run at 15:41 on 10-26 (before the 10-26 bar was available from jugaad/NSE) used the 10-23 close, i.e. a 2-trading-day-old signal for a 10-27 entry. I cannot verify what was used for the 10-27/10-28 runs; only the 10-26 15:41 run is visible.

## Q3. Who else was in the top 3 / top 10, and was the whole list up?

### Takeaway
It was the whole list and the market. On both entry days most passers rose and the universe rallied; KEC was actually better than the list on 10-27. The top 3 lost on 10-28 mostly because of KPITTECH (+5.35% o2c, stop hit).

### Cited Findings
Entry-day results for passers (recomputed; short P&L includes the 1x ATR stop, pessimistic = stop if high >= stop):

| Entry day | Signal | Passers | List mean o2c | Passers up o2c | List short win rate | Mean short P&L | Top 3 (o2c, P&L) | Universe mean o2c (409 stocks) | Breadth at signal |
|---|---|---|---|---|---|---|---|---|---|
| 10-26 | 10-23 | 15 | +2.03% | 12/15 | 20% | -1.72% | FIRSTCRY +0.18, KPITTECH +2.40, RPOWER +0.85 (P&L -0.18/-2.40/-0.85; KEC rank 4 -0.65 -> +0.65) | +1.36% | 11.25 |
| 10-27 | 10-26 | 14 | +1.07% | 9/14 | 36% | -1.14% | KPITTECH -0.38 (+0.38), KEC -0.70 (+0.70), FIRSTCRY +0.66 (-0.66) | +1.43% | 14.18 |
| 10-28 | 10-27 | 14 | +1.77% | 11/14 | 21% | -1.58% | KPITTECH +5.35 (stop hit, -3.50), KEC +2.14 (-2.14), RPOWER +2.41 (-2.41) | +0.37% | 19.80 |

- 10-28 stops hit (high >= entry+ATR): KPITTECH, TRENT, RVNL, SYNGENE (+6.44% o2c, +5.41% gap), IRCON. 10-27 stops hit: RPOWER, WHIRLPOOL, GODFRYPHLP.
- Market Breadth (percent above own 50DMA, recomputed with the repo function): 11.25 (10-23), 14.18 (10-26), 19.80 (10-27). The report file shows 11.74 on 426 stocks for 10-23. Breadth is informational only and was extremely weak (an oversold market), so the entry days were a relief bounce from the 10-21..10-23 selloff (universe mean o2c -1.80, -0.25, -2.14 on 10-21/22/23).
- The list was a strong short on 10-21 to 10-23 (vectorised mean short P&L by signal day: 10-19 +1.74%, 10-21 +0.58%, 10-22 +3.72%) and then lost three straight entry days (10-26, 10-27, 10-28) as the market bounced.
- KEC's sector Construction has SectorRank 17 of 20 (average 30-day return rank), i.e. a weak sector (unused by the rules; `calculate_sector_strength` computed on the 410 symbols).

### Inferences
- A rally in the whole list, driven by a broad market bounce from a very oversold state (breadth 11-20), explains most of the loss; this is market beta, not a KEC-specific failure.
- The short list is not hedged against a market rally (no index/breadth gate by design: "NO market-breadth gate" in the rules).

### Gaps
- No index/Nifty data available, so market return is proxied by the mean o2c of the loaded 409-stock universe (survivorship: today's constituents).
- No news/earnings calendar for KEC; the 16.5M-share day on 10-09 (14x volume, +5.79%) and the 6.19M day on 10-26 (3.3x volume, delivery 16.9%) could be news or block deals, unverifiable locally.

## Q4. Structural gaps in the rules (verified against the rules file and `nse_utils.py`)

### Takeaway
KEC is not a stock that had been rallying for weeks: it is a deep downtrender (-14% over 21 days, -18% on 10-27, 6% above its 52-week low) that bounced for a day or two. The rules are blind to the last 21 days, to gaps, volume spikes, sectors and market regime by design, but KEC's signals do not show that a stock "rallying through the filters" occurred. The real gap is that nothing screens the 1-3 day bounce, and adding such a filter shows no edge in the repo's own base rates.

### Cited Findings
KEC at each signal day (`a2.py`, computed from `KEC_2024-11-27_2026-10-28.csv`):

| Signal day | 1d | 5d | 10d | 21d | 63d | SMA20 | SMA50 | SMA200 | 52w low (intraday) | Dist. above 52w low | Volume vs prior 20d avg |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 10-26 | +2.76% | -4.39% | -8.94% | -13.98% | -28.79% | 361.3 | 394.4 | 516.3 | 317.2 | +6.2% | 3.27x |
| 10-27 | -1.53% | -3.46% | -8.50% | -17.58% | -29.42% | 358.1 | 392.2 | 514.3 | 317.2 | +4.5% | 0.50x |
| 10-28 | +1.96% | +1.24% | -5.98% | -14.48% | -27.22% | 355.2 | 390.1 | 512.3 | 317.2 | +6.6% | 0.41x |

- KEC closed below its SMA20, SMA50 and SMA200 at every signal day shown (e.g. 10-27: 331.65 vs 358.1/392.2/514.3). 52w low (close) 327.75 on 10-23; intraday low 317.25 on 10-23. So KEC set a fresh 52-week low on 10-23 and then bounced 3-6%.
- 12-1 skip of the most recent 21 days (`calculate_momentum_ranks(lookback=252, skip=21)`): a stock that rallied hard in the last month could still rank in the bottom 5%. For KEC it does not apply: the skipped month is itself -14% to -18%. The 12-1 rank mostly reflects the Oct-2025 to Sep-2026 collapse (857 to ~392).
- Rules have no check on: last 1-10 day price action, gap, news/earnings, relative volume, sector strength (SectorRank is passed but unused), market regime (breadth explicitly informational). Verified by reading the Mandatory Filters (Rules 1-4) and Ranking Rules in the rules file; the 6.19M-volume +2.76% bounce day on 10-26 was invisible to the rules.
- Rank-score structure: liquidity gives up to 30 points regardless of direction (KEC gets 23 of 83-90). Momentum score range is 0-100 over only the bottom 5% of ranks, so it is coarse.
- "Top 3" because few stocks pass: 13-15 passers per day (mean 13.7, min 10, max 17 over 220 days), so top 3 = the best ~20%.
- Exit rules: stop = entry + 1.0 x ATR(14) (KEC: ~3.8%), no profit target, squared off at close. On 10-28 the loss -2.14% was inside the stop.

### Inferences
- For KEC the "rallying through the filters" story does not hold on multi-week data. The accurate story is a persistent loser at its 52-week low that is a frequent pick (117 appearances) and bounced with the market.
- The signal-day move is visible only in the last bar: on the 10-26 signal KEC had just jumped +2.76% on 3.3x volume, and the strategy still scored it 2nd.

### Gaps
- Entry-day price/volume on 10-29 not available.

## Q5. Base rates and what the data says about two losing days

### Takeaway
Over the repo's 220 backtestable signal days (about 2025-11 to 2026-10, 3,023 pass-events) a passer rises open-to-close 41.2% of the time, wins as a short 57.8% and averages +0.17% gross per trade, matching the ~59% / +0.22% claimed validation. Two losing days for one name is ordinary; three straight losing list days was ~8.6% likely.

### Cited Findings
(`a3.py`, vectorised on an aligned panel; same rules and 1x ATR stop; trades from signal day t to entry t+1; today's constituents, so survivorship caveat; last-day numbers differ slightly from the exact repo-function recompute above, 13 vs 14 passers on some days.)

- All passers: n=3,023, stock rose o2c 41.2%, c2c up 45.3%, short win 57.8%, mean P&L +0.169%, stop hit 11.4%.
- Top 3 by score: n=659, rose 37.5%, win 61.0%, mean +0.283%, stop hit 10.2%. Rank > 3: win 56.9%, mean +0.137%. Top 10: win 58.8%, +0.206%. So Rank Score weakly helps.
- KEC itself: 117 appearances, stock rose o2c 33.3%, short win 65.8%, mean +0.566%, stop hit 8.5%; as top 3 (29 days) win 58.6%, mean +0.225%. KEC lost on 34.2% of its appearances; consecutive-appearance double losses occurred 8.5% of the time.
- Passers rising >= 1.5% c2c on the entry day: 21.3%; o2c >= 1.5%: 18.8%; o2c >= 2%: 14.3%.
- List-level: list mean short P&L < 0 on 44.5% of days; two such days in a row 20.9%; three in a row 8.6% (last three entry days 10-26/10-27/10-28 were all negative: -1.14%/-1.58%/-1.72% in the exact recompute). Top-3 mean P&L < 0 on 41.8% of days; two in a row 17.7%.
- Universe-wide mean o2c is -0.09% over the window, positive on 45.9% of days.
- Conditional splits (signal-day state, all passers): ret1 >= +2%: win 58.3%, mean +0.146% (n=496); ret1 < 0: 57.5%, +0.209%; ret5 > 0: 56.3%, +0.092%; ret5 <= 0: 59.0%, +0.227%; close > SMA20: 56.5%, +0.148%; close <= SMA20: 58.8%, +0.184%; signal volume >= 3x: 58.4%, +0.391% (n=178); within 8% of 52w low: 59.4%, +0.209%; farther: 56.8%, +0.143%.
- Entry gap (unknowable at signal time): gap >= +1% gives win 51.2%, mean -0.357%.

### Inferences
- The strategy is behaving at its stated base rate: roughly 4 in 10 passers rise o2c on a given day, and a market bounce day makes most of the list lose together. Two losing sessions for one name, or a run of three bad list days, are within normal variance; it is not evidence of a bug.
- The candidate filters (recent 1-day rally, positive 5-day return, above SMA20, near 52w low) show only small, within-noise differences in win rate (about 1-3 points) in this 220-day sample, consistent with the rules file's warning not to add untested filters. A 5-day return > 0 filter would cost mean P&L rather than help, and a ret1 >= 2% filter would have removed KEC only on the 10-26 signal.

### Gaps
- Sample is one year of today's constituents, not the point-in-time Nifty 500, Dec 2020 to Dec 2025 validation; no costs, no slippage; stop-before-target path order unknowable with daily bars.
- 410 of 430 universe symbols had a fresh-cache file (20 missing), and the vectorised panel and the exact recompute differ slightly (counts 13 vs 14 passers on 10-26/10-27, mean P&L within about 0.1 pt).
- I did not run any web search (not requested) so no external news for KEC.
