import pandas as pd
import numpy as np
import pandas_ta as ta

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    
    try:
        if len(df) < 130:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

        close = df['close'].values
        low = df['low'].values
        high = df['high'].values
        open_ = df['open'].values
        vol = df['volume'].values
        
        # 1. Pivot Detection
        def get_pivots(low_arr):
            pivots = []
            # Lookback 90 days, exclude last 3
            for i in range(len(low_arr) - 90, len(low_arr) - 3):
                if (low_arr[i] < low_arr[i-1] and low_arr[i] < low_arr[i-2] and low_arr[i] < low_arr[i-3] and
                    low_arr[i] < low_arr[i+1] and low_arr[i] < low_arr[i+2] and low_arr[i] < low_arr[i+3]):
                    pivots.append(i)
            return pivots

        pivots = get_pivots(low)
        
        # Rule 1: Trendline
        i2 = pivots[-1] if pivots else None
        i1 = None
        if i2:
            for p in reversed(pivots[:-1]):
                if i2 - p >= 25:
                    i1 = p
                    break
        
        if not i1 or not i2:
            failed_rules.append("No valid rising trendline")
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}
        
        slope = (low[i2] - low[i1]) / (i2 - i1)
        if slope <= 0:
            failed_rules.append("No valid rising trendline")
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}
        
        def get_tl(j): return low[i2] + slope * (j - i2)
        
        atr = ta.atr(df['high'], df['low'], df['close'], length=14).values
        for j in range(i2 + 1, len(df) - 1):
            if close[j] < (get_tl(j) - (0.75 * atr[j])):
                failed_rules.append("No valid rising trendline")
                break
        
        if failed_rules:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}

        # Rule 2: Bounce
        today = len(df) - 1
        tl_today = get_tl(today)
        if not (low[today] <= tl_today * 1.02 and close[today] >= tl_today and close[today] > open_[today] and close[today] <= tl_today * 1.06):
            failed_rules.append("Today is not a genuine bounce")
            
        # Rule 3: Backdrop
        ma126 = ta.sma(df['close'], length=126).iloc[-1]
        ma50 = ta.sma(df['close'], length=50).iloc[-1]
        if not (close[today] > ma126 and ma50 > ma126):
            failed_rules.append("Broader trend backdrop not intact")
            
        # Rule 4: RSI
        rsi = ta.rsi(df['close'], length=14).iloc[-1]
        if not (35 <= rsi <= 55):
            failed_rules.append("RSI outside range")
            
        # Rule 5: Liquidity
        ma_vol = ta.sma(df['volume'], length=20).iloc[-1]
        if not (ma_vol >= 100000 and close[today] >= 50):
            failed_rules.append("Minimum liquidity floor not met")
            
        # Rule 6: Sector
        s_rank = sector_ranks.get(symbol, 99)
        if s_rank > 10:
            failed_rules.append("Sector rank not in top 10")
            
        # Rule 7: Breadth
        if market_breadth < 40:
            failed_rules.append("Market breadth too low")

        if failed_rules:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}

        # Ranking
        slope_pct = slope / low[i2]
        t_score = min(100, slope_pct * 4000)
        s_score = max(0, 100 - (s_rank - 1) * 10)
        b_score = max(0, 100 - ((close[today] - tl_today) / tl_today * 100) * 25)
        r_score = max(0, 100 - abs(rsi - 45) * 4)
        rank_score = 0.3 * t_score + 0.25 * s_score + 0.25 * b_score + 0.2 * r_score

        details = {
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
            "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Sector Rank": s_rank,
            "Current Price": close[today],
            "Ideal Entry Price Low": tl_today,
            "Ideal Entry Price High": close[today],
            "Trendline Value (Today)": tl_today,
            "Trendline Slope (% per day)": slope_pct * 100,
            "Daily RSI(14)": rsi,
            "20D Average Volume": ma_vol,
            "Rank Score": rank_score
        }

        return {"Symbol": symbol, "Passed": True, "ClosenessScore": rank_score, "FailedRules": [], "Details": details}

    except Exception as e:
        return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": [f"Calculation error: {e}"], "Details": {}}