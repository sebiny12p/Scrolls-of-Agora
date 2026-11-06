"""
Configuration and Environment Settings for Scrolls of Agora.
Handles database paths, PostgreSQL connection pool options, and application domain constants.
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

# Domain Economic & Crafting Constants (Eliminating Magic Numbers)
FORGE_FEE_GOLD = 3500
FORGE_MAX_TEMPER_TIER = 5
FORGE_POWER_BOOST_PER_TIER = 95
FORGE_REAGENT_ITEM_IDS = (5011, 5012)
FORGE_REAGENT_QTY_REQUIRED = 2

MIN_ESCROW_BID_INCREMENT_PCT = 0.05
MAX_KIOSK_TAX_RATE_BPS = 2500

RMT_ANOMALY_MULTIPLIER = 15
SYSTEM_SINK_ACCOUNT = "SYSTEM_SINK"

# Systems Upgrades: Capacity, Durability, Mail, Orderbook & Auth
DEFAULT_MAX_BAG_SLOTS = 20
REPAIR_COST_PER_DURABILITY = 5
MAIL_EXPIRATION_DAYS = 30
SECRET_KEY = os.environ.get("AGORA_SECRET_KEY", "agora-cryptographic-invariance-salt-2026")
ENABLE_BACKGROUND_SCHEDULER = os.environ.get("AGORA_ENABLE_SCHEDULER", "1") in ("1", "true", "True")
