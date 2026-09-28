import pandas as pd
import pandas_ta as ta

def _get_pivot(signal_history_df):
    try:
        return signal_history_df['close'].rolling(window=20).max().iloc[-1]
    except:
        return None

def _get_atr(df):
    try:
        atr_series = ta.atr(df['high'], df['low'], df['close'], length=14)
        return atr_series.iloc[-1]
    except:
        return None

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        pivot = _get_pivot(signal_history_df)
        atr_entry = _get_atr(signal_history_df)
        if pivot is None or atr_entry is None:
            return None

        trailing_sl = entry_price - (3.0 * atr_entry)
        highest_close = entry_price
        atr_multiplier = 3.0
        
        for i, (date, row) in enumerate(future_df.iterrows()):
            days_held = i + 1
            close = row['close']
            
            # Update State
            if close > highest_close:
                highest_close = close
            
            if days_held <= 15 and close >= (1.20 * entry_price):
                atr_multiplier = 4.0
            
            atr_today = _get_atr(pd.concat([signal_history_df, future_df.iloc[:i+1]]))
            if atr_today is not None:
                candidate_sl = highest_close - (atr_multiplier * atr_today)
                if candidate_sl > trailing_sl:
                    trailing_sl = candidate_sl
            
            # Check Exits
            if days_held <= 10 and close < (0.98 * pivot):
                return {"ExitDate": date, "ExitPrice": close, "ExitReason": "FailedBreakout"}
            
            if close <= (0.92 * entry_price):
                return {"ExitDate": date, "ExitPrice": close, "ExitReason": "HardStop"}
            
            if close <= trailing_sl:
                return {"ExitDate": date, "ExitPrice": close, "ExitReason": "TSL"}
            
            if days_held >= 90:
                return {"ExitDate": date, "ExitPrice": close, "ExitReason": "MaxHold"}
                
        return None
    except:
        return None

def describe_state(entry_price, entry_date, signal_history_df, future_df):
    try:
        pivot = _get_pivot(signal_history_df)
        atr_entry = _get_atr(signal_history_df)
        if pivot is None or atr_entry is None:
            return None

        trailing_sl = entry_price - (3.0 * atr_entry)
        highest_close = entry_price
        atr_multiplier = 3.0
        
        for i, (date, row) in enumerate(future_df.iterrows()):
            days_held = i + 1
            close = row['close']
            if close > highest_close: highest_close = close
            if days_held <= 15 and close >= (1.20 * entry_price): atr_multiplier = 4.0
            
            atr_today = _get_atr(pd.concat([signal_history_df, future_df.iloc[:i+1]]))
            if atr_today is not None:
                candidate_sl = highest_close - (atr_multiplier * atr_today)
                if candidate_sl > trailing_sl: trailing_sl = candidate_sl
        
        last_close = future_df['close'].iloc[-1]
        days_held = len(future_df)
        
        return {
            "TrailingStop": trailing_sl,
            "ATRMultiplier": atr_multiplier,
            "HighestClose": highest_close,
            "LastClose": last_close,
            "DistanceToStopPct": ((last_close - trailing_sl) / last_close * 100),
            "DistanceToHardStopPct": ((last_close - (0.92 * entry_price)) / last_close * 100),
            "DaysHeld": days_held,
            "DaysToMaxHold": max(0, 90 - days_held),
            "BigWinnerOverrideActive": (atr_multiplier == 4.0),
            "AtRiskOfFailedBreakout": (days_held <= 10 and last_close < (1.02 * pivot))
        }
    except:
        return None