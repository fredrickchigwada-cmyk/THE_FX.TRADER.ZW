from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TrackedPosition:
    contract_id: str
    symbol: str
    side: str
    amount: float
    entry: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "M15"
    status: str = "OPEN"
    exit_price: Optional[float] = None
    close_reason: Optional[str] = None


class PositionManager:
    """Tracks open Demo/Deriv positions in memory."""

    def __init__(self):
        self._positions: Dict[str, TrackedPosition] = {}

    def add_position(self, position: TrackedPosition) -> None:
        if not position.contract_id:
            raise ValueError("contract_id is required")

        self._positions[position.contract_id] = position

    def get(self, contract_id: str) -> Optional[TrackedPosition]:
        return self._positions.get(contract_id)

    def open_positions(self):
        return [
            position
            for position in self._positions.values()
            if position.status == "OPEN"
        ]

    def count_open(self) -> int:
        return len(self.open_positions())

    def close_position(
        self,
        contract_id: str,
        exit_price: Optional[float] = None,
        reason: str = "MANUAL",
    ) -> TrackedPosition:
        position = self._positions.get(contract_id)

        if position is None:
            raise KeyError(f"Unknown contract: {contract_id}")

        position.status = "CLOSED"
        position.exit_price = exit_price
        position.close_reason = reason

        return position

    def remove(self, contract_id: str) -> None:
        self._positions.pop(contract_id, None)

    def snapshot(self):
        return [
            {
                "contract_id": p.contract_id,
                "symbol": p.symbol,
                "side": p.side,
                "amount": p.amount,
                "entry": p.entry,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "timeframe": p.timeframe,
                "status": p.status,
                "exit_price": p.exit_price,
                "close_reason": p.close_reason,
            }
            for p in self._positions.values()
        ]
