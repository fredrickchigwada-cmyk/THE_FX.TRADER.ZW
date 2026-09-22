import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class Tick:
    symbol: str
    price: float
    epoch: float


class MarketDataStore:
    """
    Lightweight in-memory store for the latest Deriv tick.

    No trading functionality is included.
    """

    def __init__(self):
        self.latest_ticks = {}

    def update_from_deriv(self, data: dict) -> Optional[Tick]:
        tick = data.get("tick")

        if not isinstance(tick, dict):
            return None

        symbol = tick.get("symbol")
        quote = tick.get("quote")
        epoch = tick.get("epoch")

        if not symbol or quote is None or epoch is None:
            return None

        try:
            price = float(quote)
            epoch_value = float(epoch)
        except (TypeError, ValueError):
            return None

        if price <= 0:
            return None

        result = Tick(
            symbol=symbol,
            price=price,
            epoch=epoch_value,
        )

        self.latest_ticks[symbol] = result

        return result

    def get_latest(self, symbol: str) -> Optional[Tick]:
        return self.latest_ticks.get(symbol)

    def age_seconds(self, symbol: str) -> Optional[float]:
        tick = self.get_latest(symbol)

        if tick is None:
            return None

        return max(0.0, time.time() - tick.epoch)
