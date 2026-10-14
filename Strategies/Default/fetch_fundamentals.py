"""Fetches annual fundamentals for every stock ever in the Nifty 500 from
Screener.in public company pages and caches them under data/fundamentals/.

A Python port of the fetch/parse logic in the screener-india Node library
(github.com/sahiljani/screener-india): GET /company/{SYMBOL}/consolidated/
(or /company/{SYMBOL}/ for standalone) and read each section#<name> table as
header row + body rows.

Screener.in's terms permit personal, non-commercial use only. Requests are
strictly sequential and throttled, the cache is gitignored, and nothing
derived from it may be published (e.g. on the fund website).

Outputs:
  raw/{SYMBOL}.json  parsed tables per symbol, so normalisation can be
                     re-run without refetching (--rebuild-only)
  annual.csv         one row per symbol x fiscal year, with available_from =
                     the date the figures could first have been known
  fetch_log.csv      per-symbol status of the last attempt

Run with no arguments to refresh everything older than REFRESH_DAYS.
"""

import argparse
import calendar
import glob
import json
import os
import random
import re
import sys
import time
from datetime import date, datetime, timedelta
from urllib.parse import quote

import pandas as pd
import requests
from bs4 import BeautifulSoup

from constants import FUNDAMENTALS_ANNUAL_PATH, FUNDAMENTALS_LOG_PATH, FUNDAMENTALS_RAW_DIR
from historical_universe import RAW_DIR as UNIVERSE_RAW_DIR, load_membership

BASE_URL = "https://www.screener.in"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TABLE_SECTIONS = {
    "quarters": "quarters",
    "profit_loss": "profit-loss",
    "balance_sheet": "balance-sheet",
    "cash_flow": "cash-flow",
    "ratios": "ratios",
}

# Companies renamed after they left the Nifty 500, so membership.csv only
# knows the old ticker and Screener's name search doesn't match it. Each was
# confirmed by the Screener page's own "About" text naming the old company.
SCREENER_ALIASES = {
    "IIFLWAM": "360ONE",        # IIFL Wealth Management -> 360 ONE WAM
    "PHILIPCARB": "PCBL",       # Phillips Carbon Black -> PCBL Chemical
    "LAXMIMACH": "LMW",         # Lakshmi Machine Works -> LMW
    "NBVENTURES": "NAVA",       # Nava Bharat Ventures -> Nava
    "IBREALEST": "EMBDL",       # Indiabulls Real Estate -> Embassy Developments
    "SEQUENT": "VIYASH",        # Sequent Scientific -> Viyash Scientific
    "JCHAC": "BOSCH-HCIL",      # Johnson Controls-Hitachi AC -> Bosch Home Comfort
    "INFIBEAM": "CCAVENUE",     # Infibeam Avenues -> AvenuesAI
}

REQUEST_GAP_SECONDS = (2.0, 3.5)
RETRIES = 3
REFRESH_DAYS = 90
MAX_CONSECUTIVE_BLOCKS = 5
MIN_SUCCESS_RATE = 0.70

# SEBI deadline for audited annual results is 60 days after year-end. FY20
# (March 2020) results were allowed until 31 Jul 2020 because of COVID.
ANNUAL_LAG_DAYS = 60
AVAILABLE_FROM_OVERRIDES = {date(2020, 3, 31): date(2020, 7, 31)}

# (table, label regex matched against the cleaned row label, output column)
ROW_MAP = [
    ("profit_loss", r"sales|revenue", "sales"),
    ("profit_loss", r"net profit", "net_profit"),
    ("profit_loss", r"eps in rs", "eps"),
    ("balance_sheet", r"equity capital", "equity_capital"),
    ("balance_sheet", r"reserves", "reserves"),
    ("balance_sheet", r"borrowings?", "borrowings"),
    ("balance_sheet", r"total assets", "total_assets"),
    ("ratios", r"roce %", "roce_pct"),
]
ANNUAL_COLUMNS = [
    "symbol", "isin", "sector", "basis", "period_end", "months",
    "sales", "net_profit", "eps", "equity_capital", "reserves", "borrowings",
    "total_assets", "roce_pct", "available_from", "fetched_at",
]
LOG_COLUMNS = ["symbol", "status", "basis", "latest_period", "years", "fetched_at", "url", "message"]

