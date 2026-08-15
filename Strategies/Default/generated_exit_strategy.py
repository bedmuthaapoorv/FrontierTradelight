import pandas as pd
import pandas_ta as ta

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        # Pre-Trade Calculation
        atr_period = 14
        if len(signal_history_df) < atr_period:
            return None
        
        atr_series = ta.atr(signal_history_df['high'], signal_history_df['low'], signal_history_df['close'], length=atr_period)
        atr_entry = atr_series.iloc[-1]
        
        if pd.isna(atr_entry):
            return None
            
        initial_sl = entry_price - (2.5 * atr_entry)
        
        # State Variables
        trailing_sl = initial_sl
        highest_close = entry_price
        
        # Walk through future_df
        for i, (date, row) in enumerate(future_df.iterrows()):
            close = row['close']
            trading_days_since_entry = i + 1
            
            # 1. Update Highest Close
            if close > highest_close:
                highest_close = close
            
            # 2. Ratchet Trailing Stop
            # Need history up to current day for ATR
            # Combine signal_history_df and future_df up to current date
            combined_df = pd.concat([signal_history_df, future_df.loc[:date]])
            atr_today_series = ta.atr(combined_df['high'], combined_df['low'], combined_df['close'], length=atr_period)
            atr_today = atr_today_series.iloc[-1]
            
            if not pd.isna(atr_today):
                candidate_sl = highest_close - (2.5 * atr_today)
                if candidate_sl > trailing_sl:
                    trailing_sl = candidate_sl
            
            # 3. Check Exit Conditions
            # Condition 1: Trailing Stop-Loss
            if close <= trailing_sl:
                return {
                    "InitialSL": initial_sl,
                    "ExitDate": date,
                    "ExitPrice": close,
                    "ExitReason": "TSL"
                }
            
            # Condition 2: Max Holding Period
            if trading_days_since_entry >= 90:
                return {
                    "InitialSL": initial_sl,
                    "ExitDate": date,
                    "ExitPrice": close,
                    "ExitReason": "MaxHold"
                }
        
        # No exit triggered
        return {
            "InitialSL": initial_sl,
            "ExitDate": None,
            "ExitPrice": None,
            "ExitReason": None
        }
        
    except Exception:
        return None