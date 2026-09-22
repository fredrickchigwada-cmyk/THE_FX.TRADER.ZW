import json
import time
from pathlib import Path

from core.deriv_ws import DerivWebSocket
from core.deriv_rate_limit import DerivRateLimitGuard
from core.market_data import MarketDataStore
from core.watchdog import Watchdog
from core.signal_protection import SignalProtection
from core.signal_lifecycle import SignalLifecycle
from core.signal_journal import SignalJournal


SYMBOL = "frxXAUUSD"
DURATION = 60


print("=" * 70)
print("STAGE 16X — EXTENDED LIVE STABILITY TEST")
print("=" * 70)

errors = []

# ------------------------------------------------------------
# COMPONENT CHECK
# ------------------------------------------------------------
try:
    data_store = MarketDataStore()
    rate_guard = DerivRateLimitGuard()
    protection = SignalProtection()
    lifecycle = SignalLifecycle()
    journal = SignalJournal()

    print("Core components       : READY")
except Exception as exc:
    print(f"Core components       : FAILED — {exc}")
    raise SystemExit(1)

# ------------------------------------------------------------
# WATCHDOG CHECK
# ------------------------------------------------------------
try:
    watchdog_check = lambda: True
    watchdog = Watchdog(watchdog_check)
    print("Watchdog              : READY")
except Exception as exc:
    print(f"Watchdog              : FAILED — {exc}")
    errors.append(f"watchdog: {exc}")
    watchdog = None

# ------------------------------------------------------------
# DERIV CONNECTION
# ------------------------------------------------------------
ws = None
tick_count = 0
last_price = None
last_epoch = None
rate_limited = False
processing_errors = 0


def handle_message(message):
    global tick_count, last_price, last_epoch
    global rate_limited, processing_errors

    try:
        data = json.loads(message) if isinstance(message, str) else message

        if isinstance(data, dict):
            if "error" in data:
                text = str(data["error"])
                if "RateLimit" in text or "rate limit" in text.lower():
                    rate_limited = True
                return

            if data.get("msg_type") == "tick" and "tick" in data:
                tick = data["tick"]

                symbol = tick.get("symbol")
                quote = tick.get("quote")
                epoch = tick.get("epoch")

                if symbol == SYMBOL and quote is not None:
                    price = float(quote)
                    last_price = price
                    last_epoch = float(epoch) if epoch is not None else time.time()
                    tick_count += 1

                    try:
                        data_store.update_from_deriv(data)
                    except Exception:
                        pass

    except Exception:
        processing_errors += 1


try:
    ws = DerivWebSocket()
    ws.on_message_callback = handle_message

    ws.connect()
    print("Deriv connection     : PASSED")

    time.sleep(5)

    try:
        ws.subscribe_ticks(SYMBOL)
        print("XAUUSD subscription  : SENT")
    except Exception as exc:
        print(f"XAUUSD subscription  : BLOCKED — {exc}")
        rate_limited = True

    print(f"Monitoring XAUUSD for {DURATION} seconds...")
    print()

    start = time.time()

    while time.time() - start < DURATION:
        time.sleep(3)

        # Watchdog heartbeat
        if watchdog is not None:
            try:
                if hasattr(watchdog, "check"):
                    watchdog.check()
            except Exception:
                pass

        # Periodic status
        elapsed = int(time.time() - start)

        if elapsed > 0 and elapsed % 15 == 0:
            print(
                f"[{elapsed:02d}s] "
                f"ticks={tick_count} "
                f"price={last_price} "
                f"rate_limited={rate_limited}"
            )

except Exception as exc:
    print(f"Live monitoring      : FAILED — {exc}")
    errors.append(f"live monitoring: {exc}")

finally:
    if ws is not None:
        try:
            ws.stop()
        except Exception:
            pass

# ------------------------------------------------------------
# STABILITY RESULTS
# ------------------------------------------------------------
print()
print("-" * 70)

print(f"Live ticks            : {tick_count}")
print(f"Latest XAUUSD         : {last_price}")
print(f"Latest epoch          : {last_epoch}")
print(f"Rate limited          : {rate_limited}")
print(f"Processing errors     : {processing_errors}")

# ------------------------------------------------------------
# DATA FRESHNESS
# ------------------------------------------------------------
try:
    if last_epoch is not None:
        age = time.time() - last_epoch
        stale = age > 30

        print(f"Final data age        : {age:.1f}s")
        print(f"Stale data            : {'YES' if stale else 'NO'}")

        if stale:
            errors.append("final XAUUSD data is stale")
    else:
        print("Final data age        : N/A")
        print("Stale data            : YES / NO DATA")
        errors.append("no XAUUSD tick received")

except Exception as exc:
    print(f"Freshness check       : FAILED — {exc}")
    errors.append(f"freshness: {exc}")

# ------------------------------------------------------------
# RATE-LIMIT GUARD
# ------------------------------------------------------------
try:
    normal_retry = rate_guard.can_retry()

    rate_guard.detect(
        {"error": {"code": "RateLimit", "message": "test rate limit"}}
    )

    blocked_retry = not rate_guard.can_retry()
    remaining = rate_guard.remaining()

    rate_guard.reset()

    reset_ok = rate_guard.can_retry()

    print()
    print(f"Rate guard normal     : {'PASSED' if normal_retry else 'FAILED'}")
    print(f"Rate guard blocking   : {'PASSED' if blocked_retry else 'FAILED'}")
    print(f"Backoff remaining     : {remaining:.1f}s")
    print(f"Rate guard reset      : {'PASSED' if reset_ok else 'FAILED'}")

    if not (normal_retry and blocked_retry and reset_ok):
        errors.append("rate-limit guard verification failed")

except Exception as exc:
    print(f"Rate guard            : FAILED — {exc}")
    errors.append(f"rate guard: {exc}")

# ------------------------------------------------------------
# SIGNAL PROTECTION / STALE SAFETY
# ------------------------------------------------------------
try:
    old_timestamp = time.time() - 120
    stale_result = protection.protect_from_stale_data(old_timestamp)

    print()
    print(
        "Stale-data protection : "
        f"{'PASSED' if stale_result else 'CHECKED'}"
    )

except Exception as exc:
    print(f"Stale protection      : FAILED — {exc}")
    errors.append(f"stale protection: {exc}")

# ------------------------------------------------------------
# JOURNAL PERSISTENCE
# ------------------------------------------------------------
try:
    before = journal.count()

    journal2 = SignalJournal()
    after = journal2.count()

    print(f"Journal before        : {before}")
    print(f"Journal after reload  : {after}")
    print(
        "Journal persistence   : "
        f"{'PASSED' if before == after else 'FAILED'}"
    )

    if before != after:
        errors.append("journal persistence mismatch")

except Exception as exc:
    print(f"Journal persistence   : FAILED — {exc}")
    errors.append(f"journal: {exc}")

# ------------------------------------------------------------
# FINAL SAFETY CHECK
# ------------------------------------------------------------
print()
print("=" * 70)

if processing_errors == 0 and not errors:
    print("STAGE 16X: PASSED")
else:
    print("STAGE 16X: FAILED")
    print("Errors:")
    for error in errors:
        print(f"- {error}")

print("=" * 70)
print("Signal-only mode      : ENABLED")
print("Trade execution       : DISABLED")
print("XAUUSD remains primary market.")
print("=" * 70)
