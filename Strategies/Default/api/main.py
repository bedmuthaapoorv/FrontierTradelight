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

from api.routers.backtest import router as backtest_router
from api.routers.holdings import router as holdings_router
from api.routers.jobs import router as jobs_router
from api.routers.markdown_files import make_markdown_router
from api.routers.missed_opportunities import router as missed_opportunities_router
from api.routers.fund_manager import router as fund_manager_router
from api.routers.results import make_report_router
from api.routers.stats import router as stats_router
from constants import (
    BACKTEST_SUMMARY_PATH,
    BACKTEST_TRADES_PATH,
    BACKUP_DIR,
    EXIT_BACKUP_DIR,
    EXIT_RULES_PATH,
    REPORT_PATH,
    RULES_PATH,
    SELL_REPORT_PATH,
)

app = FastAPI(title="Frontier TradeLight API")

app.include_router(
    make_markdown_router(
        prefix="/rules", path=RULES_PATH, backup_dir=BACKUP_DIR, backup_suffix="rules",
    )
)
app.include_router(
    make_markdown_router(
        prefix="/exit-rules", path=EXIT_RULES_PATH, backup_dir=EXIT_BACKUP_DIR, backup_suffix="exit_rules",
    )
)
app.include_router(jobs_router)
app.include_router(make_report_router(prefix="/results", path=REPORT_PATH))
app.include_router(make_report_router(prefix="/sell-report", path=SELL_REPORT_PATH))
app.include_router(make_report_router(prefix="/backtest-trades", path=BACKTEST_TRADES_PATH))
app.include_router(make_report_router(prefix="/backtest-summary", path=BACKTEST_SUMMARY_PATH))
app.include_router(holdings_router)
app.include_router(backtest_router)
app.include_router(missed_opportunities_router)
app.include_router(stats_router)
app.include_router(fund_manager_router)

# Vite picks the next free port (5173, 5174, ...) if 5173 is already
# taken, e.g. by another dev instance - match any localhost port instead
# of hardcoding 5173, so CORS doesn't silently break depending on which
# port Vite happened to bind to. Still localhost-only, fine for this
# local personal tool.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
