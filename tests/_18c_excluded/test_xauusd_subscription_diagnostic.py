import json
import time
import websocket

WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"
SYMBOL = "frxXAUUSD"

messages = 0
ticks = 0
opened = False


def on_open(ws):
    global opened

    opened = True

    print("[OPEN] Deriv WebSocket connected")
    print("[SEND] Requesting XAUUSD:", SYMBOL)

    ws.send(json.dumps({
        "ticks": SYMBOL,
        "subscribe": 1,
    }))


def on_message(ws, message):
    global messages, ticks

    messages += 1

    try:
        data = json.loads(message)
    except Exception:
        print("[RAW]", message)
        return

    msg_type = data.get("msg_type")

    print()
    print(f"[MESSAGE {messages}] type={msg_type}")

    if msg_type == "tick":

        tick = data.get("tick", {})

        if tick.get("symbol") == SYMBOL:
            ticks += 1

            print("  symbol :", tick.get("symbol"))
            print("  quote  :", tick.get("quote"))
            print("  epoch  :", tick.get("epoch"))

    elif msg_type == "error":

        print("  DERIV ERROR:")
        print(
            json.dumps(
                data,
                indent=2
            )
        )

    else:

        print(
            json.dumps(
                data,
                indent=2
            )
        )


def on_error(ws, error):
    print()
    print("[WEBSOCKET ERROR]")
    print(error)


def on_close(ws, code, reason):
    print()
    print("[CLOSED]")
    print("code  :", code)
    print("reason:", reason)


print()
print("=" * 80)
print(" XAUUSD SUBSCRIPTION DIAGNOSTIC")
print("=" * 80)
print()

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

import threading

thread = threading.Thread(
    target=ws.run_forever,
    kwargs={
        "ping_interval": 20,
        "ping_timeout": 10,
    },
    daemon=True,
)

thread.start()

for _ in range(30):

    if opened:
        break

    time.sleep(1)

if not opened:
    print("FAILED: WebSocket did not open.")
    raise SystemExit(1)

print()
print("Waiting 45 seconds for Deriv responses/ticks...")
print()

time.sleep(45)

try:
    ws.close()
except Exception:
    pass

print()
print("=" * 80)
print(" DIAGNOSTIC RESULT")
print("=" * 80)
print()
print("Messages received :", messages)
print("XAUUSD ticks      :", ticks)
print()

if ticks > 0:
    print("RESULT: XAUUSD LIVE DATA AVAILABLE")
elif messages > 0:
    print("RESULT: DERIV RESPONDED — inspect messages above")
else:
    print("RESULT: NO RESPONSE AFTER SUBSCRIPTION")

print()
print("No trading or order functionality was used.")
print("Signal-only verification.")
print()
