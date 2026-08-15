"""
Backtests the strategy currently defined in generated_rules.py, using the
exit logic currently defined in generated_exit_strategy.py, over a
historical date range.

Standalone module: only depends on universe_fetcher, nse_utils,
generated_rules, and generated_exit_strategy - no dependency on
stock_screener.py or app.py, so this can be lifted into a separate service
later by wrapping run_backtest() in an API endpoint.

Mechanics:
- On each trading day in [start_date, end_date], evaluates every universe
  stock using only price data available up to and including that day (no
  look-ahead), via the same generated_rules.evaluate_stock() the live
  screener uses.
- On a pass, opens a flat Rs.100 trade at the *next* trading day's open.
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
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

from universe_fetcher import get_top_stocks_by_sector
from nse_utils import fetch_stock_history, calculate_sector_strength, calculate_market_breadth, calculate_atr_stats
import generated_rules
import generated_exit_strategy

WARMUP_DAYS = 400
MIN_HISTORY_ROWS = 60
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backtest_cache")

# jugaad-data (via NSE's historical API) chunks each stock's fetch into one
# request per calendar month, and further parallelizes those chunks
# internally with its own 2-worker pool. load_universe_history additionally
# fetches FETCH_WORKERS stocks concurrently on top of that, so effective
# concurrency is FETCH_WORKERS x 2 simultaneous NSE requests. Kept
# deliberately modest (not higher) to stay well under NSE's bot-detection
# rate limiting for large multi-year backtests - see STAGGER_SECONDS below
# for the other half of that mitigation.
FETCH_WORKERS = 3
SECONDS_PER_CHUNK = 1.5
EFFECTIVE_CONCURRENCY = FETCH_WORKERS * 2

# Small random delay before each stock's fetch starts, so a 50-stock
# universe doesn't all fire its first request in the same instant (bursty
# request patterns are what typically trips bot-detection rate limits, more
# than the sustained concurrency level itself).
STAGGER_SECONDS = (0.3, 1.2)


def _month_span(from_date, to_date):
    return (to_date.year - from_date.year) * 12 + (to_date.month - from_date.month) + 1


def estimate_runtime(start_date, end_date, limit_per_sector=50, warmup_days=WARMUP_DAYS):
    """Pre-flight estimate: how many universe stocks still need fetching from
    NSE for this date range, and a rough time range for the run. Does not
    fetch anything itself - only checks the on-disk cache and the (usually
    already-cached) universe list.

    Long ranges cost more than short ones even per-stock, since NSE's API is
    paginated by calendar month under the hood - a 5-year range issues ~60+
    monthly requests per stock, not one."""
    universe = get_top_stocks_by_sector(limit_per_sector=limit_per_sector)
    fetch_from = start_date - datetime.timedelta(days=warmup_days)

    total = len(universe)
    to_fetch = sum(
        1 for symbol in universe
        if not os.path.exists(_cache_path(symbol, fetch_from, end_date))
    )

    chunks_per_stock = _month_span(fetch_from, end_date)
    total_chunk_requests = to_fetch * chunks_per_stock
    base_seconds = (total_chunk_requests * SECONDS_PER_CHUNK) / EFFECTIVE_CONCURRENCY

    return {
        "total_stocks": total,
        "cached_stocks": total - to_fetch,
        "to_fetch_stocks": to_fetch,
        "months_per_stock": chunks_per_stock,
        "estimated_low_seconds": base_seconds,
        "estimated_high_seconds": base_seconds * 3,
    }


def _cache_path(symbol, from_date, to_date):
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = f"{symbol}_{from_date.isoformat()}_{to_date.isoformat()}.csv"
    return os.path.join(CACHE_DIR, key)


def _dedupe_same_day_rows(df):
    """jugaad-data's underlying NSE source occasionally returns two rows for
    the same calendar date at a chunk boundary: one genuine OHLCV bar (real
    high != low) and one degenerate settlement-price-only placeholder bar
    (open == high == low == close). Keep the genuine bar; drop the
    placeholder. Left undeduped, a duplicate index corrupts every rolling
    window (RSI/ATR/MA) computed over the series from that point forward."""
    if not df.index.duplicated(keep=False).any():
        return df

    is_placeholder = (df["open"] == df["high"]) & (df["high"] == df["low"]) & (df["low"] == df["close"])
    # Sort so within each duplicate date, real bars (is_placeholder=False)
    # sort before placeholders, then keep the first (real) row per date.
    df = df.assign(_placeholder=is_placeholder).sort_values(["date", "_placeholder"])
    df = df[~df.index.duplicated(keep="first")].drop(columns="_placeholder")
    return df.sort_index()


def _adjust_for_splits_and_bonuses(df, threshold=0.65):
    """Detect and back-adjust for unadjusted stock splits / bonus issues.

    The NSE history this pipeline fetches is NOT split/bonus-adjusted - a
    split shows up as a genuine ~50-90% overnight drop in the raw close
    price with no corresponding move in the stock's actual value. Left as
    -is, this reads as a catastrophic single-day crash to every rule and
    exit condition (RSI, ATR, trailing stops), fabricating impossible
    losses that never happened to a real position.

    Detects a day-over-day close ratio outside [threshold, 1/threshold]
    (i.e. more than a ~35% move in either direction - far past any
    realistic single-day move for a Nifty-adjacent large-cap without a
    circuit-breaker halt) and back-adjusts every prior row's OHLC by that
    ratio (and volume inversely), the same technique used to build a
    standard split-adjusted price series.
    """
    close = df["close"].values
    ratios = close[1:] / close[:-1]
    split_idxs = [i + 1 for i, r in enumerate(ratios) if r < threshold or r > 1 / threshold]
    if not split_idxs:
        return df

    df = df.copy()
    df["volume"] = df["volume"].astype(float)
    for idx in split_idxs:
        factor = df["close"].iloc[idx] / df["close"].iloc[idx - 1]
        price_cols = ["open", "high", "low", "close"]
        df.iloc[:idx, df.columns.get_indexer(price_cols)] *= factor
        df.iloc[:idx, df.columns.get_loc("volume")] /= factor
    return df


def _load_symbol_history(symbol, from_date, to_date):
    """Fetch (or load cached) daily history for a symbol, normalized to
    lowercase OHLCV columns indexed by date, ascending, deduplicated, and
    split/bonus-adjusted. Historical ranges are immutable once in the past,
    so this cache never expires."""
    cache_path = _cache_path(symbol, from_date, to_date)
    if os.path.exists(cache_path):
        return pd.read_csv(cache_path, parse_dates=["date"], index_col="date")

    # Only stagger actual network fetches, not cache hits - avoids a
    # thundering-herd burst of requests when many symbols need fetching.
    time.sleep(random.uniform(*STAGGER_SECONDS))

    df = fetch_stock_history(symbol=symbol, from_date=from_date, to_date=to_date, series="EQ")
    if df is None or df.empty:
        return None

    df = df.sort_values(by="DATE").set_index("DATE")
    df = df.rename(columns={
        "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close", "VOLUME": "volume",
    })
    df = df[["open", "high", "low", "close", "volume"]]
    df.index.name = "date"

    df = _dedupe_same_day_rows(df)
    df = _adjust_for_splits_and_bonuses(df)

    df.to_csv(cache_path)
    return df


def load_universe_history(universe, start_date, end_date, warmup_days=WARMUP_DAYS, max_workers=FETCH_WORKERS):
    """Fetch (or load cached) history for every symbol in the universe,
    covering [start_date - warmup_days, end_date]. Fetches concurrently
    (matching universe_fetcher.py's worker count) since each symbol is an
    independent NSE request - this is the main lever on wall-clock fetch
    time for long date ranges."""
    fetch_from = start_date - datetime.timedelta(days=warmup_days)
    data = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(_load_symbol_history, symbol, fetch_from, end_date): symbol
            for symbol in universe
        }
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                df = future.result()
            except Exception:
                df = None
            if df is not None and not df.empty:
                data[symbol] = df
    return data


def _open_and_resolve_trade(symbol, full_df, signal_day, end_date, closeness_score,
                             sector=None, market_breadth=None, atr_stats=None):
    """Enter at the next trading day's open after signal_day, then hand off
    to generated_exit_strategy.resolve_exit() to decide when to exit.

    generated_exit_strategy.py is regenerated from exit_rules.md the same
    way generated_rules.py is regenerated from rules.md - this function
    doesn't know or care what exit logic it implements (fixed SL/TP,
    trailing ATR, or anything else the user writes). Its Return Contract
    (see exit_rules.md) requires it to always return InitialSL when
    computable, even if no exit condition fires - only returning None when
    the entry-time risk calc itself can't be computed, which this function
    treats as "don't open this trade" (no stop-loss means no risk basis to
    size or evaluate the trade against).

    If resolve_exit() returns a dict with no exit date (data ran out before
    any exit condition fired) or raises, this function - not the generated
    exit logic - force-closes the trade at the last available close in
    range, tagged 'RangeEnd'. This guarantee holds regardless of what
    exit_rules.md says, so a regenerated exit strategy can never
    accidentally leave a trade open forever.
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

    if exit_result is None:
        # Entry-time risk calc (e.g. ATR-based initial stop) couldn't be
        # computed - no risk basis to open or size this trade against.
        return None

    initial_sl = exit_result.get("InitialSL")

    if exit_result.get("ExitDate") is not None:
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
    profit_rs = (exit_price - entry_price) / entry_price * 100  # on a flat Rs.100 stake

    # R-multiple: return expressed in units of the initial risk taken (the
    # gap between entry and the initial stop-loss), not just raw % return -
    # this is what the risk-sizing engine's Kelly stats are computed from.
    risk_per_share = entry_price - initial_sl if initial_sl is not None else None
    if risk_per_share is not None and risk_per_share > 0:
        r_multiple = (exit_price - entry_price) / risk_per_share
    else:
        r_multiple = float("nan")

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
        "InitialSL": round(float(initial_sl), 2) if initial_sl is not None else None,
        "RMultiple": round(r_multiple, 3) if pd.notna(r_multiple) else None,
        "Sector": sector,
        "MarketBreadthAtEntry": round(float(market_breadth), 1) if market_breadth is not None else None,
        "ATR_Entry": round(float(atr_stats["ATR"]), 3) if atr_stats and pd.notna(atr_stats.get("ATR")) else None,
        "ATR_Avg60": round(float(atr_stats["ATR_Avg60"]), 3) if atr_stats and pd.notna(atr_stats.get("ATR_Avg60")) else None,
    }


