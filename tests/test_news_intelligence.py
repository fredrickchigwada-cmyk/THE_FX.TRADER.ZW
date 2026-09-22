import time
import unittest

from core.news_intelligence import (
    NewsIntelligence,
)


class NewsIntelligenceTests(unittest.TestCase):

    def setUp(self):
        self.news = NewsIntelligence(
            max_age_seconds=3600
        )

    def test_xauusd_relevance(self):
        score = self.news.relevance_score(
            "Gold rises as dollar weakens",
            "XAUUSD gains after market data",
        )
        self.assertGreaterEqual(score, 5)

    def test_usd_relevance(self):
        score = self.news.relevance_score(
            "US dollar moves higher",
            "",
        )
        self.assertGreaterEqual(score, 3)

    def test_high_impact(self):
        impact = self.news.classify_impact(
            "Fed interest rate decision",
            "FOMC announces policy decision",
        )
        self.assertEqual(impact, "HIGH")

    def test_medium_impact(self):
        impact = self.news.classify_impact(
            "Gold market update",
            "",
        )
        self.assertEqual(impact, "MEDIUM")

    def test_low_impact(self):
        impact = self.news.classify_impact(
            "Company opens new office",
            "",
        )
        self.assertEqual(impact, "LOW")

    def test_bullish_bias(self):
        bias = self.news.classify_bias(
            "Gold rises as dollar weakens",
            "",
        )
        self.assertEqual(bias, "BULLISH")

    def test_bearish_bias(self):
        bias = self.news.classify_bias(
            "Gold falls as dollar strengthens",
            "",
        )
        self.assertEqual(bias, "BEARISH")

    def test_neutral_bias(self):
        bias = self.news.classify_bias(
            "Gold market update",
            "",
        )
        self.assertEqual(bias, "NEUTRAL")

    def test_add(self):
        item = self.news.add(
            "Gold rises",
            "Dollar weakens",
            "TEST",
        )

        self.assertEqual(item.source, "TEST")
        self.assertEqual(item.bias, "BULLISH")
        self.assertGreater(item.relevance, 0)

    def test_fresh_news(self):
        self.news.add(
            "Gold rises",
            published=time.time(),
        )

        fresh = self.news.fresh_items(
            "XAUUSD"
        )

        self.assertEqual(len(fresh), 1)

    def test_stale_news_ignored(self):
        self.news.add(
            "Gold rises",
            published=time.time() - 7200,
        )

        fresh = self.news.fresh_items(
            "XAUUSD"
        )

        self.assertEqual(len(fresh), 0)

    def test_high_impact_risk(self):
        self.news.add(
            "FOMC interest rate decision",
            "Federal Reserve announces policy",
        )

        result = self.news.risk_assessment(
            "XAUUSD"
        )

        self.assertEqual(
            result["risk"],
            "HIGH",
        )
        self.assertEqual(
            result["high_impact"],
            1,
        )

    def test_empty_news_low_risk(self):
        result = self.news.risk_assessment(
            "XAUUSD"
        )

        self.assertEqual(
            result["risk"],
            "LOW",
        )
        self.assertFalse(
            result["news_available"]
        )

    def test_parse_rss(self):
        xml = """<?xml version="1.0"?>
        <rss>
          <channel>
            <item>
              <title>Gold rises</title>
              <description>Dollar weakens</description>
              <link>https://example.com/news</link>
            </item>
          </channel>
        </rss>"""

        items = self.news.parse_rss(
            xml,
            source="TEST",
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0].title,
            "Gold rises",
        )
        self.assertEqual(
            items[0].source,
            "TEST",
        )

    def test_clear(self):
        self.news.add("Gold rises")
        self.assertEqual(len(self.news.items), 1)

        self.news.clear()

        self.assertEqual(len(self.news.items), 0)

    def test_snapshot(self):
        snapshot = self.news.snapshot()

        self.assertIn("items", snapshot)
        self.assertIn("fresh", snapshot)
        self.assertIn("xauusd", snapshot)

    def test_no_trade_methods(self):
        self.assertFalse(
            hasattr(self.news, "buy")
        )
        self.assertFalse(
            hasattr(self.news, "sell")
        )
        self.assertFalse(
            hasattr(self.news, "execute")
        )
        self.assertFalse(
            hasattr(self.news, "place_trade")
        )


if __name__ == "__main__":
    unittest.main()