PERIOD_RE = re.compile(r"^([A-Za-z]{3})\s+(\d{4})(?:\s*(\d+)\s*m)?$")
MONTHS = {m: i for i, m in enumerate(calendar.month_abbr) if m}


class NotFound(Exception):
    pass


class LoginRequired(Exception):
    pass


class Blocked(Exception):
    pass


_last_request = 0.0


def _pause():
    global _last_request
    gap = random.uniform(*REQUEST_GAP_SECONDS)
    wait = _last_request + gap - time.time()
    if wait > 0:
        time.sleep(wait)
    _last_request = time.time()


def _get(session, url):
    last = None
    for attempt in range(RETRIES):
        _pause()
        try:
            r = session.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        except requests.RequestException as e:
            last = str(e)
            time.sleep(5 * (attempt + 1))
            continue
        if "/login" in r.url or "/register" in r.url:
            raise LoginRequired(url)
        if r.status_code == 404:
            raise NotFound(url)
        if r.status_code == 200:
            return r
        last = f"HTTP {r.status_code}"
        time.sleep((15 if r.status_code == 429 else 5) * (attempt + 1))
    raise Blocked(f"{url}: {last}")


def parse_tables(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = {}
    for key, section_id in TABLE_SECTIONS.items():
        section = soup.find("section", id=section_id)
        table = section.find("table") if section else None
        headers, rows = [], []
        if table is not None:
            thead = table.find("thead")
            header_row = thead.find("tr") if thead else table.find("tr")
            if header_row:
                headers = [c.get_text(" ", strip=True) for c in header_row.find_all(["th", "td"])]
            tbody = table.find("tbody")
            body_rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]
            for tr in body_rows:
                cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if cells:
                    rows.append(cells)
        tables[key] = {"headers": headers, "rows": rows}
    return tables


def _parse_period(header):
    m = PERIOD_RE.match(header.replace("\xa0", " ").strip())
    if not m or m.group(1).title() not in MONTHS:
        return None, None
    year, month = int(m.group(2)), MONTHS[m.group(1).title()]
    end = date(year, month, calendar.monthrange(year, month)[1])
    return end, int(m.group(3)) if m.group(3) else 12


def _latest_annual(tables):
    periods = [_parse_period(h)[0] for h in tables["profit_loss"]["headers"][1:]]
    periods = [p for p in periods if p is not None]
    return max(periods) if periods else None


def _expected_latest_fy(today):
    """Most recent March year-end whose results deadline has passed."""
    this_year = date(today.year, 3, 31)
    return this_year if today >= this_year + timedelta(days=ANNUAL_LAG_DAYS) else date(today.year - 1, 3, 31)


def _company_url(slug, consolidated):
    base = f"{BASE_URL}/company/{quote(slug, safe='')}/"
    return base + "consolidated/" if consolidated else base


def _fetch_slug(session, slug, today):
    """Returns (basis, tables, url) for one Screener company slug, picking
    consolidated unless standalone has a later annual period."""
    cons_url = _company_url(slug, True)
    cons = parse_tables(_get(session, cons_url).text)
    cons_latest = _latest_annual(cons)
    if cons_latest is not None and cons_latest >= _expected_latest_fy(today):
        return "consolidated", cons, cons_url

    stand_url = _company_url(slug, False)
    try:
        stand = parse_tables(_get(session, stand_url).text)
    except (NotFound, LoginRequired):
        stand = None
    stand_latest = _latest_annual(stand) if stand else None
    if stand_latest is not None and (cons_latest is None or stand_latest > cons_latest):
        return "standalone", stand, stand_url
    if cons_latest is None:
        raise NotFound(f"{slug}: no annual data")
    return "consolidated", cons, cons_url


def _alternate_tickers(isins, current):
    """Older NSE tickers for the same ISINs, from the raw index snapshots
    (membership.csv only keeps the latest ticker per ISIN)."""
    found = []
    for path in sorted(glob.glob(os.path.join(UNIVERSE_RAW_DIR, "nifty500_*.csv"))):
        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = [c.strip() for c in df.columns]
        for sym in df.loc[df["ISIN Code"].isin(isins), "Symbol"].astype(str).str.strip():
            if sym != current and sym not in found:
                found.append(sym)
    return found


