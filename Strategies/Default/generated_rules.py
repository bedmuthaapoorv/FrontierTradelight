import pandas as pd
import numpy as np
import pandas_ta as ta

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    results = {
        "Symbol": symbol,
        "Passed": False,
        "ClosenessScore": 0.0,
        "FailedRules": [],
        "Details": {}
    }

    try:
        if len(df) < 130:
            results["FailedRules"].append("Insufficient data length")
            return results

        # Data preparation
        close = df['close'].values
        low = df['low'].values
        high = df['high'].values
        open_ = df['open'].values
        vol = df['volume'].values
        idx = df.index
        
        # Indicators
        atr = ta.atr(df['high'], df['low'], df['close'], length=14)
        ma50 = ta.sma(df['close'], length=50)
        ma126 = ta.sma(df['close'], length=126)
        ma20_vol = ta.sma(df['volume'], length=20)
        rsi = ta.rsi(df['close'], length=14)
        
        curr_atr = atr.iloc[-1] if not atr.empty else 0
        curr_ma50 = ma50.iloc[-1]
        curr_ma126 = ma126.iloc[-1]
        curr_ma20_vol = ma20_vol.iloc[-1]
        curr_rsi = rsi.iloc[-1] if isinstance(rsi, pd.Series) else rsi.iloc[-1, 0]
        
        # Rule 7: Market Breadth
        if market_breadth < 40:
            results["FailedRules"].append(f"Market breadth {market_breadth:.1f} < 40")
            return results

        # Rule 6: Sector Strength
        s_rank = sector_ranks.get(symbol, 99)
        if s_rank > 10:
            results["FailedRules"].append(f"Sector rank {s_rank} > 10")
            return results

        # Rule 5: Liquidity
        if curr_ma20_vol < 100000 or close[-1] < 50:
            results["FailedRules"].append("Liquidity floor not met")
            return results

        # Rule 4: RSI
        if not (35 <= curr_rsi <= 55):
            results["FailedRules"].append(f"RSI {curr_rsi:.1f} outside range 35-55")
            return results

        # Rule 3: Backdrop
        if not (close[-1] > curr_ma126 and curr_ma50 > curr_ma126):
            results["FailedRules"].append("Trend backdrop not intact")
            return results

        # Rule 1: Pivot Detection
        lookback = 90
        pivot_candidates = []
        # Search range: last 90 days, excluding last 3
        for i in range(len(df) - 4, len(df) - 4 - lookback, -1):
            if i < 3: break
            if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i-3] and \
               low[i] < low[i+1] and low[i] < low[i+2] and low[i] < low[i+3]:
                pivot_candidates.append(i)
        
        pivot_candidates.sort()
        
        i2 = -1
        i1 = -1
        found_trend = False
        for p2 in reversed(pivot_candidates):
            for p1 in reversed(pivot_candidates):
                if p2 - p1 >= 25:
                    i2, i1 = p2, p1
                    found_trend = True
                    break
            if found_trend: break
            
        if not found_trend:
            results["FailedRules"].append("No valid rising trendline")
            return results
            
        slope = (low[i2] - low[i1]) / (i2 - i1)
        if slope <= 0:
            results["FailedRules"].append("No valid rising trendline")
            return results
            
        def get_tl(j): return low[i2] + slope * (j - i2)
        
        # Check for break
        for j in range(i2 + 1, len(df) - 1):
            if close[j] < (get_tl(j) - (0.75 * atr.iloc[j])):
                results["FailedRules"].append("No valid rising trendline")
                return results

        # Rule 2: Bounce
        today = len(df) - 1
        tl_today = get_tl(today)
        if not (low[today] <= tl_today * 1.02 and close[today] >= tl_today and \
                close[today] > open_[today] and close[today] <= tl_today * 1.06):
            results["FailedRules"].append("Today is not a genuine bounce")
            return results

        # Scoring
        slope_pct = slope / low[i2]
        tl_score = min(100, slope_pct * 4000)
        sec_score = max(0, 100 - (s_rank - 1) * 10)
        bounce_score = max(0, 100 - ((close[today] - tl_today) / tl_today * 100) * 25)
        rsi_score = max(0, 100 - abs(curr_rsi - 45) * 4)
        
        rank_score = (0.30 * tl_score) + (0.25 * sec_score) + (0.25 * bounce_score) + (0.20 * rsi_score)
        
        results.update({
            "Passed": True,
            "ClosenessScore": rank_score,
            "Details": {
                "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
                "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
                "Sector Rank": s_rank,
                "Current Price": close[today],
                "Ideal Entry Price Low": tl_today,
                "Ideal Entry Price High": close[today],
                "Ideal Exit Price": tl_today + 2.5 * curr_atr,
                "Swing Duration (Days)": "5-40",
                "Trendline Value (Today)": tl_today,
                "Trendline Slope (% per day)": slope_pct * 100,
                "Daily RSI(14)": curr_rsi,
                "20D Average Volume": curr_ma20_vol,
                "Rank Score": rank_score
            }
        })
        return results

    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {str(e)}")
        return results