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

        # Data Prep
        close = df['close'].values
        low = df['low'].values
        vol = df['volume'].values
        turnover = vol * close
        
        # Indicators
        ma20_vol = pd.Series(vol).rolling(20).mean().iloc[-1]
        ma20_turnover = pd.Series(turnover).rolling(20).mean().iloc[-1]
        ma100 = pd.Series(close).rolling(100).mean()
        atr14 = ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1]
        rsi14 = ta.rsi(df['close'], length=14)
        current_rsi = rsi14.iloc[-1] if isinstance(rsi14, pd.Series) else rsi14.iloc[-1, 0]

        # Rule 1: Liquidity
        if ma20_turnover < 50000000 or close[-1] < 50:
            results["FailedRules"].append("Liquidity floor not met")

        # Rule 2: Uptrend
        if not (close[-1] > ma100.iloc[-1] and ma100.iloc[-1] > ma100.iloc[-10]):
            results["FailedRules"].append("Uptrend context not met")

        # Rule 3: Trendline
        best_line = None
        for window in [250, 150, 100, 60]:
            if len(df) < window: continue
            subset_lows = low[-window:]
            pivot_indices = argrelextrema(subset_lows, np.less_equal, order=4)[0]
            if len(pivot_indices) < 3: continue
            
            fit_indices = pivot_indices.copy()
            fit_lows = subset_lows[fit_indices]
            
            for _ in range(int(np.ceil(0.1 * len(pivot_indices)))):
                slope, intercept = np.polyfit(fit_indices, fit_lows, 1)
                residuals = fit_lows - (slope * fit_indices + intercept)
                worst_idx = np.argmin(residuals)
                if residuals[worst_idx] < -1.0 * atr14:
                    fit_indices = np.delete(fit_indices, worst_idx)
                    fit_lows = np.delete(fit_lows, worst_idx)
                else: break
            
            slope, intercept = np.polyfit(fit_indices, fit_lows, 1)
            if slope <= 0: continue
            
            touches = sum(1 for i in pivot_indices if abs(subset_lows[i] - (slope * i + intercept)) <= 1.0 * atr14)
            if touches < 4: continue
            
            broken = all((subset_lows[-(i+1)] < (slope * (window - 1 - i) + intercept) - 1.5 * atr14) for i in range(3))
            if broken: continue
            
            best_line = {"slope": slope, "intercept": intercept, "touches": touches, "window": window}
            break
        
        if not best_line:
            results["FailedRules"].append("No qualifying ascending trendline")
        
        # Rule 4-8
        proj_today = best_line['slope'] * (best_line['window'] - 1) + best_line['intercept'] if best_line else 0
        dist_atr = abs(close[-1] - proj_today) / atr14 if best_line else 99
        
        if best_line and not (low[-1] <= proj_today + atr14 and close[-1] > close[-2] and vol[-1] >= 1.2 * ma20_vol):
            results["FailedRules"].append("Bounce confirmation failed")
        if not (35 <= current_rsi <= 55):
            results["FailedRules"].append(f"RSI outside range ({current_rsi:.1f})")
        if not (close[-1] <= 1.15 * close[-11]):
            results["FailedRules"].append("Already extended off low")
        
        sector_rank = sector_ranks.get(symbol, 99)
        if sector_rank > 10:
            results["FailedRules"].append(f"Sector rank {sector_rank} not in top 10")
        if market_breadth < 45:
            results["FailedRules"].append(f"Market breadth {market_breadth} below 45")

        # Finalize
        if not results["FailedRules"]:
            results["Passed"] = True
            # Scoring
            tl_score = min(100, best_line['touches'] * 20)
            bs_score = min(100, (vol[-1] / ma20_vol) * 50)
            ss_score = max(0, 100 - (sector_rank - 1) * 10)
            rsi_score = max(0, 100 - abs(current_rsi - 45) * 5)
            prox_score = max(0, 100 - (dist_atr * 100))
            results["ClosenessScore"] = 0.3*tl_score + 0.25*bs_score + 0.2*ss_score + 0.15*rsi_score + 0.1*prox_score

        results["Details"] = {
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
            "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Sector Rank": sector_rank,
            "Current Price": close[-1],
            "Ideal Entry Price Low": close[-1],
            "Ideal Entry Price High": close[-1] * 1.01,
            "Daily RSI(14)": current_rsi,
            "Volume[-1]": vol[-1],
            "20D Average Volume": ma20_vol,
            "Trendline Touches": best_line['touches'] if best_line else 0,
            "Distance From Trendline (ATR units)": dist_atr,
            "Rank Score": results["ClosenessScore"]
        }
    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {str(e)}")
        
    return results