import json
import time
import websocket

URL = "wss://api.derivws.com/trading/v1/options/ws/public"
SYMBOL = "frxXAUUSD"

ticks = 0
last_price = None
last_epoch = None

print()
print("=" * 90)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16L — RAW LIVE XAUUSD FEED")
print("=" * 90)
print()

ws = websocket.WebSocket()
ws.settimeout(5)

print("[LIVE] Connecting to Deriv...")

try:
    ws.connect(URL)

    print("[LIVE] Connected")

    request = {
        "ticks": SYMBOL,
        "subscribe": 1
    }

    ws.send(json.dumps(request))

    print(
        f"[LIVE] Subscription sent: {SYMBOL}"
    )

except Exception as exc:

    print(
        f"[LIVE] CONNECTION ERROR: {exc}"
    )

    ws.close()
    raise SystemExit(1)


start = time.time()

print()
print("[LIVE] Waiting for XAUUSD ticks...")
print()

while time.time() - start < 30:

    try:

        raw = ws.recv()

        if not raw:
            continue

        message = json.loads(raw)

        msg_type = message.get("msg_type")

        if msg_type == "tick":

            tick = message.get("tick", {})

            symbol = tick.get("symbol")
            quote = tick.get("quote")
            epoch = tick.get("epoch")

            if symbol != SYMBOL:
                continue

            if quote is None:
                continue

            ticks += 1
            last_price = float(quote)
            last_epoch = epoch

            print(
                f"[TICK {ticks:03d}] "
                f"XAUUSD = {last_price}"
            )

        elif msg_type == "error":

            error = message.get("error", {})

            print(
                "[DERIV ERROR] "
                f"{error.get('code')} — "
                f"{error.get('message')}"
            )

        elif msg_type == "tick" and not tick:
            print("[LIVE] Empty tick received")

    except websocket.WebSocketTimeoutException:

        continue

    except Exception as exc:

        print(
            f"[LIVE] RECEIVE ERROR: {exc}"
        )

        break


try:
    ws.close()
except Exception:
    pass


print()
print("=" * 90)
print(" STAGE 16L RAW RESULT")
print("=" * 90)

print(
    f"Ticks received : {ticks}"
)

print(
    f"Latest price   : {last_price}"
)

print(
    f"Latest epoch   : {last_epoch}"
)

print()

if ticks > 0:

    print("STAGE 16L RAW: PASSED")

    print()
    print(
        "Direct Deriv WebSocket successfully "
        "received real-time XAUUSD data."
    )

else:

    print("STAGE 16L RAW: FAILED")

    print()
    print(
        "No XAUUSD ticks were received from "
        "the direct WebSocket."
    )

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority   : ENABLED")
print("Data source       : Deriv")
print("Termux session remains open.")
print()
print("=" * 90)
