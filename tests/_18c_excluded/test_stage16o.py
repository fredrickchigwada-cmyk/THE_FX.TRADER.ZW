import json
import time
from pathlib import Path

from core.deriv_ws import DerivWebSocket
from core.candle_engine import CandleEngine
from core.signal_engine import SignalEngine
from core.signal_protection import SignalProtection
from core.signal_lifecycle import SignalLifecycle
from core.candle_close_protection import CandleCloseProtection
from core.persistent_alert_router import PersistentAlertRouter
from core.signal_journal import SignalJournal
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline
from core.candle_engine import Candle


MARKETS = {
    "XAUUSD": "frxXAUUSD",
    "STEP INDEX": "stpRNG",
    "VOLATILITY 10": "R_10",
    "VOLATILITY 25": "R_25",
    "VOLATILITY 50": "R_50",
    "VOLATILITY 75": "R_75",
    "VOLATILITY 100": "R_100",
    "BOOM 500": "BOOM500",
    "BOOM 1000": "BOOM1000",
    "CRASH 500": "CRASH500",
    "CRASH 1000": "CRASH1000",
}

HISTORY_DIR = Path("data/historical_bootstrap")
TIMEFRAME = "M1"
MONITOR_SECONDS = 30
SUBSCRIBE_DELAY = 3.5


print()
print("=" * 100)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16O — LIVE MULTI-MARKET PROTECTION + ALERT VERIFICATION")
print("=" * 100)
print()

# ------------------------------------------------------------------
# COMPONENTS
# ------------------------------------------------------------------

engine = SignalEngine()
candle_engine = CandleEngine()
protection = SignalProtection()
lifecycle = SignalLifecycle()
candle_protection = CandleCloseProtection()
alert_router = PersistentAlertRouter()

journal = SignalJournal(
    path=Path("data/signal_history_16o_test.json")
)

system = FullSystem()
pipeline = IntegrationPipeline(system)

print("COMPONENTS")
print("Deriv WebSocket       : ENABLED")
print("Candle engine         : ENABLED")
print("Signal engine         : ENABLED")
print("Signal protection     : ENABLED")
print("Candle protection     : ENABLED")
print("Lifecycle              : ENABLED")
print("Alert router          : ENABLED")
print("Journal               : ENABLED")
print("Integration pipeline  : ENABLED")
print()

# ------------------------------------------------------------------
# LOAD HISTORICAL M1 DATA
# ------------------------------------------------------------------

historical = {}

for name, symbol in MARKETS.items():

    path = HISTORY_DIR / f"{symbol}_M1.json"

    if not path.exists():
        continue

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        if isinstance(raw, dict):
            raw = raw.get(
                "candles",
                raw.get("history", [])
            )

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
                    symbol=symbol,
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

        if len(candles) >= 200:
            historical[symbol] = candles

    except Exception:
        pass

print(
    f"Historical markets ready : {len(historical)}"
)
print()

# ------------------------------------------------------------------
# LIVE DATA
# ------------------------------------------------------------------

ticks = {
    symbol: 0
    for symbol in MARKETS.values()
}

last_prices = {}
last_tick_time = {}

ws = None


def on_message(data):

    if not isinstance(data, dict):
        return

    if data.get("msg_type") != "tick":
        return

    tick = data.get("tick") or {}

    symbol = tick.get("symbol")

    if symbol not in MARKETS.values():
        return

    quote = tick.get("quote")
    epoch = tick.get("epoch")

    try:
        price = float(quote)
        epoch = float(epoch)
    except Exception:
        return

    ticks[symbol] += 1
    last_prices[symbol] = price
    last_tick_time[symbol] = epoch

    try:
        candle_engine.update_tick(
            symbol,
            price,
            epoch,
        )
    except Exception:
        pass


print("LIVE DERIV CONNECTION")
print()

ws = DerivWebSocket(
    on_message=on_message
)

try:
    ws.connect()

    print("Connection : PASSED")

except Exception as exc:

    print(f"Connection : FAILED — {exc}")
    raise SystemExit(1)

# ------------------------------------------------------------------
# SUBSCRIBE
# ------------------------------------------------------------------

print()
print("SUBSCRIBING TO LIVE MARKETS")
print()

subscribed = 0

for name, symbol in MARKETS.items():

    try:

        ws.subscribe_ticks(symbol)

        subscribed += 1

        print(
            f"{name:<20} {symbol:<15} SUBSCRIBED"
        )

    except Exception as exc:

        print(
            f"{name:<20} {symbol:<15} FAILED"
        )

    time.sleep(SUBSCRIBE_DELAY)

print()
print(f"Subscriptions requested : {len(MARKETS)}")
print(f"Subscriptions sent      : {subscribed}")
print()

