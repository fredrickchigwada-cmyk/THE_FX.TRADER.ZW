from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DerivConnectionStatus:
    connected: bool = False
    account_id: str = ""
    account_type: str = ""
    server: str = ""
    symbol: str = "XAUUSD"
    deriv_symbol: str = "frxXAUUSD"
    last_update: str = ""

    def snapshot(self):
        return {
            "connected": self.connected,
            "account_id": self.account_id,
            "account_type": self.account_type,
            "server": self.server,
            "symbol": self.symbol,
            "deriv_symbol": self.deriv_symbol,
            "last_update": self.last_update,
        }

    def connect(self, account_id, account_type, server):
        if not account_id:
            raise ValueError("Deriv account ID is required")

        if account_type not in ("DEMO", "REAL"):
            raise ValueError("Account type must be DEMO or REAL")

        self.connected = True
        self.account_id = str(account_id)
        self.account_type = account_type
        self.server = server or "production"
        self.last_update = datetime.now(timezone.utc).isoformat()

        return self.snapshot()

    def disconnect(self):
        self.connected = False
        self.account_id = ""
        self.account_type = ""
        self.last_update = ""

        return self.snapshot()
