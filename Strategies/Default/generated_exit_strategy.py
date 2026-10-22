import pandas as pd
import pandas_ta as ta

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        # Ensure we have enough history for ATR(14)
        if len(signal_history_df) < 14:
            return None

        # Compute ATR(14) from signal_history_df
        atr_series = ta.atr(
            signal_history_df['high'],
            signal_history_df['low'],
            signal_history_df['close'],
            length=14
        )
        
        if atr_series is None or atr_series.empty:
            return None
            
        atr_val = atr_series.iloc[-1]
        
        if pd.isna(atr_val):
            return None

        # Rule 1: Stop-Loss Above Entry
        # Strategy is SHORT, so SL is entry_price + 1.0 * ATR
        stop_price = entry_price + (1.0 * atr_val)
        
        # future_df contains only the entry day for this intraday strategy
        entry_day_high = future_df["high"].iloc[0]
        
        if entry_day_high >= stop_price:
            return {
                "ExitDate": future_df.index[0],
                "ExitPrice": stop_price,
                "ExitReason": "SL"
            }

        # If no condition triggers, return None. 
        # The caller handles the end-of-day square-off.
        return None

    except Exception:
        # Return None on any error to ensure robustness
        return None