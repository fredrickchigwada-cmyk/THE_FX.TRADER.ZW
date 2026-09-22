import unittest

from core.candle_engine import Candle
from core.multi_timeframe import MultiTimeframeEngine


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


class MultiTimeframeTests(unittest.TestCase):

    def test_no_data_returns_wait(self):

        engine = MultiTimeframeEngine(
            timeframes=["M1", "M5", "M15"]
        )

        result = engine.analyze(
            "TEST",
            {},
        )

        self.assertEqual(
            result.final_direction,
            "WAIT",
        )

        self.assertEqual(
            result.aligned_timeframes,
            0,
        )

    def test_missing_timeframes_are_safe(self):

        engine = MultiTimeframeEngine(
            timeframes=["M1", "M5"]
        )

        result = engine.analyze(
            "TEST",
            {
                "M1": make_candles(
                    [100] * 250
                )
            },
        )

        self.assertEqual(
            result.final_direction,
            "WAIT",
        )

        self.assertEqual(
            result.analyzed_timeframes,
            2,
        )

    def test_result_contains_each_timeframe(self):

        engine = MultiTimeframeEngine(
            timeframes=["M1", "M5", "M15"]
        )

        result = engine.analyze(
            "TEST",
            {},
        )

        self.assertEqual(
            set(result.signals.keys()),
            {"M1", "M5", "M15"},
        )

    def test_agreement_ratio_range(self):

        engine = MultiTimeframeEngine(
            timeframes=["M1", "M5", "M15"]
        )

        result = engine.analyze(
            "TEST",
            {},
        )

        self.assertGreaterEqual(
            result.agreement_ratio,
            0.0,
        )

        self.assertLessEqual(
            result.agreement_ratio,
            1.0,
        )

    def test_no_trade_methods(self):

        engine = MultiTimeframeEngine()

        forbidden = {
            "buy",
            "sell",
            "place_trade",
            "modify_trade",
            "close_trade",
            "execute_trade",
        }

        self.assertTrue(
            forbidden.isdisjoint(
                set(dir(engine))
            )
        )

    def test_flat_market_waits(self):

        engine = MultiTimeframeEngine(
            timeframes=["M1", "M5"]
        )

        candles = make_candles(
            [100] * 250
        )

        result = engine.analyze(
            "TEST",
            {
                "M1": candles,
                "M5": candles,
            },
        )

        self.assertEqual(
            result.final_direction,
            "WAIT",
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
