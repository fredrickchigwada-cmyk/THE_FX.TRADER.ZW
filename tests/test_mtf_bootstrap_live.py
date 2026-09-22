import time
import unittest

from core.mtf_bootstrap import MTFBootstrap


class MTFBootstrapLiveTest(unittest.TestCase):

    def test_stage_8g_live(self):

        bot = MTFBootstrap()

        print()
        print("==========================================")
        print(" THE_FX.TRADER.BOT.ZW")
        print(" STAGE 8G LIVE VERIFICATION")
        print(" XAUUSD RESUMABLE MTF BOOTSTRAP")
        print("==========================================")
        print()

        bot.start()

        print("[LIVE] Waiting for Deriv connection...")

        deadline = time.time() + 15

        while (
            not bot.connected
            and time.time() < deadline
        ):
            time.sleep(0.5)

        if not bot.connected:
            bot.stop()
            self.skipTest(
                "Could not establish Deriv connection."
            )

        print("[LIVE] Deriv connection: OK")
        print("[LIVE] Waiting for XAUUSD tick...")

        deadline = time.time() + 20

        while (
            bot.last_tick_time <= 0
            and time.time() < deadline
        ):
            time.sleep(0.5)

        if bot.last_tick_time <= 0:
            bot.stop()
            self.skipTest(
                "No live XAUUSD tick received."
            )

        print(
            f"[LIVE] XAUUSD: "
            f"{bot.latest_price}"
        )

        print("[LIVE] Tick stream: OK")

        # Give the bootstrap a short observation
        # window without intentionally hammering
        # the Deriv API.
        print()
        print(
            "[LIVE] Observing bootstrap for "
            "20 seconds..."
        )

        time.sleep(20)

        print()
        print("========== BOOTSTRAP STATUS ==========")

        for timeframe in bot.TIMEFRAMES:

            count = len(
                bot.get_history(
                    timeframe
                )
            )

            status = bot.get_status(
                timeframe
            )

            print(
                f"{timeframe:<5} : "
                f"{count:>4} candles "
                f"[{status}]"
            )

        print(
            "======================================"
        )

        result = bot.get_mtf_result()

        print()
        print("========== MTF RESULT ==========")

        print(
            f"Symbol              : "
            f"{result.symbol}"
        )

        print(
            f"Final Signal        : "
            f"{result.final_direction}"
        )

        print(
            f"Strength            : "
            f"{result.strength}/10"
        )

        print(
            f"Aligned Timeframes  : "
            f"{result.aligned_timeframes}"
        )

        print(
            f"Analyzed Timeframes : "
            f"{result.analyzed_timeframes}"
        )

        print(
            f"Agreement           : "
            f"{result.agreement_ratio:.2%}"
        )

        print(
            f"Live data stale?    : "
            f"{bot.is_stale()}"
        )

        print(
            "================================"
        )

        bot.stop()

        self.assertEqual(
            bot.connected,
            False,
        )

        self.assertIn(
            result.final_direction,
            {
                "BUY",
                "SELL",
                "WAIT",
            },
        )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
