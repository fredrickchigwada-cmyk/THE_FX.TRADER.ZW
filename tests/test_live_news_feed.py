import unittest

from core.live_news_feed import LiveNewsFeed


class LiveNewsFeedTests(unittest.TestCase):

    def setUp(self):
        self.feed = LiveNewsFeed()

    def test_official_feeds_configured(self):
        self.assertIn(
            "BLS_CPI",
            self.feed.FEEDS,
        )
        self.assertIn(
            "BLS_EMPLOYMENT",
            self.feed.FEEDS,
        )
        self.assertIn(
            "FED_MONETARY",
            self.feed.FEEDS,
        )

    def test_feed_names(self):
        names = self.feed.feed_names()

        self.assertEqual(len(names), 3)
        self.assertIn("BLS_CPI", names)
        self.assertIn(
            "BLS_EMPLOYMENT",
            names,
        )
        self.assertIn(
            "FED_MONETARY",
            names,
        )

    def test_unknown_feed_blocked(self):
        result = self.feed.fetch_one(
            "UNKNOWN"
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.items,
            0,
        )
        self.assertEqual(
            result.error,
            "UNKNOWN_FEED",
        )

    def test_snapshot(self):
        snapshot = self.feed.snapshot()

        self.assertIn(
            "feeds",
            snapshot,
        )
        self.assertIn(
            "xauusd",
            snapshot,
        )

    def test_xauusd_risk_available(self):
        risk = self.feed.xauusd_risk()

        self.assertEqual(
            risk["symbol"],
            "XAUUSD",
        )

    def test_no_trade_methods(self):
        self.assertFalse(
            hasattr(self.feed, "buy")
        )
        self.assertFalse(
            hasattr(self.feed, "sell")
        )
        self.assertFalse(
            hasattr(self.feed, "execute")
        )
        self.assertFalse(
            hasattr(self.feed, "place_trade")
        )


if __name__ == "__main__":
    unittest.main()
