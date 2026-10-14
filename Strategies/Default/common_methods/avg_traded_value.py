import pandas as pd


def avg_traded_value(df, length=20):
    """Average daily traded value in rupees over the last `length` bars:
    the mean of close x volume, including the latest bar. A liquidity
    measure in money terms (unlike average share volume, it is comparable
    across cheap and expensive stocks), e.g. ">= Rs 25 crore" is
    avg_traded_value(df) >= 25e7.

    Args:
        df: OHLCV DataFrame with lowercase 'close' and 'volume' columns,
            oldest first.
        length: averaging window in bars.

    Returns:
        float rupees, or None if there are fewer than `length` rows or the
        value can't be computed. Never raises.
    """
    try:
        if df is None or len(df) < length:
            return None
        value = float((df["close"] * df["volume"]).iloc[-length:].mean())
        return None if pd.isna(value) else value
    except Exception:
        return None