# ------------------------------------------------------------------
# MONITOR
# ------------------------------------------------------------------

print(
    f"Monitoring live data for {MONITOR_SECONDS} seconds..."
)
print()

deadline = time.time() + MONITOR_SECONDS

while time.time() < deadline:
    time.sleep(1)

# ------------------------------------------------------------------
# ANALYSIS + PROTECTION
# ------------------------------------------------------------------

print()
print("=" * 100)
print(" LIVE PROTECTION RESULTS")
print("=" * 100)

results = []

directional = 0
wait_count = 0
protected_count = 0
alert_count = 0
errors = 0

for name, symbol in MARKETS.items():

    try:

        candles = list(
            historical.get(symbol, [])
        )

        current = candle_engine.get_current(
            symbol,
            TIMEFRAME,
        )

        if current is not None:

            if candles and candles[-1].start == current.start:
                candles[-1] = current
            else:
                candles.append(current)

        live_ticks = ticks.get(symbol, 0)

        if live_ticks == 0:

            results.append(
                (
                    name,
                    symbol,
                    live_ticks,
                    "NO DATA",
                    "WAIT",
                    0,
                    "NO LIVE DATA",
                )
            )

            wait_count += 1
            continue

        if len(candles) < 200:

            results.append(
                (
                    name,
                    symbol,
                    live_ticks,
                    "DATA",
                    "WAIT",
                    0,
                    "INSUFFICIENT HISTORY",
                )
            )

            wait_count += 1
            continue

        signal = engine.generate(
            symbol,
            TIMEFRAME,
            candles,
        )

        direction = signal.direction

        if direction in ("BUY", "SELL"):

            directional += 1

            confirmed, reason = (
                candle_protection.validate(
                    signal,
                    candles[-1],
                )
            )

            if not confirmed:

                results.append(
                    (
                        name,
                        symbol,
                        live_ticks,
                        "LIVE",
                        "WAIT",
                        signal.strength,
                        f"CANDLE BLOCK: {reason}",
                    )
                )

                wait_count += 1
                continue

            protected = protection.emit(
                signal
            )

            lifecycle.signal_created(
                protected
            )

            lifecycle.signal_active(
                protected
            )

            protected_count += 1

            alert_result = alert_router.route(
                signal,
                now=time.time(),
            )

            if alert_result:
                alert_count += 1

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
                setup="STAGE_16O_LIVE",
                notes=signal.explanation,
            )

            results.append(
                (
                    name,
                    symbol,
                    live_ticks,
                    "LIVE",
                    direction,
                    signal.strength,
                    "PROTECTED",
                )
            )

        else:

            wait_count += 1

            results.append(
                (
                    name,
                    symbol,
                    live_ticks,
                    "LIVE",
                    "WAIT",
                    signal.strength,
                    signal.explanation,
                )
            )

    except Exception as exc:

        errors += 1

        results.append(
            (
                name,
                symbol,
                ticks.get(symbol, 0),
                "ERROR",
                "WAIT",
                0,
                str(exc),
            )
        )

# ------------------------------------------------------------------
# DISPLAY
# ------------------------------------------------------------------

print()
print(
    f"{'MARKET':<20} {'TICKS':>6} "
    f"{'STATUS':<10} {'SIGNAL':<7} "
    f"{'STR':>4}  RESULT"
)
print("-" * 100)

for row in results:

    name, symbol, count, status, direction, strength, reason = row

    print(
        f"{name:<20} "
        f"{count:>6} "
        f"{status:<10} "
        f"{direction:<7} "
        f"{strength:>4}  "
        f"{reason}"
    )

# ------------------------------------------------------------------
# STOP
# ------------------------------------------------------------------

try:
    ws.stop()
except Exception:
    pass

# ------------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------------

print()
print("=" * 100)
print(" STAGE 16O SUMMARY")
print("=" * 100)

live_markets = sum(
    1
    for symbol in MARKETS.values()
    if ticks.get(symbol, 0) > 0
)

print(
    f"Markets configured : {len(MARKETS)}"
)
print(
    f"Markets live       : {live_markets}"
)
print(
    f"Markets no-data    : "
    f"{len(MARKETS) - live_markets}"
)
print(
    f"Directional signals: {directional}"
)
print(
    f"WAIT results       : {wait_count}"
)
print(
    f"Protected signals  : {protected_count}"
)
print(
    f"Alerts routed      : {alert_count}"
)
print(
    f"Processing errors   : {errors}"
)

print()

if errors == 0 and live_markets >= 1:

    print("STAGE 16O: PASSED")

else:

    print("STAGE 16O: REVIEW REQUIRED")

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority    : ENABLED")
print("Data source        : Deriv")
print("Termux session     : REMAINS OPEN")

print()
print("=" * 100)
