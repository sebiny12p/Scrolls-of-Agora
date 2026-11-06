"""
Continuous Limit Orderbook API Router for Scrolls of Agora.
Handles resting limit bids/asks and market depth calculations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.models import LimitOrderRequest
from src.repositories.orderbook_repo import place_limit_order, get_orderbook_depth
from src.auth import get_current_player_id, resolve_effective_player_id

router = APIRouter(prefix="/api/orderbook", tags=["Orderbook"])


@router.get("/depth")
def api_get_orderbook_depth(
    item_id: int = Query(..., description="Target item template ID"),
    realm_id: int = Query(0, description="Optional regional trading hub filter"),
):
    return get_orderbook_depth(item_id=item_id, realm_id=realm_id)


@router.post("/limit-order")
def api_place_limit_order(
    req: LimitOrderRequest,
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    player_id = resolve_effective_player_id(req.player_id, auth_pid)
    return place_limit_order(
        player_id=player_id,
        item_id=req.item_id,
        realm_id=req.realm_id,
        side=req.side,
        unit_price=req.unit_price,
        quantity=req.quantity,
    )
