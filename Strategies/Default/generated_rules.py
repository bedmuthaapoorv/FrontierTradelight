import pandas as pd
import numpy as np
import pandas_ta as ta

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    
    try:
        if df is None or len(df) < 50:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

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
        
        # Values for logic
        curr_close = close[-1]
        prev_close = close[-2]
        prev20_close = close[-21] if len(close) > 20 else close[0]
        curr_vol = volume[-1]
        curr_vol_ma50 = vol_ma50.iloc[-1]
        
        # Rule 1: Liquidity
        turnover_ma20 = ta.sma(df['volume'] * df['close'], length=20).iloc[-1]
        if turnover_ma20 < 50000000 or curr_close < 50:
            failed_rules.append("Rule 1: Liquidity floor (Turnover < 5cr or Price < 50)")
            
        # Rule 2: Trend
        if not (curr_close > ma20.iloc[-1] > ma50.iloc[-1] > ma126.iloc[-1]):
            failed_rules.append("Rule 2: Moving average stack not aligned")
            
        # Rule 3: RSI
        curr_rsi = rsi.iloc[-1]
        if not (55 <= curr_rsi <= 75):
            failed_rules.append(f"Rule 3: RSI outside range (55-75): {curr_rsi:.2f}")
            
        # Rule 4: Volume
        if np.isnan(curr_vol_ma50) or curr_vol < 2.5 * curr_vol_ma50:
            failed_rules.append("Rule 4: Volume confirmation failed")
            
        # Rule 5: Proximity
        h20 = df['close'].rolling(20).max().iloc[-1]
        if not (curr_close >= 0.98 * h20 and curr_close > prev_close):
            failed_rules.append("Rule 5: Not pushing to 20-day high")
            
        # Rule 6: Extension
        if curr_close > 1.25 * prev20_close:
            failed_rules.append("Rule 6: Already extended too far")
            
        # Rule 7: Sector
        rank = sector_ranks.get(symbol, 99)
        if rank > 10:
            failed_rules.append(f"Rule 7: Sector rank {rank} not in top 10")
            
        # Rule 8: Breadth
        if market_breadth < 45:
            failed_rules.append(f"Rule 8: Market breadth {market_breadth} below 45")

        # Details
        details.update({
            "Company Name": universe.get(symbol, {}).get("Name", "Unknown"),
            "Sector": universe.get(symbol, {}).get("Sector", "Unknown"),
            "Sector Rank": rank,
            "Current Price": curr_close,
            "Ideal Entry Price Low": curr_close,
            "Ideal Entry Price High": curr_close * 1.01,
            "Daily RSI(14)": curr_rsi,
            "Volume[-1]": curr_vol,
            "Volume[-2]": volume[-2],
            "50D Average Volume": curr_vol_ma50,
            "Volume[-1] / 50D Avg (ratio)": curr_vol / curr_vol_ma50 if curr_vol_ma50 > 0 else 0,
            "20-Day High": h20,
            "Distance From 20-Day High (%)": ((h20 - curr_close) / h20) * 100,
            "Close vs Close[-20] (%)": ((curr_close - prev20_close) / prev20_close) * 100
        })

        # Ranking
        passed = len(failed_rules) == 0
        score = 0.0
        if passed:
            s_score = max(0, 100 - (rank - 1) * 10)
            v_score = min(100, (curr_vol / curr_vol_ma50) * 40)
            b_score = max(0, 100 - ((h20 - curr_close) / h20 * 100) * 30)
            r_score = max(0, 100 - abs(curr_rsi - 65) * 4)
            score = (0.3 * s_score) + (0.3 * v_score) + (0.25 * b_score) + (0.15 * r_score)
        
        details["Rank Score"] = score
        
        return {
            "Symbol": symbol,
            "Passed": passed,
            "ClosenessScore": score,
            "FailedRules": failed_rules,
            "Details": details
        }

    except Exception as e:
        return {
            "Symbol": symbol,
            "Passed": False,
            "ClosenessScore": 0.0,
            "FailedRules": [f"Calculation error: {e}"],
            "Details": {}
        }