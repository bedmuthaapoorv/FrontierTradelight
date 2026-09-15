"""NAV/units accounting for the real-money fund - entirely separate from
the backtest engine. The backtest is a research tool for evaluating
strategies against history; the fund's AUM/NAV/units here are derived only
from fund_holdings.csv (the fund's own real positions + cash) and
capital_events.csv (real deposits/withdrawals), never from any backtest
output.

Units/NAV mechanics: a deposit/withdrawal buys/redeems units at the NAV in
effect BEFORE that event is applied, so new money never inflates the NAV it
buys into. Every investor's return is then just
(units_held * latest_NAV - net_capital_contributed) / net_capital_contributed,
correct regardless of when they joined - see nav_history.csv/capital_events.csv
for the append-only ledgers this all reads from.
"""

import json
import os
from datetime import date

import pandas as pd

from constants import (
    FUND_CAPITAL_EVENTS_PATH,
    FUND_CASH_PATH,
    FUND_GENERATION_PATH,
    FUND_HOLDINGS_PATH,
    FUND_INVESTORS_PATH,
    FUND_NAV_HISTORY_PATH,
)

INVESTORS_COLUMNS = ["InvestorID", "Name", "Email", "JoinDate"]
CAPITAL_EVENTS_COLUMNS = ["Date", "InvestorID", "Type", "Amount", "NAV", "Units"]
NAV_HISTORY_COLUMNS = ["Date", "AUM", "TotalUnits", "NAV", "Generation"]
FUND_HOLDINGS_COLUMNS = ["Symbol", "Qty", "AvgCost", "CurrentPrice"]

BASE_NAV = 100.0
UNITS_EPSILON = 1e-6  # float noise from repeated amount/NAV division never nets to exactly 0


def _read_csv(path, columns):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return pd.DataFrame(columns=columns)
    return pd.read_csv(path)


def load_investors():
    return _read_csv(FUND_INVESTORS_PATH, INVESTORS_COLUMNS)


def load_capital_events():
    return _read_csv(FUND_CAPITAL_EVENTS_PATH, CAPITAL_EVENTS_COLUMNS)


def load_nav_history():
    nav_df = _read_csv(FUND_NAV_HISTORY_PATH, NAV_HISTORY_COLUMNS)
    if "Generation" not in nav_df.columns:
        nav_df["Generation"] = 0  # rows written before generation-tagging existed
    nav_df["Generation"] = nav_df["Generation"].fillna(0).astype(int)
    return nav_df


def load_generation():
    """The fund's current "era" number - bumped every time total units
    outstanding falls back to 0 (every investor fully withdrawn), so a NAV
    struck in a past era can never be mistaken for a live price in the
    current one (see latest_nav)."""
    if not os.path.exists(FUND_GENERATION_PATH):
        return 0
    with open(FUND_GENERATION_PATH, "r", encoding="utf-8") as f:
        return int(json.load(f).get("generation", 0))


def save_generation(generation):
    os.makedirs(os.path.dirname(FUND_GENERATION_PATH), exist_ok=True)
    with open(FUND_GENERATION_PATH, "w", encoding="utf-8") as f:
        json.dump({"generation": int(generation)}, f)


def load_fund_holdings():
    return _read_csv(FUND_HOLDINGS_PATH, FUND_HOLDINGS_COLUMNS)


def load_cash():
    if not os.path.exists(FUND_CASH_PATH):
        return 0.0
    with open(FUND_CASH_PATH, "r", encoding="utf-8") as f:
        return float(json.load(f).get("amount", 0.0))


def save_cash(amount):
    os.makedirs(os.path.dirname(FUND_CASH_PATH), exist_ok=True)
    with open(FUND_CASH_PATH, "w", encoding="utf-8") as f:
        json.dump({"amount": float(amount)}, f)


def compute_aum():
    """Fund AUM = sum(Qty * CurrentPrice) over fund_holdings.csv, plus cash.
    Never touches backtest_portfolio.csv or any other backtest output."""
    holdings_df = load_fund_holdings()
    positions_value = float((holdings_df["Qty"] * holdings_df["CurrentPrice"]).sum()) if not holdings_df.empty else 0.0
    return positions_value + load_cash()


