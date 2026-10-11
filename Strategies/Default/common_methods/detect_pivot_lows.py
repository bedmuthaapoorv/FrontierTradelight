import numpy as np


def detect_pivot_lows(low, start, end, window=3):
    """Find confirmed swing-low pivots by POSITION (not date label).

    A bar i is a pivot low when low[i] is strictly lower than each of the
    `window` bars before it AND each of the `window` bars after it.

    Args:
        low: array-like of lows (e.g. df['low'].values), oldest first.
        start: first position to test (inclusive). Negative values count
            from the end like Python slicing (e.g. len(low) - 1 - 90).
        end: last position to test (exclusive). Bars too close to either
            edge to have `window` neighbours on both sides are skipped.
        window: number of bars on each side that must be higher.

    Returns:
        A sorted list of integer positions into `low`. Empty list on bad
        input. Never raises.
    """
    try:
        arr = np.asarray(low, dtype=float)
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
            if all(v < arr[i - k] and v < arr[i + k] for k in range(1, window + 1)):
                pivots.append(i)
        return pivots
    except Exception:
        return []
