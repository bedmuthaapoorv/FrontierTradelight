import pandas as pd
import numpy as np
import pandas_ta as ta
from scipy.signal import argrelextrema

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    
    try:
        if len(df) < 60:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

        # Pre-calculations
        close = df['close']
        low = df['low']
        vol = df['volume']
        turnover = vol * close
        ma20_turnover = turnover.rolling(20).mean().iloc[-1]
        ma100 = ta.sma(close, length=100)
        atr14 = ta.atr(df['high'], df['low'], close, length=14).iloc[-1]
        rsi14 = ta.rsi(close, length=14).iloc[-1]
        
        # Rule 1: Liquidity
        if ma20_turnover < 50000000 or close.iloc[-1] < 50:
            failed_rules.append("Liquidity floor not met")
            
        # Rule 2: Uptrend
        if not (close.iloc[-1] > ma100.iloc[-1] and ma100.iloc[-1] > ma100.iloc[-10]):
            failed_rules.append("Not in uptrend")
            
        # Rule 3: Trendline
        winning_line = None
        for window in [250, 150, 100, 60]:
            if len(df) < window: continue
            subset = df.iloc[-window:].reset_index(drop=True)
            pivot_indices = argrelextrema(subset['low'].values, np.less_equal, order=4)[0]
            if len(pivot_indices) < 3: continue
            
            fit_indices = pivot_indices.copy()
            fit_lows = subset['low'].iloc[fit_indices].values
            
            # Robust refinement
            max_outliers = int(np.ceil(0.1 * len(pivot_indices)))
            for _ in range(max_outliers):
                coeffs = np.polyfit(fit_indices, fit_lows, 1)
                slope, intercept = coeffs[0], coeffs[1]
                residuals = fit_lows - (slope * fit_indices + intercept)
                worst_idx = np.argmin(residuals)
                if residuals[worst_idx] < -1.0 * atr14:
                    fit_indices = np.delete(fit_indices, worst_idx)
                    fit_lows = np.delete(fit_lows, worst_idx)
                else: break
            
            if slope <= 0: continue
            
            touches = sum(1 for i in pivot_indices if abs(subset['low'].iloc[i] - (slope * i + intercept)) <= 1.0 * atr14)
            if touches < 4: continue
            
            broken = all((subset['close'].iloc[-3:] - (slope * np.arange(window-3, window) + intercept)) < -1.5 * atr14)
            if broken: continue
            
            winning_line = {'slope': slope, 'intercept': intercept, 'touches': touches, 'window': window, 'proj': slope * (window - 1) + intercept}
            break
            
        if not winning_line:
            failed_rules.append("No valid ascending trendline")
        
        # Rule 4: Bounce
        if winning_line:
            if not (low.iloc[-1] <= winning_line['proj'] + (1.0 * atr14) and close.iloc[-1] > close.iloc[-2] and vol.iloc[-1] >= 1.2 * vol.rolling(20).mean().iloc[-1]):
                failed_rules.append("Bounce confirmation failed")
        
        # Rule 5: RSI
        if not (35 <= rsi14 <= 55):
            failed_rules.append(f"RSI outside range ({rsi14:.1f})")
            
        # Rule 6: Extension
        if not (close.iloc[-1] <= 1.15 * close.iloc[-10]):
            failed_rules.append("Already extended")
            
        # Rule 7: Sector
        rank = sector_ranks.get(symbol, 99)
        if rank > 10:
            failed_rules.append(f"Sector rank {rank} not in top 10")
            
        # Rule 8: Breadth
        if market_breadth < 45:
            failed_rules.append("Market breadth too low")

        passed = len(failed_rules) == 0
        
        # Scoring
        score = 0.0
        if passed:
            dist_atr = abs(close.iloc[-1] - winning_line['proj']) / atr14
            score = (0.3 * min(100, winning_line['touches'] * 20) +
                     0.25 * min(100, (vol.iloc[-1] / vol.rolling(20).mean().iloc[-1]) * 50) +
                     0.2 * max(0, 100 - (rank - 1) * 10) +
                     0.15 * max(0, 100 - abs(rsi14 - 45) * 5) +
                     0.1 * max(0, 100 - (dist_atr * 100)))

        details.update({
            "RSI": rsi14, "Sector Rank": rank, "Trendline Touches": winning_line['touches'] if winning_line else 0,
            "Distance From Trendline (ATR units)": abs(close.iloc[-1] - winning_line['proj'])/atr14 if winning_line else 0,
            "Volume[-1]": vol.iloc[-1], "20D Average Volume": vol.rolling(20).mean().iloc[-1],
            "Ideal Entry Price Low": close.iloc[-1], "Ideal Entry Price High": close.iloc[-1] * 1.01,
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"), "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Current Price": close.iloc[-1], "Rank Score": score
        })

        return {"Symbol": symbol, "Passed": passed, "ClosenessScore": score, "FailedRules": failed_rules, "Details": details}

    except Exception as e:
        return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": [f"Calculation error: {e}"], "Details": {}}