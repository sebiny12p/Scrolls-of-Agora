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


class MailSendRequest(BaseModel):
    recipient_id: int = Field(..., description="Target player ID receiving the mail")
    sender_id: int = Field(..., description="Player ID sending the parcel")
    subject: str = Field(..., min_length=1, max_length=100, description="Mail subject line")
    body: str = Field("", description="Mail body text")
    attached_gold: int = Field(0, ge=0, description="Gold balance attached in transit")
    attached_instance_id: Optional[int] = Field(None, description="Optional inventory item attached")
    cod_amount: int = Field(0, ge=0, description="Cash-on-Delivery gold required to collect")


class MailClaimRequest(BaseModel):
    mail_id: int = Field(..., description="Target mail parcel ID")
    player_id: int = Field(..., description="Player ID claiming the attachment")


class RepairRequest(BaseModel):
    player_id: int = Field(..., description="Player repairing equipment")
    instance_id: Optional[int] = Field(None, description="Specific item instance or None for all equipped/bag gear")


class SimulateWearRequest(BaseModel):
    player_id: int = Field(..., description="Player whose gear takes durability wear")
    wear_amount: int = Field(15, ge=1, le=100, description="Durability points degraded")


class P2PTradeRequest(BaseModel):
    player_a_id: int = Field(..., description="Initiating player ID")
    player_b_id: int = Field(..., description="Counterparty player ID")
    gold_a: int = Field(0, ge=0, description="Gold offered by Player A")
    gold_b: int = Field(0, ge=0, description="Gold offered by Player B")
    instance_a_id: Optional[int] = Field(None, description="Optional item offered by Player A")
    instance_b_id: Optional[int] = Field(None, description="Optional item offered by Player B")


class LimitOrderRequest(BaseModel):
    player_id: int = Field(..., description="Player placing the limit order")
    item_id: int = Field(..., description="Target item template ID")
    realm_id: int = Field(..., description="Trading hub / realm ID")
    side: str = Field(..., description="BUY or SELL")
    unit_price: int = Field(..., gt=0, description="Limit price in gold")
    quantity: int = Field(1, ge=1, le=100, description="Number of units")


class AuthLoginRequest(BaseModel):
    player_id: Optional[int] = Field(None, description="Player ID to sign in as")
    username: Optional[str] = Field(None, description="Or username to sign in with")
