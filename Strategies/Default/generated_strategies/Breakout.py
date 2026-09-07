import pandas as pd
import pandas_ta as ta
import numpy as np

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    passed = False
    rank_score = 0.0

    try:
        if df is None or len(df) < 126:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

        # Data preparation
        close = df['close']
        volume = df['volume']
        
        ma20 = ta.sma(close, length=20)
        ma50 = ta.sma(close, length=50)
        ma126 = ta.sma(close, length=126)
        vol_ma20 = ta.sma(volume, length=20)
        rsi = ta.rsi(close, length=14)
        
        # Current values
        curr_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        prev20_close = close.iloc[-21] if len(close) > 20 else close.iloc[0]
        
        curr_vol = volume.iloc[-1]
        prev_vol = volume.iloc[-2]
        curr_ma20 = ma20.iloc[-1]
        curr_ma50 = ma50.iloc[-1]
        curr_ma126 = ma126.iloc[-1]
        curr_vol_ma20 = vol_ma20.iloc[-1]
        curr_rsi = rsi.iloc[-1]
        highest_close_20 = close.iloc[-20:].max()
        
        # Mandatory Filters
        if not (curr_vol_ma20 >= 100000 and curr_close >= 50):
            failed_rules.append("Minimum Liquidity Floor")
        
        if not (curr_close > curr_ma20 > curr_ma50 > curr_ma126):
            failed_rules.append("Trend Structure (Moving Average Stack)")
            
        if not (55 <= curr_rsi <= 75):
            failed_rules.append(f"RSI outside range (RSI: {curr_rsi:.2f})")
            
        if not (prev_vol > volume.iloc[-3] and prev_vol >= 1.3 * vol_ma20.iloc[-2]):
            failed_rules.append("Volume not increasing or insufficient breakout volume")
            
        if not (curr_close >= 0.98 * highest_close_20 and curr_close > prev_close):
            failed_rules.append("Breakout Proximity to Short-Term High")
            
        if not (curr_close <= 1.25 * prev20_close):
            failed_rules.append("Stock extended too far")
            
        sector_rank = sector_ranks.get(symbol, 99)
        if not (sector_rank <= 10):
            failed_rules.append(f"Sector rank {sector_rank} not in top 10")
            
        if not (market_breadth >= 45):
            failed_rules.append(f"Market breadth {market_breadth} below threshold")

        passed = len(failed_rules) == 0

        # Scoring
        if passed:
            s_score = max(0, 100 - (sector_rank - 1) * 10)
            v_score = min(100, (prev_vol / vol_ma20.iloc[-2]) * 40)
            b_score = max(0, 100 - ((highest_close_20 - curr_close) / highest_close_20 * 100) * 30)
            r_score = max(0, 100 - abs(curr_rsi - 65) * 4)
            rank_score = (0.3 * s_score) + (0.3 * v_score) + (0.25 * b_score) + (0.15 * r_score)

        # Details
        details = {
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
            "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Sector Rank": sector_rank,
            "Current Price": curr_close,
            "Ideal Entry Price Low": curr_close,
            "Ideal Entry Price High": curr_close * 1.01,
            "Daily RSI(14)": curr_rsi,
            "Volume[-1]": prev_vol,
            "Volume[-2]": volume.iloc[-3],
            "20D Average Volume": vol_ma20.iloc[-2],
            "Volume[-1] / 20D Avg (ratio)": prev_vol / vol_ma20.iloc[-2] if vol_ma20.iloc[-2] > 0 else 0,
            "20-Day High": highest_close_20,
            "Distance From 20-Day High (%)": ((highest_close_20 - curr_close) / highest_close_20) * 100,
            "Close vs Close[-20] (%)": ((curr_close - prev20_close) / prev20_close) * 100,
            "Rank Score": rank_score
        }

    except Exception as e:
        failed_rules.append(f"Calculation error: {e}")
        passed = False

    return {
        "Symbol": symbol,
        "Passed": passed,
        "ClosenessScore": rank_score,
        "FailedRules": failed_rules,
        "Details": details
    }