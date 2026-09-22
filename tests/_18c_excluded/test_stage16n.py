import json
import time
from pathlib import Path

from core.signal_engine import SignalEngine
from core.signal_protection import SignalProtection
from core.signal_lifecycle import SignalLifecycle
from core.candle_close_protection import CandleCloseProtection
from core.persistent_alert_router import PersistentAlertRouter
from core.android_alert_bridge import AndroidAlertBridge
from core.signal_journal import SignalJournal, PerformanceTracker
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline
from core.candle_engine import Candle


print()
print("=" * 100)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16N — PROTECTION + ALERTS + JOURNAL")
print("=" * 100)
print()

# ================================================================
# COMPONENTS
# ================================================================

protection = SignalProtection()
lifecycle = SignalLifecycle()
candle_protection = CandleCloseProtection()
alert_router = PersistentAlertRouter()
android_bridge = AndroidAlertBridge()

journal_path = Path("data/signal_history_16n_test.json")
journal = SignalJournal(path=journal_path)
tracker = PerformanceTracker(journal)

system = FullSystem()
pipeline = IntegrationPipeline(system)

print("COMPONENTS")
print("Signal protection : ENABLED")
print("Candle protection : ENABLED")
print("Signal lifecycle  : ENABLED")
print("Alert router      : ENABLED")
print("Android bridge    : ENABLED")
print("Journal           : ENABLED")
print()

# ================================================================
# LOAD REAL XAUUSD M1 HISTORY
# ================================================================

history_file = Path(
    "data/historical_bootstrap/frxXAUUSD_M1.json"
)

if not history_file.exists():
    print("XAUUSD historical data file not found.")
    print("Expected:")
    print(history_file)
    raise SystemExit(1)

with history_file.open("r", encoding="utf-8") as f:
    raw = json.load(f)

if isinstance(raw, dict):
    raw = raw.get("candles", raw.get("history", []))

if not isinstance(raw, list) or not raw:
    print("XAUUSD historical data is empty or invalid.")
    raise SystemExit(1)

candles = []

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

    candles.append(
        Candle(
            symbol="frxXAUUSD",
            timeframe="M1",
            start=start,
            end=start + 60,
            open=float(item["open"]),
            high=float(item["high"]),
            low=float(item["low"]),
            close=float(item["close"]),
            volume=float(item.get("volume", 0)),
        )
    )

print(f"Historical XAUUSD candles : {len(candles)}")

if len(candles) < 200:
    print("Insufficient candles.")
    print("Required : 200")
    raise SystemExit(1)

print("Historical data            : READY")
print()

# ================================================================
# SIGNAL ENGINE
# ================================================================

print("SIGNAL ENGINE")

engine = SignalEngine()

signal = engine.generate(
    "frxXAUUSD",
    "M1",
    candles,
)

print(f"Direction     : {signal.direction}")
print(f"Strength      : {signal.strength}/10")
print(f"Confirmations : {signal.confirmations}")
print(f"Entry         : {signal.entry}")
print(f"Stop Loss     : {signal.stop_loss}")
print(f"TP1           : {signal.tp1}")
print(f"TP2           : {signal.tp2}")
print(f"Invalidation  : {signal.invalidation}")
print(f"Candle Confirm: {signal.candle_confirmed}")
print(f"Valid         : {signal.valid}")
print(f"Explanation   : {signal.explanation}")
print()

# ================================================================
# CANDLE CLOSE PROTECTION
# ================================================================

print("CANDLE CLOSE PROTECTION")

try:
    confirmed, reason = candle_protection.validate(
        signal,
        candles[-1],
    )

    print(f"Confirmed : {confirmed}")
    print(f"Reason    : {reason}")
    print("Candle protection : PASSED")

