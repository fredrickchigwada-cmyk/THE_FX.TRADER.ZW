import inspect
import unittest

from core.production_runtime import ProductionRuntime
from core.multi_market_runtime import MultiMarketRuntime
from core.integration_pipeline import IntegrationPipeline


class FakeSystem:
    def __init__(self):
        self.emergency_stop = False
        self.accepted = []

    def accept_signal(self, signal, **kwargs):
        self.accepted.append((signal, kwargs))
        return True


class Stage18KProductionIntegrationTest(unittest.TestCase):

    def test_production_runtime_architecture(self):
        source = inspect.getsource(ProductionRuntime)

        self.assertIn('PRIMARY_MARKET = "XAUUSD"', source)
        self.assertIn('PRIMARY_SYMBOL = "frxXAUUSD"', source)
        self.assertIn("subscribe_primary", source)
        self.assertIn("multi_market", source)
        self.assertIn("news_feed", source)
        self.assertIn("_on_message", source)

        forbidden = (
            "place_order",
            "execute_trade",
            "open_trade",
            "close_trade",
            "modify_trade",
        )

        for name in forbidden:
            self.assertNotIn(name, source)

    def test_multi_market_runtime_contains_xauusd(self):
        runtime = MultiMarketRuntime()

        state = runtime.get("XAUUSD")

        self.assertIsNotNone(state)
        self.assertEqual(runtime.PRIMARY_MARKET, "XAUUSD")

    def test_conflicting_high_impact_news_blocks_buy(self):
        system = FakeSystem()
        pipeline = IntegrationPipeline(system)

        result = pipeline.process_signal(
            "BUY",
            news_risk="HIGH",
            news_bias="BEARISH",
        )

        self.assertEqual(result.signal, "WAIT")
        self.assertEqual(len(system.accepted), 0)

    def test_conflicting_high_impact_news_blocks_sell(self):
        system = FakeSystem()
        pipeline = IntegrationPipeline(system)

        result = pipeline.process_signal(
            "SELL",
            news_risk="HIGH",
            news_bias="BULLISH",
        )

        self.assertEqual(result.signal, "WAIT")
        self.assertEqual(len(system.accepted), 0)

    def test_wait_never_becomes_directional(self):
        system = FakeSystem()
        pipeline = IntegrationPipeline(system)

        result = pipeline.process_signal(
            "WAIT",
            news_risk="HIGH",
            news_bias="BULLISH",
        )

        self.assertEqual(result.signal, "WAIT")
        self.assertEqual(len(system.accepted), 0)

    def test_news_parameters_are_supported(self):
        signature = inspect.signature(IntegrationPipeline.process_signal)

        self.assertIn("news_risk", signature.parameters)
        self.assertIn("news_bias", signature.parameters)

    def test_pipeline_has_news_confirmation_engine(self):
        source = inspect.getsource(IntegrationPipeline)

        self.assertIn("NewsSignalConfirmation", source)
        self.assertIn("news_confirmation", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
