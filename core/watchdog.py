"""
THE_FX.TRADER.BOT.ZW
Stage 12 — Connection / Data Watchdog

Safety:
- Signal-only
- No order placement
- No order modification
- No order closing
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class WatchdogStatus:
    running: bool = False
    connected: bool = False
    healthy: bool = False
    stale: bool = False
    reconnects: int = 0
    checks: int = 0
    last_check: float = 0.0
    last_healthy: float = 0.0
    last_error: str = ""


class Watchdog:
    """
    Monitors a connection/data source.

    check_fn must return:
        True  -> healthy
        False -> unhealthy
    """

    def __init__(
        self,
        check_fn: Callable[[], bool],
        reconnect_fn: Optional[Callable[[], bool]] = None,
        interval: float = 10.0,
        stale_after: float = 30.0,
        reconnect_delay: float = 3.0,
    ):
        self.check_fn = check_fn
        self.reconnect_fn = reconnect_fn

        self.interval = max(1.0, float(interval))
        self.stale_after = max(self.interval, float(stale_after))
        self.reconnect_delay = max(0.0, float(reconnect_delay))

        self.status = WatchdogStatus()

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def start(self) -> bool:
        with self._lock:
            if self.status.running:
                return False

            self._stop_event.clear()
            self.status.running = True

            self._thread = threading.Thread(
                target=self._run,
                name="FXTraderWatchdog",
                daemon=True,
            )
            self._thread.start()

            return True

    def stop(self) -> bool:
        with self._lock:
            if not self.status.running:
                return False

            self._stop_event.set()
            self.status.running = False

        thread = self._thread

        if thread and thread.is_alive():
            thread.join(timeout=2.0)

        self._thread = None
        return True

    def _run(self) -> None:
        while not self._stop_event.is_set():

            self.check_once()

            self._stop_event.wait(self.interval)

    def check_once(self) -> bool:
        now = time.time()

        with self._lock:
            self.status.checks += 1
            self.status.last_check = now

        healthy = False

        try:
            healthy = bool(self.check_fn())

        except Exception as exc:
            with self._lock:
                self.status.last_error = str(exc)
            healthy = False

        with self._lock:
            self.status.healthy = healthy
            self.status.connected = healthy

            if healthy:
                self.status.stale = False
                self.status.last_healthy = now
                self.status.last_error = ""
                return True

            last_healthy = self.status.last_healthy

            if last_healthy <= 0:
                self.status.stale = True
            else:
                self.status.stale = (
                    now - last_healthy >= self.stale_after
                )

        if not healthy:
            self._attempt_reconnect()

        return False

    def _attempt_reconnect(self) -> bool:
        if self.reconnect_fn is None:
            return False

        if self.reconnect_delay:
            if self._stop_event.wait(self.reconnect_delay):
                return False

        try:
            success = bool(self.reconnect_fn())

        except Exception as exc:
            with self._lock:
                self.status.last_error = str(exc)
            return False

        if success:
            with self._lock:
                self.status.reconnects += 1
                self.status.connected = True
                self.status.healthy = True
                self.status.stale = False
                self.status.last_healthy = time.time()
                self.status.last_error = ""

        return success

    def snapshot(self) -> WatchdogStatus:
        with self._lock:
            return WatchdogStatus(
                running=self.status.running,
                connected=self.status.connected,
                healthy=self.status.healthy,
                stale=self.status.stale,
                reconnects=self.status.reconnects,
                checks=self.status.checks,
                last_check=self.status.last_check,
                last_healthy=self.status.last_healthy,
                last_error=self.status.last_error,
            )


class SafetyController:
    """
    Global monitoring safety switch.

    This does NOT execute or close trades.
    It only controls whether the signal system is allowed to operate.
    """

    def __init__(self):
        self._stopped = False
        self._lock = threading.RLock()

    def stop(self) -> None:
        with self._lock:
            self._stopped = True

    def reset(self) -> None:
        with self._lock:
            self._stopped = False

    def is_stopped(self) -> bool:
        with self._lock:
            return self._stopped

    def allow_analysis(self) -> bool:
        with self._lock:
            return not self._stopped