def _search_slug(session, name):
    """Screener search fallback; only trusted if the first word of the
    company name matches, so an unrelated company is never cached."""
    query = re.sub(r"\b(ltd|limited)\.?$", "", name, flags=re.I).strip()
    try:
        r = _get(session, f"{BASE_URL}/api/company/search/?q={quote(query)}&limit=5")
        results = r.json()
    except (NotFound, LoginRequired, Blocked, ValueError):
        return None
    first_word = query.split()[0].lower() if query else ""
    for item in results:
        url = item.get("url", "")
        m = re.match(r"^/company/([^/]+)/", url)
        if m and item.get("name", "").lower().startswith(first_word):
            return m.group(1)
    return None


def fetch_company(session, symbol, isins, name, today):
    if symbol in SCREENER_ALIASES:
        return _fetch_slug(session, SCREENER_ALIASES[symbol], today)
    try:
        return _fetch_slug(session, symbol, today)
    except NotFound:
        pass
    for alt in _alternate_tickers(isins, symbol):
        try:
            return _fetch_slug(session, alt, today)
        except NotFound:
            continue
    slug = _search_slug(session, name)
    if slug and slug != symbol:
        return _fetch_slug(session, slug, today)
    raise NotFound(f"{symbol}: not on Screener.in")


def _clean_label(label):
    return re.sub(r"[\s\xa0]*\+$", "", label.replace("\xa0", " ")).strip().lower()


def _num(text):
    s = text.replace(",", "").replace("%", "").strip()
    if s in ("", "-", "--"):
        return float("nan")
    try:
        return float(s)
    except ValueError:
        return float("nan")


def normalize(record):
    """Turns one raw/{SYMBOL}.json record into annual rows."""
    tables = record["tables"]
    by_period = {}
    months_of = {}
    for h in tables["profit_loss"]["headers"][1:]:
        end, months = _parse_period(h)
        if end is not None:
            months_of[end] = months
    for table_key, pattern, field in ROW_MAP:
        table = tables.get(table_key, {"headers": [], "rows": []})
        periods = [_parse_period(h)[0] for h in table["headers"][1:]]
        for row in table["rows"]:
            if not row or not re.fullmatch(pattern, _clean_label(row[0])):
                continue
            for end, value in zip(periods, row[1:]):
                if end is not None:
                    by_period.setdefault(end, {})[field] = _num(value)
            break
    rows = []
    for end in sorted(by_period):
        if end not in months_of:
            continue
        values = by_period[end]
        rows.append({
            "symbol": record["symbol"],
            "isin": record["isin"],
            "sector": record["sector"],
            "basis": record["basis"],
            "period_end": end.isoformat(),
            "months": months_of[end],
            **{field: values.get(field, float("nan")) for _, _, field in ROW_MAP},
            "available_from": AVAILABLE_FROM_OVERRIDES.get(end, end + timedelta(days=ANNUAL_LAG_DAYS)).isoformat(),
            "fetched_at": record["fetched_at"],
        })
    return rows


def rebuild_annual():
    rows = []
    for path in sorted(glob.glob(os.path.join(FUNDAMENTALS_RAW_DIR, "*.json"))):
        with open(path, encoding="utf-8") as f:
            rows.extend(normalize(json.load(f)))
    df = pd.DataFrame(rows, columns=ANNUAL_COLUMNS)
    df.to_csv(FUNDAMENTALS_ANNUAL_PATH, index=False)
    return df


def _raw_path(symbol):
    return os.path.join(FUNDAMENTALS_RAW_DIR, re.sub(r"[^A-Za-z0-9_-]", "_", symbol) + ".json")


def _load_log():
    if not os.path.exists(FUNDAMENTALS_LOG_PATH):
        return {}
    df = pd.read_csv(FUNDAMENTALS_LOG_PATH, dtype=str, keep_default_na=False)
    return {r["symbol"]: r for r in df.to_dict("records")}


def _save_log(log):
    pd.DataFrame(list(log.values()), columns=LOG_COLUMNS).sort_values("symbol").to_csv(
        FUNDAMENTALS_LOG_PATH, index=False)


def _universe():
    m = load_membership()
    m = m[~m["Symbol"].astype(str).str.startswith("DUMMY")]
    latest = m.sort_values("SnapshotDate").groupby("Symbol").last()
    isins = m.groupby("Symbol")["ISIN"].agg(lambda s: sorted(set(s)))
    return {
        sym: {"isin": row["ISIN"], "isins": isins[sym], "name": row["Name"], "sector": row["Sector"]}
        for sym, row in latest.iterrows()
    }


