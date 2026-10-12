# Frontier TradeLight API

FastAPI backend that the React frontend talks to. There are two instances
built from near-identical code:

| Backend | Code | Port | Base URL |
| --- | --- | --- | --- |
| India | `Strategies/Default/api/` | 8000 | `http://localhost:8000` |
| US | `Strategies/US/api/` | 8001 | `http://localhost:8001` |

This document covers both. Endpoints that differ are marked; see
[US differences](#us-differences). For setup and the overall architecture,
see the [project README](../../../README.md).

## Running

`npm run dev` in `Strategies/` starts both backends. To run one on its own,
start it from its engine folder so the engine modules import as top-level
modules:

```bash
cd Strategies/Default && .venv/bin/uvicorn api.main:app --reload --port 8000
cd Strategies/US && ../Default/.venv/bin/uvicorn api.main:app --reload --port 8001
```

FastAPI's interactive docs are served at `/docs` (for example
`http://localhost:8000/docs`), with the full request and response schemas.

## Conventions

- **Local, single-user.** There is no authentication. CORS allows any
  `http://localhost:<port>` origin, so the backends must not be exposed
  beyond your machine.
- **Files are the database.** Endpoints read and write the CSV, JSON, and
  Markdown files in the engine's `data/` folder and its spec files (see the
  project README's *Data files* section).
- **Streamed jobs.** The `/jobs/*` endpoints run an engine script as a
  subprocess and stream its stdout as `text/plain`, one line at a time. The
  last line is `__EXIT_CODE__:<n>`. The frontend's `streamJob()` in
  `src/api.ts` parses this.
- **Backtests run in the background.** `POST /backtest/run` launches
  `backtest.py` as a subprocess and returns immediately. Poll
  `GET /backtest/status`. Only one backtest can run at a time; a second
  request gets `409`.

## Layout

```
api/
  main.py                    app, CORS, router mounting, /health (+ /market on US)
  routers/
    markdown_files.py        factory: mounted at /rules and /exit-rules
    results.py               factory: mounted once per report CSV
    jobs.py                  streamed script runs
    holdings.py              Sell tab positions
    backtest.py              backtest lifecycle and charts
    missed_opportunities.py  near-miss analysis
    stats.py                 leaderboard and strategy switching
    multi_strategy.py        Multi-Strategy tab
    event_watcher.py         India only
    fund_manager.py          India only
```

## Endpoints

### Health

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Returns `{"status": "ok"}` |
| GET | `/market` | **US only.** Identifies the backend's market, currency, labels, and feature flags |

### Strategy specs: `/rules` and `/exit-rules`

Both prefixes are mounted from the same factory and expose the same routes.
`/rules` manages `rules.md` and `Rules_backup/`; `/exit-rules` manages
`exit_rules.md` and `ExitRules_backup/`.

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| GET | `{prefix}` | | Current file content |
| PUT | `{prefix}` | `{content}` | Save. The previous content is backed up first if it changed |
| GET | `{prefix}/backups` | | Backups, grouped by strategy name |
| GET | `{prefix}/backups/{filename}` | | One backup's content |
| POST | `{prefix}/backups/{filename}/restore` | | Back up the live file, then overwrite it with this backup |
| POST | `{prefix}/backups/{filename}/rename` | `{new_name}` | Rename a backup |
| DELETE | `{prefix}/backups/{filename}` | | Delete a backup |

### Jobs (streamed)

| Method | Path | Runs |
| --- | --- | --- |
| POST | `/jobs/generate-screener` | `generate_screener.py`: `rules.md` to `generated_rules.py` |
| POST | `/jobs/run-screener` | `stock_screener.py`: writes `stock_report.csv` |
| POST | `/jobs/generate-exit-strategy` | `generate_exit_strategy.py`: `exit_rules.md` to `generated_exit_strategy.py` |
| POST | `/jobs/check-exit-signals` | `sell_screener.py`: writes `sell_report.csv` |

### Reports

Each prefix returns one CSV from `data/` as rows (`GET` only).

| Method | Path | File |
| --- | --- | --- |
| GET | `/results` | `stock_report.csv` |
| GET | `/sell-report` | `sell_report.csv` |
| GET | `/backtest-trades` | `backtest_trades.csv` |
| GET | `/backtest-summary` | `backtest_summary.csv` |

### Holdings (Sell tab)

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| GET | `/holdings` | | Positions from `holdings.csv` |
| PUT | `/holdings` | `{holdings: [{Symbol, EntryPrice, EntryDate, CurrentPrice?, ExitRule?}]}` | Replace all positions. `ExitRule` is a filename in the exit-rule backups; leave it blank to use the live exit strategy |

### Backtest