def load_price_data(start_date, end_date, limit_per_sector=50):
    """Fetch (or load from cache) the universe and its OHLCV history for
    [start_date, end_date] - the same first two steps run_backtest() does,
    factored out so a second sizing-mode comparison run (see
    compare_sizing_modes() / main()'s --trades-in) can reuse an already
    -resolved trade list without re-running the expensive day-by-day
    signal-evaluation loop, while still getting fresh price_data for
    mark-to-market (itself cheap, since load_universe_history hits the
    on-disk cache for any range already fetched)."""
    universe = get_top_stocks_by_sector(limit_per_sector=limit_per_sector)
    if not universe:
        raise RuntimeError("Could not build stock universe.")

    data = load_universe_history(universe, start_date, end_date)
    if not data:
        raise RuntimeError("No historical data could be fetched for any stock in the universe.")

    return universe, data


def run_backtest(start_date, end_date, limit_per_sector=50, progress_callback=None):
    """Run the backtest. Returns (trades_df, summary_df, price_data), where
    price_data is the symbol -> OHLCV DataFrame dict used to generate the
    signals - simulate_portfolio() needs it to revalue open positions
    day-by-day for a true mark-to-market equity curve.

    progress_callback, if given, is called as progress_callback(done, total, day)
    once per simulated trading day.

    Exit logic comes entirely from generated_exit_strategy.py (regenerated
    from exit_rules.md) - this function doesn't take SL/TP/ATR parameters
    itself; edit exit_rules.md and regenerate to change exit behavior.
    """
    universe, data = load_price_data(start_date, end_date, limit_per_sector=limit_per_sector)

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
                continue

            atr_stats = calculate_atr_stats(df_slice)
            trade = _open_and_resolve_trade(
                symbol, data[symbol], day, end_date, result.get("ClosenessScore", 0.0),
                sector=universe.get(symbol, {}).get("Sector"),
                market_breadth=market_breadth_today,
                atr_stats=atr_stats,
            )
            if trade:
                trades.append(trade)

    trade_columns = [
        "Symbol", "SignalDate", "EntryDate", "EntryPrice",
        "ExitDate", "ExitPrice", "ExitReason", "ClosenessScore", "ProfitRs",
        "InitialSL", "RMultiple", "Sector", "MarketBreadthAtEntry", "ATR_Entry", "ATR_Avg60",
    ]
    trades_df = pd.DataFrame(trades, columns=trade_columns)
    summary_df = summarize_trades(trades_df)
    return trades_df, summary_df, data


