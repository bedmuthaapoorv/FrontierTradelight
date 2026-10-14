import numpy as np
from scipy.signal import argrelextrema

def find_best_trendline_v2(df, atr14_val):
    """Finds the best fitting trendline from a set of windows using iterative polyfit."""
    low = df['low'].values
    windows = [250, 150, 100, 60]
    best_line = None
    max_touches = -1
    for w in windows:
        if len(df) < w: continue
        subset_low = low[-w:]
        pivot_indices = argrelextrema(subset_low, np.less_equal, order=4)[0]
        if len(pivot_indices) < 3: continue
        fit_idx = pivot_indices.copy()
        fit_lows = subset_low[fit_idx]
        m, c = 0, 0
        for _ in range(int(np.ceil(0.1 * len(fit_idx)) + 1)):
            if len(fit_idx) < 2: break
            A = np.vstack([fit_idx, np.ones(len(fit_idx))]).T
            m, c = np.linalg.lstsq(A, fit_lows, rcond=None)[0]
            residuals = fit_lows - (m * fit_idx + c)
            worst_idx = np.argmin(residuals)
            if residuals[worst_idx] < -1.0 * atr14_val:
                fit_idx = np.delete(fit_idx, worst_idx)
                fit_lows = np.delete(fit_lows, worst_idx)
            else: break
        if m <= 0: continue
        touches = sum(1 for i in pivot_indices if abs(subset_low[i] - (m * i + c)) <= 1.0 * atr14_val)
        if touches < 4: continue
        broken = all((subset_low[-(3-i)] < (m * (w - 1 - i) + c) - 1.5 * atr14_val) for i in range(3))
        if not broken and touches > max_touches:
            max_touches = touches
            best_line = {"m": m, "c": c, "touches": touches, "w": w}
    return best_line
