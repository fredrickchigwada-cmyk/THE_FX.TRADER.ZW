import json
import time

from core.deriv_ws import DerivWebSocket


SYMBOL = "frxXAUUSD"
TICKS = 0
LAST_PRICE = None
LAST_EPOCH = None
RATE_LIMITED = False


def on_message(data):
    global TICKS, LAST_PRICE, LAST_EPOCH, RATE_LIMITED

    text = json.dumps(data)

    if "RateLimit" in text or "rate limit" in text.lower():
        RATE_LIMITED = True
        print("\n[DERIV] RATE LIMIT RECEIVED")
        print(text)
        return

    if data.get("msg_type") == "tick":
        tick = data.get("tick", {})

        price = tick.get("quote")
        epoch = tick.get("epoch")

        if price is not None:
            TICKS += 1
            LAST_PRICE = price
            LAST_EPOCH = epoch

            print(
                f"[TICK {TICKS:03d}] "
                f"XAUUSD = {price} | epoch={epoch}"
            )


print("=" * 65)
print(" STAGE 16S — CONTROLLED XAUUSD LIVE TEST")
print("=" * 65)

ws = DerivWebSocket(on_message=on_message)

print("\nConnecting to Deriv...")
ws.connect()

deadline = time.time() + 15

while not ws.connected and time.time() < deadline:
    time.sleep(0.25)

print("Connection status :", "CONNECTED" if ws.connected else "FAILED")

if not ws.connected:
    print("\nSTAGE 16S: FAILED — WebSocket did not connect")
    raise SystemExit(1)

print("\nSubscribing ONCE to XAUUSD...")
try:
    ws.subscribe_ticks(SYMBOL)
    print("Subscription request : SENT")
except Exception as exc:
    print("Subscription request : BLOCKED")
    print("Reason :", exc)

print("\nMonitoring for 30 seconds...")

end_time = time.time() + 30

while time.time() < end_time:
    if RATE_LIMITED:
        break

    time.sleep(1)

try:
    ws.stop()
except Exception:
    pass

print("\n" + "=" * 65)
print(" STAGE 16S RESULT")
print("=" * 65)

print("Symbol          :", SYMBOL)
print("Connected       :", ws.connected)
print("Ticks received  :", TICKS)
print("Latest price    :", LAST_PRICE)
print("Latest epoch    :", LAST_EPOCH)
print("Rate limited    :", RATE_LIMITED)

if TICKS > 0:
    print("\nXAUUSD LIVE DATA : PASSED")
    print("STAGE 16S: PASSED")
elif RATE_LIMITED:
    print("\nXAUUSD LIVE DATA : RATE LIMITED")
    print("Stage 16S is blocked by Deriv API rate limiting.")
else:
    print("\nXAUUSD LIVE DATA : NO DATA")
    print("STAGE 16S: REVIEW REQUIRED")

print("=" * 65)
print("Automatic trading : DISABLED")
print("Trade execution    : DISABLED")
print("Signal-only mode   : ENABLED")
print("XAUUSD priority    : ENABLED")
print("Data source        : Deriv")
print("Termux session     : REMAINS OPEN")
print("=" * 65)
