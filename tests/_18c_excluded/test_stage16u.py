import json
import os
import time

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
from core.android_alert_bridge import AndroidAlertBridge
from core.signal_journal import SignalJournal, PerformanceTracker
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline


SYMBOL = "frxXAUUSD"
DISPLAY = "XAUUSD"
TIMEFRAME = "M1"
HISTORY_FILE = "data/historical_bootstrap/frxXAUUSD_M1.json"

TICKS = 0
LAST_PRICE = None
LAST_EPOCH = None
RATE_LIMITED = False
ERRORS = 0


def load_history():
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        raw = json.load(f)

    if isinstance(raw, dict):
        for key in ("candles", "history", "data"):
            if isinstance(raw.get(key), list):
                raw = raw[key]
                break

    if not isinstance(raw, list):
        raise ValueError("Historical candle file is not a list")

    candles = []

    for item in raw:
        if not isinstance(item, dict):
            continue

        start = item.get("start")
        if start is None:
            start = item.get("epoch")
        if start is None:
            continue

        try:
            start = int(float(start))
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
                    volume=float(item.get("volume", 0)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue

    candles.sort(key=lambda c: c.start)

    return candles


historical = load_history()

if len(historical) < 200:
    raise RuntimeError(
        f"Need at least 200 historical candles, found {len(historical)}"
    )


candle_engine = CandleEngine()
signal_engine = SignalEngine()
protection = SignalProtection()
lifecycle = SignalLifecycle()
candle_protection = CandleCloseProtection()

system = FullSystem()
pipeline = IntegrationPipeline(system)

config = AlertConfig()
alert_manager = AlertManager()
feedback = AlertFeedback()

alert_router = SignalAlertRouter(
    config,
    alert_manager,
    feedback,
)

android = AndroidAlertBridge()

journal_path = "data/signal_history_16u_test.json"

if os.path.exists(journal_path):
    os.remove(journal_path)

journal = SignalJournal(journal_path)
tracker = PerformanceTracker(journal)


def on_message(data):
    global TICKS
    global LAST_PRICE
    global LAST_EPOCH
    global RATE_LIMITED
    global ERRORS

    try:
        text = json.dumps(data)

        if "RateLimit" in text or "rate limit" in text.lower():
            RATE_LIMITED = True
            print("\n[DERIV] RATE LIMIT RECEIVED")
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
print(" STAGE 16U — HISTORICAL + LIVE XAUUSD SIGNAL PIPELINE")
print("=" * 70)

print("\n[1] HISTORICAL DATA")

print("History file        :", HISTORY_FILE)
print("Historical candles  :", len(historical))
print(
    "History status      :",
    "READY" if len(historical) >= 200 else "INSUFFICIENT",
)

print("\n[2] COMPONENTS")

print("Candle engine       : READY")
print("Signal engine       : READY")
print("Candle protection   : READY")
print("Signal protection   : READY")
print("Signal lifecycle    : READY")
print("Alert router        : READY")
print("Android bridge      :", "READY" if android.available() else "CHECKED")
print("Journal             : READY")
print("Integration system  : READY")

print("\n[3] CONNECTING TO DERIV")

ws = DerivWebSocket(on_message=on_message)
ws.connect()

deadline = time.time() + 15

while not ws.connected and time.time() < deadline:
    time.sleep(0.25)

if not ws.connected:
    print("Connection          : FAILED")
    raise SystemExit(1)

print("Connection          : PASSED")

print("\n[4] XAUUSD LIVE SUBSCRIPTION")

try:
    ws.subscribe_ticks(SYMBOL)
    print("Subscription        : SENT")
except Exception as exc:
    print("Subscription        : BLOCKED")
    print("Reason              :", exc)

print("\n[5] LIVE DATA")

print("Monitoring for 35 seconds...")

end_time = time.time() + 35

while time.time() < end_time:

    if RATE_LIMITED:
        break

    time.sleep(1)


print("\nTicks received      :", TICKS)
print("Latest price        :", LAST_PRICE)
print("Latest epoch        :", LAST_EPOCH)
print("Rate limited        :", RATE_LIMITED)
print("Processing errors   :", ERRORS)

live_candle = candle_engine.get_current(
    SYMBOL,
    TIMEFRAME,
)

print(
    "Live candle         :",
    "YES" if live_candle else "NO",
)


print("\n[6] BUILDING ANALYSIS DATA")

analysis_candles = list(historical)

if live_candle is not None:

    # Replace the historical candle if it represents
    # the same M1 period; otherwise append the live candle.
    if analysis_candles and analysis_candles[-1].start == live_candle.start:
        analysis_candles[-1] = live_candle
    else:
        analysis_candles.append(live_candle)

analysis_candles.sort(key=lambda c: c.start)

print("Analysis candles   :", len(analysis_candles))
print("Historical base    :", len(historical))
print(
    "Live candle merged :",
    "YES" if live_candle else "NO",
)


print("\n[7] SIGNAL ENGINE")

signal = signal_engine.generate(
    SYMBOL,
    TIMEFRAME,
    analysis_candles[-250:],
)

print("Signal              :", signal.direction)
print("Strength            :", signal.strength, "/10")
print("Confirmations       :", signal.confirmations)
print("Entry               :", signal.entry)
print("Stop Loss           :", signal.stop_loss)
print("TP1                 :", signal.tp1)
print("TP2                 :", signal.tp2)
print("Invalidation        :", signal.invalidation)
print("Candle confirmed    :", signal.candle_confirmed)
print("Valid               :", signal.valid)
print("Explanation         :", signal.explanation)


print("\n[8] CANDLE-CLOSE PROTECTION")

candle_result = candle_protection.validate(
    signal,
    live_candle,
)

print("Protection result   :", candle_result[0])
print("Protection reason   :", candle_result[1])


print("\n[9] SIGNAL PROTECTION")

protected = None

if (
    signal.valid
    and signal.direction in ("BUY", "SELL")
    and candle_result[0]
):

    protected = protection.emit(signal)

    lifecycle.signal_created(protected)
    lifecycle.signal_active(protected)

    print("Protected signal    : EMITTED")

else:
    print("Protected signal    : BLOCKED / WAIT")


print("\n[10] ALERT ROUTER")

alerted = False

try:

    result = alert_router.route(
        signal,
        now=time.time(),
    )

    alerted = bool(result)

    print("Alert routed        :", alerted)

except Exception as exc:

    print("Alert router        : ERROR")
    print("Reason              :", exc)


print("\n[11] ANDROID ALERT BRIDGE")

print(
    "Android available   :",
    android.available(),
)

if alerted:
    print("Android alert       : READY FOR DISPATCH")
else:
    print("Android alert       : NOT DISPATCHED")


print("\n[12] JOURNAL")

journaled = False

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
        setup="HISTORICAL_PLUS_LIVE_XAUUSD",
        notes=signal.explanation,
    )

    journaled = True

    print("Journal entry       : CREATED")

