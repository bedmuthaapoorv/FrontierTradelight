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


OPTIONAL_INPUTS = ("momentum_ranks", "fundamentals")

_accepted_inputs = weakref.WeakKeyDictionary()


def accepted_inputs(fn):
    """The optional evaluate_stock inputs (OPTIONAL_INPUTS) this compiled
    strategy declares. A **kwargs strategy accepts all of them."""
    cached = _accepted_inputs.get(fn)
    if cached is not None:
        return cached
    try:
        params = inspect.signature(fn).parameters
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()):
            accepted = frozenset(OPTIONAL_INPUTS)
        else:
            accepted = frozenset(name for name in OPTIONAL_INPUTS if name in params)
    except (TypeError, ValueError):
        accepted = frozenset()
    try:
        _accepted_inputs[fn] = accepted
    except TypeError:
        pass
    return accepted


def warn_if_fundamentals_missing(fn):
    """A strategy compiled to use fundamentals silently fails every stock
    ("Fundamentals not available") when the local cache hasn't been built,
    so say so up front. Returns True if a warning was printed."""
    if "fundamentals" not in accepted_inputs(fn):
        return False
    from fundamentals import load_annual_or_none

    if load_annual_or_none() is not None:
        return False
    print(
        "WARNING: this strategy uses fundamentals, but the local fundamentals cache "
        "(data/fundamentals/annual.csv) hasn't been built - every stock will fail its "
        "fundamentals rules. Run `python fetch_fundamentals.py` in Strategies/Default first."
    )
    return True


def call_evaluate(fn, symbol, df, universe, sector_ranks, market_breadth, **optional_inputs):
    """Calls a strategy's evaluate_stock with the five standard arguments plus
    whichever optional inputs (momentum_ranks, fundamentals) it was compiled
    to accept. Strategies compiled before an input existed simply don't
    receive it, so every older strategy keeps working unchanged."""
    unknown = set(optional_inputs) - set(OPTIONAL_INPUTS)
    if unknown:
        raise TypeError(f"Unknown evaluate_stock input(s): {sorted(unknown)}")
    accepted = accepted_inputs(fn)
    extras = {name: value for name, value in optional_inputs.items() if name in accepted}
    return fn(symbol, df, universe, sector_ranks, market_breadth, **extras)
