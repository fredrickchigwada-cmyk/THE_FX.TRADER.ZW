import json
import threading
import time
from typing import Dict, List, Optional

import websocket

from core.candle_engine import Candle
from core.multi_timeframe import MultiTimeframeEngine


class MTFBootstrap:
    """
    Rate-limit-safe XAUUSD multi-timeframe bootstrap.

    Historical data is loaded gradually while the
    live XAUUSD tick stream continues running.

    SIGNAL-ONLY:
    No trade execution is implemented.
    """

    WS_URL = (
        "wss://api.derivws.com/"
        "trading/v1/options/ws/public"
    )

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

    HISTORY_COUNT = 200

    # Normal delay between history requests.
    REQUEST_DELAY = 15.0

    # Delay after a Deriv RateLimit response.
    RATE_LIMIT_BACKOFF = 60.0

    # Maximum number of bootstrap retries during
    # one running session.
    MAX_RETRIES_PER_TIMEFRAME = 5

    STALE_SECONDS = 30

    def __init__(self):

        self.ws = None
        self.thread = None

        self.connected = False
        self.stop_requested = False

        self.last_tick_time = 0.0
        self.latest_price: Optional[float] = None

        self.history: Dict[
            str,
            List[Candle]
        ] = {
            timeframe: []
            for timeframe in self.TIMEFRAMES
        }

        self.current: Dict[
            str,
            Optional[Candle]
        ] = {
            timeframe: None
            for timeframe in self.TIMEFRAMES
        }

        self.request_id = 1000

        self.request_lock = threading.Lock()

        self.response_events = {}
        self.responses = {}

        self.engine = MultiTimeframeEngine(
            timeframes=list(
                self.TIMEFRAMES.keys()
            )
        )

        self.bootstrap_status = {
            timeframe: "PENDING"
            for timeframe in self.TIMEFRAMES
        }

        self.bootstrap_errors = {
            timeframe: None
            for timeframe in self.TIMEFRAMES
        }

    # =================================================
    # CONNECTION
    # =================================================

    def start(self):

        if (
            self.thread
            and self.thread.is_alive()
        ):
            return

        self.stop_requested = False

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="XAUUSD-MTF",
        )

        self.thread.start()

    def _run(self):

        try:

            self.ws = websocket.WebSocketApp(
                self.WS_URL,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
            )

            self.ws.run_forever(
                ping_interval=30,
                ping_timeout=10,
            )

        except Exception as exc:

            self.connected = False

            print(
                f"[MTF] Connection exception: "
                f"{exc}"
            )

    def _on_open(self, ws):

        self.connected = True

        print(
            "[MTF] XAUUSD connection established"
        )

        self._subscribe_ticks()

        threading.Thread(
            target=self._bootstrap_history,
            daemon=True,
            name="MTF-History",
        ).start()

    def _on_error(
        self,
        ws,
        error,
    ):

        self.connected = False

        print(
            f"[MTF] WebSocket error: "
            f"{error}"
        )

    def _on_close(
        self,
        ws,
        close_status_code,
        close_msg,
    ):

        self.connected = False

        print(
            "[MTF] XAUUSD connection closed"
        )

    # =================================================
    # LIVE TICKS
    # =================================================

    def _subscribe_ticks(self):

        if not self.connected:
            return

        try:

            self.ws.send(
                json.dumps({
                    "ticks": self.SYMBOL,
                    "subscribe": 1,
                    "req_id": 1,
                })
            )

            print(
                "[MTF] Live XAUUSD ticks subscribed"
            )

        except Exception as exc:

            print(
                f"[MTF] Tick subscription error: "
                f"{exc}"
            )

    def _process_tick(
        self,
        data,
    ):

        tick = data.get(
            "tick"
        )

        if not isinstance(
            tick,
            dict,
        ):
            return

        if tick.get(
            "symbol"
        ) != self.SYMBOL:
            return

        try:

            price = float(
                tick["quote"]
            )

            epoch = float(
                tick["epoch"]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):

            return

        if price <= 0:
            return

        self.latest_price = price
        self.last_tick_time = time.time()

        self._update_candles(
            price,
            epoch,
        )

    # =================================================
    # LOCAL CANDLE BUILDING
    # =================================================

    @staticmethod
    def _candle_start(
        epoch: float,
        seconds: int,
    ) -> int:

        return (
            int(epoch // seconds)
            * seconds
        )

    def _update_candles(
        self,
        price: float,
        epoch: float,
    ):

        for timeframe, seconds in (
            self.TIMEFRAMES.items()
        ):

            start = self._candle_start(
                epoch,
                seconds,
            )

            end = start + seconds

            current = self.current[
                timeframe
            ]

            if current is None:

                self.current[
                    timeframe
                ] = Candle(
                    symbol=self.SYMBOL,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1,
                )

                continue

            if start > current.start:

                self.history[
                    timeframe
                ].append(
                    current
                )

                if len(
                    self.history[
                        timeframe
                    ]
                ) > 500:

                    self.history[
                        timeframe
                    ] = (
                        self.history[
                            timeframe
                        ][-500:]
                    )

                self.current[
                    timeframe
                ] = Candle(
                    symbol=self.SYMBOL,
                    timeframe=timeframe,
                    start=start,
                    end=end,
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1,
                )

                continue

            if start == current.start:

                current.high = max(
                    current.high,
                    price,
                )

                current.low = min(
                    current.low,
                    price,
                )

                current.close = price
                current.volume += 1

    # =================================================
    # BOOTSTRAP
    # =================================================

    def _bootstrap_history(self):

        print()
        print(
            "[MTF] Starting resumable "
            "history bootstrap"
        )

        for timeframe, granularity in (
            self.TIMEFRAMES.items()
        ):

            if self.stop_requested:
                return

            if not self.connected:
                return

            if len(
                self.history[
                    timeframe
                ]
            ) >= self.HISTORY_COUNT:

                self.bootstrap_status[
                    timeframe
                ] = "READY"

                continue

            retries = 0

            while (
                retries
                < self.MAX_RETRIES_PER_TIMEFRAME
                and not self.stop_requested
                and self.connected
            ):

                self.bootstrap_status[
                    timeframe
                ] = "LOADING"

                print(
                    f"[MTF] Loading "
                    f"{timeframe} history "
                    f"(attempt "
                    f"{retries + 1}/"
                    f"{self.MAX_RETRIES_PER_TIMEFRAME})"
                )

                response = (
                    self._request_history(
                        timeframe,
                        granularity,
                    )
                )

                if response is None:

                    retries += 1

                    self.bootstrap_errors[
                        timeframe
                    ] = "NO_RESPONSE"

                    print(
                        f"[MTF] {timeframe}: "
                        "no response"
                    )

                    time.sleep(
                        self.REQUEST_DELAY
                    )

                    continue

                error = response.get(
                    "error"
                )

                if error:

                    code = (
                        error.get("code")
                        if isinstance(
                            error,
                            dict,
                        )
                        else None
                    )

                    self.bootstrap_errors[
                        timeframe
                    ] = error

                    if code == "RateLimit":

                        retries += 1

                        self.bootstrap_status[
                            timeframe
                        ] = "RATE_LIMITED"

                        print(
                            f"[MTF] {timeframe}: "
                            "rate limited"
                        )

                        print(
                            f"[MTF] Waiting "
                            f"{self.RATE_LIMIT_BACKOFF}s "
                            "before retry..."
                        )

                        time.sleep(
                            self.RATE_LIMIT_BACKOFF
                        )

                        continue

                    self.bootstrap_status[
                        timeframe
                    ] = "ERROR"

                    print(
                        f"[MTF] {timeframe}: "
                        f"{error}"
                    )

                    break

                raw = response.get(
                    "candles",
                    []
                )

                candles = []

                for item in raw:

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
                        )

                    except (
                        KeyError,
                        TypeError,
                        ValueError,
                    ):

                        continue

                candles.sort(
                    key=lambda candle:
                    candle.start
                )

                if candles:

                    self.history[
                        timeframe
                    ] = candles[-500:]

                count = len(
                    self.history[
                        timeframe
                    ]
                )

                if count >= (
                    self.HISTORY_COUNT
                ):

                    self.bootstrap_status[
                        timeframe
                    ] = "READY"

                    print(
                        f"[MTF] {timeframe}: "
                        f"{count} candles READY"
                    )

                    break

                self.bootstrap_status[
                    timeframe
                ] = "PARTIAL"

                print(
                    f"[MTF] {timeframe}: "
                    f"{count} candles available"
                )

                break

            if self.bootstrap_status[
                timeframe
            ] not in {
                "READY",
                "PARTIAL",
            }:

                self.bootstrap_status[
                    timeframe
                ] = "BUILDING"

            # Space requests deliberately.
            time.sleep(
                self.REQUEST_DELAY
            )

        print()
        print(
            "[MTF] Bootstrap pass finished."
        )

    # =================================================
    # HISTORY REQUEST
    # =================================================

    def _request_history(
        self,
        timeframe: str,
        granularity: int,
    ):

        with self.request_lock:

            self.request_id += 1

            req_id = self.request_id

            event = threading.Event()

            self.response_events[
                req_id
            ] = event

            if not self.ws or not self.connected:

                self.response_events.pop(
                    req_id,
                    None,
                )

                return None

            payload = {
                "ticks_history":
                    self.SYMBOL,

                "adjust_start_time":
                    1,

                "count":
                    self.HISTORY_COUNT,

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

                self.ws.send(
                    json.dumps(payload)
                )

            except Exception as exc:

                self.response_events.pop(
                    req_id,
                    None,
                )

                print(
                    f"[MTF] History request "
                    f"failed: {exc}"
                )

                return None

        event.wait(
            20
        )

        response = self.responses.pop(
            req_id,
            None,
        )

        self.response_events.pop(
            req_id,
            None,
        )

        return response

    # =================================================
    # MESSAGE ROUTING
    # =================================================

    def _on_message(
        self,
        ws,
        message,
    ):

        try:

            data = json.loads(
                message
            )

        except json.JSONDecodeError:

            return

        if data.get(
            "msg_type"
        ) == "tick":

            self._process_tick(
                data
            )

            return

        req_id = data.get(
            "req_id"
        )

        if req_id is not None:

            event = (
                self.response_events.get(
                    req_id
                )
            )

            if event:

                self.responses[
                    req_id
                ] = data

                event.set()

    # =================================================
    # PUBLIC STATUS
    # =================================================

    def is_stale(self):

        if not self.connected:
            return True

        if self.last_tick_time <= 0:
            return True

        return (
            time.time()
            - self.last_tick_time
            > self.STALE_SECONDS
        )

    def get_history(
        self,
        timeframe: str,
    ) -> List[Candle]:

        return list(
            self.history.get(
                timeframe,
                []
            )
        )

    def get_current(
        self,
        timeframe: str,
    ) -> Optional[Candle]:

        return self.current.get(
            timeframe
        )

    def get_status(
        self,
        timeframe: str,
    ) -> str:

        return self.bootstrap_status.get(
            timeframe,
            "UNKNOWN",
        )

    def get_mtf_result(self):

        candles = {
            timeframe:
            self.get_history(
                timeframe
            )
            for timeframe
            in self.TIMEFRAMES
        }

        return self.engine.analyze(
            self.SYMBOL,
            candles,
        )

    def stop(self):

        self.stop_requested = True
        self.connected = False

        if self.ws:

            try:
                self.ws.close()
            except Exception:
                pass


if __name__ == "__main__":

    print(
        "THE_FX.TRADER.BOT.ZW"
    )

    print(
        "Stage 8G"
    )

    print(
        "Resumable MTF Bootstrap"
    )

    print(
        "Signal-only mode: ENABLED"
    )

    print(
        "Automatic trading: DISABLED"
    )
