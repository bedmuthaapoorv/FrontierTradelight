# Frontier TradeLight — AI-Assisted Swing Trading Screener & Backtester

An AI-assisted stock screener and backtester for the Indian market (NSE).
You describe an **entry strategy** and an **exit strategy** in plain
English, Gemini turns each into Python, and the tooling runs them against
real NSE data to produce a live shortlist and/or a historical,
capital-aware backtest. A FastAPI backend + React frontend tie the whole
flow together, alongside a separate real-money Fund Manager view and a
news-driven Event Watcher signal.

All of the project's code lives under [`Strategies/`](Strategies/), with
the Python engine in [`Strategies/Default/`](Strategies/Default/) and the
web UI in [`Strategies/frontend/`](Strategies/frontend/).

## How the strategy engine fits together

```
rules.md       --(Gemini)-->  generated_rules.py        --(used by)-->  stock_screener.py --> data/stock_report.csv
                                                                  \
exit_rules.md  --(Gemini)-->  generated_exit_strategy.py  ---------+-->  backtest.py --> data/backtest_trades.csv
                                                                  /                   --> data/backtest_summary.csv
                                              universe_fetcher.py                    --> data/backtest_portfolio.csv
                                       (Nifty 100 + sector + market-breadth data, cached)
```

All generated/runtime output (reports, caches, logs) is written to
[`Strategies/Default/data/`](Strategies/Default/data/), kept separate from
the project's source files.

- **`rules.md`** — the entry strategy spec: mandatory filters, rejection
  rules, ranking/scoring weights, and desired output columns, in plain
  English. Edit this to change or create a strategy. See
  [`RULES_GUIDE.md`](Strategies/Default/RULES_GUIDE.md) for how to write
  one. The live strategy is versioned by editing this file directly — every
  save auto-backs up the previous version to
  [`Strategies/Rules_backup/`](Strategies/Rules_backup/), browsable/
  restorable from the Rules tab's version history drawer.
- **`generate_screener.py`** — reads `rules.md`, sends it to the Gemini API,
  and writes the resulting
  `evaluate_stock(symbol, df, universe, sector_ranks, market_breadth)`
  function to `generated_rules.py`. Only rewrites `generated_rules.py` —
  safe to run anytime without touching anything else.
- **`generated_rules.py`** — generated code (checked into the repo, but
  regenerated whenever you run `generate_screener.py`). Don't hand-edit
  unless you're okay with it being overwritten.
- **`exit_rules.md`** — the exit strategy spec, in the same plain-English
  style as `rules.md`: when a trade closes (stop-loss, take-profit,
  trailing stop, time-based, or anything else computable from OHLCV). See
  the "Exit strategy" section of
  [`BACKTEST_GUIDE.md`](Strategies/Default/BACKTEST_GUIDE.md) for how to
  write one. Same auto-backup pattern, saved to
  [`Strategies/ExitRules_backup/`](Strategies/ExitRules_backup/).
- **`generate_exit_strategy.py`** — reads `exit_rules.md`, sends it to
  Gemini, and writes the resulting `resolve_exit(...)` function to
  `generated_exit_strategy.py`. Same regenerate-anytime safety as above.
- **`generated_exit_strategy.py`** — generated exit logic, used only by
  `backtest.py`. `backtest.py` itself (not this file) always force-closes
  any still-open trade at the end of the backtest's date range, so a
  regenerated exit strategy can never leave a trade open forever.
- **`universe_fetcher.py`** — downloads the Nifty 100 constituent list from
  NSE, pulls price history via `jugaad-data`, ranks stocks by sector
  performance, and returns the top N stocks per sector. Results are cached
  in `universe_cache.json` for 1 day.
- **`nse_utils.py`** — shared NSE data-fetching helpers (with retry/backoff
  and rate-limit-conscious staggering), plus `calculate_sector_strength`
  and `calculate_market_breadth`, both used by the live screener and the
  backtester.
