import pandas as pd
import pandas_ta as ta

def get_next_rebalance(entry_date):
    e = pd.Timestamp(entry_date).date()
    candidates = [
        pd.date_range(start=f"{e.year}-06-15", end=f"{e.year}-06-15")[0].date(),
        pd.date_range(start=f"{e.year}-12-15", end=f"{e.year}-12-15")[0].date(),
        pd.date_range(start=f"{e.year + 1}-06-15", end=f"{e.year + 1}-06-15")[0].date()
    ]
    for c in sorted(candidates):
        if c > e:
            return c
    return None

def resolve_exit(entry_price, entry_date, signal_history_df, future_df):
    try:
        if future_df is None or future_df.empty:
            return None
        
        stop_level = 0.70 * entry_price
        next_rebalance = get_next_rebalance(entry_date)
        
        for i in range(len(future_df)):
            row = future_df.iloc[i]
            close = row['close']
            if pd.isna(close):
                continue
            
            d = pd.Timestamp(future_df.index[i]).date()
            session_num = i + 1
            
            if close <= stop_level:
                return {"ExitDate": future_df.index[i], "ExitPrice": close, "ExitReason": "CatastrophicStop"}
            
            if next_rebalance and d >= next_rebalance:
                return {"ExitDate": future_df.index[i], "ExitPrice": close, "ExitReason": "Rebalance"}
            
            if session_num >= 150:
                return {"ExitDate": future_df.index[i], "ExitPrice": close, "ExitReason": "MaxHold"}
                
        return None
    except Exception:
        return None

def describe_state(entry_price, entry_date, signal_history_df, future_df):
    try:
        if future_df is None or future_df.empty:
            return None
        
        last_row = future_df.dropna(subset=['close']).iloc[-1]
        last_close = last_row['close']
        last_date = pd.Timestamp(last_row.name).date()
        
        stop_level = 0.70 * entry_price
        next_rebalance = get_next_rebalance(entry_date)
        ltcg_date = pd.Timestamp(entry_date).date() + pd.Timedelta(days=366)
        
        days_to_rebalance = (next_rebalance - last_date).days if next_rebalance else 0
        days_to_ltcg = (ltcg_date - last_date).days
        
        return {
            "TrailingStop": stop_level,
            "DistanceToStopPct": ((last_close - stop_level) / last_close * 100),
            "DaysHeld": len(future_df),
            "DaysToMaxHold": max(0, days_to_rebalance),
            "NextRebalance": str(next_rebalance),
            "RebalanceDue": last_date >= next_rebalance,
            "LastClose": last_close,
            "ReturnSinceEntryPct": ((last_close - entry_price) / entry_price * 100),
            "StopPctFromEntry": -30.0,
            "LTCGDate": str(ltcg_date),
            "DaysToLTCG": max(0, days_to_ltcg)
        }
    except Exception:
        return None