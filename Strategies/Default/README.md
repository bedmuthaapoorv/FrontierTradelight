# India engine (`Strategies/Default/`)

The India (NSE) strategy engine and its API backend. Every script here
expects to run with this folder as the working directory, because modules
import each other as top-level modules (`from constants import ...`). The
API (`uvicorn api.main:app`), the launchers, and the job endpoints all
respect this.

For setup, the app's tabs, and the end-to-end pipeline, see the
[project README](../../README.md).

## Guides

- [`RULES_GUIDE.md`](RULES_GUIDE.md): how to write `rules.md`, including
  router strategies.
- [`BACKTEST_GUIDE.md`](BACKTEST_GUIDE.md): how the backtest works, how to
  write `exit_rules.md`, and how to read the output.
- [`api/README.md`](api/README.md): API endpoint reference.

## Modules

### Specs and code generation

| File | Purpose |
| --- | --- |
| `rules.md`, `exit_rules.md` | Entry and exit strategy specs, in plain English. Local only (gitignored); versions are kept in `../Rules_backup/` and `../ExitRules_backup/` |
| `generate_screener.py` | Sends `rules.md` to Gemini and writes `generated_rules.py`. In router mode it also writes `generated_strategies/<Key>.py` |
| `generate_exit_strategy.py` | Sends `exit_rules.md` to Gemini and writes `generated_exit_strategy.py` |
| `generated_rules.py` | Generated `evaluate_stock(symbol, df, universe, sector_ranks, market_breadth)`. Don't edit by hand |
| `generated_exit_strategy.py` | Generated `resolve_exit(...)`. Don't edit by hand |
| `backup_utils.py` | Versioned backups of both specs. Names each backup `<strategy_slug>_<rules\|exit_rules>_<YYYYMMDD_HHMMSS>.md` from the spec's `Strategy Name:` line, and groups versions by strategy |

### Market data and universe

| File | Purpose |
| --- | --- |
| `nse_utils.py` | NSE price history via `jugaad-data`, with retry/backoff. Also `calculate_sector_strength` and `calculate_market_breadth` |
| `universe_fetcher.py` | Live universe: today's Nifty 500, ranked by sector return, top N per sector. Cached for 1 day |
| `historical_universe.py` | Point-in-time Nifty 500 membership from archived NSE lists, stored in `data/universe_history/`. Run it directly to add newer snapshots |
| `nifty_utils.py` | Nifty 50 index benchmark curve for backtest comparison |
| `inflation_utils.py` | India annual CPI from the World Bank API, for inflation-adjusted returns. Cached for 30 days |

### Runners

| File | Purpose |
| --- | --- |
| `stock_screener.py` | Live buy screener. Writes `data/stock_report.csv` |
| `sell_screener.py` | Checks `data/holdings.csv` against each holding's exit rule. Writes `data/sell_report.csv`. Pinned exit-rule versions compile to `generated_exit_strategies/` |
| `backtest.py` | Signal replay plus a capital-constrained portfolio simulation. Writes the `backtest_*.csv` files and `near_misses.csv` |
| `backtest_runner.py` | Parses a running backtest's progress, and records finished benchmark-range runs to the leaderboard |
| `stats_utils.py` | Reads and writes `data/strategy_stats.csv`, keyed by entry + exit strategy pair |
| `multi_strategy_utils.py` | Evaluates one stock against several saved strategies, compiled under `data/multi_strategy/` |

### India-only features

| File | Purpose |
| --- | --- |
| `event_watcher_utils.py` | Event Watcher: PIB defence press releases matched against a shipbuilder watchlist, plus MEESHO investor/analyst-meet filings from NSE |
| `fund_manager_utils.py` | Fund Manager NAV/units accounting (investors, capital events, NAV history, holdings, cash) |
| `fund_documents_utils.py` | Fund document storage with metadata |

### Shared and legacy

| File | Purpose |
| --- | --- |
| `constants.py` | Every file path and the benchmark date range (`BENCHMARK_START_DATE` / `BENCHMARK_END_DATE`) |
| `strings.py` | UI copy for the removed Streamlit app. No longer imported |
| `requirements.txt` | Python dependencies for both backends |
| `.env.template` | Copy to `.env` and set `GEMINI_API_KEY` |

## Folders

| Folder | Contents |
| --- | --- |
| `api/` | FastAPI app. See [`api/README.md`](api/README.md) |
| `generated_strategies/` | Compiled sub-strategies for router-mode `rules.md` (Breakout, MeanReversion, Trendline) |
| `generated_exit_strategies/` | Compiled pinned exit-rule versions used by the Sell tab (created on demand) |
| `data/` | All runtime output and caches. Mostly gitignored; see the project README's *Data files* section |
| `.venv/` | The Python environment shared by both backends (not tracked) |
