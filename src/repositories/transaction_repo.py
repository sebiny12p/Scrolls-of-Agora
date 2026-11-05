"""
Transactional Repository for Scrolls of Agora.
Implements ACID-compliant multi-table database transactions:
  1. Pessimistic Buyout with Zero AB-BA Deadlock Guarantee
  2. Escrow Bid Locking & Automatic Outbid Refunds
  3. Arcane Forge Crafting (Multi-Table Inventory, Wallets & Enchantment Binding)
  4. Weekly Sealed-Bid Kiosk Auction Settlement & Loser Refunds
"""

import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from src.database import (
    get_db_cursor,
    execute_sql,
    is_postgres,
    PG_POOL,
    row_to_dict,
    rows_to_dicts,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def execute_pessimistic_buyout(listing_id: int, buyer_id: int) -> Dict[str, Any]:
    """
    Executes an atomic buyout transaction with exclusive row-level locking.
    Prevents item cloning and race-condition double spending.
    """
    t0 = time.perf_counter()
    if is_postgres():
        return _execute_postgres_buyout(listing_id, buyer_id, t0)
    else:
        return _execute_sqlite_buyout(listing_id, buyer_id, t0)


def _execute_sqlite_buyout(listing_id: int, buyer_id: int, t0: float) -> Dict[str, Any]:
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, """
            SELECT l.*, r.tax_rate_bps, r.realm_name, r.controlling_guild_id, ii.mint_serial, ii.item_id, it.item_name
            FROM auction_listings l
            JOIN realms r ON r.realm_id = l.realm_id
            JOIN inventory_items ii ON ii.instance_id = l.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            WHERE l.listing_id = ?;
        """, (listing_id,))
        listing = cur.fetchone()

        if not listing:
            return {"success": False, "code": "ERR_NOT_FOUND", "message": "Listing does not exist."}

        if listing["status"] != "ACTIVE":
            return {
                "success": False,
                "code": "ERR_ALREADY_CLOSED",
                "message": f"Lock serialized: Listing #{listing_id} already {listing['status']}.",
            }

        if listing["buyout_price"] is None:
            return {"success": False, "code": "ERR_NO_BUYOUT", "message": "Listing is bid-only."}

        if listing["seller_id"] == buyer_id:
            return {"success": False, "code": "ERR_SELF_TRADE", "message": "Cannot buy your own listing."}

        execute_sql(cur, "SELECT gold_balance, is_banned FROM players WHERE player_id = ?;", (buyer_id,))
        buyer = cur.fetchone()
        if not buyer or buyer["is_banned"]:
            return {"success": False, "code": "ERR_BANNED", "message": "Account is banned by the Inquisitor."}
        if buyer["gold_balance"] < listing["buyout_price"]:
            return {"success": False, "code": "ERR_INSUFFICIENT_GOLD", "message": "Insufficient liquid gold."}

        # Step 4: Refund Escrow to Previous Outbid Player
        if listing["high_bidder_id"] is not None and listing["current_bid"] > 0:
            execute_sql(cur, """
                UPDATE players
                SET escrow_gold = escrow_gold - ?,
                    gold_balance = gold_balance + ?
                WHERE player_id = ?;
            """, (listing["current_bid"], listing["current_bid"], listing["high_bidder_id"]))

        # Step 5: Compute Kiosk Cut & Guild Dividend
        gross = int(listing["buyout_price"])
        tax = (gross * int(listing["tax_rate_bps"])) // 10000
        net_payout = gross - tax
        guild_dividend = tax // 2

        if listing["controlling_guild_id"] and guild_dividend > 0:
            execute_sql(
                cur,
                "UPDATE trade_guilds SET treasury_gold = treasury_gold + ?, tax_dividend_earned = tax_dividend_earned + ? WHERE guild_id = ?;",
                (guild_dividend, guild_dividend, listing["controlling_guild_id"]),
            )

        execute_sql(cur, "UPDATE players SET gold_balance = gold_balance - ? WHERE player_id = ?;", (gross, buyer_id))
        execute_sql(cur, "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;", (net_payout, listing["seller_id"]))

        execute_sql(
            cur,
            "UPDATE inventory_items SET owner_id = ?, is_escrowed = 0 WHERE instance_id = ?;",
            (buyer_id, listing["instance_id"]),
        )

        execute_sql(
            cur,
            "UPDATE auction_listings SET status = 'SOLD', high_bidder_id = ?, current_bid = ? WHERE listing_id = ?;",
            (buyer_id, gross, listing_id),
        )

        now_str = utc_now().strftime("%Y-%m-%d %H:%M:%S")
        execute_sql(cur, """
            INSERT INTO ledger_transactions (
                listing_id, instance_id, seller_id, buyer_id,
                gross_price, market_tax_burned, seller_net_payout, settlement_type, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'INSTANT_BUYOUT', ?);
        """, (listing_id, listing["instance_id"], listing["seller_id"], buyer_id, gross, tax, net_payout, now_str))

        tx_id = getattr(cur, "lastrowid", None)
        lat_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "success": True,
            "code": "SETTLED",
            "tx_id": tx_id,
            "gross_price": gross,
            "tax_burned": tax,
            "seller_payout": net_payout,
            "guild_dividend": guild_dividend,
            "mint_serial": listing["mint_serial"],
            "item_name": listing["item_name"],
            "latency_ms": lat_ms,
            "message": f"ACID Buyout Settled: Acquired [{listing['item_name']}] for {gross:,}g ({tax:,}g burned in taxes).",
        }


