import datetime

import pandas as pd

# NSE sessions that are not normal full trading days: the one-hour Diwali
# Muhurat session and the short special live sessions NSE runs to test its
# disaster-recovery site. They trade at 7-23% of normal volume, so treated
# as ordinary bars they drag the next 20 sessions' volume averages ~4% low
# (letting extra stocks through volume filters), let a signal fill inside a
# thin one-hour session, and count towards session-based holds. Every price
# loader drops these bars instead (see drop_special_sessions); their price
# move shows up in the next full session's opening gap.
#
# Full-length special sessions (e.g. the Saturday Budget-day sessions on
# 2020-02-01 and 2025-02-01, or 2024-01-20) are normal-volume trading days
# and deliberately NOT listed here.
#
# Add each year's Muhurat date from NSE's holiday circular. Dates marked
# "cache" were confirmed as low-volume bars in the backtest price cache
# (research_notes/Holiday shortened weeks on NSE/nse_data_analysis.md).
SPECIAL_SESSIONS = {
    datetime.date(2017, 10, 19): "Muhurat",
    datetime.date(2018, 11, 7): "Muhurat",
    datetime.date(2019, 10, 27): "Muhurat",
    datetime.date(2020, 11, 14): "Muhurat",  # cache
    datetime.date(2021, 11, 4): "Muhurat",  # cache
    datetime.date(2022, 10, 24): "Muhurat",  # cache
    datetime.date(2023, 11, 12): "Muhurat",  # cache
    datetime.date(2024, 3, 2): "Special DR session",  # cache
    datetime.date(2024, 5, 18): "Special DR session",  # cache
    datetime.date(2024, 11, 1): "Muhurat",  # cache
    datetime.date(2025, 10, 21): "Muhurat",  # cache
    datetime.date(2026, 11, 8): "Muhurat",  # press reports; confirm against NSE's circular
}


def is_special_session(day):
    if isinstance(day, datetime.datetime):
        day = day.date()
    return day in SPECIAL_SESSIONS


def drop_special_sessions(df, date_col=None):
    """Return df without rows on SPECIAL_SESSIONS dates. Looks at the
    index by default, or at `date_col` when the dates are a column (as in
    fetch_stock_history's raw DATE column)."""
    if df is None or df.empty:
        return df
    dates = pd.to_datetime(df[date_col] if date_col else df.index)
    special = pd.DatetimeIndex(dates).normalize().isin(pd.to_datetime(list(SPECIAL_SESSIONS)))
    return df[~special] if special.any() else df
