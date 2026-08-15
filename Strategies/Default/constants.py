import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))

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

# Risk-based sizing comparison run (same trades, sizing_mode="risk") - kept
# as separate files so the equal-weight baseline above is never overwritten
# and both can be loaded side by side in the Risk tab.
BACKTEST_TRADES_RISK_PATH = os.path.join(DATA_DIR, "backtest_trades_risk.csv")
BACKTEST_SUMMARY_RISK_PATH = os.path.join(DATA_DIR, "backtest_summary_risk.csv")
BACKTEST_PORTFOLIO_RISK_PATH = os.path.join(DATA_DIR, "backtest_portfolio_risk.csv")
BACKTEST_RISK_INFO_PATH = os.path.join(DATA_DIR, "backtest_risk_info.json")
BACKTEST_RISK_LOG_PATH = os.path.join(DATA_DIR, "backtest_risk_run.log")

BACKTEST_CACHE_DIR = os.path.join(DATA_DIR, "backtest_cache")
UNIVERSE_CACHE_PATH = os.path.join(DATA_DIR, "universe_cache.json")
INFLATION_CACHE_PATH = os.path.join(DATA_DIR, "inflation_cache.json")
NIFTY50_CACHE_PATH = os.path.join(DATA_DIR, "nifty50_cache.json")