def _is_fresh(entry, now):
    if not entry or entry["status"] not in ("ok", "not_found") or not entry["fetched_at"]:
        return False
    return now - datetime.fromisoformat(entry["fetched_at"]) < timedelta(days=REFRESH_DAYS)


def main():
    parser = argparse.ArgumentParser(description="Fetch and cache Screener.in annual fundamentals for Nifty 500 symbols.")
    parser.add_argument("--symbols", nargs="+", help="Only these symbols (must be in membership.csv)")
    parser.add_argument("--force", action="store_true", help="Refetch even if fetched recently")
    parser.add_argument("--max", type=int, help="Stop after fetching this many symbols")
    parser.add_argument("--rebuild-only", action="store_true", help="Rebuild annual.csv from cached raw JSON, no network")
    args = parser.parse_args()

    if args.rebuild_only:
        df = rebuild_annual()
        print(f"annual.csv rebuilt: {len(df)} rows, {df['symbol'].nunique()} symbols")
        return 0

    universe = _universe()
    symbols = sorted(universe)
    if args.symbols:
        unknown = [s for s in args.symbols if s not in universe]
        if unknown:
            print(f"Not in membership.csv, skipped: {', '.join(unknown)}")
        symbols = [s for s in args.symbols if s in universe]

    log = _load_log()
    now = datetime.now()
    todo = [s for s in symbols if args.force or not _is_fresh(log.get(s), now)]
    if args.max:
        todo = todo[:args.max]
    print(f"{len(symbols)} symbols, {len(symbols) - len(todo)} fresh (skipped), {len(todo)} to fetch")

    session = requests.Session()
    counts = {"ok": 0, "not_found": 0, "login_required": 0, "error": 0}
    consecutive_blocks = 0
    aborted = False
    for i, sym in enumerate(todo, 1):
        info = universe[sym]
        entry = {"symbol": sym, "fetched_at": datetime.now().isoformat(timespec="seconds"),
                 "basis": "", "latest_period": "", "years": "", "url": "", "message": ""}
        try:
            basis, tables, url = fetch_company(session, sym, info["isins"], info["name"], now.date())
            record = {"symbol": sym, "isin": info["isin"], "sector": info["sector"], "basis": basis,
                      "url": url, "fetched_at": entry["fetched_at"], "tables": tables}
            with open(_raw_path(sym), "w", encoding="utf-8") as f:
                json.dump(record, f)
            years = normalize(record)
            entry.update(status="ok", basis=basis, url=url, years=str(len(years)),
                         latest_period=years[-1]["period_end"] if years else "")
            consecutive_blocks = 0
        except NotFound as e:
            entry.update(status="not_found", message=str(e))
            consecutive_blocks = 0
        except LoginRequired as e:
            entry.update(status="login_required", message=str(e))
        except Blocked as e:
            entry.update(status="error", message=str(e))
            consecutive_blocks += 1
        except Exception as e:  # parsing surprises shouldn't kill a 45-minute run
            entry.update(status="error", message=f"{type(e).__name__}: {e}")
        counts[entry["status"]] += 1
        log[sym] = entry
        _save_log(log)
        print(f"[{i}/{len(todo)}] {sym}: {entry['status']} {entry['basis']} "
              f"{entry['years'] and entry['years'] + ' yrs'} {entry['latest_period']} {entry['message']}".rstrip())
        if consecutive_blocks >= MAX_CONSECUTIVE_BLOCKS:
            print(f"Stopping: {MAX_CONSECUTIVE_BLOCKS} consecutive blocked requests - Screener.in may be rate-limiting. Rerun later; finished symbols are kept.")
            aborted = True
            break

    df = rebuild_annual()
    attempted = sum(counts.values())
    print(f"\nFetched: {counts['ok']} ok, {counts['not_found']} not found, "
          f"{counts['login_required']} login required, {counts['error']} errors (of {attempted} attempted)")
    print(f"annual.csv: {len(df)} rows, {df['symbol'].nunique()} symbols")
    if attempted and (counts["ok"] + counts["not_found"]) / attempted < MIN_SUCCESS_RATE:
        print(f"WARNING: under {MIN_SUCCESS_RATE:.0%} of attempted symbols resolved - check fetch_log.csv")
    return 1 if aborted else 0


if __name__ == "__main__":
    sys.exit(main())
