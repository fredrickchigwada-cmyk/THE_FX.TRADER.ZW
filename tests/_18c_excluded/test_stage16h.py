import json
from pathlib import Path

from core.technical_analysis import TechnicalAnalysis
from core.candle_engine import Candle


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
        data = json.loads(path.read_text(encoding="utf-8"))

        if isinstance(data, dict):
            return data.get("candles", [])

        if isinstance(data, list):
            return data

    except Exception:
        pass

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


def get_value(obj, *names, default=None):

    for name in names:

        if hasattr(obj, name):
            return getattr(obj, name)

        if isinstance(obj, dict) and name in obj:
            return obj[name]

    return default


print()
print("=" * 100)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16H — MULTI-MARKET TECHNICAL ANALYSIS")
print("=" * 100)
print()

analyzer = TechnicalAnalysis()

successful = 0
failed = 0

for market, symbol in MARKETS.items():

    print()
    print("=" * 100)
    print(f"{market} ({symbol})")
    print("=" * 100)

    for timeframe in TIMEFRAMES:

        raw = load_candles(
            symbol,
            timeframe,
        )

        candles = build_candles(
            symbol,
            timeframe,
            raw,
        )

        if len(candles) < 200:

            print(
                f"{timeframe:<5} "
                f"INSUFFICIENT DATA "
                f"({len(candles)}/200)"
            )

            failed += 1
            continue

        try:

            result = analyzer.analyze(candles)

            price = get_value(
                result,
                "price",
                "current_price",
            )

            if price is None:
                price = candles[-1].close

            ema50 = get_value(
                result,
                "ema50",
                "ema_50",
            )

            ema200 = get_value(
                result,
                "ema200",
                "ema_200",
            )

            rsi = get_value(
                result,
                "rsi",
                "rsi14",
                "rsi_14",
            )

            atr = get_value(
                result,
                "atr",
                "atr14",
                "atr_14",
            )

            trend = get_value(
                result,
                "trend",
            )

            structure = get_value(
                result,
                "structure",
                "market_structure",
            )

            support = get_value(
                result,
                "support",
            )

            resistance = get_value(
                result,
                "resistance",
            )

            momentum = get_value(
                result,
                "momentum",
            )

            candle_confirmation = get_value(
                result,
                "candle_confirmation",
                "candle_confirmed",
            )

            print()
            print(
                f"{timeframe} — "
                f"candles={len(candles)}"
            )

            print(f"  Price       : {price}")
            print(f"  EMA 50      : {ema50}")
            print(f"  EMA 200     : {ema200}")
            print(f"  RSI 14      : {rsi}")
            print(f"  ATR 14      : {atr}")
            print(f"  Trend       : {trend}")
            print(f"  Structure   : {structure}")
            print(f"  Support     : {support}")
            print(f"  Resistance  : {resistance}")
            print(f"  Momentum    : {momentum}")
            print(
                f"  Candle      : "
                f"{candle_confirmation}"
            )

            successful += 1

        except Exception as exc:

            print(
                f"{timeframe:<5} "
                f"ANALYSIS ERROR: {exc}"
            )

            failed += 1


expected = len(MARKETS) * len(TIMEFRAMES)

print()
print("=" * 100)
print(" STAGE 16H SUMMARY")
print("=" * 100)
print(f"Analysis completed : {successful}")
print(f"Analysis errors    : {failed}")
print(f"Expected analyses  : {expected}")
print("=" * 100)

if successful == expected:

    print()
    print("STAGE 16H: PASSED")
    print()
    print(
        "All 9 markets have technical analysis "
        "available on M1/M3/M5."
    )

else:

    print()
    print("STAGE 16H: PARTIAL")
    print()
    print(
        "Some market/timeframe analyses require attention."
    )

print()
print("Automatic trading : DISABLED")
print("Signal-only mode   : ENABLED")
print("XAUUSD priority    : ENABLED")
print("Data source        : Deriv")
print("Termux session remains open.")
print()
