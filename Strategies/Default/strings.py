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
    "in data/backtest_cache/; later runs over the same range reuse that cache "
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

NIFTY_COMPARISON_HELP = (
    "Overlays what your starting capital would be worth spread equally "
    "across the Nifty 50 constituents over the same period - a buy-and-hold "
    "benchmark to judge whether the strategy actually beat just holding the "
    "index."
)

NIFTY_COMPARISON_CAPTION = (
    "NSE's official index-history data isn't reachable from here, so this "
    "is an equal-weighted proxy built from the 50 constituent stocks' own "
    "daily closes, not the real weighted Nifty 50 index level - directionally "
    "representative, not exact."
)

NIFTY_FETCH_ERROR = (
    "Couldn't build the Nifty 50 comparison (constituent list or price data "
    "unavailable) - showing your portfolio only."
)

MAX_DRAWDOWN_HELP = (
    "Largest peak-to-trough drop in equity during the run. A high CAGR next "
    "to a deep drawdown means the return came with real pain along the way, "
    "not steady compounding."
)

SHARPE_RATIO_HELP = (
    "Return per unit of volatility, annualized from daily equity changes "
    "(assumes a 0% risk-free rate, since no risk-free rate data is "
    "available here). Higher means steadier gains, not just bigger ones."
)

COMPOSITE_SCORE_HELP = (
    "(CAGR x Sharpe) / |Max Drawdown| - a single number that rewards high, "
    "steady returns and penalizes deep drawdowns, so two runs with similar "
    "CAGR but very different risk profiles don't look equally good. Useful "
    "for ranking strategy variants against each other, not as a "
    "standalone target."
)

YEARLY_BREAKDOWN_CAPTION = (
    "A single CAGR over a multi-year range can hide a lot - a return "
    "dominated by one exceptional year looks the same in that headline "
    "number as one built from steady, repeatable years. Check here before "
    "trusting the CAGR above as a forward expectation. For an interactive "
    "version - toggle years on/off and see the CAGR recompute live - see "
    "the **Deep Dive** tab."
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
    "run the check. Holdings are saved to data/holdings.csv as you edit, so "
    "they persist across sessions - remove a row once you've sold that "
    "position."
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

NEAR_MISS_HOLDING_DAYS = 20

MISSED_OPPORTUNITIES_CAPTION = (
    "Every day the backtest evaluates a stock, a stock that fails exactly "
    "one rule is logged as a near-miss along with what a simple "
    f"{NEAR_MISS_HOLDING_DAYS}-trading-day hold from the next day's open "
    "would have returned. This is not a trade the strategy took - it's "
    "what the rule that blocked it cost you, so you can see which filters "
    "are worth loosening instead of guessing."
)

NO_NEAR_MISSES_INFO = (
    "No near-miss data yet. Run a backtest from the Backtest tab first - "
    "near_misses.csv is written alongside the trade results."
)

RULE_BREAKDOWN_CAPTION = (
    "Sorted by average forward return, highest first. A rule near the top "
    "with a return and win rate clearly better than your realized trades "
    "is likely too tight - try loosening its threshold in rules.md and "
    "rerunning the backtest to confirm."
)

TOP_NEAR_MISSES_CAPTION = (
    "The single biggest near-misses across all rules - concrete examples "
    "of what got away, not just the aggregate stats above."
)

DEEP_DIVE_CAPTION = (
    "A single CAGR over a multi-year backtest can be carried almost "
    "entirely by one unusually strong (or weak) year. Uncheck a year "
    "below to see what the CAGR looks like without it - if the number "
    "swings wildly, that year is doing most of the work."
)

DEEP_DIVE_NO_DATA_INFO = (
    "No backtest data yet. Run a backtest from the Backtest tab first."
)

DEEP_DIVE_NOT_ENOUGH_YEARS_INFO = (
    "This backtest only spans one calendar year - there's nothing to "
    "compare yet. Run a longer backtest to use this page."
)

DEEP_DIVE_ALL_YEARS_CAPTION = (
    "All years are currently selected, so both columns match. Uncheck a "
    "year above to see the difference."
)

DEEP_DIVE_NO_YEARS_SELECTED_CAPTION = "Select at least one year to see its stats."

DEEP_DIVE_STITCHED_CHART_CAPTION = (
    "The equity curve for just the years you selected, stitched together "
    "in order (each year picks up where the last one left off) - not the "
    "same as re-running the backtest on only those years, but shows the "
    "real ups and downs within each included year rather than a straight "
    "line between yearly totals."
)

RETURN_TO_PAIN_HELP = (
    "CAGR divided by the worst drawdown you experienced - in plain terms, "
    "how much yearly return you got for every 1% of the deepest dip along "
    "the way. Higher is better: a low ratio means the return came with a "
    "rough, high-pain ride even if the headline CAGR looks good."
)

DEEP_DIVE_PARTIAL_YEAR_HELP = (
    "Your selection covers less than a full year, so this CAGR is an "
    "extrapolation - it takes the actual return over those few months and "
    "projects what it would look like if that same rate held for a full "
    "year. It is NOT a measured annual rate, and can look much larger (or "
    "smaller) than the plain, non-annualized return shown on the Backtest "
    "tab's Year-by-year breakdown for the same period."
)

DEEP_DIVE_PARTIAL_YEAR_CAPTION = (
    "This covers only ~{months:.1f} months of data - the CAGR above is "
    "extrapolated from a partial year, not a real measured annual rate. "
    "Treat it as a rough projection, not a reliable figure."
)
