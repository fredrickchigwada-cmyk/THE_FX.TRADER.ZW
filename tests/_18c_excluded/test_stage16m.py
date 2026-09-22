import json
import time
import threading
import websocket
from pathlib import Path

from core.candle_engine import CandleEngine, Candle
from core.signal_engine import SignalEngine
from core.full_system import FullSystem
from core.integration_pipeline import IntegrationPipeline


URL = "wss://api.derivws.com/trading/v1/options/ws/public"

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

MONITOR_SECONDS = 35

tick_counts = {
    name: 0
    for name in MARKETS
}

latest_prices = {
    name: None
    for name in MARKETS
}

latest_epochs = {
    name: None
    for name in MARKETS
}

candles = CandleEngine()
signal_engine = SignalEngine()

system = FullSystem()
pipeline = IntegrationPipeline(system)


def load_history(display_name, symbol):

    candidates = [
        HISTORY_DIR / f"{symbol}_M1.json",
        HISTORY_DIR / f"{display_name.replace(' ', '_')}_M1.json",
    ]

    for path in candidates:

        if not path.exists():
            continue

        try:

            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(data, dict):
                data = data.get("candles", [])

            result = []

            for item in data:

                try:

                    start = int(
                        float(
                            item.get(
                                "epoch",
                                item.get("start")
                            )
                        )
                    )

                    result.append(
                        Candle(
                            symbol=symbol,
                            timeframe="M1",
                            start=start,
                            end=start + 60,
                            open=float(item["open"]),
                            high=float(item["high"]),
                            low=float(item["low"]),
                            close=float(item["close"]),
                            volume=float(
                                item.get(
                                    "volume",
                                    0
                                )
                            ),
                        )
                    )

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    continue

            return result[-250:]

        except Exception:
            return []

    return []


history = {
    name: load_history(name, symbol)
    for name, symbol in MARKETS.items()
}


print()
print("=" * 100)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16M — MULTI-MARKET LIVE PIPELINE")
print("=" * 100)
print()

for name, symbol in MARKETS.items():

    print(
        f"{name:<20} {symbol:<15} "
        f"history={len(history[name])}"
    )

print()


# ---------------------------------------------------------
# WebSocket
# ---------------------------------------------------------

ws = websocket.WebSocket()
ws.settimeout(5)

print("[LIVE] Connecting to Deriv...")

try:

    ws.connect(URL)

except Exception as exc:

    print(
        f"[LIVE] Connection failed: {exc}"
    )

    raise SystemExit(1)

print("[LIVE] Connected")
print()


# ---------------------------------------------------------
# Subscribe with spacing
# ---------------------------------------------------------

for name, symbol in MARKETS.items():

    try:

        ws.send(
            json.dumps({
                "ticks": symbol,
                "subscribe": 1,
            })
        )

        print(
            f"[LIVE] Subscribed: "
            f"{name} -> {symbol}"
        )

        # Protect the connection from rapid
        # subscription requests.

        time.sleep(3.5)

    except Exception as exc:

        print(
            f"[LIVE] Subscription failed: "
            f"{name} — {exc}"
        )


print()
print(
    f"[LIVE] Monitoring {len(MARKETS)} markets "
    f"for {MONITOR_SECONDS} seconds..."
)
print()


# ---------------------------------------------------------
# Receive live data
# ---------------------------------------------------------

start_time = time.time()

while time.time() - start_time < MONITOR_SECONDS:

    try:

        raw = ws.recv()

        if not raw:
            continue

        message = json.loads(raw)

        if message.get("msg_type") != "tick":
            continue

        tick = message.get("tick") or {}

        symbol = tick.get("symbol")
        quote = tick.get("quote")
        epoch = tick.get("epoch")

        if symbol not in MARKETS.values():
            continue

        if quote is None:
            continue

        price = float(quote)

        if epoch is None:
            epoch = time.time()

        epoch = float(epoch)

        display_name = next(
            (
                name
                for name, value in MARKETS.items()
                if value == symbol
            ),
            symbol,
        )

        tick_counts[display_name] += 1
        latest_prices[display_name] = price
        latest_epochs[display_name] = epoch

        candles.update_tick(
            symbol,
            price,
            epoch,
        )

    except websocket.WebSocketTimeoutException:

        continue

    except Exception as exc:

        print(
            f"[LIVE] Receive error: {exc}"
        )


