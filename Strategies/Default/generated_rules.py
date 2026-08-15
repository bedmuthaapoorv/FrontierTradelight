import pandas as pd
import numpy as np
import pandas_ta as ta
from scipy.signal import argrelextrema

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    passed = False
    closeness_score = 0.0

    try:
        if len(df) < 100:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

        # Basic Indicators
        close = df['close']
        low = df['low']
        vol = df['volume']
        atr = ta.atr(df['high'], df['low'], close, length=14).iloc[-1]
        ma20_vol = vol.rolling(20).mean().iloc[-1]
        ma100 = close.rolling(100).mean()
        
        # Rule 1: Liquidity
        if ma20_vol < 100000 or close.iloc[-1] < 50:
            failed_rules.append("Liquidity floor not met")

        # Rule 2: Uptrend
        if not (close.iloc[-1] > ma100.iloc[-1] and ma100.iloc[-1] > ma100.iloc[-10]):
            failed_rules.append("Not in uptrend")

        # Rule 3: Trendline Detection
        pivots = argrelextrema(low.values[-100:], np.less_equal, order=4)[0]
        pivot_indices = pivots + (len(df) - 100)
        
        best_line = None
        max_touches = 0
        
        if len(pivots) >= 2:
            for i in range(len(pivots)):
                for j in range(i + 1, len(pivots)):
                    idx1, idx2 = pivot_indices[i], pivot_indices[j]
                    if idx2 - idx1 < 10: continue
                    
                    slope = (low.iloc[idx2] - low.iloc[idx1]) / (idx2 - idx1)
                    if slope <= 0: continue
                    
                    intercept = low.iloc[idx1] - slope * idx1
                    
                    touches = 0
                    for p_idx in pivot_indices:
                        proj = slope * p_idx + intercept
                        if abs(low.iloc[p_idx] - proj) <= atr:
                            touches += 1
                    
                    # Breakdown check
                    breakdown = False
                    for k in range(len(df) - 100, len(df)):
                        proj = slope * k + intercept
                        if (proj - close.iloc[k]) > 1.5 * atr:
                            breakdown = True
                            break
                    
                    if not breakdown and touches >= 3 and touches > max_touches:
                        max_touches = touches
                        best_line = (slope, intercept)

        if not best_line:
            failed_rules.append("No valid ascending trendline found")
        else:
            slope, intercept = best_line
            proj_today = slope * (len(df) - 1) + intercept
            dist_atr = abs(low.iloc[-1] - proj_today) / atr
            
            # Rule 4: Bounce
            if not (low.iloc[-1] <= proj_today + atr and close.iloc[-1] > close.iloc[-2] and vol.iloc[-1] >= 1.2 * ma20_vol):
                failed_rules.append("Bounce confirmation failed")

            # Rule 5: RSI
            rsi = ta.rsi(close, length=14).iloc[-1]
            if not (35 <= rsi <= 55):
                failed_rules.append(f"RSI outside range ({rsi:.1f})")

            # Rule 6: Extension
            if close.iloc[-1] > 1.15 * close.iloc[-10]:
                failed_rules.append("Stock already extended")

            # Rule 7: Sector
            rank = sector_ranks.get(symbol, 99)
            if rank > 10:
                failed_rules.append(f"Sector rank {rank} not in top 10")

            # Rule 8: Breadth
            if market_breadth < 45:
                failed_rules.append("Market breadth too low")

            if not failed_rules:
                passed = True
                # Ranking
                tl_score = min(100, max_touches * 20)
                bnc_score = min(100, (vol.iloc[-1] / ma20_vol) * 50)
                sec_score = max(0, 100 - (rank - 1) * 10)
                rsi_score = max(0, 100 - abs(rsi - 45) * 5)
                prox_score = max(0, 100 - (dist_atr * 100))
                closeness_score = (0.3 * tl_score) + (0.25 * bnc_score) + (0.2 * sec_score) + (0.15 * rsi_score) + (0.1 * prox_score)

            details = {
                "RSI": rsi, "SectorRank": rank, "TrendlineTouches": max_touches,
                "Volume1": vol.iloc[-1], "Volume20Avg": ma20_vol, "DistanceATR": dist_atr
            }

    except Exception as e:
        failed_rules.append(f"Calculation error: {e}")

    return {
        "Symbol": symbol,
        "Passed": passed,
        "ClosenessScore": closeness_score,
        "FailedRules": failed_rules,
        "Details": details
    }