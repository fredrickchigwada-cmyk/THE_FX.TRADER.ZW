from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


BASE_DIR = Path("database")
DB_PATH = BASE_DIR / "app.db"
BACKUP_DIR = BASE_DIR / "backups"
SETTINGS_PATH = BASE_DIR / "settings.json"


class AppDatabase:
    """Central persistent database layer for THE_FX.TRADER.ZW."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    contract_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    entry_price REAL,
                    settlement_price REAL,
                    stake REAL,
                    payout REAL,
                    profit REAL,
                    profit_percentage REAL,
                    status TEXT NOT NULL,
                    result TEXT NOT NULL,
                    settled_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT NOT NULL,
                    severity TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS database_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()

    # -------------------------
    # Trades
    # -------------------------

    def add_trade(self, record: Any) -> bool:
        values = (
            record.contract_id,
            record.symbol,
            record.side,
            record.entry_price,
            record.settlement_price,
            record.stake,
            record.payout,
            record.profit,
            record.profit_percentage,
            record.status,
            record.result,
            record.settled_at,
        )

        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO trades (
                    contract_id,
                    symbol,
                    side,
                    entry_price,
                    settlement_price,
                    stake,
                    payout,
                    profit,
                    profit_percentage,
                    status,
                    result,
                    settled_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

            conn.commit()
            return cursor.rowcount == 1

    def get_trade(self, contract_id: str) -> Optional[dict]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM trades WHERE contract_id = ?",
                (str(contract_id),),
            ).fetchone()

        return dict(row) if row else None

    def all_trades(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM trades ORDER BY settled_at ASC"
            ).fetchall()

        return [dict(row) for row in rows]

    def trade_count(self) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS count FROM trades"
            ).fetchone()

        return int(row["count"])

    def total_profit(self) -> float:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(profit), 0) AS total FROM trades"
            ).fetchone()

        return float(row["total"])

    # -------------------------
    # Alerts
    # -------------------------

    def add_alert(
        self,
        alert_type: str,
        message: str,
        symbol: str = "XAUUSD",
        severity: str = "INFO",
    ) -> int:
        created_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            cursor = conn.execute("""
                INSERT INTO alerts (
                    alert_type,
                    symbol,
                    message,
                    severity,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                alert_type,
                symbol,
                message,
                severity,
                created_at,
            ))

            conn.commit()
            return int(cursor.lastrowid)

    def all_alerts(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM alerts ORDER BY created_at ASC"
            ).fetchall()

        return [dict(row) for row in rows]

    # -------------------------
    # Events / integrity
    # -------------------------

    def log_event(self, event_type: str, details: dict | None = None):
        created_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as conn:
            conn.execute("""
                INSERT INTO database_events (
                    event_type,
                    details,
                    created_at
                )
                VALUES (?, ?, ?)
            """, (
                event_type,
                json.dumps(details or {}),
                created_at,
            ))

            conn.commit()

    def integrity_check(self) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "PRAGMA integrity_check"
            ).fetchone()

        return row is not None and row[0] == "ok"

    def table_counts(self) -> dict:
        with self._connect() as conn:
            trades = conn.execute(
                "SELECT COUNT(*) FROM trades"
            ).fetchone()[0]

            alerts = conn.execute(
                "SELECT COUNT(*) FROM alerts"
            ).fetchone()[0]

            events = conn.execute(
                "SELECT COUNT(*) FROM database_events"
            ).fetchone()[0]

        return {
            "trades": int(trades),
            "alerts": int(alerts),
            "events": int(events),
        }

    # -------------------------
    # Backup / recovery
    # -------------------------

    def backup(self, destination: str | Path | None = None) -> Path:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        if destination is None:
            stamp = datetime.now(timezone.utc).strftime(
                "%Y%m%d_%H%M%S"
            )
            destination = BACKUP_DIR / f"app_{stamp}.db"
        else:
            destination = Path(destination)

        destination.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as source:
            with sqlite3.connect(destination) as target:
                source.backup(target)

        return destination

    def close(self):
        return None


class SettingsDatabase:
    """Persistent JSON settings validation layer."""

    def __init__(self, path: str | Path = SETTINGS_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, settings: dict):
        payload = dict(settings)
        payload["updated_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        temp = self.path.with_suffix(".tmp")

        with temp.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        temp.replace(self.path)

    def load(self) -> dict:
        if not self.path.exists():
            return {}

        with self.path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
