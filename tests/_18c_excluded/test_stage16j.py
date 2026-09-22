import json
from pathlib import Path

from core.candle_engine import Candle
from core.signal_engine import SignalEngine


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


def confirm(signals):
    """
    Stage 8-style MTF confirmation.

    Only valid BUY/SELL signals count.
    WAIT does not count.
    Equal BUY/SELL counts produce WAIT.
    Agreement must be >= 60%.
    """

    valid = [
        s for s in signals
        if s["signal"] in ("BUY", "SELL")
    ]

    if not valid:
        return {
            "signal": "WAIT",
            "strength": 0,
            "agreement": 0,
            "reason": "NO_VALID_DIRECTIONAL_SIGNALS",
        }

    buys = sum(
        1 for s in valid
        if s["signal"] == "BUY"
    )

    sells = sum(
        1 for s in valid
        if s["signal"] == "SELL"
    )

    if buys == sells:
        return {
            "signal": "WAIT",
            "strength": 0,
            "agreement": 0,
            "reason": (
                f"CONFLICT: BUY={buys}, SELL={sells}"
            ),
        }

    if buys > sells:
        direction = "BUY"
        aligned = [
            s for s in valid
            if s["signal"] == "BUY"
        ]
    else:
        direction = "SELL"
        aligned = [
            s for s in valid
            if s["signal"] == "SELL"
        ]

    agreement = len(aligned) / len(valid)

    if agreement < 0.60:
        return {
            "signal": "WAIT",
            "strength": 0,
            "agreement": agreement,
            "reason": (
                f"WEAK_AGREEMENT: "
                f"{direction}={len(aligned)}/"
                f"{len(valid)}"
            ),
        }

    average_strength = (
        sum(
            float(s["strength"])
            for s in aligned
        ) / len(aligned)
    )

    mtf_strength = min(
        10,
        max(
            0,
            average_strength * agreement
        )
    )

    if mtf_strength < 6:
        return {
            "signal": "WAIT",
            "strength": round(mtf_strength, 2),
            "agreement": agreement,
            "reason": (
                f"MTF_STRENGTH_BELOW_MINIMUM: "
                f"{mtf_strength:.2f}/10"
            ),
        }

    return {
        "signal": direction,
        "strength": round(mtf_strength, 2),
        "agreement": agreement,
        "reason": (
            f"MTF_ALIGNED: "
            f"{direction}={len(aligned)}/"
            f"{len(valid)}"
        ),
    }


print()
print("=" * 110)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16J — MULTI-TIMEFRAME SIGNAL CONFIRMATION")
print("=" * 110)
print()

engine = SignalEngine()

total = 0
mtf_buy = 0
mtf_sell = 0
mtf_wait = 0
errors = 0

for market, symbol in MARKETS.items():

    print()
    print("=" * 110)
    print(f"{market} ({symbol})")
    print("=" * 110)

    signals = []

    for timeframe in TIMEFRAMES:

        candles = build(
            symbol,
            timeframe,
            load(symbol, timeframe),
        )

        try:

            signal = engine.generate(
                symbol,
                timeframe,
                candles,
            )

            direction = get(
                signal,
                "signal",
                "direction",
                default="WAIT",
            )

            strength = get(
                signal,
                "strength",
                default=0,
            )

            confirmations = get(
                signal,
                "confirmations",
                default=0,
            )

            signals.append(
                {
                    "timeframe": timeframe,
                    "signal": str(direction),
                    "strength": float(strength or 0),
                    "confirmations": int(
                        confirmations or 0
                    ),
                }
            )

            print(
                f"{timeframe}: "
                f"{direction} "
                f"{strength}/10 "
                f"({confirmations} confirmations)"
            )

            total += 1

        except Exception as exc:

            errors += 1

            print(
                f"{timeframe}: ERROR — {exc}"
            )

    result = confirm(signals)

    direction = result["signal"]

    if direction == "BUY":
        mtf_buy += 1
    elif direction == "SELL":
        mtf_sell += 1
    else:
        mtf_wait += 1

    print()
    print(
        f"MTF RESULT : {direction}"
    )
    print(
        f"MTF STRENGTH: "
        f"{result['strength']}/10"
    )
    print(
        f"AGREEMENT  : "
        f"{result['agreement'] * 100:.1f}%"
    )
    print(
        f"REASON     : "
        f"{result['reason']}"
    )


print()
print("=" * 110)
print(" STAGE 16J SUMMARY")
print("=" * 110)
print(f"Timeframe analyses : {total}")
print(f"MTF BUY            : {mtf_buy}")
print(f"MTF SELL           : {mtf_sell}")
print(f"MTF WAIT           : {mtf_wait}")
print(f"Processing errors  : {errors}")
print(
    f"Expected analyses : "
    f"{len(MARKETS) * len(TIMEFRAMES)}"
)
print("=" * 110)

if (
    total == len(MARKETS) * len(TIMEFRAMES)
    and errors == 0
):
    print()
    print("STAGE 16J: PASSED")
else:
    print()
    print("STAGE 16J: PARTIAL")

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority   : ENABLED")
print("Data source       : Deriv")
print("Termux session remains open.")
print()
print("=" * 110)
