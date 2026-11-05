"""
Unit and integration tests for Relational Algebra queries, Recursive CTE, and fraud seizure.
"""

import pytest
from src.repositories.analytics_repo import (
    run_analytical_query,
    get_rmt_laundering_graph,
    ban_and_seize_rmt_mule_ring,
    ANALYTICAL_CATALOG,
)
from src.database import audit_ledger_integrity


@pytest.mark.parametrize("query_key", list(ANALYTICAL_CATALOG.keys()))
def test_all_relational_queries(query_key):
    res = run_analytical_query(query_key)
    assert "rows" in res
    assert len(res["rows"]) > 0
    assert "query_plan" in res


def test_recursive_cte_cycle_safety():
    res = get_rmt_laundering_graph()
    assert "edges" in res
    assert len(res["edges"]) >= 3
    assert res["max_hop_depth"] >= 2
    assert res["total_laundered_gold"] > 0


def test_fraud_audit_seizure():
    res = ban_and_seize_rmt_mule_ring()
    assert res["success"] is True
    assert res["banned_accounts"] > 0
    assert res["seized_gold"] > 0

    # Verify ledger journal invariance after seizure
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["net_system_imbalance"] == 0
