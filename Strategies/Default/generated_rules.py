import pandas as pd
import pandas_ta as ta
import numpy as np

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    results = {
        "Symbol": symbol,
        "Passed": False,
        "ClosenessScore": 0.0,
        "FailedRules": [],
        "Details": {}
    }

    try:
        if df is None or len(df) < 50:
            results["FailedRules"].append("Insufficient data")
            return results

        # Data preparation
        close = df['close'].values
        volume = df['volume'].values
        high = df['high'].values
        low = df['low'].values
        
        # Indicators
        ma20 = ta.sma(df['close'], length=20)
        ma50 = ta.sma(df['close'], length=50)
        ma126 = ta.sma(df['close'], length=126)
        rsi = ta.rsi(df['close'], length=14)
        vol_ma50 = ta.sma(df['volume'], length=50)
        
        # Turnover calculation
        turnover = df['volume'] * df['close']
        ma_turnover20 = turnover.rolling(window=20).mean()
        
        # Values at last session (index -1)
        c_curr = close[-1]
        c_prev = close[-2]
        c_20d_ago = close[-21] if len(close) > 20 else close[0]
        v_curr = volume[-1]
        v_prev = volume[-2]
        
        ma20_val = ma20.iloc[-1]
        ma50_val = ma50.iloc[-1]
        ma126_val = ma126.iloc[-1]
        rsi_val = rsi.iloc[-1]
        vol_ma50_val = vol_ma50.iloc[-1]
        turnover_ma20_val = ma_turnover20.iloc[-1]
        h20 = np.max(close[-20:])
        
        # Mandatory Rules
        failed = []
        
        if not (turnover_ma20_val >= 50000000 and c_curr >= 50):
            failed.append("Rule 1: Minimum Liquidity Floor (Turnover/Price)")
            
        if not (c_curr > ma20_val and ma20_val > ma50_val and ma50_val > ma126_val):
            failed.append("Rule 2: Trend Structure (MA Stack)")
            
        if not (55 <= rsi_val <= 75):
            failed.append(f"Rule 3: RSI outside range (RSI: {rsi_val:.2f})")
            
        if not (v_curr >= 2.5 * vol_ma50_val):
            failed.append("Rule 4: Volume Confirmation (50D/2.5x)")
            
        if not (c_curr >= 0.98 * h20 and c_curr > c_prev):
            failed.append("Rule 5: Breakout Proximity to 20D High")
            
        if not (c_curr <= 1.25 * c_20d_ago):
            failed.append("Rule 6: Already Extended Too Far")
            
        rank = sector_ranks.get(symbol, 99)
        if not (rank <= 10):
            failed.append(f"Rule 7: Sector rank {rank} not in top 10")
            
        if not (market_breadth >= 45):
            failed.append(f"Rule 8: Market Breadth {market_breadth} below 45")

        results["FailedRules"] = failed
        results["Passed"] = len(failed) == 0
        
        # Ranking Score
        s_score = max(0, 100 - (rank - 1) * 10)
        v_score = min(100, (v_curr / vol_ma50_val) * 40)
        bq_score = max(0, 100 - ((h20 - c_curr) / h20 * 100) * 30)
        rsi_score = max(0, 100 - abs(rsi_val - 65) * 4)
        
        results["ClosenessScore"] = (0.3 * s_score) + (0.3 * v_score) + (0.25 * bq_score) + (0.15 * rsi_score)
        
        # Details
        meta = universe.get(symbol, {"Name": "Unknown", "Sector": "Unknown"})
        results["Details"] = {
            "Symbol": symbol,
            "Company Name": meta["Name"],
            "Sector": meta["Sector"],
            "Sector Rank": rank,
            "Current Price": c_curr,
            "Ideal Entry Price Low": c_curr,
            "Ideal Entry Price High": c_curr * 1.01,
            "Daily RSI(14)": rsi_val,
            "Volume[-1]": v_curr,
            "Volume[-2]": v_prev,
            "50D Average Volume": vol_ma50_val,
            "Volume[-1] / 50D Avg (ratio)": v_curr / vol_ma50_val,
            "20-Day High": h20,
            "Distance From 20-Day High (%)": ((h20 - c_curr) / h20) * 100,
            "Close vs Close[-20] (%)": ((c_curr - c_20d_ago) / c_20d_ago) * 100,
            "Rank Score": results["ClosenessScore"]
        }
        
    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {str(e)}")
        
    return results