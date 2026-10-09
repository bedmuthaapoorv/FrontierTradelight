import pandas as pd
import pandas_ta as ta

def _get_pre_trade_data(entry_price, entry_date, signal_history_df):
    try:
        entry_ts = pd.Timestamp(entry_date).normalize()
        mask = signal_history_df.index.normalize() < entry_ts
        history = signal_history_df[mask]
        p = len(history) - 1
        
        if p < 23:
            return None, None, 0.92 * entry_price
            
        c_window = history['high'].iloc[p-22:p-4].to_numpy()
        c_pos = (p - 22) + (len(c_window) - 1 - int(c_window[::-1].argmax()))
        pivot = history['high'].iloc[c_pos]

        d_window = history['low'].iloc[c_pos+1:p].to_numpy()
        d_pos = (c_pos + 1) + (len(d_window) - 1 - int(d_window[::-1].argmin()))
        handle_low = history['low'].iloc[d_pos]
        if pd.isna(pivot) or pd.isna(handle_low):
            return None, None, 0.92 * entry_price
        
        initial_stop = max(0.99 * handle_low, 0.92 * entry_price)
        return pivot, handle_low, initial_stop
    except:
        return None, None, 0.92 * entry_price

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        pivot, handle_low, initial_stop = _get_pre_trade_data(entry_price, entry_date, signal_history_df)
        
        trailing_sl = initial_stop
        highest_close = entry_price
        atr_multiplier = 3.0
        big_winner = False
        
        for s in range(1, len(future_df) + 1):
            current_row = future_df.iloc[s-1]
            close = current_row['close']
            
            # Update State
            if close > highest_close:
                highest_close = close
            
            if not big_winner and s <= 15 and close >= 1.20 * entry_price:
                big_winner = True
                atr_multiplier = 4.0
            
            combined = pd.concat([signal_history_df, future_df.iloc[:s]])
            combined = combined[~combined.index.duplicated(keep="last")]
            
            atr_series = ta.atr(combined['high'], combined['low'], combined['close'], length=22)
            if atr_series is not None and not atr_series.empty:
                atr_today = atr_series.iloc[-1]
                candidate_sl = highest_close - (atr_multiplier * atr_today)
                if candidate_sl > trailing_sl:
                    trailing_sl = candidate_sl
            
            hold_floor_active = (big_winner and s <= 40)
            
            # Exit Conditions
            if close <= initial_stop:
                return {"ExitDate": future_df.index[s-1], "ExitPrice": close, "ExitReason": "InitialStop"}
            
            if 11 <= s <= 21 and pivot is not None and close < pivot and highest_close < 1.05 * entry_price:
                return {"ExitDate": future_df.index[s-1], "ExitPrice": close, "ExitReason": "FailedBreakout"}
            
            if hold_floor_active:
                sma50_c = ta.sma(combined['close'], length=50)
                sma50_v = ta.sma(combined['volume'], length=50)
                if sma50_c is not None and sma50_v is not None:
                    if close < sma50_c.iloc[-1] and current_row['volume'] > sma50_v.iloc[-1]:
                        return {"ExitDate": future_df.index[s-1], "ExitPrice": close, "ExitReason": "BigWinner50DMA"}
            
            if not hold_floor_active and trailing_sl > initial_stop and close <= trailing_sl:
                return {"ExitDate": future_df.index[s-1], "ExitPrice": close, "ExitReason": "TSL"}
            
            if s >= 30 and close < 1.05 * entry_price and highest_close < 1.10 * entry_price:
                return {"ExitDate": future_df.index[s-1], "ExitPrice": close, "ExitReason": "TimeStop"}
            
            if s >= 90:
                return {"ExitDate": future_df.index[s-1], "ExitPrice": close, "ExitReason": "MaxHold"}
                
        return None
    except:
        return None

def describe_state(entry_price, entry_date, signal_history_df, future_df):
    if future_df.empty: return None
    try:
        pivot, handle_low, initial_stop = _get_pre_trade_data(entry_price, entry_date, signal_history_df)
        trailing_sl, highest_close, atr_multiplier, big_winner = initial_stop, entry_price, 3.0, False
        
        for s in range(1, len(future_df) + 1):
            row = future_df.iloc[s-1]
            if row['close'] > highest_close: highest_close = row['close']
            if not big_winner and s <= 15 and row['close'] >= 1.20 * entry_price:
                big_winner, atr_multiplier = True, 4.0
            
            combined = pd.concat([signal_history_df, future_df.iloc[:s]])
            combined = combined[~combined.index.duplicated(keep="last")]
            atr = ta.atr(combined['high'], combined['low'], combined['close'], length=22)
            if atr is not None:
                cand = highest_close - (atr_multiplier * atr.iloc[-1])
                if cand > trailing_sl: trailing_sl = cand
        
        hold_floor = (big_winner and len(future_df) <= 40)
        eff_stop = initial_stop if (hold_floor or trailing_sl <= initial_stop) else trailing_sl
        last_close = future_df['close'].iloc[-1]
        
        return {
            "TrailingStop": eff_stop,
            "DistanceToStopPct": (last_close - eff_stop) / last_close * 100,
            "DaysHeld": len(future_df),
            "DaysToMaxHold": max(0, 90 - len(future_df)),
            "LastClose": last_close,
            "HighestClose": highest_close,
            "InitialStop": initial_stop,
            "Pivot": pivot,
            "HandleLow": handle_low,
            "ATRMultiplier": atr_multiplier,
            "BigWinner": big_winner,
            "HoldFloorActive": hold_floor,
            "InFailedBreakoutWindow": (11 <= len(future_df) <= 21 and highest_close < 1.05 * entry_price)
        }
    except:
        return None