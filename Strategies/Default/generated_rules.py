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
        if df is None or len(df) < 126:
            results["FailedRules"].append("Insufficient data history")
            return results

        # Data preparation
        close = df['close']
        volume = df['volume']
        
        # Indicators
        ma20 = ta.sma(close, length=20)
        ma50 = ta.sma(close, length=50)
        ma126 = ta.sma(close, length=126)
        rsi = ta.rsi(close, length=14)
        vol_ma20 = ta.sma(volume, length=20)
        
        # Current values
        curr_close = close.iloc[-1]
        prev_close = close.iloc[-2]
        prev20_close = close.iloc[-21] if len(df) >= 21 else close.iloc[0]
        
        curr_vol = volume.iloc[-1]
        prev_vol = volume.iloc[-2]
        curr_vol_ma20 = vol_ma20.iloc[-1]
        
        curr_ma20 = ma20.iloc[-1]
        curr_ma50 = ma50.iloc[-1]
        curr_ma126 = ma126.iloc[-1]
        curr_rsi = rsi.iloc[-1]
        
        highest_close_20 = close.iloc[-20:].max()
        
        # Metadata
        stock_info = universe.get(symbol, {"Name": "Unknown", "Sector": "Unknown"})
        sector_rank = sector_ranks.get(symbol, 99)
        
        # Mandatory Rules
        failed = []
        
        if not (curr_vol_ma20 >= 100000 and curr_close >= 50):
            failed.append("Liquidity floor not met")
            
        if not (curr_close > curr_ma20 > curr_ma50 > curr_ma126):
            failed.append("Trend structure (MA stack) not met")
            
        if not (55 <= curr_rsi <= 75):
            failed.append(f"RSI outside range ({curr_rsi:.1f})")
            
        if not (prev_vol > volume.iloc[-3] and prev_vol >= 1.3 * vol_ma20.iloc[-2]):
            failed.append("Volume confirmation not met")
            
        if not (curr_close >= 0.98 * highest_close_20 and curr_close > prev_close):
            failed.append("Breakout proximity not met")
            
        if not (curr_close <= 1.25 * prev20_close):
            failed.append("Stock extended too far")
            
        if not (sector_rank <= 10):
            failed.append(f"Sector rank {sector_rank} not in top 10")
            
        if not (market_breadth >= 45):
            failed.append(f"Market breadth {market_breadth} below threshold")

        # Details population
        results["Details"] = {
            "Company Name": stock_info["Name"],
            "Sector": stock_info["Sector"],
            "Sector Rank": sector_rank,
            "Current Price": curr_close,
            "Daily RSI(14)": curr_rsi,
            "Volume[-1]": prev_vol,
            "Volume[-2]": volume.iloc[-3],
            "20D Average Volume": vol_ma20.iloc[-2],
            "Volume[-1] / 20D Avg (ratio)": prev_vol / vol_ma20.iloc[-2] if vol_ma20.iloc[-2] > 0 else 0,
            "20-Day High": highest_close_20,
            "Distance From 20-Day High (%)": ((highest_close_20 - curr_close) / highest_close_20) * 100,
            "Close vs Close[-20] (%)": ((curr_close - prev20_close) / prev20_close) * 100
        }

        # Scoring
        if not failed:
            s_score = max(0, 100 - (sector_rank - 1) * 10)
            v_score = min(100, (prev_vol / vol_ma20.iloc[-2]) * 40)
            b_score = max(0, 100 - ((highest_close_20 - curr_close) / highest_close_20 * 100) * 30)
            r_score = max(0, 100 - abs(curr_rsi - 65) * 4)
            
            rank_score = (0.3 * s_score) + (0.3 * v_score) + (0.25 * b_score) + (0.15 * r_score)
            results["ClosenessScore"] = rank_score
            results["Details"]["Rank Score"] = rank_score
            results["Passed"] = True
        else:
            results["FailedRules"] = failed
            results["ClosenessScore"] = 0.0

    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {str(e)}")
        
    return results