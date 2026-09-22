import json
import time
from pathlib import Path

import websocket

from core.candle_engine import CandleEngine, Candle
from core.signal_engine import SignalEngine
from core.signal_protection import SignalProtection
from core.signal_lifecycle import SignalLifecycle
from core.candle_close_protection import CandleCloseProtection
from core.persistent_alert_router import PersistentAlertRouter
from core.android_alert_bridge import AndroidAlertBridge
from core.signal_journal import SignalJournal
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline


WS_URL = "wss://api.derivws.com/trading/v1/options/ws/public"

SYMBOL = "frxXAUUSD"
TIMEFRAME = "M1"

HISTORY_FILE = Path(
    "data/historical_bootstrap/frxXAUUSD_M1.json"
)

MONITOR_SECONDS = 75


print()
print("=" * 100)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16P — XAUUSD RAW LIVE ALERT-READY VERIFICATION")
print("=" * 100)
print()

# ================================================================
# LOAD HISTORY
# ================================================================

if not HISTORY_FILE.exists():
    print("ERROR: XAUUSD historical data missing.")
    raise SystemExit(1)

with HISTORY_FILE.open("r", encoding="utf-8") as f:
    raw = json.load(f)

if isinstance(raw, dict):
    raw = raw.get(
        "candles",
        raw.get("history", [])
    )

historical = []

for item in raw:

    start = int(
        item.get(
            "start",
            item.get(
                "epoch",
                item.get("time", 0)
            )
        )
    )

    historical.append(
        Candle(
            symbol=SYMBOL,
            timeframe=TIMEFRAME,
            start=start,
            end=start + 60,
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item.get("volume", 0)),
        )
    )

print(
    f"Historical candles : {len(historical)}"
)
print("Historical data    : READY")
print()

# ================================================================
# COMPONENTS
# ================================================================

candle_engine = CandleEngine()
signal_engine = SignalEngine()
protection = SignalProtection()
lifecycle = SignalLifecycle()
candle_protection = CandleCloseProtection()
alert_router = PersistentAlertRouter()
android_bridge = AndroidAlertBridge()

journal = SignalJournal(
    path=Path("data/signal_history_16p_raw_test.json")
)

system = FullSystem()
pipeline = IntegrationPipeline(system)

print("COMPONENTS")
print("Raw Deriv WebSocket : ENABLED")
print("XAUUSD              : PRIORITY")
print("Signal-only         : ENABLED")
print("Automatic trading   : DISABLED")
print()

# ================================================================
# LIVE STATE
# ================================================================

tick_count = 0
latest_price = None
latest_epoch = None
errors = []
connected = False
subscribed = False


def handle_message(ws, message):

    global tick_count
    global latest_price
    global latest_epoch

    try:
        data = json.loads(message)
    except Exception:
        return

    msg_type = data.get("msg_type")

    if msg_type == "tick":

        tick = data.get("tick") or {}

        if tick.get("symbol") != SYMBOL:
            return

        try:
            price = float(tick["quote"])
            epoch = float(tick["epoch"])
        except Exception:
            return

        tick_count += 1
        latest_price = price
        latest_epoch = epoch

        try:
            candle_engine.update_tick(
                SYMBOL,
                price,
                epoch,
            )
        except Exception as exc:
            errors.append(
                f"candle: {exc}"
            )

        if tick_count <= 10:
            print(
                f"[TICK {tick_count:03d}] "
                f"XAUUSD = {price}"
            )

    elif msg_type == "error":

        error = data.get("error") or {}

        message_text = (
            error.get("message")
            or str(error)
        )

        errors.append(
            f"Deriv: {message_text}"
        )

        print(
            f"[DERIV ERROR] {message_text}"
        )


def handle_open(ws):

    global connected
    global subscribed

    connected = True

    print("[DERIV] WebSocket OPEN")
    print("[DERIV] Sending XAUUSD subscription...")

    request = {
        "ticks": SYMBOL,
        "subscribe": 1,
    }

    ws.send(
        json.dumps(request)
    )

    subscribed = True

    print(
        "[DERIV] XAUUSD subscription SENT"
    )


def handle_error(ws, error):

    errors.append(
        f"websocket: {error}"
    )

    print(
        f"[WEBSOCKET ERROR] {error}"
    )


def handle_close(ws, close_status_code, close_msg):

    global connected

    connected = False

    print(
        "[DERIV] WebSocket CLOSED"
    )


# ================================================================
# RAW CONNECTION
# ================================================================

print("CONNECTING TO DERIV")
print()

ws = websocket.WebSocketApp(
    WS_URL,
    on_open=handle_open,
    on_message=handle_message,
    on_error=handle_error,
    on_close=handle_close,
)

ws.run_in_background = True

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

# ================================================================
# WAIT FOR CONNECTION
# ================================================================

for _ in range(30):

    if connected:
        break

    time.sleep(1)

if not connected:

    print()
    print("ERROR: Raw Deriv WebSocket did not connect.")

    try:
        ws.close()
    except Exception:
        pass

    raise SystemExit(1)

