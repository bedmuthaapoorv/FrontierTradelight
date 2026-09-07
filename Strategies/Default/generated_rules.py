import pandas as pd
import numpy as np
import pandas_ta as ta
from scipy.signal import argrelextrema

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    results = {
        "Symbol": symbol,
        "Passed": False,
        "ClosenessScore": 0.0,
        "FailedRules": [],
        "Details": {}
    }
    
    try:
        if len(df) < 60:
            results["FailedRules"].append("Insufficient data (min 60 days)")
            return results

        # Pre-calculations
        close = df['close']
        low = df['low']
        vol = df['volume']
        turnover = vol * close
        ma20_vol = turnover.rolling(20).mean()
        ma100 = close.rolling(100).mean()
        atr14 = ta.atr(df['high'], df['low'], close, length=14)
        if atr14 is None or atr14.empty:
            results["FailedRules"].append("ATR calculation failed")
            return results
        
        curr_atr = atr14.iloc[-1]
        
        # Rule 1: Liquidity
        if not (ma20_vol.iloc[-1] >= 50000000 and close.iloc[-1] >= 50):
            results["FailedRules"].append("Liquidity floor not met")
            
        # Rule 2: Uptrend
        if not (close.iloc[-1] > ma100.iloc[-1] and ma100.iloc[-1] > ma100.iloc[-10]):
            results["FailedRules"].append("Not in uptrend")
            
        # Rule 3: Trendline
        best_line = None
        max_touches = -1
        
        for window in [250, 150, 100, 60]:
            if len(df) < window: continue
            subset = df.iloc[-window:].reset_index(drop=True)
            pivots = argrelextrema(subset['low'].values, np.less_equal, order=4)[0]
            if len(pivots) < 3: continue
            
            fit_indices = pivots.copy()
            fit_lows = subset['low'].iloc[pivots].values
            
            # Robust refinement
            for _ in range(int(np.ceil(0.1 * len(pivots)))):
                if len(fit_indices) < 3: break
                coeffs = np.polyfit(fit_indices, fit_lows, 1)
                proj = coeffs[0] * fit_indices + coeffs[1]
                residuals = fit_lows - proj
                worst_idx = np.argmin(residuals)
                if residuals[worst_idx] < -1.0 * curr_atr:
                    fit_indices = np.delete(fit_indices, worst_idx)
                    fit_lows = np.delete(fit_lows, worst_idx)
                else: break
            
            slope, intercept = np.polyfit(fit_indices, fit_lows, 1)
            if slope <= 0: continue
            
            touches = 0
            for i in pivots:
                if abs(subset['low'].iloc[i] - (slope * i + intercept)) <= 1.0 * curr_atr:
                    touches += 1
            
            broken = False
            for i in range(window-3, window):
                if (subset['close'].iloc[i] - (slope * i + intercept)) < -1.5 * curr_atr:
                    broken = True
            
            if touches >= 4 and not broken and touches > max_touches:
                max_touches = touches
                best_line = {"slope": slope, "intercept": intercept, "touches": touches, "window": window}
        
        if not best_line:
            results["FailedRules"].append("No valid ascending trendline found")
        
        # Rule 4-8
        rsi = ta.rsi(close, length=14)
        curr_rsi = rsi.iloc[-1] if isinstance(rsi, pd.Series) else rsi.iloc[:, 0].iloc[-1]
        
        if best_line:
            proj_today = best_line['slope'] * (best_line['window'] - 1) + best_line['intercept']
            dist_atr = abs(close.iloc[-1] - proj_today) / curr_atr
            
            if not (low.iloc[-1] <= proj_today + curr_atr and close.iloc[-1] > close.iloc[-2] and vol.iloc[-1] >= 1.2 * vol.rolling(20).mean().iloc[-1]):
                results["FailedRules"].append("Bounce confirmation failed")
            if not (35 <= curr_rsi <= 55):
                results["FailedRules"].append(f"RSI outside range ({curr_rsi:.1f})")
            if not (close.iloc[-1] <= 1.15 * close.iloc[-11]):
                results["FailedRules"].append("Already extended")
        
        rank = sector_ranks.get(symbol, 99)
        if rank > 10: results["FailedRules"].append(f"Sector rank {rank} not in top 10")
        if market_breadth < 45: results["FailedRules"].append("Market breadth too low")
        
        if not results["FailedRules"]:
            results["Passed"] = True
            # Scoring
            t_score = min(100, best_line['touches'] * 20)
            b_score = min(100, (vol.iloc[-1] / vol.rolling(20).mean().iloc[-1]) * 50)
            s_score = max(0, 100 - (rank - 1) * 10)
            r_score = max(0, 100 - abs(curr_rsi - 45) * 5)
            p_score = max(0, 100 - (dist_atr * 100))
            results["ClosenessScore"] = 0.3*t_score + 0.25*b_score + 0.2*s_score + 0.15*r_score + 0.1*p_score
            
            results["Details"] = {
                "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
                "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
                "Sector Rank": rank,
                "Current Price": close.iloc[-1],
                "Ideal Entry Price Low": close.iloc[-1],
                "Ideal Entry Price High": close.iloc[-1] * 1.01,
                "Daily RSI(14)": curr_rsi,
                "Volume[-1]": vol.iloc[-1],
                "20D Average Volume": vol.rolling(20).mean().iloc[-1],
                "Trendline Touches": best_line['touches'],
                "Distance From Trendline (ATR units)": dist_atr,
                "Rank Score": results["ClosenessScore"]
            }
            
    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {e}")
        
    return results