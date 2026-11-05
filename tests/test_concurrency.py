"""
Concurrency stress tests benchmarking Pessimistic Locking vs Unprotected Naive Reads.
"""

from src.services.dupe_bench_service import run_dupe_race_condition_attack


def test_pessimistic_locking_stress():
    # 50 simultaneous concurrent threads firing against a single 1-of-1 listing
    res = run_dupe_race_condition_attack(concurrent_threads=50, locking_mode="PESSIMISTIC_FOR_UPDATE")
    assert res["settled"] == 1
    assert res["rejected_by_lock"] == 49
    assert res["items_duplicated"] == 0
    assert res["final_listing_status"] == "SOLD"


def test_unprotected_race_window():
    # 30 concurrent threads hitting unprotected read
    res = run_dupe_race_condition_attack(concurrent_threads=30, locking_mode="UNSAFE_NAIVE_READ")
    assert res["stale_reads_detected"] >= 1
    assert res["items_duplicated"] == 0
