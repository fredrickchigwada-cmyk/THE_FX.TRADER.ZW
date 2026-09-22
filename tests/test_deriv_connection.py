import unittest

from core.deriv_ws import DerivWebSocket
from core.market_data import MarketDataStore


class DerivConnectionTests(unittest.TestCase):

    def test_websocket_configuration(self):
        self.assertTrue(
            DerivWebSocket.WS_URL.startswith("wss://")
        )

    def test_signal_only_module_has_no_trade_methods(self):
        bot = DerivWebSocket()

        forbidden = [
            "buy",
            "sell",
            "place_trade",
            "modify_trade",
            "close_trade",
        ]

        for method in forbidden:
            self.assertFalse(
                hasattr(bot, method),
                f"Forbidden trading method found: {method}"
            )

    def test_market_data_store(self):
        store = MarketDataStore()

        data = {
            "tick": {
                "symbol": "TEST",
                "quote": 123.45,
                "epoch": 1700000000,
            }
        }

        tick = store.update_from_deriv(data)

        self.assertIsNotNone(tick)
        self.assertEqual(tick.symbol, "TEST")
        self.assertEqual(tick.price, 123.45)

    def test_invalid_tick_is_rejected(self):
        store = MarketDataStore()

        data = {
            "tick": {
                "symbol": "TEST",
                "quote": "invalid",
                "epoch": 1700000000,
            }
        }

        tick = store.update_from_deriv(data)

        self.assertIsNone(tick)


if __name__ == "__main__":
    unittest.main(verbosity=2)