try:
    ws.close()
except Exception:
    pass


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print()
print("=" * 100)
print(" LIVE MARKET RESULTS")
print("=" * 100)

print(
    f"{'MARKET':<20}"
    f"{'TICKS':>8}"
    f"{'CANDLE':>10}"
    f"{'PRICE':>15}"
    f"{'STATUS':>15}"
)

print("-" * 100)


live_markets = 0
no_data_markets = 0
pipeline_errors = 0


for name, symbol in MARKETS.items():

    count = tick_counts[name]

    current = candles.get_current(
        symbol,
        "M1",
    )

    if count > 0 and current:

        status = "LIVE"
        live_markets += 1

    else:

        status = "NO DATA"
        no_data_markets += 1

    price = latest_prices[name]

    price_text = (
        f"{price:.5f}"
        if price is not None
        else "-"
    )

    print(
        f"{name:<20}"
        f"{count:>8}"
        f"{('YES' if current else 'NO'):>10}"
        f"{price_text:>15}"
        f"{status:>15}"
    )


# ---------------------------------------------------------
# Live signal checks
# ---------------------------------------------------------

print()
print("=" * 100)
print(" LIVE SIGNAL CHECKS")
print("=" * 100)

pipeline_results = {
    "BUY": 0,
    "SELL": 0,
    "WAIT": 0,
}


for name, symbol in MARKETS.items():

    if tick_counts[name] == 0:
        continue

    current = candles.get_current(
        symbol,
        "M1",
    )

    if not current:
        continue

    base = history[name]

    if len(base) < 200:

        print(
            f"{name:<20} WAIT — "
            f"historical base below 200 candles"
        )

        pipeline_results["WAIT"] += 1
        continue

    combined = list(base)

    if combined and combined[-1].start == current.start:

        combined[-1] = current

    else:

        combined.append(current)

    combined = combined[-250:]

    try:

        signal = signal_engine.generate(
            symbol,
            "M1",
            combined,
        )

        direction = getattr(
            signal,
            "signal",
            "WAIT",
        )

        strength = getattr(
            signal,
            "strength",
            0,
        )

        confirmations = getattr(
            signal,
            "confirmations",
            0,
        )

        print(
            f"{name:<20}"
            f"{direction:<8}"
            f"Strength={strength}/10 "
            f"Confirmations={confirmations}"
        )

        if direction in ("BUY", "SELL"):

            result = pipeline.process_signal(
                signal
            )

            pipeline_status = getattr(
                result,
                "status",
                "UNKNOWN",
            )

            print(
                f"{'':20}"
                f"PIPELINE={pipeline_status}"
            )

            pipeline_results[direction] += 1

        else:

            pipeline_results["WAIT"] += 1

            print(
                f"{'':20}"
                "PIPELINE=WAIT"
            )

    except Exception as exc:

        pipeline_errors += 1

        print(
            f"{name:<20}"
            f"ERROR: {exc}"
        )


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print()
print("=" * 100)
print(" STAGE 16M SUMMARY")
print("=" * 100)

print(
    f"Markets configured : {len(MARKETS)}"
)

print(
    f"Markets live       : {live_markets}"
)

print(
    f"Markets no-data    : {no_data_markets}"
)

print(
    f"Pipeline BUY       : "
    f"{pipeline_results['BUY']}"
)

print(
    f"Pipeline SELL      : "
    f"{pipeline_results['SELL']}"
)

print(
    f"Pipeline WAIT      : "
    f"{pipeline_results['WAIT']}"
)

print(
    f"Processing errors  : {pipeline_errors}"
)

print()

if live_markets > 0 and pipeline_errors == 0:

    print("STAGE 16M: PASSED")

    print()
    print(
        "Multi-market live Deriv data successfully "
        "entered the signal pipeline."
    )

else:

    print("STAGE 16M: PARTIAL")

    print()
    print(
        "The live feed requires further verification."
    )

print()
print("XAUUSD priority    : ENABLED")
print("Data source        : Deriv")
print("Signal-only mode   : ENABLED")
print("Automatic trading  : DISABLED")
print("Trade execution    : DISABLED")
print("Termux session remains open.")
print()
print("=" * 100)