def latest_nav():
    """Most recently recorded NAV *in the current generation* - or BASE_NAV
    whenever the fund currently has zero units outstanding, or the current
    generation has no NAV recorded yet. A past generation's NAV rows stay
    exactly as recorded in nav_history.csv (real history for whoever held
    through it) but are never read here once the fund has fully wound down
    and restarted - see load_generation - so a stale figure with nothing
    behind it can never re-price a fresh era's investors."""
    if total_units_outstanding() == 0.0:
        return BASE_NAV
    nav_df = load_nav_history()
    nav_df = nav_df[nav_df["Generation"] == load_generation()]
    if nav_df.empty:
        return BASE_NAV
    nav_df = nav_df.sort_values("Date")
    return float(nav_df.iloc[-1]["NAV"])


def total_units_outstanding():
    """Sum of every capital event's signed Units, snapped to a clean 0 when
    within float noise of it (e.g. a full withdrawal leaving -1e-13 instead
    of exactly 0)."""
    events_df = load_capital_events()
    if events_df.empty:
        return 0.0
    total = float(events_df["Units"].sum())
    return 0.0 if abs(total) < UNITS_EPSILON else total


def record_nav_for_today():
    """Computes today's NAV from AUM / units-outstanding-before-today, and
    appends (or overwrites, if already recorded today) a row to
    nav_history.csv. Mirrors the design's rule: today's capital events are
    applied AFTER this NAV is struck, so new money never inflates the NAV
    it buys into."""
    today = date.today()
    # Units strictly before today (a capital event dated today must not
    # affect the NAV struck for today).
    events_df = load_capital_events()
    if events_df.empty:
        units_pre = 0.0
    else:
        events_df["Date"] = pd.to_datetime(events_df["Date"]).dt.date
        units_pre = float(events_df[events_df["Date"] < today]["Units"].sum())
        if abs(units_pre) < UNITS_EPSILON:
            units_pre = 0.0

    aum = compute_aum()

    if units_pre <= 0:
        return {
            "status": "error",
            "message": "No capital events recorded before today - add the fund's first deposit before striking a NAV.",
        }

    nav = aum / units_pre

    nav_df = load_nav_history()
    nav_df["Date"] = nav_df["Date"].astype(str) if not nav_df.empty else nav_df["Date"]
    today_str = today.isoformat()
    nav_df = nav_df[nav_df["Date"] != today_str]
    new_row = pd.DataFrame([{"Date": today_str, "AUM": aum, "TotalUnits": units_pre, "NAV": nav, "Generation": load_generation()}])
    nav_df = pd.concat([nav_df, new_row], ignore_index=True)
    os.makedirs(os.path.dirname(FUND_NAV_HISTORY_PATH), exist_ok=True)
    nav_df.to_csv(FUND_NAV_HISTORY_PATH, index=False)

    return {"status": "ok", "date": today_str, "aum": aum, "total_units": units_pre, "nav": nav}


def investor_summary():
    """Every investor with their current unit holding, value at the latest
    NAV, and return % against their net capital contributed - each figure
    correct regardless of when that investor joined, since it only reads
    off their own capital_events rows."""
    investors_df = load_investors()
    events_df = load_capital_events()
    nav = latest_nav()

    rows = []
    for _, inv in investors_df.iterrows():
        inv_events = events_df[events_df["InvestorID"] == inv["InvestorID"]] if not events_df.empty else events_df
        units_held = float(inv_events["Units"].sum()) if not inv_events.empty else 0.0
        if abs(units_held) < UNITS_EPSILON:
            units_held = 0.0  # snap float noise (e.g. -1e-13 from a full withdrawal) to a clean 0
        net_contributed = 0.0
        if not inv_events.empty:
            deposits = inv_events[inv_events["Type"] == "DEPOSIT"]["Amount"].sum()
            withdrawals = inv_events[inv_events["Type"] == "WITHDRAWAL"]["Amount"].sum()
            net_contributed = float(deposits - withdrawals)
        current_value = units_held * nav
        return_pct = ((current_value - net_contributed) / net_contributed * 100) if net_contributed > 0 else None
        rows.append({
            "investor_id": inv["InvestorID"],
            "name": inv["Name"],
            "email": inv["Email"] if pd.notna(inv["Email"]) else "",
            "join_date": inv["JoinDate"],
            "units_held": units_held,
            "current_value": current_value,
            "return_pct": return_pct,
        })
    return rows


