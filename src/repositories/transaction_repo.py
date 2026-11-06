"""
Transactional Repository for Scrolls of Agora.
Implements ACID-compliant multi-table database transactions:
  1. Pessimistic Buyout with Zero AB-BA Deadlock Guarantee
  2. Escrow Bid Locking & Automatic Outbid Refunds
  3. Arcane Forge Crafting (Multi-Table Inventory, Wallets & Enchantment Binding)
  4. Weekly Sealed-Bid Kiosk Auction Settlement & Loser Refunds
  5. True Double-Entry General Ledger Journal Invariance
"""

import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from src.config import (
    FORGE_FEE_GOLD,
    FORGE_MAX_TEMPER_TIER,
    FORGE_POWER_BOOST_PER_TIER,
    FORGE_REAGENT_ITEM_IDS,
    FORGE_REAGENT_QTY_REQUIRED,
    MIN_ESCROW_BID_INCREMENT_PCT,
    SYSTEM_SINK_ACCOUNT,
    DEFAULT_MAX_BAG_SLOTS,
    REPAIR_COST_PER_DURABILITY,
)
from src.database import (
    get_db_cursor,
    execute_sql,
    execute_insert,
    is_postgres,
    PG_POOL,
    row_to_dict,
    rows_to_dicts,
    record_journal_entries,
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

        # Step 4: Compute Kiosk Cut & Guild Dividend
        gross = int(listing["buyout_price"])
        tax = (gross * int(listing["tax_rate_bps"])) // 10000
        net_payout = gross - tax
        guild_dividend = tax // 2 if listing["controlling_guild_id"] else 0
        tax_burned = tax - guild_dividend

        # Step 5: Deterministic Wallet Balance Updates (ORDER BY player_id ASC)
        participants = sorted([
            (buyer_id, -gross),
            (listing["seller_id"], net_payout)
        ], key=lambda x: x[0])

        for pid, delta in participants:
            execute_sql(cur, "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;", (delta, pid))

        # Refund Escrow to Previous Outbid Player if present
        if listing["high_bidder_id"] is not None and listing["current_bid"] > 0:
            execute_sql(cur, """
                UPDATE players
                SET escrow_gold = escrow_gold - ?,
                    gold_balance = gold_balance + ?
                WHERE player_id = ?;
            """, (listing["current_bid"], listing["current_bid"], listing["high_bidder_id"]))

        # Credit Guild Dividend if kiosk is controlled
        if listing["controlling_guild_id"] and guild_dividend > 0:
            execute_sql(
                cur,
                "UPDATE trade_guilds SET treasury_gold = treasury_gold + ?, tax_dividend_earned = tax_dividend_earned + ? WHERE guild_id = ?;",
                (guild_dividend, guild_dividend, listing["controlling_guild_id"]),
            )

        # Step 6: Transfer Item Ownership & Close Listing (With Bag Slot Check & Mailbox Overflow)
        from src.repositories.mail_repo import get_player_bag_count, deliver_overflow_or_system_mail
        bag_count = get_player_bag_count(cur, buyer_id)
        overflow_to_mail = False

        if bag_count >= DEFAULT_MAX_BAG_SLOTS:
            overflow_to_mail = True
            execute_sql(
                cur,
                "UPDATE inventory_items SET owner_id = ?, is_escrowed = 1 WHERE instance_id = ?;",
                (buyer_id, listing["instance_id"]),
            )
            deliver_overflow_or_system_mail(
                cur,
                recipient_id=buyer_id,
                subject=f"Kiosk Buyout: {listing['item_name']} (Bag Full)",
                body=f"Your inventory was full ({bag_count}/{DEFAULT_MAX_BAG_SLOTS} slots). The courier has delivered your purchased item.",
                attached_instance_id=listing["instance_id"],
            )
        else:
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

        # Step 7: Record Settlement Receipt
        now_str = utc_now().strftime("%Y-%m-%d %H:%M:%S")
        tx_id = execute_insert(cur, """
            INSERT INTO ledger_transactions (
                listing_id, instance_id, seller_id, buyer_id,
                gross_price, market_tax_burned, seller_net_payout, settlement_type, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'INSTANT_BUYOUT', ?);
        """, (listing_id, listing["instance_id"], listing["seller_id"], buyer_id, gross, tax, net_payout, now_str), pkey_column="tx_id")

        # Step 8: Double-Entry General Ledger Journal (Strict Sum(amount) == 0)
        tx_group_id = f"TX-BUYOUT-{listing_id}-{uuid.uuid4().hex[:6]}"
        journal_entries = [
            ("PLAYER_LIQUID", str(buyer_id), -gross, f"Buyout debit for Listing #{listing_id}"),
            ("PLAYER_LIQUID", str(listing["seller_id"]), net_payout, f"Seller net payout for Listing #{listing_id}"),
        ]
        if guild_dividend > 0:
            journal_entries.append(
                ("GUILD_TREASURY", str(listing["controlling_guild_id"]), guild_dividend, f"Kiosk dividend for Listing #{listing_id}")
            )
        if tax_burned > 0:
            journal_entries.append(
                ("SYSTEM_SINK", SYSTEM_SINK_ACCOUNT, tax_burned, f"Kiosk tax burn for Listing #{listing_id}")
            )

        record_journal_entries(cur, tx_group_id, "BUYOUT", journal_entries)

        from src.services.broadcaster import broadcaster
        broadcaster.broadcast_sync("BUYOUT", {
            "listing_id": listing_id,
            "buyer_id": buyer_id,
            "gross": gross,
            "item_name": listing["item_name"],
            "overflow_to_mail": overflow_to_mail,
        })

        lat_ms = round((time.perf_counter() - t0) * 1000, 2)
        msg_suffix = " (Transferred to inventory bag)" if not overflow_to_mail else " (Bag full: parcel delivered to Mailbox)"
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
            "overflow_to_mail": overflow_to_mail,
            "latency_ms": lat_ms,
            "message": f"ACID Buyout Settled: Acquired [{listing['item_name']}] for {gross:,}g ({tax:,}g burned/split in taxes){msg_suffix}.",
        }


