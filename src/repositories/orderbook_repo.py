"""
Double-Sided Continuous Limit Orderbook Matching Engine for Scrolls of Agora.
Handles resting bid/ask limit orders, price-time priority crossing,
escrow locking, and double-entry ledger settlement.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from src.database import (
    get_db_cursor,
    execute_sql,
    execute_insert,
    row_to_dict,
    rows_to_dicts,
    record_journal_entries,
)
from src.services.broadcaster import broadcaster


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_orderbook_depth(item_id: int, realm_id: int = 0) -> Dict[str, Any]:
    """Retrieves orderbook depth (bids and asks ladder) for a given item."""
    realm_filter = "AND realm_id = ?" if realm_id and realm_id > 0 else ""
    params = (item_id, realm_id) if realm_id and realm_id > 0 else (item_id,)

    with get_db_cursor() as cur:
        # Bids (Buyers wanting to purchase at limit price or lower)
        execute_sql(
            cur,
            f"""
            SELECT unit_price, SUM(quantity - filled_quantity) AS volume, COUNT(*) AS order_count
            FROM limit_orders
            WHERE item_id = ? AND side = 'BUY' AND status = 'OPEN' {realm_filter}
            GROUP BY unit_price
            ORDER BY unit_price DESC;
            """,
            params,
        )
        bids = rows_to_dicts(cur.fetchall())

        # Asks (Sellers offering item at limit price or higher)
        execute_sql(
            cur,
            f"""
            SELECT unit_price, SUM(quantity - filled_quantity) AS volume, COUNT(*) AS order_count
            FROM limit_orders
            WHERE item_id = ? AND side = 'SELL' AND status = 'OPEN' {realm_filter}
            GROUP BY unit_price
            ORDER BY unit_price ASC;
            """,
            params,
        )
        asks = rows_to_dicts(cur.fetchall())

    return {
        "item_id": item_id,
        "realm_id": realm_id,
        "bids": bids,
        "asks": asks,
        "spread": (asks[0]["unit_price"] - bids[0]["unit_price"]) if bids and asks else None,
    }


def place_limit_order(
    player_id: int,
    item_id: int,
    realm_id: int,
    side: str,
    unit_price: int,
    quantity: int = 1,
) -> Dict[str, Any]:
    """
    Submits a limit order to the continuous orderbook.
    Locks gold into escrow for BUY orders, and attempts immediate continuous matching.
    """
    side = side.upper()
    if side not in ("BUY", "SELL"):
        return {"success": False, "code": "ERR_INVALID_SIDE", "message": "Side must be BUY or SELL."}
    if unit_price <= 0 or quantity <= 0:
        return {"success": False, "code": "ERR_INVALID_AMOUNT", "message": "Price and quantity must be positive."}

    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "SELECT gold_balance, is_banned, username FROM players WHERE player_id = ?;", (player_id,))
        player = cur.fetchone()
        if not player or player["is_banned"]:
            return {"success": False, "code": "ERR_BANNED", "message": "Player account invalid or banned."}

        total_cost = unit_price * quantity
        tx_group_id = f"TX-LIMIT-{uuid.uuid4().hex[:10].upper()}"

        if side == "BUY":
            if player["gold_balance"] < total_cost:
                return {
                    "success": False,
                    "code": "ERR_INSUFFICIENT_GOLD",
                    "message": f"Requires {total_cost}g liquid gold, but balance is {player['gold_balance']}g.",
                }

            # Escrow lock on buyer funds
            execute_sql(
                cur,
                "UPDATE players SET gold_balance = gold_balance - ?, escrow_gold = escrow_gold + ? WHERE player_id = ?;",
                (total_cost, total_cost, player_id),
            )
            record_journal_entries(
                cur,
                tx_group_id=tx_group_id,
                event_type="LIMIT_ESCROW_LOCK",
                entries=[
                    ("PLAYER_LIQUID", str(player_id), -total_cost, f"Limit Buy Order #{tx_group_id} escrow hold"),
                    ("PLAYER_ESCROW", str(player_id), total_cost, f"Limit Buy Order #{tx_group_id} escrow locked"),
                ],
            )
        else:
            # Side == SELL: Player must own at least `quantity` un-escrowed instances
            execute_sql(
                cur,
                "SELECT instance_id FROM inventory_items WHERE owner_id = ? AND item_id = ? AND is_escrowed = 0 LIMIT ?;",
                (player_id, item_id, quantity),
            )
            available_items = [r["instance_id"] if hasattr(r, "keys") else r[0] for r in cur.fetchall()]
            if len(available_items) < quantity:
                return {
                    "success": False,
                    "code": "ERR_INSUFFICIENT_ITEMS",
                    "message": f"You do not possess {quantity} un-escrowed units of this item.",
                }

            for inst_id in available_items:
                execute_sql(cur, "UPDATE inventory_items SET is_escrowed = 1 WHERE instance_id = ?;", (inst_id,))

        order_id = execute_insert(
            cur,
            """
            INSERT INTO limit_orders (player_id, item_id, realm_id, side, unit_price, quantity, filled_quantity, status)
            VALUES (?, ?, ?, ?, ?, ?, 0, 'OPEN');
            """,
            (player_id, item_id, realm_id, side, unit_price, quantity),
            pkey_column="order_id",
        )

        # ---------------------------------------------------------------------
        # Continuous Matching Engine: Match opposite resting orders
        # ---------------------------------------------------------------------
        fills = 0
        if side == "BUY":
            # Find resting SELL orders with unit_price <= our bid
            execute_sql(
                cur,
                """
                SELECT * FROM limit_orders
                WHERE item_id = ? AND side = 'SELL' AND status = 'OPEN' AND unit_price <= ? AND player_id <> ?
                ORDER BY unit_price ASC, order_id ASC;
                """,
                (item_id, unit_price, player_id),
            )
            resting_sells = rows_to_dicts(cur.fetchall())
            for sell_ord in resting_sells:
                if fills >= quantity:
                    break
                # Find the seller's escrowed item instance (isolated from kiosk auction listings)
                execute_sql(
                    cur,
                    """
                    SELECT instance_id FROM inventory_items
                    WHERE owner_id = ? AND item_id = ? AND is_escrowed = 1
                      AND instance_id NOT IN (SELECT instance_id FROM auction_listings WHERE status = 'ACTIVE')
                    LIMIT 1;
                    """,
                    (sell_ord["player_id"], item_id),
                )
                inst_row = cur.fetchone()
                if not inst_row:
                    continue
                traded_inst_id = inst_row["instance_id"] if hasattr(inst_row, "keys") else inst_row[0]

                execution_price = sell_ord["unit_price"]  # Price improvement for buyer!
                buyer_surplus = unit_price - execution_price

                # Transfer item
                execute_sql(
                    cur,
                    "UPDATE inventory_items SET owner_id = ?, is_escrowed = 0 WHERE instance_id = ?;",
                    (player_id, traded_inst_id),
                )
                # Release buyer escrow & pay seller
                execute_sql(
                    cur,
                    "UPDATE players SET escrow_gold = escrow_gold - ? WHERE player_id = ?;",
                    (unit_price, player_id),
                )
                if buyer_surplus > 0:
                    execute_sql(
                        cur,
                        "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;",
                        (buyer_surplus, player_id),
                    )
                execute_sql(
                    cur,
                    "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;",
                    (execution_price, sell_ord["player_id"]),
                )

                # Balanced journal
                match_tx = f"TX-MATCH-{uuid.uuid4().hex[:10].upper()}"
                entries = [
                    ("PLAYER_ESCROW", str(player_id), -unit_price, "Orderbook fill escrow release"),
                    ("PLAYER_LIQUID", str(sell_ord["player_id"]), execution_price, "Orderbook sell fill payment"),
                ]
                if buyer_surplus > 0:
                    entries.append(("PLAYER_LIQUID", str(player_id), buyer_surplus, "Price-improvement refund"))

                record_journal_entries(cur, tx_group_id=match_tx, event_type="LIMIT_MATCH", entries=entries)

                # Mark order states
                execute_sql(cur, "UPDATE limit_orders SET filled_quantity = filled_quantity + 1 WHERE order_id = ?;", (sell_ord["order_id"],))
                execute_sql(cur, "UPDATE limit_orders SET status = 'FILLED' WHERE order_id = ? AND filled_quantity >= quantity;", (sell_ord["order_id"],))
                fills += 1

            if fills > 0:
                execute_sql(cur, "UPDATE limit_orders SET filled_quantity = ?, status = CASE WHEN ? >= quantity THEN 'FILLED' ELSE 'OPEN' END WHERE order_id = ?;", (fills, fills, order_id))

        elif side == "SELL":
            # Incoming SELL order: Match against resting BUY orders with unit_price >= our ask price
            execute_sql(
                cur,
                """
                SELECT * FROM limit_orders
                WHERE item_id = ? AND side = 'BUY' AND status = 'OPEN' AND unit_price >= ? AND player_id <> ?
                ORDER BY unit_price DESC, order_id ASC;
                """,
                (item_id, unit_price, player_id),
            )
            resting_buys = rows_to_dicts(cur.fetchall())
            for buy_ord in resting_buys:
                if fills >= quantity or fills >= len(available_items):
                    break
                traded_inst_id = available_items[fills]

                # Resting order sets execution price
                execution_price = buy_ord["unit_price"]

                # Transfer item to buyer
                execute_sql(
                    cur,
                    "UPDATE inventory_items SET owner_id = ?, is_escrowed = 0 WHERE instance_id = ?;",
                    (buy_ord["player_id"], traded_inst_id),
                )
                # Deduct from buyer escrow & pay seller
                execute_sql(
                    cur,
                    "UPDATE players SET escrow_gold = escrow_gold - ? WHERE player_id = ?;",
                    (execution_price, buy_ord["player_id"]),
                )
                execute_sql(
                    cur,
                    "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;",
                    (execution_price, player_id),
                )

                # Balanced journal
                match_tx = f"TX-MATCH-{uuid.uuid4().hex[:10].upper()}"
                entries = [
                    ("PLAYER_ESCROW", str(buy_ord["player_id"]), -execution_price, "Limit match escrow release"),
                    ("PLAYER_LIQUID", str(player_id), execution_price, "Limit match seller payout"),
                ]
                record_journal_entries(cur, tx_group_id=match_tx, event_type="LIMIT_MATCH", entries=entries)

                # Update resting buy order
                execute_sql(cur, "UPDATE limit_orders SET filled_quantity = filled_quantity + 1 WHERE order_id = ?;", (buy_ord["order_id"],))
                execute_sql(cur, "UPDATE limit_orders SET status = 'FILLED' WHERE order_id = ? AND filled_quantity >= quantity;", (buy_ord["order_id"],))
                fills += 1

            if fills > 0:
                execute_sql(cur, "UPDATE limit_orders SET filled_quantity = ?, status = CASE WHEN ? >= quantity THEN 'FILLED' ELSE 'OPEN' END WHERE order_id = ?;", (fills, fills, order_id))

    broadcaster.broadcast_sync("ORDERBOOK_UPDATE", {"item_id": item_id, "side": side, "order_id": order_id, "fills": fills})

    return {
        "success": True,
        "order_id": order_id,
        "side": side,
        "unit_price": unit_price,
        "quantity": quantity,
        "immediate_fills": fills,
        "message": f"Limit {side} order #{order_id} submitted ({fills}/{quantity} filled immediately).",
    }
