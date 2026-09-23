from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TradeRecord:
    contract_id: str
    symbol: str
    side: str
    entry_price: Optional[float]
    settlement_price: Optional[float]
    stake: Optional[float]
    payout: Optional[float]
    profit: Optional[float]
    profit_percentage: Optional[float]
    status: str
    result: str
    settled_at: str


class TradeJournal:
    """Creates standardized records from settled Deriv contracts."""

    def __init__(self):
        self._records = []

    @staticmethod
    def from_contract(snapshot, symbol="frxXAUUSD", side="BUY"):
        if not snapshot:
            raise ValueError("snapshot is required")

        if not snapshot.is_expired and not snapshot.is_sold:
            raise ValueError("Contract is not settled")

        profit = snapshot.profit

        if profit is None:
            result = "UNKNOWN"
        elif profit > 0:
            result = "WIN"
        elif profit < 0:
            result = "LOSS"
        else:
            result = "BREAKEVEN"

        record = TradeRecord(
            contract_id=snapshot.contract_id,
            symbol=symbol,
            side=side,
            entry_price=snapshot.entry_spot,
            settlement_price=snapshot.current_spot,
            stake=snapshot.buy_price,
            payout=snapshot.payout,
            profit=profit,
            profit_percentage=snapshot.profit_percentage,
            status=snapshot.status,
            result=result,
            settled_at=datetime.now(timezone.utc).isoformat(),
        )

        return record

    def add(self, record: TradeRecord):
        self._records.append(record)

    def all(self):
        return list(self._records)

    def count(self):
        return len(self._records)

    def total_profit(self):
        return sum(
            record.profit or 0.0
            for record in self._records
        )