def _execute_postgres_buyout(listing_id: int, buyer_id: int, t0: float) -> Dict[str, Any]:
    with PG_POOL.connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                try:
                    cur.execute("SELECT * FROM execute_atomic_buyout(%s, %s);", (listing_id, buyer_id))
                    res = cur.fetchone()
                    lat_ms = round((time.perf_counter() - t0) * 1000, 2)

                    # Also record double-entry journal if successful
                    if res["success"]:
                        gross = int(res["gross_paid"])
                        tax = int(res["tax_burned"])
                        net_payout = int(res["seller_payout"])
                        guild_dividend = tax // 2
                        tax_burned = tax - guild_dividend

                        tx_group_id = f"TX-BUYOUT-PG-{listing_id}-{uuid.uuid4().hex[:6]}"
                        journal_entries = [
                            ("PLAYER_LIQUID", str(buyer_id), -gross, f"Buyout debit for Listing #{listing_id}"),
                            ("PLAYER_LIQUID", str(res.get("seller_id", "SELLER")), net_payout, f"Seller payout for #{listing_id}"),
                        ]
                        if guild_dividend > 0:
                            journal_entries.append(("GUILD_TREASURY", "GUILD", guild_dividend, "Kiosk dividend"))
                        if tax_burned > 0:
                            journal_entries.append(("SYSTEM_SINK", SYSTEM_SINK_ACCOUNT, tax_burned, "Tax burn"))

                        record_journal_entries(cur, tx_group_id, "BUYOUT", journal_entries)

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

        min_increment = 1.0 + MIN_ESCROW_BID_INCREMENT_PCT
        min_req = listing["start_price"] if listing["current_bid"] == 0 else int(listing["current_bid"] * min_increment) + 1
        if bid_amount < min_req:
            return {"success": False, "message": f"Minimum required bid is {min_req:,}g (+{int(MIN_ESCROW_BID_INCREMENT_PCT*100)}% increment)."}

        if listing["buyout_price"] and bid_amount >= listing["buyout_price"]:
            return execute_pessimistic_buyout(listing_id, bidder_id)

        execute_sql(cur, "SELECT gold_balance FROM players WHERE player_id = ?;", (bidder_id,))
        bidder = cur.fetchone()
        if not bidder or bidder["gold_balance"] < bid_amount:
            return {"success": False, "message": "Insufficient liquid gold for escrow lock."}

        # Deterministic Lock Ordering on Participant Wallets
        prior_bidder_id = listing["high_bidder_id"]
        prior_bid = listing["current_bid"]

        if prior_bidder_id is not None and prior_bid > 0:
            # Ascending player lock ordering
            for pid in sorted([bidder_id, prior_bidder_id]):
                if pid == prior_bidder_id:
                    # Refund previous bidder
                    execute_sql(
                        cur,
                        "UPDATE players SET escrow_gold = escrow_gold - ?, gold_balance = gold_balance + ? WHERE player_id = ?;",
                        (prior_bid, prior_bid, prior_bidder_id),
                    )
                else:
                    # Lock new bidder's gold into escrow
                    execute_sql(
                        cur,
                        "UPDATE players SET gold_balance = gold_balance - ?, escrow_gold = escrow_gold + ? WHERE player_id = ?;",
                        (bid_amount, bid_amount, bidder_id),
                    )
            # Record balancing journal entries for the refund
            tx_group_refund = f"TX-ESCREF-{listing_id}-{uuid.uuid4().hex[:6]}"
            record_journal_entries(cur, tx_group_refund, "ESCROW_REFUND", [
                ("PLAYER_ESCROW", str(prior_bidder_id), -prior_bid, f"Escrow release for outbid Listing #{listing_id}"),
                ("PLAYER_LIQUID", str(prior_bidder_id), prior_bid, f"Liquid gold refund for outbid Listing #{listing_id}"),
            ])
        else:
            execute_sql(
                cur,
                "UPDATE players SET gold_balance = gold_balance - ?, escrow_gold = escrow_gold + ? WHERE player_id = ?;",
                (bid_amount, bid_amount, bidder_id),
            )

        # Record balancing journal entries for the new bid lock
        tx_group_bid = f"TX-ESCLOCK-{listing_id}-{uuid.uuid4().hex[:6]}"
        record_journal_entries(cur, tx_group_bid, "ESCROW_LOCK", [
            ("PLAYER_LIQUID", str(bidder_id), -bid_amount, f"Liquid debit for Escrow bid on #{listing_id}"),
            ("PLAYER_ESCROW", str(bidder_id), bid_amount, f"Escrow lock credit for bid on #{listing_id}"),
        ])

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

        lid = execute_insert(cur, """
            INSERT INTO auction_listings (
                instance_id, seller_id, realm_id, listing_type,
                start_price, buyout_price, current_bid, status, listed_at, expires_at
            ) VALUES (?, ?, ?, 'AUCTION', ?, ?, 0, 'ACTIVE', ?, ?);
        """, (instance_id, seller_id, target_realm, start_price, buyout_price, now_str, exp_str), pkey_column="listing_id")
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
        if gear["temper_tier"] >= FORGE_MAX_TEMPER_TIER:
            return {"success": False, "message": f"Item has already reached Maximum Mythic Temper Tier (+{FORGE_MAX_TEMPER_TIER})."}

        execute_sql(cur, "SELECT gold_balance FROM players WHERE player_id = ?;", (player_id,))
        p_row = cur.fetchone()
        if not p_row or p_row["gold_balance"] < FORGE_FEE_GOLD:
            return {"success": False, "message": f"Requires {FORGE_FEE_GOLD:,}g gold for Arcane Forge tempering."}

        # Check for crafting reagents
        reagent_placeholders = ",".join("?" for _ in FORGE_REAGENT_ITEM_IDS)
        execute_sql(cur, f"""
            SELECT instance_id, stack_size, item_id FROM inventory_items
            WHERE owner_id = ? AND item_id IN ({reagent_placeholders}) AND is_escrowed = 0 AND stack_size >= ?
            LIMIT 1;
        """, (player_id, *FORGE_REAGENT_ITEM_IDS, FORGE_REAGENT_QTY_REQUIRED))
        reagent = cur.fetchone()
        reagent_msg = f"{FORGE_FEE_GOLD:,}g Forge Gold"
        if reagent:
            if reagent["stack_size"] > FORGE_REAGENT_QTY_REQUIRED:
                execute_sql(
                    cur,
                    "UPDATE inventory_items SET stack_size = stack_size - ? WHERE instance_id = ?;",
                    (FORGE_REAGENT_QTY_REQUIRED, reagent["instance_id"]),
                )
            else:
                execute_sql(cur, "DELETE FROM inventory_items WHERE instance_id = ?;", (reagent["instance_id"],))
            reagent_msg = f"{FORGE_REAGENT_QTY_REQUIRED}x Dreugh Wax/Resin + {FORGE_FEE_GOLD:,}g"

        execute_sql(cur, "UPDATE players SET gold_balance = gold_balance - ? WHERE player_id = ?;", (FORGE_FEE_GOLD, player_id))

        # Record balancing journal entry: Player liquid debit, System sink credit
        tx_group_forge = f"TX-FORGE-{instance_id}-{uuid.uuid4().hex[:6]}"
        record_journal_entries(cur, tx_group_forge, "FORGE_FEE", [
            ("PLAYER_LIQUID", str(player_id), -FORGE_FEE_GOLD, f"Arcane Forge fee for tempering Item #{instance_id}"),
            ("SYSTEM_SINK", SYSTEM_SINK_ACCOUNT, FORGE_FEE_GOLD, f"Arcane Forge sink fee for Item #{instance_id}"),
        ])

        new_tier = gear["temper_tier"] + 1
        power_boost = FORGE_POWER_BOOST_PER_TIER * new_tier
        new_serial = f"AGORA-TMPR{new_tier}-{uuid.uuid4().hex[:6].upper()}"

        execute_sql(cur, """
            UPDATE inventory_items
            SET temper_tier = ?, bonus_power = bonus_power + ?, mint_serial = ?
            WHERE instance_id = ?;
        """, (new_tier, power_boost, new_serial, instance_id))

        # Standard SQL ON CONFLICT syntax natively supported in SQLite 3.24+ and PostgreSQL
        execute_sql(
            cur,
            """
            INSERT INTO item_instance_enchantments (instance_id, enchant_id)
            VALUES (?, ?)
            ON CONFLICT (instance_id, enchant_id) DO NOTHING;
            """,
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

        # Record balancing journal entry: Guild treasury debit, System escrow credit
        tx_group_kbid = f"TX-KBID-{realm_id}-{guild_id}-{uuid.uuid4().hex[:6]}"
        record_journal_entries(cur, tx_group_kbid, "KIOSK_BID", [
            ("GUILD_TREASURY", str(guild_id), -bid_gold, f"Sealed kiosk bid for {realm['realm_name']}"),
            ("SYSTEM_SINK", f"ESCROW_KIOSK_{realm_id}", bid_gold, f"Escrow lock for {realm['realm_name']} kiosk bid"),
        ])

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

            # Record winning lease fee journal entry (transfers from escrow to system sink)
            tx_group_win = f"TX-KWIN-{rid}-{winner['guild_id']}-{uuid.uuid4().hex[:6]}"
            record_journal_entries(cur, tx_group_win, "KIOSK_WIN_FEE", [
                ("SYSTEM_SINK", f"ESCROW_KIOSK_{rid}", -winner["bid_gold"], f"Kiosk lease escrow release for {r['realm_name']}"),
                ("SYSTEM_SINK", SYSTEM_SINK_ACCOUNT, winner["bid_gold"], f"Kiosk lease fee settled for {r['realm_name']}"),
            ])

            refunded_count = 0
            for loser in bids[1:]:
                execute_sql(cur, "UPDATE kiosk_bids SET status = 'REFUNDED' WHERE kiosk_bid_id = ?;", (loser["kiosk_bid_id"],))
                execute_sql(cur, "UPDATE trade_guilds SET treasury_gold = treasury_gold + ? WHERE guild_id = ?;", (loser["bid_gold"], loser["guild_id"]))
                refunded_count += 1

                # Record refund journal entry
                tx_group_ref = f"TX-KREF-{loser['kiosk_bid_id']}-{uuid.uuid4().hex[:6]}"
                record_journal_entries(cur, tx_group_ref, "KIOSK_REFUND", [
                    ("SYSTEM_SINK", f"ESCROW_KIOSK_{rid}", -loser["bid_gold"], f"Losing kiosk bid escrow refund for {r['realm_name']}"),
                    ("GUILD_TREASURY", str(loser["guild_id"]), loser["bid_gold"], f"Losing kiosk bid refund to treasury"),
                ])

            flips.append({
                "realm": r["realm_name"],
                "winner": winner["guild_name"],
                "winning_bid": winner["bid_gold"],
                "refunded_rivals": refunded_count,
            })

        from src.services.broadcaster import broadcaster
        broadcaster.broadcast_sync("KIOSK_FLIP", {"flips": flips})

        return {
            "success": True,
            "flips": flips,
            "message": f"Weekly Kiosk Flip Complete: Resolved leases across {len(flips)} hubs & refunded losing syndicates.",
        }


def repair_player_equipment(player_id: int, instance_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Repairs damaged equipment instances at the Blacksmith.
    Restores durability to 100% and transfers gold fee to SYSTEM_SINK.
    Enforces balanced double-entry general ledger invariance.
    """
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "SELECT player_id, username, gold_balance, is_banned FROM players WHERE player_id = ?;", (player_id,))
        player = cur.fetchone()
        if not player or player["is_banned"]:
            return {"success": False, "code": "ERR_BANNED", "message": "Player invalid or banned."}

        if instance_id is not None:
            execute_sql(cur, """
                SELECT ii.instance_id, ii.current_durability, it.item_name
                FROM inventory_items ii
                JOIN item_templates it ON it.item_id = ii.item_id
                WHERE ii.instance_id = ? AND ii.owner_id = ? AND ii.is_escrowed = 0;
            """, (instance_id, player_id))
            items_to_repair = rows_to_dicts(cur.fetchall())
        else:
            execute_sql(cur, """
                SELECT ii.instance_id, ii.current_durability, it.item_name
                FROM inventory_items ii
                JOIN item_templates it ON it.item_id = ii.item_id
                WHERE ii.owner_id = ? AND ii.is_escrowed = 0 AND ii.current_durability < 100;
            """, (player_id,))
            items_to_repair = rows_to_dicts(cur.fetchall())

        if not items_to_repair:
            return {"success": False, "code": "ERR_NO_REPAIR_NEEDED", "message": "All equipment is at 100% durability."}

        total_points_lost = sum(100 - item["current_durability"] for item in items_to_repair)
        total_repair_cost = total_points_lost * REPAIR_COST_PER_DURABILITY

        if total_repair_cost <= 0:
            return {"success": False, "code": "ERR_NO_REPAIR_NEEDED", "message": "All equipment is at 100% durability."}

        if player["gold_balance"] < total_repair_cost:
            return {
                "success": False,
                "code": "ERR_INSUFFICIENT_GOLD",
                "message": f"Requires {total_repair_cost:,}g to repair {len(items_to_repair)} item(s) ({total_points_lost} pts lost), but player has {player['gold_balance']:,}g.",
            }

        # Deduct player gold and update item durability
        execute_sql(cur, "UPDATE players SET gold_balance = gold_balance - ? WHERE player_id = ?;", (total_repair_cost, player_id))
        for item in items_to_repair:
            execute_sql(cur, "UPDATE inventory_items SET current_durability = 100 WHERE instance_id = ?;", (item["instance_id"],))

        # Record balanced double-entry journal entry
        tx_repair = f"TX-REPAIR-{uuid.uuid4().hex[:10].upper()}"
        record_journal_entries(
            cur,
            tx_group_id=tx_repair,
            event_type="REPAIR_FEE",
            entries=[
                ("PLAYER_LIQUID", str(player_id), -total_repair_cost, f"Blacksmith repair fee for {len(items_to_repair)} item(s)"),
                ("SYSTEM_SINK", SYSTEM_SINK_ACCOUNT, total_repair_cost, "Blacksmith repair service gold burn"),
            ],
        )

    from src.services.broadcaster import broadcaster
    broadcaster.broadcast_sync("REPAIR_COMPLETE", {"player_id": player_id, "items_repaired": len(items_to_repair), "cost": total_repair_cost})
    return {
        "success": True,
        "items_repaired": len(items_to_repair),
        "durability_restored": total_points_lost,
        "repair_cost": total_repair_cost,
        "message": f"Repaired {len(items_to_repair)} item(s) to 100% durability at Blacksmith for {total_repair_cost:,}g gold.",
    }


def degrade_equipment_durability(player_id: int, amount: int = 15) -> Dict[str, Any]:
    """Simulates dungeon combat wear, degrading equipment durability."""
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, """
            UPDATE inventory_items
            SET current_durability = MAX(0, current_durability - ?)
            WHERE owner_id = ? AND is_escrowed = 0;
        """, (amount, player_id))
        affected = cur.rowcount if hasattr(cur, "rowcount") else 1

    return {
        "success": True,
        "player_id": player_id,
        "degradation_applied": amount,
        "items_affected": affected,
        "message": f"Combat simulation: {affected} item(s) degraded by {amount} durability points.",
    }


def execute_p2p_trade(
    player_a_id: int,
    player_b_id: int,
    gold_a: int = 0,
    gold_b: int = 0,
    instance_a_id: Optional[int] = None,
    instance_b_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes an atomic 2-way peer-to-peer trade between Player A and Player B.
    Enforces deterministic lock hierarchy (ORDER BY player_id ASC) to guarantee zero deadlocks.
    Enforces double-entry ledger balance invariance.
    """
    if player_a_id == player_b_id:
        return {"success": False, "code": "ERR_SELF_TRADE", "message": "Cannot trade with yourself."}

    from src.repositories.mail_repo import get_player_bag_count

    with get_db_cursor(immediate=True) as cur:
        # Deterministic primary key lock ordering
        pids = sorted([player_a_id, player_b_id])
        execute_sql(cur, "SELECT player_id, username, gold_balance, is_banned FROM players WHERE player_id IN (?, ?) ORDER BY player_id ASC;", (pids[0], pids[1]))
        players = {r["player_id"]: r for r in rows_to_dicts(cur.fetchall())}

        p_a = players.get(player_a_id)
        p_b = players.get(player_b_id)
        if not p_a or not p_b or p_a["is_banned"] or p_b["is_banned"]:
            return {"success": False, "code": "ERR_INVALID_PLAYER", "message": "One or both trading parties are invalid or banned."}

        if p_a["gold_balance"] < gold_a:
            return {"success": False, "code": "ERR_INSUFFICIENT_GOLD_A", "message": f"{p_a['username']} has insufficient gold."}
        if p_b["gold_balance"] < gold_b:
            return {"success": False, "code": "ERR_INSUFFICIENT_GOLD_B", "message": f"{p_b['username']} has insufficient gold."}

        # Validate item A
        if instance_a_id is not None:
            execute_sql(cur, "SELECT instance_id, owner_id, is_escrowed FROM inventory_items WHERE instance_id = ?;", (instance_a_id,))
            item_a = cur.fetchone()
            if not item_a or item_a["owner_id"] != player_a_id or item_a["is_escrowed"]:
                return {"success": False, "code": "ERR_INVALID_ITEM_A", "message": f"Item A is not owned by {p_a['username']} or is escrowed."}

        # Validate item B
        if instance_b_id is not None:
            execute_sql(cur, "SELECT instance_id, owner_id, is_escrowed FROM inventory_items WHERE instance_id = ?;", (instance_b_id,))
            item_b = cur.fetchone()
            if not item_b or item_b["owner_id"] != player_b_id or item_b["is_escrowed"]:
                return {"success": False, "code": "ERR_INVALID_ITEM_B", "message": f"Item B is not owned by {p_b['username']} or is escrowed."}

        # Bag slot check
        bag_a = get_player_bag_count(cur, player_a_id)
        bag_b = get_player_bag_count(cur, player_b_id)
        net_slot_change_a = (1 if instance_b_id else 0) - (1 if instance_a_id else 0)
        net_slot_change_b = (1 if instance_a_id else 0) - (1 if instance_b_id else 0)

        if bag_a + net_slot_change_a > DEFAULT_MAX_BAG_SLOTS:
            return {"success": False, "code": "ERR_BAG_FULL_A", "message": f"{p_a['username']}'s bag is full."}
        if bag_b + net_slot_change_b > DEFAULT_MAX_BAG_SLOTS:
            return {"success": False, "code": "ERR_BAG_FULL_B", "message": f"{p_b['username']}'s bag is full."}

        # Execute Gold Swap (ORDER BY player_id ASC)
        net_gold_a = gold_b - gold_a
        net_gold_b = gold_a - gold_b

        for pid, delta in sorted([(player_a_id, net_gold_a), (player_b_id, net_gold_b)], key=lambda x: x[0]):
            execute_sql(cur, "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;", (delta, pid))

        # Execute Item Ownership Swap
        if instance_a_id is not None:
            execute_sql(cur, "UPDATE inventory_items SET owner_id = ?, is_escrowed = 0 WHERE instance_id = ?;", (player_b_id, instance_a_id))
        if instance_b_id is not None:
            execute_sql(cur, "UPDATE inventory_items SET owner_id = ?, is_escrowed = 0 WHERE instance_id = ?;", (player_a_id, instance_b_id))

        # Record balanced double-entry journal if gold was exchanged
        if gold_a != 0 or gold_b != 0:
            tx_trade = f"TX-P2P-{uuid.uuid4().hex[:10].upper()}"
            record_journal_entries(
                cur,
                tx_group_id=tx_trade,
                event_type="P2P_TRADE",
                entries=[
                    ("PLAYER_LIQUID", str(player_a_id), net_gold_a, f"P2P Trade settlement with {p_b['username']}"),
                    ("PLAYER_LIQUID", str(player_b_id), net_gold_b, f"P2P Trade settlement with {p_a['username']}"),
                ],
            )

    from src.services.broadcaster import broadcaster
    broadcaster.broadcast_sync("P2P_TRADE", {"player_a": player_a_id, "player_b": player_b_id})
    return {
        "success": True,
        "message": f"P2P Trade executed atomically between {p_a['username']} and {p_b['username']}.",
    }


def sweep_expired_listings() -> Dict[str, Any]:
    """
    Automated sweeper that finds expired auction listings, marks them EXPIRED,
    refunds any active high bidder escrow, and returns unsold items to sellers via Courier Mail.
    """
    now_str = utc_now().strftime("%Y-%m-%d %H:%M:%S")
    swept = []

    from src.repositories.mail_repo import deliver_overflow_or_system_mail

    with get_db_cursor(immediate=True) as cur:
        execute_sql(
            cur,
            """
            SELECT al.*, it.item_name
            FROM auction_listings al
            JOIN inventory_items ii ON ii.instance_id = al.instance_id
            JOIN item_templates it ON it.item_id = ii.item_id
            WHERE al.status = 'ACTIVE' AND al.expires_at <= ?;
            """,
            (now_str,),
        )
        expired = rows_to_dicts(cur.fetchall())

        for exp in expired:
            lid = exp["listing_id"]
            execute_sql(cur, "UPDATE auction_listings SET status = 'EXPIRED' WHERE listing_id = ?;", (lid,))

            # Refund high bidder escrow if present
            if exp["high_bidder_id"] is not None and exp["current_bid"] > 0:
                refund_amount = int(exp["current_bid"])
                execute_sql(cur, "SELECT escrow_gold FROM players WHERE player_id = ?;", (exp["high_bidder_id"],))
                p_row = cur.fetchone()
                p_escrow = p_row["escrow_gold"] if hasattr(p_row, "keys") else (p_row[0] if p_row else 0)
                actual_refund = min(refund_amount, p_escrow)
                if actual_refund > 0:
                    execute_sql(
                        cur,
                        "UPDATE players SET escrow_gold = escrow_gold - ?, gold_balance = gold_balance + ? WHERE player_id = ?;",
                        (actual_refund, actual_refund, exp["high_bidder_id"]),
                    )
                    tx_ref = f"TX-EXPIRE-REF-{lid}-{uuid.uuid4().hex[:6]}"
                    record_journal_entries(
                        cur,
                        tx_group_id=tx_ref,
                        event_type="ESCROW_REFUND",
                        entries=[
                            ("PLAYER_ESCROW", str(exp["high_bidder_id"]), -actual_refund, f"Expired auction escrow return #{lid}"),
                            ("PLAYER_LIQUID", str(exp["high_bidder_id"]), actual_refund, f"Escrow refund for expired auction #{lid}"),
                        ],
                    )

            # Return unsold item to seller via courier parcel
            deliver_overflow_or_system_mail(
                cur,
                recipient_id=exp["seller_id"],
                subject=f"Expired Auction Returned: {exp['item_name']}",
                body=f"Your listing #{lid} for [{exp['item_name']}] reached its expiration without a buyout. The parcel has been returned to your mailbox.",
                attached_instance_id=exp["instance_id"],
            )
            swept.append(lid)

    if swept:
        from src.services.broadcaster import broadcaster
        broadcaster.broadcast_sync("LISTINGS_SWEPT", {"count": len(swept), "listing_ids": swept})

    return {
        "success": True,
        "swept_count": len(swept),
        "listing_ids": swept,
        "message": f"Swept {len(swept)} expired listing(s) and returned items to sellers via Courier Mail.",
    }
