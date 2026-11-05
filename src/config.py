"""
Configuration and Environment Settings for Scrolls of Agora.
Handles database paths, PostgreSQL connection pool options, and application defaults.
"""

import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_DIR = PROJECT_ROOT / "sql"
STATIC_DIR = PROJECT_ROOT / "static"
DOCS_DIR = PROJECT_ROOT / "docs"

# SQLite Database Location
DEFAULT_SQLITE_PATH = PROJECT_ROOT / "scrolls_of_agora.db"
DB_PATH = Path(os.environ.get("AGORA_DB_PATH", str(DEFAULT_SQLITE_PATH)))

# PostgreSQL Connection DSN (defaults to local docker container)
PG_DSN = os.environ.get(
    "AGORA_PG_DSN",
    "postgresql://agora:ScrollsOfAgora!2026@127.0.0.1:5435/scrolls_of_agora",
)

# Server Config
HOST = os.environ.get("AGORA_HOST", "127.0.0.1")
PORT = int(os.environ.get("AGORA_PORT", "8090"))
DEBUG = os.environ.get("AGORA_DEBUG", "0") in ("1", "true", "True")
