import time
import unittest

from core.market_service import MarketService


class MarketServiceTests(unittest.TestCase):

    def test_service_has_discovery_engine(self):
        service = MarketService()

        self.assertIsNotNone(
            service.discovery
        )

        service.stop()

    def test_not_connected_protection(self):
        service = MarketService()

        success, status = service.discover()

        self.assertFalse(success)
        self.assertEqual(
            status,
            "NOT_CONNECTED"
        )

        service.stop()

    def test_cache_protection(self):
        service = MarketService()

        service.ready = True
        service.last_discovery_request = time.time()

        success, status = service.discover()

        self.assertTrue(success)
        self.assertEqual(
            status,
            "CACHE_ACTIVE"
        )

        service.stop()

    def test_market_access(self):
        service = MarketService()

        fake_response = {
            "active_symbols": [
                {
                    "symbol": "1HZ75V",
                    "underlying_symbol": "1HZ75V",
                    "underlying_symbol_name":
                        "Volatility 75 Index",
                    "exchange_is_open": True,
                    "is_trading_suspended": False,
                }
            ]
        }

        service.discovery.process_response(
            fake_response
        )

        market = service.get_market(
            "VOLATILITY 75"
        )

        self.assertIsNotNone(market)
        self.assertTrue(market.available)
        self.assertEqual(
            market.symbol,
            "1HZ75V"
        )

        service.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
