"""
Market API Router for Scrolls of Agora.
"""

from fastapi import APIRouter
from src.repositories.market_repo import get_market_state, get_item_candles
from src.database import get_engine_telemetry

router = APIRouter(tags=["Market Orderbook & State"])


@router.get("/api/state")
def api_get_market_state(player_id: int = 1005, realm_id: int = 0):
    return get_market_state(player_id=player_id, realm_id=realm_id)


@router.get("/api/candles/{item_id}")
def api_get_item_candles(item_id: int):
    return get_item_candles(item_id)


@router.get("/api/telemetry")
def api_get_engine_telemetry():
    return get_engine_telemetry()