def append_investor(investor_id, name, email, join_date):
    investors_df = load_investors()
    investors_df = investors_df[investors_df["InvestorID"] != investor_id]
    new_row = pd.DataFrame([{"InvestorID": investor_id, "Name": name, "Email": email, "JoinDate": join_date}])
    investors_df = pd.concat([investors_df, new_row], ignore_index=True)
    os.makedirs(os.path.dirname(FUND_INVESTORS_PATH), exist_ok=True)
    investors_df.to_csv(FUND_INVESTORS_PATH, index=False)


def remove_investor(investor_id):
    """Removes an investor record. Refused only if they still hold a
    non-negligible unit balance (removing them would silently drop their
    share of total units, corrupting every other investor's NAV-derived
    value) - a real exit must go through a WITHDRAWAL capital event first.
    Past capital events are left as-is in capital_events.csv (the audit
    trail), just no longer joined to an active investor row - fully
    withdrawing and then removing an investor is the normal offboarding
    flow, not something to block."""
    events_df = load_capital_events()
    inv_events = events_df[events_df["InvestorID"] == investor_id] if not events_df.empty else events_df
    if not inv_events.empty:
        units_held = float(inv_events["Units"].sum())
        if abs(units_held) > UNITS_EPSILON:
            return {"status": "error", "message": "Investor still holds units - record a WITHDRAWAL for their full balance first."}

    investors_df = load_investors()
    investors_df = investors_df[investors_df["InvestorID"] != investor_id]
    investors_df.to_csv(FUND_INVESTORS_PATH, index=False)
    return {"status": "ok"}


def append_capital_event(event_date, investor_id, event_type, amount, nav_override=None):
    """Records a deposit/withdrawal, buying/redeeming units at the NAV in
    effect right now (the latest recorded NAV) - not a NAV computed from
    today's post-event AUM, so this event itself never moves the NAV it
    transacts at.

    nav_override lets you backfill a REAL past event at the NAV it actually
    transacted at, instead of today's live NAV - the normal case for
    entering history after the fact (e.g. an investor who joined on a date
    the fund's per-unit value genuinely differed from what it is today).
    Get it wrong and every investor's current value/return becomes wrong,
    so only use it when you know the true historical NAV."""
    units_before = total_units_outstanding()
    nav = nav_override if nav_override is not None else latest_nav()
    units = (amount / nav) if event_type == "DEPOSIT" else -(amount / nav)

    events_df = load_capital_events()
    new_row = pd.DataFrame([{
        "Date": event_date, "InvestorID": investor_id, "Type": event_type,
        "Amount": amount, "NAV": nav, "Units": units,
    }])
    events_df = pd.concat([events_df, new_row], ignore_index=True)
    os.makedirs(os.path.dirname(FUND_CAPITAL_EVENTS_PATH), exist_ok=True)
    events_df.to_csv(FUND_CAPITAL_EVENTS_PATH, index=False)

    # A withdrawal that brings the fund back to exactly 0 units ends this
    # generation - the next deposit starts a fresh one, so no stale NAV row
    # from this generation can ever price it (see latest_nav).
    if units_before != 0.0 and total_units_outstanding() == 0.0:
        save_generation(load_generation() + 1)

    return {"nav": nav, "units": units}


def remove_capital_event(row_index):
    """Deletes one capital event by its row position in capital_events.csv
    (the identifier /fund-manager/overview hands back per event - same
    "position in the file is the id" approach as this tool's other
    single-user CRUD, e.g. backup filenames). Only corrects the ledger
    going forward: a NAV already struck and recorded in nav_history.csv
    before the correction is left as-is, not retroactively recalculated."""
    events_df = load_capital_events()
    if row_index not in events_df.index:
        return {"status": "error", "message": "Capital event not found."}
    events_df = events_df.drop(index=row_index)
    events_df.to_csv(FUND_CAPITAL_EVENTS_PATH, index=False)
    return {"status": "ok"}
