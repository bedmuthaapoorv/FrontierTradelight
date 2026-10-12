import numpy as np


def find_rising_trendline(low, close, atr, pivots, min_gap=25, break_atr_mult=0.75):
    """Fit a rising support trendline through two pivot lows and check it is
    still unbroken today.

    Algorithm: anchor on the MOST RECENT pivot (p2). Walk earlier pivots
    from newest to oldest; take the first p1 that is at least `min_gap`
    bars before p2 and gives a positive slope. The line is broken if any
    close strictly after p2 and before today (the last bar) is below
    line - break_atr_mult * ATR on that bar. If that candidate is broken,
    try the next older p1. The first unbroken candidate wins.

    Args:
        low, close: array-like (e.g. df['low'].values), oldest first, same length.
        atr: array-like ATR aligned with low/close (e.g. ta.atr(...).values).
        pivots: sorted pivot-low positions (see detect_pivot_lows).
        min_gap: minimum bars between the two anchor pivots.
        break_atr_mult: how many ATRs below the line a close must be to
            count as a break.

    Returns:
        None if no valid line, else a dict:
            "p1", "p2": anchor positions,
            "slope": price change per bar (> 0),
            "anchor_price": low[p2],
            "value_today": line value at the last bar,
            "slope_pct": slope / low[p2] (fraction per bar).
        The line value at any position i is anchor_price + slope * (i - p2).
        Never raises.
    """
    try:
        low = np.asarray(low, dtype=float)
        close = np.asarray(close, dtype=float)
        atr = np.asarray(atr, dtype=float)
        today = len(low) - 1
        if len(pivots) < 2:
            return None
        p2 = pivots[-1]
        for p1 in reversed(pivots[:-1]):
            if p2 - p1 < min_gap:
                continue
            slope = (low[p2] - low[p1]) / (p2 - p1)
            if slope <= 0:
                continue
            broken = False
            for j in range(p2 + 1, today):
                line_j = low[p2] + slope * (j - p2)
                if close[j] < line_j - break_atr_mult * atr[j]:
                    broken = True
                    break
            if not broken:
                return {
                    "p1": int(p1),
                    "p2": int(p2),
                    "slope": float(slope),
                    "anchor_price": float(low[p2]),
                    "value_today": float(low[p2] + slope * (today - p2)),
                    "slope_pct": float(slope / low[p2]) if low[p2] else 0.0,
                }
        return None
    except Exception:
        return None
