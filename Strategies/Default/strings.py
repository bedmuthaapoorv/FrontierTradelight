"""Longer UI copy for app.py, kept here so app.py stays focused on layout/logic."""

APP_DESCRIPTION = (
    "AI-assisted swing-trading screener and backtester for NSE (India) stocks. "
    "Describe your entry and exit strategy in plain English, which then screens "
    "live data and backtests historical performance across custom date range, "
    "all locally."
)

NO_RULES_BACKUPS_CAPTION = (
    "No backups yet. Backups are created automatically whenever you save a "
    "changed rules.md."
)

GENERATE_SCREENER_CAPTION = (
    "Reads rules.md, calls Gemini, writes generated_rules.py. Requires "
    "GEMINI_API_KEY in .env."
)

RUN_SCREENER_CAPTION = (
    "Fetches the stock universe and price history, scores each stock, writes "
    "stock_report.csv."
)

BACKTEST_TAB_CAPTION = (
    "Simulates generated_rules.py over a historical date range using the exit "
    "logic in generated_exit_strategy.py. On each signal, opens a flat Rs.100 "
    "trade at the next trading day's open, holds until your exit strategy "
    "triggers, or force-exits at the range's last close if it never does."
)

EXIT_STRATEGY_ELSEWHERE_CAPTION = (
    "Edit exit_rules.md from the Sell tab - it drives both this backtest "
    "and the live holdings check, and editing it there keeps it next to "
    "the decision it's actually used for."
)

EXIT_STRATEGY_CAPTION = (
    "Define your exit strategy in exit_rules.md, then generate it - the same "
    "way rules.md drives generated_rules.py. Write your own logic here (fixed "
    "SL/TP, trailing ATR, time-based, anything computable from OHLCV) instead "
    "of picking from a fixed list of built-in options."
)

NO_EXIT_BACKUPS_CAPTION = (
    "No backups yet. Backups are created automatically whenever you save a "
    "changed exit_rules.md."
)

POSITION_SLOTS_CAPTION = (
    "Signals compete for a fixed number of position slots, sized as an equal "
    "share of current total equity (so position size compounds with growth). "
    "When more signals fire on a day than there are free slots, the highest "
    "ClosenessScore gets priority; the rest are skipped for lack of capital, "
    "not opened at a smaller size."
)

CACHE_CAPTION = (
    "First run for a given date range fetches history from NSE and caches it "
    "in backtest_cache/; later runs over the same range reuse that cache "
    "regardless of exit strategy changes."
)

CAGR_HELP = (
    "Compound annual growth rate - the total return spread evenly across "
    "years, so it's comparable to things like FD/index annual returns rather "
    "than a lump 3-year figure."
)

INFLATION_ADJUSTED_HELP = (
    "Deflates the equity curve using India's actual annual CPI inflation "
    "rate (World Bank data) for each calendar year the backtest spans - "
    "shows what your returns are worth in today's purchasing power, not "
    "just nominal rupees."
)

INFLATION_FETCH_ERROR = (
    "Couldn't fetch India's CPI inflation data from the World Bank API "
    "(no internet access, or the request failed) - showing nominal "
    "results only."
)

MAX_DRAWDOWN_HELP = (
    "Largest peak-to-trough drop in equity during the run. A high CAGR next "
    "to a deep drawdown means the return came with real pain along the way, "
    "not steady compounding."
)

YEARLY_BREAKDOWN_CAPTION = (
    "A single CAGR over a multi-year range can hide a lot - a return "
    "dominated by one exceptional year looks the same in that headline "
    "number as one built from steady, repeatable years. Check here before "
    "trusting the CAGR above as a forward expectation."
)

SELL_TAB_CAPTION = (
    "Runs the exit logic in generated_exit_strategy.py against the stocks "
    "you currently hold - the sell-side mirror of the Run tab's screener. "
    "For each holding, checks whether your exit strategy would already "
    "have fired between your entry date and today. Price history comes "
    "from NSE's own data feed, which only has up to yesterday's official "
    "close available (no live/intraday feed) - fill in Current Price below "
    "per holding to check against today's live price instead."
)

HOLDINGS_EDITOR_CAPTION = (
    "Add each open position below (symbol, entry price, entry date), then "
    "run the check. Holdings are saved to holdings.csv as you edit, so they "
    "persist across sessions - remove a row once you've sold that position."
)

NO_HOLDINGS_CAPTION = "Add at least one holding above before checking exit signals."

CURRENT_PRICE_HELP = (
    "Optional. NSE's own data feed only has yesterday's close available "
    "(see the caption above) - paste today's LTP from your broker app here "
    "to fold in a live price instead. Leave blank to fall back to the last "
    "published close."
)

BACKTEST_STOPPED_WARNING = (
    "Backtest stopped. Partial progress is lost — results/CSVs are only "
    "written when a run finishes."
)
