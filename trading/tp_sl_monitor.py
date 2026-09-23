from typing import Optional


class TPSLMonitor:
    """Checks tracked positions against the current XAUUSD price."""

    def __init__(self, position_manager):
        self.position_manager = position_manager

    @staticmethod
    def check_position(position, current_price: float) -> Optional[str]:
        if position.status != "OPEN":
            return None

        price = float(current_price)

        if position.side == "BUY":
            if (
                position.take_profit is not None
                and price >= position.take_profit
            ):
                return "TAKE_PROFIT"

            if (
                position.stop_loss is not None
                and price <= position.stop_loss
            ):
                return "STOP_LOSS"

        elif position.side == "SELL":
            if (
                position.take_profit is not None
                and price <= position.take_profit
            ):
                return "TAKE_PROFIT"

            if (
                position.stop_loss is not None
                and price >= position.stop_loss
            ):
                return "STOP_LOSS"

        return None

    def check_all(self, current_price: float):
        triggered = []

        for position in self.position_manager.open_positions():
            reason = self.check_position(position, current_price)

            if reason:
                triggered.append({
                    "contract_id": position.contract_id,
                    "side": position.side,
                    "price": float(current_price),
                    "reason": reason,
                })

        return triggered