- **`stock_screener.py`** — the live entry point. Builds the stock universe,
  fetches recent daily price data per stock, computes sector-strength ranks
  and market breadth, runs `generated_rules.py`'s `evaluate_stock` on each
  stock, and writes the ranked results to `stock_report.csv`.
- **`backtest.py`** — a standalone backtesting module (no dependency on
  `stock_screener.py` or the API/UI layer, so it can be lifted into its own
  service later). Replays `generated_rules.py` + `generated_exit_strategy.py`
  over a historical date range with no look-ahead, then runs a second pass
  that simulates a real, capital-constrained portfolio (starting capital, a
  fixed number of concurrent position slots — 6 by default in the UI,
  compounding as trades close) to answer "would this strategy have actually
  grown my money," not just "did individual signals tend to work." When run
  over the exact benchmark date range (2021-01-01 to 2026-01-01), CAGR /
  Max Drawdown / Composite Score get recorded onto the Stats tab's
  leaderboard automatically. See
  [`BACKTEST_GUIDE.md`](Strategies/Default/BACKTEST_GUIDE.md) for full
  details on both layers.

## The app

The primary interface is a **FastAPI backend + React (Vite/TypeScript)
frontend** (`Strategies/Default/api/` and `Strategies/frontend/`). A legacy
Streamlit UI (`Strategies/Default/app.py`) still exists but is being phased
out.

The main tabbed app has 9 tabs:

- **Rules** — view/edit `rules.md`, save (auto-backs up the previous
  version), and restore any previous version from a searchable drawer that
  shows which saved version is LATEST and which one earned the best
  recorded Composite Score.
- **Run** — buttons to run `generate_screener.py` (rebuild
  `generated_rules.py` from `rules.md`) and `stock_screener.py` (fetch
  data, score stocks, write `stock_report.csv`), each with streamed console
  output.
- **Results** — browse `stock_report.csv` as a sortable/filterable table,
  with a toggle to show only stocks that passed all mandatory filters.
- **Sell** — track your actual open positions (`holdings.csv`) and check
  them against the live exit strategy's signals.
- **Backtest** — edit/save/generate `exit_rules.md`, pick a date range,
  starting capital, and max concurrent positions (defaults to 6), run a
  backtest with a live log and a stop button, and see the score-bucketed
  trade summary plus the real portfolio result (final equity, total
  return, CAGR, Max Drawdown, Composite Score, equity curve).
- **Deep Dive** — drill into a single stock's indicators and rule-by-rule
  pass/fail breakdown.
- **Missed Opportunities** — near-misses from the last backtest (stocks
  that failed exactly one mandatory rule), grouped by blocking rule with
  the forward return they would have earned, so you can see which filters
  are worth loosening.
- **Stats** — a leaderboard of every strategy ever benchmarked (CAGR, Max
  Drawdown, Composite Score, trade count), with one-click switching between
  recorded strategy versions.
