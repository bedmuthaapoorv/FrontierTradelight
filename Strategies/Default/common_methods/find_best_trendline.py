import numpy as np
from common_methods import detect_pivot_lows

def find_best_trendline(df, atr14):
    """Finds the best fitting trendline from a set of windows using iterative polyfit."""
    winning_line = None
    best_touches = -1
    for window in [250, 150, 100, 60]:
        if len(df) < window: continue
        subset = df.iloc[-window:]
        lows = subset['low'].values
        pivots = detect_pivot_lows(lows, 0, len(lows), window=4)
        if len(pivots) < 3: continue
        fit_indices = np.array(pivots)
        fit_lows = lows[fit_indices]
        slope, intercept = 0, 0
        for _ in range(int(np.ceil(0.1 * len(pivots)) + 1)):
            poly = np.polyfit(fit_indices, fit_lows, 1)
            slope, intercept = poly[0], poly[1]
            residuals = fit_lows - (slope * fit_indices + intercept)
            worst_idx = np.argmin(residuals)
            if residuals[worst_idx] < -1.0 * atr14:
                fit_indices = np.delete(fit_indices, worst_idx)
                fit_lows = np.delete(fit_lows, worst_idx)
            else: break
        if slope <= 0: continue
        touches = sum(1 for i in pivots if abs(lows[i] - (slope * i + intercept)) <= 1.0 * atr14)
        if touches < 4: continue
        broken = all(df['close'].iloc[-3-i] < (slope * (window - 1 - i) + intercept) - 1.5 * atr14 for i in range(3))
        if not broken and touches > best_touches:
            best_touches = touches
            winning_line = {"slope": slope, "intercept": intercept, "touches": touches, "window": window}
    return winning_line
