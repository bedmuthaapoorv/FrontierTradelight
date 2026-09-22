"""PIB naval-commissioning event watcher - see event_watcher_utils.py for
the reasoning. Read-only signal tab: GET returns the cached matches, POST
/refresh re-polls PIB and merges in anything new."""

from fastapi import APIRouter
from pydantic import BaseModel

import event_watcher_utils as ew

router = APIRouter(prefix="/event-watcher")


@router.get("")
def get_events():
    return ew.get_state()


@router.post("/refresh")
def refresh_events():
    return ew.refresh()


class HistoricalRequest(BaseModel):
    date: str


@router.post("/historical")
def fetch_historical_events(body: HistoricalRequest):
    return ew.fetch_historical(body.date)


@router.delete("/historical")
def clear_historical_events():
    return ew.clear_historical()


class WatchlistGroup(BaseModel):
    symbol: str
    names: list[str]


class VesselClassAlias(BaseModel):
    phrase: str
    symbol: str


class KeywordConfigRequest(BaseModel):
    event_keywords: list[str]
    watchlist: list[WatchlistGroup]
    vessel_class_aliases: list[VesselClassAlias]


@router.get("/keywords")
def get_keywords():
    return ew.get_keyword_config()


@router.put("/keywords")
def put_keywords(body: KeywordConfigRequest):
    return ew.set_keyword_config(body.model_dump())
