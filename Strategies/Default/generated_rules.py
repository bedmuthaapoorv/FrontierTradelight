import pandas as pd
import numpy as np
import pandas_ta as ta
from scipy.signal import argrelextrema

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    
    try:
        if len(df) < 60:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data (< 60 days)"], "Details": {}}

        # Data Prep
        df = df.copy()
        close = df['close']
        low = df['low']
        vol = df['volume']
        turnover = vol * close
        
        # Indicators
        ma20_vol = turnover.rolling(20).mean()
        ma100 = close.rolling(100).mean()
        atr14 = ta.atr(df['high'], df['low'], df['close'], length=14)
        if atr14 is None: atr14 = pd.Series(0, index=df.index)
        atr14_val = atr14.iloc[-1]
        
        rsi = ta.rsi(close, length=14)
        rsi_val = rsi.iloc[-1] if rsi is not None else 50
        
        # Rule 1: Liquidity
        if ma20_vol.iloc[-1] < 50000000 or close.iloc[-1] < 50:
            failed_rules.append("Liquidity or Price floor not met")
            
        # Rule 2: Uptrend
        if not (close.iloc[-1] > ma100.iloc[-1] and ma100.iloc[-1] > ma100.iloc[-11]):
            failed_rules.append("Uptrend context not met")
            
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
            max_drops = int(np.ceil(0.1 * len(pivots)))
            for _ in range(max_drops):
                slope, intercept = np.polyfit(fit_indices, fit_lows, 1)
                residuals = fit_lows - (slope * fit_indices + intercept)
                worst_idx = np.argmin(residuals)
                if residuals[worst_idx] < -1.0 * atr14_val:
                    fit_indices = np.delete(fit_indices, worst_idx)
                    fit_lows = np.delete(fit_lows, worst_idx)
                else: break
            
            if slope <= 0: continue
            
            touches = 0
            for i in pivots:
                if abs(subset['low'].iloc[i] - (slope * i + intercept)) <= 1.0 * atr14_val:
                    touches += 1
            
            if touches >= 4:
                broken = True
                for i in range(window - 3, window):
                    if not (subset['close'].iloc[i] < (slope * i + intercept) - 1.5 * atr14_val):
                        broken = False
                        break
                if not broken and touches > max_touches:
                    max_touches = touches
                    best_line = (slope, intercept, window)
        
        if not best_line:
            failed_rules.append("No qualifying ascending trendline found")
        else:
            slope, intercept, window = best_line
            proj_today = slope * (window - 1) + intercept
            
            # Rule 4: Bounce
            vol_ma20 = vol.rolling(20).mean()
            if not (low.iloc[-1] <= proj_today + atr14_val and close.iloc[-1] > close.iloc[-2] and vol.iloc[-1] >= 1.2 * vol_ma20.iloc[-1]):
                failed_rules.append("Bounce confirmation failed")
                
            # Rule 5: RSI
            if not (35 <= rsi_val <= 55):
                failed_rules.append(f"RSI outside range ({rsi_val:.1f})")
                
            # Rule 6: Extension
            if close.iloc[-1] > 1.15 * close.iloc[-11]:
                failed_rules.append("Stock already extended")
                
        # Rule 7 & 8
        rank = sector_ranks.get(symbol, 99)
        if rank > 10: failed_rules.append(f"Sector rank {rank} not in top 10")
        if market_breadth < 45: failed_rules.append("Market breadth too low")
        
        passed = len(failed_rules) == 0
        
        # Scoring
        score = 0.0
        if best_line:
            dist_atr = abs(low.iloc[-1] - proj_today) / atr14_val if atr14_val > 0 else 0
            score = (min(100, max_touches * 20) * 0.3) + \
                    (min(100, (vol.iloc[-1] / vol_ma20.iloc[-1]) * 50) * 0.25) + \
                    (max(0, 100 - (rank - 1) * 10) * 0.2) + \
                    (max(0, 100 - abs(rsi_val - 45) * 5) * 0.15) + \
                    (max(0, 100 - (dist_atr * 100)) * 0.1)
        
        details = {
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
            "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Sector Rank": rank,
            "Current Price": close.iloc[-1],
            "Ideal Entry Price Low": close.iloc[-1],
            "Ideal Entry Price High": close.iloc[-1] * 1.01,
            "Daily RSI(14)": rsi_val,
            "Volume[-1]": vol.iloc[-1],
            "20D Average Volume": vol_ma20.iloc[-1],
            "Trendline Touches": max_touches if best_line else 0,
            "Distance From Trendline (ATR units)": abs(low.iloc[-1] - proj_today) / atr14_val if best_line and atr14_val > 0 else 0,
            "Rank Score": score
        }
        
        return {"Symbol": symbol, "Passed": passed, "ClosenessScore": score, "FailedRules": failed_rules, "Details": details}
        
    except Exception as e:
        return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": [f"Calculation error: {e}"], "Details": {}}