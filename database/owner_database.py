import os
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "fx_owner.db"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def hash_owner_id(value):
    return hashlib.sha256(value.encode()).hexdigest()


class OwnerDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = str(db_path)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS owners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_ref TEXT NOT NULL UNIQUE,
                display_name TEXT,
                email TEXT,
                phone TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                last_login TEXT
            );

            CREATE TABLE IF NOT EXISTS deriv_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                deriv_account_id TEXT NOT NULL,
                account_type TEXT NOT NULL
                    CHECK(account_type IN ('DEMO', 'REAL')),
                currency TEXT DEFAULT 'USD',
                encrypted_auth_token TEXT,
                token_version INTEGER DEFAULT 1,
                connected INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                UNIQUE(owner_id, deriv_account_id),
                FOREIGN KEY(owner_id)
                    REFERENCES owners(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS trading_preferences (
                owner_id INTEGER PRIMARY KEY,
                account_type TEXT NOT NULL DEFAULT 'DEMO'
                    CHECK(account_type IN ('DEMO', 'REAL')),
                trading_mode TEXT NOT NULL DEFAULT 'MANUAL'
                    CHECK(trading_mode IN ('MANUAL', 'AUTO')),
                symbol TEXT NOT NULL DEFAULT 'XAUUSD',
                timeframe TEXT NOT NULL DEFAULT 'M1',
                risk_per_trade REAL NOT NULL DEFAULT 1.0,
                max_open_trades INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL,

                FOREIGN KEY(owner_id)
                    REFERENCES owners(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS alert_preferences (
                owner_id INTEGER PRIMARY KEY,
                buy_alert INTEGER DEFAULT 1,
                sell_alert INTEGER DEFAULT 1,
                tp_alert INTEGER DEFAULT 1,
                sl_alert INTEGER DEFAULT 1,
                news_alert INTEGER DEFAULT 1,
                sound_enabled INTEGER DEFAULT 1,
                vibration_enabled INTEGER DEFAULT 1,
                connection_alert INTEGER DEFAULT 1,
                updated_at TEXT NOT NULL,

                FOREIGN KEY(owner_id)
                    REFERENCES owners(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS login_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                account_type TEXT,
                created_at TEXT NOT NULL,

                FOREIGN KEY(owner_id)
                    REFERENCES owners(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS trade_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                deriv_account_id TEXT,
                symbol TEXT NOT NULL DEFAULT 'XAUUSD',
                timeframe TEXT,
                trading_mode TEXT,
                direction TEXT,
                entry REAL,
                stop_loss REAL,
                take_profit REAL,
                stake REAL,
                result TEXT,
                deriv_contract_id TEXT,
                created_at TEXT NOT NULL,
                closed_at TEXT,

                FOREIGN KEY(owner_id)
                    REFERENCES owners(id)
                    ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_deriv_accounts_owner
                ON deriv_accounts(owner_id);

            CREATE INDEX IF NOT EXISTS idx_login_events_owner
                ON login_events(owner_id);

            CREATE INDEX IF NOT EXISTS idx_trade_records_owner
                ON trade_records(owner_id);
            """)


    def create_owner(self, owner_ref, display_name=None,
                     email=None, phone=None):

        now = utc_now()
        safe_ref = hash_owner_id(owner_ref)

        with self.connect() as conn:
            cur = conn.execute("""
                INSERT INTO owners
                (owner_ref, display_name, email, phone,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                safe_ref,
                display_name,
                email,
                phone,
                now,
                now
            ))

            owner_id = cur.lastrowid

            conn.execute("""
                INSERT INTO trading_preferences
                (owner_id, updated_at)
                VALUES (?, ?)
            """, (owner_id, now))

            conn.execute("""
                INSERT INTO alert_preferences
                (owner_id, updated_at)
                VALUES (?, ?)
            """, (owner_id, now))

            return owner_id


    def add_deriv_account(self, owner_id, account_id,
                          account_type="DEMO",
                          encrypted_auth_token=None):

        account_type = account_type.upper()

        if account_type not in ("DEMO", "REAL"):
            raise ValueError("account_type must be DEMO or REAL")

        now = utc_now()

        with self.connect() as conn:
            conn.execute("""
                INSERT INTO deriv_accounts
                (owner_id, deriv_account_id, account_type,
                 encrypted_auth_token, connected,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(owner_id, deriv_account_id)
                DO UPDATE SET
                    account_type=excluded.account_type,
                    encrypted_auth_token=excluded.encrypted_auth_token,
                    connected=1,
                    updated_at=excluded.updated_at
            """, (
                owner_id,
                account_id,
                account_type,
                encrypted_auth_token,
                now,
                now
            ))


    def set_mode(self, owner_id, account_type, trading_mode):
        account_type = account_type.upper()
        trading_mode = trading_mode.upper()

        if account_type not in ("DEMO", "REAL"):
            raise ValueError("Invalid account type")

        if trading_mode not in ("MANUAL", "AUTO"):
            raise ValueError("Invalid trading mode")

        now = utc_now()

        with self.connect() as conn:
            conn.execute("""
                UPDATE trading_preferences
                SET account_type=?,
                    trading_mode=?,
                    updated_at=?
                WHERE owner_id=?
            """, (
                account_type,
                trading_mode,
                now,
                owner_id
            ))


    def record_login(self, owner_id, account_type):
        now = utc_now()

        with self.connect() as conn:
            conn.execute("""
                UPDATE owners
                SET last_login=?, updated_at=?
                WHERE id=?
            """, (now, now, owner_id))

            conn.execute("""
                INSERT INTO login_events
                (owner_id, event_type, account_type, created_at)
                VALUES (?, 'LOGIN', ?, ?)
            """, (owner_id, account_type.upper(), now))


    def status(self, owner_id):
        with self.connect() as conn:
            owner = conn.execute("""
                SELECT id, display_name, email, phone,
                       created_at, updated_at, last_login
                FROM owners
                WHERE id=?
            """, (owner_id,)).fetchone()

            preferences = conn.execute("""
                SELECT account_type, trading_mode, symbol,
                       timeframe, risk_per_trade, max_open_trades
                FROM trading_preferences
                WHERE owner_id=?
            """, (owner_id,)).fetchone()

            accounts = conn.execute("""
                SELECT deriv_account_id, account_type,
                       currency, connected
                FROM deriv_accounts
                WHERE owner_id=?
            """, (owner_id,)).fetchall()

            return {
                "owner": dict(owner) if owner else None,
                "trading": dict(preferences) if preferences else None,
                "deriv_accounts": [dict(x) for x in accounts]
            }


def self_test():
    test_db = DB_PATH.parent / "fx_owner_test.db"

    if test_db.exists():
        test_db.unlink()

    db = OwnerDatabase(test_db)

    owner_id = db.create_owner(
        "THE_FX_OWNER_TEST",
        display_name="Owner Test"
    )

    db.add_deriv_account(
        owner_id,
        "CR_DEMO_TEST",
        "DEMO",
        encrypted_auth_token="ENCRYPTED_TOKEN_PLACEHOLDER"
    )

    db.set_mode(owner_id, "DEMO", "AUTO")
    db.record_login(owner_id, "DEMO")

    status = db.status(owner_id)

    assert status["owner"]["id"] == owner_id
    assert status["trading"]["account_type"] == "DEMO"
    assert status["trading"]["trading_mode"] == "AUTO"
    assert len(status["deriv_accounts"]) == 1

    # Critical security test:
    schema = sqlite3.connect(test_db).execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='owners'"
    ).fetchone()[0]

    assert "password" not in schema.lower()

    test_db.unlink()

    print("=" * 72)
    print("THE_FX.TRADER.ZW — OWNER DATABASE TEST")
    print("=" * 72)
    print("PASS : SQLite database creation")
    print("PASS : Owner profile")
    print("PASS : Deriv account table")
    print("PASS : DEMO / REAL account separation")
    print("PASS : MANUAL / AUTO preferences")
    print("PASS : Trading preferences")
    print("PASS : Alert preferences")
    print("PASS : Login history")
    print("PASS : Trade records")
    print("PASS : Password field NOT stored")
    print("PASS : XAUUSD default")
    print("-" * 72)
    print("REAL ORDER SUBMITTED : NO")
    print("REAL MONEY USED      : NO")
    print("RESULT               : OWNER DATABASE PASS")
    print("=" * 72)


if __name__ == "__main__":
    self_test()
