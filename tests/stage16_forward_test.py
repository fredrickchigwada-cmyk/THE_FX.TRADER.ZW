import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.deriv_ws import DerivWebSocket
from core.market_discovery import MarketDiscovery

SYMBOL = "XAUUSD"

discovery = MarketDiscovery()
messages = []

def on_message(data):
    if not isinstance(data, dict):
        return

    messages.append(data)

    # Feed active-symbol responses into the existing discovery engine.
    if "active_symbols" in data:
        result = discovery.process_response(data)

        print()
        print("[RESPONSE] active_symbols received")
        print("[RESPONSE] markets processed:", len(result))

        market = discovery.get(SYMBOL)

        if market:
            print("[XAUUSD] symbol   :", market.symbol)
            print("[XAUUSD] available:", market.available)

def on_error(error):
    print()
    print("[WEBSOCKET ERROR]", type(error).__name__, ":", error)

print("=" * 60)
print("THE_FX.TRADER.BOT.ZW")
print("STAGE 16A — XAUUSD DERIV CONNECTION TEST")
print("=" * 60)
print()
print("Mode              : SIGNAL ONLY")
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print()

ws = None

try:
    print("[1/5] Creating WebSocket...")

    ws = DerivWebSocket(
        on_message=on_message,
        on_error=on_error,
    )

    print("[OK] WebSocket created")

    print()
    print("[2/5] Starting connection...")

    ws.connect()

    # Wait for the actual connection state.
    deadline = time.time() + 15

    while time.time() < deadline:
        if ws.connected:
            break
        time.sleep(0.25)

    if not ws.connected:
        print("[ERROR] WebSocket did not become connected.")
    else:
        print("[OK] WebSocket connected")

        print()
        print("[3/5] Requesting active symbols...")

        try:
            ws.request_active_symbols()
            print("[OK] Request sent")
        except Exception as exc:
            print(
                "[REQUEST ERROR]",
                type(exc).__name__,
                ":",
                exc
            )

        # Wait for the response.
        deadline = time.time() + 20

        while time.time() < deadline:
            market = discovery.get(SYMBOL)

            if market is not None and market.symbol:
                break

            time.sleep(0.5)

        print()
        print("[4/5] XAUUSD discovery result")

        market = discovery.get(SYMBOL)

        if market is None:
            print("Status    :", discovery.status(SYMBOL))
            print("Available :", False)
            print("Symbol    : None")
        else:
            print("Status    :", discovery.status(SYMBOL))
            print("Available :", market.available)
            print("Symbol    :", market.symbol)

        print()
        print("[5/5] WebSocket diagnostics")
        print("-" * 60)
        print("Connected         :", ws.connected)
        print("Messages received :", ws.messages_received)
        print("Callbacks captured:", len(messages))
        print("Rate limited      :", ws.is_rate_limited())
        print("Stale             :", ws.is_stale(30))
        print("-" * 60)

except KeyboardInterrupt:
    print()
    print("Test stopped by user.")

except Exception as exc:
    print()
    print("[ERROR]", type(exc).__name__, ":", exc)

finally:
    if ws is not None:
        try:
            ws.stop()
        except Exception:
            pass

print()
print("=" * 60)
print("STAGE 16A COMPLETE")
print("=" * 60)
print("No trades were placed.")
print("Termux session remains open.")
print("=" * 60)
