from deriv.auth import DerivAuthenticator
from trading.deriv_executor import DerivExecutionClient
from trading.contract_monitor import ContractMonitor
from trading.trade_monitor import TradeMonitor
from trading.trade_journal import TradeJournal
from trading.settlement_processor import SettlementProcessor
from trading.trade_lifecycle import TradeLifecycle
from database.trade_database import TradeDatabase


def get_trade_lifecycle(database=None):
    client = DerivExecutionClient(
        DerivAuthenticator()
    )

    client.connect()

    database = database or TradeDatabase()

    contract_monitor = ContractMonitor(client)

    trade_monitor = TradeMonitor(
        contract_monitor
    )

    journal = TradeJournal()

    settlement_processor = SettlementProcessor(
        journal,
        database,
    )

    lifecycle = TradeLifecycle(
        trade_monitor,
        settlement_processor,
    )

    return client, lifecycle