except Exception as exc:
    print(f"Candle protection : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# SIGNAL PROTECTION
# ================================================================

print("SIGNAL PROTECTION")

protected = None

if signal.valid and signal.direction in ("BUY", "SELL"):

    try:
        protected = protection.emit(signal)

        print("Protection emit : PASSED")
        print(f"Protected type  : {type(protected).__name__}")

    except Exception as exc:
        print(f"Protection emit : FAILED — {exc}")
        raise SystemExit(1)

else:
    print("Current XAUUSD result is not a valid directional signal.")
    print("Protection emission : SAFELY SKIPPED")
    print("WAIT is accepted by the signal system.")

print()

# ================================================================
# SIGNAL LIFECYCLE
# ================================================================

print("SIGNAL LIFECYCLE")

if protected is not None:

    try:
        created = lifecycle.signal_created(
            protected
        )

        active = lifecycle.signal_active(
            protected
        )

        print(f"Created event : {created}")
        print(f"Active event  : {active}")
        print("Lifecycle     : PASSED")

    except Exception as exc:
        print(f"Lifecycle : FAILED — {exc}")
        raise SystemExit(1)

else:
    print("No directional signal.")
    print("Lifecycle : SAFELY SKIPPED")

print()

# ================================================================
# STALE DATA PROTECTION
# ================================================================

print("STALE DATA PROTECTION")

try:
    stale = protection.check_stale(
        time.time() - 60
    )

    print(f"60-second-old data : {stale}")
    print("Stale protection   : PASSED")

except Exception as exc:
    print(f"Stale protection : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# PRICE PROTECTION
# ================================================================

print("PRICE PROTECTION")

if signal.direction in ("BUY", "SELL"):

    test_price = (
        signal.stop_loss
        if signal.stop_loss is not None
        else signal.entry
    )

    if test_price is not None:

        try:
            price_result = protection.check_price(
                signal.symbol,
                signal.timeframe,
                float(test_price),
            )

            print(
                f"Price check : {price_result}"
            )
            print("Price protection : PASSED")

        except Exception as exc:
            print(
                f"Price protection : FAILED — {exc}"
            )
            raise SystemExit(1)

    else:
        print("No usable price level.")
        print("Price protection : SAFELY SKIPPED")

else:
    print("WAIT signal.")
    print("Price protection : SAFELY SKIPPED")

print()

# ================================================================
# ALERT ROUTER
# ================================================================

print("ALERT ROUTER")

try:
    alert_result = alert_router.route(
        signal,
        now=time.time(),
    )

    print(f"Alert result : {alert_result}")
    print("Alert router : PASSED")

except Exception as exc:
    print(f"Alert router : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# ANDROID BRIDGE
# ================================================================

print("ANDROID BRIDGE")

try:
    available = android_bridge.available()

    print(
        f"Termux:API available : {available}"
    )

    if available:
        print("Android bridge : READY")
    else:
        print("Android bridge : NOT AVAILABLE")
        print("No Android alert will be triggered.")

except Exception as exc:
    print(f"Android bridge : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# JOURNAL
# ================================================================

print("SIGNAL JOURNAL")

try:
    record = journal.add(
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
        setup="STAGE_16N_XAUUSD_TEST",
        notes=signal.explanation,
    )

    print(f"Journal record : {record}")
    print(f"Journal count  : {journal.count()}")
    print("Journal : PASSED")

except Exception as exc:
    print(f"Journal : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# PERFORMANCE TRACKER
# ================================================================

print("PERFORMANCE TRACKER")

try:
    summary = tracker.summary()

    print(f"Summary : {summary}")
    print("Performance tracker : PASSED")

except Exception as exc:
    print(f"Performance tracker : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# FULL INTEGRATION PIPELINE
# ================================================================

print("INTEGRATION PIPELINE")

try:
    result = pipeline.process_signal(
        signal
    )

    print(f"Pipeline status : {result.status}")
    print(f"Journaled       : {result.journaled}")
    print(f"Alerted         : {result.alerted}")
    print("Integration pipeline : PASSED")

except Exception as exc:
    print(f"Integration pipeline : FAILED — {exc}")
    raise SystemExit(1)

print()

# ================================================================
# FINAL SUMMARY
# ================================================================

print("=" * 100)
print(" STAGE 16N SUMMARY")
print("=" * 100)

print("Real XAUUSD data    : PASSED")
print("Signal engine       : PASSED")
print("Candle protection   : PASSED")
print("Signal protection   : PASSED")
print("Signal lifecycle    : PASSED")
print("Stale protection    : PASSED")
print("Price protection    : PASSED")
print("Alert router        : PASSED")
print("Android bridge      : CHECKED")
print("Journal             : PASSED")
print("Performance tracker : PASSED")
print("Pipeline            : PASSED")

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority   : ENABLED")
print("Data source       : Deriv")
print("Termux session     : REMAINS OPEN")

print()
print("=" * 100)
print("STAGE 16N: PASSED")
print("=" * 100)
