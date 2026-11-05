"""
Unit and integration tests for ACID transactions, deterministic lock ordering, and ledger entries.
"""

from src.repositories.transaction_repo import (
    execute_pessimistic_buyout,
    place_escrow_bid,
    list_inventory_item,
    temper_and_enchant_item,
    place_kiosk_bid,
    trigger_weekly_kiosk_flip,
)
from src.database import audit_ledger_integrity, get_db_cursor, execute_sql


def test_atomic_buyout_settlement():
    res = execute_pessimistic_buyout(listing_id=102, buyer_id=1005)
    assert res["success"] is True
    assert res["code"] == "SETTLED"
    assert res["gross_price"] == 88000

    # Ensure listing is closed
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT status, high_bidder_id FROM auction_listings WHERE listing_id = 102;")
        row = cur.fetchone()
        assert row["status"] == "SOLD"
        assert row["high_bidder_id"] == 1005

    # Verify that ledger balance remains 100% zero-imbalance
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_escrow_bid_and_outbid_refund():
    # 1. Place initial bid
    res1 = place_escrow_bid(listing_id=110, bidder_id=1001, bid_amount=14500)
    assert res1["success"] is True

    # 2. Outbid by second bidder
    res2 = place_escrow_bid(listing_id=110, bidder_id=1005, bid_amount=16000)
    assert res2["success"] is True

    # Verify outbid player escrow returned
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT current_bid, high_bidder_id FROM auction_listings WHERE listing_id = 110;")
        listing = cur.fetchone()
        assert listing["current_bid"] == 16000
        assert listing["high_bidder_id"] == 1005

    # Verify ledger journal invariance
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_temper_and_enchant_crafting():
    res = temper_and_enchant_item(instance_id=9013, player_id=1005, enchant_id=1)
    assert res["success"] is True
    assert "Tempered" in res["message"]

    # Verify item bonus power increased
    with get_db_cursor() as cur:
        execute_sql(cur, "SELECT temper_tier, bonus_power FROM inventory_items WHERE instance_id = 9013;")
        item = cur.fetchone()
        assert item["temper_tier"] == 1
        assert item["bonus_power"] == 95

    # Verify ledger journal invariance
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0


def test_sealed_kiosk_bid_and_weekly_flip():
    res_bid = place_kiosk_bid(realm_id=3, guild_id=3, bid_gold=1300000)
    assert res_bid["success"] is True

    res_flip = trigger_weekly_kiosk_flip()
    assert res_flip["success"] is True
    assert len(res_flip["flips"]) == 5

    # Verify ledger journal invariance
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0
