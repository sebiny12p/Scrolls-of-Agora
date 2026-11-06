"""
Persistent In-Game Mail & Courier Parcel Repository for Scrolls of Agora.
Handles asynchronous delivery, Cash-on-Delivery (COD), inventory overflow parcels,
and double-entry journal balance invariance.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional

from src.config import DEFAULT_MAX_BAG_SLOTS, MAIL_EXPIRATION_DAYS
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


def get_player_bag_count(cur: Any, player_id: int) -> int:
    """Returns count of active, non-escrowed inventory items held in player's bag."""
    execute_sql(
        cur,
        "SELECT COUNT(*) AS bag_count FROM inventory_items WHERE owner_id = ? AND is_escrowed = 0;",
        (player_id,),
    )
    row = cur.fetchone()
    if not row:
        return 0
    return row["bag_count"] if hasattr(row, "keys") else row[0]


def get_player_mailbox(player_id: int) -> List[Dict[str, Any]]:
    """Retrieves all active mail items for a given player."""
    with get_db_cursor() as cur:
        execute_sql(
            cur,
            """
            SELECT
                pm.*,
                ii.mint_serial, ii.temper_tier, ii.bonus_power,
                it.item_id, it.item_name, it.icon_key, it.rarity
            FROM player_mail pm
            LEFT JOIN inventory_items ii ON ii.instance_id = pm.attached_instance_id
            LEFT JOIN item_templates it ON it.item_id = ii.item_id
            WHERE pm.recipient_id = ?
            ORDER BY pm.is_collected ASC, pm.mail_id DESC;
            """,
            (player_id,),
        )
        return rows_to_dicts(cur.fetchall())


def get_player_sent_mail(player_id: int) -> List[Dict[str, Any]]:
    """Retrieves all parcels dispatched by a given player."""
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT username FROM players WHERE player_id = ?;", (player_id,))
        p_row = cur.fetchone()
        if not p_row:
            return []
        uname = p_row["username"] if hasattr(p_row, "keys") else p_row[0]
        execute_sql(
            cur,
            """
            SELECT
                pm.*, p.username AS recipient_name,
                ii.mint_serial, ii.temper_tier, ii.bonus_power,
                it.item_id, it.item_name, it.icon_key, it.rarity
            FROM player_mail pm
            JOIN players p ON p.player_id = pm.recipient_id
            LEFT JOIN inventory_items ii ON ii.instance_id = pm.attached_instance_id
            LEFT JOIN item_templates it ON it.item_id = ii.item_id
            WHERE pm.sender_name = ?
            ORDER BY pm.mail_id DESC;
            """,
            (uname,),
        )
        return rows_to_dicts(cur.fetchall())


