import pandas as pd
import pandas_ta as ta
import numpy as np

def evaluate_stock(symbol, df, universe, sector_ranks, market_breadth):
    failed_rules = []
    details = {}
    passed = False
    rank_score = 0.0

    try:
        if len(df) < 100:
            return {"Symbol": symbol, "Passed": False, "ClosenessScore": 0.0, "FailedRules": ["Insufficient data (<100 sessions)"], "Details": {}}

        close = df['close']
        volume = df['volume']
        
        # Rule 1: RSI
        rsi_series = ta.rsi(close, length=14)
        if rsi_series is None or rsi_series.isna().iloc[-1]:
            failed_rules.append("RSI data missing")
        else:
            rsi_val = rsi_series.iloc[-1]
            details["RSI(14)"] = rsi_val
            if rsi_val > 30:
                failed_rules.append(f"RSI outside range ({rsi_val:.2f})")

        # Rule 2: SMA20
        sma20 = ta.sma(close, length=20).iloc[-1]
        dist_sma20 = ((sma20 - close.iloc[-1]) / sma20) * 100
        details["SMA20"] = sma20
        details["Distance From SMA20 (%)"] = dist_sma20
        if not (close.iloc[-1] < sma20 and dist_sma20 >= 5.0):
            failed_rules.append(f"Distance from SMA20 ({dist_sma20:.2f}%) insufficient or price above SMA")

        # Rule 3: Bollinger Bands
        bb = ta.bbands(close, length=20, std=2)
        lbb_col = next(c for c in bb.columns if c.startswith('BBL_'))
        lbb = bb[lbb_col].iloc[-1]
        details["Lower Bollinger Band"] = lbb
        if close.iloc[-1] > lbb:
            failed_rules.append("Price above Lower Bollinger Band")

        # Rule 4: Volume
        avg_vol_20 = volume.iloc[-21:-1].mean()
        vol_prev = volume.iloc[-2]
        details["Volume[-1]"] = vol_prev
        details["20D Average Volume"] = avg_vol_20
        if vol_prev <= (1.5 * avg_vol_20):
            failed_rules.append("Volume not capitulation level")

        # Rule 5: SMA100
        sma100 = ta.sma(close, length=100).iloc[-1]
        details["SMA100"] = sma100
        if close.iloc[-1] < (0.85 * sma100):
            failed_rules.append("Structural breakdown (Price < 85% SMA100)")

        # Rule 6: Sector Rank
        rank = sector_ranks.get(symbol, 99)
        details["Sector Rank"] = rank
        if rank > 10:
            failed_rules.append(f"Sector rank {rank} not in top 10")

        # Finalize
        if not failed_rules:
            passed = True
            # Scoring
            s1 = max(0, (30 - rsi_val) * (100 / 30))
            s2 = min(100, dist_sma20 * 10)
            s3 = min(100, ((vol_prev / avg_vol_20) - 1) * 100)
            s4 = max(0, 100 - (rank - 1) * 10)
            rank_score = (0.35 * s1) + (0.30 * s2) + (0.20 * s3) + (0.15 * s4)
            details["Rank Score"] = rank_score

        details["Company Name"] = universe.get(symbol, {}).get("Name", "N/A")
        details["Sector"] = universe.get(symbol, {}).get("Sector", "N/A")
        details["Current Price"] = close.iloc[-1]

    except Exception as e:
        failed_rules.append(f"Calculation error: {str(e)}")

    return {
        "Symbol": symbol,
        "Passed": passed,
        "ClosenessScore": rank_score,
        "FailedRules": failed_rules,
        "Details": details
    }