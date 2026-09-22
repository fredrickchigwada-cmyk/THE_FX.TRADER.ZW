import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.deriv_ws import DerivWebSocket

received = []

def on_message(data):
    if isinstance(data, dict) and "active_symbols" in data:
        received.extend(data["active_symbols"])

print("=" * 60)
print("DERIV ACTIVE SYMBOL INSPECTION")
print("=" * 60)

ws = DerivWebSocket(on_message=on_message)

try:
    ws.connect()

    deadline = time.time() + 15
    while not ws.connected and time.time() < deadline:
        time.sleep(0.25)

    if not ws.connected:
        print("ERROR: WebSocket did not connect.")
    else:
        print("Connected: YES")
        ws.request_active_symbols()

        deadline = time.time() + 15
        while not received and time.time() < deadline:
            time.sleep(0.25)

        print()
        print("Active symbols received:", len(received))
        print("-" * 60)

        for i, item in enumerate(received, 1):
            if isinstance(item, dict):
                print(
                    f"{i:02d}. "
                    f"symbol={item.get('symbol')!r} | "
                    f"display_name={item.get('display_name')!r} | "
                    f"underlying_symbol={item.get('underlying_symbol')!r} | "
                    f"underlying_symbol_name={item.get('underlying_symbol_name')!r}"
                )

finally:
    try:
        ws.stop()
    except Exception:
        pass

print("=" * 60)
print("INSPECTION COMPLETE")
print("=" * 60)
