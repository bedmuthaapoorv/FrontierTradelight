def find_p1_pivot(pivots, p2, min_gap):
    """Finds the most recent pivot p1 such that p2 - p1 >= min_gap."""
    for p in reversed(pivots[:-1]):
        if p2 - p >= min_gap:
            return p
    return None
