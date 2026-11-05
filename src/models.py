"""
Typed Request and Response Models for Scrolls of Agora.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class BuyoutRequest(BaseModel):
    listing_id: int = Field(..., description="Target auction listing ID to buyout")
    buyer_id: int = Field(..., description="Player ID acquiring the item")


class BidRequest(BaseModel):
    listing_id: int = Field(..., description="Target auction listing ID")
    bidder_id: int = Field(..., description="Player ID placing the bid")
    bid_amount: int = Field(..., description="Total gold amount locked in escrow", gt=0)


class ListItemRequest(BaseModel):
    instance_id: int = Field(..., description="Physical item instance ID from bag")
    seller_id: int = Field(..., description="Player ID selling the item")
    realm_id: Optional[int] = Field(None, description="Optional target kiosk hub ID")
    start_price: int = Field(..., description="Starting bid floor in gold", gt=0)
    buyout_price: int = Field(..., description="Instant purchase price in gold", gt=0)


class TemperCraftRequest(BaseModel):
    instance_id: int = Field(..., description="Physical weapon/armor instance ID")
    player_id: int = Field(..., description="Player ID initiating tempering")
    enchant_id: int = Field(1, description="Glyph enchantment to bind")


class KioskBidRequest(BaseModel):
    realm_id: int = Field(..., description="Target regional trading hub")
    guild_id: int = Field(..., description="Bidding trade syndicate ID")
    bid_gold: int = Field(..., description="Sealed treasury bid in gold", gt=0)


class DupeStressRequest(BaseModel):
    concurrent_threads: int = Field(100, description="Concurrent threads firing buyout", ge=2, le=200)
    locking_mode: str = Field(
        "PESSIMISTIC_FOR_UPDATE",
        description="PESSIMISTIC_FOR_UPDATE or UNSAFE_NAIVE_READ"
    )
