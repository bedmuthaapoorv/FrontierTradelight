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
        if len(df) < 250:
            results["FailedRules"].append("Insufficient data (< 250 sessions)")
            return results

        T = len(df) - 1
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        vol = df['volume'].values
        
        # Step 1: Right rim C
        window_c = high[T-22 : T-4]
        if len(window_c) == 0:
            results["FailedRules"].append("No handle structure (insufficient data for C)")
            return results
        
        c_idx_in_window = np.where(window_c == np.max(window_c))[0][-1]
        C = (T - 22) + c_idx_in_window
        
        if C < T - 22 or C > T - 5:
            results["FailedRules"].append("No handle structure (C out of range)")
            return results
            
        if C + 1 <= T - 1:
            if high[C] < np.max(high[C+1 : T]):
                results["FailedRules"].append("No handle structure (higher high after right rim)")
                return results

        # Step 2: Handle low D
        D = (C + 1) + np.where(low[C+1 : T] == np.min(low[C+1 : T]))[0][-1]

        # Step 3: Left rim A
        A = -1
        search_range = range(C - 30, max(10, C - 250) - 1, -1)
        for i in search_range:
            if i - 10 < 0 or i + 10 >= T: continue
            if high[i] >= np.max(high[i-10 : i+11]):
                if high[i] >= np.max(high[i : C]):
                    A = i
                    break
        if A == -1:
            results["FailedRules"].append("No left rim found")
            return results

        # Step 4: Cup low B
        B = (A + 1) + np.where(low[A+1 : C] == np.min(low[A+1 : C]))[0][-1]

        # Step 5: Prior-advance base K
        if A < 60:
            results["FailedRules"].append("Unverifiable prior trend (< 60 sessions before left rim)")
            return results
        K = np.min(low[max(0, A - 120) : A])

        # Derived
        cup_bars = C - A
        handle_bars = T - C
        cup_depth = (high[A] - low[B]) / high[A]
        handle_depth = (high[C] - low[D]) / high[C]
        vol_sma50 = np.mean(vol[T-50 : T])
        vol_ratio = vol[T] / vol_sma50 if vol_sma50 > 0 else 0

        # Mandatory Filters
        failed = []
        turnover_sma20 = np.mean((vol * close)[T-19 : T+1])
        if turnover_sma20 < 50000000 or close[T] < 50: failed.append("Minimum Liquidity Floor")
        if high[A] < 1.30 * K: failed.append("Prior Uptrend Into the Base")
        if not (30 <= cup_bars <= 250): failed.append("Cup Length")
        if not (0.12 <= cup_depth <= 0.35): failed.append("Cup Depth")
        
        # Rule 5: Rounded Cup
        x = np.linspace(0, 1, C - A + 1)
        y = close[A : C+1]
        poly = np.polyfit(x, y, 2)
        a, b, c = poly
        r_sq = 1 - (np.sum((y - np.polyval(poly, x))**2) / np.sum((y - np.mean(y))**2))
        if not (a > 0 and r_sq >= 0.60 and 0.25 <= (-b / (2 * a)) <= 0.75): failed.append("Rounded (U-Shaped) Cup Bottom (Parabola)")
        if not ((B - A) >= 0.25 * cup_bars and (C - B) >= 0.25 * cup_bars and (B - A) >= 20): failed.append("Rounded (U-Shaped) Cup Bottom (Balanced)")
        bottom_zone = low[B] + 0.25 * (min(high[A], high[C]) - low[B])
        if not (np.sum(close[A : C+1] <= bottom_zone) >= 0.15 * (cup_bars + 1)): failed.append("Rounded (U-Shaped) Cup Bottom (Time near bottom)")
        
        if not (high[C] >= high[A] - 0.20 * (high[A] - low[B]) and high[C] >= 0.85 * high[A] and high[C] <= 1.02 * high[A]): failed.append("Rim Alignment")
        
        # Rule 7: Handle
        handle_lows = low[C+1 : T]
        handle_slope = np.polyfit(np.arange(len(handle_lows)), handle_lows, 1)[0]
        sma50 = ta.sma(pd.Series(close), length=50).iloc[D]
        sma200 = ta.sma(pd.Series(close), length=200).iloc[D]
        if not (5 <= handle_bars <= 22 and handle_depth <= 0.12 and low[D] > (high[A] + low[B]) / 2 and close[D] >= sma50 and low[D] > sma200 and handle_slope <= 0): failed.append("Handle Shape")
        
        if not (np.mean(vol[C+1 : T]) < ta.sma(pd.Series(vol), length=50).iloc[C]): failed.append("Handle Volume Dry-Up")
        if not (close[T] > 1.001 * high[C]): failed.append("Breakout Close Above the Pivot")
        if vol_ratio < 1.4: failed.append("Breakout Volume")
        if close[T] > 1.05 * high[C]: failed.append("Not Extended Beyond the Buy Zone")

        results["FailedRules"] = failed
        results["Passed"] = len(failed) == 0
        
        # Ranking
        v_score = min(100, max(0, (vol_ratio - 1.4) / (2.5 - 1.4) * 100))
        h_score = 0.5 * min(100, max(0, (22 - handle_bars) / 17 * 100)) + 0.5 * min(100, max(0, (0.12 - handle_depth) / 0.12 * 100))
        c_score = 0.5 * min(100, max(0, (r_sq - 0.60) / 0.40 * 100)) + 0.5 * (100 if 0.15 <= cup_depth <= 0.30 else 50)
        rs_score = min(100, max(0, (close[T] / np.max(high[max(0, T-252):T+1]) - 0.70) / 0.30 * 100))
        ss_score = max(0, 100 - (sector_ranks.get(symbol, 99) - 1) * 10)
        results["ClosenessScore"] = 0.25*v_score + 0.20*h_score + 0.15*c_score + 0.15*market_breadth + 0.15*rs_score + 0.10*ss_score
        
        # Details
        results["Details"] = {
            "Company Name": universe.get(symbol, {}).get("Name", "N/A"),
            "Sector": universe.get(symbol, {}).get("Sector", "N/A"),
            "Sector Rank": sector_ranks.get(symbol, 99),
            "Current Price": close[T],
            "Ideal Entry Price Low": high[C],
            "Ideal Entry Price High": 1.05 * high[C],
            "Ideal Exit Price": high[C] + 0.61 * (high[C] - low[B]),
            "Initial Stop": max(0.99 * low[D], 0.92 * close[T]),
            "Pivot": high[C],
            "Handle Low": low[D],
            "Cup Depth (%)": cup_depth * 100,
            "Cup Bars": cup_bars,
            "Handle Bars": handle_bars,
            "Handle Depth (%)": handle_depth * 100,
            "Cup R²": r_sq,
            "Breakout Volume Ratio (VolRatio)": vol_ratio,
            "% Above Pivot": (close[T] / high[C] - 1) * 100,
            "Market Breadth": market_breadth,
            "Rank Score": results["ClosenessScore"]
        }
        return results

    except Exception as e:
        results["FailedRules"].append(f"Calculation error: {e}")
        return results