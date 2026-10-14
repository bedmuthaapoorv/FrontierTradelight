def check_trendline_integrity(close, low, atr_vals, i2, slope):
    """Checks if any close price violates the trendline threshold between i2 and the end of the data."""
    for j in range(i2 + 1, len(close) - 1):
        tl_j = low[i2] + slope * (j - i2)
        if close[j] < (tl_j - 0.75 * atr_vals[j]):
            return False
    return True
