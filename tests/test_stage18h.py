import unittest
from unittest.mock import patch

from core.production_runtime import ProductionRuntime


class Stage18HTests(unittest.TestCase):

    def setUp(self):
        self.runtime = ProductionRuntime()

    def tearDown(self):
        try:
            self.runtime.stop()
        except Exception:
            pass

    def test_news_feed_connected_to_runtime(self):
        self.assertIsNotNone(
            self.runtime.news_feed
        )

    def test_primary_market_is_xauusd(self):
        self.assertEqual(
            self.runtime.PRIMARY_MARKET,
            "XAUUSD",
        )

    def test_news_defaults_are_safe(self):
        self.assertEqual(
            self.runtime.status.news_risk,
            "LOW",
        )
        self.assertEqual(
            self.runtime.status.news_bias,
            "NEUTRAL",
        )
        self.assertFalse(
            self.runtime.status.news_available
        )

    def test_refresh_news_updates_status(self):
        fake_snapshot = {
            "feeds": {},
            "last_refresh": 123.0,
            "xauusd": {
                "symbol": "XAUUSD",
                "risk": "HIGH",
                "bias": "BEARISH",
                "fresh_items": 2,
                "high_impact": 1,
                "bullish": 0,
                "bearish": 2,
                "news_available": True,
            },
        }

        with patch.object(
            self.runtime.news_feed,
            "refresh",
            return_value={},
        ), patch.object(
            self.runtime.news_feed,
            "xauusd_risk",
            return_value=fake_snapshot["xauusd"],
        ), patch.object(
            self.runtime.news_feed,
            "snapshot",
            return_value=fake_snapshot,
        ):
            result = self.runtime.refresh_news(
                force=True
            )

        self.assertEqual(
            self.runtime.status.news_risk,
            "HIGH",
        )
        self.assertEqual(
            self.runtime.status.news_bias,
            "BEARISH",
        )
        self.assertEqual(
            self.runtime.status.news_items,
            2,
        )
        self.assertTrue(
            self.runtime.status.news_available
        )
        self.assertIsNotNone(result)

    def test_snapshot_contains_news(self):
        snap = self.runtime.snapshot()

        self.assertIn(
            "news_available",
            snap,
        )
        self.assertIn(
            "news_risk",
            snap,
        )
        self.assertIn(
            "news_bias",
            snap,
        )
        self.assertIn(
            "news_items",
            snap,
        )

    def test_news_never_has_trade_methods(self):
        self.assertFalse(
            hasattr(self.runtime.news_feed, "buy")
        )
        self.assertFalse(
            hasattr(self.runtime.news_feed, "sell")
        )
        self.assertFalse(
            hasattr(self.runtime.news_feed, "execute")
        )
        self.assertFalse(
            hasattr(self.runtime.news_feed, "place_trade")
        )

    def test_signal_only_runtime(self):
        self.assertTrue(
            self.runtime.snapshot()["signal_only"]
        )
        self.assertFalse(
            self.runtime.snapshot()["trade_execution"]
        )


if __name__ == "__main__":
    unittest.main()
