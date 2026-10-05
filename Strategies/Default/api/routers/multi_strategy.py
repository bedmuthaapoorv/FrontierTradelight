"""Multi-Strategy tab: one stock, several saved strategies at once. See
multi_strategy_utils.py for how strategies are compiled and evaluated."""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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


@router.post("/run-stream")
def run_stream(body: RunRequest):
    """Same as /run, but streams newline-delimited JSON events as each
    strategy progresses (type "progress"), ending with one "result" or
    "error" event - drives the per-strategy progress bars."""
    if not body.symbol.strip():
        raise HTTPException(status_code=400, detail="Enter a stock symbol.")
    if not body.strategy_keys:
        raise HTTPException(status_code=400, detail="Select at least one strategy.")

    def lines():
        for event in ms.run_stock_events(body.symbol, body.strategy_keys, body.refresh_context):
            yield json.dumps(event) + "\n"

    return StreamingResponse(lines(), media_type="application/x-ndjson")
