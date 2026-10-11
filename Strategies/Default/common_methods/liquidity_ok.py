import pandas as pd


def liquidity_ok(df, min_avg_volume=100000, min_price=50, length=20):
    """Minimum-liquidity floor check on the latest bar.

    Passes when the `length`-day simple average of volume (including the
    latest bar) is >= min_avg_volume AND the latest close is >= min_price.

    Args:
        df: OHLCV DataFrame with lowercase 'close' and 'volume' columns,
            oldest first.
        min_avg_volume: minimum average daily volume (shares).
        min_price: minimum latest close price.
        length: averaging window in bars.

    Returns:
        (passed: bool, avg_volume: float or None, last_close: float or None).
        passed is False when data is missing/insufficient. Never raises.
    """
    try:
        if df is None or len(df) < length:
            return False, None, None
        avg_volume = float(df["volume"].rolling(length).mean().iloc[-1])
        last_close = float(df["close"].iloc[-1])
        if pd.isna(avg_volume) or pd.isna(last_close):
            return False, avg_volume, last_close
        return (avg_volume >= min_avg_volume and last_close >= min_price), avg_volume, last_close
    except Exception:
        return False, None, None
