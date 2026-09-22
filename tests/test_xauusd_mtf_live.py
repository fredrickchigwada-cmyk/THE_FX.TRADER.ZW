import json
import threading
import time
import unittest

import websocket

from core.candle_engine import Candle
from core.multi_timeframe import MultiTimeframeEngine


class XAUUSDMTFLiveTest(unittest.TestCase):

    WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
    SYMBOL = "frxXAUUSD"

    TIMEFRAMES = {
        "M1": 60,
        "M3": 180,
        "M5": 300,
        "M15": 900,
        "M30": 1800,
        "H1": 3600,
        "H4": 14400,
    }

    TARGET_CANDLES = 250
    REQUEST_DELAY = 2.5
    TIMEOUT = 90

    def test_live_xauusd_mtf(self):

        messages = []
        errors = []
        lock = threading.Lock()
        finished = threading.Event()

        request_map = {
            index: timeframe
            for index, timeframe
            in enumerate(
                self.TIMEFRAMES.keys(),
                start=1,
            )
        }

        expected_ids = set(
            request_map.keys()
        )

        received_ids = set()

        def on_open(ws):

            print(
                "[XAUUSD-MTF] Connected to Deriv"
            )

            print(
                "[XAUUSD-MTF] "
                "Requesting historical candles..."
            )

            for req_id, (
                timeframe,
                granularity,
            ) in enumerate(
                self.TIMEFRAMES.items(),
                start=1,
            ):

                print(
                    f"[XAUUSD-MTF] "
                    f"Requesting {timeframe} "
                    f"({self.TARGET_CANDLES} candles)"
                )

                payload = {
                    "ticks_history":
                        self.SYMBOL,

                    "adjust_start_time":
                        1,

                    "count":
                        self.TARGET_CANDLES,

                    "end":
                        "latest",

                    "granularity":
                        granularity,

                    "style":
                        "candles",

                    "req_id":
                        req_id,
                }

                try:
                    ws.send(
                        json.dumps(payload)
                    )
                except Exception as exc:
                    errors.append(exc)

                time.sleep(
                    self.REQUEST_DELAY
                )

        def on_message(ws, message):

            try:

                data = json.loads(message)

                with lock:
                    messages.append(data)

                if data.get("error"):

                    error = data["error"]

                    errors.append(error)

                    print(
                        "[XAUUSD-MTF] "
                        f"Error: {error}"
                    )

                    if (
                        isinstance(error, dict)
                        and error.get("code")
                        == "RateLimit"
                    ):
                        finished.set()

                    return

                if (
                    data.get("msg_type")
                    == "candles"
                ):

                    req_id = data.get(
                        "req_id"
                    )

                    timeframe = request_map.get(
                        req_id
                    )

                    if timeframe is None:
                        return

                    count = len(
                        data.get(
                            "candles",
                            []
                        )
                    )

                    with lock:
                        received_ids.add(
                            req_id
                        )

                    print(
                        f"[XAUUSD-MTF] "
                        f"{timeframe} received: "
                        f"{count} candles"
                    )

                    if received_ids >= expected_ids:
                        finished.set()

            except Exception as exc:

                errors.append(exc)

        def on_error(ws, error):

            errors.append(error)

            print(
                f"[XAUUSD-MTF] "
                f"WebSocket error: {error}"
            )

            finished.set()

        def on_close(
            ws,
            close_status_code,
            close_msg,
        ):

            print(
                "[XAUUSD-MTF] "
                "Connection closed"
            )

        print()
        print(
            "=========================================="
        )
        print(
            " THE_FX.TRADER.BOT.ZW"
        )
        print(
            " STAGE 8D"
        )
        print(
            " XAUUSD MTF HISTORY LOADER"
        )
        print(
            "=========================================="
        )
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

        finished.wait(
            self.TIMEOUT
        )

        try:
            ws.close()
        except Exception:
            pass

        time.sleep(1)

        for error in errors:

            if (
                isinstance(error, dict)
                and error.get("code")
                == "RateLimit"
            ):

                self.skipTest(
                    "Deriv rate limit is active."
                )

        candles_by_timeframe = {}

        print()
        print(
            "========== HISTORY RESULTS =========="
        )

        with lock:
            candle_messages = [
                item
                for item in messages
                if item.get(
                    "msg_type"
                ) == "candles"
            ]

        for response in candle_messages:

            req_id = response.get(
                "req_id"
            )

            timeframe = request_map.get(
                req_id
            )

            if timeframe is None:
                continue

            raw_candles = response.get(
                "candles",
                []
            )

            candles = []

            for item in raw_candles:

                try:

                    epoch = int(
                        item["epoch"]
                    )

                    candles.append(
                        Candle(
                            symbol=self.SYMBOL,
                            timeframe=timeframe,
                            start=epoch,
                            end=(
                                epoch
                                + self.TIMEFRAMES[
                                    timeframe
                                ]
                            ),
                            open=float(
                                item["open"]
                            ),
                            high=float(
                                item["high"]
                            ),
                            low=float(
                                item["low"]
                            ),
                            close=float(
                                item["close"]
                            ),
                            volume=0,
                        )
                    )

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ):

                    continue

            status = (
                "READY"
                if len(candles) >= 200
                else "INSUFFICIENT"
            )

            print(
                f"{timeframe:<5} : "
                f"{len(candles):>3} candles "
                f"[{status}]"
            )

            if len(candles) >= 200:
                candles_by_timeframe[
                    timeframe
                ] = candles

        print(
            "===================================="
        )

        if not candles_by_timeframe:

            self.skipTest(
                "No timeframe has enough "
                "usable XAUUSD history."
            )

        engine = MultiTimeframeEngine(
            timeframes=list(
                self.TIMEFRAMES.keys()
            )
        )

        result = engine.analyze(
            self.SYMBOL,
            candles_by_timeframe,
        )

        print()
        print(
            "========== XAUUSD MTF RESULT =========="
        )

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

        print()
        print(
            "TIMEFRAME SIGNALS"
        )

        for timeframe in (
            self.TIMEFRAMES
        ):

            signal = result.signals[
                timeframe
            ]

            print(
                f"{timeframe:<5} : "
                f"{signal.direction:<4} "
                f"{signal.strength}/10 "
                f"confirmations="
                f"{signal.confirmations} "
                f"valid="
                f"{signal.valid}"
            )

        print()
        print(
            f"Explanation : "
            f"{result.explanation}"
        )

        print(
            "========================================"
        )

        self.assertIn(
            result.final_direction,
            {
                "BUY",
                "SELL",
                "WAIT",
            },
        )

        self.assertGreaterEqual(
            result.strength,
            0,
        )

        self.assertLessEqual(
            result.strength,
            10,
        )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
