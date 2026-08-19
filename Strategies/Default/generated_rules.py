import pandas as pd
import pandas_ta as ta
import numpy as np

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    passed = False
    closeness_score = 0.0

    try:
        if len(df) < 126:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

        # Data preparation
        close = df['close']
        vol = df['volume']
        
        ma20 = ta.sma(close, length=20)
        ma50 = ta.sma(close, length=50)
        ma126 = ta.sma(close, length=126)
        rsi = ta.rsi(close, length=14)
        vol_ma20 = ta.sma(vol, length=20)
        highest_close_20 = close.rolling(window=20).max()

        # Current values
        c0 = close.iloc[-1]
        c1 = close.iloc[-2]
        c20_ago = close.iloc[-21] if len(df) > 20 else close.iloc[0]
        v0 = vol.iloc[-1]
        v1 = vol.iloc[-2]
        v2 = vol.iloc[-3]
        v_ma20 = vol_ma20.iloc[-1]
        
        rsi_val = rsi.iloc[-1]
        ma20_val = ma20.iloc[-1]
        ma50_val = ma50.iloc[-1]
        ma126_val = ma126.iloc[-1]
        h20 = highest_close_20.iloc[-1]
        
        sector_rank = sector_ranks.get(symbol, 99)

        # Mandatory Rules
        if not (v_ma20 >= 100000 and c0 >= 50):
            failed_rules.append("Liquidity floor (Vol MA20 >= 100k and Close >= 50)")
        
        if not (c0 > ma20_val > ma50_val > ma126_val):
            failed_rules.append("Trend structure (MA stack)")
            
        if not (55 <= rsi_val <= 75):
            failed_rules.append(f"RSI outside range (55-75): {rsi_val:.2f}")
            
        if not (v1 > v2 and v1 >= 1.3 * v_ma20):
            failed_rules.append("Volume confirmation (Breakout volume)")
            
        if not (c0 >= 0.98 * h20 and c0 > c1):
            failed_rules.append("Breakout proximity to 20-day high")
            
        if not (c0 <= 1.25 * c20_ago):
            failed_rules.append("Extended move (Close > 1.25 * Close[-20])")
            
        if not (sector_rank <= 10):
            failed_rules.append(f"Sector rank {sector_rank} not in top 10")
            
        if not (market_breadth >= 45):
            failed_rules.append(f"Market breadth {market_breadth} below 45")

        # Details
        details = {
            "RSI": float(rsi_val),
            "SectorRank": sector_rank,
            "Volume1": float(v1),
            "Volume2": float(v2),
            "VolumeMA20": float(v_ma20),
            "HighestClose20": float(h20),
            "Close": float(c0),
            "MarketBreadth": float(market_breadth)
        }

        if not failed_rules:
            passed = True
            # Ranking Score
            s_score = max(0, 100 - (sector_rank - 1) * 10)
            v_score = min(100, (v1 / v_ma20) * 40)
            b_score = max(0, 100 - ((h20 - c0) / h20 * 100) * 30)
            r_score = max(0, 100 - abs(rsi_val - 65) * 4)
            closeness_score = (0.3 * s_score) + (0.3 * v_score) + (0.25 * b_score) + (0.15 * r_score)
        else:
            closeness_score = 0.0

    except Exception as e:
        failed_rules.append(f"Calculation error: {str(e)}")
        passed = False

    return {
        "Symbol": symbol,
        "Passed": passed,
        "ClosenessScore": float(closeness_score),
        "FailedRules": failed_rules,
        "Details": details
    }