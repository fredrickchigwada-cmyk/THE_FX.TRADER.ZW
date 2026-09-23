from trading.settlement_processor import SettlementProcessor


class TradeLifecycle:
    """Unified read-only trade monitoring lifecycle."""

    def __init__(
        self,
        trade_monitor,
        settlement_processor,
    ):
        self.trade_monitor = trade_monitor
        self.settlement_processor = settlement_processor

    def inspect(
        self,
        contract_id,
        symbol="frxXAUUSD",
        side="BUY",
    ):
        snapshot = self.trade_monitor.get_snapshot(
            contract_id,
            symbol=symbol,
            side=side,
        )

        result = {
            "monitor": self.trade_monitor.to_dict(snapshot),
            "settlement": None,
        }

        if snapshot.settled:
            result["settlement"] = self.settlement_processor.process(
                self.trade_monitor.contract_monitor.get_contract(
                    contract_id
                ),
                symbol=symbol,
                side=side,
            )

        return result