def kelly_stats(r_multiples):
    """Raw Kelly inputs and the resulting (unclipped, possibly negative)
    Kelly fraction from a set of closed trades' R-multiples:

        W  = win rate
        b  = avg win R / avg loss R   (payoff ratio)
        f* = W - (1-W)/b              (Kelly criterion)

    Returned unclipped on purpose - a negative f* is the meaningful signal
    that the sample shows no edge, which the sizing path floors away but
    the UI needs to be able to report honestly. Returns None for the
    derived fields when they aren't computable (empty sample, or no wins /
    no losses yet so b is undefined).
    """
    valid = [r for r in r_multiples if r is not None and pd.notna(r)]
    out = {
        "sample_size": len(valid), "win_rate": None, "avg_win_r": None,
        "avg_loss_r": None, "payoff_ratio": None, "kelly_fraction": None,
    }
    if not valid:
        return out

    wins = [r for r in valid if r > 0]
    losses = [abs(r) for r in valid if r <= 0]
    out["win_rate"] = len(wins) / len(valid)
    if not wins or not losses:
        return out

    avg_win_r = sum(wins) / len(wins)
    avg_loss_r = sum(losses) / len(losses)
    out["avg_win_r"], out["avg_loss_r"] = avg_win_r, avg_loss_r
    if avg_loss_r <= 0:
        return out

    payoff_ratio = avg_win_r / avg_loss_r
    out["payoff_ratio"] = payoff_ratio
    out["kelly_fraction"] = out["win_rate"] - (1 - out["win_rate"]) / payoff_ratio
    return out


def _kelly_base_risk_pct(closed_r_multiples, min_trades_for_kelly, default_risk_pct, half_kelly_cap_pct):
    """Half-Kelly base risk % from a walk-forward set of closed trades'
    R-multiples (return per trade expressed in units of initial risk taken).

    base_risk_pct = clip(0.5 * f* * 100, 0, half_kelly_cap_pct), with f*
    from kelly_stats().

    Falls back to a flat default_risk_pct (rather than 0, so both sizing
    modes stay comparable across the same date range) when: too few closed
    trades exist yet to estimate W/b reliably, there are no wins or no
    losses yet (b undefined), or the estimated edge is non-positive
    (f* <= 0).
    """
    stats = kelly_stats(closed_r_multiples)
    if stats["sample_size"] < min_trades_for_kelly:
        return default_risk_pct

    kelly_fraction = stats["kelly_fraction"]
    if kelly_fraction is None or kelly_fraction <= 0:
        return default_risk_pct

    return float(min(0.5 * kelly_fraction * 100, half_kelly_cap_pct))


