from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

from core.deriv_ws import DerivWebSocket, DerivRateLimitError


XAUUSD_SYMBOL = "frxXAUUSD"


@dataclass
class XAUUSDTick:
    symbol: str
    quote: float
    epoch: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    tick_id: Optional[str] = None
    pip_size: Optional[int] = None

    @property
    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self.epoch, tz=timezone.utc)

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "quote": self.quote,
            "epoch": self.epoch,
            "bid": self.bid,
            "ask": self.ask,
            "tick_id": self.tick_id,
            "pip_size": self.pip_size,
            "datetime_utc": self.datetime_utc.isoformat(),
        }


class XAUUSDMarketData:
    def __init__(
        self,
        on_tick: Optional[Callable[[XAUUSDTick], None]] = None,
        on_status: Optional[Callable[[str], None]] = None,
    ):
        self.on_tick = on_tick
        self.on_status = on_status

        self._client = None
        self._lock = threading.Lock()

        self._connected = False
        self._running = False
        self._market_open = False

        self._last_tick = None
        self._last_error = None
        self._last_update_time = None

        # Prevent the subscribe call from racing the WebSocket connection.
        self._connected_event = threading.Event()

    @property
    def connected(self):
        return self._connected

    @property
    def market_open(self):
        return self._market_open

    @property
    def last_tick(self):
        return self._last_tick

    @property
    def last_error(self):
        return self._last_error

    def _status(self, value: str):
        print(f"[XAUUSD] STATUS: {value}")

        if self.on_status:
            try:
                self.on_status(value)
            except Exception:
                pass

    def _on_open(self):
        with self._lock:
            self._connected = True
            self._last_error = None

        self._connected_event.set()
        self._status("CONNECTED")

    def _on_error(self, error):
        message = str(error)

        with self._lock:
            self._last_error = message

        lower = message.lower()

        if "marketisclosed" in lower or "market is closed" in lower:
            with self._lock:
                self._market_open = False

            self._status("MARKET_CLOSED")
            return

        if (
            isinstance(error, DerivRateLimitError)
            or "rate limit" in lower
            or "ratelimit" in lower
        ):
            self._status("RATE_LIMITED")
            return

        self._status("ERROR")

    def _on_message(self, message):
        if not isinstance(message, dict):
            return

        # Deriv error response
        error = message.get("error")

        if error:
            error_code = str(error.get("code", ""))
            error_message = str(error.get("message", ""))

            combined = f"{error_code} {error_message}".lower()

            if "marketisclosed" in combined or "market is closed" in combined:
                with self._lock:
                    self._market_open = False
                    self._last_error = error_message

                self._status("MARKET_CLOSED")
                return

            if "rate limit" in combined or "ratelimit" in combined:
                with self._lock:
                    self._last_error = error_message

                self._status("RATE_LIMITED")
                return

            with self._lock:
                self._last_error = error_message

            self._status("ERROR")
            return

        # Only process tick messages.
        if message.get("msg_type") != "tick":
            return

        tick = message.get("tick")

        if not isinstance(tick, dict):
            return

        symbol = tick.get("symbol")

        if symbol and symbol != XAUUSD_SYMBOL:
            return

        try:
            quote = float(tick["quote"])
            epoch = int(tick["epoch"])
        except (KeyError, TypeError, ValueError):
            return

        parsed = XAUUSDTick(
            symbol=symbol or XAUUSD_SYMBOL,
            quote=quote,
            epoch=epoch,
            bid=self._float_or_none(tick.get("bid")),
            ask=self._float_or_none(tick.get("ask")),
            tick_id=tick.get("id"),
            pip_size=self._int_or_none(tick.get("pip_size")),
        )

        with self._lock:
            self._last_tick = parsed
            self._last_update_time = time.time()
            self._market_open = True
            self._last_error = None

        self._status("MARKET_OPEN")

        if self.on_tick:
            try:
                self.on_tick(parsed)
            except Exception as exc:
                print(f"[XAUUSD] Tick callback error: {exc}")

    @staticmethod
    def _float_or_none(value):
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int_or_none(value):
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def start(self, timeout: float = 10.0):
        if self._running:
            return

        self._running = True
        self._connected_event.clear()

        try:
            self._client = DerivWebSocket(
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
            )

            # Start the socket connection first.
            self._client.connect()

            # Wait until the WebSocket callback confirms the connection.
            if not self._connected_event.wait(timeout):
                self._running = False
                self._status("DISCONNECTED")
                raise RuntimeError(
                    "WebSocket connection timeout"
                )

            # Only subscribe after connection is confirmed.
            try:
                self._client.subscribe_ticks(XAUUSD_SYMBOL)

            except DerivRateLimitError as exc:
                self._on_error(exc)

            except Exception as exc:
                message = str(exc)

                if "rate limit" in message.lower():
                    self._on_error(DerivRateLimitError(message))
                else:
                    self._on_error(exc)

        except Exception:
            self._running = False
            self._status("DISCONNECTED")
            raise

    def stop(self):
        self._running = False
        self._connected_event.clear()

        client = self._client

        if client is not None:
            try:
                client.disconnect()
            except Exception:
                pass

        with self._lock:
            self._connected = False

        self._status("DISCONNECTED")

    def snapshot(self):
        with self._lock:
            tick = self._last_tick

            return {
                "symbol": XAUUSD_SYMBOL,
                "connected": self._connected,
                "market_open": self._market_open,
                "last_error": self._last_error,
                "last_update_time": self._last_update_time,
                "last_tick": tick.to_dict() if tick else None,
            }
