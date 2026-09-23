from dataclasses import dataclass
from typing import Optional


@dataclass
class ContractSnapshot:
    contract_id: str
    status: str
    is_expired: bool
    is_sold: bool
    is_valid_to_sell: bool
    entry_spot: Optional[float]
    current_spot: Optional[float]
    buy_price: Optional[float]
    payout: Optional[float]
    profit: Optional[float]
    profit_percentage: Optional[float]
    expiry_time: Optional[int]


class ContractMonitor:
    """Read-only monitor for an existing Deriv contract."""

    def __init__(self, execution_client):
        self.client = execution_client

    def get_contract(self, contract_id: str) -> ContractSnapshot:
        if not contract_id:
            raise ValueError("contract_id is required")

        response = self.client.request({
            "proposal_open_contract": 1,
            "contract_id": str(contract_id),
        })

        contract = response.get("proposal_open_contract")

        if not contract:
            raise RuntimeError(
                "Deriv response did not contain proposal_open_contract"
            )

        def number(value):
            if value is None:
                return None
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

        return ContractSnapshot(
            contract_id=str(contract.get("contract_id", contract_id)),
            status=str(contract.get("status", "unknown")),
            is_expired=bool(contract.get("is_expired", 0)),
            is_sold=bool(contract.get("is_sold", 0)),
            is_valid_to_sell=bool(contract.get("is_valid_to_sell", 0)),
            entry_spot=number(contract.get("entry_spot")),
            current_spot=number(contract.get("current_spot")),
            buy_price=number(contract.get("buy_price")),
            payout=number(contract.get("payout")),
            profit=number(contract.get("profit")),
            profit_percentage=number(contract.get("profit_percentage")),
            expiry_time=contract.get("expiry_time"),
        )

    @staticmethod
    def is_settled(snapshot: ContractSnapshot) -> bool:
        return snapshot.is_expired or snapshot.is_sold
