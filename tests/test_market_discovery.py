import unittest

from core.market_discovery import MarketDiscovery


class MarketDiscoveryTests(unittest.TestCase):

    def setUp(self):
        self.discovery = MarketDiscovery()

    def test_requested_markets_exist(self):
        self.assertIn(
            "BTCUSD",
            MarketDiscovery.REQUESTED_MARKETS
        )

        self.assertIn(
            "XAUUSD",
            MarketDiscovery.REQUESTED_MARKETS
        )

        self.assertIn(
            "STEP INDEX",
            MarketDiscovery.REQUESTED_MARKETS
        )

        self.assertIn(
            "VOLATILITY 75",
            MarketDiscovery.REQUESTED_MARKETS
        )

    def test_normalization(self):
        self.assertEqual(
            self.discovery.normalize("Volatility_75"),
            "VOLATILITY 75"
        )

        self.assertEqual(
            self.discovery.normalize("Boom-500"),
            "BOOM 500"
        )

    def test_process_active_symbols(self):
        fake_response = {
            "active_symbols": [
                {
                    "symbol": "1HZ75V",
                    "underlying_symbol": "1HZ75V",
                    "underlying_symbol_name": "Volatility 75 Index",
                    "exchange_is_open": True,
                    "is_trading_suspended": False,
                },
                {
                    "symbol": "BTCUSD",
                    "underlying_symbol": "BTCUSD",
                    "underlying_symbol_name": "Bitcoin / US Dollar",
                    "exchange_is_open": True,
                    "is_trading_suspended": False,
                },
            ]
        }

        results = self.discovery.process_response(
            fake_response
        )

        btc = self.discovery.get("BTCUSD")
        vol75 = self.discovery.get("VOLATILITY 75")

        self.assertTrue(btc.available)
        self.assertEqual(btc.symbol, "BTCUSD")

        self.assertTrue(vol75.available)
        self.assertEqual(vol75.symbol, "1HZ75V")

        self.assertEqual(len(results), 17)

    def test_missing_market_is_unavailable(self):
        fake_response = {
            "active_symbols": []
        }

        self.discovery.process_response(
            fake_response
        )

        market = self.discovery.get("BTCUSD")

        self.assertIsNotNone(market)
        self.assertFalse(market.available)
        self.assertEqual(
            self.discovery.status("BTCUSD"),
            "UNAVAILABLE"
        )

    def test_closed_market(self):
        fake_response = {
            "active_symbols": [
                {
                    "symbol": "BTCUSD",
                    "underlying_symbol": "BTCUSD",
                    "underlying_symbol_name": "Bitcoin / US Dollar",
                    "exchange_is_open": False,
                    "is_trading_suspended": False,
                }
            ]
        }

        self.discovery.process_response(
            fake_response
        )

        self.assertEqual(
            self.discovery.status("BTCUSD"),
            "CLOSED"
        )

    def test_suspended_market_is_closed(self):
        fake_response = {
            "active_symbols": [
                {
                    "symbol": "BTCUSD",
                    "underlying_symbol": "BTCUSD",
                    "underlying_symbol_name": "Bitcoin / US Dollar",
                    "exchange_is_open": True,
                    "is_trading_suspended": True,
                }
            ]
        }

        self.discovery.process_response(
            fake_response
        )

        self.assertEqual(
            self.discovery.status("BTCUSD"),
            "CLOSED"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
