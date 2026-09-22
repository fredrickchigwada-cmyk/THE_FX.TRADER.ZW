import json
import time
import threading
from typing import Optional, Callable

import websocket


from core.deriv_rate_limit import DerivRateLimitGuard
class DerivRateLimitError(Exception):
    """Raised when Deriv rejects a request because of rate limiting."""


class DerivWebSocket:
    """
    Public Deriv market-data WebSocket.

    SIGNAL-ONLY:
    This class receives market data only.
    It cannot place, modify, or close trades.
    """

    WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

    # Conservative client-side protection.
    # Deriv request spacing. A subscription is allowed immediately
    # after a fresh WebSocket connection; subsequent requests are spaced.
    MIN_REQUEST_INTERVAL = 1.0
    DEFAULT_BACKOFF = 10.0
    MAX_BACKOFF = 300.0

    def __init__(
        self,
        on_message: Optional[Callable[[dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_open: Optional[Callable[[], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.on_message_callback = on_message

        # Deriv tick-subscription rate-limit protection.
        # Signal-only. No trading functionality.
        self.rate_limit_guard = DerivRateLimitGuard(
            base_backoff=30.0,
            max_backoff=300.0,
        )

        self.on_error_callback = on_error
        self.on_open_callback = on_open
        self.on_close_callback = on_close

        self.ws = None
        self.thread = None

        self.connected = False
        self.stop_requested = False

        self.last_message_time = 0.0
        self.messages_received = 0

        self.last_request_time = 0.0
        self.rate_limited_until = 0.0
        self.backoff_seconds = self.DEFAULT_BACKOFF

        self._request_lock = threading.Lock()

    def connect(self):
        if self.thread and self.thread.is_alive():
            return

        self.stop_requested = False

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="DerivWebSocket",
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

            if self.on_error_callback:
                self.on_error_callback(exc)

    def _on_open(self, ws):
        self.connected = True
        self.last_message_time = time.time()

        if self.on_open_callback:
            self.on_open_callback()

    def _on_message(self, ws, message):
        self.last_message_time = time.time()
        self.messages_received += 1

        try:
            data = json.loads(message)
        except json.JSONDecodeError as exc:
            if self.on_error_callback:
                self.on_error_callback(exc)
            return

        # Detect server-side rate limiting.
        error = data.get("error")

        if isinstance(error, dict):
            if error.get("code") == "RateLimit":
                self._handle_rate_limit()

                if self.on_error_callback:
                    self.on_error_callback(
                        DerivRateLimitError(
                            error.get(
                                "message",
                                "Deriv rate limit reached.",
                            )
                        )
                    )

                return

        # Detect Deriv rate-limit responses.
        if "RateLimit" in str(data):
            self.rate_limit_guard.detect(data)

        if self.on_message_callback:
            self.on_message_callback(data)

    def _on_error(self, ws, error):
        self.connected = False

        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False

        if self.on_close_callback:
            self.on_close_callback()

    def _handle_rate_limit(self):
        now = time.time()

        self.rate_limited_until = (
            now + self.backoff_seconds
        )

        self.backoff_seconds = min(
            self.backoff_seconds * 2,
            self.MAX_BACKOFF,
        )

    def _request_allowed(self):
        now = time.time()

        if now < self.rate_limited_until:
            return False

        if (
            now - self.last_request_time
            < self.MIN_REQUEST_INTERVAL
        ):
            return False

        return True

    def send(self, payload: dict):
        """
        Send a request only when the client-side rate limiter
        allows it.
        """

        if not self.ws or not self.connected:
            raise ConnectionError(
                "Deriv WebSocket is not connected."
            )

        with self._request_lock:

            if not self._request_allowed():
                remaining = max(
                    0.0,
                    self.rate_limited_until - time.time(),
                )

                raise DerivRateLimitError(
                    "Request blocked by local rate protection. "
                    f"Retry in approximately {remaining:.1f} seconds."
                )

            self.ws.send(json.dumps(payload))

            self.last_request_time = time.time()

    def request_active_symbols(self):
        """
        Request active symbols.

        The caller must respect rate-limit protection.
        """

        self.send({
            "active_symbols": "brief",
            "req_id": 1,
        })

    def ticks_history(
        self,
        symbol: str,
        count: int = 200,
        granularity: int = 60,
    ):
        """
        Request historical tick data from Deriv.

        This is market-data only.
        No trading or execution functionality.
        """

        if not symbol:
            raise ValueError("symbol is required")

        if count < 1:
            raise ValueError("count must be positive")

        if granularity < 1:
            raise ValueError("granularity must be positive")

        request = {
            "ticks_history": str(symbol),
            "count": int(count),
            "end": "latest",
            "style": "candles",
            "granularity": int(granularity),
        }

        return self.send(request)

    def subscribe_ticks(self, symbol: str):
        """
        Subscribe to a live Deriv tick stream.

        Rate-limit protection prevents rapid repeated
        subscription attempts.

        Signal-only market data.
        No trading/execution functionality.
        """

        if not symbol:
            raise ValueError("symbol is required")

        if not self.connected:
            raise RuntimeError(
                "WebSocket is not connected"
            )

        if not self.rate_limit_guard.can_retry():

            remaining = (
                self.rate_limit_guard.remaining()
            )

            raise RuntimeError(
                "Deriv tick subscription is "
                "rate-limited. "
                f"Retry after {remaining:.1f}s."
            )

        request = {
            "ticks": str(symbol),
            "subscribe": 1,
        }

        return self.send(request)

    def stop(self):
        self.stop_requested = True
        self.connected = False

        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def is_rate_limited(self):
        return time.time() < self.rate_limited_until

    def rate_limit_remaining(self):
        return max(
            0.0,
            self.rate_limited_until - time.time(),
        )

    def is_stale(self, timeout_seconds: int = 30):
        if not self.connected:
            return True

        if self.last_message_time <= 0:
            return True

        return (
            time.time() - self.last_message_time
            > timeout_seconds
        )
