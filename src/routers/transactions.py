"""
Transactions API Router for Scrolls of Agora.
Handles buyouts, escrow bids, inventory listing, arcane forge, and weekly kiosk auctions.
"""

import random
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from src.models import (
    BuyoutRequest,
    BidRequest,
    ListItemRequest,
    TemperCraftRequest,
    KioskBidRequest,
    RepairRequest,
    SimulateWearRequest,
    P2PTradeRequest,
)
from src.repositories.transaction_repo import (
    execute_pessimistic_buyout,
    place_escrow_bid,
    list_inventory_item,
    temper_and_enchant_item,
    place_kiosk_bid,
    trigger_weekly_kiosk_flip,
    repair_player_equipment,
    degrade_equipment_durability,
    execute_p2p_trade,
    sweep_expired_listings,
)
from src.auth import get_current_player_id, resolve_effective_player_id
from src.database import get_db_cursor, execute_sql, rows_to_dicts, row_to_dict

router = APIRouter(tags=["ACID Transactions"])


@router.post("/api/buyout")
def api_buyout(req: BuyoutRequest):
    res = execute_pessimistic_buyout(req.listing_id, req.buyer_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/bid")
def api_bid(req: BidRequest):
    res = place_escrow_bid(req.listing_id, req.bidder_id, req.bid_amount)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/list-item")
def api_list_item(req: ListItemRequest):
    res = list_inventory_item(req.instance_id, req.seller_id, req.realm_id or 0, req.start_price, req.buyout_price)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/temper-item")
def api_temper_item(req: TemperCraftRequest):
    res = temper_and_enchant_item(req.instance_id, req.player_id, req.enchant_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/kiosk-bid")
def api_kiosk_bid(req: KioskBidRequest):
    res = place_kiosk_bid(req.realm_id, req.guild_id, req.bid_gold)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/kiosk-flip")
def api_kiosk_flip():
    res = trigger_weekly_kiosk_flip()
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/bot-tick")
def trigger_autonomous_market_bot():
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "SELECT listing_id, seller_id, current_bid, start_price, buyout_price FROM auction_listings WHERE status = 'ACTIVE';")
        active = rows_to_dicts(cur.fetchall())

        action_roll = random.random()
        candidates = [1001, 1002, 1003, 1004, 1006, 1007, 1009, 1010]

        if len(active) < 9 or action_roll < 0.45:
            # Post a new listing from random template
            templates = [5003, 5004, 5006, 5007, 5008, 5009, 5010, 5011, 5012]
            chosen_item = random.choice(templates)
            chosen_seller = random.choice(candidates)
            execute_sql(cur, "SELECT item_name, base_vendor_value FROM item_templates WHERE item_id = ?;", (chosen_item,))
            t_row = cur.fetchone()
            t_dict = row_to_dict(t_row)
            b_val = t_dict.get("base_vendor_value", 1000)

            markup = random.uniform(1.2, 2.4)
            buyout = int(max(100, b_val * markup))
            start_p = int(buyout * 0.7)
            rid = random.randint(1, 5)
            serial = f"AGORA-BOT-{random.randint(10000, 99999)}"

            execute_sql(
                cur,
                "INSERT INTO inventory_items (item_id, owner_id, mint_serial, temper_tier, bonus_power, stack_size, is_escrowed) VALUES (?, ?, ?, 0, 0, 1, 1);",
                (chosen_item, chosen_seller, serial),
            )
            inst_id = getattr(cur, "lastrowid", None)
            if inst_id is None:
                execute_sql(cur, "SELECT instance_id FROM inventory_items WHERE mint_serial = ?;", (serial,))
                row = cur.fetchone()
                inst_id = row["instance_id"] if hasattr(row, "keys") else row[0]

            res = list_inventory_item(inst_id, chosen_seller, rid, start_p, buyout)
            return {"action": "NEW_LISTING", "detail": res.get("message", "Created bot listing")}

        elif active:
            target = random.choice(active)
            potential_buyers = [b for b in candidates if b != target["seller_id"]]
            if not potential_buyers:
                return {"action": "IDLE", "detail": "No eligible buyers."}
            buyer = random.choice(potential_buyers)

            if target["buyout_price"] and (random.random() < 0.40):
                res = execute_pessimistic_buyout(target["listing_id"], buyer)
                return {"action": "BUYOUT", "detail": res.get("message", "Executed buyout")}
            else:
                curr_bid = target["current_bid"] if target["current_bid"] > 0 else target["start_price"]
                new_bid = int(curr_bid * 1.08) + 50
                res = place_escrow_bid(target["listing_id"], buyer, new_bid)
                return {"action": "BID", "detail": res.get("message", "Placed bid")}

        return {"action": "IDLE", "detail": "Market equilibrium stable."}


@router.post("/api/blacksmith/repair")
def api_repair_equipment(
    req: RepairRequest,
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    pid = resolve_effective_player_id(req.player_id, auth_pid)
    res = repair_player_equipment(player_id=pid, instance_id=req.instance_id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/combat/simulate-wear")
def api_simulate_wear(
    req: SimulateWearRequest,
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    pid = resolve_effective_player_id(req.player_id, auth_pid)
    return degrade_equipment_durability(player_id=pid, amount=req.wear_amount)


@router.post("/api/trade/p2p")
def api_p2p_trade(
    req: P2PTradeRequest,
    auth_pid: Optional[int] = Depends(get_current_player_id),
):
    # If authenticated, ensure initiating party matches
    pid_a = resolve_effective_player_id(req.player_a_id, auth_pid)
    res = execute_p2p_trade(
        player_a_id=pid_a,
        player_b_id=req.player_b_id,
        gold_a=req.gold_a,
        gold_b=req.gold_b,
        instance_a_id=req.instance_a_id,
        instance_b_id=req.instance_b_id,
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res


@router.post("/api/kiosk/sweep-expired")
def api_sweep_expired():
    return sweep_expired_listings()
