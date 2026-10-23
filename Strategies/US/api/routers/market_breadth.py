"""Latest market breadth (% of universe above its 50-day MA), as saved by
the most recent screener run - the header shows it without refetching."""

import json
import os

from fastapi import APIRouter

from constants import MARKET_BREADTH_PATH

router = APIRouter()


@router.get("/market-breadth")
def market_breadth():
    if not os.path.exists(MARKET_BREADTH_PATH):
        return {"breadth": None}
    with open(MARKET_BREADTH_PATH, encoding="utf-8") as f:
        return json.load(f)
