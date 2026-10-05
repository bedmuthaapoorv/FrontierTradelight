"""US daily price history from Alpaca's Market Data API - the US
counterpart of Default/nse_utils.py.

Every caller in this folder was written against jugaad-data's NSE frame
shape (uppercase DATE/OPEN/HIGH/LOW/CLOSE/VOLUME), so fetch_stock_history
returns exactly that shape and the backtester / screeners / multi-strategy
code consume it unchanged.

Why Alpaca rather than yfinance: jugaad-data's NSE endpoint needed one
request per stock per calendar month and bot-blocked bursts of them. Alpaca's
/v2/stocks/bars takes many symbols per request and returns up to 10,000 bars
per page, so the whole S&P 500 over five years is a few dozen requests
against a documented limit (200/min on the free plan) rather than tens of
thousands against an undocumented one. fetch_bars_batch is the bulk path;
fetch_stock_history is a single-symbol convenience over it.

Credentials come from ALPACA_API_KEY / ALPACA_SECRET_KEY in US/.env.
"""

import datetime
import os
import threading
import time

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
MARKET_TZ = "America/New_York"
PAGE_LIMIT = 10000
# Symbols per request. The bars endpoint takes them as one comma-joined
# query parameter, so this mostly bounds URL length - pagination, not this,
# is what keeps each response under PAGE_LIMIT bars.
SYMBOLS_PER_REQUEST = 100

# Free plan: 200 requests/minute, shared by every thread in this process.
# Spaced slightly under that so a long backtest fetch never trips a 429 in
# the first place; _get still honors 429s if it does.
MIN_REQUEST_INTERVAL = 60 / 190
_throttle_lock = threading.Lock()
_last_request_at = 0.0

# The free plan can read the consolidated (SIP) feed - every US exchange's
# volume - for anything older than 15 minutes. If the account turns out not
# to have that, fall back to the IEX-only feed once and stay there for the
# rest of the process. IEX prices are fine but its volume is only IEX's
# own small slice of the market, so volume-based rules read very low on it.
SIP_DELAY = datetime.timedelta(minutes=16)
_feed = "sip"

# A daily bar is final once the 16:00 ET close has propagated through the
# 15-minute SIP delay. Before then today's bar is partial and is dropped, so
# the screeners see completed sessions only - the same "up to yesterday's
# close" view the NSE pipeline always had.
SESSION_FINAL_AFTER = datetime.time(16, 20)


class AlpacaCredentialsError(RuntimeError):
    pass


def _headers():
    key = os.environ.get("ALPACA_API_KEY", "").strip()
    secret = os.environ.get("ALPACA_SECRET_KEY", "").strip()
    if not key or not secret or key == "enter here":
        raise AlpacaCredentialsError(
            "ALPACA_API_KEY / ALPACA_SECRET_KEY not set. Add them to Strategies/US/.env "
            "(free account at https://alpaca.markets)."
        )
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}


def _throttle():
    global _last_request_at
    with _throttle_lock:
        wait = _last_request_at + MIN_REQUEST_INTERVAL - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()


def _get(params, retries=5):
    """One bars request, retrying 429s (honoring Retry-After) and transient
    5xx/network errors. Switches to the IEX feed if SIP is refused."""
    global _feed
    headers = _headers()
    last_error = None
    for attempt in range(retries):
        _throttle()
        try:
            resp = requests.get(BARS_URL, headers=headers, params={**params, "feed": _feed}, timeout=30)
        except requests.RequestException as e:
            last_error = e
            time.sleep(2 * (attempt + 1))
            continue

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (401, 403) and _feed == "sip" and "subscription" in resp.text.lower():
            print("Alpaca: SIP feed not permitted on this account, falling back to IEX (volume will be IEX-only).")
            _feed = "iex"
            continue
        if resp.status_code in (401, 403):
            raise AlpacaCredentialsError(f"Alpaca rejected the API keys ({resp.status_code}): {resp.text[:200]}")
        if resp.status_code == 429 or resp.status_code >= 500:
            last_error = RuntimeError(f"Alpaca {resp.status_code}: {resp.text[:200]}")
            retry_after = resp.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else 2 * (attempt + 1))
            continue
        raise RuntimeError(f"Alpaca {resp.status_code}: {resp.text[:200]}")
    raise last_error


def _now_market():
    return pd.Timestamp.now(tz=MARKET_TZ)


def _request_window(from_date, to_date):
    """RFC3339 start/end for [from_date, to_date] in market time, with end
    clamped to SIP_DELAY ago (the free plan refuses anything more recent)."""
    start = pd.Timestamp(from_date).tz_localize(MARKET_TZ)
    end = (pd.Timestamp(to_date) + pd.Timedelta(days=1)).tz_localize(MARKET_TZ)
    end = min(end, _now_market() - SIP_DELAY)
    return start.isoformat(), end.isoformat()


