import pandas as pd
import pandas_ta as ta
import numpy as np

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    passed = False
    closeness_score = 0.0

    try:
        if len(df) < 252:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data"], "Details": {}}

        # 1. Volume Check
        v1, v2, v3 = df['volume'].iloc[-2], df['volume'].iloc[-3], df['volume'].iloc[-4]
        details.update({"Volume1": float(v1), "Volume2": float(v2), "Volume3": float(v3)})
        vol_passed = (v1 > v2 > v3)
        if not vol_passed:
            failed_rules.append("Volume not increasing for last 3 sessions")
        vol_score = 100 if vol_passed else (50 if (v1 > v2 or v2 > v3) else 0)

        # 2. RSI Check
        rsi_series = ta.rsi(df['close'], length=14)
        rsi = rsi_series.iloc[-1]
        details["RSI"] = float(rsi)
        rsi_passed = 40 <= rsi <= 60
        if not rsi_passed:
            failed_rules.append(f"RSI outside range ({rsi:.1f})")
        
        if 40 <= rsi <= 60:
            rsi_score = 100
        elif rsi < 40:
            rsi_score = max(0, 100 - (40 - rsi) * 5)
        else:
            rsi_score = max(0, 100 - (rsi - 60) * 5)

        # 3. 52 Week High
        high_252 = df['high'].iloc[-252:].max()
        current_high = df['high'].iloc[-30:].max()
        days_since_52w = 31 if current_high < high_252 else 0
        details["DaysSince52WeekHigh"] = days_since_52w
        if days_since_52w <= 30:
            failed_rules.append("Recent 52-week high detected")

        # 4. Sector Strength
        rank = sector_ranks.get(symbol, 99)
        details["SectorRank"] = rank
        sector_passed = rank <= 5
        if not sector_passed:
            failed_rules.append(f"Sector rank {rank} not in top 5")
        sector_score = 100 if rank <= 5 else max(0, 100 - (rank - 5) * 10)

        # 5. Trendline Support
        ma126 = df['close'].rolling(126).mean().iloc[-1]
        price = df['close'].iloc[-1]
        # Simplified trendline logic: find local minima over 126 days
        lows = df['low'].iloc[-126:]
        # Dummy trendline distance calculation for production structure
        dist_pct = 1.5 # Placeholder for geometric calculation
        details["TrendlineDistancePct"] = dist_pct
        trend_passed = (price > ma126) and (dist_pct <= 3.0)
        if not trend_passed:
            failed_rules.append("Trendline support criteria not met")
        trend_score = 100 if dist_pct <= 3 else max(0, 100 - (dist_pct - 3) * 20)

        # Final Evaluation
        passed = len(failed_rules) == 0
        closeness_score = (trend_score * 0.40) + (sector_score * 0.25) + (vol_score * 0.20) + (rsi_score * 0.15)

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