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

# Fund Manager - the real-money fund's own records (NAV/units accounting for
# investors), kept in their own folder and entirely separate from the
# backtest engine's data above: the backtest is a research tool for
# evaluating strategies against history, the fund's numbers are never
# derived from it.
FUND_DATA_DIR = os.path.join(DATA_DIR, "fund")
os.makedirs(FUND_DATA_DIR, exist_ok=True)

FUND_INVESTORS_PATH = os.path.join(FUND_DATA_DIR, "investors.csv")
FUND_CAPITAL_EVENTS_PATH = os.path.join(FUND_DATA_DIR, "capital_events.csv")
FUND_NAV_HISTORY_PATH = os.path.join(FUND_DATA_DIR, "nav_history.csv")
FUND_HOLDINGS_PATH = os.path.join(FUND_DATA_DIR, "fund_holdings.csv")
FUND_CASH_PATH = os.path.join(FUND_DATA_DIR, "cash.json")
FUND_GENERATION_PATH = os.path.join(FUND_DATA_DIR, "generation.json")

# Fund documents - agreements/statements/compliance/tax paperwork the user
# uploads for the fund, distinct from any strategy or backtest file. Actual
# files live under FUND_DOCUMENTS_DIR named by their own doc id (never the
# original filename, to avoid path-traversal/collision issues); metadata
# (original name, category, date, notes) lives in the CSV alongside them.
FUND_DOCUMENTS_DIR = os.path.join(FUND_DATA_DIR, "documents")
os.makedirs(FUND_DOCUMENTS_DIR, exist_ok=True)
FUND_DOCUMENTS_META_PATH = os.path.join(FUND_DATA_DIR, "documents_meta.csv")

# Event Watcher - scans PIB (Press Information Bureau) press releases for
# naval commissioning/induction announcements and flags the listed
# shipbuilders they name (see event_watcher_utils.py). Entirely a news
# signal, unrelated to the OHLCV-based rules.md screener - it never feeds
# the backtester, only surfaces manual candidates in its own tab.
EVENT_WATCHER_DIR = os.path.join(DATA_DIR, "event_watcher")
os.makedirs(EVENT_WATCHER_DIR, exist_ok=True)
EVENT_WATCHER_EVENTS_PATH = os.path.join(EVENT_WATCHER_DIR, "events.csv")
EVENT_WATCHER_META_PATH = os.path.join(EVENT_WATCHER_DIR, "meta.json")
EVENT_WATCHER_KEYWORDS_PATH = os.path.join(EVENT_WATCHER_DIR, "keywords.json")
EVENT_WATCHER_SCANNED_PATH = os.path.join(EVENT_WATCHER_DIR, "last_scanned.json")
# Second, unrelated source in the same tab: Meesho investor/analyst meets
# pulled from NSE's own corporate-announcements API (see
# event_watcher_utils.py's investor-meet section for why this is separate
# from the PIB-derived events.csv above - different feed, different schema,
# informational only, no Signal/Ceiling scoring).
EVENT_WATCHER_INVESTOR_MEETS_PATH = os.path.join(EVENT_WATCHER_DIR, "meesho_investor_meets.csv")
EVENT_WATCHER_INVESTOR_MEETS_META_PATH = os.path.join(EVENT_WATCHER_DIR, "meesho_investor_meets_meta.json")
