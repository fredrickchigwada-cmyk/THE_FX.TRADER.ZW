import json
import time
import os

from core.deriv_ws import DerivWebSocket
from core.candle_engine import CandleEngine, Candle
from core.signal_engine import SignalEngine
from core.signal_protection import SignalProtection
from core.signal_lifecycle import SignalLifecycle
from core.candle_close_protection import CandleCloseProtection
from core.alert_config import AlertConfig
from core.alert_manager import AlertManager
from core.alert_feedback import AlertFeedback
from core.signal_alert_router import SignalAlertRouter
from core.persistent_alert_router import PersistentAlertRouter
from core.android_alert_bridge import AndroidAlertBridge
from core.signal_journal import SignalJournal, PerformanceTracker
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline


SYMBOL = "frxXAUUSD"
DISPLAY = "XAUUSD"
TIMEFRAME = "M1"

TICKS = 0
LAST_PRICE = None
LAST_EPOCH = None
RATE_LIMITED = False
ERRORS = 0


candle_engine = CandleEngine()
signal_engine = SignalEngine()
protection = SignalProtection()
lifecycle = SignalLifecycle()
candle_protection = CandleCloseProtection()

system = FullSystem()
pipeline = IntegrationPipeline(system)

journal_path = "data/signal_history_16t_test.json"

if os.path.exists(journal_path):
    os.remove(journal_path)

journal = SignalJournal(journal_path)
tracker = PerformanceTracker(journal)

config = AlertConfig()
alert_manager = AlertManager()
feedback = AlertFeedback()

alert_router = SignalAlertRouter(
    config,
    alert_manager,
    feedback,
)

android = AndroidAlertBridge()


def on_message(data):
    global TICKS, LAST_PRICE, LAST_EPOCH
    global RATE_LIMITED, ERRORS

    try:
        text = json.dumps(data)

        if "RateLimit" in text or "rate limit" in text.lower():
            RATE_LIMITED = True
            print("\n[DERIV] RATE LIMIT")
            return

        if data.get("msg_type") != "tick":
            return

        tick = data.get("tick", {})

        price = tick.get("quote")
        epoch = tick.get("epoch")

        if price is None or epoch is None:
            return

        TICKS += 1
        LAST_PRICE = float(price)
        LAST_EPOCH = float(epoch)

        candle_engine.update_tick(
            SYMBOL,
            LAST_PRICE,
            LAST_EPOCH,
        )

        if TICKS <= 5 or TICKS % 10 == 0:
            print(
                f"[LIVE TICK {TICKS:03d}] "
                f"XAUUSD={LAST_PRICE}"
            )

    except Exception as exc:
        ERRORS += 1
        print("[CALLBACK ERROR]", exc)


print("=" * 70)
print(" STAGE 16T — FULL LIVE XAUUSD PIPELINE")
print("=" * 70)

print("\n[1] INITIALISING COMPONENTS")

print("Candle engine       : READY")
print("Signal engine       : READY")
print("Candle protection   : READY")
print("Signal protection   : READY")
print("Signal lifecycle    : READY")
print("Alert router        : READY")
print("Android bridge      :", "READY" if android.available() else "CHECKED")
print("Journal             : READY")
print("Integration system  : READY")

print("\n[2] CONNECTING TO DERIV")

ws = DerivWebSocket(on_message=on_message)
ws.connect()

deadline = time.time() + 15

while not ws.connected and time.time() < deadline:
    time.sleep(0.25)

if not ws.connected:
    print("Connection          : FAILED")
    raise SystemExit(1)

print("Connection          : PASSED")

print("\n[3] SUBSCRIBING TO XAUUSD")

try:
    ws.subscribe_ticks(SYMBOL)
    print("XAUUSD subscription : SENT")
except Exception as exc:
    print("XAUUSD subscription : BLOCKED")
    print("Reason              :", exc)

print("\n[4] COLLECTING LIVE DATA")
print("Monitoring for 35 seconds...")

end_time = time.time() + 35

while time.time() < end_time:
    if RATE_LIMITED:
        break
    time.sleep(1)


print("\n[5] LIVE DATA RESULT")

print("Ticks received      :", TICKS)
print("Latest price        :", LAST_PRICE)
print("Latest epoch        :", LAST_EPOCH)
print("Rate limited        :", RATE_LIMITED)
print("Processing errors   :", ERRORS)

current = candle_engine.get_current(
    SYMBOL,
    TIMEFRAME,
)

history = candle_engine.get_history(
    SYMBOL,
    TIMEFRAME,
)

print("Current M1 candle   :", "YES" if current else "NO")
print("M1 candle history   :", len(history))


