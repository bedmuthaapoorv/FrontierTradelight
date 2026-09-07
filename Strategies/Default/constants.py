import os
from datetime import date

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# The standard range every strategy's Stats tab row is compared on. Not a
# suggestion - tabs/backtest.py only upserts into the Stats tab when a
# backtest actually ran over exactly this range, so the leaderboard never
# silently mixes results from different time windows.
BENCHMARK_START_DATE = date(2021, 1, 1)
BENCHMARK_END_DATE = date(2026, 1, 1)

RULES_PATH = os.path.join(APP_DIR, "rules.md")
BACKUP_DIR = os.path.normpath(os.path.join(APP_DIR, "..", "Rules_backup"))

EXIT_RULES_PATH = os.path.join(APP_DIR, "exit_rules.md")
EXIT_BACKUP_DIR = os.path.normpath(os.path.join(APP_DIR, "..", "ExitRules_backup"))

# All generated/runtime data (reports, caches, logs) lives under one
# folder instead of scattered across Default/ - keeps the project root to
# source files only.
DATA_DIR = os.path.join(APP_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

REPORT_PATH = os.path.join(DATA_DIR, "stock_report.csv")

HOLDINGS_PATH = os.path.join(DATA_DIR, "holdings.csv")
SELL_REPORT_PATH = os.path.join(DATA_DIR, "sell_report.csv")

BACKTEST_TRADES_PATH = os.path.join(DATA_DIR, "backtest_trades.csv")
BACKTEST_SUMMARY_PATH = os.path.join(DATA_DIR, "backtest_summary.csv")
BACKTEST_PORTFOLIO_PATH = os.path.join(DATA_DIR, "backtest_portfolio.csv")
BACKTEST_LOG_PATH = os.path.join(DATA_DIR, "backtest_run.log")
NEAR_MISSES_PATH = os.path.join(DATA_DIR, "near_misses.csv")
STRATEGY_STATS_PATH = os.path.join(DATA_DIR, "strategy_stats.csv")
BACKTEST_META_PATH = os.path.join(DATA_DIR, "backtest_meta.json")

BACKTEST_CACHE_DIR = os.path.join(DATA_DIR, "backtest_cache")
UNIVERSE_CACHE_PATH = os.path.join(DATA_DIR, "universe_cache.json")
INFLATION_CACHE_PATH = os.path.join(DATA_DIR, "inflation_cache.json")
NIFTY50_CACHE_PATH = os.path.join(DATA_DIR, "nifty50_cache.json")
