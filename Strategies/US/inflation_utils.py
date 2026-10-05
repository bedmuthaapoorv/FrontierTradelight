"""Fetches real US CPI inflation (annual %, by calendar year) from the
World Bank's public API - no key required. Used to deflate the backtest's
equity curve to inflation-adjusted terms instead of a user-guessed flat rate.
"""

import json
import os
from datetime import datetime, timedelta

import requests

from constants import INFLATION_CACHE_PATH

CACHE_PATH = INFLATION_CACHE_PATH
CACHE_EXPIRY_DAYS = 30  # annual CPI figures change rarely; no need to refetch often
WORLD_BANK_URL = "https://api.worldbank.org/v2/country/US/indicator/FP.CPI.TOTL.ZG"


def fetch_cpi_yearly():
    """Returns {year (int): annual inflation rate (%, float)} for the US, or
    None if it couldn't be fetched and nothing usable is cached."""
    cached = _read_cache()
    if cached is not None:
        return cached

    try:
        response = requests.get(WORLD_BANK_URL, params={"format": "json", "per_page": 100}, timeout=15)
        response.raise_for_status()
        _, records = response.json()

        yearly_rates = {
            int(record["date"]): float(record["value"])
            for record in records
            if record.get("value") is not None
        }

        if not yearly_rates:
            return None

        _write_cache(yearly_rates)
        return yearly_rates

    except Exception:
        return None


def _read_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cached = json.load(f)
        cache_date = datetime.fromisoformat(cached["timestamp"])
        if datetime.now() - cache_date >= timedelta(days=CACHE_EXPIRY_DAYS):
            return None
        return {int(year): rate for year, rate in cached["yearly_rates"].items()}
    except Exception:
        return None


def _write_cache(yearly_rates):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump({"timestamp": datetime.now().isoformat(), "yearly_rates": yearly_rates}, f)
    except Exception:
        pass


def deflate_equity(dates, equity, yearly_rates):
    """Converts a nominal equity curve to real (inflation-adjusted) terms,
    using each calendar year's actual US CPI inflation rate rather than
    one flat assumed rate - years without published data yet fall back to
    the latest known year's rate. Compounds daily within each year."""
    latest_known_rate = yearly_rates[max(yearly_rates)]
    daily_pct = dates.dt.year.map(lambda year: yearly_rates.get(year, latest_known_rate))
    daily_factor = (1 + daily_pct / 100) ** (1 / 365.25)
    deflator = daily_factor.cumprod()
    deflator = deflator / deflator.iloc[0]
    return equity / deflator
