# Frontier TradeLight

See the [project README](../README.md) for the full picture — architecture,
setup, every tab, and the strategy-engine pipeline (`rules.md` ->
`generated_rules.py` -> screener/backtester).

## Running the project

```bash
npm run dev
```

This starts the FastAPI backend (`http://localhost:8000`) and the Vite/React frontend (`http://localhost:5173`) together. (Run from this `Strategies/` directory — that's where this `package.json` lives.)

The legacy Streamlit UI (being phased out) can still be run separately with:

```bash
python -m streamlit run Default/app.py
```