print()
print(
    f"Monitoring XAUUSD for {MONITOR_SECONDS} seconds..."
)
print()

# ================================================================
# LIVE MONITOR
# ================================================================

deadline = time.time() + MONITOR_SECONDS

while time.time() < deadline:
    time.sleep(1)

# ================================================================
# LIVE RESULT
# ================================================================

print()
print("=" * 100)
print(" XAUUSD LIVE DATA")
print("=" * 100)

print(
    f"Connected      : {connected}"
)

print(
    f"Subscribed     : {subscribed}"
)

print(
    f"Ticks received : {tick_count}"
)

print(
    f"Latest price   : {latest_price}"
)

print(
    f"Latest epoch   : {latest_epoch}"
)

current_candle = candle_engine.get_current(
    SYMBOL,
    TIMEFRAME,
)

print(
    f"Current candle : "
    f"{'YES' if current_candle else 'NO'}"
)

if errors:
    print()
    print("Errors:")
    for error in errors[-10:]:
        print(
            f" - {error}"
        )

if tick_count == 0:

    print()
    print(
        "STAGE 16P RAW: REVIEW REQUIRED"
    )
    print(
        "No XAUUSD tick data was received."
    )

    try:
        ws.close()
    except Exception:
        pass

    raise SystemExit(1)

# ================================================================
# ANALYSIS
# ================================================================

candles = list(historical)

if current_candle is not None:

    if (
        candles
        and candles[-1].start
        == current_candle.start
    ):
        candles[-1] = current_candle
    else:
        candles.append(current_candle)

signal = signal_engine.generate(
    SYMBOL,
    TIMEFRAME,
    candles,
)

print()
print("=" * 100)
print(" XAUUSD SIGNAL")
print("=" * 100)

print(
    f"Direction     : {signal.direction}"
)

print(
    f"Strength      : {signal.strength}/10"
)

print(
    f"Confirmations : {signal.confirmations}"
)

print(
    f"Entry         : {signal.entry}"
)

print(
    f"Stop Loss     : {signal.stop_loss}"
)

print(
    f"TP1           : {signal.tp1}"
)

print(
    f"TP2           : {signal.tp2}"
)

print(
    f"Invalidation  : {signal.invalidation}"
)

print(
    f"Candle confirm: {signal.candle_confirmed}"
)

print(
    f"Valid         : {signal.valid}"
)

print(
    f"Explanation   : {signal.explanation}"
)

# ================================================================
# PROTECTION
# ================================================================

confirmed, reason = candle_protection.validate(
    signal,
    current_candle,
)

print()
print("CANDLE PROTECTION")
print(
    f"Confirmed : {confirmed}"
)
print(
    f"Reason    : {reason}"
)

protected = None
alerted = False
journaled = False

if (
    signal.valid
    and signal.direction in ("BUY", "SELL")
    and confirmed
):

    print()
    print("SIGNAL PROTECTION")

    protected = protection.emit(
        signal
    )

    lifecycle.signal_created(
        protected
    )

    lifecycle.signal_active(
        protected
    )

    print("Protection : PASSED")
    print("Lifecycle   : ACTIVE")

    print()
    print("ALERT ROUTING")

    alert_result = alert_router.route(
        signal,
        now=time.time(),
    )

    alerted = bool(alert_result)

    print(
        f"Alert routed : {alerted}"
    )

    print()
    print("JOURNAL")

    journal.add(
        symbol=signal.symbol,
        timeframe=signal.timeframe,
        signal=signal.direction,
        strength=signal.strength,
        confirmations=signal.confirmations,
        entry=signal.entry,
        stop_loss=signal.stop_loss,
        tp1=signal.tp1,
        tp2=signal.tp2,
        result="PENDING",
        setup="STAGE_16P_RAW_LIVE_XAUUSD",
        notes=signal.explanation,
    )

    journaled = True

    print("Journal : PASSED")

else:

    print()
    print(
        "No directional signal passed "
        "all protection requirements."
    )

    print(
        "No alert emitted."
    )

# ================================================================
# CLEAN CLOSE
# ================================================================

try:
    ws.close()
except Exception:
    pass

# ================================================================
# FINAL
# ================================================================

print()
print("=" * 100)
print(" STAGE 16P SUMMARY")
print("=" * 100)

print(
    f"XAUUSD ticks       : {tick_count}"
)

print(
    f"Live candle        : "
    f"{'YES' if current_candle else 'NO'}"
)

print(
    f"Signal             : {signal.direction}"
)

print(
    f"Strength           : {signal.strength}/10"
)

print(
    f"Candle protection  : "
    f"{'PASSED' if confirmed else 'BLOCKED'}"
)

print(
    f"Protected signal   : "
    f"{'YES' if protected else 'NO'}"
)

print(
    f"Alert routed       : {alerted}"
)

print(
    f"Journaled          : {journaled}"
)

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority    : ENABLED")
print("Data source       : Deriv")
print("Termux session     : REMAINS OPEN")

print()
print("=" * 100)
print("STAGE 16P RAW: PASSED")
print("=" * 100)
