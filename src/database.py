"""
Multi-Engine Relational Database Adapter for Scrolls of Agora.
Supports:
  1. PostgreSQL (16/17+) with psycopg ConnectionPool & true row-level locking
  2. SQLite 3 with Write-Ahead Logging (WAL) and foreign key enforcement

Provides dialect adaptation, connection pooling, and transactional context managers.
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Any, Dict, List, Optional, Tuple

from src.config import DB_PATH, SQL_DIR, PG_DSN

_INIT_LOCK = threading.Lock()
ACTIVE_BACKEND: str = "SQLITE_WAL"
PG_POOL: Optional[Any] = None

# Attempt PostgreSQL connection pool initialization if driver and server are present
try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    # Test short connect
    with psycopg.connect(PG_DSN, connect_timeout=1) as _test_conn:
        pass

    PG_POOL = ConnectionPool(
        conninfo=PG_DSN,
        min_size=2,
        max_size=32,
        kwargs={"row_factory": dict_row},
    )
    ACTIVE_BACKEND = "POSTGRESQL"
except Exception:
    PG_POOL = None
    ACTIVE_BACKEND = "SQLITE_WAL"


def is_postgres() -> bool:
    return ACTIVE_BACKEND == "POSTGRESQL" and PG_POOL is not None


def get_sqlite_conn(timeout: float = 30.0) -> sqlite3.Connection:
    """Create a configured SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(str(DB_PATH), timeout=timeout, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


@contextmanager
def get_db_cursor(immediate: bool = False) -> Generator[Any, None, None]:
    """
    Context manager yielding a database cursor within a managed transaction.
    Automatically commits on normal completion or rolls back on exceptions.
    For SQLite, immediate=True issues 'BEGIN IMMEDIATE;' to acquire an immediate write lock.
    """
    if is_postgres():
        with PG_POOL.connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    yield cur
    else:
        conn = get_sqlite_conn()
        try:
            if immediate:
                conn.execute("BEGIN IMMEDIATE;")
            cur = conn.cursor()
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def adapt_sql(sql: str) -> str:
    """Adapts generic parameterized SQL to the active database engine dialect."""
    if is_postgres():
        # Replace ? placeholder with %s
        sql = sql.replace("?", "%s")
        # Replace SQLite string aggregation with PostgreSQL standard
        if "GROUP_CONCAT(" in sql:
            sql = sql.replace("GROUP_CONCAT(", "STRING_AGG(")
        # Replace SQLite conflict clause with PostgreSQL standard
        if "INSERT OR IGNORE INTO item_instance_enchantments" in sql:
            sql = sql.replace(
                "INSERT OR IGNORE INTO item_instance_enchantments",
                "INSERT INTO item_instance_enchantments"
            ) + " ON CONFLICT (instance_id, enchant_id) DO NOTHING"
        # Adapt datetime functions
        sql = sql.replace("datetime('now')", "CURRENT_TIMESTAMP")
    else:
        # SQLite adjustments if coming from standard SQL
        if "STRING_AGG(" in sql:
            sql = sql.replace("STRING_AGG(", "GROUP_CONCAT(")
        if "%s" in sql and "?" not in sql:
            sql = sql.replace("%s", "?")
    return sql


def execute_sql(cur: Any, sql: str, params: Tuple = ()) -> Any:
    """Executes a SQL statement adapting dialect syntax and parameters."""
    adapted = adapt_sql(sql)
    if params:
        return cur.execute(adapted, params)
    return cur.execute(adapted)


def row_to_dict(row: Any) -> Dict[str, Any]:
    """Convert a row object (sqlite3.Row or psycopg dict) to standard python dict."""
    if row is None:
        return {}
    if isinstance(row, dict):
        return row
    if hasattr(row, "keys"):
        return {k: row[k] for k in row.keys()}
    return dict(row)


def rows_to_dicts(rows: List[Any]) -> List[Dict[str, Any]]:
    return [row_to_dict(r) for r in rows]


def init_database(force: bool = False) -> None:
    """
    Initializes the database schema and seeds from SQL files.
    If force is False, initialization is skipped if tables already exist.
    """
    with _INIT_LOCK:
        if is_postgres():
            _init_postgres(force)
        else:
            _init_sqlite(force)


def _init_sqlite(force: bool = False) -> None:
    if not force and DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        conn = get_sqlite_conn()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM realms;")
            count = cur.fetchone()[0]
            if count >= 5:
                conn.close()
                return
        except Exception:
            pass
        finally:
            conn.close()

    schema_file = SQL_DIR / "schema_sqlite.sql"
    seed_file = SQL_DIR / "seed_sqlite.sql"

    if not schema_file.exists():
        raise FileNotFoundError(f"Missing schema file: {schema_file}")

    schema_sql = schema_file.read_text(encoding="utf-8")
    seed_sql = seed_file.read_text(encoding="utf-8") if seed_file.exists() else ""

    conn = get_sqlite_conn()
    cur = conn.cursor()
    try:
        cur.executescript(schema_sql)
        if seed_sql.strip():
            cur.executescript(seed_sql)
        conn.commit()
    finally:
        conn.close()


def _init_postgres(force: bool = False) -> None:
    schema_file = SQL_DIR / "schema.sql"
    seed_file = SQL_DIR / "seed.sql"
    tx_file = SQL_DIR / "transactions.sql"

    schema_sql = schema_file.read_text(encoding="utf-8")
    seed_sql = seed_file.read_text(encoding="utf-8") if seed_file.exists() else ""
    tx_sql = tx_file.read_text(encoding="utf-8") if tx_file.exists() else ""

    with PG_POOL.connection() as conn:
        with conn.cursor() as cur:
            if not force:
                cur.execute("SELECT to_regclass('realms');")
                res = cur.fetchone()
                if res and res["to_regclass"]:
                    return

            cur.execute(schema_sql)
            if tx_sql.strip():
                cur.execute(tx_sql)
            if seed_sql.strip():
                cur.execute(seed_sql)
            conn.commit()


def get_engine_telemetry() -> Dict[str, Any]:
    """Returns runtime telemetry for the active database engine."""
    info: Dict[str, Any] = {
        "active_backend": ACTIVE_BACKEND,
        "is_postgres": is_postgres(),
    }
    if is_postgres():
        info["pool_min"] = PG_POOL.min_size
        info["pool_max"] = PG_POOL.max_size
        info["dsn_masked"] = PG_DSN.split("@")[-1] if "@" in PG_DSN else "local"
        info["locking_mode"] = "Row-Level Multi-Version Concurrency (MVCC + FOR UPDATE)"
    else:
        info["db_file"] = str(DB_PATH)
        info["file_size_bytes"] = DB_PATH.stat().st_size if DB_PATH.exists() else 0
        info["journal_mode"] = "WAL (Write-Ahead Logging)"
        info["locking_mode"] = "Database-Level 2PL (BEGIN IMMEDIATE Serialization)"
    return info
