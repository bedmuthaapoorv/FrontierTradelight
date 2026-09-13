"""CRUD for data/holdings.csv, the sell-side mirror of the file CRUD in
markdown_files.py - a thin wrapper around read/write, no new logic. Mirrors
tabs/sell.py's render_holdings_editor, minus the Streamlit data_editor.
"""

import os

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from constants import HOLDINGS_PATH

router = APIRouter(prefix="/holdings")

COLUMNS = ["Symbol", "EntryPrice", "EntryDate", "CurrentPrice"]


class Holding(BaseModel):
    Symbol: str
    EntryPrice: float
    EntryDate: str
    CurrentPrice: float | None = None


class HoldingsPayload(BaseModel):
    holdings: list[Holding]


@router.get("")
def get_holdings():
    if not os.path.exists(HOLDINGS_PATH):
        return {"holdings": []}
    df = pd.read_csv(HOLDINGS_PATH)
    if "CurrentPrice" not in df.columns:
        df["CurrentPrice"] = None
    # astype(object) first: assigning None into a still-float64 column
    # silently reverts it back to NaN instead of keeping None.
    df = df.astype(object).where(pd.notnull(df), None)
    return {"holdings": df.to_dict("records")}


@router.put("")
def put_holdings(body: HoldingsPayload):
    df = pd.DataFrame([h.model_dump() for h in body.holdings], columns=COLUMNS)
    df.to_csv(HOLDINGS_PATH, index=False)
    return {"status": "saved", "count": len(df)}
