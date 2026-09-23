import json
import threading
import time
from typing import Callable, Optional

import websocket


PUBLIC_WS_URL = (
    "wss://api.derivws.com/"
    "trading/v1/options/ws/public"
)


class DerivWebSocketError(Exception):
    pass


class DerivWebSocket:
    """
    THE_FX.TRADER.ZW WebSocket manager.

    Stage 04 responsibilities:
    - Connect to Deriv
    - Receive messages
    - Send requests
    - Maintain connection state
    - Handle errors
    - Reconnect
    - Keep trading execution OUT of this layer
    """

    def __init__(
        self,
        url: str = PUBLIC_WS_URL,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_open: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
    ):
        self.url = url

        self.on_message_callback = on_message
        self.on_error_callback = on_error
        self.on_open_callback = on_open
        self.on_close_callback = on_close

        self.ws = None
        self.thread = None

        self.connected = False
        self.stop_requested = False

        self.reconnect_enabled = True
        self.reconnect_delay = 3

        self._lock = threading.Lock()

    # -----------------------------------------
    # CONNECTION
    # -----------------------------------------

    def connect(self, background: bool = True):
        """
        Connect to the configured WebSocket.

        background=True runs the WebSocket in a daemon thread.
        """

        if self.connected:
            return

        self.stop_requested = False

        if background:
            self.thread = threading.Thread(
                target=self._run,
                daemon=True,
            )
            self.thread.start()
        else:
            self._run()

    def _run(self):
        while not self.stop_requested:

            try:
                self.ws = websocket.WebSocketApp(
                    self.url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )

                self.ws.run_forever(
                    ping_interval=20,
                    ping_timeout=10,
                )

            except Exception as exc:
                self._handle_error(exc)

            if self.stop_requested:
                break

            if not self.reconnect_enabled:
                break

            time.sleep(self.reconnect_delay)

    # -----------------------------------------
    # CALLBACKS
    # -----------------------------------------

    def _on_open(self, ws):
        self.connected = True

        print(
            "[DERIV WS] CONNECTED"
        )

        if self.on_open_callback:
            self.on_open_callback(self)

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = message

        if self.on_message_callback:
            self.on_message_callback(data)

    def _on_error(self, ws, error):
        self.connected = False

        self._handle_error(error)

        if self.on_error_callback:
            self.on_error_callback(error)

    def _on_close(
        self,
        ws,
        close_status_code,
        close_msg,
    ):
        self.connected = False

        print(
            "[DERIV WS] DISCONNECTED"
        )

        if self.on_close_callback:
            self.on_close_callback(
                close_status_code,
                close_msg,
            )

    # -----------------------------------------
    # SEND
    # -----------------------------------------

    def send(self, payload: dict):
        """
        Send a JSON request through the WebSocket.
        """

        if not self.connected or self.ws is None:
            raise DerivWebSocketError(
                "WebSocket is not connected."
            )

        message = json.dumps(payload)

        with self._lock:
            self.ws.send(message)

    # -----------------------------------------
    # PING
    # -----------------------------------------

    def ping(self):
        if self.ws is not None and self.connected:
            try:
                self.ws.sock.ping()
            except Exception as exc:
                self._handle_error(exc)

    # -----------------------------------------
    # STATUS
    # -----------------------------------------

    def status(self) -> dict:
        return {
            "connected": self.connected,
            "url": self.url,
            "reconnect_enabled": self.reconnect_enabled,
            "stop_requested": self.stop_requested,
        }

    # -----------------------------------------
    # STOP
    # -----------------------------------------

    def disconnect(self):
        self.stop_requested = True
        self.reconnect_enabled = False

        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass

        self.connected = False

    # -----------------------------------------
    # ERROR HANDLING
    # -----------------------------------------

    def _handle_error(self, error):
        print(
            f"[DERIV WS ERROR] {error}"
        )
