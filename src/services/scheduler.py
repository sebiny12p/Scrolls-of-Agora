"""
Asynchronous Background Scheduler & Automation Daemon for Scrolls of Agora.
Runs continuous background jobs:
  1. Expired listing sweeper (returns items to sellers via Mail)
  2. Real-time OHLC candlestick aggregation roll-up
  3. Real-time market telemetry WebSocket heartbeat
"""

import asyncio
import logging
from typing import Optional
from src.config import ENABLE_BACKGROUND_SCHEDULER
from src.services.broadcaster import broadcaster

logger = logging.getLogger("agora.scheduler")


class AgoraBackgroundDaemon:
    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def start(self) -> None:
        if not ENABLE_BACKGROUND_SCHEDULER:
            return
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        from src.repositories.transaction_repo import sweep_expired_listings
        from src.repositories.analytics_repo import rollup_realtime_ohlc
        from src.database import get_engine_telemetry

        tick = 0
        while self._running:
            try:
                await asyncio.sleep(10)
                tick += 1

                # Heartbeat every 10s
                telemetry = get_engine_telemetry()
                await broadcaster.broadcast("HEARTBEAT", telemetry)

                # Sweep expired listings every 30s
                if tick % 3 == 0:
                    try:
                        res = sweep_expired_listings()
                        if res.get("swept_count", 0) > 0:
                            logger.info(f"Background sweeper: {res['message']}")
                    except Exception as e:
                        logger.error(f"Error in expired listing sweeper: {e}")

                # Roll-up OHLC every 60s
                if tick % 6 == 0:
                    try:
                        rollup_realtime_ohlc()
                    except Exception as e:
                        logger.error(f"Error in OHLC roll-up: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in background daemon: {e}")
                await asyncio.sleep(5)


daemon = AgoraBackgroundDaemon()