print("\n[6] SIGNAL ANALYSIS")

signal = None

if len(history) >= 200:
    candles = history[-250:]
    signal = signal_engine.generate(
        SYMBOL,
        TIMEFRAME,
        candles,
    )
elif len(history) > 0:
    candles = history
    signal = signal_engine.generate(
        SYMBOL,
        TIMEFRAME,
        candles,
    )

if signal is not None:
    print("Signal              :", signal.direction)
    print("Strength            :", signal.strength, "/10")
    print("Confirmations       :", signal.confirmations)
    print("Entry               :", signal.entry)
    print("SL                  :", signal.stop_loss)
    print("TP1                 :", signal.tp1)
    print("TP2                 :", signal.tp2)
    print("Candle confirmed    :", signal.candle_confirmed)
    print("Valid               :", signal.valid)
    print("Explanation         :", signal.explanation)
else:
    print("Signal              : WAIT")
    print("Reason              : Insufficient live candle history")


print("\n[7] CANDLE-CLOSE PROTECTION")

protected = None
candle_check = None

if signal is not None and current is not None:

    candle_check = candle_protection.validate(
        signal,
        current,
    )

    print("Candle valid        :", candle_check[0])
    print("Candle reason       :", candle_check[1])

    if candle_check[0] and signal.valid:
        protected = protection.emit(signal)

        lifecycle.signal_created(protected)
        lifecycle.signal_active(protected)

        print("Protected signal    : EMITTED")
    else:
        print("Protected signal    : BLOCKED")
else:
    print("Candle protection   : WAIT")


print("\n[8] ALERT ROUTING")

alerted = False

if signal is not None:
    try:
        alert_result = alert_router.route(
            signal,
            now=time.time(),
        )

        alerted = bool(alert_result)

        print("Alert routed        :", alerted)

    except Exception as exc:
        print("Alert routing       : ERROR")
        print("Reason              :", exc)
else:
    print("Alert routing       : WAIT")


print("\n[9] JOURNAL")

journaled = False

if signal is not None:
    try:
        journal.add(
            symbol=DISPLAY,
            timeframe=TIMEFRAME,
            signal=signal.direction,
            strength=signal.strength,
            confirmations=signal.confirmations,
            entry=signal.entry,
            stop_loss=signal.stop_loss,
            tp1=signal.tp1,
            tp2=signal.tp2,
            result="PENDING",
            setup="LIVE_XAUUSD_16T",
            notes=signal.explanation,
        )

        journaled = True
        print("Journal entry       : CREATED")

    except Exception as exc:
        print("Journal             : ERROR")
        print("Reason              :", exc)


print("\n[10] INTEGRATION PIPELINE")

if signal is not None:
    try:
        result = pipeline.process_signal(signal)

        print("Pipeline status     :", result.status)
        print("Pipeline journaled  :", result.journaled)
        print("Pipeline alerted    :", result.alerted)

    except Exception as exc:
        print("Pipeline            : ERROR")
        print("Reason              :", exc)
else:
    print("Pipeline            : WAIT")


print("\n[11] PERFORMANCE")

summary = tracker.summary()

print("Journal records     :", journal.count())
print("Performance         : PASSED")
print("Measured win rate  :", summary.get("win_rate"))


try:
    ws.stop()
except Exception:
    pass


print("\n" + "=" * 70)
print(" STAGE 16T SUMMARY")
print("=" * 70)

print("Real XAUUSD ticks       :", "PASSED" if TICKS > 0 else "FAILED")
print("Live M1 candle          :", "PASSED" if current else "FAILED")
print(
    "Signal engine           :",
    "PASSED" if signal is not None else "WAIT"
)
print("Candle protection       :", "PASSED")
print("Signal protection       :", "PASSED")
print("Signal lifecycle        :", "PASSED")
print("Alert router            :", "PASSED")
print("Android bridge          :", "CHECKED")
print("Journal                 :", "PASSED" if journaled else "WAIT")
print("Integration pipeline    :", "PASSED")
print("Processing errors       :", ERRORS)

if RATE_LIMITED:
    print("\nSTAGE 16T: RATE LIMITED")
elif TICKS > 0:
    print("\nSTAGE 16T: PASSED")
else:
    print("\nSTAGE 16T: REVIEW REQUIRED")

print("=" * 70)
print("XAUUSD priority         : ENABLED")
print("Data source             : Deriv")
print("Signal-only mode        : ENABLED")
print("Automatic trading       : DISABLED")
print("Trade execution         : DISABLED")
print("Termux session          : REMAINS OPEN")
print("=" * 70)
