# Stock Selection Rules

## Strategy Metadata

Strategy Name: Regime Router v1
Market: India (NSE/BSE)
Timeframe: Daily
Holding Period: Varies by active sub-strategy

---

## Strategy Rationale

Real discretionary and systematic traders don't run one strategy in every
market condition - they favor momentum/breakout setups when the broader
market is strong and participation is broad, and lean on mean-reversion or
more selective trend-pullback setups when it isn't. This router expresses
that idea using the only market-wide, day-level signal this pipeline has:
MarketBreadth (% of the whole universe trading above its own 50-day
average).

The three referenced strategies below were each individually backtested
over 2021-01-01 to 2026-01-01 and recorded in the Stats tab:
- Breakout Momentum v6: CAGR +10.03%/yr, MaxDD -18.1%, Composite 0.55
- Trendline Bounce Confirmation v3: CAGR +10.66%/yr, MaxDD -10.2%, Composite 1.81
- Oversold Mean Reversion: CAGR +3.38%/yr, MaxDD -7.2%, Composite 0.98

Trendline had the best risk-adjusted return alone, but Breakout's edge
comes specifically from strong, broad-based up markets while Mean
Reversion's small, low-drawdown edge tends to show up when the market is
weak/choppy rather than trending - a plausible case that routing between
them by regime instead of running any one alone could reduce Breakout's
large drawdown (which likely came from being active in weak markets too)
without giving up its upside in genuinely strong markets.

MarketBreadth thresholds below are based on the historical distribution
already documented in Breakout Momentum v6's own rules.md (mean ~57,
median ~58, 10th percentile ~28) - 60 marks meaningfully-above-average
breadth, 40 marks meaningfully-below-average.

---

## Referenced Strategies

Each entry is `Key: path` where path is an existing, already-saved rules.md
backup - this router calls into that file's own Mandatory Filters/Ranking
Rules, it does not redefine them. Paths are relative to Default/ (the
working directory generate_screener.py runs from).

- Breakout: ../Rules_backup/breakout_momentum_v6_rules_20260828_113724.md
- Trendline: ../Rules_backup/trendline_bounce_confirmation_v3_rules.md
- MeanReversion: ../Rules_backup/oversold_mean_reversion_rules.md

---

## Routing Rules

Evaluated ONCE PER TRADING DAY (not per stock) using MarketBreadth - the
only signal available uniformly to every stock on a given day (no Nifty/
index data exists in this pipeline). Checked top to bottom; the first
matching route wins and that strategy screens every stock for the whole
day. If nothing matches, the Default Strategy is used.

### Route 1: Strong breadth -> Breakout
Condition: MarketBreadth >= 60

### Route 2: Weak breadth -> Mean Reversion
Condition: MarketBreadth < 40

### Default Strategy: Trendline
