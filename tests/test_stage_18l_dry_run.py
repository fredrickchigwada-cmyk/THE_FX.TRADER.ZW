import inspect
import unittest

from core.production_runtime import ProductionRuntime


class Stage18LDryRunTest(unittest.TestCase):

    def test_runtime_can_initialize(self):
        runtime = ProductionRuntime()

        self.assertIsNotNone(runtime)
        self.assertIsNotNone(runtime.ws)
        self.assertIsNotNone(runtime.multi_market)
        self.assertIsNotNone(runtime.news_feed)

        runtime.stop()

    def test_xauusd_primary_configuration(self):
        runtime = ProductionRuntime()

        self.assertEqual(runtime.PRIMARY_MARKET, "XAUUSD")
        self.assertEqual(runtime.PRIMARY_SYMBOL, "frxXAUUSD")
        self.assertEqual(runtime.PRIMARY_TIMEFRAME, "M1")

        runtime.stop()

    def test_actual_runtime_lifecycle(self):
        runtime = ProductionRuntime()

        self.assertTrue(hasattr(runtime, "connect"))
        self.assertTrue(hasattr(runtime, "subscribe_primary"))
        self.assertTrue(hasattr(runtime, "run"))
        self.assertTrue(hasattr(runtime, "stop"))

        self.assertEqual(
            str(inspect.signature(runtime.connect)),
            "()",
        )

        self.assertEqual(
            str(inspect.signature(runtime.subscribe_primary)),
            "()",
        )

        self.assertEqual(
            str(inspect.signature(runtime.run)),
            "(duration=None)",
        )

        self.assertEqual(
            str(inspect.signature(runtime.stop)),
            "()",
        )

        runtime.stop()

    def test_runtime_has_required_production_methods(self):
        runtime = ProductionRuntime()

        required = (
            "connect",
            "subscribe_primary",
            "analyze_primary",
            "process_signal",
            "refresh_news",
            "health_check",
            "snapshot",
            "run",
            "stop",
        )

        for method in required:
            self.assertTrue(
                callable(getattr(runtime, method, None)),
                f"Missing production method: {method}",
            )

        runtime.stop()

    def test_runtime_is_signal_only(self):
        source = inspect.getsource(ProductionRuntime)

        forbidden = (
            "place_order",
            "execute_trade",
            "open_trade",
            "close_trade",
            "modify_trade",
        )

        for method in forbidden:
            self.assertNotIn(method, source)

    def test_no_trade_execution_api(self):
        runtime = ProductionRuntime()

        forbidden = (
            "place_order",
            "execute_trade",
            "open_trade",
            "close_trade",
            "modify_trade",
        )

        for method in forbidden:
            self.assertFalse(
                hasattr(runtime, method),
                f"Forbidden trade method exists: {method}",
            )

        runtime.stop()

    def test_snapshot_without_live_data(self):
        runtime = ProductionRuntime()

        snapshot = runtime.snapshot()

        self.assertIsInstance(snapshot, dict)

        runtime.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
