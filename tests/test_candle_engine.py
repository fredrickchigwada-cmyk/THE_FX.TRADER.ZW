import unittest

from core.candle_engine import CandleEngine


class CandleEngineTests(unittest.TestCase):

    def setUp(self):
        self.engine = CandleEngine()

    def test_all_timeframes_exist(self):
        expected = [
            "M1",
            "M3",
            "M5",
            "M15",
            "M30",
            "H1",
            "H2",
            "H4",
            "H6",
            "H8",
            "H12",
            "D1",
            "W1",
            "MN1",
        ]

        self.assertEqual(
            list(self.engine.TIMEFRAMES.keys()),
            expected,
        )

    def test_m1_timeframe(self):
        self.assertEqual(
            self.engine.timeframe_seconds("M1"),
            60,
        )

    def test_m5_timeframe(self):
        self.assertEqual(
            self.engine.timeframe_seconds("M5"),
            300,
        )

    def test_h1_timeframe(self):
        self.assertEqual(
            self.engine.timeframe_seconds("H1"),
            3600,
        )

    def test_invalid_timeframe(self):
        with self.assertRaises(ValueError):
            self.engine.timeframe_seconds("XYZ")

    def test_ohlc_building(self):
        base = 1000

        prices = [
            100.0,
            101.0,
            99.0,
            102.0,
        ]

        for index, price in enumerate(prices):
            self.engine.update_tick(
                "TEST",
                price,
                base + index,
            )

        candle = self.engine.get_current(
            "TEST",
            "M1",
        )

        self.assertIsNotNone(candle)

        self.assertEqual(candle.open, 100.0)
        self.assertEqual(candle.high, 102.0)
        self.assertEqual(candle.low, 99.0)
        self.assertEqual(candle.close, 102.0)
        self.assertEqual(candle.volume, 4)

    def test_new_candle_is_created(self):
        self.engine.update_tick(
            "TEST",
            100.0,
            1000,
        )

        completed = self.engine.update_tick(
            "TEST",
            105.0,
            1060,
        )

        # Only M1 has crossed into a new candle period.
        # Longer timeframes are still forming.
        self.assertEqual(
            len(completed),
            1,
        )

        history = self.engine.get_history(
            "TEST",
            "M1",
        )

        self.assertEqual(len(history), 1)

        self.assertEqual(
            history[0].open,
            100.0,
        )

        current = self.engine.get_current(
            "TEST",
            "M1",
        )

        self.assertEqual(
            current.open,
            105.0,
        )

    def test_bullish_candle(self):
        self.engine.update_tick(
            "TEST",
            100.0,
            1000,
        )

        self.engine.update_tick(
            "TEST",
            105.0,
            1001,
        )

        candle = self.engine.get_current(
            "TEST",
            "M1",
        )

        self.assertTrue(candle.bullish)
        self.assertFalse(candle.bearish)

    def test_bearish_candle(self):
        self.engine.update_tick(
            "TEST",
            105.0,
            1000,
        )

        self.engine.update_tick(
            "TEST",
            100.0,
            1001,
        )

        candle = self.engine.get_current(
            "TEST",
            "M1",
        )

        self.assertTrue(candle.bearish)
        self.assertFalse(candle.bullish)


if __name__ == "__main__":
    unittest.main(verbosity=2)
