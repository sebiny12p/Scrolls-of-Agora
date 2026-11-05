"""
Pytest configuration and database fixtures for Scrolls of Agora.
"""

import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database import init_database


@pytest.fixture(autouse=True)
def reset_db_state():
    """Re-initializes the database before each test run for idempotent test isolation."""
    init_database(force=True)
    yield
