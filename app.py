"""
Scrolls of Agora (v3.1): Decentralized Tamriel Guild Exchange & Relational Database Workbench.
Entry point for FastAPI application, mounting modular routers and static telemetry assets.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import STATIC_DIR, HOST, PORT
from src.database import init_database, get_engine_telemetry, audit_ledger_integrity
from src.models import (
    BuyoutRequest,
    BidRequest,
    ListItemRequest,
    TemperCraftRequest,
    KioskBidRequest,
    DupeStressRequest,
    MailSendRequest,
    MailClaimRequest,
    RepairRequest,
    SimulateWearRequest,
    P2PTradeRequest,
    LimitOrderRequest,
    AuthLoginRequest,
)
from src.repositories.market_repo import get_market_state, get_item_candles
from src.repositories.transaction_repo import (
    execute_pessimistic_buyout,
    place_escrow_bid,
    list_inventory_item,
    temper_and_enchant_item,
    place_kiosk_bid,
    trigger_weekly_kiosk_flip,
    repair_player_equipment,
    degrade_equipment_durability,
    execute_p2p_trade,
    sweep_expired_listings,
)
from src.repositories.analytics_repo import (
    run_analytical_query,
    get_rmt_laundering_graph,
    ban_and_seize_rmt_mule_ring,
    rollup_realtime_ohlc,
)
from src.repositories.mail_repo import (
    get_player_mailbox,
    send_player_mail,
    claim_mail_attachment,
)
from src.repositories.orderbook_repo import (
    place_limit_order,
    get_orderbook_depth,
)
from src.services.dupe_bench_service import run_dupe_race_condition_attack
from src.services.broadcaster import broadcaster
from src.services.scheduler import daemon
from src.auth import create_player_token, verify_player_token

# Routers
from src.routers import market, transactions, analytics, benchmarks, mail, orderbook, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize schema & seed on startup if database is not already initialized
    init_database(force=False)
    daemon.start()
    yield
    await daemon.stop()


app = FastAPI(
    title="Scrolls of Agora — Relational Database Exchange & Telemetry Console",
    description="Decentralized MMORPG Guild Kiosk Economy, ACID Transactions & Concurrency Benchmark",
    version="3.2.0",
    lifespan=lifespan,
)

# Mount Routers
app.include_router(market.router)
app.include_router(transactions.router)
app.include_router(analytics.router)
app.include_router(benchmarks.router)
app.include_router(mail.router)
app.include_router(orderbook.router)
app.include_router(auth.router)


@app.websocket("/ws/feed")
async def websocket_telemetry_feed(websocket: WebSocket):
    """Real-time push notification stream for market orderbooks, trades, and parcel alerts."""
    await broadcaster.connect(websocket)
    try:
        while True:
            _ = await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        await broadcaster.disconnect(websocket)

# Mount Static Files (CSS, JS, Assets)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_dashboard():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)


# -----------------------------------------------------------------------------
# Re-exported test harnesses and aliases for backward-compatibility with test suites
# -----------------------------------------------------------------------------
def init_and_seed_database():
    init_database(force=True)


api_place_bid = transactions.api_bid
api_temper_and_enchant_item = transactions.api_temper_item
api_place_kiosk_bid = transactions.api_kiosk_bid
api_trigger_weekly_kiosk_flip = transactions.api_kiosk_flip


if __name__ == "__main__":
    import uvicorn
    # Auto-initialize database on direct CLI run
    init_database(force=False)
    telemetry = get_engine_telemetry()
    print("=" * 72)
    print("  SCROLLS OF AGORA (v3.1) — RELATIONAL DATABASE WORKBENCH")
    print(f"  Active Engine: {telemetry['active_backend']}")
    print(f"  Server URL:    http://{HOST}:{PORT}")
    print("=" * 72)
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)
