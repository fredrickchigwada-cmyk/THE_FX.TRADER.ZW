"""
THE_FX.TRADER.BOT.ZW
Stage 13 — Signal Journal & Performance

Records signals and measured outcomes.
No automatic trading.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


JOURNAL_FILE = "data/signal_history.json"


@dataclass
class SignalRecord:
    symbol: str
    timeframe: str
    signal: str
    strength: float
    confirmations: int
    entry: Optional[float]
    stop_loss: Optional[float]
    tp1: Optional[float]
    tp2: Optional[float]
    result: str
    timestamp: str
    setup: str = ""
    notes: str = ""


VALID_SIGNALS = {"BUY", "SELL", "WAIT"}
VALID_RESULTS = {
    "PENDING",
    "TP1",
    "TP2",
    "SL",
    "INVALIDATED",
    "EXPIRED",
    "CANCELLED",
}


class SignalJournal:

    def __init__(self, path: str = JOURNAL_FILE):
        self.path = path
        self._lock = threading.RLock()
        self._records: List[SignalRecord] = []

        self._ensure_directory()
        self.load()

    def _ensure_directory(self):
        directory = os.path.dirname(self.path)

        if directory:
            os.makedirs(directory, exist_ok=True)

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def load(self) -> int:
        with self._lock:

            if not os.path.exists(self.path):
                self._records = []
                return 0

            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, list):
                    self._records = []
                    return 0

                records = []

                for item in data:
                    if not isinstance(item, dict):
                        continue

                    try:
                        records.append(
                            SignalRecord(**item)
                        )
                    except TypeError:
                        continue

                self._records = records
                return len(records)

            except (OSError, json.JSONDecodeError):
                self._records = []
                return 0

    def _save(self):
        self._ensure_directory()

        data = [
            asdict(record)
            for record in self._records
        ]

        directory = os.path.dirname(self.path) or "."

        fd, temporary = tempfile.mkstemp(
            prefix=".signal_history_",
            suffix=".tmp",
            dir=directory,
        )

        try:
            with os.fdopen(
                fd,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

                f.flush()
                os.fsync(f.fileno())

            os.replace(temporary, self.path)

        finally:
            if os.path.exists(temporary):
                os.remove(temporary)

    def add(
        self,
        symbol: str,
        timeframe: str,
        signal: str,
        strength: float = 0,
        confirmations: int = 0,
        entry: Optional[float] = None,
        stop_loss: Optional[float] = None,
        tp1: Optional[float] = None,
        tp2: Optional[float] = None,
        result: str = "PENDING",
        setup: str = "",
        notes: str = "",
        timestamp: Optional[str] = None,
    ) -> SignalRecord:

        signal = str(signal).upper()
        result = str(result).upper()

        if signal not in VALID_SIGNALS:
            raise ValueError(
                f"Invalid signal: {signal}"
            )

        if result not in VALID_RESULTS:
            raise ValueError(
                f"Invalid result: {result}"
            )

        record = SignalRecord(
            symbol=str(symbol),
            timeframe=str(timeframe),
            signal=signal,
            strength=float(strength),
            confirmations=int(confirmations),
            entry=entry,
            stop_loss=stop_loss,
            tp1=tp1,
            tp2=tp2,
            result=result,
            timestamp=timestamp or self._timestamp(),
            setup=str(setup),
            notes=str(notes),
        )

        with self._lock:
            self._records.append(record)
            self._save()

        return record

    def update_result(
        self,
        timestamp: str,
        result: str,
        notes: Optional[str] = None,
    ) -> bool:

        result = str(result).upper()

        if result not in VALID_RESULTS:
            raise ValueError(
                f"Invalid result: {result}"
            )

        with self._lock:

            for record in reversed(self._records):

                if record.timestamp == timestamp:
                    record.result = result

                    if notes is not None:
                        record.notes = str(notes)

                    self._save()
                    return True

        return False

    def all(self) -> List[SignalRecord]:
        with self._lock:
            return list(self._records)

    def recent(self, limit: int = 50) -> List[SignalRecord]:
        limit = max(1, int(limit))

        with self._lock:
            return list(self._records[-limit:])[::-1]

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def clear(self):
        with self._lock:
            self._records = []
            self._save()


class PerformanceTracker:

    def __init__(self, journal: SignalJournal):
        self.journal = journal

    def _closed_records(self):
        return [
            r
            for r in self.journal.all()
            if r.signal in {"BUY", "SELL"}
            and r.result in {
                "TP1",
                "TP2",
                "SL",
            }
        ]

    def totals(self) -> Dict[str, int]:

        records = self.journal.all()

        return {
            "total": len(records),
            "buy": sum(
                r.signal == "BUY"
                for r in records
            ),
            "sell": sum(
                r.signal == "SELL"
                for r in records
            ),
            "wait": sum(
                r.signal == "WAIT"
                for r in records
            ),
            "pending": sum(
                r.result == "PENDING"
                for r in records
            ),
            "tp1": sum(
                r.result == "TP1"
                for r in records
            ),
            "tp2": sum(
                r.result == "TP2"
                for r in records
            ),
            "sl": sum(
                r.result == "SL"
                for r in records
            ),
        }

    def win_rate(self) -> Optional[float]:

        records = self._closed_records()

        if not records:
            return None

        wins = sum(
            r.result in {"TP1", "TP2"}
            for r in records
        )

        return (wins / len(records)) * 100.0

    def by_symbol(self) -> Dict[str, Dict[str, int]]:

        output = {}

        for record in self._closed_records():

            symbol = record.symbol

            if symbol not in output:
                output[symbol] = {
                    "signals": 0,
                    "wins": 0,
                    "losses": 0,
                }

            output[symbol]["signals"] += 1

            if record.result in {"TP1", "TP2"}:
                output[symbol]["wins"] += 1
            elif record.result == "SL":
                output[symbol]["losses"] += 1

        return output

    def by_timeframe(self) -> Dict[str, Dict[str, int]]:

        output = {}

        for record in self._closed_records():

            timeframe = record.timeframe

            if timeframe not in output:
                output[timeframe] = {
                    "signals": 0,
                    "wins": 0,
                    "losses": 0,
                }

            output[timeframe]["signals"] += 1

            if record.result in {"TP1", "TP2"}:
                output[timeframe]["wins"] += 1
            elif record.result == "SL":
                output[timeframe]["losses"] += 1

        return output

    def by_direction(self) -> Dict[str, Dict[str, int]]:

        output = {
            "BUY": {
                "signals": 0,
                "wins": 0,
                "losses": 0,
            },
            "SELL": {
                "signals": 0,
                "wins": 0,
                "losses": 0,
            },
        }

        for record in self._closed_records():

            direction = record.signal

            output[direction]["signals"] += 1

            if record.result in {"TP1", "TP2"}:
                output[direction]["wins"] += 1
            elif record.result == "SL":
                output[direction]["losses"] += 1

        return output

    def summary(self) -> Dict:

        totals = self.totals()

        return {
            "totals": totals,
            "win_rate": self.win_rate(),
            "by_symbol": self.by_symbol(),
            "by_timeframe": self.by_timeframe(),
            "by_direction": self.by_direction(),
        }