def _execute_postgres_buyout(listing_id: int, buyer_id: int, t0: float) -> Dict[str, Any]:
    with PG_POOL.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT * FROM execute_atomic_buyout(%s, %s);", (listing_id, buyer_id))
                    res = cur.fetchone()
                    lat_ms = round((time.perf_counter() - t0) * 1000, 2)
                    return {
                        "success": res["success"],
                        "code": res["code"],
                        "tx_id": res["tx_id"],
                        "gross_price": res["gross_paid"],
                        "tax_burned": res["tax_burned"],
                        "seller_payout": res["seller_payout"],
                        "latency_ms": lat_ms,
                        "message": res["message"],
                    }
                except Exception as e:
                    return {"success": False, "code": "ERR_POSTGRES", "message": str(e)}


def place_escrow_bid(listing_id: int, bidder_id: int, bid_amount: int) -> Dict[str, Any]:
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "SELECT * FROM auction_listings WHERE listing_id = ?;", (listing_id,))
        listing = cur.fetchone()
        if not listing or listing["status"] != "ACTIVE":
            return {"success": False, "message": "Listing is no longer active."}

        if listing["seller_id"] == bidder_id:
            return {"success": False, "message": "Seller cannot bid on own item."}

        min_req = listing["start_price"] if listing["current_bid"] == 0 else int(listing["current_bid"] * 1.05) + 1
        if bid_amount < min_req:
            return {"success": False, "message": f"Minimum required bid is {min_req:,}g (+5% increment)."}

        if listing["buyout_price"] and bid_amount >= listing["buyout_price"]:
            return execute_pessimistic_buyout(listing_id, bidder_id)

        execute_sql(cur, "SELECT gold_balance FROM players WHERE player_id = ?;", (bidder_id,))
        bidder = cur.fetchone()
        if not bidder or bidder["gold_balance"] < bid_amount:
            return {"success": False, "message": "Insufficient liquid gold for escrow lock."}

        # Refund previous bidder
        if listing["high_bidder_id"] is not None and listing["current_bid"] > 0:
            execute_sql(
                cur,
                "UPDATE players SET escrow_gold = escrow_gold - ?, gold_balance = gold_balance + ? WHERE player_id = ?;",
                (listing["current_bid"], listing["current_bid"], listing["high_bidder_id"]),
            )

        execute_sql(
            cur,
            "UPDATE players SET gold_balance = gold_balance - ?, escrow_gold = escrow_gold + ? WHERE player_id = ?;",
            (bid_amount, bid_amount, bidder_id),
        )

        execute_sql(
            cur,
            "UPDATE auction_listings SET current_bid = ?, high_bidder_id = ? WHERE listing_id = ?;",
            (bid_amount, bidder_id, listing_id),
        )
        execute_sql(
            cur,
            "INSERT INTO auction_bids (listing_id, bidder_id, bid_amount) VALUES (?, ?, ?);",
            (listing_id, bidder_id, bid_amount),
        )
        return {
            "success": True,
            "message": f"Escrow bid of {bid_amount:,}g locked on Listing #{listing_id} (prior bidder refunded).",
        }


