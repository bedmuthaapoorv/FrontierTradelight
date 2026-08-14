import pandas as pd
import pandas_ta as ta

def get_atr(df, length=14):
    try:
        if len(df) < length:
            return None
        atr_series = ta.atr(df['high'], df['low'], df['close'], length=length)
        return atr_series.iloc[-1]
    except:
        return None

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        atr_entry = get_atr(signal_history_df, 14)
        if atr_entry is None:
            return None

        trailing_sl = entry_price - (2.5 * atr_entry)
        highest_close = entry_price
        
        for i, (date, row) in enumerate(future_df.iterrows()):
            close = row['close']
            days_held = i + 1
            
            if close > highest_close:
                highest_close = close
            
            history_up_to_today = pd.concat([signal_history_df, future_df.iloc[:i+1]])
            atr_today = get_atr(history_up_to_today, 14)
            
            if atr_today is not None:
                candidate_sl = highest_close - (2.5 * atr_today)
                if candidate_sl > trailing_sl:
                    trailing_sl = candidate_sl
            
            if close <= trailing_sl:
                return {"ExitDate": date, "ExitPrice": close, "ExitReason": "TSL"}
            
            if days_held >= 90:
                return {"ExitDate": date, "ExitPrice": close, "ExitReason": "MaxHold"}
                
        return None
    except:
        return None

def describe_state(entry_price, entry_date, signal_history_df, future_df):
    try:
        atr_entry = get_atr(signal_history_df, 14)
        if atr_entry is None:
            return None

        trailing_sl = entry_price - (2.5 * atr_entry)
        highest_close = entry_price
        
        for i, (date, row) in enumerate(future_df.iterrows()):
            close = row['close']
            if close > highest_close:
                highest_close = close
            
            history_up_to_today = pd.concat([signal_history_df, future_df.iloc[:i+1]])
            atr_today = get_atr(history_up_to_today, 14)
            
            if atr_today is not None:
                candidate_sl = highest_close - (2.5 * atr_today)
                if candidate_sl > trailing_sl:
                    trailing_sl = candidate_sl
        
        last_close = future_df['close'].iloc[-1]
        days_held = len(future_df)
        
        return {
            "TrailingStop": float(trailing_sl),
            "HighestClose": float(highest_close),
            "LastClose": float(last_close),
            "DistanceToStopPct": float(((last_close - trailing_sl) / last_close) * 100),
            "DaysHeld": int(days_held),
            "DaysToMaxHold": int(max(0, 90 - days_held))
        }
    except:
        return None