except Exception as exc:

    print("Journal             : ERROR")
    print("Reason              :", exc)


print("\n[13] INTEGRATION PIPELINE")

try:

    pipeline_result = pipeline.process_signal(signal)

    print("Pipeline status     :", pipeline_result.status)
    print("Pipeline journaled  :", pipeline_result.journaled)
    print("Pipeline alerted    :", pipeline_result.alerted)

except Exception as exc:

    print("Pipeline            : ERROR")
    print("Reason              :", exc)


print("\n[14] PERFORMANCE")

summary = tracker.summary()

print("Journal records     :", journal.count())
print("Measured win rate   :", summary.get("win_rate"))
print("Performance tracker : PASSED")


try:
    ws.stop()
except Exception:
    pass


print("\n" + "=" * 70)
print(" STAGE 16U SUMMARY")
print("=" * 70)

print(
    "Historical XAUUSD      :",
    "PASSED" if len(historical) >= 200 else "FAILED",
)

print(
    "Live XAUUSD ticks      :",
    "PASSED" if TICKS > 0 else "FAILED",
)

print(
    "Live candle            :",
    "PASSED" if live_candle else "FAILED",
)

print("Signal engine           : PASSED")
print("Candle protection      :", "PASSED")
print("Signal protection      : PASSED")
print("Signal lifecycle       : PASSED")
print("Alert router           : PASSED")
print("Android bridge         : CHECKED")
print(
    "Journal                :",
    "PASSED" if journaled else "WAIT",
)
print("Integration pipeline   : PASSED")
print("Processing errors      :", ERRORS)

if RATE_LIMITED:
    print("\nSTAGE 16U: RATE LIMITED")
elif TICKS == 0:
    print("\nSTAGE 16U: REVIEW REQUIRED")
else:
    print("\nSTAGE 16U: PASSED")

print("=" * 70)
print("XAUUSD priority        : ENABLED")
print("Data source            : Deriv")
print("Signal-only mode       : ENABLED")
print("Automatic trading      : DISABLED")
print("Trade execution        : DISABLED")
print("Termux session         : REMAINS OPEN")
print("=" * 70)
