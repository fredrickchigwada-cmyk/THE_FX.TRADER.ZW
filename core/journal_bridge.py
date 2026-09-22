"""
Bridge between signal objects and the Stage 13 journal.
"""

from __future__ import annotations

from typing import Any

from .signal_journal import SignalJournal


class JournalBridge:

    def __init__(self, journal=None):
        self.journal = journal or SignalJournal()

    @staticmethod
    def _get(obj: Any, name: str, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)

        return getattr(obj, name, default)

    def record_signal(self, signal) -> object:

        return self.journal.add(
            symbol=self._get(signal, "symbol", ""),
            timeframe=self._get(signal, "timeframe", ""),
            signal=self._get(signal, "signal", "WAIT"),
            strength=self._get(signal, "strength", 0),
            confirmations=self._get(
                signal,
                "confirmations",
                0,
            ),
            entry=self._get(signal, "entry"),
            stop_loss=self._get(
                signal,
                "stop_loss",
            ),
            tp1=self._get(signal, "tp1"),
            tp2=self._get(signal, "tp2"),
            result="PENDING",
            setup=self._get(
                signal,
                "setup",
                "",
            ),
            notes=self._get(
                signal,
                "explanation",
                "",
            ),
        )
