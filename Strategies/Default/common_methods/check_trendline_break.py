def check_trendline_break(close, low, atr_vals, p2, slope, today_idx):
    """Checks if any close price violates the trendline threshold between p2 and today_idx."""
    for j in range(p2 + 1, today_idx):
        tl_j = low[p2] + slope * (j - p2)
        if close[j] < tl_j - (0.75 * atr_vals[j]):
            return True
    return False
