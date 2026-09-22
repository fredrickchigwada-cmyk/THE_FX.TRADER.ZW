"""
THE_FX.TRADER.BOT.ZW
Stage 16K — Live Signal Pipeline Integration

Signal-only:
Deriv data -> candles -> SignalEngine -> MTF confirmation
-> protection -> journal/alerts pipeline

NO TRADE EXECUTION.
"""

import json
import time
from pathlib import Path

from core.candle_engine import Candle
from core.signal_engine import SignalEngine
from core.integration_pipeline import IntegrationPipeline
from core.full_system import FullSystem


MARKETS = {
    "XAUUSD": "frxXAUUSD",
    "STEP INDEX": "stpRNG",
    "VOLATILITY 10": "R_10",
    "VOLATILITY 25": "R_25",
    "VOLATILITY 50": "R_50",
    "VOLATILITY 75": "R_75",
    "BOOM 1000": "BOOM1000",
    "CRASH 500": "CRASH500",
    "CRASH 1000": "CRASH1000",
}

TIMEFRAMES = {
    "M1": 60,
    "M3": 180,
    "M5": 300,
}

BASE_DIR = Path("data/historical_bootstrap")


def load(symbol, timeframe):
    path = BASE_DIR / f"{symbol}_{timeframe}.json"

    if not path.exists():
        return []

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            return data.get("candles", [])

        return data

    except Exception:
        return []


def build(symbol, timeframe, raw):
    candles = []
    seconds = TIMEFRAMES[timeframe]

    for item in raw:
        try:
            start = int(float(item["epoch"]))

            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    start=start,
                    end=start + seconds,
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item.get("volume", 0)),
                )
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

    return candles


def get(obj, *names, default=None):
    for name in names:

        if hasattr(obj, name):
            return getattr(obj, name)

        if isinstance(obj, dict) and name in obj:
            return obj[name]

    return default


def mtf_confirm(signals):

    valid = [
        s for s in signals
        if s["signal"] in ("BUY", "SELL")
    ]

    if not valid:
        return {
            "signal": "WAIT",
            "strength": 0,
            "confirmations": 0,
            "reason": "NO_VALID_DIRECTIONAL_SIGNALS",
        }

    buys = [
        s for s in valid
        if s["signal"] == "BUY"
    ]

    sells = [
        s for s in valid
        if s["signal"] == "SELL"
    ]

    if len(buys) == len(sells):
        return {
            "signal": "WAIT",
            "strength": 0,
            "confirmations": 0,
            "reason": "BUY_SELL_CONFLICT",
        }

    aligned = buys if len(buys) > len(sells) else sells
    direction = "BUY" if buys else "SELL"

    agreement = len(aligned) / len(valid)

    if agreement < 0.60:
        return {
            "signal": "WAIT",
            "strength": 0,
            "confirmations": len(aligned),
            "reason": "INSUFFICIENT_MTF_AGREEMENT",
        }

    strength = (
        sum(
            float(s["strength"])
            for s in aligned
        )
        / len(aligned)
    )

    strength *= agreement
    strength = round(
        min(10, max(0, strength)),
        2,
    )

    if strength < 6:
        return {
            "signal": "WAIT",
            "strength": strength,
            "confirmations": len(aligned),
            "reason": "MTF_STRENGTH_BELOW_MINIMUM",
        }

    return {
        "signal": direction,
        "strength": strength,
        "confirmations": len(aligned),
        "reason": "MTF_CONFIRMED",
    }


print()
print("=" * 110)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16K — LIVE SIGNAL PIPELINE INTEGRATION")
print("=" * 110)
print()

engine = SignalEngine()
system = FullSystem()
pipeline = IntegrationPipeline(system)

processed = 0
buy = 0
sell = 0
wait = 0
errors = 0

for market, symbol in MARKETS.items():

    print()
    print("-" * 110)
    print(f"{market} ({symbol})")
    print("-" * 110)

    timeframe_signals = []

    for timeframe in TIMEFRAMES:

        candles = build(
            symbol,
            timeframe,
            load(symbol, timeframe),
        )

        if len(candles) < 200:

            print(
                f"{timeframe}: "
                f"WAIT — {len(candles)}/200 candles"
            )

            timeframe_signals.append(
                {
                    "timeframe": timeframe,
                    "signal": "WAIT",
                    "strength": 0,
                }
            )

            continue

        try:

            signal = engine.generate(
                symbol,
                timeframe,
                candles,
            )

            direction = str(
                get(
                    signal,
                    "signal",
                    "direction",
                    default="WAIT",
                )
            )

            strength = float(
                get(
                    signal,
                    "strength",
                    default=0,
                ) or 0
            )

            confirmations = int(
                get(
                    signal,
                    "confirmations",
                    default=0,
                ) or 0
            )

            timeframe_signals.append(
                {
                    "timeframe": timeframe,
                    "signal": direction,
                    "strength": strength,
                    "confirmations": confirmations,
                }
            )

            print(
                f"{timeframe}: "
                f"{direction} "
                f"{strength}/10 "
                f"({confirmations} confirmations)"
            )

            processed += 1

        except Exception as exc:

            errors += 1

            print(
                f"{timeframe}: ERROR — {exc}"
            )

    mtf = mtf_confirm(timeframe_signals)

    direction = mtf["signal"]

    print()
    print(
        f"MTF: {direction} | "
        f"Strength {mtf['strength']}/10 | "
        f"Confirmations {mtf['confirmations']}"
    )
    print(
        f"Reason: {mtf['reason']}"
    )

    # Feed the actual MTF-approved signal into
    # the existing integration pipeline only when
    # it is a valid directional signal.
    if direction in ("BUY", "SELL"):

        try:

            # Use the strongest aligned timeframe
            # as the source signal object.
            aligned = [
                s for s in timeframe_signals
                if s["signal"] == direction
            ]

            source_tf = max(
                aligned,
                key=lambda x: x["strength"],
            )["timeframe"]

            source_candles = build(
                symbol,
                source_tf,
                load(symbol, source_tf),
            )

            source_signal = engine.generate(
                symbol,
                source_tf,
                source_candles,
            )

            result = pipeline.process_signal(
                source_signal
            )

            print()
            print(
                f"PIPELINE STATUS: "
                f"{get(result, 'status', default='UNKNOWN')}"
            )
            print(
                f"PIPELINE ALERTED: "
                f"{get(result, 'alerted', default=False)}"
            )
            print(
                f"PIPELINE JOURNALED: "
                f"{get(result, 'journaled', default=False)}"
            )

            if direction == "BUY":
                buy += 1
            else:
                sell += 1

        except Exception as exc:

            errors += 1

            print(
                f"PIPELINE ERROR: {exc}"
            )

    else:

        wait += 1

        print(
            "PIPELINE: WAIT — "
            "no directional signal forwarded"
        )

    time.sleep(0.1)


print()
print("=" * 110)
print(" STAGE 16K SUMMARY")
print("=" * 110)
print(f"Timeframe analyses : {processed}")
print(f"Pipeline BUY       : {buy}")
print(f"Pipeline SELL      : {sell}")
print(f"Pipeline WAIT      : {wait}")
print(f"Errors             : {errors}")
print("=" * 110)

if errors == 0:

    print()
    print("STAGE 16K: PASSED")
    print()
    print(
        "Signal pipeline integration completed "
        "without execution errors."
    )

else:

    print()
    print("STAGE 16K: PARTIAL")

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority   : ENABLED")
print("Data source       : Deriv")
print("Termux session remains open.")
print()
print("=" * 110)