| Method | Path | Body / query | Description |
| --- | --- | --- | --- |
| POST | `/backtest/run` | `{start, end, initial_capital, max_positions}` | Start a backtest (`409` if one is already running) |
| POST | `/backtest/stop` | | Stop the running backtest |
| GET | `/backtest/status` | | Running state, day progress, ETA, and the log tail. The first poll after a successful finish records the result to the Stats leaderboard if the run used the benchmark range |
| GET | `/backtest/result` | | Portfolio summary of the last run (final equity, return, CAGR, Max Drawdown, Composite Score) |
| GET | `/backtest/chart` | `?inflation=bool&nifty=bool` (India) or `?inflation=bool&benchmark=bool` (US) | Equity curve, with optional inflation-adjusted and benchmark series |
| GET | `/backtest/yearly` | | Per-calendar-year returns |
| GET | `/backtest/portfolio-by-year` | | Daily equity path for each year, used by Deep Dive |

### Missed Opportunities

| Method | Path | Description |
| --- | --- | --- |
| GET | `/missed-opportunities` | Near-misses from the last backtest, grouped by blocking rule, with forward returns |

### Stats

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| GET | `/stats` | | Leaderboard rows from `strategy_stats.csv` |
| GET | `/stats/strategy-options` | | Selectable strategies (current live, plus each backup group) |
| POST | `/stats/load-strategy` | `{group_key}` | Make that strategy's latest version the live `rules.md` (backing up the current one) and regenerate `generated_rules.py` |

### Multi-Strategy

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| GET | `/multi-strategy/strategies` | | Strategies available to compare |
| POST | `/multi-strategy/run` | `{symbol, strategy_keys, refresh_context?}` | Evaluate one stock against each strategy |
| POST | `/multi-strategy/run-stream` | same | **India only.** Same as `/run`, but streams newline-delimited JSON `progress` events, then one `result` or `error` event |

### Event Watcher (India only)

Two independent sources: PIB defence press releases matched against a
shipbuilder watchlist, and NSE investors/analysts-meet filings for MEESHO.

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| GET | `/event-watcher` | | Cached PIB matches and last-checked state |
| POST | `/event-watcher/refresh` | | Poll the live feed now |
| GET | `/event-watcher/scanned` | | Every release scanned, matched or not |
| POST | `/event-watcher/historical` | `{date}` | Look up releases for a past date from the feed's git history |
| DELETE | `/event-watcher/historical` | | Clear historical lookup results |
| GET | `/event-watcher/keywords` | | Matching config |
| PUT | `/event-watcher/keywords` | `{event_keywords, watchlist: [{symbol, names}], vessel_class_aliases: [{phrase, symbol}]}` | Replace the matching config |
| GET | `/event-watcher/investor-meets` | | Cached MEESHO investor/analyst meets |
| POST | `/event-watcher/investor-meets/refresh` | | Pull new filings and parse meeting dates from their PDFs |

### Fund Manager (India only)

| Method | Path | Body | Description |
| --- | --- | --- | --- |
| GET | `/fund-manager/overview` | | AUM, NAV, investors, capital events, NAV history |
| POST | `/fund-manager/nav/calculate` | | Record today's NAV from current holdings and cash |
| POST | `/fund-manager/investors` | `{investor_id, name, email?, join_date}` | Add an investor |
| DELETE | `/fund-manager/investors/{investor_id}` | | Remove an investor |
| POST | `/fund-manager/capital-events` | `{date, investor_id, type, amount, nav_override?}` | Record a deposit or withdrawal |
| DELETE | `/fund-manager/capital-events/{row_index}` | | Remove a capital event |
| GET | `/fund-manager/holdings` | | Fund positions and cash |
| PUT | `/fund-manager/holdings` | `{holdings: [{Symbol, Qty, AvgCost, CurrentPrice}], cash}` | Replace fund positions and cash |
| GET | `/fund-manager/documents` | | Document metadata |
| POST | `/fund-manager/documents` | multipart: `file`, `category`, `date`, `notes` | Upload a document |
| GET | `/fund-manager/documents/{doc_id}/download` | | Download a document |
| DELETE | `/fund-manager/documents/{doc_id}` | | Delete a document |

## US differences

The US backend (`Strategies/US/api/`) shares every router file except the
ones listed here:

- **No** `event_watcher.py` or `fund_manager.py` routers.
- **Adds** `GET /market`, which the frontend uses to confirm it reached the
  US process.
- `GET /backtest/chart` takes `benchmark` (S&P 500 via SPY) instead of
  `nifty`, and returns it under the `benchmark` key.
- `POST /multi-strategy/run-stream` is not implemented.
- Rule backups live in `Strategies/US/Rules_backup/` and
  `Strategies/US/ExitRules_backup/`, separate from India's.
