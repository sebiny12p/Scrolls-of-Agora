"""
Benchmarks & Database Maintenance API Router for Scrolls of Agora.
Handles the multi-threaded Anti-Dupe stress test and database reset operations.
"""

from fastapi import APIRouter
from src.models import DupeStressRequest
from src.services.dupe_bench_service import run_dupe_race_condition_attack
from src.database import init_database

router = APIRouter(tags=["Benchmarks & Admin"])


@router.post("/api/stress-test-dupe")
def api_stress_test_dupe(req: DupeStressRequest):
    return run_dupe_race_condition_attack(req.concurrent_threads, req.locking_mode)


@router.post("/api/reset")
def api_reset_economy():
    init_database(force=True)
    return {"success": True, "message": "Database re-initialized from SQL schema & seed files."}
