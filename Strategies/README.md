# Frontier TradeLight

See the [project README](../README.md) for the full picture — architecture,
setup, every tab, and the strategy-engine pipeline (`rules.md` ->
`generated_rules.py` -> screener/backtester).

## Running the project

```bash
npm run dev
```

This starts the India backend (`Default/`, `http://localhost:8000`), the US backend (`US/`, `http://localhost:8001`) and the Vite/React frontend (`http://localhost:5173`) together. (Run from this `Strategies/` directory — that's where this `package.json` lives.) Use the **India / US** switch in the app header to pick which backend the UI talks to.

## US market (`US/`)

`US/` is a separate copy of `Default/` for S&P 500 stocks: its own rules, rule backups, caches, holdings and backtests. Price history comes from Alpaca's free Market Data API (`US/market_data.py`), which fetches many symbols per request instead of NSE's one request per stock per month. The Fund Manager and Event Watcher are India-only. The US backend runs on `Default/.venv`.

Setup: create a free account at alpaca.markets, then add your keys to `US/.env` (see `US/.env.template`):

```
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
```

The legacy Streamlit UI (being phased out) can still be run separately with:

```bash
python -m streamlit run Default/app.py
```
