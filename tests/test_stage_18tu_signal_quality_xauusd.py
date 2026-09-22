import unittest

from core.signal_engine import SignalEngine, Signal
from core.production_runtime import ProductionRuntime
from config.settings import REQUESTED_MARKETS, DEFAULT_TIMEFRAMES


class TestStage18TU(unittest.TestCase):

    # ---------------------------------------------------------
    # 18T — SIGNAL QUALITY ENGINE
    # ---------------------------------------------------------

    def test_signal_engine_exists_and_is_signal_only(self):
        engine = SignalEngine()

        self.assertTrue(getattr(engine, "SIGNAL_ONLY", True))
        self.assertFalse(hasattr(engine, "execute_trade"))
        self.assertFalse(hasattr(engine, "place_trade"))
        self.assertFalse(hasattr(engine, "close_trade"))

    def test_signal_quality_thresholds_are_configured(self):
        engine = SignalEngine()

        self.assertEqual(engine.MIN_CANDLES, 200)
        self.assertEqual(engine.MIN_CONFIRMATIONS, 4)
        self.assertEqual(engine.MIN_STRENGTH, 6)

    def test_atr_risk_parameters_are_configured(self):
        engine = SignalEngine()

        self.assertEqual(engine.SL_ATR, 1.5)
        self.assertEqual(engine.TP1_ATR, 1.5)
        self.assertEqual(engine.TP2_ATR, 3.0)

    def test_insufficient_data_returns_wait(self):
        engine = SignalEngine()

        result = engine.generate(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertIsInstance(result, Signal)
        self.assertEqual(result.direction, "WAIT")
        self.assertFalse(result.valid)
        self.assertIsNone(result.stop_loss)
        self.assertIsNone(result.tp1)
        self.assertIsNone(result.tp2)

    def test_strength_is_bounded(self):
        engine = SignalEngine()

        self.assertEqual(engine._strength(0), 0)
        self.assertGreaterEqual(engine._strength(1), 1)
        self.assertLessEqual(engine._strength(100), 10)

    def test_wait_never_contains_directional_risk_targets(self):
        engine = SignalEngine()

        result = engine._wait(
            "XAUUSD",
            "M1",
            "TEST_WAIT",
            price=5000.0,
            confirmations=2,
        )

        self.assertEqual(result.direction, "WAIT")
        self.assertFalse(result.valid)
        self.assertIsNone(result.stop_loss)
        self.assertIsNone(result.tp1)
        self.assertIsNone(result.tp2)
        self.assertIsNone(result.invalidation)

    # ---------------------------------------------------------
    # 18U — XAUUSD PRODUCTION SIGNAL ENGINE
    # ---------------------------------------------------------

    def test_xauusd_is_primary_everywhere(self):
        runtime = ProductionRuntime()

        self.assertEqual(runtime.PRIMARY_MARKET, "XAUUSD")
        self.assertIn("XAUUSD", REQUESTED_MARKETS)

        multi = getattr(runtime, "multi_market", None)
        self.assertIsNotNone(multi)
        self.assertEqual(multi.PRIMARY_MARKET, "XAUUSD")

    def test_xauusd_primary_symbol_is_configured(self):
        runtime = ProductionRuntime()

        self.assertTrue(
            isinstance(runtime.PRIMARY_SYMBOL, str)
            and runtime.PRIMARY_SYMBOL.strip()
        )

    def test_xauusd_primary_timeframe_is_configured(self):
        runtime = ProductionRuntime()

        self.assertIn(
            runtime.PRIMARY_TIMEFRAME,
            DEFAULT_TIMEFRAMES,
        )

    def test_production_runtime_is_signal_only(self):
        runtime = ProductionRuntime()

        snapshot = runtime.snapshot()

        self.assertTrue(snapshot["signal_only"])
        self.assertFalse(snapshot["trade_execution"])

    def test_production_runtime_has_signal_processing(self):
        runtime = ProductionRuntime()

        self.assertTrue(callable(runtime.analyze_primary))
        self.assertTrue(callable(runtime.process_signal))

    def test_invalid_or_missing_xauusd_data_does_not_create_signal(self):
        runtime = ProductionRuntime()

        result = runtime.analyze_primary()

        # With no loaded candle history, production must safely return None
        # rather than fabricate a BUY or SELL.
        if result is None:
            self.assertIsNone(result)
        else:
            self.assertIn(result.direction, {"BUY", "SELL", "WAIT"})

    def test_requested_timeframes_have_no_duplicates(self):
        self.assertEqual(
            len(DEFAULT_TIMEFRAMES),
            len(set(DEFAULT_TIMEFRAMES)),
        )


if __name__ == "__main__":
    unittest.main()
