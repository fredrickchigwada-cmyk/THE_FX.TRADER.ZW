import unittest

from core.mtf_bootstrap import MTFBootstrap


class MTFBootstrapTest(unittest.TestCase):

    def test_timeframes_exist(self):

        bot = MTFBootstrap()

        expected = {
            "M1",
            "M3",
            "M5",
            "M15",
            "M30",
            "H1",
            "H4",
        }

        self.assertEqual(
            set(bot.TIMEFRAMES.keys()),
            expected,
        )

    def test_xauusd_symbol(self):

        bot = MTFBootstrap()

        self.assertEqual(
            bot.SYMBOL,
            "frxXAUUSD",
        )

    def test_history_starts_empty(self):

        bot = MTFBootstrap()

        for timeframe in bot.TIMEFRAMES:

            self.assertEqual(
                bot.get_history(
                    timeframe
                ),
                [],
            )

    def test_no_data_is_stale(self):

        bot = MTFBootstrap()

        self.assertTrue(
            bot.is_stale()
        )

    def test_mtf_without_data_waits(self):

        bot = MTFBootstrap()

        result = bot.get_mtf_result()

        self.assertEqual(
            result.final_direction,
            "WAIT",
        )

    def test_no_trade_methods(self):

        bot = MTFBootstrap()

        forbidden = [
            "buy",
            "sell",
            "place_trade",
            "execute_trade",
            "modify_trade",
            "close_trade",
        ]

        for method in forbidden:

            self.assertFalse(
                hasattr(bot, method),
                method,
            )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
