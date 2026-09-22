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


def load_candles(symbol, timeframe):
    path = BASE_DIR / f"{symbol}_{timeframe}.json"

    if not path.exists():
        return []

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        if isinstance(data, dict):
            return data.get("candles", [])

        if isinstance(data, list):
            return data

    except Exception:
        return []

    return []


def build_candles(symbol, timeframe, raw):

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


print()
print("=" * 110)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16I — MULTI-MARKET SIGNAL GENERATION")
print("=" * 110)
print()

engine = SignalEngine()

results = []
errors = 0

for market, symbol in MARKETS.items():

    print()
    print("=" * 110)
    print(f"{market} ({symbol})")
    print("=" * 110)

    for timeframe in TIMEFRAMES:

        raw = load_candles(symbol, timeframe)

        candles = build_candles(
            symbol,
            timeframe,
            raw,
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

            entry = get(
                signal,
                "entry",
            )

            stop_loss = get(
                signal,
                "stop_loss",
            )

            tp1 = get(
                signal,
                "tp1",
            )

            tp2 = get(
                signal,
                "tp2",
            )

            invalidation = get(
                signal,
                "invalidation",
            )

            explanation = get(
                signal,
                "explanation",
                default="",
            )

            candle_confirmed = get(
                signal,
                "candle_confirmed",
                "candle_confirmation",
                default=False,
            )

            print()
            print(
                f"{timeframe} | "
                f"{direction} | "
                f"Strength {strength}/10 | "
                f"Confirmations {confirmations}"
            )

            print(f"  Candles     : {len(candles)}")
            print(f"  Entry       : {entry}")
            print(f"  Stop Loss   : {stop_loss}")
            print(f"  TP1         : {tp1}")
            print(f"  TP2         : {tp2}")
            print(f"  Invalidation: {invalidation}")
            print(f"  Candle      : {candle_confirmed}")
            print(f"  Explanation : {explanation}")

            results.append(
                {
                    "market": market,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "signal": str(direction),
                    "strength": strength,
                    "confirmations": confirmations,
                }
            )

        except Exception as exc:

            errors += 1

            print()
            print(
                f"{timeframe} | SIGNAL ERROR: {exc}"
            )


expected = len(MARKETS) * len(TIMEFRAMES)

buy = sum(
    1 for r in results
    if r["signal"] == "BUY"
)

sell = sum(
    1 for r in results
    if r["signal"] == "SELL"
)

wait = sum(
    1 for r in results
    if r["signal"] == "WAIT"
)

print()
print("=" * 110)
print(" STAGE 16I SUMMARY")
print("=" * 110)
print(f"Analyses processed : {len(results)}")
print(f"BUY signals        : {buy}")
print(f"SELL signals       : {sell}")
print(f"WAIT signals       : {wait}")
print(f"Processing errors  : {errors}")
print(f"Expected analyses  : {expected}")
print("=" * 110)

if len(results) == expected and errors == 0:

    print()
    print("STAGE 16I: PASSED")
    print()
    print(
        "SignalEngine successfully processed "
        "all configured market/timeframe combinations."
    )

else:

    print()
    print("STAGE 16I: PARTIAL")

print()
print("Automatic trading : DISABLED")
print("Trade execution   : DISABLED")
print("Signal-only mode  : ENABLED")
print("XAUUSD priority   : ENABLED")
print("Data source       : Deriv")
print("Termux session remains open.")
print()
print("=" * 110)
