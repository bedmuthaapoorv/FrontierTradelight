"""FastAPI backend for Frontier TradeLight, replacing the Streamlit UI.

Run from Default/ (same convention every other script in this project
uses) so the existing top-level engine modules - backtest.py,
stock_screener.py, generate_screener.py, generate_exit_strategy.py,
sell_screener.py, backup_utils.py, stats_utils.py - import exactly as
they already do, with zero changes to any of them:

    uvicorn api.main:app --reload --port 8000

Phase 1 (this file): just a health check, to prove the FastAPI process
starts cleanly and the Vite dev server can reach it through CORS. Routers
for rules/exit-rules/jobs/results/stats get added in later phases.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Frontier TradeLight API")

# Vite's default dev server origin. Widen this (or make it configurable)
# once there's a real deployment target - hardcoded to localhost during
# the phased migration since this is a local personal tool.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
