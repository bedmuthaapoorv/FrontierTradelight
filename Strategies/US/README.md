# US engine (`Strategies/US/`)

The US (S&P 500) strategy engine and its API backend (port 8001). It
started as a copy of the India engine in [`../Default/`](../Default/README.md)
and keeps the same module names, interfaces, and data-file layout, so the
shared React frontend works against either backend unchanged. This page
covers only what differs. For everything else, see the
[India engine README](../Default/README.md) and the
[project README](../../README.md).

Like the India engine, run scripts with this folder as the working
directory.

## Guides

- [`RULES_GUIDE.md`](RULES_GUIDE.md): how to write `rules.md` for US stocks.
- [`BACKTEST_GUIDE.md`](BACKTEST_GUIDE.md): the backtest, adjusted for
  Alpaca data and dollars.
- [API reference](../Default/api/README.md#us-differences): shared with
  India, with a US differences section.

## How it differs from India

| Area | India (`Default/`) | US (`US/`) |
| --- | --- | --- |
| Price data | `nse_utils.py`: `jugaad-data`, one request per stock per month | `market_data.py`: Alpaca Market Data API, many symbols per request. Uses the consolidated (SIP) feed and falls back to IEX-only if the account can't read SIP |
| Live universe | `universe_fetcher.py`: today's Nifty 500 | `universe_fetcher.py`: today's S&P 500 (public constituents CSV), top N per GICS sector by 6-month return |
| Backtest universe | Point-in-time Nifty 500 (`historical_universe.py`) | Today's S&P 500 list, so the backtest has survivorship bias. `backtest.py` adds `--limit-per-sector` (default 50) |
| Benchmark | `nifty_utils.py`: Nifty 50 index level | `sp500_utils.py`: SPY |
| Inflation | India CPI (World Bank) | US CPI (World Bank) |
| Rule data | Includes NSE delivery % | No delivery % |
| Rule backups | `../Rules_backup/`, `../ExitRules_backup/` | `Rules_backup/`, `ExitRules_backup/` in this folder. They are kept separate because India strategies use rupee thresholds |
| India-only features | Event Watcher, Fund Manager | Not available |
| API | | Adds `GET /market`. No `/multi-strategy/run-stream` |
| `.env` | `GEMINI_API_KEY` | `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, plus `GEMINI_API_KEY` if you regenerate rules |
| Python environment | `Default/.venv` | Also `Default/.venv` (there is no `requirements.txt` here) |

`ProfitRs` and similar column names keep their India names because the
shared frontend reads them. On the US side the values are dollars, or
equivalently % return on a flat 100 stake.

## Modules

`backtest.py`, `backtest_runner.py`, `backup_utils.py`, `constants.py`,
`generate_screener.py`, `generate_exit_strategy.py`, `generated_rules.py`,
`generated_exit_strategy.py`, `inflation_utils.py`, `multi_strategy_utils.py`,
`sell_screener.py`, `stats_utils.py`, `stock_screener.py`, and
`universe_fetcher.py` do the same job as their India counterparts (see the
[India module tables](../Default/README.md#modules)). Only the data source
and market-specific wording differ.

US-only modules:

| File | Purpose |
| --- | --- |
| `market_data.py` | Alpaca daily bars, returned in the same column shape as `jugaad-data` so the rest of the engine is unchanged. Also provides `calculate_sector_strength` and `calculate_market_breadth` (which live in `nse_utils.py` on India) |
| `sp500_utils.py` | SPY benchmark curve |
