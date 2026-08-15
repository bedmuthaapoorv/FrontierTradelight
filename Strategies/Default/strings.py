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

CHART_DRILLDOWN_HINT = (
    "Drag across the chart to select a date range and see exactly which "
    "trades were active during it."
)

SELL_TAB_CAPTION = (
    "Runs the exit logic in generated_exit_strategy.py against the stocks "
    "you currently hold, using live price data - the sell-side mirror of "
    "the Run tab's screener. For each holding, checks whether your exit "
    "strategy would already have fired between your entry date and today."
)

HOLDINGS_EDITOR_CAPTION = (
    "Add each open position below (symbol, entry price, entry date), then "
    "run the check. Holdings are saved to holdings.csv as you edit, so they "
    "persist across sessions - remove a row once you've sold that position."
)

NO_HOLDINGS_CAPTION = "Add at least one holding above before checking exit signals."

BACKTEST_STOPPED_WARNING = (
    "Backtest stopped. Partial progress is lost — results/CSVs are only "
    "written when a run finishes."
)

COMPARE_RISK_SIZING_HELP = (
    "After the equal-weight run finishes, re-simulates portfolio sizing on "
    "the identical trade list using half-Kelly risk-based sizing (portfolio/"
    "sector heat caps, volatility and market-breadth adjustment, a Monte "
    "Carlo-calibrated drawdown throttle) instead of an equal slot per "
    "position. Cheap - it reuses the same signals, only sizing differs. "
    "Results appear in the Risk tab."
)

RISK_PARAMS_CAPTION = (
    "Half-Kelly cap: hard ceiling on risk % per trade even if the Kelly "
    "formula (from win rate and average R-multiple of past closed trades) "
    "implies more. Heat caps: total capital-at-risk (to each open "
    "position's initial stop) allowed at once, portfolio-wide and per "
    "sector - a new trade that would breach either is sized down to fit "
    "rather than skipped. Monte Carlo: bootstraps past trades' R-multiples "
    "into synthetic equity paths to calibrate drawdown throttle bands and "
    "estimate risk of ruin."
)

VAR_SECTION_CAPTION = (
    "Value at Risk (VaR): the loss a trade won't exceed with X% confidence, "
    "built from the actual entry-to-exit % return of every historical "
    "trade this strategy has taken (regardless of whether capital was "
    "available to fund it - this measures the asset/strategy's own return "
    "behavior, not the sizing engine). CVaR (shown alongside, in the "
    "tooltip) is the average loss in the worst-case tail beyond VaR - a "
    "harsher number, since VaR alone says nothing about how bad things get "
    "past that threshold."
)

VAR_METHOD_HELP = (
    "Historical (default): uses the actual historical trade returns "
    "directly - no resampling, exactly what happened. Simple and "
    "transparent, but the tail percentile is noisy with few trades. "
    "Monte Carlo: bootstrap-resamples those same historical returns "
    "thousands of times (optionally compounding several trades per "
    "simulated path via the horizon control) to smooth out that sampling "
    "noise and estimate risk over a multi-trade horizon."
)

VAR_BY_ASSET_CAPTION = (
    "Only shown for symbols with enough closed trades for a meaningful "
    "percentile estimate. Rs figures use each symbol's own average funded "
    "position size where available."
)

RISK_TAB_CAPTION = (
    "Compares the same trade signals under two sizing regimes: the "
    "original equal-weight split per position slot, versus half-Kelly "
    "risk-based sizing with portfolio/sector heat caps, a volatility-ratio "
    "and market-breadth adjustment, and a Monte Carlo-calibrated drawdown "
    "throttle. Run a backtest from the Backtest tab with \"Also compare "
    "with risk-based sizing\" checked to populate this."
)
