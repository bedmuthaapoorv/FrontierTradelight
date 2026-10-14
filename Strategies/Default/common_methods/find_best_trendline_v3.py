import numpy as np
from common_methods import detect_pivot_lows

def find_best_trendline_v3(df, curr_atr):
    """Finds the best fitting trendline from a set of windows using iterative polyfit."""
    for window in [250, 150, 100, 60]:
        if len(df) < window: continue
        subset = df.iloc[-window:]
        pivots = detect_pivot_lows(subset['low'].values, 0, window, window=4)
        if len(pivots) < 3: continue
        fit_indices = np.array(pivots)
        fit_lows = subset['low'].iloc[pivots].values
        for _ in range(int(np.ceil(0.1 * len(fit_indices)))):
            poly = np.polyfit(fit_indices, fit_lows, 1)
            line = poly[0] * fit_indices + poly[1]
            resids = fit_lows - line
            if np.min(resids) < -1.0 * curr_atr:
                idx_to_drop = np.argmin(resids)
                fit_indices = np.delete(fit_indices, idx_to_drop)
                fit_lows = np.delete(fit_lows, idx_to_drop)
            else: break
        poly = np.polyfit(fit_indices, fit_lows, 1)
        if poly[0] <= 0: continue
        touches = sum(1 for p in pivots if abs(subset['low'].iloc[p] - (poly[0] * p + poly[1])) <= 1.0 * curr_atr)
        if touches < 4: continue
        broken = False
        for i in range(window - 3, window):
            if subset['close'].iloc[i] < (poly[0] * i + poly[1]) - 1.5 * curr_atr:
                broken = True; break
        if not broken:
            return {"slope": poly[0], "intercept": poly[1], "touches": touches, "window": window}
    return None
