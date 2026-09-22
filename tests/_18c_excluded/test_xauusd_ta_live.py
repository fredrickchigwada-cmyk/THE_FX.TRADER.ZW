import json
import time
import unittest

from core.deriv_ws import DerivWebSocket, DerivRateLimitError
from core.candle_engine import CandleEngine
from core.technical_analysis import TechnicalAnalysis


class XAUUSDTechnicalAnalysisLiveTest(unittest.TestCase):

    def test_live_xauusd_technical_analysis(self):

        connected = []
        candles_received = []
        errors = []

        def on_open():
            connected.append(True)
            print("[XAUUSD-TA] WebSocket connected")

        def on_message(data):

            if data.get("msg_type") == "candles":
                candles = data.get("candles", [])

                if isinstance(candles, list):
                    candles_received.extend(candles)

                    print(
                        f"[XAUUSD-TA] Received "
                        f"{len(candles)} historical candles"
                    )

            if data.get("msg_type") == "error":
                error = data.get("error", {})
                errors.append(error)

                print(
                    f"[XAUUSD-TA] Deriv error: "
                    f"{error}"
                )

        def on_error(error):
            errors.append(error)

            print(
                f"[XAUUSD-TA] ERROR: {error!r}"
            )

        client = DerivWebSocket(
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
        )

        try:

            print()
            print("==========================================")
            print(" THE_FX.TRADER.BOT.ZW")
            print(" LIVE XAUUSD TECHNICAL ANALYSIS")
            print("==========================================")
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
                "[XAUUSD-TA] Requesting "
                "XAUUSD M1 candle history..."
            )

            request = {
                "ticks_history": "frxXAUUSD",
                "adjust_start_time": 1,
                "count": 250,
                "end": "latest",
                "granularity": 60,
                "style": "candles",
                "req_id": 100,
            }

            try:
                client.send(request)

            except DerivRateLimitError as exc:

                self.skipTest(
                    f"Deriv rate protection active: {exc}"
                )

            deadline = time.time() + 15

            while time.time() < deadline:

                if candles_received:
                    break

                for error in errors:

                    if isinstance(
                        error,
                        DerivRateLimitError,
                    ):
                        self.skipTest(
                            "Deriv rate limit is active."
                        )

                    if isinstance(error, dict):

                        code = error.get(
                            "code",
                            "",
                        )

                        if code == "RateLimit":
                            self.skipTest(
                                "Deriv rate limit is active."
                            )

                time.sleep(0.25)

            self.assertGreater(
                len(candles_received),
                0,
                "No XAUUSD candle history received."
            )

            engine = CandleEngine()

            for item in candles_received:

                try:

                    epoch = float(
                        item["epoch"]
                    )

                    open_price = float(
                        item["open"]
                    )

                    high = float(
                        item["high"]
                    )

                    low = float(
                        item["low"]
                    )

                    close = float(
                        item["close"]
                    )

                    # Feed each historical candle into the
                    # technical-analysis representation.
                    from core.candle_engine import Candle

                    candle = Candle(
                        symbol="frxXAUUSD",
                        timeframe="M1",
                        start=int(epoch),
                        end=int(epoch) + 60,
                        open=open_price,
                        high=high,
                        low=low,
                        close=close,
                        volume=0,
                    )

                    engine.history.setdefault(
                        "frxXAUUSD",
                        {}
                    )

                    engine.history[
                        "frxXAUUSD"
                    ].setdefault(
                        "M1",
                        []
                    )

                    engine.history[
                        "frxXAUUSD"
                    ]["M1"].append(candle)

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    continue

            candles = engine.get_history(
                "frxXAUUSD",
                "M1",
            )

            self.assertGreaterEqual(
                len(candles),
                200,
                "Not enough valid candles for analysis."
            )

            analysis = TechnicalAnalysis.analyze(
                candles
            )

            self.assertTrue(
                analysis["ready"]
            )

            self.assertIsNotNone(
                analysis["ema50"]
            )

            self.assertIsNotNone(
                analysis["ema200"]
            )

            self.assertIsNotNone(
                analysis["rsi"]
            )

            self.assertIsNotNone(
                analysis["atr"]
            )

            self.assertIsNotNone(
                analysis["support"]
            )

            self.assertIsNotNone(
                analysis["resistance"]
            )

            print()
            print("========== LIVE XAUUSD TA ==========")
            print(
                f"Symbol        : frxXAUUSD"
            )
            print(
                f"Timeframe     : M1"
            )
            print(
                f"Candles       : {len(candles)}"
            )
            print(
                f"Price         : {analysis['price']:.2f}"
            )
            print(
                f"EMA 50        : {analysis['ema50']:.2f}"
            )
            print(
                f"EMA 200       : {analysis['ema200']:.2f}"
            )
            print(
                f"RSI 14        : {analysis['rsi']:.2f}"
            )
            print(
                f"ATR 14        : {analysis['atr']:.4f}"
            )
            print(
                f"Structure     : {analysis['structure']}"
            )
            print(
                f"Support       : {analysis['support']:.2f}"
            )
            print(
                f"Resistance    : {analysis['resistance']:.2f}"
            )
            print(
                f"Momentum      : "
                f"{analysis['momentum']:.4f}%"
            )
            print(
                f"Candle        : "
                f"{analysis['candle_confirmation']}"
            )
            print("====================================")
            print()

        finally:
            client.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
