"""Point-in-time Nifty 500 membership, stored locally and permanently.

The backtest used to build its universe from *today's* Nifty 500 list ranked
by *today's* 6-month return - survivorship + look-ahead bias, and a number
that changed daily. This module replaces that with the index as it actually
stood on each simulated day.

Source: archived copies (Wayback Machine) of NSE's published
ind_nifty500list.csv. Each snapshot is saved verbatim under
data/universe_history/raw/ and consolidated into
data/universe_history/membership.csv. Once downloaded nothing here touches
the network again - run `python historical_universe.py` only to add newer
snapshots (existing ones are never re-fetched).

Membership on a day = the most recent snapshot dated on or before that day
(forward-filled). Snapshots are sparse, so a stock added/removed between two
snapshots only shows up at the next one; see coverage_report(). Drop any
extra snapshot CSV into raw/ as nifty500_YYYYMMDD.csv and rerun to refine.

ISIN is the identity key: NSE tickers get renamed (e.g. ZOMATO -> ETERNAL)
but ISINs don't, so renamed stocks are not mistaken for additions/removals.
"""

import functools
import gzip
import io
import os
import re
import time
from datetime import date, datetime

import pandas as pd
import requests

from constants import DATA_DIR

HISTORY_DIR = os.path.join(DATA_DIR, "universe_history")
RAW_DIR = os.path.join(HISTORY_DIR, "raw")
MEMBERSHIP_PATH = os.path.join(HISTORY_DIR, "membership.csv")

CDX_URL = "http://web.archive.org/cdx/search/cdx"
CSV_URLS = [
    "archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "www1.nseindia.com/content/indices/ind_nifty500list.csv",
    "www.niftyindices.com/IndexConstituent/ind_nifty500list.csv",
]
REQUIRED_COLUMNS = {"Company Name", "Industry", "Symbol", "ISIN Code"}
MIN_ROWS = 400  # a real Nifty 500 list; guards against truncated/error pages

_membership_cache = None


def _get(url, params=None, retries=6):
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=60)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            last = str(e)
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"GET {url} failed: {last}")


def _decode(content):
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
    return content.decode("utf-8-sig", errors="replace")


def _parse_snapshot(text):
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]
    if not REQUIRED_COLUMNS.issubset(df.columns) or len(df) < MIN_ROWS:
        return None
    return df


def discover_archived_snapshots(from_year=2019):
    """(timestamp, original_url) of every distinct archived 200-OK copy."""
    found = {}
    for u in CSV_URLS:
        text = _get(CDX_URL, params={
            "url": u, "output": "txt", "fl": "timestamp,original",
            "collapse": "digest", "filter": "statuscode:200", "from": str(from_year),
        }).text
        for line in text.splitlines():
            ts, original = line.split()
            found.setdefault(ts[:8], (ts, original))
    return [found[d] for d in sorted(found)]


def download_missing():
    os.makedirs(RAW_DIR, exist_ok=True)
    added = []
    for ts, original in discover_archived_snapshots():
        day = ts[:8]
        path = os.path.join(RAW_DIR, f"nifty500_{day}.csv")
        if os.path.exists(path):
            continue
        r = _get(f"http://web.archive.org/web/{ts}id_/{original}")
        text = _decode(r.content)
        if _parse_snapshot(text) is None:
            print(f"  skipped {day}: not a valid Nifty 500 list")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  saved snapshot {day}")
        added.append(day)
    return added