- **Event Watcher** — a separate, entirely news-driven signal: scans PIB
  (Press Information Bureau) Ministry of Defence press releases for naval
  commissioning/induction announcements naming a watchlisted shipbuilder
  (e.g. Cochin Shipyard, Mazagon Dock, GRSE), since a real historical rally
  in one of these stocks lined up exactly with such an announcement. Fully
  separate from the OHLCV-based rules.md screener/backtester — it never
  feeds a strategy or the backtester, only surfaces a manual candidate.
  Supports live polling, a real historical lookup (via the underlying
  feed's own git history, for dates outside its ~8-day live window), and a
  slide-over editor for the matching keywords/watchlist/vessel-class
  aliases it uses. See
  [`event_watcher_utils.py`](Strategies/Default/event_watcher_utils.py) for
  the full reasoning and data-source caveats.

**Fund Manager** (`/fund-manager`) is a separate standalone view — the
real-money fund's own NAV/units accounting, entirely independent of the
backtest engine (which is a research tool, never a source of truth for
real fund numbers). It has three tabs:

- **Overview** — AUM, current NAV, per-investor units/value/return, capital
  event history (deposits/withdrawals, each removable), and a "Send
  update" action that opens a Gmail compose draft with the investor's
  current numbers plus optional notes.
- **Holdings** — the fund's actual positions and cash balance (distinct
  from the personal Sell tab's `holdings.csv`).
- **Documents** — storage for fund paperwork (agreements, investor
  statements, compliance filings, tax records) with metadata, entirely
  separate from the NAV/units accounting.

## Setup

Note: This project works best with python@3.12 and Node 18+.

1. **Install Python dependencies:**

   ```bash
   cd Strategies/Default
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies:**

   ```bash
   cd Strategies/frontend
   npm install
   ```

   and the dev-orchestration dependency one level up:

   ```bash
   cd Strategies
   npm install
   ```

3. **Configure your Gemini API key** (only needed for `generate_screener.py`
   / `generate_exit_strategy.py`):

   ```bash
   cd Strategies/Default
   cp .env.template .env
   ```

   ```
   GEMINI_API_KEY=your_actual_key_here
   ```

## Usage

### Option A: Full app (recommended)

```bash
cd Strategies
npm run dev
```

Starts the FastAPI backend (`http://localhost:8000`) and the Vite/React
frontend (`http://localhost:5173`) together. Open the frontend URL for the
full tabbed app described above.

Prebuilt launchers that do the same thing without a terminal (resolve the
real Python/Node interpreters and avoid leaving orphaned child processes on
close) are also available: `Strategies/Start FrontierTradeLight.command`
(Mac), `Strategies/Start FrontierTradeLight.bat` /
`Strategies/Start FrontierTradeLight.ps1` (Windows).

### Option B: Legacy Streamlit UI

```bash
cd Strategies/Default
streamlit run app.py
```

A subset of the functionality (Rules, Run, Results, Backtest) in the
original single-process UI. Being phased out in favor of the React app.

### Option C: Command line

**1. Define or edit your entry strategy** in `rules.md`, and your exit
strategy in `exit_rules.md`.

**2. Generate the logic** (only needed after editing the corresponding
`.md` file):

```bash
python generate_screener.py        # rules.md -> generated_rules.py
python generate_exit_strategy.py   # exit_rules.md -> generated_exit_strategy.py
```

**3a. Run the live screener:**

```bash
python stock_screener.py
```

This fetches (or loads cached) top stocks per sector, downloads recent
daily price history, computes sector-strength ranks and market breadth,
runs `evaluate_stock` on every stock, prints the top 20 by `ClosenessScore`,
and saves the full ranked results to `stock_report.csv`.

**3b. Or run a backtest:**

```bash
python backtest.py --start 2021-01-01 --end 2026-01-01 \
    --initial-capital 100000 --max-positions 6
```

This replays the strategy over the date range with no look-ahead, resolves
every signal's entry/exit independently, then simulates a real portfolio on
top of those trades. Writes `data/backtest_trades.csv`,
`data/backtest_summary.csv`, and `data/backtest_portfolio.csv`, and prints a
portfolio summary (final equity, total return, funded vs.
skipped-for-lack-of-capital trade counts). Running over the exact benchmark
range (2021-01-01 to 2026-01-01) also upserts CAGR/Max Drawdown/Composite
Score onto the Stats leaderboard when done through the app/API (not the
bare CLI, which only writes the CSVs).

## Output

All generated output lives in
[`Strategies/Default/data/`](Strategies/Default/data/):

- **`stock_report.csv`** (live screener) — one row per evaluated stock:
  `Symbol`, `Passed` (bool), `ClosenessScore` (0–100), `FailedRules`, plus
  every metric captured in `Details` (RSI, volumes, sector rank, etc.).
- **`backtest_trades.csv`** (backtest) — one row per simulated trade:
  entry/exit dates and prices, `ExitReason`, `ClosenessScore`, `ProfitRs`,
  and whether the portfolio simulation actually funded it (`Funded`,
  `AllocatedCapital`).
- **`backtest_summary.csv`** (backtest) — trades bucketed by
  `ClosenessScore`, with win rate and mean/median/total profit per bucket.
- **`backtest_portfolio.csv`** (backtest) — the portfolio's equity curve
  over time.
- **`near_misses.csv`** (backtest) — stocks that failed exactly one rule,
  used by the Missed Opportunities tab.
- **`strategy_stats.csv`** — the Stats tab's leaderboard: one row per
  benchmarked strategy (+ exit strategy) version, with CAGR, Max Drawdown,
  Composite Score, and trade count.
- **`holdings.csv`** / **`sell_report.csv`** (Sell tab) — your tracked
  positions and the latest exit-signal check against them.
- **`fund/`** — the Fund Manager's own records (investors, capital events,
  NAV history, fund holdings, cash), entirely separate from the backtest
  engine's data above.
