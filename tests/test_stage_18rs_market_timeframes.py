import unittest

from config.settings import REQUESTED_MARKETS, DEFAULT_TIMEFRAMES
from core.market_discovery import MarketDiscovery
from core.multi_market_runtime import MultiMarketRuntime


class TestStage18RSMarketAndTimeframes(unittest.TestCase):

    def test_xauusd_is_primary_market(self):
        self.assertIn("XAUUSD", REQUESTED_MARKETS)

        runtime = MultiMarketRuntime()

        self.assertEqual(runtime.PRIMARY_MARKET, "XAUUSD")

    def test_all_requested_markets_are_present(self):
        expected = {
            "XAUUSD",
            "BTCUSD",
            "STEP INDEX",
            "VOLATILITY 75",
            "VOLATILITY 10",
            "VOLATILITY 25",
            "VOLATILITY 50",
            "VOLATILITY 100",
            "BOOM 500",
            "BOOM 1000",
            "CRASH 500",
            "CRASH 1000",
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "NAS100",
            "US30",
        }

        self.assertEqual(expected, set(REQUESTED_MARKETS))

    def test_market_discovery_distinguishes_available_and_missing(self):
        discovery = MarketDiscovery()

        discovery.process_response({
            "active_symbols": [
                {
                    "symbol": "frxXAUUSD",
                    "underlying_symbol": "frxXAUUSD",
                    "display_name": "Gold",
                    "exchange_is_open": True,
                    "is_trading_suspended": False,
                },
                {
                    "symbol": "R_75",
                    "underlying_symbol": "R_75",
                    "display_name": "Volatility 75 Index",
                    "exchange_is_open": True,
                    "is_trading_suspended": False,
                },
            ]
        })

        self.assertTrue(discovery.get("XAUUSD").available)
        self.assertTrue(discovery.get("VOLATILITY 75").available)

        self.assertFalse(discovery.get("EURUSD").available)

    def test_closed_market_is_not_reported_open(self):
        discovery = MarketDiscovery()

        discovery.process_response({
            "active_symbols": [
                {
                    "symbol": "frxXAUUSD",
                    "underlying_symbol": "frxXAUUSD",
                    "display_name": "Gold",
                    "exchange_is_open": False,
                    "is_trading_suspended": False,
                }
            ]
        })

        self.assertEqual(
            discovery.status("XAUUSD"),
            "CLOSED",
        )

    def test_suspended_market_is_closed(self):
        discovery = MarketDiscovery()

        discovery.process_response({
            "active_symbols": [
                {
                    "symbol": "frxXAUUSD",
                    "underlying_symbol": "frxXAUUSD",
                    "display_name": "Gold",
                    "exchange_is_open": True,
                    "is_trading_suspended": True,
                }
            ]
        })

        self.assertEqual(
            discovery.status("XAUUSD"),
            "CLOSED",
        )

    def test_missing_market_is_not_falsely_active(self):
        discovery = MarketDiscovery()

        discovery.process_response({
            "active_symbols": []
        })

        self.assertNotEqual(
            discovery.status("XAUUSD"),
            "OPEN",
        )

    def test_multimarket_runtime_contains_primary(self):
        runtime = MultiMarketRuntime()

        snapshot = runtime.snapshot()

        self.assertIn("markets", snapshot)
        self.assertIn("XAUUSD", snapshot["markets"])

    def test_required_timeframes_are_configured(self):
        required = {
            "M1", "M3", "M5", "M15", "M30",
            "H1", "H2", "H4", "H6", "H8",
            "H12", "D1", "W1", "MN1",
        }

        self.assertTrue(
            required.issubset(set(DEFAULT_TIMEFRAMES))
        )

    def test_timeframes_have_no_duplicates(self):
        self.assertEqual(
            len(DEFAULT_TIMEFRAMES),
            len(set(DEFAULT_TIMEFRAMES)),
        )

    def test_primary_market_remains_xauusd(self):
        runtime = MultiMarketRuntime()

        self.assertEqual(
            runtime.PRIMARY_MARKET,
            "XAUUSD",
        )


if __name__ == "__main__":
    unittest.main()
