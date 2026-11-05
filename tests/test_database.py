"""
Unit and integration tests for database connectivity, dialect adaptation, and ledger integrity.
"""

from src.database import (
    adapt_sql,
    get_db_cursor,
    execute_sql,
    get_engine_telemetry,
    audit_ledger_integrity,
    record_journal_entries,
)


def test_telemetry():
    telemetry = get_engine_telemetry()
    assert "active_backend" in telemetry
    assert "locking_mode" in telemetry


def test_adapt_sql_placeholders():
    # Test that adapt_sql does not replace ? inside string literals
    raw = "SELECT * FROM items WHERE name = 'What?' AND id = ?;"
    adapted = adapt_sql(raw)
    assert "'What?'" in adapted


def test_double_entry_balance_audit():
    audit = audit_ledger_integrity()
    assert audit["is_valid"] is True
    assert audit["imbalanced_groups_count"] == 0
    assert audit["net_system_imbalance"] == 0
    assert audit["total_transaction_groups"] > 0


def test_double_entry_imbalance_prevention():
    # Verify that record_journal_entries raises ValueError on unbalanced transactions
    with get_db_cursor(immediate=True) as cur:
        try:
            record_journal_entries(cur, "TX-TEST-INVALID", "BUYOUT", [
                ("PLAYER_LIQUID", "1001", -1000, "Debit"),
                ("PLAYER_LIQUID", "1002", 900, "Credit"), # Net = -100 != 0
            ])
            assert False, "Expected ValueError on double-entry imbalance"
        except ValueError:
            pass
