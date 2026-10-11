def sector_rank(sector_ranks, symbol, default=99):
    """Look up a stock's sector rank (1 = strongest sector).

    `sector_ranks` is keyed by STOCK SYMBOL, not by sector name - never look
    up the stock's sector name first and index by that.

    Args:
        sector_ranks: dict mapping symbol -> int rank.
        symbol: the stock symbol being evaluated.
        default: rank returned when the symbol is missing (treated as weak).

    Returns:
        int rank. Never raises.
    """
    try:
        value = sector_ranks.get(symbol, default)
        return int(value) if value is not None else default
    except Exception:
        return default
