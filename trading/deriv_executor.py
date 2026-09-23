import json
import threading
import time
from typing import Any, Optional

from deriv.auth import DerivAuthenticator, DerivAuthenticationError


class DerivExecutionError(Exception):
    """Raised when a Deriv execution operation fails."""


class DerivExecutionClient:
    def check_market_hours(self, symbol="frxXAUUSD"):
        """Check Deriv's public trading schedule for a symbol."""
        import json
        import threading
        import time
        import websocket

        result = {}
        event = threading.Event()

        def on_message(ws, message):
            nonlocal result
            try:
                result = json.loads(message)
            except Exception:
                result = {"error": {"message": message}}
            finally:
                event.set()

        def on_error(ws, error):
            nonlocal result
            result = {"error": {"message": str(error)}}
            event.set()

        ws = websocket.WebSocketApp(
            "wss://api.derivws.com/trading/v1/options/ws/public",
            on_message=on_message,
            on_error=on_error,
        )

        thread = threading.Thread(target=ws.run_forever, daemon=True)
        thread.start()

        # Give the public connection time to open.
        time.sleep(0.5)

        ws.send(json.dumps({
            "trading_times": 1
        }))

        if not event.wait(10):
            ws.close()
            return {
                "symbol": symbol,
                "status": "UNKNOWN",
                "open": None,
                "message": "Trading schedule request timed out."
            }

        ws.close()

        if "error" in result:
            raise DerivExecutionError(
                f"Trading schedule error: "
                f"{result['error'].get('message', result['error'])}"
            )

        # The endpoint returns hierarchical market/submarket/symbol data.
        def find_symbol(obj):
            if isinstance(obj, dict):
                if obj.get("symbol") == symbol:
                    return obj
                for value in obj.values():
                    found = find_symbol(value)
                    if found:
                        return found
            elif isinstance(obj, list):
                for item in obj:
                    found = find_symbol(item)
                    if found:
                        return found
            return None

        schedule = find_symbol(result)

        if schedule is None:
            return {
                "symbol": symbol,
                "status": "UNKNOWN",
                "open": None,
                "message": "No schedule entry found for the symbol."
            }

        return {
            "symbol": symbol,
            "status": "SCHEDULE_AVAILABLE",
            "open": None,
            "schedule": schedule,
            "message": "Deriv trading schedule received."
        }


    def __init__(
        self,
        authenticator: Optional[DerivAuthenticator] = None,
        *,
        timeout: float = 15.0,
    ):
        self.authenticator = authenticator or DerivAuthenticator()
        self.timeout = timeout

        self.ws = None
        self.connected = False

        self._lock = threading.Lock()
        self._counter = 0
        self._responses: dict[int, dict[str, Any]] = {}
        self._events: dict[int, threading.Event] = {}

    def _next_req_id(self) -> int:
        with self._lock:
            self._counter += 1
            return self._counter

    def connect(self) -> None:
        """
        Obtain the authenticated WebSocket URL and connect.

        No trade is placed.
        """

        try:
            url = self.authenticator.get_authenticated_websocket_url()
        except DerivAuthenticationError as exc:
            raise DerivExecutionError(str(exc)) from exc

        try:
            import websocket
        except ImportError as exc:
            raise DerivExecutionError(
                "websocket-client is not installed."
            ) from exc

        opened = threading.Event()
        connection_error: list[Exception] = []

        def on_open(ws):
            self.connected = True
            opened.set()

        def on_message(ws, message):
            try:
                data = json.loads(message)
            except (TypeError, ValueError):
                return

            req_id = data.get("req_id")

            if req_id is not None:
                try:
                    req_id = int(req_id)
                except (TypeError, ValueError):
                    return

                with self._lock:
                    self._responses[req_id] = data
                    event = self._events.get(req_id)

                if event:
                    event.set()

        def on_error(ws, error):
            if not opened.is_set():
                connection_error.append(
                    DerivExecutionError(str(error))
                )

        def on_close(ws, close_status_code, close_msg):
            self.connected = False

        self.ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        thread = threading.Thread(
            target=self.ws.run_forever,
            daemon=True,
        )
        thread.start()

        if not opened.wait(timeout=self.timeout):
            self.connected = False

            if connection_error:
                raise connection_error[0]

            raise DerivExecutionError(
                "Timed out connecting to authenticated Deriv WebSocket."
            )

    def request(
        self,
        payload: dict[str, Any],
        *,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Send an authenticated WebSocket request and wait for its response.

        This method does not restrict the operation type; callers must
        apply the execution guard before sending trading requests.
        """

        if not self.connected or self.ws is None:
            raise DerivExecutionError(
                "Authenticated Deriv WebSocket is not connected."
            )

        req_id = self._next_req_id()

        request = dict(payload)
        request["req_id"] = req_id

        event = threading.Event()

        with self._lock:
            self._events[req_id] = event

        try:
            self.ws.send(json.dumps(request))

            wait_timeout = (
                self.timeout
                if timeout is None
                else timeout
            )

            if not event.wait(timeout=wait_timeout):
                raise DerivExecutionError(
                    f"Timed out waiting for Deriv response "
                    f"(req_id={req_id})."
                )

            with self._lock:
                response = self._responses.pop(req_id, None)

            if not response:
                raise DerivExecutionError(
                    f"Missing Deriv response (req_id={req_id})."
                )

            if "error" in response:
                error = response["error"]

                if isinstance(error, dict):
                    code = error.get("code", "UnknownError")
                    message = error.get("message", "Unknown Deriv error")
                    raise DerivExecutionError(
                        f"{code}: {message}"
                    )

                raise DerivExecutionError(str(error))

            return response

        finally:
            with self._lock:
                self._events.pop(req_id, None)

    def protected_proposal(self, parameters):
        """
        Request a proposal while converting Deriv market-closed
        responses into a clean MARKET_CLOSED result.
        No buy/order is performed here.
        """
        try:
            return {
                "status": "PROPOSAL_SUCCESS",
                "closed": False,
                "response": self.request({
                    "proposal": 1,
                    **parameters,
                }),
            }

        except DerivExecutionError as exc:
            status = deriv_market_closed_error(exc)

            if status["closed"]:
                return {
                    "status": "MARKET_CLOSED",
                    "closed": True,
                    "message": status["message"],
                }

            raise

    def ping(self) -> dict[str, Any]:
        return self.request({"ping": 1})

    def portfolio(self) -> dict[str, Any]:
        """
        Retrieve currently open positions.

        This is read-only.
        """
        return self.request({"portfolio": 1})

    def proposal(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """
        Request a trading proposal.

        This does NOT buy the contract.
        """
        payload = {
            "proposal": 1,
            **parameters,
        }

        return self.request(payload)


    def buy(self, proposal_id, price, *, demo=True):
        """
        Execute a Deriv contract purchase.

        Demo-only safety:
        real trading is explicitly refused.
        """
        if not demo:
            raise DerivExecutionError(
                "Real trading is disabled. Demo execution is required."
            )

        if not self.connected:
            raise DerivExecutionError(
                "Execution client is not connected."
            )

        if not proposal_id:
            raise DerivExecutionError(
                "Missing proposal_id."
            )

        try:
            buy_price = float(price)
        except (TypeError, ValueError):
            raise DerivExecutionError(
                "Invalid buy price."
            )

        if buy_price <= 0:
            raise DerivExecutionError(
                "Invalid buy price."
            )

        return self.request({
            "buy": str(proposal_id),
            "price": buy_price,
        })



    def sell(self, contract_id, price=0, *, demo=True):
        """
        Close an open Deriv contract.

        Demo-only safety:
        real trading is explicitly refused.
        price=0 requests a market close.
        """
        if not demo:
            raise DerivExecutionError(
                "Real trading is disabled. Demo execution is required."
            )

        if not self.connected:
            raise DerivExecutionError(
                "Execution client is not connected."
            )

        if not contract_id:
            raise DerivExecutionError(
                "Missing contract_id."
            )

        close_price = float(price)

        if close_price < 0:
            raise DerivExecutionError(
                "Close price cannot be negative."
            )

        return self.request({
            "sell": contract_id,
            "price": close_price,
        })


    def disconnect(self) -> None:
        if self.ws is not None:
            try:
                self.ws.close()
            except Exception:
                pass

        self.ws = None
        self.connected = False

# ============================================================
# MARKET-CLOSED PROTECTION
# ============================================================

def deriv_market_closed_error(error):
    """
    Convert Deriv's market-closed response into a simple
    boolean/status that the application can handle.
    """
    message = str(error)

    if (
        "Trading is not available" in message
        or "ContractBuyValidationError" in message
        or "MarketIsClosed" in message
    ):
        return {
            "closed": True,
            "status": "MARKET_CLOSED",
            "message": message,
        }

    return {
        "closed": False,
        "status": "ERROR",
        "message": message,
    }