def run_monte_carlo(r_multiples, base_risk_pct=1.0, n_simulations=2000, ruin_threshold_pct=-50.0,
                     path_length=None, seed=None):
    """Bootstrap-resample historical trade R-multiples (with replacement) to
    build a distribution of synthetic equity paths, all sized at a constant
    base_risk_pct per trade and assumed sequential (not modeling true
    concurrency - a known v1 simplification). Used for two things computed
    from the same resampled paths:

    - Drawdown calibration bands (P10/P50/P90 of each path's max drawdown %)
      that the live drawdown throttle compares the realized equity curve
      against.
    - Risk of ruin: the fraction of paths whose equity ever falls below
      (1 + ruin_threshold_pct/100) of the starting value.

    Returns {"drawdown_p10", "drawdown_p50", "drawdown_p90" (all positive
    magnitudes, %), "risk_of_ruin_pct"}. All zero if there's no valid
    R-multiple history to resample from.
    """
    r = np.array([x for x in r_multiples if x is not None and pd.notna(x)], dtype=float)
    if len(r) == 0:
        return {"drawdown_p10": 0.0, "drawdown_p50": 0.0, "drawdown_p90": 0.0, "risk_of_ruin_pct": 0.0}

    rng = np.random.default_rng(seed)
    n = path_length or len(r)
    ruin_level = 1 + ruin_threshold_pct / 100
    max_drawdowns = np.empty(n_simulations)
    ruin_count = 0

    for i in range(n_simulations):
        sample = rng.choice(r, size=n, replace=True)
        equity_path = np.cumprod(1 + (base_risk_pct / 100) * sample)
        running_peak = np.maximum.accumulate(np.concatenate(([1.0], equity_path)))[1:]
        drawdowns = (equity_path - running_peak) / running_peak
        max_drawdowns[i] = abs(drawdowns.min()) * 100
        if (equity_path <= ruin_level).any():
            ruin_count += 1

    return {
        "drawdown_p10": float(np.percentile(max_drawdowns, 10)),
        "drawdown_p50": float(np.percentile(max_drawdowns, 50)),
        "drawdown_p90": float(np.percentile(max_drawdowns, 90)),
        "risk_of_ruin_pct": ruin_count / n_simulations * 100,
    }


def calculate_var(returns_pct, confidence=0.95, method="historical", n_simulations=2000,
                   horizon_trades=1, seed=None):
    """Value at Risk (and Conditional VaR / Expected Shortfall) from the
    historical distribution of a trade's own realized entry-to-exit % return
    (ProfitRs - "the historical data of the return made on the entry and
    the exit", per trade).

    VaR_pct at confidence C is the loss threshold such that C% of
    historical outcomes were no worse than it - i.e. -1x the (1-C)
    percentile of the return distribution. CVaR_pct (Expected Shortfall) is
    the average loss *conditional on* being in that worst (1-C)% tail - a
    harsher, and more informative, number than VaR alone since VaR itself
    says nothing about how bad the tail beyond it gets.

    method="historical" (default): classic historical simulation - use the
    actual realized returns directly, no resampling. Only as reliable as
    the sample is large; with few trades the tail percentile is noisy.

    method="monte_carlo": bootstrap-resample the same historical returns
    (with replacement) into n_simulations synthetic sequences of
    horizon_trades trades each, compounded - smooths historical sampling
    noise and extends to a multi-trade horizon (horizon_trades > 1) rather
    than being limited to whatever single-trade outcomes actually occurred.
    With horizon_trades=1 this converges to the historical method's number
    as n_simulations grows, just resampled.

    Returns {"VaR_pct", "CVaR_pct", "sample_size"} - both nan if there's no
    usable return history.
    """
    valid = np.array([r for r in returns_pct if r is not None and pd.notna(r)], dtype=float)
    if len(valid) == 0:
        return {"VaR_pct": float("nan"), "CVaR_pct": float("nan"), "sample_size": 0}

    alpha = 1 - confidence

    if method == "monte_carlo":
        rng = np.random.default_rng(seed)
        samples = rng.choice(valid, size=(n_simulations, horizon_trades), replace=True)
        outcome_pct = (np.prod(1 + samples / 100, axis=1) - 1) * 100
    else:
        outcome_pct = valid

    threshold = np.percentile(outcome_pct, alpha * 100)
    var_pct = max(-float(threshold), 0.0)

    tail = outcome_pct[outcome_pct <= threshold]
    cvar_pct = max(-float(tail.mean()), 0.0) if len(tail) > 0 else var_pct

    return {"VaR_pct": var_pct, "CVaR_pct": cvar_pct, "sample_size": int(len(valid))}


def compute_var_report(trades_df, portfolio_equity, confidence_levels=(0.95, 0.99), method="historical",
                        n_simulations=2000, horizon_trades=1, min_trades_per_symbol=5, seed=None):
    """VaR/CVaR at the portfolio level (every trade's own ProfitRs, i.e. the
    strategy's overall entry-to-exit return distribution - unweighted by
    whether capital was actually available to fund it, since this measures
    the asset/strategy's inherent risk, not the sizing engine's behavior)
    and per-symbol (only for symbols with at least min_trades_per_symbol
    trades - the percentile of a handful of trades isn't meaningful).

    Rs amounts translate the portfolio-level % into money using
    portfolio_equity (what's actually at stake), and the per-symbol %
    into money using that symbol's own average AllocatedCapital where
    available (i.e. only from trades that were actually funded).

    Returns {"portfolio": {"95": {...}, "99": {...}}, "by_symbol": DataFrame,
    "method", "horizon_trades"}.
    """
    portfolio_var = {}
    for conf in confidence_levels:
        stats = calculate_var(
            trades_df["ProfitRs"].tolist(), confidence=conf, method=method,
            n_simulations=n_simulations, horizon_trades=horizon_trades, seed=seed,
        )
        key = f"{conf * 100:.0f}"
        portfolio_var[key] = {
            **stats,
            "VaR_rs": round(stats["VaR_pct"] / 100 * portfolio_equity, 2) if pd.notna(stats["VaR_pct"]) else None,
            "CVaR_rs": round(stats["CVaR_pct"] / 100 * portfolio_equity, 2) if pd.notna(stats["CVaR_pct"]) else None,
        }

    rows = []
    if "Symbol" in trades_df.columns:
        for symbol, group in trades_df.groupby("Symbol"):
            if len(group) < min_trades_per_symbol:
                continue
            funded_group = group[group["Funded"] == True] if "Funded" in group.columns else group
            avg_allocated = funded_group["AllocatedCapital"].mean() if "AllocatedCapital" in funded_group.columns and not funded_group.empty else None

            row = {"Symbol": symbol, "Trades": len(group)}
            for conf in confidence_levels:
                stats = calculate_var(
                    group["ProfitRs"].tolist(), confidence=conf, method=method,
                    n_simulations=n_simulations, horizon_trades=horizon_trades, seed=seed,
                )
                key = f"{conf * 100:.0f}"
                row[f"VaR{key}_pct"] = round(stats["VaR_pct"], 2) if pd.notna(stats["VaR_pct"]) else None
                row[f"CVaR{key}_pct"] = round(stats["CVaR_pct"], 2) if pd.notna(stats["CVaR_pct"]) else None
                row[f"VaR{key}_rs"] = (
                    round(stats["VaR_pct"] / 100 * avg_allocated, 2)
                    if avg_allocated is not None and pd.notna(stats["VaR_pct"]) else None
                )
            rows.append(row)

    sort_col = f"VaR{confidence_levels[0] * 100:.0f}_pct"
    by_symbol_df = pd.DataFrame(rows)
    if not by_symbol_df.empty and sort_col in by_symbol_df.columns:
        by_symbol_df = by_symbol_df.sort_values(sort_col, ascending=False).reset_index(drop=True)

    return {"portfolio": portfolio_var, "by_symbol": by_symbol_df, "method": method, "horizon_trades": horizon_trades}


