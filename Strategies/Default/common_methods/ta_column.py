import pandas as pd


def ta_column(result, prefix=None):
    """Return a single pandas Series from a pandas_ta indicator result,
    whether pandas_ta returned a Series or a multi-column DataFrame.

    Args:
        result: the return value of any pandas_ta call (Series, DataFrame or None).
        prefix: for a DataFrame result, the column-name prefix to select
            (e.g. "BBL_" for the lower Bollinger band, "MACDh_" for the MACD
            histogram, "ADX_" for ADX). Never pass a full hardcoded column
            name - suffixes vary by pandas_ta version. Ignored for a Series.

    Returns:
        The selected pandas Series, or None if result is None/empty or no
        column matches the prefix. Never raises.
    """
    if result is None:
        return None
    if isinstance(result, pd.Series):
        return result if not result.empty else None
    if isinstance(result, pd.DataFrame):
        if result.empty:
            return None
        if prefix is None:
            return result.iloc[:, 0]
        for col in result.columns:
            if str(col).startswith(prefix):
                return result[col]
    return None
