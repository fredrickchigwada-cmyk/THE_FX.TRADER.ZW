import unittest

from config.settings import (
    BOT_NAME,
    SIGNAL_ONLY,
    DEFAULT_TIMEFRAMES,
    REQUESTED_MARKETS,
)


class FoundationTests(unittest.TestCase):

    def test_bot_name(self):
        self.assertEqual(
            BOT_NAME,
            "THE_FX.TRADER.BOT.ZW"
        )

    def test_signal_only(self):
        self.assertTrue(SIGNAL_ONLY)

    def test_timeframes(self):
        self.assertIn("M1", DEFAULT_TIMEFRAMES)
        self.assertIn("M15", DEFAULT_TIMEFRAMES)
        self.assertIn("H1", DEFAULT_TIMEFRAMES)
        self.assertIn("H4", DEFAULT_TIMEFRAMES)
        self.assertIn("D1", DEFAULT_TIMEFRAMES)

    def test_markets(self):
        self.assertIn("BTCUSD", REQUESTED_MARKETS)
        self.assertIn("XAUUSD", REQUESTED_MARKETS)
        self.assertIn("STEP INDEX", REQUESTED_MARKETS)
        self.assertIn("VOLATILITY 75", REQUESTED_MARKETS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