- **`event_watcher/`** — Event Watcher's cached matches, last-checked
  metadata, and the editable keyword/watchlist/vessel-class-alias config.

## Documentation

- [`Strategies/Default/RULES_GUIDE.md`](Strategies/Default/RULES_GUIDE.md) —
  how to write `rules.md` (entry strategy).
- [`Strategies/Default/BACKTEST_GUIDE.md`](Strategies/Default/BACKTEST_GUIDE.md) —
  how the backtester and portfolio simulation work, how to write
  `exit_rules.md`, and how to read the output.
- [`Strategies/Default/rules.md`](Strategies/Default/rules.md) — the
  current live entry strategy (worked example).
- [`Strategies/Default/exit_rules.md`](Strategies/Default/exit_rules.md) —
  the current live exit strategy (worked example).
- [`Strategies/Default/PLUGIN_GUIDE.md`](Strategies/Default/PLUGIN_GUIDE.md) —
  how to add a new tab to the legacy Streamlit UI as a self-contained
  plugin.
- Prior strategy versions — auto-saved whenever you save a changed
  `rules.md` (restorable from the Rules tab) or `exit_rules.md`
  (restorable from the Backtest tab), browsable in
  [`Strategies/Rules_backup/`](Strategies/Rules_backup/) and
  [`Strategies/ExitRules_backup/`](Strategies/ExitRules_backup/).

## Notes & caveats

- `data/universe_cache.json` and `data/backtest_cache/` are generated/cached
  data, not tracked in git. `universe_cache.json` expires after 1 day; the
  backtest's per-symbol history cache never expires (historical ranges are
  immutable once in the past) — delete `data/backtest_cache/` to force a
  refetch.
- `jugaad-data` pulls from NSE's historical (EOD) archives, which lag live
  quotes by 1+ trading session — expect some drift if you compare against
  a live/real-time source. This is inherent to any EOD data source, not a
  calculation bug.
- Because `generated_rules.py` and `generated_exit_strategy.py` are
  AI-generated, always review the diff after regenerating before trusting
  or committing it — treat the AI output as a draft, not gospel. Watch in
  particular for hardcoded `pandas_ta` column names (they vary by version)
  and swallowed exception messages — both have shown up in past
  generations.
- Backtest "total return" is cumulative over the whole date range, not
  annualized — check the accompanying CAGR figure before judging a result
  as strong or weak.
- The backtest uses *today's* Nifty 100 constituent list applied
  retroactively (survivorship bias), and doesn't model slippage or
  brokerage/STT costs.
- Event Watcher's live feed is sourced from an unofficial, single-maintainer
  community scrape of PIB (not a government source) — it could go stale or
  disappear without warning; treat "no matches" and "feed unreachable" as
  genuinely different outcomes.
- Whichever entry strategy (`rules.md`) and exit strategy (`exit_rules.md`)
  are live at any given time aren't guaranteed to be the pair they were
  originally designed/benchmarked together as — check both files' metadata
  headers before treating a Stats tab number as representative of a
  specific, intentional entry+exit combination.
- Never commit your real `.env` file or API key.