def build_membership():
    """Consolidates every raw snapshot into membership.csv."""
    frames = []
    for name in sorted(os.listdir(RAW_DIR)):
        m = re.fullmatch(r"nifty500_(\d{8})\.csv", name)
        if not m:
            continue
        with open(os.path.join(RAW_DIR, name), encoding="utf-8-sig") as f:
            df = _parse_snapshot(f.read())
        if df is None:
            continue
        df = df.rename(columns={"Company Name": "Name", "Industry": "Sector",
                                "Symbol": "Symbol", "ISIN Code": "ISIN"})
        df = df[["Symbol", "ISIN", "Name", "Sector"]].copy()
        df.insert(0, "SnapshotDate", datetime.strptime(m.group(1), "%Y%m%d").date().isoformat())
        frames.append(df)
    if not frames:
        raise RuntimeError("No valid snapshots in " + RAW_DIR)
    out = pd.concat(frames, ignore_index=True)
    out["Symbol"] = out["Symbol"].str.strip()
    # Collapse renames: NSE serves a stock's full history under its current
    # ticker, so every snapshot row is re-keyed to the ISIN's latest symbol.
    latest_symbol = out.sort_values("SnapshotDate").groupby("ISIN")["Symbol"].last()
    out["Symbol"] = out["ISIN"].map(latest_symbol).fillna(out["Symbol"])
    out.to_csv(MEMBERSHIP_PATH, index=False)
    return out


def load_membership():
    global _membership_cache
    if _membership_cache is None:
        if not os.path.exists(MEMBERSHIP_PATH):
            raise RuntimeError(
                "Historical universe not built. Run `python historical_universe.py` once.")
        df = pd.read_csv(MEMBERSHIP_PATH)
        df["SnapshotDate"] = pd.to_datetime(df["SnapshotDate"]).dt.date
        _membership_cache = df
    return _membership_cache


def snapshot_dates():
    return sorted(load_membership()["SnapshotDate"].unique())


def _as_of_snapshot(day):
    """Latest snapshot dated <= day; the earliest one if day predates all."""
    dates = snapshot_dates()
    eligible = [d for d in dates if d <= day]
    return eligible[-1] if eligible else dates[0]


@functools.lru_cache(maxsize=None)
def _members_of_snapshot(snap):
    df = load_membership()
    return frozenset(df.loc[df["SnapshotDate"] == snap, "Symbol"])


def members_as_of(day):
    """frozenset of symbols in the Nifty 500 on `day` (cached per snapshot,
    so calling it once per simulated day is cheap)."""
    return _members_of_snapshot(_as_of_snapshot(day))


def symbols_between(start_date, end_date):
    """Every symbol that was a member at any point in [start, end] - the set
    whose price history the backtest needs to load."""
    df = load_membership()
    dates = snapshot_dates()
    relevant = {_as_of_snapshot(start_date), _as_of_snapshot(end_date)}
    relevant |= {d for d in dates if start_date <= d <= end_date}
    return sorted(df[df["SnapshotDate"].isin(relevant)]["Symbol"].unique())


def universe_info(symbols=None):
    """{symbol: {"Name", "Sector"}} using each symbol's most recent snapshot
    entry - for sector/name lookups by the rules (generated_rules uses it)."""
    df = load_membership().sort_values("SnapshotDate").drop_duplicates("Symbol", keep="last")
    if symbols is not None:
        df = df[df["Symbol"].isin(set(symbols))]
    return {r.Symbol: {"Name": r.Name, "Sector": r.Sector} for r in df.itertuples()}


def coverage_report(start_date=None, end_date=None):
    dates = snapshot_dates()
    lines = [f"{len(dates)} snapshots: {dates[0]} -> {dates[-1]}"]
    prev = None
    for d in dates:
        if prev is not None:
            gap = (d - prev).days
            a = set(load_membership().query("SnapshotDate == @prev")["ISIN"])
            b = set(load_membership().query("SnapshotDate == @d")["ISIN"])
            flag = "  <-- long gap" if gap > 200 else ""
            lines.append(f"  {prev} -> {d}: {gap:4d}d, +{len(b - a)} / -{len(a - b)} constituents{flag}")
        prev = d
    return "\n".join(lines)


if __name__ == "__main__":
    print("Looking for new archived Nifty 500 snapshots...")
    new = download_missing()
    out = build_membership()
    print(f"Built membership.csv: {out['SnapshotDate'].nunique()} snapshots, "
          f"{out['Symbol'].nunique()} distinct symbols.")
    print(coverage_report())
