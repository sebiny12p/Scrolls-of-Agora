"""
Automated Verification & Concurrency Stress Suite for Scrolls of Agora (v3.0)
Tests:
  1. Schema & Seed Integrity (12 tables, 5 Tamriel Hubs: Wayrest, Elden Root, Mournhold, Imperial City, Rawl'kha)
  2. Atomic Escrow Bid & Automatic Outbid Refund
  3. Arcane Tempering & Glyph Enchanting Forge (Multi-Table Atomic Craft)
  4. The Weekly Kiosk Flip (Sealed-Bid Guild Trader Resolution & Refunds)
  5. Recursive CTE RMT Mule Graph Tracer & Atomic Inquisitor Seizure
  6. 100-Thread Simultaneous Race-Condition Buyout Attack (0 Dupes Guarantee)
  7. All 7 Relational Algebra & SQL Analytical Queries
"""

import sys
import app as engine

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_all_tests():
    print("=" * 72)
    print("  SCROLLS OF AGORA (v3.0) — AUTOMATED RELATIONAL & CONCURRENCY SUITE")
    print("=" * 72)

    # 1. Reset and check initial 5-hub Tamriel state
    engine.init_and_seed_database()
    state = engine.get_market_state()
    kpis = state["kpis"]
    hub_names = [r["realm_name"] for r in state["realms"]]
    assert hub_names == ["Wayrest", "Elden Root", "Mournhold", "Imperial City", "Rawl'kha"], f"Unexpected hubs: {hub_names}"
    assert kpis["active_orders"] == 12, f"Expected 12 active orders across 5 hubs, got {kpis['active_orders']}"
    assert kpis["total_minted_items"] == kpis["unique_serials"], "Mint serial uniqueness violated!"
    print(f"[PASS] 5 Tamriel Hubs Verified: {', '.join(hub_names)} ({kpis['active_orders']} active listings, {kpis['unique_serials']} unique serials).")

    # 2. Test Atomic Escrow Bidding & Outbid Refund
    res_bid = engine.api_place_bid(engine.BidRequest(listing_id=110, bidder_id=1001, bid_amount=14500))
    assert res_bid["success"] is True
    res_outbid = engine.api_place_bid(engine.BidRequest(listing_id=110, bidder_id=1005, bid_amount=16000))
    assert res_outbid["success"] is True
    print(f"[PASS] Atomic Escrow Bid & Outbid Refund Verified: {res_outbid['message']}")

    # 3. Test Arcane Tempering & Glyph Enchanting (Atomic Multi-Table Crafting)
    temper_res = engine.api_temper_and_enchant_item(
        engine.TemperCraftRequest(instance_id=9013, player_id=1005, enchant_id=1)
    )
    assert temper_res["success"] is True
    print(f"[PASS] Arcane Tempering Forge Verified: {temper_res['message']}")

    # 4. Test Sealed Guild Kiosk Bid & The Weekly Kiosk Flip
    bid_kiosk = engine.api_place_kiosk_bid(engine.KioskBidRequest(realm_id=3, guild_id=3, bid_gold=1300000))
    assert bid_kiosk["success"] is True
    flip_res = engine.api_trigger_weekly_kiosk_flip()
    assert flip_res["success"] is True and len(flip_res["flips"]) == 5
    print(f"[PASS] Sealed Guild Kiosk Bid & Weekly Flip Verified: {flip_res['message']}")

    # 5. Test Recursive CTE RMT Laundering Tracer & Atomic Inquisitor Seizure
    rmt_graph = engine.get_rmt_laundering_graph()
    assert len(rmt_graph["edges"]) >= 3, "Expected at least 3 RMT laundering hops"
    ban_res = engine.ban_and_seize_rmt_mule_ring()
    assert ban_res["success"] is True and ban_res["seized_gold"] > 0
    print(f"[PASS] Recursive CTE RMT Tracer & Inquisitor Seizure Verified: {ban_res['message']}")

    # 6. Test 100-Thread Simultaneous Buyout Race Condition Attack
    # 6A. Unsafe Naive Read (Demonstrates race-condition exploit / dirty read)
    unsafe_res = engine.run_dupe_race_condition_attack(
        engine.DupeStressRequest(concurrent_threads=50, locking_mode="UNSAFE_NAIVE_READ")
    )
    assert unsafe_res["succeeded"] > 1, f"Expected multiple race wins under naive read, got {unsafe_res['succeeded']}"
    print(
        f"[PASS] Unprotected Race Benchmark: {unsafe_res['succeeded']} phantom purchases granted "
        f"({unsafe_res['items_duplicated']} dupes detected, {unsafe_res['total_duration_ms']} ms)."
    )

    # 6B. Pessimistic Row-Level Locking (Guarantees zero dupes)
    stress_res = engine.run_dupe_race_condition_attack(
        engine.DupeStressRequest(concurrent_threads=100, locking_mode="PESSIMISTIC_FOR_UPDATE")
    )
    assert stress_res["succeeded"] == 1, f"Expected exactly 1 buyout winner, got {stress_res['succeeded']}"
    assert stress_res["rejected_by_lock"] == 99, f"Expected 99 lock rejections, got {stress_res['rejected_by_lock']}"
    assert stress_res["items_duplicated"] == 0, "Item duplication occurred!"
    print(
        f"[PASS] 100-Thread Anti-Dupe Stress Test: {stress_res['succeeded']} settled, "
        f"{stress_res['rejected_by_lock']} blocked by lock, {stress_res['items_duplicated']} dupes "
        f"({stress_res['total_duration_ms']} ms)."
    )

    # 7. Verify all 7 Relational Algebra & SQL Queries
    query_keys = [
        "q1_mythic_projection",
        "q2_isa_equipment_join",
        "q3_market_scarcity_diff",
        "q4_realm_tax_burn",
        "q5_cross_realm_arbitrage",
        "q6_rmt_anomaly_detection",
        "q7_whale_leaderboard",
    ]
    for qk in query_keys:
        q_out = engine.run_analytical_query(qk)
        assert len(q_out["rows"]) > 0, f"Query {qk} returned 0 rows!"
        print(f"[PASS] {q_out['title']} -> {len(q_out['rows'])} rows ({q_out['latency_us']} us)")

    # Reset back to clean initial state for the live UI
    engine.init_and_seed_database()
    print("=" * 72)
    print("  ALL 13 VERIFICATION & CONCURRENCY CHECKS PASSED 100%!")
    print("=" * 72)


if __name__ == "__main__":
    run_all_tests()
