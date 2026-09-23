class SettlementProcessor:
    """Converts settled Deriv contracts into persistent trade history."""

    def __init__(self, journal, database):
        self.journal = journal
        self.database = database

    def process(self, snapshot, symbol="frxXAUUSD", side="BUY"):
        if not snapshot:
            raise ValueError("snapshot is required")

        if not snapshot.is_expired and not snapshot.is_sold:
            raise ValueError("Contract is not settled")

        # Prevent duplicate database entries.
        existing = self.database.get_trade(snapshot.contract_id)

        if existing is not None:
            return {
                "status": "ALREADY_RECORDED",
                "contract_id": snapshot.contract_id,
                "record": existing,
            }

        record = self.journal.from_contract(
            snapshot,
            symbol=symbol,
            side=side,
        )

        inserted = self.database.add_trade(record)

        if not inserted:
            existing = self.database.get_trade(
                snapshot.contract_id
            )

            return {
                "status": "ALREADY_RECORDED",
                "contract_id": snapshot.contract_id,
                "record": existing,
            }

        return {
            "status": "RECORDED",
            "contract_id": snapshot.contract_id,
            "record": record,
        }
