import unittest

from core.candle_engine import Candle
from core.technical_analysis import TechnicalAnalysis


def make_candles(values):
    candles = []

    for index, value in enumerate(values):

        candles.append(
            Candle(
                symbol="TEST",
                timeframe="M1",
                start=index * 60,
                end=(index + 1) * 60,
                open=float(value),
                high=float(value) + 1.0,
                low=float(value) - 1.0,
                close=float(value),
                volume=1,
            )
        )

    return candles


class TechnicalAnalysisTests(unittest.TestCase):

    def test_ema(self):

        values = [
            1,
            2,
            3,
            4,
            5,
        ]

        result = TechnicalAnalysis.ema(
            values,
            3,
        )

        self.assertIsNotNone(result)

        self.assertGreater(
            result,
            3.0,
        )

    def test_ema_insufficient_data(self):

        result = TechnicalAnalysis.ema(
            [1, 2],
            5,
        )

        self.assertIsNone(result)

    def test_rsi_uptrend(self):

        values = list(
            range(1, 20)
        )

        result = TechnicalAnalysis.rsi(
            values,
            14,
        )

        self.assertIsNotNone(result)

        self.assertGreater(
            result,
            50.0,
        )

    def test_rsi_downtrend(self):

        values = list(
            range(20, 1, -1)
        )

        result = TechnicalAnalysis.rsi(
            values,
            14,
        )

        self.assertIsNotNone(result)

        self.assertLess(
            result,
            50.0,
        )

    def test_atr(self):

        candles = make_candles(
            range(1, 20)
        )

        result = TechnicalAnalysis.atr(
            candles,
            14,
        )

        self.assertIsNotNone(result)

        self.assertGreater(
            result,
            0,
        )

    def test_market_structure_bullish(self):

        candles = make_candles(
            [1, 2, 3, 4, 5, 6]
        )

        result = TechnicalAnalysis.market_structure(
            candles,
            lookback=5,
        )

        self.assertEqual(
            result,
            "BULLISH",
        )

    def test_market_structure_bearish(self):

        candles = make_candles(
            [6, 5, 4, 3, 2, 1]
        )

        result = TechnicalAnalysis.market_structure(
            candles,
            lookback=5,
        )

        self.assertEqual(
            result,
            "BEARISH",
        )

    def test_support_resistance(self):

        candles = make_candles(
            [10, 12, 8, 15, 11]
        )

        levels = TechnicalAnalysis.support_resistance(
            candles,
            lookback=5,
        )

        self.assertEqual(
            levels["support"],
            7.0,
        )

        self.assertEqual(
            levels["resistance"],
            16.0,
        )

    def test_momentum_positive(self):

        values = [
            100,
            101,
            102,
            103,
            104,
            110,
        ]

        result = TechnicalAnalysis.momentum(
            values,
            period=5,
        )

        self.assertIsNotNone(result)

        self.assertGreater(
            result,
            0,
        )

    def test_candle_confirmation(self):

        candles = [
            Candle(
                symbol="TEST",
                timeframe="M1",
                start=0,
                end=60,
                open=105,
                high=106,
                low=99,
                close=100,
            ),
            Candle(
                symbol="TEST",
                timeframe="M1",
                start=60,
                end=120,
                open=100,
                high=110,
                low=99,
                close=108,
            ),
        ]

        result = TechnicalAnalysis.candle_confirmation(
            candles
        )

        self.assertEqual(
            result,
            "BULLISH_REVERSAL",
        )

    def test_full_analysis(self):

        candles = make_candles(
            range(1, 250)
        )

        result = TechnicalAnalysis.analyze(
            candles
        )

        self.assertTrue(
            result["ready"]
        )

        self.assertIn(
            "ema50",
            result,
        )

        self.assertIn(
            "ema200",
            result,
        )

        self.assertIn(
            "rsi",
            result,
        )

        self.assertIn(
            "atr",
            result,
        )

        self.assertIn(
            "structure",
            result,
        )

        self.assertIn(
            "support",
            result,
        )

        self.assertIn(
            "resistance",
            result,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
