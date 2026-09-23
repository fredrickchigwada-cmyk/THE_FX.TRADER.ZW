from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Optional

from trading.mode_controller import ModeController

DB_PATH = Path("database/fx_owner.db")

EMAIL_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


class EmailModeService:
    """
    Connects an owner email identity to the existing
    DEMO/REAL x MANUAL/AUTO mode controller.

    No Deriv password or PAT is stored here.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.mode_controller = ModeController()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def validate_email(email: str) -> str:
        email = (email or "").strip().lower()

        if not EMAIL_RE.fullmatch(email):
            raise ValueError("Invalid email address")

        return email

    def owner_by_email(self, email: str) -> Optional[dict]:
        email = self.validate_email(email)

        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, owner_ref, display_name, email, phone,
                       created_at, updated_at, last_login
                FROM owners
                WHERE lower(email) = ?
                LIMIT 1
                """,
                (email,),
            ).fetchone()

        return dict(row) if row else None

    def login(self, email: str) -> dict:
        email = self.validate_email(email)

        owner = self.owner_by_email(email)

        if owner is None:
            raise ValueError("Owner email is not registered")

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE owners
                SET last_login = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (owner["id"],),
            )

            conn.execute(
                """
                INSERT INTO login_events
                (owner_id, event_type, account_type, created_at)
                VALUES (?, 'EMAIL_LOGIN', 'DEMO', CURRENT_TIMESTAMP)
                """,
                (owner["id"],),
            )

        return self.status(email)

    def select_mode(
        self,
        email: str,
        account: str,
        mode: str,
    ) -> dict:
        email = self.validate_email(email)

        owner = self.owner_by_email(email)
        if owner is None:
            raise ValueError("Owner email is not registered")

        account = account.upper().strip()
        mode = mode.upper().strip()

        if account not in ("DEMO", "REAL"):
            raise ValueError("Account must be DEMO or REAL")

        if mode not in ("MANUAL", "AUTO"):
            raise ValueError("Mode must be MANUAL or AUTO")

        # Selecting a mode always resets real authorization.
        self.mode_controller.select(account, mode)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trading_preferences
                (
                    owner_id,
                    account_type,
                    trading_mode,
                    symbol,
                    timeframe,
                    risk_per_trade,
                    max_open_trades,
                    updated_at
                )
                VALUES (?, ?, ?, 'XAUUSD', 'M1', 1.0, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(owner_id, account_type)
                DO UPDATE SET
                    trading_mode = excluded.trading_mode,
                    symbol = 'XAUUSD',
                    updated_at = CURRENT_TIMESTAMP
                """,
                (owner["id"], account, mode),
            )

        return self.status(email)

    def authorize_real(self, email: str, confirmation: bool) -> dict:
        email = self.validate_email(email)

        owner = self.owner_by_email(email)
        if owner is None:
            raise ValueError("Owner email is not registered")

        result = self.mode_controller.authorize_real(
            confirmation=bool(confirmation)
        )

        return self.status(email)

    def revoke_real(self, email: str) -> dict:
        email = self.validate_email(email)

        owner = self.owner_by_email(email)
        if owner is None:
            raise ValueError("Owner email is not registered")

        self.mode_controller.revoke_real()

        return self.status(email)

    def status(self, email: str) -> dict:
        email = self.validate_email(email)

        owner = self.owner_by_email(email)
        if owner is None:
            raise ValueError("Owner email is not registered")

        mode_status = self.mode_controller.status()

        return {
            "owner_id": owner["id"],
            "email": owner["email"],
            "display_name": owner["display_name"],
            "account": mode_status["account"],
            "mode": mode_status["mode"],
            "real_authorized": mode_status["real_authorized"],
            "can_execute": mode_status["can_execute"],
            "available_modes": [
                "DEMO MANUAL",
                "DEMO AUTO",
                "REAL MANUAL",
                "REAL AUTO",
            ],
        }
