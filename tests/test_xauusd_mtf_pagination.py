import json
import threading
import time
import unittest

import websocket

from core.candle_engine import Candle
from core.multi_timeframe import MultiTimeframeEngine


class XAUUSDMTFPaginationTest(unittest.TestCase):

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

    TARGET_CANDLES = 200
    PAGE_SIZE = 250

    REQUEST_TIMEOUT = 20
    MAX_PAGES = 5

    def test_paginated_xauusd_history(self):

        print()
        print("==========================================")
        print(" THE_FX.TRADER.BOT.ZW")
        print(" STAGE 8E")
        print(" PAGINATED XAUUSD MTF HISTORY")
        print("==========================================")
        print()

        ws = None
        connected = threading.Event()

        responses = {}
        errors = {}

        response_events = {}

        request_counter = 1000

        lock = threading.Lock()

        def on_open(socket):

            print(
                "[PAGINATION] Deriv WebSocket connected"
            )

            connected.set()

        def on_message(socket, message):

            try:
                data = json.loads(message)

                req_id = data.get("req_id")

                if req_id is None:
                    return

                with lock:

                    responses[req_id] = data

                    event = response_events.get(
                        req_id
                    )

                    if event:
                        event.set()

            except Exception as exc:

                print(
                    f"[PAGINATION] "
                    f"Message error: {exc}"
                )

        def on_error(socket, error):

            print(
                f"[PAGINATION] "
                f"WebSocket error: {error}"
            )

        def on_close(
            socket,
            close_status_code,
            close_msg,
        ):

            print(
                "[PAGINATION] "
                "WebSocket closed"
            )

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

        if not connected.wait(15):

            self.skipTest(
                "Could not connect to Deriv."
            )

        def request_page(
            timeframe,
            granularity,
            end,
        ):

            nonlocal request_counter

            request_counter += 1

            req_id = request_counter

            event = threading.Event()

            with lock:
                response_events[req_id] = event

            payload = {
                "ticks_history": self.SYMBOL,
                "adjust_start_time": 1,
                "count": self.PAGE_SIZE,
                "end": end,
                "granularity": granularity,
                "style": "candles",
                "req_id": req_id,
            }

            try:

                ws.send(
                    json.dumps(payload)
                )

            except Exception as exc:

                errors[req_id] = exc

                return None

            if not event.wait(
                self.REQUEST_TIMEOUT
            ):

                return None

            with lock:
                response = responses.get(
                    req_id
                )

            with lock:
                response_events.pop(
                    req_id,
                    None
                )

            return response

        all_history = {}

        for timeframe, granularity in (
            self.TIMEFRAMES.items()
        ):

            print()
            print(
                f"========== {timeframe} =========="
            )

            combined = {}

            end = "latest"

            for page in range(
                1,
                self.MAX_PAGES + 1,
            ):

                print(
                    f"[PAGINATION] "
                    f"{timeframe} "
                    f"page {page}/{self.MAX_PAGES}"
                )

                response = request_page(
                    timeframe,
                    granularity,
                    end,
                )

                if response is None:

                    print(
                        f"[PAGINATION] "
                        f"{timeframe}: "
                        "no response"
                    )

                    break

                if response.get(
                    "error"
                ):

                    error = response[
                        "error"
                    ]

                    print(
                        f"[PAGINATION] "
                        f"{timeframe}: "
                        f"{error}"
                    )

                    if (
                        isinstance(error, dict)
                        and error.get("code")
                        == "RateLimit"
                    ):

                        self.skipTest(
                            "Deriv rate limit "
                            "is active."
                        )

                    break

                raw_candles = response.get(
                    "candles",
                    []
                )

                if not raw_candles:

                    print(
                        f"[PAGINATION] "
                        f"{timeframe}: "
                        "empty page"
                    )

                    break

                page_epochs = []

                for item in raw_candles:

                    try:

                        epoch = int(
                            item["epoch"]
                        )

                        candle = Candle(
                            symbol=self.SYMBOL,
                            timeframe=timeframe,
                            start=epoch,
                            end=(
                                epoch
                                + granularity
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

                        combined[
                            epoch
                        ] = candle

                        page_epochs.append(
                            epoch
                        )

                    except (
                        KeyError,
                        TypeError,
                        ValueError,
                    ):
                        continue

                print(
                    f"[PAGINATION] "
                    f"{timeframe}: "
                    f"+{len(page_epochs)} "
                    f"candles, total="
                    f"{len(combined)}"
                )

                if len(combined) >= (
                    self.TARGET_CANDLES
                ):

                    break

                oldest = min(
                    page_epochs
                )

                # Ask Deriv for candles older
                # than the oldest candle received.
                end = oldest - 1

                # Give the API a small pause
                # between pagination requests.
                time.sleep(2.5)

            candles = sorted(
                combined.values(),
                key=lambda candle:
                candle.start,
            )

            all_history[
                timeframe
            ] = candles

            status = (
                "READY"
                if len(candles)
                >= self.TARGET_CANDLES
                else "INSUFFICIENT"
            )

            print(
                f"[PAGINATION] "
                f"{timeframe} FINAL: "
                f"{len(candles)} candles "
                f"[{status}]"
            )

            # Pause before moving to the
            # next timeframe.
            time.sleep(2.5)

        try:
            ws.close()
        except Exception:
            pass

        print()
        print(
            "=========================================="
        )
        print(
            " FINAL HISTORY SUMMARY"
        )
        print(
            "=========================================="
        )

        ready_history = {}

        for timeframe in self.TIMEFRAMES:

            candles = all_history.get(
                timeframe,
                []
            )

            ready = len(candles) >= (
                self.TARGET_CANDLES
            )

            print(
                f"{timeframe:<5} : "
                f"{len(candles):>4} candles "
                f"["
                f"{'READY' if ready else 'INSUFFICIENT'}"
                f"]"
            )

            if ready:

                ready_history[
                    timeframe
                ] = candles

        print(
            "=========================================="
        )

        if not ready_history:

            self.skipTest(
                "No timeframe reached the "
                "required history."
            )

        # Run the actual MTF engine using
        # whatever timeframes successfully
        # obtained real history.
        engine = MultiTimeframeEngine(
            timeframes=list(
                self.TIMEFRAMES.keys()
            )
        )

        result = engine.analyze(
            self.SYMBOL,
            ready_history,
        )

        print()
        print(
            "========== XAUUSD MTF =========="
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
            "================================"
        )
        print()

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
