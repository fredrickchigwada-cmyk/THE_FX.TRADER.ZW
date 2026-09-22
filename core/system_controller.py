"""
THE_FX.TRADER.BOT.ZW
Stage 12 — System Controller

Central safe controller for startup, watchdog and emergency STOP.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .watchdog import SafetyController, Watchdog


@dataclass
class SystemStatus:
    running: bool
    connected: bool
    healthy: bool
    stale: bool
    emergency_stop: bool
    reconnects: int
    checks: int
    uptime: float


class SystemController:

    def __init__(
        self,
        connection_check,
        reconnect=None,
        watchdog_interval=10.0,
        stale_after=30.0,
    ):
        self.safety = SafetyController()

        self.started_at: Optional[float] = None

        self.watchdog = Watchdog(
            check_fn=connection_check,
            reconnect_fn=reconnect,
            interval=watchdog_interval,
            stale_after=stale_after,
        )

    def start(self) -> bool:

        if self.safety.is_stopped():
            return False

        self.started_at = time.time()

        return self.watchdog.start()

    def stop(self) -> None:
        self.watchdog.stop()

    def emergency_stop(self) -> None:
        """
        Stops signal monitoring.

        IMPORTANT:
        This does not place, modify or close trades.
        """
        self.safety.stop()
        self.watchdog.stop()

    def reset_emergency_stop(self) -> None:
        self.safety.reset()

    def can_analyze(self) -> bool:
        status = self.watchdog.snapshot()

        return (
            not self.safety.is_stopped()
            and status.running
            and status.healthy
            and not status.stale
        )

    def status(self) -> SystemStatus:

        wd = self.watchdog.snapshot()

        uptime = 0.0

        if self.started_at:
            uptime = max(0.0, time.time() - self.started_at)

        return SystemStatus(
            running=wd.running,
            connected=wd.connected,
            healthy=wd.healthy,
            stale=wd.stale,
            emergency_stop=self.safety.is_stopped(),
            reconnects=wd.reconnects,
            checks=wd.checks,
            uptime=uptime,
        )
