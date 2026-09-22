import unittest

from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline
from core.signal_engine import Signal


def make_signal(
    direction="BUY",
    strength=8,
    valid=True,
):
    return Signal(
        symbol="XAUUSD",
        timeframe="M1",
        direction=direction,
        strength=strength,
        confirmations=5,
        entry=4300.0,
        stop_loss=4290.0,
        tp1=4310.0,
        tp2=4320.0,
        invalidation=4290.0,
        explanation="18F controlled technical signal",
        candle_confirmed=True,
        valid=valid,
    )


class Stage18FTests(unittest.TestCase):

    def setUp(self):
        self.system = FullSystem()
        self.system.reset_emergency_stop()
        self.pipeline = IntegrationPipeline(
            self.system
        )

    def test_matching_news_preserves_buy(self):
        result = self.pipeline.process_signal(
            make_signal("BUY"),
            news_risk="MEDIUM",
            news_bias="BULLISH",
        )

        self.assertEqual(
            result.status,
            "PROCESSED",
        )
        self.assertEqual(
            result.signal,
            "BUY",
        )
        self.assertTrue(result.journaled)

    def test_matching_news_preserves_sell(self):
        result = self.pipeline.process_signal(
            make_signal("SELL"),
            news_risk="MEDIUM",
            news_bias="BEARISH",
        )

        self.assertEqual(
            result.status,
            "PROCESSED",
        )
        self.assertEqual(
            result.signal,
            "SELL",
        )
        self.assertTrue(result.journaled)

    def test_high_impact_conflict_blocks_buy(self):
        result = self.pipeline.process_signal(
            make_signal("BUY"),
            news_risk="HIGH",
            news_bias="BEARISH",
        )

        self.assertEqual(
            result.status,
            "NEWS_BLOCKED",
        )
        self.assertEqual(
            result.signal,
            "WAIT",
        )
        self.assertFalse(result.journaled)
        self.assertFalse(result.alerted)
        self.assertIn(
            "HIGH_IMPACT_NEWS_CONFLICT",
            result.explanation,
        )

    def test_high_impact_conflict_blocks_sell(self):
        result = self.pipeline.process_signal(
            make_signal("SELL"),
            news_risk="HIGH",
            news_bias="BULLISH",
        )

        self.assertEqual(
            result.status,
            "NEWS_BLOCKED",
        )
        self.assertEqual(
            result.signal,
            "WAIT",
        )
        self.assertFalse(result.journaled)

    def test_news_cannot_create_buy(self):
        result = self.pipeline.process_signal(
            make_signal("WAIT"),
            news_risk="HIGH",
            news_bias="BULLISH",
        )

        self.assertEqual(
            result.signal,
            "WAIT",
        )
        self.assertFalse(result.journaled)

    def test_news_cannot_create_sell(self):
        result = self.pipeline.process_signal(
            make_signal("WAIT"),
            news_risk="HIGH",
            news_bias="BEARISH",
        )

        self.assertEqual(
            result.signal,
            "WAIT",
        )
        self.assertFalse(result.journaled)

    def test_neutral_news_preserves_buy(self):
        result = self.pipeline.process_signal(
            make_signal("BUY"),
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(
            result.signal,
            "BUY",
        )
        self.assertTrue(result.journaled)

    def test_neutral_news_preserves_sell(self):
        result = self.pipeline.process_signal(
            make_signal("SELL"),
            news_risk="LOW",
            news_bias="NEUTRAL",
        )

        self.assertEqual(
            result.signal,
            "SELL",
        )
        self.assertTrue(result.journaled)

    def test_emergency_stop_still_has_priority(self):
        self.system.emergency_stop_system()

        result = self.pipeline.process_signal(
            make_signal("BUY"),
            news_risk="LOW",
            news_bias="BULLISH",
        )

        self.assertEqual(
            result.status,
            "EMERGENCY_STOP",
        )
        self.assertEqual(
            result.signal,
            "WAIT",
        )

    def test_existing_call_without_news_still_works(self):
        result = self.pipeline.process_signal(
            make_signal("BUY")
        )

        self.assertEqual(
            result.status,
            "PROCESSED",
        )
        self.assertEqual(
            result.signal,
            "BUY",
        )

    def test_no_trade_execution(self):
        self.assertFalse(
            hasattr(self.pipeline, "buy")
        )
        self.assertFalse(
            hasattr(self.pipeline, "sell")
        )
        self.assertFalse(
            hasattr(self.pipeline, "execute")
        )
        self.assertFalse(
            hasattr(self.pipeline, "place_trade")
        )


if __name__ == "__main__":
    unittest.main()
