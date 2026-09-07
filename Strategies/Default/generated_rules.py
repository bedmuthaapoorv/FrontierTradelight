"""Auto-generated router: compiled from rules.md's "Referenced Strategies"
and "Routing Rules" sections by generate_screener.py. Do not edit by hand -
edit rules.md and regenerate instead."""

from generated_strategies import Breakout as _s_Breakout
from generated_strategies import Trendline as _s_Trendline
from generated_strategies import MeanReversion as _s_MeanReversion

def select_strategy(market_breadth):
    try:
        if not isinstance(market_breadth, (int, float)):
            return "Trendline"
        
        if market_breadth >= 60:
            return "Breakout"
        elif market_breadth < 40:
            return "MeanReversion"
        else:
            return "Trendline"
    except:
        return "Trendline"

_STRATEGIES = {"Breakout": _s_Breakout, "Trendline": _s_Trendline, "MeanReversion": _s_MeanReversion}
_FALLBACK_KEY = "Trendline"


def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    try:
        active_key = select_strategy(market_breadth)
        if active_key not in _STRATEGIES:
            active_key = _FALLBACK_KEY
    except Exception:
        active_key = _FALLBACK_KEY

    result = _STRATEGIES[active_key].evaluate_stock(symbol, df, universe, sector_ranks, market_breadth)
    result.setdefault("Details", {})["Active Strategy"] = active_key
    return result