def list_inventory_item(instance_id: int, seller_id: int, realm_id: int, start_price: int, buyout_price: int) -> Dict[str, Any]:
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, """
            SELECT ii.*, it.item_name, p.realm_id AS player_realm_id
            FROM inventory_items ii
            JOIN item_templates it ON it.item_id = ii.item_id
            JOIN players p ON p.player_id = ii.owner_id
            WHERE ii.instance_id = ? AND ii.owner_id = ?;
        """, (instance_id, seller_id))
        item = cur.fetchone()
        if not item:
            return {"success": False, "message": "Item not found in your character's inventory."}
        if item["is_escrowed"]:
            return {"success": False, "message": "Item is already escrowed on a City Kiosk."}
        if start_price <= 0 or buyout_price < start_price:
            return {"success": False, "message": "Buyout price must be >= start price (> 0g)."}

        target_realm = realm_id if realm_id and realm_id > 0 else item["player_realm_id"]
        execute_sql(cur, "SELECT realm_name FROM realms WHERE realm_id = ?;", (target_realm,))
        r_row = cur.fetchone()
        r_name = r_row["realm_name"] if r_row else "Mournhold"

        execute_sql(cur, "UPDATE inventory_items SET is_escrowed = 1 WHERE instance_id = ?;", (instance_id,))
        now_str = utc_now().strftime("%Y-%m-%d %H:%M:%S")
        exp_str = (utc_now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")

        execute_sql(cur, """
            INSERT INTO auction_listings (
                instance_id, seller_id, realm_id, listing_type,
                start_price, buyout_price, current_bid, status, listed_at, expires_at
            ) VALUES (?, ?, ?, 'AUCTION', ?, ?, 0, 'ACTIVE', ?, ?);
        """, (instance_id, seller_id, target_realm, start_price, buyout_price, now_str, exp_str))
        lid = getattr(cur, "lastrowid", None)
        return {
            "success": True,
            "listing_id": lid,
            "message": f"Listed [{item['item_name']}] ({item['mint_serial']}) at {r_name} Kiosk for {buyout_price:,}g.",
        }


def temper_and_enchant_item(instance_id: int, player_id: int, enchant_id: int = 1) -> Dict[str, Any]:
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, """
            SELECT ii.*, it.item_name, it.category, it.rarity, it.base_vendor_value
            FROM inventory_items ii
            JOIN item_templates it ON it.item_id = ii.item_id
            WHERE ii.instance_id = ? AND ii.owner_id = ?;
        """, (instance_id, player_id))
        gear = cur.fetchone()
        if not gear:
            return {"success": False, "message": "Select an unlocked Equipment or Artifact item from your bag."}
        if gear["is_escrowed"]:
            return {"success": False, "message": "Cannot temper an item while it is escrowed on a Kiosk."}
        if gear["category"] not in ("Weapon", "Armor", "Artifact"):
            return {"success": False, "message": "Only Weapons, Armor, and Artifacts can be tempered at the Arcane Forge."}
        if gear["temper_tier"] >= 5:
            return {"success": False, "message": "Item has already reached Maximum Mythic Temper Tier (+5)."}

        forge_fee = 3500
        execute_sql(cur, "SELECT gold_balance FROM players WHERE player_id = ?;", (player_id,))
        p_row = cur.fetchone()
        if not p_row or p_row["gold_balance"] < forge_fee:
            return {"success": False, "message": f"Requires {forge_fee:,}g gold for Arcane Forge tempering."}

        execute_sql(cur, """
            SELECT instance_id, stack_size, item_id FROM inventory_items
            WHERE owner_id = ? AND item_id IN (5011, 5012) AND is_escrowed = 0 AND stack_size >= 2
            LIMIT 1;
        """, (player_id,))
        reagent = cur.fetchone()
        reagent_msg = "3,500g Forge Gold"
        if reagent:
            if reagent["stack_size"] > 2:
                execute_sql(cur, "UPDATE inventory_items SET stack_size = stack_size - 2 WHERE instance_id = ?;", (reagent["instance_id"],))
            else:
                execute_sql(cur, "DELETE FROM inventory_items WHERE instance_id = ?;", (reagent["instance_id"],))
            reagent_msg = "2x Dreugh Wax/Resin + 3,500g"

        execute_sql(cur, "UPDATE players SET gold_balance = gold_balance - ? WHERE player_id = ?;", (forge_fee, player_id))

        new_tier = gear["temper_tier"] + 1
        power_boost = 95 * new_tier
        new_serial = f"AGORA-TMPR{new_tier}-{uuid.uuid4().hex[:6].upper()}"

        execute_sql(cur, """
            UPDATE inventory_items
            SET temper_tier = ?, bonus_power = bonus_power + ?, mint_serial = ?
            WHERE instance_id = ?;
        """, (new_tier, power_boost, new_serial, instance_id))

        execute_sql(
            cur,
            "INSERT OR IGNORE INTO item_instance_enchantments (instance_id, enchant_id) VALUES (?, ?);",
            (instance_id, enchant_id),
        )
        execute_sql(cur, "SELECT enchant_name FROM enchantments WHERE enchant_id = ?;", (enchant_id,))
        ench = cur.fetchone()
        ench_name = ench["enchant_name"] if ench else "Arcane Glyph"

        return {
            "success": True,
            "message": f"Tempered [{gear['item_name']}] to Tier +{new_tier} (+{power_boost} Power, bound {ench_name}) using {reagent_msg}!",
        }


