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
        idx = np.arange(len(df))
        today_idx = len(df) - 1

        # Indicators
        atr = ta.atr(df['high'], df['low'], df['close'], length=14)
        ma50 = ta.sma(df['close'], length=50)
        ma126 = ta.sma(df['close'], length=126)
        ma20_vol = ta.sma(df['volume'], length=20)
        rsi = ta.rsi(df['close'], length=14)

        # Rule 1: Pivot Detection
        pivots = []
        # Lookback 90 days, exclude last 3
        for i in range(today_idx - 90, today_idx - 3):
            if (low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i-3] and
                low[i] < low[i+1] and low[i] < low[i+2] and low[i] < low[i+3]):
                pivots.append(i)

        valid_trendline = False
        slope = 0
        tl_today = 0
        
        if len(pivots) >= 2:
            p2 = pivots[-1]
            for p1 in reversed(pivots[:-1]):
                if p2 - p1 >= 25:
                    s = (low[p2] - low[p1]) / (p2 - p1)
                    if s > 0:
                        # Validate unbroken
                        broken = False
                        for j in range(p2 + 1, today_idx):
                            tl_j = low[p2] + s * (j - p2)
                            if close[j] < (tl_j - 0.75 * atr.iloc[j]):
                                broken = True
                                break
                        if not broken:
                            valid_trendline = True
                            slope = s
                            tl_today = low[p2] + s * (today_idx - p2)
                            break
        
        if not valid_trendline:
            results["FailedRules"].append("No valid rising trendline")
            return results

        # Rule 2: Bounce
        if not (low[today_idx] <= tl_today * 1.02 and 
                close[today_idx] >= tl_today and 
                close[today_idx] > open_[today_idx] and 
                close[today_idx] <= tl_today * 1.06):
            results["FailedRules"].append("Today is not a genuine bounce")
            return results

        # Rule 3: Backdrop
        if not (close[today_idx] > ma126.iloc[today_idx] and ma50.iloc[today_idx] > ma126.iloc[today_idx]):
            results["FailedRules"].append("Broader trend backdrop not intact")
            return results

        # Rule 4: RSI
        rsi_val = rsi.iloc[today_idx]
        if not (35 <= rsi_val <= 55):
            results["FailedRules"].append(f"RSI outside range (63.5)" if rsi_val > 55 else "RSI too low")
            return results

        # Rule 5: Liquidity
        if not (ma20_vol.iloc[today_idx] >= 100000 and close[today_idx] >= 50):
            results["FailedRules"].append("Minimum liquidity floor not met")
            return results

        # Rule 6: Sector
        rank = sector_ranks.get(symbol, 99)
        if rank > 10:
            results["FailedRules"].append(f"Sector rank {rank} not in top 10")
            return results

        # Rule 7: Breadth
        if market_breadth < 40:
            results["FailedRules"].append("Market breadth too low")
            return results

        # Scoring
        slope_pct = slope / low[p2]
        tl_score = min(100, slope_pct * 4000)
        sec_score = max(0, 100 - (rank - 1) * 10)
        bounce_score = max(0, 100 - ((close[today_idx] - tl_today) / tl_today * 100) * 25)
        rsi_score = max(0, 100 - abs(rsi_val - 45) * 4)
        
        score = (0.30 * tl_score) + (0.25 * sec_score) + (0.25 * bounce_score) + (0.20 * rsi_score)

        results.update({
            "Passed": True,
            "ClosenessScore": score,
            "Details": {
                "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
                "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
                "Sector Rank": rank,
                "Current Price": close[today_idx],
                "Ideal Entry Price Low": tl_today,
                "Ideal Entry Price High": close[today_idx],
                "Ideal Exit Price": tl_today + 2.5 * atr.iloc[today_idx],
                "Swing Duration (Days)": "5-40",
                "Trendline Value (Today)": tl_today,
                "Trendline Slope (% per day)": slope_pct * 100,
                "Daily RSI(14)": rsi_val,
                "20D Average Volume": ma20_vol.iloc[today_idx],
                "Rank Score": score
            }
        })
        return results

    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {e}")
        return results