def send_player_mail(
    sender_id: int,
    recipient_id: int,
    subject: str,
    body: str = "",
    attached_gold: int = 0,
    attached_instance_id: Optional[int] = None,
    cod_amount: int = 0,
) -> Dict[str, Any]:
    """
    Sends mail from one player to another with optional gold or attached item.
    Locks attached assets in escrow until collected.
    """
    if sender_id == recipient_id:
        return {"success": False, "code": "ERR_SELF_MAIL", "message": "Cannot send mail to yourself."}

    with get_db_cursor(immediate=True) as cur:
        # Verify sender and recipient
        execute_sql(cur, "SELECT username, gold_balance, is_banned FROM players WHERE player_id = ?;", (sender_id,))
        sender = cur.fetchone()
        if not sender or sender["is_banned"]:
            return {"success": False, "code": "ERR_SENDER_INVALID", "message": "Sender account is invalid or banned."}

        execute_sql(cur, "SELECT username, is_banned FROM players WHERE player_id = ?;", (recipient_id,))
        recipient = cur.fetchone()
        if not recipient or recipient["is_banned"]:
            return {"success": False, "code": "ERR_RECIPIENT_INVALID", "message": "Recipient account not found."}

        if attached_gold > 0 and sender["gold_balance"] < attached_gold:
            return {"success": False, "code": "ERR_INSUFFICIENT_GOLD", "message": "Insufficient gold to attach."}

        # Check attached item
        if attached_instance_id is not None:
            execute_sql(
                cur,
                "SELECT instance_id, owner_id, is_escrowed FROM inventory_items WHERE instance_id = ?;",
                (attached_instance_id,),
            )
            item = cur.fetchone()
            if not item or item["owner_id"] != sender_id:
                return {"success": False, "code": "ERR_NOT_OWNER", "message": "You do not own this item."}
            if item["is_escrowed"]:
                return {"success": False, "code": "ERR_ESCROWED", "message": "Item is already escrowed elsewhere."}

            execute_sql(
                cur,
                "UPDATE inventory_items SET is_escrowed = 1 WHERE instance_id = ?;",
                (attached_instance_id,),
            )

        tx_group_id = f"TX-MAIL-{uuid.uuid4().hex[:10].upper()}"

        if attached_gold > 0:
            execute_sql(
                cur,
                "UPDATE players SET gold_balance = gold_balance - ?, escrow_gold = escrow_gold + ? WHERE player_id = ?;",
                (attached_gold, attached_gold, sender_id),
            )
            record_journal_entries(
                cur,
                tx_group_id=tx_group_id,
                event_type="ESCROW_LOCK",
                entries=[
                    ("PLAYER_LIQUID", str(sender_id), -attached_gold, f"Mail attachment debit to {recipient['username']}"),
                    ("PLAYER_ESCROW", str(sender_id), attached_gold, f"Mail attachment escrow hold for Mail #{tx_group_id}"),
                ],
            )

        exp_str = (utc_now() + timedelta(days=MAIL_EXPIRATION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
        mail_id = execute_insert(
            cur,
            """
            INSERT INTO player_mail (
                recipient_id, sender_name, subject, body,
                attached_gold, attached_instance_id, cod_amount, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                recipient_id,
                sender["username"],
                subject,
                body,
                attached_gold,
                attached_instance_id,
                cod_amount,
                exp_str,
            ),
            pkey_column="mail_id",
        )

    broadcaster.broadcast_sync("MAIL_ARRIVED", {"recipient_id": recipient_id, "subject": subject})

    return {
        "success": True,
        "mail_id": mail_id,
        "message": f"Parcel successfully dispatched to {recipient['username']}.",
    }


def claim_mail_attachment(mail_id: int, player_id: int) -> Dict[str, Any]:
    """
    Collects attached gold and inventory item from a mail parcel.
    Enforces maximum bag slot capacity and Cash-on-Delivery payment if required.
    """
    with get_db_cursor(immediate=True) as cur:
        execute_sql(
            cur,
            """
            SELECT pm.*, p.username AS recipient_name, p.gold_balance
            FROM player_mail pm
            JOIN players p ON p.player_id = pm.recipient_id
            WHERE pm.mail_id = ?;
            """,
            (mail_id,),
        )
        mail = cur.fetchone()

        if not mail:
            return {"success": False, "code": "ERR_NOT_FOUND", "message": "Mail parcel does not exist."}
        if mail["recipient_id"] != player_id:
            return {"success": False, "code": "ERR_NOT_RECIPIENT", "message": "You cannot claim another player's mail."}
        if mail["is_collected"]:
            return {"success": False, "code": "ERR_ALREADY_CLAIMED", "message": "Attachments already collected."}

        # Bag slot check if item is attached
        if mail["attached_instance_id"] is not None:
            current_slots = get_player_bag_count(cur, player_id)
            if current_slots >= DEFAULT_MAX_BAG_SLOTS:
                return {
                    "success": False,
                    "code": "ERR_BAG_FULL",
                    "message": f"Inventory full ({current_slots}/{DEFAULT_MAX_BAG_SLOTS} slots). Clear bag space before claiming item.",
                }

        # Handle Cash-on-Delivery
        cod = int(mail["cod_amount"])
        if cod > 0:
            if mail["gold_balance"] < cod:
                return {"success": False, "code": "ERR_INSUFFICIENT_GOLD", "message": f"Need {cod}g liquid gold to pay COD fee."}

            execute_sql(cur, "SELECT player_id FROM players WHERE username = ?;", (mail["sender_name"],))
            sender_row = cur.fetchone()
            sender_id = sender_row["player_id"] if sender_row else None

            tx_cod = f"TX-COD-{uuid.uuid4().hex[:10].upper()}"
            execute_sql(cur, "UPDATE players SET gold_balance = gold_balance - ? WHERE player_id = ?;", (cod, player_id))
            if sender_id:
                execute_sql(cur, "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;", (cod, sender_id))
                record_journal_entries(
                    cur,
                    tx_group_id=tx_cod,
                    event_type="MAIL_COD",
                    entries=[
                        ("PLAYER_LIQUID", str(player_id), -cod, f"COD payment to {mail['sender_name']}"),
                        ("PLAYER_LIQUID", str(sender_id), cod, f"COD receipt from {mail['recipient_name']}"),
                    ],
                )

        # Claim attached gold
        gold = int(mail["attached_gold"])
        if gold > 0:
            tx_claim = f"TX-CLAIM-{uuid.uuid4().hex[:10].upper()}"
            execute_sql(cur, "UPDATE players SET gold_balance = gold_balance + ? WHERE player_id = ?;", (gold, player_id))
            # Determine sender if possible to release escrow
            execute_sql(cur, "SELECT player_id FROM players WHERE username = ?;", (mail["sender_name"],))
            sender_row = cur.fetchone()
            if sender_row:
                sender_id = str(sender_row["player_id"])
                execute_sql(
                    cur,
                    "UPDATE players SET escrow_gold = CASE WHEN escrow_gold >= ? THEN escrow_gold - ? ELSE 0 END WHERE player_id = ?;",
                    (gold, gold, sender_row["player_id"]),
                )
                record_journal_entries(
                    cur,
                    tx_group_id=tx_claim,
                    event_type="ESCROW_REFUND",
                    entries=[
                        ("PLAYER_ESCROW", sender_id, -gold, f"Released mail escrow to {mail['recipient_name']}"),
                        ("PLAYER_LIQUID", str(player_id), gold, f"Claimed mail gold attachment from {mail['sender_name']}"),
                    ],
                )
            else:
                record_journal_entries(
                    cur,
                    tx_group_id=tx_claim,
                    event_type="ESCROW_REFUND",
                    entries=[
                        ("SYSTEM_SINK", "SYSTEM_SINK", -gold, f"Released system courier parcel gold to {mail['recipient_name']}"),
                        ("PLAYER_LIQUID", str(player_id), gold, f"Claimed system mail gold attachment from {mail['sender_name']}"),
                    ],
                )

        # Claim attached item
        item_id = mail["attached_instance_id"]
        if item_id is not None:
            execute_sql(
                cur,
                "UPDATE inventory_items SET owner_id = ?, is_escrowed = 0 WHERE instance_id = ?;",
                (player_id, item_id),
            )

        execute_sql(
            cur,
            "UPDATE player_mail SET is_collected = 1, is_read = 1 WHERE mail_id = ?;",
            (mail_id,),
        )

    return {
        "success": True,
        "message": f"Successfully claimed parcel: +{gold}g gold, Item #{item_id or 'None'}.",
    }


def deliver_overflow_or_system_mail(
    cur: Any,
    recipient_id: int,
    subject: str,
    body: str,
    attached_gold: int = 0,
    attached_instance_id: Optional[int] = None,
) -> int:
    """Helper used across transactions to dispatch automatic system courier parcels."""
    exp_str = (utc_now() + timedelta(days=MAIL_EXPIRATION_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    mail_id = execute_insert(
        cur,
        """
        INSERT INTO player_mail (
            recipient_id, sender_name, subject, body,
            attached_gold, attached_instance_id, cod_amount, expires_at
        ) VALUES (?, 'Agora Courier', ?, ?, ?, ?, 0, ?);
        """,
        (recipient_id, subject, body, attached_gold, attached_instance_id, exp_str),
        pkey_column="mail_id",
    )
    if attached_gold > 0:
        tx_sys_mail = f"TX-SYS-PARCEL-{mail_id}-{uuid.uuid4().hex[:6].upper()}"
        record_journal_entries(
            cur,
            tx_group_id=tx_sys_mail,
            event_type="ESCROW_LOCK",
            entries=[
                ("SYSTEM_SINK", "SYSTEM_SINK", attached_gold, f"System courier parcel gold provision for Mail #{mail_id}"),
                ("SYSTEM_SINK", "SYSTEM_SINK", -attached_gold, f"System gold allocated to courier parcel hold #{mail_id}"),
            ],
        )
    return mail_id or 1
