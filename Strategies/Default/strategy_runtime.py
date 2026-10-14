"""Shared helpers for running a compiled strategy: its declared direction
and holding style, and calling evaluate_stock() with the optional inputs
it accepts."""

import inspect
import weakref

from backup_utils import declared_strategy_name


def strategy_meta(rules_content):
    """Reads the optional "Direction:" and "Holding:" lines from a
    rules.md's Strategy Metadata. Defaults (no lines) are a long, swing
    strategy - today's behaviour for every existing strategy."""
    direction = declared_strategy_name(rules_content or "", name_field="Direction").lower()
    holding = declared_strategy_name(rules_content or "", name_field="Holding").lower()
    return {
        "direction": "Short" if direction.startswith("short") else "Long",
        "intraday": holding.startswith("intraday"),
    }


_accepts_momentum = weakref.WeakKeyDictionary()


def _takes_momentum_ranks(fn):
    cached = _accepts_momentum.get(fn)
    if cached is not None:
        return cached
    try:
        params = inspect.signature(fn).parameters
        accepts = "momentum_ranks" in params or any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
    except (TypeError, ValueError):
        accepts = False
    try:
        _accepts_momentum[fn] = accepts
    except TypeError:
        pass
    return accepts


def call_evaluate(fn, symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=None):
    """Calls a strategy's evaluate_stock, passing momentum_ranks only to
    strategies compiled after it was added - older compiled strategies take
    exactly five arguments and keep working unchanged."""
    if _takes_momentum_ranks(fn):
        return fn(symbol, df, universe, sector_ranks, market_breadth, momentum_ranks=momentum_ranks)
    return fn(symbol, df, universe, sector_ranks, market_breadth)