def place_kiosk_bid(realm_id: int, guild_id: int, bid_gold: int) -> Dict[str, Any]:
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "SELECT * FROM trade_guilds WHERE guild_id = ?;", (guild_id,))
        guild = cur.fetchone()
        if not guild or guild["treasury_gold"] < bid_gold:
            return {"success": False, "message": "Guild treasury lacks sufficient gold for this sealed bid."}

        execute_sql(cur, "SELECT realm_name FROM realms WHERE realm_id = ?;", (realm_id,))
        realm = cur.fetchone()
        if not realm:
            return {"success": False, "message": "Trading hub not found."}

        execute_sql(cur, "UPDATE trade_guilds SET treasury_gold = treasury_gold - ? WHERE guild_id = ?;", (bid_gold, guild_id))
        execute_sql(
            cur,
            "INSERT INTO kiosk_bids (realm_id, guild_id, bid_gold, status) VALUES (?, ?, ?, 'SEALED');",
            (realm_id, guild_id, bid_gold),
        )
        return {
            "success": True,
            "message": f"Sealed blind bid of {bid_gold:,}g submitted by [{guild['guild_name']}] for {realm['realm_name']} Kiosk!",
        }


def trigger_weekly_kiosk_flip() -> Dict[str, Any]:
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "SELECT realm_id, realm_name FROM realms;")
        all_realms = rows_to_dicts(cur.fetchall())
        flips = []

        for r in all_realms:
            rid = r["realm_id"]
            # Ensure competitive sealed bid exists per hub before resolving
            execute_sql(cur, "SELECT COUNT(*) FROM kiosk_bids WHERE realm_id = ? AND status = 'SEALED';", (rid,))
            count_sealed = cur.fetchone()[0]
            if count_sealed == 0:
                ai_guild = random.choice([1, 2, 3, 4, 5])
                ai_bid = random.randint(450000, 1250000)
                execute_sql(
                    cur,
                    "INSERT INTO kiosk_bids (realm_id, guild_id, bid_gold, status) VALUES (?, ?, ?, 'SEALED');",
                    (rid, ai_guild, ai_bid),
                )

            execute_sql(cur, """
                SELECT kb.kiosk_bid_id, kb.guild_id, kb.bid_gold, tg.guild_name
                FROM kiosk_bids kb
                JOIN trade_guilds tg ON tg.guild_id = kb.guild_id
                WHERE kb.realm_id = ? AND kb.status = 'SEALED'
                ORDER BY kb.bid_gold DESC, kb.kiosk_bid_id ASC;
            """, (rid,))
            bids = rows_to_dicts(cur.fetchall())

            if not bids:
                continue

            winner = bids[0]
            execute_sql(cur, "UPDATE kiosk_bids SET status = 'WON' WHERE kiosk_bid_id = ?;", (winner["kiosk_bid_id"],))
            execute_sql(cur, "UPDATE realms SET controlling_guild_id = ? WHERE realm_id = ?;", (winner["guild_id"], rid))

            refunded_count = 0
            for loser in bids[1:]:
                execute_sql(cur, "UPDATE kiosk_bids SET status = 'REFUNDED' WHERE kiosk_bid_id = ?;", (loser["kiosk_bid_id"],))
                execute_sql(cur, "UPDATE trade_guilds SET treasury_gold = treasury_gold + ? WHERE guild_id = ?;", (loser["bid_gold"], loser["guild_id"]))
                refunded_count += 1

            flips.append({
                "realm": r["realm_name"],
                "winner": winner["guild_name"],
                "winning_bid": winner["bid_gold"],
                "refunded_rivals": refunded_count,
            })

        return {
            "success": True,
            "flips": flips,
            "message": f"Weekly Kiosk Flip Complete: Resolved leases across {len(flips)} hubs & refunded losing syndicates.",
        }
