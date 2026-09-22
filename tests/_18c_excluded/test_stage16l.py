import json
import time
from pathlib import Path

from core.deriv_ws import DerivWebSocket
from core.candle_engine import CandleEngine
from core.candle_engine import Candle
from core.signal_engine import SignalEngine
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline


SYMBOL = "frxXAUUSD"
TIMEFRAME = "M1"

HISTORY_FILE = Path(
    "data/historical_bootstrap/frxXAUUSD_M1.json"
)

LIVE_SECONDS = 30


def load_history():

    if not HISTORY_FILE.exists():
        return []

    data = json.loads(
        HISTORY_FILE.read_text(
            encoding="utf-8"
        )
    )

    if isinstance(data, dict):
        return data.get("candles", [])

    return data


def build_history(raw):

    candles = []

    for item in raw:

        try:

            start = int(
                float(
                    item.get(
                        "epoch",
                        item.get("start")
                    )
                )
            )

            candles.append(
                Candle(
                    symbol=SYMBOL,
                    timeframe=TIMEFRAME,
                    start=start,
                    end=start + 60,
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(
                        item.get("volume", 0)
                    ),
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

    return candles


print()
print("=" * 100)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16L — REAL-TIME XAUUSD PIPELINE")
print("=" * 100)
print()

history = build_history(load_history())

print(
    f"Historical M1 candles : {len(history)}"
)

if len(history) < 200:

    print(
        "ERROR: Fewer than 200 historical candles."
    )

    raise SystemExit(1)

print("Historical base       : READY")
print(f"Live symbol            : {SYMBOL}")
print()


# ---------------------------------------------------------
# Core components
# ---------------------------------------------------------

ws = None
candle_engine = CandleEngine()
signal_engine = SignalEngine()

system = FullSystem()
pipeline = IntegrationPipeline(system)

tick_count = 0
last_price = None
last_epoch = None
live_candle = None
errors = []


# ---------------------------------------------------------
# Raw message callback
# ---------------------------------------------------------

system = FullSystem()
pipeline = IntegrationPipeline(system)


def handle_message(message):

    global tick_count
    global last_price
    global last_epoch
    global live_candle

    try:
        if not isinstance(message, dict):
            return

        if message.get("msg_type") != "tick":
            return

        tick = message.get("tick") or {}

        if tick.get("symbol") != SYMBOL:
            return

        if tick.get("quote") is None:
            return

        last_price = float(tick["quote"])
        last_epoch = float(
            tick.get("epoch", time.time())
        )

        tick_count += 1

        candle_engine.update_tick(
            SYMBOL,
            last_price,
            last_epoch,
        )

        live_candle = candle_engine.get_current(
            SYMBOL,
            TIMEFRAME,
        )

        print(
            f"[TICK {tick_count:03d}] "
            f"XAUUSD {last_price}"
        )

    except Exception as exc:
        errors.append(str(exc))
        print(f"[TICK ERROR] {exc}")


ws = DerivWebSocket(
    on_message=handle_message
)

# ---------------------------------------------------------
# Connect
# ---------------------------------------------------------

print("[LIVE] Connecting to Deriv...")


try:

    ws.connect()

    # Give the WebSocket thread time to establish.
    time.sleep(3)

except Exception as exc:

    print(
        f"[LIVE] Connection error: {exc}"
    )

    raise SystemExit(1)


if not ws.connected:

    print()
    print(
        "[LIVE] WebSocket did not become connected."
    )

    print(
        "This is a connection-layer issue."
    )

    ws.stop()

    raise SystemExit(1)


print(
    "[LIVE] WebSocket connected."
)


# ---------------------------------------------------------
# Subscribe
# ---------------------------------------------------------

try:

    ws.subscribe_ticks(SYMBOL)

    print(
        "[LIVE] XAUUSD subscription requested."
    )

except Exception as exc:

    print(
        f"[LIVE] Subscription error: {exc}"
    )

    ws.stop()

    raise SystemExit(1)


# ---------------------------------------------------------
# Monitor
# ---------------------------------------------------------

print()
print(
    f"[LIVE] Monitoring for "
    f"{LIVE_SECONDS} seconds..."
)
print()

start = time.time()

while time.time() - start < LIVE_SECONDS:

    time.sleep(1)


# ---------------------------------------------------------
# Stop
# ---------------------------------------------------------

ws.stop()

print()
print("=" * 100)
print(" LIVE RESULT")
print("=" * 100)

print(
    f"Ticks received : {tick_count}"
)

print(
    f"Latest price   : {last_price}"
)

print(
    f"Latest epoch   : {last_epoch}"
)

if live_candle:

    print()
    print("CURRENT M1 CANDLE")

    print(
        f"Start  : {live_candle.start}"
    )

    print(
        f"Open   : {live_candle.open}"
    )

    print(
        f"High   : {live_candle.high}"
    )

    print(
        f"Low    : {live_candle.low}"
    )

    print(
        f"Close  : {live_candle.close}"
    )

    print(
        f"Volume : {live_candle.volume}"
    )

else:

    print(
        "Current candle : NOT AVAILABLE"
    )


# ---------------------------------------------------------
# Live signal check
# ---------------------------------------------------------

if tick_count > 0 and live_candle:

    candles = list(history)

    if candles and candles[-1].start == live_candle.start:

        candles[-1] = live_candle

    else:

        candles.append(live_candle)

    candles = candles[-250:]

    print()
    print("=" * 100)
    print(" LIVE SIGNAL CHECK")
    print("=" * 100)

    try:

        signal = signal_engine.generate(
            SYMBOL,
            TIMEFRAME,
            candles,
        )

        direction = getattr(
            signal,
            "signal",
            "WAIT",
        )

        print(
            f"Signal        : {direction}"
        )

        print(
            f"Strength      : "
            f"{getattr(signal, 'strength', 0)}/10"
        )

        print(
            f"Confirmations : "
            f"{getattr(signal, 'confirmations', 0)}"
        )

        print(
            f"Explanation   : "
            f"{getattr(signal, 'explanation', '')}"
        )

        if direction in ("BUY", "SELL"):

            result = pipeline.process_signal(
                signal
            )

            print()
            print(
                "PIPELINE STATUS : "
                f"{getattr(result, 'status', 'UNKNOWN')}"
            )

            print(
                "PIPELINE JOURNAL: "
                f"{getattr(result, 'journaled', False)}"
            )

            print(
                "PIPELINE ALERTED: "
                f"{getattr(result, 'alerted', False)}"
            )

        else:

            print()
            print(
                "PIPELINE: WAIT — "
                "no directional signal forwarded"
            )

    except Exception as exc:

        errors.append(str(exc))

        print(
            f"LIVE SIGNAL ERROR: {exc}"
        )


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

print()
print("=" * 100)
print(" STAGE 16L SUMMARY")
print("=" * 100)

print(
    f"Historical candles : {len(history)}"
)

print(
    f"Live ticks         : {tick_count}"
)

print(
    f"Live candle        : "
    f"{'YES' if live_candle else 'NO'}"
)

print(
    f"Processing errors   : {len(errors)}"
)

print()

if tick_count > 0 and live_candle:

    print("STAGE 16L: PASSED")

    print()
    print(
        "Real-time XAUUSD ticks successfully "
        "entered the candle pipeline."
    )

else:

    print("STAGE 16L: FAILED")

    print()
    print(
        "No usable live XAUUSD tick stream "
        "was received."
    )

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority    : ENABLED")
print("Data source        : Deriv")
print("Termux session remains open.")
print()
print("=" * 100)
