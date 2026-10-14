"""
Backtests the strategy currently defined in generated_rules.py, using the
exit logic currently defined in generated_exit_strategy.py, over a
historical date range.

Standalone module: only depends on universe_fetcher, market_data,
generated_rules, and generated_exit_strategy - no dependency on
stock_screener.py or app.py, so this can be lifted into a separate service
later by wrapping run_backtest() in an API endpoint.

Mechanics:
- On each trading day in [start_date, end_date], evaluates every universe
  stock using only price data available up to and including that day (no
  look-ahead), via the same generated_rules.evaluate_stock() the live
  screener uses.
- On a pass, opens a flat $100 trade at the *next* trading day's open.
- Walks forward day by day (close price only, no intraday by default -
  generated_exit_strategy.py decides the exact exit condition, since it's
  generated from exit_rules.md the same way generated_rules.py is generated
  from rules.md) until generated_exit_strategy.resolve_exit() finds an exit,
  or the date range ends. This module - not the generated exit logic -
  always force-closes any still-open trade at the range's last close,
  tagged 'RangeEnd', so that fallback can never be silently missed by a
  regenerated exit strategy.
- Multiple simultaneous trades on the same symbol are allowed - every
  signal opens its own independent trade.
"""

import argparse
import datetime
import json
import os
import re
import warnings
warnings.filterwarnings("ignore")

import pandas as pd

from universe_fetcher import get_top_stocks_by_sector
from market_data import fetch_bars_batch, calculate_sector_strength, calculate_market_breadth
from backup_utils import declared_strategy_name
from stats_utils import hash_rules_content
from constants import (
    BACKTEST_CACHE_DIR,
    BACKTEST_META_PATH,
    BACKTEST_PORTFOLIO_PATH,
    BACKTEST_SUMMARY_PATH,
    BACKTEST_TRADES_PATH,
    EXIT_RULES_PATH,
    NEAR_MISSES_PATH,
    RULES_PATH,
)
import generated_rules
import generated_exit_strategy

WARMUP_DAYS = 400
MIN_HISTORY_ROWS = 60
CACHE_DIR = BACKTEST_CACHE_DIR

# Alpaca bars requests carry up to this many bars each (see
# market_data.PAGE_LIMIT), against a free-plan limit of ~190 requests/min
# that market_data paces itself to. Used only for the pre-flight estimate.
BARS_PER_REQUEST = 10000
TRADING_DAYS_PER_YEAR = 252
REQUESTS_PER_SECOND = 190 / 60


