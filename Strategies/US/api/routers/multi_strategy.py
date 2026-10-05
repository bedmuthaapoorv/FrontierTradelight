"""Multi-Strategy tab: one stock, several saved strategies at once. See
multi_strategy_utils.py for how strategies are compiled and evaluated."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import multi_strategy_utils as ms

router = APIRouter(prefix="/multi-strategy")


@router.get("/strategies")
def get_strategies():
    context = ms.read_market_context()
    return {
        "strategies": ms.list_strategies(),
        "context_date": context["date"] if context else None,
    }


class RunRequest(BaseModel):
    symbol: str
    strategy_keys: list[str]
    refresh_context: bool = False


@router.post("/run")
def run(body: RunRequest):
    if not body.symbol.strip():
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")
    if not body.strategy_keys:
        raise HTTPException(status_code=400, detail="Select at least one strategy.")
    try:
        return ms.run_stock(body.symbol, body.strategy_keys, refresh_context=body.refresh_context)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not fetch data for {body.symbol.strip().upper()}: {e}")
