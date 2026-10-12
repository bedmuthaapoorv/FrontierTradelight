# Frontier TradeLight

**An AI-assisted swing-trading screener and backtester for Indian (NSE) and
US (S&P 500) stocks.**

You write an **entry strategy** and an **exit strategy** in plain English.
Gemini compiles each one into Python. The engine then runs that code against
real market data in two ways: as a live screener that produces a ranked
shortlist, and as a historical, capital-constrained backtest. A FastAPI
backend and a React frontend tie the workflow together. The app also
includes a news-driven Event Watcher signal and a separate Fund Manager
view for real-money NAV/units accounting.

- **Architecture diagram:** [Eraser workspace](https://app.eraser.io/workspace/v1y7m3ZvWhMKdUCjvG4m)
- **License:** [Apache 2.0](LICENSE)

---

## Contents

- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Strategy engine](#strategy-engine)
- [The app](#the-app)
- [Setup](#setup)
- [Usage](#usage)
- [Data files](#data-files)
- [Further documentation](#further-documentation)
- [Notes and caveats](#notes-and-caveats)

---

## Architecture

The full system diagram is on
[Eraser](https://app.eraser.io/workspace/v1y7m3ZvWhMKdUCjvG4m). The core
strategy pipeline (shown for the India engine; the US engine mirrors it):

```
rules.md       --(Gemini)--> generated_rules.py ----------+--> stock_screener.py --> data/stock_report.csv
                generate_screener.py                       |
                                                           +--> backtest.py ------> data/backtest_trades.csv
exit_rules.md  --(Gemini)--> generated_exit_strategy.py ---+         ^              data/backtest_summary.csv
                generate_exit_strategy.py                  |         |              data/backtest_portfolio.csv
                                                           |         |              data/near_misses.csv
                                                           +--> sell_screener.py -> data/sell_report.csv
                                                                     |
        historical_universe.py (point-in-time Nifty 500) ------------+
        nifty_utils.py (Nifty 50 benchmark), inflation_utils.py (World Bank CPI)
```

- **Two independent backends, one frontend.** `Strategies/Default/` is the
  India engine (port 8000). `Strategies/US/` is a separate copy of the
  engine for S&P 500 stocks (port 8001). The React frontend has an
  **India / US** switch in its header that picks which backend it talks to.
- **Rules are plain-English Markdown.** `rules.md` and `exit_rules.md` are
  the specs. The `generate_*.py` scripts send them to Gemini and write the
  generated Python. Every save of a changed spec is auto-backed up, so any
  past version can be restored.
- **The backtester is standalone.** `backtest.py` has no dependency on the
  screener or the API layer. The API launches it as a subprocess and tracks
  its progress through `backtest_runner.py`.
- **All runtime output goes to `data/`**, kept separate from source files.

---

## Repository layout

| Path | What it is |
| --- | --- |
| [`Strategies/Default/`](Strategies/Default/README.md) | India (NSE) engine: screener, backtester, code generators, utilities, and the FastAPI app in `api/` ([API reference](Strategies/Default/api/README.md)) |
| [`Strategies/US/`](Strategies/US/README.md) | US (S&P 500) engine: same structure as `Default/`, with price data from Alpaca (`market_data.py`) and an S&P 500 benchmark (`sp500_utils.py`) |
| [`Strategies/frontend/`](Strategies/frontend/README.md) | React + Vite + TypeScript web app |
| [`Strategies/Rules_backup/`](Strategies/Rules_backup/), [`Strategies/ExitRules_backup/`](Strategies/ExitRules_backup/) | Auto-saved versions of the India `rules.md` and `exit_rules.md` (the US engine keeps its own in `Strategies/US/`) |
| `Strategies/*/generated_strategies/` | Compiled sub-strategies used by router-mode `rules.md` files (see [Router strategies](Strategies/Default/RULES_GUIDE.md#router-strategies-switching-between-strategies-by-market-regime)) |
| [`Strategies/package.json`](Strategies/package.json) | `npm run dev`, which starts both backends and the frontend together |
| `Strategies/Start FrontierTradeLight.*` | One-click launchers for macOS (`.command`) and Windows (`.bat` / `.ps1`) |
| [`reports/`](reports/README.md), [`research_notes/`](research_notes/README.md) | Strategy research write-ups and the source notes behind them |

---

## Strategy engine

Each module below exists in `Strategies/Default/`. Unless a note says
otherwise, `Strategies/US/` has a module of the same name. For a complete
per-file reference, see the [India engine README](Strategies/Default/README.md)
and the [US differences](Strategies/US/README.md).

### Strategy specs and code generation

- **`rules.md`**: the entry strategy, written in plain English. It holds
  mandatory filters, rejection rules, ranking/scoring weights, and output
  columns. See [`RULES_GUIDE.md`](Strategies/Default/RULES_GUIDE.md). It
  can also be a *router* that switches between several saved strategies
  based on market breadth.
- **`generate_screener.py`**: sends `rules.md` to Gemini and writes the
  resulting `evaluate_stock(symbol, df, universe, sector_ranks,
  market_breadth)` to `generated_rules.py`. It writes only that file (plus
  `generated_strategies/` in router mode).
- **`exit_rules.md`**: the exit strategy in the same style: stop-loss,
  take-profit, trailing stop, time-based exit, or anything else computable
  from OHLCV. See the exit-strategy section of
  [`BACKTEST_GUIDE.md`](Strategies/Default/BACKTEST_GUIDE.md).
- **`generate_exit_strategy.py`**: sends `exit_rules.md` to Gemini and
  writes `resolve_exit(...)` to `generated_exit_strategy.py`.
- **`generated_rules.py` / `generated_exit_strategy.py`**: generated code,
  checked in. Don't hand-edit them, because the next generation overwrites
  them.
- **`backup_utils.py`**: versioned backups of both specs, grouped by
  strategy name, and powers the version-history drawers in the app. Each
  save of a changed spec writes
  `<strategy_slug>_<rules|exit_rules>_<YYYYMMDD_HHMMSS>.md` to the backup
  folder, with the slug taken from the spec's `Strategy Name:` line. Every
  `.md` file in a backup folder is listed as a version, so keep other files
  out of those folders.

### Data and universe

- **`historical_universe.py`** *(India)*: point-in-time Nifty 500
  membership, built from archived NSE constituent lists and stored
  permanently in `data/universe_history/`. The backtester uses it so that
  each simulated day only trades stocks that were in the index on that day.
- **`universe_fetcher.py`**: the live universe. It fetches today's index
  list (Nifty 500 on India, S&P 500 on US), ranks sectors by recent return,
  and keeps the top N stocks per sector. The result is cached for one day.
- **`nse_utils.py`** *(India)* / **`market_data.py`** *(US)*: price-history
  fetchers. India uses `jugaad-data`, with retry/backoff and staggering to
  stay under NSE's rate limits. US uses Alpaca's batched bars endpoint.
  `nse_utils.py` also provides `calculate_sector_strength` and
  `calculate_market_breadth`.
- **`nifty_utils.py`** *(India)* / **`sp500_utils.py`** *(US)*: benchmark
  equity curves (the Nifty 50 index level, or SPY) for comparing a backtest
  against.
- **`inflation_utils.py`**: annual CPI from the World Bank API, used to show
  inflation-adjusted backtest returns.

### Runners

- **`stock_screener.py`**: the live buy screener. It builds the universe,
  fetches recent prices, computes sector ranks and market breadth, runs
  `evaluate_stock` on every stock, and writes `data/stock_report.csv`.
- **`sell_screener.py`**: the sell-side mirror. For each position in
  `data/holdings.csv`, it replays the exit logic since entry and reports
  whether the exit would have fired. Each holding can pin its own exit-rule
  version (the `ExitRule` column). A blank value means the live
  `generated_exit_strategy.py`.
- **`backtest.py`**: replays the entry and exit logic over a date range with
  no look-ahead. A second pass then simulates a real portfolio with
  starting capital, a fixed number of concurrent position slots, and
  compounding as trades close. See
  [`BACKTEST_GUIDE.md`](Strategies/Default/BACKTEST_GUIDE.md).
- **`backtest_runner.py`** / **`stats_utils.py`**: progress parsing for a
  running backtest, and the Stats leaderboard (CAGR, Max Drawdown,
  Composite Score, trade count). A result is recorded only when the
  backtest ran over the exact benchmark range of **2021-01-01 to
  2026-01-01** (`constants.py`).
- **`multi_strategy_utils.py`**: runs one stock through several saved
  strategies at once. It compiles each strategy into its own module under
  `data/multi_strategy/`, so the live `rules.md` is never touched.

### India-only modules

- **`event_watcher_utils.py`**: the Event Watcher signal (see below).
- **`fund_manager_utils.py`**, **`fund_documents_utils.py`**: the Fund
  Manager ledger and its document storage.

---

## The app

The tabbed app at `http://localhost:5173` has ten tabs. All of them except
Event Watcher work for both markets.

| Tab | What it does |
| --- | --- |
| **Rules** | Edit and save `rules.md`. Restore any earlier version from a searchable drawer that marks the latest version and the best-scoring one. |
| **Run** | Regenerate `generated_rules.py` from `rules.md`, and run the live screener, with streamed console output. |
| **Results** | Sortable, filterable view of `stock_report.csv`, with a toggle to show only stocks that passed every filter. |
| **Sell** | Track open positions (`holdings.csv`), choose an exit-rule version per holding, and check each one against its exit signal. |
| **Backtest** | Edit and generate `exit_rules.md`, then run a backtest with a date range, starting capital, and max concurrent positions (default 6). Shows a live log with a stop button, score-bucketed trade stats, and the portfolio result (final equity, total and inflation-adjusted return, CAGR, Max Drawdown, Composite Score, equity curve against the benchmark). |
| **Deep Dive** | A single stock's indicators and a rule-by-rule pass/fail breakdown. |
| **Missed Opportunities** | Near-misses from the last backtest (stocks that failed exactly one rule), grouped by the blocking rule, with the forward return each would have earned. |
| **Stats** | Leaderboard of every benchmarked entry + exit strategy pair, with one-click switching to any recorded version. |
| **Event Watcher** *(India only)* | A news-driven signal that is fully separate from the screener and backtester. It scans PIB Ministry of Defence press releases for naval commissioning or induction news that names a watchlisted shipbuilder (Cochin Shipyard, Mazagon Dock, GRSE, HAL, and others). It supports live polling, historical lookup, and an editor for keywords, the watchlist, and vessel-class aliases. It also tracks MEESHO investor/analyst-meet filings from NSE. See [`event_watcher_utils.py`](Strategies/Default/event_watcher_utils.py). |
| **Multi-Strategy** | Runs one stock through several saved strategies side by side. |

### Fund Manager *(India only)*

The Fund Manager is at `/fund-manager` (linked from the app header). It is a
standalone view for a real-money fund's NAV/units accounting and is
completely independent of the backtest engine. Backtests are a research
tool and are never a source of fund numbers. It has three tabs:

- **Overview**: AUM, NAV, per-investor units and value, and capital-event
  history (deposits and withdrawals). Its "Send update" action opens an
  email draft.
- **Holdings**: the fund's actual positions and cash. These are separate
  from the personal Sell tab.
- **Documents**: file storage, with metadata, for fund paperwork.

---

## Setup

**Requirements:** Python 3.12, Node.js 18+, a
[Gemini API key](https://aistudio.google.com/apikey) (only needed for code
generation), and, for the US market, a free
[Alpaca](https://alpaca.markets) account.

1. **Create the Python virtual environment.** It must live at
   `Strategies/Default/.venv`, because `npm run dev` and the launchers run
   `Default/.venv/bin/uvicorn` directly. Both backends share this
   environment.

   ```bash
   cd Strategies/Default
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Install the Node dependencies** for the dev orchestrator and the
   frontend:

   ```bash
   cd Strategies
   npm install
   npm install --prefix frontend
   ```

3. **Add your API keys:**

   ```bash
   cp Strategies/Default/.env.template Strategies/Default/.env   # GEMINI_API_KEY
   cp Strategies/US/.env.template Strategies/US/.env             # ALPACA_API_KEY, ALPACA_SECRET_KEY
   ```

   The US engine generates code with Gemini too, so add `GEMINI_API_KEY` to
   `Strategies/US/.env` as well if you plan to regenerate US rules.

4. **Create your strategy specs.** `rules.md` and `exit_rules.md` are
   gitignored, so a fresh clone has none. Restore a version from the Rules
   and Backtest tabs' version drawers, copy one from
   `Strategies/Rules_backup/` and `Strategies/ExitRules_backup/`, or write
   your own by following the guides.

---

## Usage

### Web app (recommended)

```bash
cd Strategies
npm run dev
```

This starts the India backend (`http://localhost:8000`), the US backend
(`http://localhost:8001`), and the frontend (`http://localhost:5173`). The
launchers in `Strategies/` (`Start FrontierTradeLight.command` on macOS,
`.bat` / `.ps1` on Windows) do the same without a terminal, install missing
Node dependencies, and clean up child processes on exit.

### Command line

Run these from `Strategies/Default/` (India) or `Strategies/US/` (US), with
the virtual environment active.

```bash
# Regenerate code after editing a spec
python generate_screener.py         # rules.md      -> generated_rules.py
python generate_exit_strategy.py    # exit_rules.md -> generated_exit_strategy.py

# Live screening
python stock_screener.py            # buys  -> data/stock_report.csv
python sell_screener.py             # sells -> data/sell_report.csv (--holdings, --out)

# Backtest (--max-positions defaults to 10 on the CLI, 6 in the app)
python backtest.py --start 2021-01-01 --end 2026-01-01 \
    --initial-capital 100000 --max-positions 6

# India only: pull newer archived Nifty 500 snapshots and print coverage
python historical_universe.py
```

The US `backtest.py` also accepts `--limit-per-sector` (default 50). The
CLI backtest writes only the CSVs. Results reach the Stats leaderboard only
when the backtest is run through the app over the benchmark range.

---

## Data files

All runtime data lives in `Strategies/Default/data/` (India) and
`Strategies/US/data/` (US). Most of it is regenerable and gitignored. The
files marked **tracked** have no other source, so they are committed.

| File | Contents |
| --- | --- |
| `stock_report.csv` | One row per screened stock: `Symbol`, `Passed`, `ClosenessScore` (0-100), `FailedRules`, plus every metric in `Details` |
| `backtest_trades.csv` | One row per simulated trade: entry and exit, `ExitReason`, `ClosenessScore`, `ProfitRs` (% return on a flat 100 stake), `Funded`, `AllocatedCapital` |
| `backtest_summary.csv` | Trades bucketed by `ClosenessScore`, with win rate and mean, median, and total profit |
| `backtest_portfolio.csv` | Portfolio equity curve |
| `near_misses.csv` | Stocks that failed exactly one rule (feeds Missed Opportunities) |
| `backtest_meta.json`, `backtest_run.log` | Metadata and log of the last backtest |
| `strategy_stats.csv` | **Tracked.** The Stats leaderboard |
| `holdings.csv` | **Tracked.** Your positions for the Sell tab (`Symbol, EntryPrice, EntryDate, CurrentPrice, ExitRule`) |
| `sell_report.csv` | Latest sell-signal check |
| `universe_history/` | **Tracked, India.** Archived Nifty 500 snapshots and the consolidated `membership.csv` |
| `fund/` | **Tracked, India.** Fund Manager ledger and documents |
| `event_watcher/` | India. Event Watcher matches, poll state, and the editable keyword/watchlist config |
| `multi_strategy/` | Compiled strategy modules and the cached market context for the Multi-Strategy tab |
| `backtest_cache/`, `universe_cache.json`, `inflation_cache.json`, `nifty50_cache.json` | Caches. The universe expires after 1 day and CPI after 30 days. Per-symbol backtest history never expires, so delete `backtest_cache/` to force a refetch |

---

## Further documentation

- [India engine](Strategies/Default/README.md) and
  [US engine](Strategies/US/README.md): per-module reference.
- [API reference](Strategies/Default/api/README.md): every endpoint on both
  backends.
- [Frontend](Strategies/frontend/README.md): source layout, market
  switching, and how to add a tab.
- [`RULES_GUIDE.md`](Strategies/Default/RULES_GUIDE.md): how to write
  `rules.md`, including router strategies
  ([US version](Strategies/US/RULES_GUIDE.md)).
- [`BACKTEST_GUIDE.md`](Strategies/Default/BACKTEST_GUIDE.md): how the
  backtest and portfolio simulation work, how to write `exit_rules.md`,
  and how to read the output
  ([US version](Strategies/US/BACKTEST_GUIDE.md)).
- [`Strategies/Rules_backup/`](Strategies/Rules_backup/) and
  [`Strategies/ExitRules_backup/`](Strategies/ExitRules_backup/): every
  saved strategy version, with worked examples of real specs.
- [`reports/`](reports/README.md): indexed research write-ups, for example
  on exits for horizontal breakouts and on strategies for low market
  breadth. Their source notes are indexed in
  [`research_notes/`](research_notes/README.md).
- [Architecture diagram (Eraser)](https://app.eraser.io/workspace/v1y7m3ZvWhMKdUCjvG4m).

---

## Notes and caveats

- **Review generated code.** `generated_rules.py` and
  `generated_exit_strategy.py` are AI output, so read the diff after
  regenerating and before you trust or commit it. Hardcoded `pandas_ta`
  column names (they vary by version) and swallowed exceptions have both
  appeared in past generations.
- **Universe bias.** The India backtest uses point-in-time Nifty 500
  membership, but the snapshots are sparse, so index changes between two
  snapshots show up late. The US backtest and both live screeners use
  *today's* index list, so the US backtest has survivorship bias.
- **No trading costs.** Backtests don't model slippage, brokerage, or taxes
  (STT, fees).
- **Total return is cumulative**, not annualized. Check CAGR before judging
  a result.
- **EOD data lag (India).** `jugaad-data` reads NSE's end-of-day archives,
  which lag live quotes by at least one session.
- **Event Watcher's feed** comes from an unofficial community scrape of
  PIB, which could go stale without warning. "No matches" and "feed
  unreachable" mean different things.
- **Entry and exit pairing.** The live `rules.md` and `exit_rules.md` are
  not necessarily the pair that was benchmarked together. Check both
  files' metadata headers before you treat a Stats number as representative.
- **Secrets.** Never commit a real `.env` file. Only `.env.template` is
  tracked.
