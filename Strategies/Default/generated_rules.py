import pandas as pd
import pandas_ta as ta
from common_methods import detect_pivot_lows, find_rising_trendline, liquidity_ok, sector_rank, ta_column

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    try:
        if len(df) < 130:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}
        
        failed_rules = []
        T = len(df) - 1
        low = df['low'].values
        close = df['close'].values
        open_p = df['open'].values
        
        # Rule 7: Market Breadth
        if market_breadth < 40:
            failed_rules.append(f"Market breadth {market_breadth:.1f} below 40")
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}

        # Rule 1: Trendline
        pivots = detect_pivot_lows(low, T - 90, T - 3, window=3)
        if len(pivots) < 2:
            failed_rules.append("No valid rising trendline")
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}
        
        atr = ta_column(ta.atr(df['high'], df['low'], df['close'], length=14))
        tl = find_rising_trendline(low, close, atr.values if atr is not None else None, pivots, min_gap=25, break_atr_mult=0.75)
        
        if not tl:
            failed_rules.append("No valid rising trendline")
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}
        
        tl_today = tl['anchor_price'] + tl['slope'] * (T - tl['p2'])
        
        # Rule 2: Bounce
        if not (low[T] <= tl_today * 1.02 and close[T] >= tl_today and close[T] > open_p[T] and close[T] <= tl_today * 1.06):
            failed_rules.append("Today is not a genuine bounce off the trendline")
        
        # Rule 3: Backdrop
        ma50 = ta_column(ta.sma(df['close'], length=50))
        ma126 = ta_column(ta.sma(df['close'], length=126))
        if not (close[T] > ma126.iloc[-1] and ma50.iloc[-1] > ma126.iloc[-1]):
            failed_rules.append("Broader trend backdrop not intact")
            
        # Rule 4: RSI
        rsi = ta_column(ta.rsi(df['close'], length=14))
        rsi_val = rsi.iloc[-1]
        if not (35 <= rsi_val <= 55):
            failed_rules.append(f"RSI {rsi_val:.1f} outside pullback zone")
            
        # Rule 5: Liquidity
        liq_ok, avg_vol, last_close = liquidity_ok(df, min_avg_volume=100000, min_price=50, length=20)
        if not liq_ok:
            failed_rules.append("Liquidity floor check failed")
            
        # Rule 6: Sector
        rank = sector_rank(sector_ranks, symbol, default=99)
        if rank > 10:
            failed_rules.append(f"Sector rank {rank} not in top 10")
            
        if failed_rules:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": failed_rules, "Details": {}}
            
        # Scoring
        tl_quality = min(100, (tl['slope'] / tl['anchor_price']) * 4000)
        sec_score = max(0, 100 - (rank - 1) * 10)
        bounce_score = max(0, 100 - ((close[T] - tl_today) / tl_today * 100) * 25)
        rsi_score = max(0, 100 - abs(rsi_val - 45) * 4)
        score = 0.3 * tl_quality + 0.25 * sec_score + 0.25 * bounce_score + 0.2 * rsi_score
        
        details = {
            "Company Name": universe.get(symbol, {}).get("Name", "Unknown"),
            "Sector": universe.get(symbol, {}).get("Sector", "Unknown"),
            "Sector Rank": rank,
            "Current Price": close[T],
            "Ideal Entry Price Low": tl_today,
            "Ideal Entry Price High": close[T],
            "Ideal Exit Price": tl_today + 2.5 * atr.iloc[-1],
            "Swing Duration (Days)": "5-40",
            "Trendline Value (Today)": tl_today,
            "Trendline Slope (% per day)": (tl['slope'] / tl['anchor_price']) * 100,
            "Daily RSI(14)": rsi_val,
            "20D Average Volume": avg_vol,
            "Rank Score": score
        }
        
        return {"Symbol": symbol, "Passed": True, "ClosenessScore": score, "FailedRules": [], "Details": details}
    except Exception as e:
        return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": [f"Calculation error: {e}"], "Details": {}}