# Pre-flight check: how many stocks still need fetching and roughly how
# long a run over this date range will take, without fetching anything.
def estimate_runtime(start_date, end_date, limit_per_sector=50, warmup_days=WARMUP_DAYS):
    """Pre-flight estimate: how many universe stocks still need fetching
    from Alpaca for this date range, and a rough time range for the run.
    Does not fetch anything itself - only checks the on-disk cache and the
    (usually already-cached) universe list.

    Unlike NSE (one request per stock per calendar month), Alpaca returns
    many symbols' bars per request, so cost scales with total bars, not
    stocks x months."""
    universe = get_top_stocks_by_sector(limit_per_sector=limit_per_sector)
    fetch_from = start_date - datetime.timedelta(days=warmup_days)

    total = len(universe)
    to_fetch = sum(
        1 for symbol in universe
        if not os.path.exists(_cache_path(symbol, fetch_from, end_date))
    )

    bars_per_stock = (end_date - fetch_from).days / 365.25 * TRADING_DAYS_PER_YEAR
    requests_needed = -(-int(to_fetch * bars_per_stock) // BARS_PER_REQUEST) if to_fetch else 0
    base_seconds = requests_needed / REQUESTS_PER_SECOND

    return {
        "total_stocks": total,
        "cached_stocks": total - to_fetch,
        "to_fetch_stocks": to_fetch,
        "estimated_requests": requests_needed,
        "estimated_low_seconds": base_seconds,
        "estimated_high_seconds": base_seconds * 3,
    }


# Builds the on-disk cache filename for one symbol's fetched history over
# a given date range.
def _cache_path(symbol, from_date, to_date):
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = f"{symbol}_{from_date.isoformat()}_{to_date.isoformat()}.csv"
    return os.path.join(CACHE_DIR, key)


def _read_cached_history(cache_path):
    cached = pd.read_csv(cache_path, parse_dates=["date"], index_col="date")
    if "delivery_pct" not in cached.columns:
        cached["delivery_pct"] = float("nan")
    return cached


# Converts market_data's NSE-shaped frame to the lowercase, date-indexed
# frame every rule and exit check reads.
def _normalize_history(raw):
    """Alpaca bars are already split-adjusted (market_data requests
    adjustment="split") and carry one bar per date, so none of the NSE
    pipeline's split/bonus back-adjustment or chunk-boundary dedupe applies
    here. US exchanges publish no delivery %, so delivery_pct is NaN -
    any rule that reads it sees "unavailable", same as an old NSE cache."""
    df = raw.sort_values(by="DATE").set_index("DATE")
    df = df.rename(columns={
        "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close", "VOLUME": "volume",
    })
    df = df[["open", "high", "low", "close", "volume"]]
    df["delivery_pct"] = float("nan")
    df.index.name = "date"
    return df


# Loads the whole universe's history: cache hits from disk, everything
# else in one batched Alpaca fetch.
def load_universe_history(universe, start_date, end_date, warmup_days=WARMUP_DAYS):
    """Fetch (or load cached) history for every symbol in the universe,
    covering [start_date - warmup_days, end_date]. Historical ranges are
    immutable once in the past, so the per-symbol cache never expires.

    Symbols not yet cached are fetched together through
    market_data.fetch_bars_batch - a handful of multi-symbol requests
    rather than one staggered request per stock."""
    fetch_from = start_date - datetime.timedelta(days=warmup_days)
    data = {}
    missing = []
    for symbol in universe:
        cache_path = _cache_path(symbol, fetch_from, end_date)
        if os.path.exists(cache_path):
            data[symbol] = _read_cached_history(cache_path)
        else:
            missing.append(symbol)

    if missing:
        print(f"Fetching {len(missing)} uncached stock(s) from Alpaca ({len(data)} cached)...")
        fetched = fetch_bars_batch(
            missing, fetch_from, end_date,
            progress=lambda done, total: print(f"  fetched {done}/{total} symbols"),
        )
        for symbol, raw in fetched.items():
            df = _normalize_history(raw)
            if df.empty:
                continue
            df.to_csv(_cache_path(symbol, fetch_from, end_date))
            data[symbol] = df

    return data


# Opens a trade the day after a signal fires and resolves its exit via
# generated_exit_strategy.py, force-closing at range end if nothing fires.
def _open_and_resolve_trade(symbol, full_df, signal_day, end_date, closeness_score, active_strategy=None):
    """Enter at the next trading day's open after signal_day, then hand off
    to generated_exit_strategy.resolve_exit() to decide when to exit.

    generated_exit_strategy.py is regenerated from exit_rules.md the same
    way generated_rules.py is regenerated from rules.md - this function
    doesn't know or care what exit logic it implements (fixed SL/TP,
    trailing ATR, or anything else the user writes).

    If resolve_exit() returns None (no exit condition fired) or raises, this
    function - not the generated exit logic - force-closes the trade at the
    last available close in range, tagged 'RangeEnd'. This guarantee holds
    regardless of what exit_rules.md says, so a regenerated exit strategy
    can never accidentally leave a trade open forever.
    """
    future = full_df[(full_df.index.date > signal_day) & (full_df.index.date <= end_date)]
    if future.empty:
        return None

    entry_date = future.index[0]
    entry_price = float(future["open"].iloc[0])
    signal_history = full_df[full_df.index.date <= signal_day]

    exit_result = None
    try:
        exit_result = generated_exit_strategy.resolve_exit(entry_price, entry_date, signal_history, future)
    except Exception:
        exit_result = None

    if exit_result is not None:
        exit_date = exit_result["ExitDate"]
        exit_price = float(exit_result["ExitPrice"])
        exit_reason = exit_result["ExitReason"]
    else:
        exit_date = future.index[-1]
        exit_price = float(future["close"].iloc[-1])
        exit_reason = "RangeEnd"

    # pd.Timestamp is itself a subclass of datetime.date (via datetime.datetime),
    # so a plain isinstance check can't distinguish them - always normalize
    # through pd.Timestamp(...).date() instead, which is safe for a
    # datetime.date, a datetime.datetime, or a pd.Timestamp alike.
    exit_date = pd.Timestamp(exit_date).date()
    profit_rs = (exit_price - entry_price) / entry_price * 100  # on a flat $100 stake (ProfitRs kept as the column name the shared frontend reads; it's equivalently % return)

    return {
        "Symbol": symbol,
        "SignalDate": signal_day,
        "EntryDate": entry_date.date(),
        "EntryPrice": round(entry_price, 2),
        "ExitDate": exit_date,
        "ExitPrice": round(exit_price, 2),
        "ExitReason": exit_reason,
        "ClosenessScore": round(float(closeness_score), 2),
        "ProfitRs": round(profit_rs, 2),
        "Active Strategy": active_strategy,
    }


NEAR_MISS_HOLDING_DAYS = 20


# Strips the specific numbers out of a failure message so near-misses
# group by rule instead of each getting its own one-off label.
def _normalize_rule_label(failed_rule):
    """generated_rules.py's failure messages embed the specific value that
    failed (e.g. "RSI outside range (55-75): 76.39", "Sector rank 14 not in
    top 10") - fine for a single message, but it means every near-miss gets
    its own one-off label, so grouping "by rule" never aggregates. Strips
    all numbers to get a stable per-rule label instead (the full original
    message is kept separately as FailedRuleDetail for individual review)."""
    normalized = re.sub(r"\d+\.?\d*", "", failed_rule)
    normalized = re.sub(r"\s+", " ", normalized).strip(" :")
    return normalized or failed_rule


# What a stock did over a fixed holding period after a given day - used to
# score near-misses, since they never opened a real trade with exit logic.
def _forward_return_pct(full_df, signal_day, holding_days=NEAR_MISS_HOLDING_DAYS):
    """What a stock did after a given day, on the same next-day-open entry
    convention as a real trade - used to score near-misses (see below)
    against a fixed holding period, not the exit strategy (a near-miss
    never opened a real trade, so there's no exit logic to run)."""
    future = full_df[full_df.index.date > signal_day]
    if future.empty:
        return None

    entry_price = float(future["open"].iloc[0])
    if entry_price == 0:
        return None

    exit_row_idx = min(holding_days - 1, len(future) - 1)
    exit_price = float(future["close"].iloc[exit_row_idx])
    return (exit_price - entry_price) / entry_price * 100


# Core simulation loop: walks the date range day by day, evaluates every
# stock with the live strategy, opens trades on passes, and tracks near-misses.
def run_backtest(start_date, end_date, limit_per_sector=50, progress_callback=None):
    """Run the backtest. Returns (trades_df, summary_df, near_misses_df).

    progress_callback, if given, is called as progress_callback(done, total, day)
    once per simulated trading day.

    Exit logic comes entirely from generated_exit_strategy.py (regenerated
    from exit_rules.md) - this function doesn't take SL/TP/ATR parameters
    itself; edit exit_rules.md and regenerate to change exit behavior.

    Also tracks "near-misses": stocks that failed exactly one rule on a
    given day. For each, records what a simple NEAR_MISS_HOLDING_DAYS-day
    hold would have returned, so you can see - per rule - whether the
    stocks it's blocking tend to be worth catching (see near_misses_df,
    and the "Missed Opportunities" tab that reads it).
    """
    universe = get_top_stocks_by_sector(limit_per_sector=limit_per_sector)
    if not universe:
        raise RuntimeError("Could not build stock universe.")

    data = load_universe_history(universe, start_date, end_date)
    if not data:
        raise RuntimeError("No historical data could be fetched for any stock in the universe.")

    all_dates = sorted({
        ts.date() for df in data.values() for ts in df.index
        if start_date <= ts.date() <= end_date
    })

    # Precompute each symbol's dates as a plain list once (avoids repeated
    # `.index.date` conversion, which is the expensive part of slicing).
    symbol_dates = {symbol: df.index.date for symbol, df in data.items()}
    # Pointer into each symbol's rows: index of the last row known to be
    # available as of the current day. Advances monotonically as `day`
    # advances, so building each day's snapshot is O(stocks) instead of
    # O(stocks x rows) - the loop below never re-scans older rows.
    pos = {symbol: -1 for symbol in data}

    trades = []
    near_misses = []
    total_days = len(all_dates)

    for day_idx, day in enumerate(all_dates):
        if progress_callback:
            progress_callback(day_idx + 1, total_days, day)

        snapshot = {}
        for symbol, df in data.items():
            dates = symbol_dates[symbol]
            p = pos[symbol]
            n = len(dates)
            while p + 1 < n and dates[p + 1] <= day:
                p += 1
            pos[symbol] = p

            if p + 1 >= MIN_HISTORY_ROWS and p >= 0 and dates[p] == day:
                snapshot[symbol] = df.iloc[:p + 1]

        if not snapshot:
            continue

        sector_ranks_today = calculate_sector_strength(snapshot, universe)
        market_breadth_today = calculate_market_breadth(snapshot)

        for symbol, df_slice in snapshot.items():
            try:
                result = generated_rules.evaluate_stock(symbol, df_slice, universe, sector_ranks_today, market_breadth_today)
            except Exception:
                continue

            if not result.get("Passed"):
                failed_rules = result.get("FailedRules", [])
                if len(failed_rules) == 1:
                    forward_return = _forward_return_pct(data[symbol], day)
                    if forward_return is not None:
                        near_misses.append({
                            "Date": day,
                            "Symbol": symbol,
                            "FailedRule": _normalize_rule_label(failed_rules[0]),
                            "FailedRuleDetail": failed_rules[0],
                            "ClosenessScore": round(float(result.get("ClosenessScore", 0.0)), 2),
                            "ForwardReturnPct": round(forward_return, 2),
                        })
                continue

            trade = _open_and_resolve_trade(
                symbol, data[symbol], day, end_date, result.get("ClosenessScore", 0.0),
                active_strategy=result.get("Details", {}).get("Active Strategy"),
            )
            if trade:
                trades.append(trade)

    trade_columns = [
        "Symbol", "SignalDate", "EntryDate", "EntryPrice",
        "ExitDate", "ExitPrice", "ExitReason", "ClosenessScore", "ProfitRs",
        "Active Strategy",
    ]
    trades_df = pd.DataFrame(trades, columns=trade_columns)
    summary_df = summarize_trades(trades_df)

    near_miss_columns = ["Date", "Symbol", "FailedRule", "FailedRuleDetail", "ClosenessScore", "ForwardReturnPct"]
    near_misses_df = pd.DataFrame(near_misses, columns=near_miss_columns)

    return trades_df, summary_df, near_misses_df


# Replays run_backtest()'s trade list through a capital-constrained
# portfolio - deciding which signals actually got funded and compounding equity.
def simulate_portfolio(trades_df, initial_capital=100000.0, max_concurrent_positions=10):
    """
    Simulates a real, capital-constrained portfolio on top of the already
    fully-resolved trade list from run_backtest() (each trade's entry/exit
    dates and % return are computed independently of capital - this
    function only decides which signals the portfolio actually had room to
    fund, and compounds capital as positions open and close).

    Position sizing: each newly funded trade gets
    (current total equity) / max_concurrent_positions - an equal-weight
    slot recomputed fresh each time, so position size compounds with
    portfolio growth. When more signals fire on a day than there are free
    slots, higher ClosenessScore gets priority; the rest are marked
    unfunded (skipped for lack of capital), not opened at a smaller size.

    Returns (portfolio_df, trades_df) where portfolio_df is a chronological
    equity curve (Date, Equity) and trades_df is the input with two added
    columns: Funded (bool) and AllocatedCapital (float).
    """
    trades = trades_df.copy()
    if trades.empty:
        trades["Funded"] = pd.Series(dtype=bool)
        trades["AllocatedCapital"] = pd.Series(dtype=float)
        return pd.DataFrame(columns=["Date", "Equity"]), trades

    trades["EntryDate"] = pd.to_datetime(trades["EntryDate"])
    trades["ExitDate"] = pd.to_datetime(trades["ExitDate"])

    entries_by_date = {}
    for idx, row in trades.iterrows():
        entries_by_date.setdefault(row["EntryDate"], []).append(idx)

    cash = initial_capital
    open_positions = {}  # idx -> allocated capital
    funded = {}
    allocated = {}
    equity_curve = []

    all_dates = sorted(set(trades["EntryDate"]).union(trades["ExitDate"]))
    for date in all_dates:
        # Exits before entries on the same day, so freed capital is
        # available for same-day reinvestment.
        exits_today = trades.index[trades["ExitDate"] == date]
        for idx in exits_today:
            if funded.get(idx):
                profit_pct = trades.loc[idx, "ProfitRs"]
                cash += open_positions.pop(idx) * (1 + profit_pct / 100)

        entries_today = sorted(
            entries_by_date.get(date, []),
            key=lambda i: trades.loc[i, "ClosenessScore"],
            reverse=True,
        )
        for idx in entries_today:
            if len(open_positions) >= max_concurrent_positions:
                funded[idx] = False
                continue
            total_equity = cash + sum(open_positions.values())
            size = total_equity / max_concurrent_positions
            # Filling the last free slot leaves cash ~= size, so float
            # rounding can make size exceed cash by a hair; tolerate it.
            if size <= cash + 1e-9 * total_equity:
                size = min(size, cash)
                open_positions[idx] = size
                cash -= size
                funded[idx] = True
                allocated[idx] = size
            else:
                funded[idx] = False

        # Same-day round trips (EntryDate == ExitDate, e.g. a 1-day-hold
        # exit strategy like BTST) never hit the exits-today step above,
        # since their exit event was already checked earlier in this same
        # iteration, before the position existed - close them immediately
        # after opening instead, or their capital/slot would stay locked
        # forever and starve every later signal.
        for idx in entries_today:
            if funded.get(idx) and trades.loc[idx, "ExitDate"] == date:
                profit_pct = trades.loc[idx, "ProfitRs"]
                cash += open_positions.pop(idx) * (1 + profit_pct / 100)

        equity_curve.append({"Date": date, "Equity": cash + sum(open_positions.values())})

    trades["Funded"] = trades.index.map(lambda i: funded.get(i, False))
    trades["AllocatedCapital"] = trades.index.map(lambda i: round(allocated.get(i, 0.0), 2))
    trades["EntryDate"] = trades["EntryDate"].dt.date
    trades["ExitDate"] = trades["ExitDate"].dt.date

    portfolio_df = pd.DataFrame(equity_curve)
    return portfolio_df, trades


# Buckets trades by ClosenessScore and reports win rate/profit per bucket.
def summarize_trades(trades_df):
    """Bucket trades by ClosenessScore and report win rate / profit per bucket."""
    columns = ["ScoreBucket", "Trades", "WinRatePct", "MeanProfitRs", "MedianProfitRs", "TotalProfitRs"]
    if trades_df.empty:
        return pd.DataFrame(columns=columns)

    bins = [0, 20, 40, 60, 80, 100]
    labels = ["0-20", "20-40", "40-60", "60-80", "80-100"]
    trades_df = trades_df.copy()
    trades_df["ScoreBucket"] = pd.cut(trades_df["ClosenessScore"], bins=bins, labels=labels, include_lowest=True)

    summary = trades_df.groupby("ScoreBucket", observed=True).agg(
        Trades=("ProfitRs", "count"),
        WinRatePct=("ProfitRs", lambda s: round((s > 0).mean() * 100, 1)),
        MeanProfitRs=("ProfitRs", lambda s: round(s.mean(), 2)),
        MedianProfitRs=("ProfitRs", lambda s: round(s.median(), 2)),
        TotalProfitRs=("ProfitRs", lambda s: round(s.sum(), 2)),
    ).reset_index()

    return summary


# Parses a "YYYY-MM-DD" CLI argument into a date object.
def _parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def _read_if_exists(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


# CLI entry point: parses args, runs the backtest, simulates the portfolio,
# writes all output CSVs, and records which strategy this run belongs to.
def main():
    parser = argparse.ArgumentParser(
        description="Backtest the current generated_rules.py strategy using generated_exit_strategy.py for exits."
    )
    parser.add_argument("--start", required=True, type=_parse_date, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, type=_parse_date, help="End date YYYY-MM-DD")
    parser.add_argument("--limit-per-sector", type=int, default=50)
    parser.add_argument("--initial-capital", type=float, default=100000.0, help="Starting portfolio capital, e.g. 100000")
    parser.add_argument("--max-positions", type=int, default=10, help="Max number of concurrent open positions")
    parser.add_argument("--trades-out", default=BACKTEST_TRADES_PATH)
    parser.add_argument("--summary-out", default=BACKTEST_SUMMARY_PATH)
    parser.add_argument("--portfolio-out", default=BACKTEST_PORTFOLIO_PATH)
    parser.add_argument("--near-misses-out", default=NEAR_MISSES_PATH)
    args = parser.parse_args()

    def progress(done, total, day):
        print(f"Evaluating day {done}/{total} ({day})...")

    trades_df, summary_df, near_misses_df = run_backtest(
        args.start, args.end,
        limit_per_sector=args.limit_per_sector,
        progress_callback=progress,
    )

    portfolio_df, trades_df = simulate_portfolio(
        trades_df, initial_capital=args.initial_capital, max_concurrent_positions=args.max_positions
    )

    trades_df.to_csv(args.trades_out, index=False)
    summary_df.to_csv(args.summary_out, index=False)
    portfolio_df.to_csv(args.portfolio_out, index=False)
    near_misses_df.to_csv(args.near_misses_out, index=False)

    # Records which strategy this specific run's results belong to, at the
    # moment the backtest actually ran - NOT re-read from rules.md later,
    # since rules.md can be swapped to a different strategy afterward
    # (e.g. via the "Load a previous strategy" modal) without a new
    # backtest being run. The Stats tab must attribute these numbers to
    # the strategy that produced them, not to whatever happens to be
    # loaded in rules.md when it's later viewed.
    # rules.md / exit_rules.md are gitignored per-user files, so a fresh
    # checkout may not have them; record an empty name rather than crash
    # after the whole backtest has already run.
    with open(BACKTEST_META_PATH, "w", encoding="utf-8") as f:
        rules_content = _read_if_exists(RULES_PATH)
        json.dump({
            "strategy_name": declared_strategy_name(rules_content),
            "rules_content_hash": hash_rules_content(rules_content),
            "exit_strategy_name": declared_strategy_name(
                _read_if_exists(EXIT_RULES_PATH), name_field="Exit Strategy Name"
            ),
            "initial_capital": args.initial_capital,
            "start_date": args.start.isoformat(),
            "end_date": args.end.isoformat(),
        }, f)

    print(f"\n{len(trades_df)} trades simulated.")
    print(summary_df.to_string(index=False))
    print(f"\n{len(near_misses_df)} near-misses recorded (stocks that failed exactly one rule).")

    if not portfolio_df.empty:
        final_equity = portfolio_df["Equity"].iloc[-1]
        total_return_pct = (final_equity - args.initial_capital) / args.initial_capital * 100
        funded_count = int(trades_df["Funded"].sum())
        skipped_count = len(trades_df) - funded_count
        print(f"\n--- PORTFOLIO ({args.max_positions} concurrent slots, ${args.initial_capital:,.0f} start) ---")
        print(f"Funded trades: {funded_count} (skipped for lack of capital: {skipped_count})")
        print(f"Final equity: ${final_equity:,.2f}")
        print(f"Total return: {total_return_pct:.2f}%")

    print(f"\nTrades saved to {args.trades_out}")
    print(f"Summary saved to {args.summary_out}")
    print(f"Portfolio equity curve saved to {args.portfolio_out}")
    print(f"Near-misses saved to {args.near_misses_out}")


if __name__ == "__main__":
    main()
