from dataclasses import dataclass
from typing import Optional


@dataclass
class TradeMonitorSnapshot:
    contract_id: str
    symbol: str
    side: str
    status: str
    entry_price: Optional[float]
    current_price: Optional[float]
    stake: Optional[float]
    payout: Optional[float]
    profit: Optional[float]
    profit_percentage: Optional[float]
    expiry_time: Optional[int]
    expired: bool
    sold: bool
    valid_to_sell: bool
    settled: bool


class TradeMonitor:
    """Read-only monitor for an existing Deriv contract."""

    def __init__(self, contract_monitor):
        self.contract_monitor = contract_monitor

    def get_snapshot(
        self,
        contract_id: str,
        symbol: str = "frxXAUUSD",
        side: str = "BUY",
    ) -> TradeMonitorSnapshot:

        snapshot = self.contract_monitor.get_contract(contract_id)

        settled = (
            snapshot.is_expired
            or snapshot.is_sold
        )

        return TradeMonitorSnapshot(
            contract_id=snapshot.contract_id,
            symbol=symbol,
            side=side,
            status=snapshot.status,
            entry_price=snapshot.entry_spot,
            current_price=snapshot.current_spot,
            stake=snapshot.buy_price,
            payout=snapshot.payout,
            profit=snapshot.profit,
            profit_percentage=snapshot.profit_percentage,
            expiry_time=snapshot.expiry_time,
            expired=snapshot.is_expired,
            sold=snapshot.is_sold,
            valid_to_sell=snapshot.is_valid_to_sell,
            settled=settled,
        )

    @staticmethod
    def to_dict(snapshot: TradeMonitorSnapshot):
        return {
            "contract_id": snapshot.contract_id,
            "symbol": snapshot.symbol,
            "side": snapshot.side,
            "status": snapshot.status,
            "entry_price": snapshot.entry_price,
            "current_price": snapshot.current_price,
            "stake": snapshot.stake,
            "payout": snapshot.payout,
            "profit": snapshot.profit,
            "profit_percentage": snapshot.profit_percentage,
            "expiry_time": snapshot.expiry_time,
            "expired": snapshot.expired,
            "sold": snapshot.sold,
            "valid_to_sell": snapshot.valid_to_sell,
            "settled": snapshot.settled,
        }
