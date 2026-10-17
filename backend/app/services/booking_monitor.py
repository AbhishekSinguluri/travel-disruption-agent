import asyncio
import logging
import datetime
import os
from app.db.repositories import get_booking_repository
from app.api.monitoring import check_monitor

logger = logging.getLogger(__name__)

class BookingMonitorService:
    def __init__(self):
        self.enabled = True
        self.interval_seconds = int(os.getenv("BOOKING_MONITOR_INTERVAL_SECONDS", 30))
        if self.interval_seconds < 30:
            self.interval_seconds = 30
            
        self.is_running = False
        self._task = None
        self.last_check_at = None
        self.next_check_at = None
        self.last_check_status = None
        self.last_error = None
        
    def start(self):
        if self._task is None or self._task.done():
            self.is_running = True
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("[BookingMonitor] Automatic monitoring started")
            logger.info(f"[BookingMonitor] Interval: {self.interval_seconds} seconds")

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("[BookingMonitor] Automatic monitoring stopped")

    def configure(self, enabled: bool, interval_seconds: int = None):
        self.enabled = enabled
        if interval_seconds is not None:
            if interval_seconds < 30:
                interval_seconds = 30
            self.interval_seconds = interval_seconds
            logger.info(f"[BookingMonitor] Interval updated to: {self.interval_seconds} seconds")
            
        if self.enabled and not self.is_running:
            self.start()
        elif not self.enabled:
            # We don't stop the loop entirely so it can be re-enabled without restart,
            # but it will just sleep in the loop.
            pass

    async def _monitor_loop(self):
        while self.is_running:
            if not self.enabled:
                self.next_check_at = None
                await asyncio.sleep(1)
                continue
                
            try:
                repo = get_booking_repository()
                # Use hasattr check for repo method or fallback to mock DB
                active_monitors = []
                if hasattr(repo, "monitors"):
                    active_monitors = [m_id for m_id, m in repo.monitors.items() if m.get("status") == "ACTIVE"]
                else:
                    from app.services.mock_db import MOCK_DB
                    monitors = MOCK_DB.get("monitoring", {})
                    active_monitors = [m_id for m_id, m in monitors.items() if m.get("status") == "ACTIVE"]
                
                logger.info(f"[BookingMonitor] Active monitors: {len(active_monitors)}")
                self.last_check_at = datetime.datetime.now().isoformat()
                
                for m_id in active_monitors:
                    logger.info(f"[BookingMonitor] Checking monitor {m_id}")
                    try:
                        result = await check_monitor(m_id)
                        if result.get("status") == "change_detected":
                            logger.info(f"[BookingMonitor] Change detected: {result.get('alert', {}).get('alert_type')}")
                            logger.info("[BookingMonitor] Alert created")
                        elif result.get("status") == "no_change":
                            logger.info("[BookingMonitor] No changes")
                        else:
                            logger.info(f"[BookingMonitor] Result: {result}")
                    except Exception as ex:
                        logger.error(f"[BookingMonitor] Error checking monitor {m_id}: {ex}")
                        self.last_error = str(ex)
                        
                self.last_check_status = "success"
                self.last_error = None
                
            except Exception as e:
                logger.error(f"[BookingMonitor] Loop error: {e}")
                self.last_check_status = "error"
                self.last_error = str(e)
                
            self.next_check_at = (datetime.datetime.now() + datetime.timedelta(seconds=self.interval_seconds)).isoformat()
            
            # Sleep in 1-second chunks so we can interrupt it or pick up config changes faster
            slept = 0
            while slept < self.interval_seconds and self.is_running and self.enabled:
                await asyncio.sleep(1)
                slept += 1

monitor_service = BookingMonitorService()

def get_monitor_service():
    return monitor_service
