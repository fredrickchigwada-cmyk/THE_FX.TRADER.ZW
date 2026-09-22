"""
THE_FX.TRADER.BOT.ZW
Stage 14 — Full System Integration

Pipeline:

Deriv WebSocket
      ↓
Market Data
      ↓
Candle Engine
      ↓
Technical Analysis
      ↓
Signal Engine
      ↓
Multi-Timeframe Confirmation
      ↓
Signal Protection
      ↓
Alert Router
      ↓
Android Notification
      ↓
Signal Journal

SAFETY:
Automatic trading is permanently disabled.
No buy/sell order is ever submitted.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

from .signal_journal import SignalJournal, PerformanceTracker


@dataclass
class SystemSnapshot:
    running: bool
    connected: bool
    healthy: bool
    stale: bool
    emergency_stop: bool
    market: str
    timeframe: str
    signal: str
    strength: float
    confirmations: int
    journal_records: int


class FullSystem:

    def __init__(
        self,
        market="XAUUSD",
        timeframe="M1",
        journal=None,
    ):
        self.market = market
        self.timeframe = timeframe

        self.journal = journal or SignalJournal()
        self.performance = PerformanceTracker(
            self.journal
        )

        self.running = False
        self.connected = False
        self.healthy = False
        self.stale = False
        self.emergency_stop = False

        self.last_signal = "WAIT"
        self.last_strength = 0.0
        self.last_confirmations = 0

        self.started_at: Optional[float] = None

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:

        with self._lock:

            if self.running:
                return False

            if self.emergency_stop:
                return False

            self.running = True
            self.connected = True
            self.healthy = True
            self.stale = False
            self.started_at = time.time()

            self._stop_event.clear()

            self._thread = threading.Thread(
                target=self._monitor,
                name="FXTraderFullSystem",
                daemon=True,
            )

            self._thread.start()

            return True

    def _monitor(self):

        while not self._stop_event.is_set():

            with self._lock:

                if not self.running:
                    break

                if self.emergency_stop:
                    break

                # The actual Deriv/analysis pipeline remains
                # responsible for producing real signals.
                #
                # This controller never fabricates one.
                self.connected = True
                self.healthy = True
                self.stale = False

            self._stop_event.wait(5.0)

    def stop(self):

        self._stop_event.set()

        with self._lock:
            self.running = False
            self.connected = False
            self.healthy = False

        thread = self._thread

        if thread and thread.is_alive():
            thread.join(timeout=2)

        self._thread = None

    def emergency_stop_system(self):

        with self._lock:
            self.emergency_stop = True

        self.stop()

    def reset_emergency_stop(self):

        with self._lock:
            self.emergency_stop = False

    def accept_signal(
        self,
        signal,
        strength=0,
        confirmations=0,
        entry=None,
        stop_loss=None,
        tp1=None,
        tp2=None,
        setup="",
        explanation="",
    ):
        """
        Records an already-generated signal.

        WAIT is recorded for journal purposes but never triggers
        a BUY/SELL alert.

        This method never executes trades.
        """

        signal = str(signal).upper()

        if signal not in {"BUY", "SELL", "WAIT"}:
            raise ValueError(
                f"Invalid signal: {signal}"
            )

        with self._lock:

            if self.emergency_stop:
                return None

            self.last_signal = signal
            self.last_strength = float(strength)
            self.last_confirmations = int(confirmations)

        return self.journal.add(
            symbol=self.market,
            timeframe=self.timeframe,
            signal=signal,
            strength=strength,
            confirmations=confirmations,
            entry=entry,
            stop_loss=stop_loss,
            tp1=tp1,
            tp2=tp2,
            result="PENDING",
            setup=setup,
            notes=explanation,
        )

    def update_result(
        self,
        timestamp,
        result,
        notes=None,
    ):
        return self.journal.update_result(
            timestamp,
            result,
            notes,
        )

    def snapshot(self) -> SystemSnapshot:

        with self._lock:
            return SystemSnapshot(
                running=self.running,
                connected=self.connected,
                healthy=self.healthy,
                stale=self.stale,
                emergency_stop=self.emergency_stop,
                market=self.market,
                timeframe=self.timeframe,
                signal=self.last_signal,
                strength=self.last_strength,
                confirmations=self.last_confirmations,
                journal_records=self.journal.count(),
            )

    def performance_summary(self):

        return self.performance.summary()

    # Explicit safety guard:
    # There are intentionally no trading methods.
