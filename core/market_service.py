import time
import threading

from core.market_discovery import MarketDiscovery
from core.deriv_ws import DerivWebSocket, DerivRateLimitError


class MarketService:
    """
    Connects Deriv's WebSocket market discovery response
    to the MarketDiscovery engine.

    Uses one persistent WebSocket connection and caches
    discovery results to avoid unnecessary API requests.
    """

    CACHE_SECONDS = 300

    def __init__(self):
        self.discovery = MarketDiscovery()

        self.client = DerivWebSocket(
            on_message=self._on_message,
            on_error=self._on_error,
            on_open=self._on_open,
            on_close=self._on_close,
        )

        self.ready = False
        self.last_error = None
        self.last_discovery_request = 0.0

        self._lock = threading.Lock()

    def start(self):
        """Start the persistent Deriv connection."""
        self.client.connect()

    def stop(self):
        """Stop the Deriv connection."""
        self.client.stop()

        with self._lock:
            self.ready = False

    def _on_open(self):
        self.ready = True
        self.last_error = None

        print("[MARKETS] Deriv connection ready")

    def _on_close(self):
        self.ready = False
        print("[MARKETS] Deriv connection closed")

    def _on_error(self, error):
        self.last_error = error
        print(f"[MARKETS] Error: {error!r}")

    def _on_message(self, data):
        if data.get("msg_type") == "active_symbols":
            self._process_active_symbols(data)

    def _process_active_symbols(self, data):
        results = self.discovery.process_response(data)

        print()
        print("========== DERIV MARKET DISCOVERY ==========")

        for market in results:
            status = self.discovery.status(
                market.requested_name
            )

            actual = market.symbol or "NONE"

            print(
                f"{market.requested_name:<18} "
                f"-> {actual:<12} "
                f"{status}"
            )

        print("============================================")
        print()

    def discover(self):
        """
        Request active symbols only when:
        - connected
        - not rate limited
        - cache has expired
        - no request was made too recently
        """

        if not self.ready:
            return False, "NOT_CONNECTED"

        if self.client.is_rate_limited():
            remaining = self.client.rate_limit_remaining()

            return (
                False,
                f"RATE_LIMITED:{remaining:.1f}"
            )

        now = time.time()

        if (
            now - self.last_discovery_request
            < self.CACHE_SECONDS
        ):
            return True, "CACHE_ACTIVE"

        try:
            self.client.request_active_symbols()

            self.last_discovery_request = time.time()

            return True, "REQUEST_SENT"

        except DerivRateLimitError as exc:
            self.last_error = exc

            return False, "RATE_LIMITED"

        except Exception as exc:
            self.last_error = exc

            return False, f"ERROR:{exc}"

    def get_market(self, name):
        return self.discovery.get(name)

    def get_status(self, name):
        return self.discovery.status(name)

    def all_markets(self):
        return self.discovery.all_markets()


if __name__ == "__main__":
    service = MarketService()

    try:
        print("Starting market discovery...")
        service.start()

        # Give WebSocket time to connect.
        time.sleep(2)

        success, status = service.discover()

        print(
            f"[MARKETS] Discovery request: "
            f"{success} / {status}"
        )

        # Allow response to arrive.
        time.sleep(5)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        service.stop()
