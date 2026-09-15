"""Read-only fund dashboard + NAV calculator, backed by fund_manager_utils.py
- entirely separate from the backtest engine's routers (backtest.py,
missed_opportunities.py, stats.py). This view never makes buy/sell
decisions; the personal Holdings/Sell tab (api/routers/holdings.py) is
untouched and unrelated to any of this.
"""

import os

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

import fund_manager_utils as fm
from constants import FUND_HOLDINGS_PATH

router = APIRouter(prefix="/fund-manager")


@router.get("/overview")
def get_overview():
    aum = fm.compute_aum()
    nav = fm.latest_nav()
    nav_df = fm.load_nav_history().sort_values("Date") if not fm.load_nav_history().empty else fm.load_nav_history()
    events_df = fm.load_capital_events()
    events_df = events_df.sort_values("Date", ascending=False) if not events_df.empty else events_df

    total_units = fm.total_units_outstanding()

    return {
        "aum": aum,
        "nav": nav,
        "total_units": total_units,
        "investor_count": len(fm.load_investors()),
        "nav_history": [
            {"date": row["Date"], "nav": float(row["NAV"])} for _, row in nav_df.iterrows()
        ],
        "recent_capital_events": [
            {
                "index": int(idx),
                "date": row["Date"],
                "investor_id": row["InvestorID"],
                "type": row["Type"],
                "amount": float(row["Amount"]),
                "units": float(row["Units"]),
            }
            for idx, row in events_df.head(10).iterrows()
        ],
        "investors": fm.investor_summary(),
    }


@router.post("/nav/calculate")
def calculate_nav():
    return fm.record_nav_for_today()


class InvestorRequest(BaseModel):
    investor_id: str
    name: str
    email: str = ""
    join_date: str


@router.post("/investors")
def add_investor(body: InvestorRequest):
    fm.append_investor(body.investor_id, body.name, body.email, body.join_date)
    return {"status": "ok"}


@router.delete("/investors/{investor_id}")
def delete_investor(investor_id: str):
    return fm.remove_investor(investor_id)


class CapitalEventRequest(BaseModel):
    date: str
    investor_id: str
    type: str
    amount: float
    nav_override: float | None = None


@router.post("/capital-events")
def add_capital_event(body: CapitalEventRequest):
    if body.type not in ("DEPOSIT", "WITHDRAWAL"):
        return {"status": "error", "message": "type must be DEPOSIT or WITHDRAWAL"}
    result = fm.append_capital_event(body.date, body.investor_id, body.type, body.amount, body.nav_override)
    return {"status": "ok", **result}


@router.delete("/capital-events/{row_index}")
def delete_capital_event(row_index: int):
    return fm.remove_capital_event(row_index)


# --- Fund holdings: the fund's own positions + cash record. Whole-list
# replace, same pattern as api/routers/holdings.py's personal Holdings CRUD.

class FundHolding(BaseModel):
    Symbol: str
    Qty: float
    AvgCost: float
    CurrentPrice: float


class FundHoldingsPayload(BaseModel):
    holdings: list[FundHolding]
    cash: float


@router.get("/holdings")
def get_fund_holdings():
    df = fm.load_fund_holdings()
    return {"holdings": df.to_dict("records"), "cash": fm.load_cash()}


@router.put("/holdings")
def put_fund_holdings(body: FundHoldingsPayload):
    df = pd.DataFrame([h.model_dump() for h in body.holdings], columns=fm.FUND_HOLDINGS_COLUMNS)
    os.makedirs(os.path.dirname(FUND_HOLDINGS_PATH), exist_ok=True)
    df.to_csv(FUND_HOLDINGS_PATH, index=False)
    fm.save_cash(body.cash)
    return {"status": "saved", "count": len(df)}
