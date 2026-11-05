"""
Analytics API Router for Scrolls of Agora.
Exposes the 7 Relational Algebra query suites, query plan telemetry,
and recursive CTE RMT money-laundering tracking.
"""

from fastapi import APIRouter, HTTPException
from src.repositories.analytics_repo import (
    run_analytical_query,
    get_rmt_laundering_graph,
    ban_and_seize_rmt_mule_ring,
    ANALYTICAL_CATALOG,
)

router = APIRouter(tags=["Relational Algebra & Analytics"])


@router.get("/api/analytics/{query_key}")
def api_analytical_query(query_key: str):
    if query_key not in ANALYTICAL_CATALOG:
        raise HTTPException(status_code=404, detail="Query key not found in catalog.")
    return run_analytical_query(query_key)


@router.get("/api/rmt-graph")
def api_rmt_graph():
    return get_rmt_laundering_graph()


@router.post("/api/ban-rmt-ring")
def api_ban_rmt_ring():
    return ban_and_seize_rmt_mule_ring()
