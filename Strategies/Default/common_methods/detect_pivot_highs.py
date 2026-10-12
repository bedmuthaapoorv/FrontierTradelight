import numpy as np


def detect_pivot_highs(high, start, end, window=3):
    """Find confirmed swing-high pivots by POSITION (not date label).

    A bar i is a pivot high when high[i] is strictly higher than each of
    the `window` bars before it AND each of the `window` bars after it.

    Args:
        high: array-like of highs (e.g. df['high'].values), oldest first.
        start: first position to test (inclusive). Negative values count
            from the end like Python slicing.
        end: last position to test (exclusive). Bars too close to either
            edge to have `window` neighbours on both sides are skipped.
        window: number of bars on each side that must be lower.

    Returns:
        A sorted list of integer positions into `high`. Empty list on bad
        input. Never raises.
    """
    try:
        arr = np.asarray(high, dtype=float)
        n = len(arr)
        if start < 0:
            start += n
        if end < 0:
            end += n
        start = max(start, window)
        end = min(end, n - window)
        pivots = []
        for i in range(start, end):
            v = arr[i]
            if all(v > arr[i - k] and v > arr[i + k] for k in range(1, window + 1)):
                pivots.append(i)
        return pivots
    except Exception:
        return []
