import time
from typing import Callable, Optional


class MonitorLoop:
    """Controlled read-only polling loop for an existing contract."""

    def __init__(
        self,
        trade_monitor,
        interval: float = 2.0,
        on_update: Optional[Callable] = None,
    ):
        if interval <= 0:
            raise ValueError("interval must be greater than zero")

        self.trade_monitor = trade_monitor
        self.interval = interval
        self.on_update = on_update
        self.running = False

    def run(
        self,
        contract_id: str,
        symbol: str = "frxXAUUSD",
        side: str = "BUY",
        max_checks: Optional[int] = None,
    ):
        self.running = True
        checks = 0
        updates = []

        try:
            while self.running:
                snapshot = self.trade_monitor.get_snapshot(
                    contract_id,
                    symbol=symbol,
                    side=side,
                )

                data = self.trade_monitor.to_dict(snapshot)
                updates.append(data)

                if self.on_update:
                    self.on_update(data)

                checks += 1

                if data["settled"]:
                    break

                if max_checks is not None and checks >= max_checks:
                    break

                time.sleep(self.interval)

        finally:
            self.running = False

        return updates

    def stop(self):
        self.running = False
