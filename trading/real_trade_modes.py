from dataclasses import dataclass
from typing import Literal


RealMode = Literal["MANUAL", "AUTO"]


@dataclass
class RealTradingMode:
    mode: RealMode = "MANUAL"
    enabled: bool = False
    symbol: str = "XAUUSD"
    max_open_trades: int = 1
    min_lot: float = 0.01
    max_lot: float = 0.50

    def set_mode(self, mode: str) -> None:
        mode = str(mode).upper()

        if mode not in {"MANUAL", "AUTO"}:
            raise ValueError("Real trading mode must be MANUAL or AUTO")

        self.mode = mode

    def authorize(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def can_execute(
        self,
        *,
        symbol: str,
        side: str,
        open_positions: int = 0,
        confirmed: bool = False,
    ) -> tuple[bool, str]:

        if not self.enabled:
            return False, "Real trading is disabled"

        if symbol != "XAUUSD":
            return False, "Unsupported symbol"

        if side not in {"BUY", "SELL"}:
            return False, "Invalid side"

        if open_positions >= self.max_open_trades:
            return False, "Maximum open trades reached"

        if self.mode == "MANUAL" and not confirmed:
            return False, "Manual confirmation required"

        if self.mode == "AUTO" and not confirmed:
            return True, "Auto execution authorized"

        return True, "Manual execution authorized"

    def snapshot(self) -> dict:
        return {
            "mode": self.mode,
            "enabled": self.enabled,
            "symbol": self.symbol,
            "max_open_trades": self.max_open_trades,
            "lot_range": {
                "min": self.min_lot,
                "max": self.max_lot,
            },
        }
