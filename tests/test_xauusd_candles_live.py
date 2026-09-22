import time
import unittest

from core.deriv_ws import DerivWebSocket, DerivRateLimitError
from core.candle_engine import CandleEngine


class XAUUSDCandleLiveTest(unittest.TestCase):

    def test_live_xauusd_candle_building(self):

        connected = []
        ticks = []
        errors = []

        engine = CandleEngine()

        def on_open():
            connected.append(True)
            print("[XAUUSD-CANDLE] WebSocket connected")

        def on_message(data):

            if data.get("msg_type") != "tick":
                return

            tick = data.get("tick", {})

            if tick.get("symbol") != "frxXAUUSD":
                return

            ticks.append(tick)

            try:
                completed = engine.update_tick(
                    symbol=tick["symbol"],
                    price=float(tick["quote"]),
                    epoch=float(tick["epoch"]),
                )

                current_m1 = engine.get_current(
                    "frxXAUUSD",
                    "M1",
                )

                if current_m1:
                    print(
                        "[M1] "
                        f"O={current_m1.open} "
                        f"H={current_m1.high} "
                        f"L={current_m1.low} "
                        f"C={current_m1.close} "
                        f"T={current_m1.volume}"
                    )

                if completed:
                    for candle in completed:
                        print()
                        print("========== COMPLETED CANDLE ==========")
                        print(f"Symbol : {candle.symbol}")
                        print(f"TF     : {candle.timeframe}")
                        print(f"Open   : {candle.open}")
                        print(f"High   : {candle.high}")
                        print(f"Low    : {candle.low}")
                        print(f"Close  : {candle.close}")
                        print(f"Volume : {candle.volume}")
                        print("======================================")
                        print()

            except Exception as exc:
                errors.append(exc)
                print(
                    f"[XAUUSD-CANDLE] Processing error: {exc!r}"
                )

        def on_error(error):
            errors.append(error)
            print(
                f"[XAUUSD-CANDLE] ERROR: {error!r}"
            )

        client = DerivWebSocket(
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
        )

        try:
            print()
            print("========================================")
            print(" THE_FX.TRADER.BOT.ZW")
            print(" LIVE XAUUSD CANDLE TEST")
            print("========================================")
            print()

            client.connect()

            deadline = time.time() + 10

            while time.time() < deadline:
                if connected:
                    break
                time.sleep(0.25)

            self.assertTrue(
                connected,
                "Could not connect to Deriv."
            )

            print(
                "[XAUUSD-CANDLE] Subscribing to frxXAUUSD..."
            )

            try:
                client.subscribe_ticks(
                    "frxXAUUSD"
                )

            except DerivRateLimitError as exc:
                self.skipTest(
                    f"Deriv rate protection active: {exc}"
                )

            deadline = time.time() + 15

            while time.time() < deadline:

                if ticks:
                    break

                for error in errors:
                    if isinstance(
                        error,
                        DerivRateLimitError
                    ):
                        self.skipTest(
                            "Deriv rate limit is active."
                        )

                time.sleep(0.25)

            self.assertGreater(
                len(ticks),
                0,
                "No live XAUUSD ticks received."
            )

            current = engine.get_current(
                "frxXAUUSD",
                "M1",
            )

            self.assertIsNotNone(
                current,
                "M1 candle was not created."
            )

            self.assertGreater(
                current.open,
                0,
            )

            self.assertGreaterEqual(
                current.high,
                current.open,
            )

            self.assertLessEqual(
                current.low,
                current.open,
            )

            self.assertGreater(
                current.close,
                0,
            )

            print()
            print("========== XAUUSD CANDLE VERIFIED ==========")
            print(f"Ticks received : {len(ticks)}")
            print(f"Symbol         : {current.symbol}")
            print(f"Timeframe      : {current.timeframe}")
            print(f"Open           : {current.open}")
            print(f"High           : {current.high}")
            print(f"Low            : {current.low}")
            print(f"Close          : {current.close}")
            print(f"Ticks in candle: {current.volume}")
            print("============================================")
            print()

        finally:
            client.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
