import pandas as pd
import pandas_ta as ta

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        if signal_history_df.empty or future_df.empty:
            return None

        signal_date = pd.Timestamp(signal_history_df.index[-1]).date()
        entry_day = pd.Timestamp(entry_date).date()
        signal_close = signal_history_df['close'].iloc[-1]

        # Rule 0: Entry Condition Not Met
        # Check if it's the Monday after a weekend (3 days difference)
        # and if the gap is at least 1%
        day_diff = (entry_day - signal_date).days
        if day_diff != 3 or entry_price < (1.01 * signal_close):
            return {
                "ExitDate": future_df.index[0],
                "ExitPrice": entry_price,
                "ExitReason": "NoEntry"
            }

        # Rule 1: Stop-Loss Above Entry
        # Short position: SL at 5% above entry
        stop = entry_price * 1.05
        entry_day_high = future_df["high"].iloc[0]

        if entry_day_high >= stop:
            return {
                "ExitDate": future_df.index[0],
                "ExitPrice": stop,
                "ExitReason": "SL"
            }

        # No exit triggered, return None for caller to handle SquareOff
        return None

    except Exception:
        return None