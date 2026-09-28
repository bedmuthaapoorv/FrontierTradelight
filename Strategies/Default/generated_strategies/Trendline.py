import pandas as pd
import numpy as np
import pandas_ta as ta
from scipy.signal import argrelextrema
from math import ceil

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
        ma20_vol = vol.rolling(20).mean()
        ma100 = close.rolling(100).mean()
        atr14 = ta.atr(df['high'], df['low'], df['close'], length=14)
        rsi14 = ta.rsi(close, length=14)
        
        curr_atr = atr14.iloc[-1] if not atr14.empty else 0
        curr_rsi = rsi14.iloc[-1] if isinstance(rsi14, pd.Series) else 0
        
        # Rule 1: Liquidity
        if ma20_vol.iloc[-1] < 100000 or close.iloc[-1] < 50:
            results["FailedRules"].append("Rule 1: Minimum Liquidity Floor failed")
            
        # Rule 2: Uptrend
        if not (close.iloc[-1] > ma100.iloc[-1] and ma100.iloc[-1] > ma100.iloc[-11]):
            results["FailedRules"].append("Rule 2: Uptrend Context failed")

        # Rule 3: Trendline
        best_line = None
        max_touches = -1
        
        for window in [250, 150, 100, 60]:
            if len(df) < window: continue
            subset = df.iloc[-window:].reset_index(drop=True)
            pivots = argrelextrema(subset['low'].values, np.less, order=4)[0]
            if len(pivots) < 3: continue
            
            fit_indices = pivots.astype(float)
            fit_lows = subset['low'].iloc[pivots].values
            
            # Robust refinement
            for _ in range(ceil(0.1 * len(pivots))):
                X = np.vstack([fit_indices, np.ones(len(fit_indices))]).T
                m, c = np.linalg.lstsq(X, fit_lows, rcond=None)[0]
                residuals = fit_lows - (m * fit_indices + c)
                if residuals.min() < -1.0 * curr_atr:
                    idx_to_drop = np.argmin(residuals)
                    fit_indices = np.delete(fit_indices, idx_to_drop)
                    fit_lows = np.delete(fit_lows, idx_to_drop)
                else: break
            
            if m <= 0: continue
            
            touches = sum(1 for i in pivots if abs(subset['low'].iloc[i] - (m * i + c)) <= 1.0 * curr_atr)
            if touches < 4: continue
            
            broken = all((subset['close'].iloc[-(3-i)] < (m * (window - 1 - i) + c) - 1.5 * curr_atr) for i in range(3))
            if broken: continue
            
            if touches > max_touches:
                max_touches = touches
                best_line = {'m': m, 'c': c, 'touches': touches, 'window': window}

        if not best_line:
            results["FailedRules"].append("Rule 3: Ascending Trendline Detection failed")
        else:
            proj_today = best_line['m'] * (best_line['window'] - 1) + best_line['c']
            
            # Rule 4: Bounce
            if not (low.iloc[-1] <= proj_today + curr_atr and close.iloc[-1] > close.iloc[-2] and vol.iloc[-1] >= 1.2 * ma20_vol.iloc[-1]):
                results["FailedRules"].append("Rule 4: Bounce Confirmation failed")
            
            # Rule 5: RSI
            if not (35 <= curr_rsi <= 55):
                results["FailedRules"].append("Rule 5: RSI Pullback Zone failed")
                
            # Rule 6: Extension
            if not (close.iloc[-1] <= 1.15 * close.iloc[-11]):
                results["FailedRules"].append("Rule 6: Already Extended failed")

        # Rule 7 & 8
        rank = sector_ranks.get(symbol, 99)
        if rank > 10: results["FailedRules"].append("Rule 7: Sector Strength failed")
        if market_breadth < 45: results["FailedRules"].append("Rule 8: Market Breadth failed")

        # Finalize
        results["Passed"] = len(results["FailedRules"]) == 0
        
        # Details & Score
        dist_atr = abs(close.iloc[-1] - proj_today) / curr_atr if best_line and curr_atr > 0 else 0
        results["Details"] = {
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
            "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Sector Rank": rank,
            "Current Price": close.iloc[-1],
            "Ideal Entry Price Low": close.iloc[-1],
            "Ideal Entry Price High": close.iloc[-1] * 1.01,
            "Ideal Exit Price": close.iloc[-1] + 2.5 * curr_atr,
            "Swing Duration (Days)": "5-40",
            "Daily RSI(14)": curr_rsi,
            "Volume[-1]": vol.iloc[-1],
            "20D Average Volume": ma20_vol.iloc[-1],
            "Trendline Touches": best_line['touches'] if best_line else 0,
            "Distance From Trendline (ATR units)": dist_atr,
            "Rank Score": 0.0
        }
        
        if results["Passed"]:
            s1 = min(100, best_line['touches'] * 20)
            s2 = min(100, (vol.iloc[-1] / ma20_vol.iloc[-1]) * 50)
            s3 = max(0, 100 - (rank - 1) * 10)
            s4 = max(0, 100 - abs(curr_rsi - 45) * 5)
            s5 = max(0, 100 - (dist_atr * 100))
            results["ClosenessScore"] = 0.3*s1 + 0.25*s2 + 0.2*s3 + 0.15*s4 + 0.1*s5
            results["Details"]["Rank Score"] = results["ClosenessScore"]

    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {str(e)}")
        
    return results