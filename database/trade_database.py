import sqlite3
from pathlib import Path
from typing import Optional


DEFAULT_DB_PATH = Path("database") / "trades.db"


class TradeDatabase:
    """Persistent SQLite storage for settled trade records."""

    def __init__(self, db_path=DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as conn:
            conn.execute(
                """
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
                """
            )
            conn.commit()

    def add_trade(self, record) -> bool:
        """Store a trade. Returns False if contract already exists."""

        with self._connect() as conn:
            cursor = conn.execute(
                """
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
                """,
                (
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
                ),
            )
            conn.commit()
            return cursor.rowcount == 1

    def get_trade(self, contract_id: str) -> Optional[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            row = conn.execute(
                "SELECT * FROM trades WHERE contract_id = ?",
                (str(contract_id),),
            ).fetchone()

            return dict(row) if row else None

    def all_trades(self):
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                "SELECT * FROM trades ORDER BY settled_at ASC"
            ).fetchall()

            return [dict(row) for row in rows]

    def count(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM trades"
            ).fetchone()[0]

    def total_profit(self):
        with self._connect() as conn:
            result = conn.execute(
                "SELECT COALESCE(SUM(profit), 0) FROM trades"
            ).fetchone()[0]

            return float(result)

    def close(self):
        """Compatibility method for future connection-pool implementations."""
        return None