def simulate_portfolio(
    trades_df,
    price_data=None,
    initial_capital=100000.0,
    max_concurrent_positions=10,
    sizing_mode="equal_weight",
    half_kelly_cap_pct=2.0,
    min_trades_for_kelly=20,
    default_risk_pct=1.0,
    portfolio_heat_cap_pct=6.0,
    sector_heat_cap_pct=3.0,
    vol_multiplier_bounds=(0.5, 1.5),
    breadth_multiplier_bounds=(0.5, 1.0),
    mc_simulations=2000,
    mc_ruin_threshold_pct=-50.0,
    ruin_tolerance_pct=5.0,
    min_viable_position_rs=500.0,
):
    """
    Simulates a real, capital-constrained portfolio on top of the already
    fully-resolved trade list from run_backtest() (each trade's entry/exit
    dates and % return are computed independently of capital - this
    function only decides which signals the portfolio actually had room to
    fund, how big to size them, and compounds capital as positions open and
    close).

    Walks every calendar trading day present in price_data (not just
    entry/exit event dates), so open positions are revalued against daily
    closes and portfolio_df is a true daily mark-to-market equity curve. If
    price_data is omitted, falls back to the coarser event-only date walk
    (equity only sampled at entry/exit dates) for backward compatibility.

    sizing_mode="equal_weight" (default) preserves the original behavior
    exactly: each newly funded trade gets (current total equity) /
    max_concurrent_positions, a slot recomputed fresh each time. When more
    signals fire on a day than there are free slots, higher ClosenessScore
    gets priority; the rest are marked unfunded.

    sizing_mode="risk" replaces the sizing formula with a half-Kelly,
    risk-based engine (see _kelly_base_risk_pct and run_monte_carlo):
    base risk % from walk-forward Kelly stats on closed trades' R-multiples,
    adjusted by a volatility-ratio multiplier (current ATR vs its own
    60-day average), a market-breadth multiplier, and a drawdown-throttle
    multiplier (calibrated against Monte Carlo drawdown bands) - then capped
    by portfolio and sector "heat" (total capital-at-risk to initial stops,
    as a % of equity). A trade that would breach a heat cap is shrunk to
    the remaining headroom rather than skipped outright; it's only skipped
    if the shrunk size falls below min_viable_position_rs. The
    max_concurrent_positions gate and ClosenessScore priority ordering are
    unchanged pre-filters in both modes.

    Returns (portfolio_df, trades_df, risk_info). portfolio_df is a
    chronological equity curve (Date, Equity, PortfolioHeatPct - the last
    column present but 0 in equal_weight mode). trades_df is the input with
    added columns: Funded, AllocatedCapital (both modes), and in risk mode
    also BaseRiskPct, VolMultiplier, BreadthMultiplier,
    DrawdownThrottleMultiplier, FinalRiskPct, DollarRiskAllocated,
    PortfolioHeatAtEntry, SectorHeatAtEntry, CapBreached, SizingRationale.
    risk_info holds the Monte Carlo drawdown bands and risk-of-ruin used to
    calibrate the run (empty dict in equal_weight mode).
    """
    trades = trades_df.copy()
    risk_info = {}
    if trades.empty:
        trades["Funded"] = pd.Series(dtype=bool)
        trades["AllocatedCapital"] = pd.Series(dtype=float)
        return pd.DataFrame(columns=["Date", "Equity", "PortfolioHeatPct"]), trades, risk_info

    trades["EntryDate"] = pd.to_datetime(trades["EntryDate"])
    trades["ExitDate"] = pd.to_datetime(trades["ExitDate"])

    entries_by_date = {}
    for idx, row in trades.iterrows():
        entries_by_date.setdefault(row["EntryDate"], []).append(idx)

    # Full daily trading calendar for mark-to-market, restricted to the
    # trades' own date span (no point revaluing before the first entry or
    # after the last exit). Falls back to event-only dates if no price data
    # was supplied.
    if price_data:
        span_start, span_end = trades["EntryDate"].min(), trades["ExitDate"].max()
        calendar_dates = sorted({
            ts.normalize() for df in price_data.values() for ts in df.index
            if span_start <= ts <= span_end
        })
        # Per-symbol close price reindexed to the full calendar, forward
        # filled so a symbol's price on a day it didn't trade (holiday,
        # gap) still has a usable last-known value for revaluation.
        close_by_symbol = {
            symbol: df["close"].reindex(pd.DatetimeIndex(calendar_dates), method="ffill")
            for symbol, df in price_data.items()
        }
    else:
        calendar_dates = sorted(set(trades["EntryDate"]).union(trades["ExitDate"]))
        close_by_symbol = {}

    risk_mode = sizing_mode == "risk"

    # Pre-loop Monte Carlo pass (once per run, not per-day - see
    # run_monte_carlo docstring) using the full trade set's R-multiples at
    # the flat default_risk_pct, to calibrate: (a) drawdown throttle bands,
    # (b) a one-time risk-of-ruin check that scales down every subsequent
    # Kelly-derived risk % for the rest of the run if the strategy's
    # historical edge implies an unacceptably high chance of ruin at that
    # risk level.
    ruin_scale = 1.0
    dd_p50 = dd_p90 = None
    if risk_mode:
        mc = run_monte_carlo(
            trades["RMultiple"].tolist(),
            base_risk_pct=default_risk_pct,
            n_simulations=mc_simulations,
            ruin_threshold_pct=mc_ruin_threshold_pct,
        )
        risk_info = mc
        dd_p50, dd_p90 = mc["drawdown_p50"], mc["drawdown_p90"]
        if mc["risk_of_ruin_pct"] > ruin_tolerance_pct:
            ruin_scale = 0.5

    cash = initial_capital
    open_positions = {}  # idx -> {"allocated": Rs, "entry_price": float, "initial_sl": float or None, "sector": str}
    funded = {}
    allocated = {}
    closed_r_multiples = []  # walk-forward, only trades closed strictly before "today"
    running_peak_equity = initial_capital
    extra_cols = {col: {} for col in [
        "BaseRiskPct", "VolMultiplier", "BreadthMultiplier", "DrawdownThrottleMultiplier",
        "FinalRiskPct", "DollarRiskAllocated", "PortfolioHeatAtEntry", "SectorHeatAtEntry",
        "CapBreached", "SizingRationale",
    ]}
    equity_curve = []

    def position_risk_dollars(pos):
        """Capital-at-risk if this open position hit its initial stop,
        using InitialSL as the conservative risk basis (the live trailing
        stop tightens over the trade's life but isn't exposed by the exit
        contract as a day-by-day series - a v1 simplification)."""
        if pos["initial_sl"] is None or pos["entry_price"] <= 0:
            return 0.0
        return pos["allocated"] * max(0.0, pos["entry_price"] - pos["initial_sl"]) / pos["entry_price"]

    for date in calendar_dates:
        # Exits before entries on the same day, so freed capital is
        # available for same-day reinvestment.
        exits_today = trades.index[trades["ExitDate"] == date]
        for idx in exits_today:
            if funded.get(idx):
                profit_pct = trades.loc[idx, "ProfitRs"]
                cash += open_positions.pop(idx)["allocated"] * (1 + profit_pct / 100)
                r_mult = trades.loc[idx, "RMultiple"] if "RMultiple" in trades.columns else None
                closed_r_multiples.append(r_mult)

        entries_today = sorted(
            entries_by_date.get(date, []),
            key=lambda i: trades.loc[i, "ClosenessScore"],
            reverse=True,
        )

        current_total_equity = cash + sum(p["allocated"] for p in open_positions.values())
        current_portfolio_heat_rs = sum(position_risk_dollars(p) for p in open_positions.values())

        if risk_mode:
            base_risk_pct = _kelly_base_risk_pct(
                closed_r_multiples, min_trades_for_kelly, default_risk_pct, half_kelly_cap_pct
            ) * ruin_scale

        for idx in entries_today:
            if len(open_positions) >= max_concurrent_positions:
                funded[idx] = False
                continue

            row = trades.loc[idx]
            entry_price = float(row["EntryPrice"])

            if not risk_mode:
                size = current_total_equity / max_concurrent_positions
                if size <= cash:
                    open_positions[idx] = {
                        "allocated": size, "entry_price": entry_price,
                        "initial_sl": row.get("InitialSL"), "sector": row.get("Sector"),
                    }
                    cash -= size
                    funded[idx] = True
                    allocated[idx] = size
                    current_total_equity = cash + sum(p["allocated"] for p in open_positions.values())
                else:
                    funded[idx] = False
                continue

            # --- Risk-based sizing ---
            initial_sl = row.get("InitialSL")
            risk_per_share_ratio = (
                (entry_price - initial_sl) / entry_price
                if initial_sl is not None and entry_price > 0 and entry_price > initial_sl
                else None
            )
            if risk_per_share_ratio is None:
                # No valid risk basis (shouldn't happen once InitialSL is
                # always populated, but guards a malformed/regenerated exit
                # strategy from silently sizing off garbage).
                funded[idx] = False
                extra_cols["CapBreached"][idx] = "NoRiskBasis"
                continue

            atr_entry, atr_avg60 = row.get("ATR_Entry"), row.get("ATR_Avg60")
            if atr_entry and atr_avg60 and atr_avg60 > 0:
                vol_ratio = atr_entry / atr_avg60
                vol_multiplier = min(max(1 / vol_ratio, vol_multiplier_bounds[0]), vol_multiplier_bounds[1])
            else:
                vol_multiplier = 1.0  # neutral - insufficient ATR history

            breadth = row.get("MarketBreadthAtEntry")
            if breadth is not None and pd.notna(breadth):
                # Linear scale from the entry-gate threshold (45) to a
                # "strong breadth" reference (80) into the configured bounds.
                breadth_multiplier = breadth_multiplier_bounds[0] + (
                    breadth_multiplier_bounds[1] - breadth_multiplier_bounds[0]
                ) * min(max((breadth - 45) / (80 - 45), 0.0), 1.0)
            else:
                breadth_multiplier = 1.0

            if dd_p50 is not None and dd_p90 is not None and dd_p90 > dd_p50:
                current_dd_pct = abs(
                    (current_total_equity - running_peak_equity) / running_peak_equity
                ) * 100 if running_peak_equity > 0 else 0.0
                if current_dd_pct <= dd_p50:
                    throttle_multiplier = 1.0
                elif current_dd_pct <= dd_p90:
                    throttle_multiplier = 1.0 - 0.5 * (current_dd_pct - dd_p50) / (dd_p90 - dd_p50)
                else:
                    throttle_multiplier = 0.25
            else:
                throttle_multiplier = 1.0

            final_risk_pct = min(
                base_risk_pct * vol_multiplier * breadth_multiplier * throttle_multiplier,
                half_kelly_cap_pct,
            )
            dollar_risk = final_risk_pct / 100 * current_total_equity

            sector = row.get("Sector")
            sector_heat_rs = sum(
                position_risk_dollars(p) for p in open_positions.values() if p["sector"] == sector
            )
            portfolio_headroom = max(0.0, portfolio_heat_cap_pct / 100 * current_total_equity - current_portfolio_heat_rs)
            sector_headroom = max(0.0, sector_heat_cap_pct / 100 * current_total_equity - sector_heat_rs)
            headroom = min(portfolio_headroom, sector_headroom)

            cap_breached = "None"
            if dollar_risk > headroom:
                cap_breached = "Both" if headroom == sector_headroom and headroom == portfolio_headroom else (
                    "Portfolio" if headroom == portfolio_headroom else "Sector"
                )
                dollar_risk = headroom

            position_size_rs = min(dollar_risk / risk_per_share_ratio, cash)

            if position_size_rs < min_viable_position_rs:
                funded[idx] = False
                extra_cols["CapBreached"][idx] = cap_breached if cap_breached != "None" else "MinSize"
                continue

            open_positions[idx] = {
                "allocated": position_size_rs, "entry_price": entry_price,
                "initial_sl": initial_sl, "sector": sector,
            }
            cash -= position_size_rs
            funded[idx] = True
            allocated[idx] = position_size_rs
            current_total_equity = cash + sum(p["allocated"] for p in open_positions.values())
            current_portfolio_heat_rs += position_size_rs * risk_per_share_ratio

            extra_cols["BaseRiskPct"][idx] = round(base_risk_pct, 3)
            extra_cols["VolMultiplier"][idx] = round(vol_multiplier, 3)
            extra_cols["BreadthMultiplier"][idx] = round(breadth_multiplier, 3)
            extra_cols["DrawdownThrottleMultiplier"][idx] = round(throttle_multiplier, 3)
            extra_cols["FinalRiskPct"][idx] = round(final_risk_pct, 3)
            extra_cols["DollarRiskAllocated"][idx] = round(position_size_rs * risk_per_share_ratio, 2)
            extra_cols["PortfolioHeatAtEntry"][idx] = round(current_portfolio_heat_rs / current_total_equity * 100, 2) if current_total_equity > 0 else 0.0
            extra_cols["SectorHeatAtEntry"][idx] = round(
                sum(position_risk_dollars(p) for p in open_positions.values() if p["sector"] == sector)
                / current_total_equity * 100, 2
            ) if current_total_equity > 0 else 0.0
            extra_cols["CapBreached"][idx] = cap_breached
            extra_cols["SizingRationale"][idx] = (
                f"Kelly {base_risk_pct:.2f}% x vol {vol_multiplier:.2f} x breadth {breadth_multiplier:.2f} "
                f"x DD-throttle {throttle_multiplier:.2f} = {final_risk_pct:.2f}%"
                + (f", {cap_breached.lower()}-capped" if cap_breached != "None" else "")
            )

        # Daily mark-to-market: revalue every still-open position at
        # today's close (falls back to the allocated capital unchanged if
        # no price data was supplied, i.e. the event-only legacy mode).
        if close_by_symbol:
            position_value_total = 0.0
            for idx, pos in open_positions.items():
                symbol = trades.loc[idx, "Symbol"]
                today_close = close_by_symbol.get(symbol, pd.Series(dtype=float)).get(date)
                if today_close is not None and pd.notna(today_close) and pos["entry_price"] > 0:
                    position_value_total += pos["allocated"] * (today_close / pos["entry_price"])
                else:
                    position_value_total += pos["allocated"]
        else:
            position_value_total = sum(p["allocated"] for p in open_positions.values())

        today_equity = cash + position_value_total
        running_peak_equity = max(running_peak_equity, today_equity)
        portfolio_heat_pct = (
            sum(position_risk_dollars(p) for p in open_positions.values()) / today_equity * 100
            if risk_mode and today_equity > 0 else 0.0
        )
        equity_curve.append({"Date": date, "Equity": today_equity, "PortfolioHeatPct": round(portfolio_heat_pct, 2)})

    trades["Funded"] = trades.index.map(lambda i: funded.get(i, False))
    trades["AllocatedCapital"] = trades.index.map(lambda i: round(allocated.get(i, 0.0), 2))
    if risk_mode:
        for col, values in extra_cols.items():
            trades[col] = trades.index.map(lambda i: values.get(i))
    trades["EntryDate"] = trades["EntryDate"].dt.date
    trades["ExitDate"] = trades["ExitDate"].dt.date

    portfolio_df = pd.DataFrame(equity_curve)
    return portfolio_df, trades, risk_info


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


