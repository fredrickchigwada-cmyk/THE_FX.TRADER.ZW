import json
import threading
import time
import unittest

import websocket

from core.candle_engine import Candle
from core.signal_engine import SignalEngine


class XAUUSDSignalLiveTest(unittest.TestCase):

    WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
    SYMBOL = "frxXAUUSD"

    def test_live_xauusd_signal(self):

        messages = []
        errors = []
        done = threading.Event()

        def on_open(ws):
            print("[XAUUSD-SIGNAL] WebSocket connected")

            ws.send(json.dumps({
                "ticks_history": self.SYMBOL,
                "adjust_start_time": 1,
                "count": 250,
                "end": "latest",
                "granularity": 60,
                "style": "candles",
                "req_id": 200,
            }))

        def on_message(ws, message):
            try:
                data = json.loads(message)
                messages.append(data)

                if data.get("error"):
                    errors.append(data["error"])
                    done.set()
                    return

                if data.get("msg_type") == "candles":
                    done.set()

            except Exception as exc:
                errors.append(exc)
                done.set()

        def on_error(ws, error):
            errors.append(error)
            done.set()

        def on_close(ws, code, msg):
            pass

        print()
        print("==========================================")
        print(" THE_FX.TRADER.BOT.ZW")
        print(" LIVE XAUUSD SIGNAL ENGINE")
        print("==========================================")
        print()

        ws = websocket.WebSocketApp(
            self.WS_URL,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        thread = threading.Thread(
            target=ws.run_forever,
            kwargs={
                "ping_interval": 30,
                "ping_timeout": 10,
            },
            daemon=True,
        )

        thread.start()

        finished = done.wait(20)

        try:
            ws.close()
        except Exception:
            pass

        if not finished:
            self.fail(
                "Timed out waiting for XAUUSD candle history."
            )

        for error in errors:
            if isinstance(error, dict):
                if error.get("code") == "RateLimit":
                    self.skipTest(
                        "Deriv rate limit is active."
                    )

        self.assertFalse(
            errors,
            f"Deriv returned errors: {errors}",
        )

        candle_response = None

        for data in messages:
            if data.get("msg_type") == "candles":
                candle_response = data
                break

        self.assertIsNotNone(
            candle_response,
            "No XAUUSD candle history received.",
        )

        raw_candles = candle_response.get(
            "candles"
        )

        self.assertIsInstance(
            raw_candles,
            list,
        )

        self.assertGreater(
            len(raw_candles),
            200,
        )

        candles = []

        for item in raw_candles:

            candles.append(
                Candle(
                    symbol=self.SYMBOL,
                    timeframe="M1",
                    start=int(item["epoch"]),
                    end=int(item["epoch"]) + 60,
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=0,
                )
            )

        engine = SignalEngine()

        signal = engine.generate(
            self.SYMBOL,
            "M1",
            candles,
        )

        print()
        print("========== LIVE XAUUSD SIGNAL ==========")
        print(f"Symbol         : {signal.symbol}")
        print(f"Timeframe      : {signal.timeframe}")
        print(f"Signal         : {signal.direction}")
        print(f"Strength       : {signal.strength}/10")
        print(
            f"Confirmations  : "
            f"{signal.confirmations}"
        )
        print(f"Entry          : {signal.entry}")
        print(f"Stop Loss      : {signal.stop_loss}")
        print(f"TP1            : {signal.tp1}")
        print(f"TP2            : {signal.tp2}")
        print(
            f"Invalidation   : "
            f"{signal.invalidation}"
        )
        print(
            f"Candle Confirm : "
            f"{signal.candle_confirmed}"
        )
        print(
            f"Valid          : "
            f"{signal.valid}"
        )
        print(
            f"Explanation    : "
            f"{signal.explanation}"
        )
        print("=========================================")
        print()

        self.assertIn(
            signal.direction,
            {
                "BUY",
                "SELL",
                "WAIT",
            },
        )

        self.assertGreaterEqual(
            signal.strength,
            0,
        )

        self.assertLessEqual(
            signal.strength,
            10,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
