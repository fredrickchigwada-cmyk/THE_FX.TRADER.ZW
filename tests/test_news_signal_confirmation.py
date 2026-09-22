import unittest

from core.news_signal_confirmation import (
    NewsSignalConfirmation,
)


class NewsSignalConfirmationTests(unittest.TestCase):

    def setUp(self):
        self.engine = NewsSignalConfirmation()

    def test_buy_with_bullish_news_confirmed(self):
        result = self.engine.evaluate(
            "BUY",
            8,
            "MEDIUM",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "BUY")
        self.assertTrue(result.news_confirmed)
        self.assertFalse(result.conflict)
        self.assertEqual(
            result.reason,
            "NEWS_CONFIRMS_TECHNICAL_SIGNAL",
        )

    def test_sell_with_bearish_news_confirmed(self):
        result = self.engine.evaluate(
            "SELL",
            8,
            "MEDIUM",
            "BEARISH",
        )

        self.assertEqual(result.final_signal, "SELL")
        self.assertTrue(result.news_confirmed)
        self.assertFalse(result.conflict)

    def test_high_impact_buy_conflict_wait(self):
        result = self.engine.evaluate(
            "BUY",
            8,
            "HIGH",
            "BEARISH",
        )

        self.assertEqual(result.final_signal, "WAIT")
        self.assertTrue(result.conflict)
        self.assertEqual(
            result.reason,
            "HIGH_IMPACT_NEWS_CONFLICT",
        )

    def test_high_impact_sell_conflict_wait(self):
        result = self.engine.evaluate(
            "SELL",
            8,
            "HIGH",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "WAIT")
        self.assertTrue(result.conflict)

    def test_medium_conflict_weak_buy_wait(self):
        result = self.engine.evaluate(
            "BUY",
            7,
            "MEDIUM",
            "BEARISH",
        )

        self.assertEqual(result.final_signal, "WAIT")
        self.assertTrue(result.conflict)

    def test_medium_conflict_weak_sell_wait(self):
        result = self.engine.evaluate(
            "SELL",
            7,
            "MEDIUM",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "WAIT")
        self.assertTrue(result.conflict)

    def test_strong_signal_survives_medium_conflict(self):
        result = self.engine.evaluate(
            "BUY",
            8,
            "MEDIUM",
            "BEARISH",
        )

        self.assertEqual(result.final_signal, "BUY")
        self.assertTrue(result.conflict)
        self.assertEqual(
            result.reason,
            "LOW_RISK_NEWS_CONFLICT_TECHNICAL_RETAINED",
        )

    def test_low_impact_conflict_retains_buy(self):
        result = self.engine.evaluate(
            "BUY",
            6,
            "LOW",
            "BEARISH",
        )

        self.assertEqual(result.final_signal, "BUY")
        self.assertTrue(result.conflict)

    def test_low_impact_conflict_retains_sell(self):
        result = self.engine.evaluate(
            "SELL",
            6,
            "LOW",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "SELL")
        self.assertTrue(result.conflict)

    def test_neutral_news_retains_buy(self):
        result = self.engine.evaluate(
            "BUY",
            7,
            "LOW",
            "NEUTRAL",
        )

        self.assertEqual(result.final_signal, "BUY")
        self.assertFalse(result.news_confirmed)

    def test_neutral_news_retains_sell(self):
        result = self.engine.evaluate(
            "SELL",
            7,
            "LOW",
            "NEUTRAL",
        )

        self.assertEqual(result.final_signal, "SELL")
        self.assertFalse(result.news_confirmed)

    def test_wait_remains_wait(self):
        result = self.engine.evaluate(
            "WAIT",
            0,
            "HIGH",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "WAIT")
        self.assertEqual(
            result.reason,
            "TECHNICAL_SIGNAL_WAIT",
        )

    def test_news_alone_cannot_create_buy(self):
        result = self.engine.evaluate_news_only(
            "HIGH",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "WAIT")

    def test_news_alone_cannot_create_sell(self):
        result = self.engine.evaluate_news_only(
            "HIGH",
            "BEARISH",
        )

        self.assertEqual(result.final_signal, "WAIT")

    def test_invalid_signal_wait(self):
        result = self.engine.evaluate(
            "INVALID",
            9,
            "HIGH",
            "BULLISH",
        )

        self.assertEqual(result.final_signal, "WAIT")
        self.assertEqual(
            result.reason,
            "INVALID_TECHNICAL_SIGNAL",
        )

    def test_strength_clamped(self):
        result = self.engine.evaluate(
            "BUY",
            99,
            "LOW",
            "BULLISH",
        )

        self.assertEqual(
            result.technical_strength,
            10,
        )

    def test_to_dict(self):
        result = self.engine.evaluate(
            "BUY",
            8,
            "LOW",
            "BULLISH",
        )

        data = result.to_dict()

        self.assertIn("final_signal", data)
        self.assertIn("news_risk", data)
        self.assertIn("news_bias", data)

    def test_no_trade_methods(self):
        self.assertFalse(
            hasattr(self.engine, "buy")
        )
        self.assertFalse(
            hasattr(self.engine, "sell")
        )
        self.assertFalse(
            hasattr(self.engine, "execute")
        )
        self.assertFalse(
            hasattr(self.engine, "place_trade")
        )


if __name__ == "__main__":
    unittest.main()
