"""
THE_FX.TRADER.BOT.ZW
Stage 12 — Safe Auto Start

Startup sequence:
1. Load configuration
2. Check safety state
3. Connect to Deriv
4. Start monitoring/watchdog
5. Begin signal analysis

No automatic trading.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class StartupStatus:
    started: bool = False
    connected: bool = False
    monitoring: bool = False
    stopped: bool = False
    last_error: str = ""


class AutoStartController:

    def __init__(
        self,
        connect_fn: Callable[[], bool],
        monitor_fn: Optional[Callable[[], None]] = None,
    ):
        self.connect_fn = connect_fn
        self.monitor_fn = monitor_fn

        self.status = StartupStatus()

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

    def start(self) -> bool:
        with self._lock:

            if self.status.started:
                return False

            self.status = StartupStatus(started=True)
            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._startup,
                name="FXTraderAutoStart",
                daemon=True,
            )

            self._thread.start()

            return True

    def _startup(self) -> None:

        try:
            connected = bool(self.connect_fn())

            with self._lock:
                self.status.connected = connected

            if not connected:
                with self._lock:
                    self.status.last_error = "DERIV_CONNECTION_FAILED"
                return

            with self._lock:
                self.status.monitoring = True

            if self.monitor_fn:
                self.monitor_fn()

        except Exception as exc:
            with self._lock:
                self.status.last_error = str(exc)

    def stop(self) -> None:

        self._stop_event.set()

        with self._lock:
            self.status.monitoring = False
            self.status.stopped = True
            self.status.started = False

    def snapshot(self) -> StartupStatus:
        with self._lock:
            return StartupStatus(
                started=self.status.started,
                connected=self.status.connected,
                monitoring=self.status.monitoring,
                stopped=self.status.stopped,
                last_error=self.status.last_error,
            )
