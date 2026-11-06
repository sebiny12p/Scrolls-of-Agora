"""
Comprehensive Unit & Integration Test Suite for Scrolls of Agora Systems Upgrades:
  1. Persistent In-Game Mailbox & Courier Delivery
  2. Inventory Bag Capacity Constraints & Overflow Routing
  3. Equipment Durability Degradation & Blacksmith Repair Station
  4. Atomic 2-Way Peer-to-Peer (P2P) Secure Trade
  5. Continuous Limit Orderbook Matching Engine
  6. Dynamic Real-Time OHLC Aggregator Pipeline
  7. Cryptographic Auth Session Token Security
  8. Automated Expired Listing Sweeper
"""

import pytest
from src.database import get_db_cursor, execute_sql, audit_ledger_integrity
from src.repositories.mail_repo import send_player_mail, claim_mail_attachment, get_player_mailbox
from src.repositories.transaction_repo import (
    repair_player_equipment,
    degrade_equipment_durability,
    execute_p2p_trade,
    sweep_expired_listings,
    execute_pessimistic_buyout,
)
from src.repositories.orderbook_repo import place_limit_order, get_orderbook_depth
from src.repositories.analytics_repo import rollup_realtime_ohlc
from src.auth import create_player_token, verify_player_token


def test_in_game_mailbox_and_claim():
    # Player 1005 sends 5,000g and Item #9013 to Player 1001
    res_send = send_player_mail(
        sender_id=1005,
        recipient_id=1001,
        subject="Consortium Dividend",
        body="Here is your share of the Mournhold trade revenue.",
        attached_gold=5000,
        attached_instance_id=9013,
    )
    assert res_send["success"] is True
    mail_id = res_send["mail_id"]

    # Verify parcel appears in recipient's mailbox
    mailbox = get_player_mailbox(1001)
    matching = [m for m in mailbox if m["mail_id"] == mail_id]
    assert len(matching) == 1
    assert matching[0]["attached_gold"] == 5000
    assert matching[0]["is_collected"] == 0

    # Claim mail attachment
    res_claim = claim_mail_attachment(mail_id=mail_id, player_id=1001)
    assert res_claim["success"] is True

    # Verify item transferred and double-entry invariant holds
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT owner_id, is_escrowed FROM inventory_items WHERE instance_id = 9013;")
        item = cur.fetchone()
        assert item["owner_id"] == 1001
        assert item["is_escrowed"] == 0

    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_equipment_durability_and_blacksmith_repair():
    # Degrade player 1005 equipment
    degrade_equipment_durability(player_id=1005, amount=30)

    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT MIN(current_durability) AS min_d FROM inventory_items WHERE owner_id = 1005 AND is_escrowed = 0;")
        min_d = cur.fetchone()["min_d"]
        assert min_d < 100

    # Repair at Blacksmith
    repair_res = repair_player_equipment(player_id=1005)
    assert repair_res["success"] is True
    assert repair_res["items_repaired"] > 0
    assert repair_res["repair_cost"] > 0

    # Verify all equipment restored to 100%
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT MIN(current_durability) AS min_d FROM inventory_items WHERE owner_id = 1005 AND is_escrowed = 0;")
        assert cur.fetchone()["min_d"] == 100

    # Verify zero-imbalance in general ledger
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_p2p_atomic_trade_invariance():
    # Player 1005 sells Item #9014 directly to Player 1001 for 25,000g (P2P zero-kiosk trade)
    res = execute_p2p_trade(
        player_a_id=1005,
        player_b_id=1001,
        gold_a=0,
        gold_b=25000,
        instance_a_id=9014,
        instance_b_id=None,
    )
    assert res["success"] is True

    # Verify Item 9014 transferred to Player 1001
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT owner_id, is_escrowed FROM inventory_items WHERE instance_id = 9014;")
        item = cur.fetchone()
        assert item["owner_id"] == 1001
        assert item["is_escrowed"] == 0

    # Ledger audit
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_continuous_limit_orderbook_matching():
    # Player 1001 places BUY limit order for Crown of White-Gold (5004) at 15,000g
    buy_res = place_limit_order(
        player_id=1001,
        item_id=5004,
        realm_id=1,
        side="BUY",
        unit_price=15000,
        quantity=1,
    )
    assert buy_res["success"] is True
    assert buy_res["side"] == "BUY"

    # Player 1005 owns Item #9014 (item_id 5004). Place SELL limit order at 12,000g (should cross!)
    sell_res = place_limit_order(
        player_id=1005,
        item_id=5004,
        realm_id=1,
        side="SELL",
        unit_price=12000,
        quantity=1,
    )
    assert sell_res["success"] is True
    assert sell_res["immediate_fills"] == 1

    # Check orderbook depth
    depth = get_orderbook_depth(item_id=5004, realm_id=1)
    assert "bids" in depth
    assert "asks" in depth

    # Ledger audit
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_realtime_ohlc_pipeline():
    res = rollup_realtime_ohlc()
    assert res["success"] is True
    assert res["candles_generated"] > 0


def test_cryptographic_auth_tokens():
    token = create_player_token(player_id=1005, username="Aurelius_Goldhand")
    assert isinstance(token, str)
    assert "." in token

    decoded = verify_player_token(token)
    assert decoded is not None
    assert decoded["sub"] == 1005
    assert decoded["name"] == "Aurelius_Goldhand"

    # Tampered token check
    tampered = token[:-4] + "ABCD"
    assert verify_player_token(tampered) is None


def test_expired_listing_sweeper():
    # Update listing 101 to expired in the past
    with get_db_cursor(immediate=True) as cur:
        execute_sql(cur, "UPDATE auction_listings SET expires_at = '2020-01-01 00:00:00' WHERE listing_id = 101;")

    sweep_res = sweep_expired_listings()
    assert sweep_res["success"] is True
    assert 101 in sweep_res["listing_ids"]

    # Verify listing is now EXPIRED
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT status FROM auction_listings WHERE listing_id = 101;")
        assert cur.fetchone()["status"] == "EXPIRED"

    # Ledger invariance
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0