def _parse_date(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()


def main():
    parser = argparse.ArgumentParser(
        description="Backtest the current generated_rules.py strategy using generated_exit_strategy.py for exits."
    )
    parser.add_argument("--start", required=True, type=_parse_date, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, type=_parse_date, help="End date YYYY-MM-DD")
    parser.add_argument("--limit-per-sector", type=int, default=50)
    parser.add_argument("--initial-capital", type=float, default=100000.0, help="Starting portfolio capital, e.g. 100000")
    parser.add_argument("--max-positions", type=int, default=10, help="Max number of concurrent open positions")
    parser.add_argument("--trades-out", default="backtest_trades.csv")
    parser.add_argument("--summary-out", default="backtest_summary.csv")
    parser.add_argument("--portfolio-out", default="backtest_portfolio.csv")
    parser.add_argument("--sizing-mode", choices=["equal_weight", "risk"], default="equal_weight",
                         help="'equal_weight' (default, original behavior) or 'risk' for half-Kelly risk-based sizing")
    parser.add_argument("--half-kelly-cap-pct", type=float, default=2.0)
    parser.add_argument("--min-trades-for-kelly", type=int, default=20)
    parser.add_argument("--default-risk-pct", type=float, default=1.0)
    parser.add_argument("--portfolio-heat-cap-pct", type=float, default=6.0)
    parser.add_argument("--sector-heat-cap-pct", type=float, default=3.0)
    parser.add_argument("--mc-simulations", type=int, default=2000)
    parser.add_argument("--mc-ruin-threshold-pct", type=float, default=-50.0)
    parser.add_argument("--trades-in", default=None,
                         help="Reuse an already-resolved trades CSV (from a prior run over the same date range) "
                              "instead of re-running signal generation - only re-simulates portfolio sizing. "
                              "Lets equal_weight and risk sizing be compared on the identical trade set cheaply.")
    parser.add_argument("--risk-info-out", default=None,
                         help="If given (sizing_mode=risk only), writes the Monte Carlo drawdown-band/"
                              "risk-of-ruin summary as JSON to this path.")
    args = parser.parse_args()

    def progress(done, total, day):
        print(f"Evaluating day {done}/{total} ({day})...")

    if args.trades_in:
        trades_df = pd.read_csv(args.trades_in)
        summary_df = summarize_trades(trades_df)
        _, price_data = load_price_data(args.start, args.end, limit_per_sector=args.limit_per_sector)
    else:
        trades_df, summary_df, price_data = run_backtest(
            args.start, args.end,
            limit_per_sector=args.limit_per_sector,
            progress_callback=progress,
        )

    portfolio_df, trades_df, risk_info = simulate_portfolio(
        trades_df, price_data=price_data,
        initial_capital=args.initial_capital, max_concurrent_positions=args.max_positions,
        sizing_mode=args.sizing_mode,
        half_kelly_cap_pct=args.half_kelly_cap_pct,
        min_trades_for_kelly=args.min_trades_for_kelly,
        default_risk_pct=args.default_risk_pct,
        portfolio_heat_cap_pct=args.portfolio_heat_cap_pct,
        sector_heat_cap_pct=args.sector_heat_cap_pct,
        mc_simulations=args.mc_simulations,
        mc_ruin_threshold_pct=args.mc_ruin_threshold_pct,
    )

    trades_df.to_csv(args.trades_out, index=False)
    summary_df.to_csv(args.summary_out, index=False)
    portfolio_df.to_csv(args.portfolio_out, index=False)

    print(f"\n{len(trades_df)} trades simulated.")
    print(summary_df.to_string(index=False))

    if not portfolio_df.empty:
        final_equity = portfolio_df["Equity"].iloc[-1]
        total_return_pct = (final_equity - args.initial_capital) / args.initial_capital * 100
        funded_count = int(trades_df["Funded"].sum())
        skipped_count = len(trades_df) - funded_count
        print(f"\n--- PORTFOLIO ({args.max_positions} concurrent slots, Rs.{args.initial_capital:,.0f} start, sizing_mode={args.sizing_mode}) ---")
        print(f"Funded trades: {funded_count} (skipped for lack of capital/risk caps: {skipped_count})")
        print(f"Final equity: Rs.{final_equity:,.2f}")
        print(f"Total return: {total_return_pct:.2f}%")
        if risk_info:
            print(f"Monte Carlo ({args.mc_simulations} paths) drawdown bands: "
                  f"P50={risk_info['drawdown_p50']:.1f}% P90={risk_info['drawdown_p90']:.1f}% | "
                  f"Risk of ruin: {risk_info['risk_of_ruin_pct']:.2f}%")

    if args.risk_info_out and risk_info:
        with open(args.risk_info_out, "w", encoding="utf-8") as f:
            json.dump(risk_info, f, indent=2)

    print(f"\nTrades saved to {args.trades_out}")
    print(f"Summary saved to {args.summary_out}")
    print(f"Portfolio equity curve saved to {args.portfolio_out}")


if __name__ == "__main__":
    main()
