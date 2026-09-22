import unittest

from core.candle_engine import Candle
from core.signal_engine import SignalEngine


def make_candles(values):
    candles = []

    for index, value in enumerate(values):

        value = float(value)

        candles.append(
            Candle(
                symbol="TEST",
                timeframe="M1",
                start=index * 60,
                end=(index + 1) * 60,
                open=value,
                high=value + 0.5,
                low=value - 0.5,
                close=value,
                volume=1,
            )
        )

    return candles


class SignalEngineTests(unittest.TestCase):

    def setUp(self):
        self.engine = SignalEngine()

    def test_insufficient_data_returns_wait(self):

        candles = make_candles(
            range(1, 50)
        )

        signal = self.engine.generate(
            "TEST",
            "M1",
            candles,
        )

        self.assertEqual(
            signal.direction,
            "WAIT",
        )

        self.assertFalse(
            signal.valid
        )

    def test_flat_market_returns_wait(self):

        candles = make_candles(
            [100] * 250
        )

        signal = self.engine.generate(
            "TEST",
            "M1",
            candles,
        )

        self.assertEqual(
            signal.direction,
            "WAIT",
        )

    def test_signal_has_required_fields(self):

        candles = make_candles(
            range(1, 251)
        )

        signal = self.engine.generate(
            "TEST",
            "M1",
            candles,
        )

        self.assertIn(
            signal.direction,
            {
                "BUY",
                "SELL",
                "WAIT",
            },
        )

        self.assertGreaterEqual(
            signal.strength,
            0,
        )

        self.assertLessEqual(
            signal.strength,
            10,
        )

        self.assertGreaterEqual(
            signal.confirmations,
            0,
        )

    def test_no_trade_methods(self):

        forbidden = {
            "buy",
            "sell",
            "place_trade",
            "modify_trade",
            "close_trade",
            "execute_trade",
        }

        available = set(
            dir(self.engine)
        )

        self.assertTrue(
            forbidden.isdisjoint(available)
        )

    def test_signal_only_class(self):

        self.assertFalse(
            hasattr(
                self.engine,
                "execute_trade",
            )
        )

        self.assertFalse(
            hasattr(
                self.engine,
                "place_trade",
            )
        )

    def test_wait_can_carry_price(self):

        candles = make_candles(
            [100] * 250
        )

        signal = self.engine.generate(
            "TEST",
            "M1",
            candles,
        )

        self.assertEqual(
            signal.direction,
            "WAIT",
        )

        self.assertEqual(
            signal.entry,
            100.0,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