def _bars_to_frame(bars):
    """Alpaca bar dicts -> NSE-shaped frame. Daily bars are stamped at
    midnight ET expressed in UTC (e.g. 04:00Z/05:00Z depending on DST);
    converting back to ET before taking the date is what keeps every bar
    on its real trading day - the same class of bug Default/nse_utils.py
    had to correct for jugaad-data's IST stamps."""
    df = pd.DataFrame(bars)
    dates = pd.to_datetime(df["t"], utc=True).dt.tz_convert(MARKET_TZ).dt.normalize().dt.tz_localize(None)
    return pd.DataFrame({
        "DATE": dates,
        "OPEN": df["o"].astype(float),
        "HIGH": df["h"].astype(float),
        "LOW": df["l"].astype(float),
        "CLOSE": df["c"].astype(float),
        "VOLUME": df["v"].astype(float),
    })


def _drop_partial_session(df):
    now = _now_market()
    if now.time() >= SESSION_FINAL_AFTER:
        return df
    today = pd.Timestamp(now.date())
    return df[df["DATE"] < today]


def fetch_bars_batch(symbols, from_date, to_date, progress=None):
    """Daily bars for many symbols at once: {symbol: NSE-shaped DataFrame}.
    Symbols with no data in range are simply absent from the result.

    Prices are split-adjusted only (adjustment="split"), not dividend-
    adjusted, so historical closes stay comparable to what a position was
    actually bought at - matching the split-only back-adjustment the NSE
    pipeline applied itself."""
    symbols = list(dict.fromkeys(symbols))
    start, end = _request_window(from_date, to_date)
    collected = {}

    for i in range(0, len(symbols), SYMBOLS_PER_REQUEST):
        chunk = symbols[i:i + SYMBOLS_PER_REQUEST]
        params = {
            "symbols": ",".join(chunk),
            "timeframe": "1Day",
            "start": start,
            "end": end,
            "adjustment": "split",
            "limit": PAGE_LIMIT,
        }
        page_token = None
        while True:
            if page_token:
                params["page_token"] = page_token
            payload = _get(params)
            for symbol, bars in (payload.get("bars") or {}).items():
                collected.setdefault(symbol, []).extend(bars)
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        params.pop("page_token", None)
        if progress:
            progress(min(i + SYMBOLS_PER_REQUEST, len(symbols)), len(symbols))

    result = {}
    for symbol, bars in collected.items():
        if not bars:
            continue
        df = _bars_to_frame(bars)
        df = df[df["DATE"] <= pd.Timestamp(to_date)]
        df = _drop_partial_session(df)
        df = df.drop_duplicates(subset="DATE", keep="last").sort_values("DATE").reset_index(drop=True)
        if not df.empty:
            result[symbol] = df
    return result


def fetch_stock_history(symbol, from_date, to_date):
    """Single-symbol history in the NSE frame shape, or an empty frame."""
    return fetch_bars_batch([symbol], from_date, to_date).get(symbol, pd.DataFrame())


def calculate_sector_strength(data, universe):
    """Rank sectors by average 30-day return and map each symbol to its sector's rank.

    `data` maps symbol -> a DataFrame with a lowercase 'close' column, sorted
    ascending by date. Only uses data already present in each DataFrame, so
    passing a date-truncated slice (as the backtester does) keeps this
    look-ahead free.
    """
    sector_returns = {}

    for symbol, info in universe.items():
        df = data.get(symbol)
        if df is None or len(df) < 30:
            continue

        recent = df["close"].iloc[-30:]
        pct_return = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0] * 100

        sector = info["Sector"]
        sector_returns.setdefault(sector, []).append(pct_return)

    sector_avg_return = {
        sector: sum(returns) / len(returns)
        for sector, returns in sector_returns.items()
    }

    ranked_sectors = sorted(sector_avg_return, key=sector_avg_return.get, reverse=True)
    sector_rank = {sector: rank + 1 for rank, sector in enumerate(ranked_sectors)}

    return {
        symbol: sector_rank.get(info["Sector"], 99)
        for symbol, info in universe.items()
    }


def calculate_market_breadth(data, ma_period=50):
    """Percentage (0-100) of stocks in `data` currently trading above their
    own MA(ma_period). A stand-in for an S&P 500 index regime filter, built
    entirely from data the pipeline already fetches (no external index).

    `data` maps symbol -> a DataFrame with a lowercase 'close' column, sorted
    ascending by date. Only uses data already present in each DataFrame, so
    passing a date-truncated slice (as the backtester does) keeps this
    look-ahead free. Returns 50.0 (neutral) if nothing is computable.
    """
    above = 0
    total = 0

    for df in data.values():
        if df is None or len(df) < ma_period:
            continue

        ma = df["close"].rolling(ma_period).mean().iloc[-1]
        if pd.isna(ma):
            continue

        total += 1
        if df["close"].iloc[-1] > ma:
            above += 1

    if total == 0:
        return 50.0

    return (above / total) * 100
