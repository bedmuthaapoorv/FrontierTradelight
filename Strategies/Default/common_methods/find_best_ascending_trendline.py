import numpy as np
from common_methods import detect_pivot_lows

def find_best_ascending_trendline(low, atr_val, total_len):
    """Finds the best ascending trendline by iterating through windows and refining pivots."""
    for window in [250, 150, 100, 60]:
        if total_len < window: continue
        subset_low = low[-window:]
        pivots = detect_pivot_lows(subset_low, 0, window, window=4)
        if len(pivots) < 3: continue
        fit_indices = np.array(pivots)
        fit_lows = subset_low[fit_indices]
        slope, intercept = 0, 0
        for _ in range(int(np.ceil(0.1 * len(fit_indices)) + 1)):
            if len(fit_indices) < 2: break
            slope, intercept = np.polyfit(fit_indices, fit_lows, 1)
            residuals = fit_lows - (slope * fit_indices + intercept)
            worst_idx = np.argmin(residuals)
            if residuals[worst_idx] < -1.0 * atr_val:
                fit_indices = np.delete(fit_indices, worst_idx)
                fit_lows = np.delete(fit_lows, worst_idx)
            else: break
        if slope <= 0: continue
        touches = sum(1 for i in pivots if abs(subset_low[i] - (slope * i + intercept)) <= 1.0 * atr_val)
        if touches < 4: continue
        broken = False
        for i in range(window - 3, window):
            if (subset_low[i] - (slope * i + intercept)) < -1.5 * atr_val:
                broken = True
        if not broken:
            return {"slope": slope, "intercept": intercept, "touches": touches, "window": window}
    return None
