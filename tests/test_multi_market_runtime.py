import unittest
import time

from core.multi_market_runtime import (
    MultiMarketRuntime,
    PRIMARY_MARKET,
    REQUESTED_MARKETS,
)


class FakeMarket:
    def __init__(
        self,
        symbol,
        available=True,
        trading_suspended=False,
        exchange_is_open=True,
    ):
        self.symbol = symbol
        self.available = available
        self.trading_suspended = trading_suspended
        self.exchange_is_open = exchange_is_open


class FakeDiscovery:
    def __init__(self):
        self.markets = {}

    def process_response(self, data):
        return []

    def get(self, name):
        return self.markets.get(name)

    def status(self, name):
        market = self.get(name)

        if market is None:
            return "CHECKING"

        if not market.available:
            return "UNAVAILABLE"

        if market.trading_suspended is True:
            return "CLOSED"

        if market.exchange_is_open is False:
            return "CLOSED"

        if market.exchange_is_open is True:
            return "OPEN"

        return "ACTIVE"


class TestMultiMarketRuntime(unittest.TestCase):

    def test_primary_market_is_xauusd(self):
        self.assertEqual(PRIMARY_MARKET, "XAUUSD")

    def test_all_requested_markets_present(self):
        self.assertEqual(len(REQUESTED_MARKETS), 17)
        self.assertIn("XAUUSD", REQUESTED_MARKETS)
        self.assertIn("BTCUSD", REQUESTED_MARKETS)
        self.assertIn("VOLATILITY 75", REQUESTED_MARKETS)

    def test_runtime_contains_all_markets(self):
        runtime = MultiMarketRuntime(FakeDiscovery())

        self.assertEqual(
            len(runtime.markets),
            len(REQUESTED_MARKETS),
        )

    def test_discovery_symbol_is_used(self):
        discovery = FakeDiscovery()

        discovery.markets["XAUUSD"] = FakeMarket(
            "frxXAUUSD"
        )

        runtime = MultiMarketRuntime(discovery)
        runtime.refresh()

        self.assertEqual(
            runtime.symbol("XAUUSD"),
            "frxXAUUSD",
        )

    def test_unavailable_market_cannot_signal(self):
        discovery = FakeDiscovery()

        discovery.markets["BTCUSD"] = FakeMarket(
            "BTCUSD",
            available=False,
        )

        runtime = MultiMarketRuntime(discovery)
        runtime.refresh()

        self.assertFalse(
            runtime.signal_allowed("BTCUSD")
        )

    def test_closed_market_cannot_signal(self):
        discovery = FakeDiscovery()

        discovery.markets["XAUUSD"] = FakeMarket(
            "frxXAUUSD",
            available=True,
            trading_suspended=True,
            exchange_is_open=True,
        )

        runtime = MultiMarketRuntime(discovery)
        runtime.refresh()

        self.assertEqual(
            runtime.status("XAUUSD"),
            "CLOSED",
        )

        self.assertFalse(
            runtime.signal_allowed("XAUUSD")
        )

    def test_valid_tick_updates_market(self):
        discovery = FakeDiscovery()

        discovery.markets["XAUUSD"] = FakeMarket(
            "frxXAUUSD"
        )

        runtime = MultiMarketRuntime(discovery)
        runtime.refresh()

        self.assertTrue(
            runtime.update_tick(
                "XAUUSD",
                5000.25,
                time.time(),
            )
        )

        self.assertTrue(
            runtime.data_ready("XAUUSD")
        )

    def test_invalid_price_rejected(self):
        discovery = FakeDiscovery()

        discovery.markets["XAUUSD"] = FakeMarket(
            "frxXAUUSD"
        )

        runtime = MultiMarketRuntime(discovery)
        runtime.refresh()

        self.assertFalse(
            runtime.update_tick(
                "XAUUSD",
                -1,
                time.time(),
            )
        )

    def test_stale_data_blocks_signal(self):
        discovery = FakeDiscovery()

        discovery.markets["XAUUSD"] = FakeMarket(
            "frxXAUUSD"
        )

        runtime = MultiMarketRuntime(discovery)
        runtime.refresh()

        runtime.update_tick(
            "XAUUSD",
            5000.25,
            time.time() - 30,
        )

        self.assertFalse(
            runtime.signal_allowed("XAUUSD")
        )

    def test_snapshot_is_signal_only(self):
        runtime = MultiMarketRuntime(FakeDiscovery())

        snapshot = runtime.snapshot()

        self.assertTrue(snapshot["signal_only"])
        self.assertFalse(snapshot["trade_execution"])
        self.assertEqual(
            snapshot["primary_market"],
            "XAUUSD",
        )

    def test_no_trade_execution_api(self):
        runtime = MultiMarketRuntime(FakeDiscovery())

        forbidden = [
            name
            for name in dir(runtime)
            if any(
                word in name.lower()
                for word in (
                    "buy",
                    "sell",
                    "order",
                    "trade",
                    "execute",
                    "close_position",
                )
            )
        ]

        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main()
