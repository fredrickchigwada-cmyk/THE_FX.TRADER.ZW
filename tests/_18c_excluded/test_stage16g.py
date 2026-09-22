import json
import time
import threading
from pathlib import Path

from core.deriv_ws import DerivWebSocket


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

COUNT = 250

# Conservative pacing for Deriv/local protection.
REQUEST_DELAY = 8.0
RATE_LIMIT_WAIT = 30.0
TIMEOUT = 20.0
MAX_ATTEMPTS = 5

BASE_DIR = Path("data/historical_bootstrap")
BASE_DIR.mkdir(parents=True, exist_ok=True)

responses = {}
lock = threading.Lock()
request_id = 5000


def on_message(data):
    req_id = data.get("req_id")

    if req_id is None:
        return

    try:
        req_id = int(req_id)
    except (TypeError, ValueError):
        return

    with lock:
        responses[req_id] = data


def next_request_id():
    global request_id
    request_id += 1
    return request_id


def load_saved(symbol, timeframe):

    path = BASE_DIR / f"{symbol}_{timeframe}.json"

    if not path.exists():
        return None

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )

        candles = data.get("candles", [])

        if len(candles) >= 200:
            return data

    except Exception:
        pass

    return None


def save_candles(
    market,
    symbol,
    timeframe,
    granularity,
    candles,
):

    path = BASE_DIR / f"{symbol}_{timeframe}.json"

    payload = {
        "market": market,
        "symbol": symbol,
        "timeframe": timeframe,
        "granularity": granularity,
        "requested": COUNT,
        "received": len(candles),
        "timestamp": time.time(),
        "candles": candles,
    }

    temp = path.with_suffix(".tmp")

    temp.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    temp.replace(path)


def request_history(ws, symbol, timeframe, granularity):

    for attempt in range(1, MAX_ATTEMPTS + 1):

        req_id = next_request_id()

        request = {
            "ticks_history": symbol,
            "style": "candles",
            "granularity": granularity,
            "count": COUNT,
            "end": "latest",
            "req_id": req_id,
        }

        try:

            ws.send(request)

        except Exception as exc:

            message = str(exc)

            print(
                f"    attempt {attempt}: SEND ERROR — {message}"
            )

            if (
                "rate protection" in message.lower()
                or "rate limit" in message.lower()
            ):

                print(
                    f"    waiting {RATE_LIMIT_WAIT}s..."
                )

                time.sleep(RATE_LIMIT_WAIT)
                continue

            time.sleep(REQUEST_DELAY)
            continue

        deadline = time.time() + TIMEOUT
        response = None

        while time.time() < deadline:

            with lock:
                response = responses.pop(req_id, None)

            if response is not None:
                break

            time.sleep(0.2)

        if response is None:

            print(
                f"    attempt {attempt}: TIMEOUT"
            )

            if attempt < MAX_ATTEMPTS:
                print(
                    f"    waiting {RATE_LIMIT_WAIT}s..."
                )
                time.sleep(RATE_LIMIT_WAIT)

            continue

        error = response.get("error")

        if error:

            message = error.get(
                "message",
                "Unknown Deriv error",
            )

            print(
                f"    attempt {attempt}: {message}"
            )

            if (
                "rate" in message.lower()
                or "limit" in message.lower()
                or "protect" in message.lower()
            ):

                print(
                    f"    waiting {RATE_LIMIT_WAIT}s..."
                )

                time.sleep(RATE_LIMIT_WAIT)

            else:

                time.sleep(REQUEST_DELAY)

            continue

        raw = response.get("candles", [])

        valid = []

        for candle in raw:

            try:

                valid.append({
                    "epoch": int(candle["epoch"]),
                    "open": float(candle["open"]),
                    "high": float(candle["high"]),
                    "low": float(candle["low"]),
                    "close": float(candle["close"]),
                })

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

        if len(valid) >= 200:
            return valid

        print(
            f"    attempt {attempt}: "
            f"only {len(valid)} valid candles"
        )

        time.sleep(REQUEST_DELAY)

    return None


print()
print("=" * 70)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16G — RATE-SAFE HISTORICAL BOOTSTRAP")
print("=" * 70)
print()

ws = DerivWebSocket(on_message=on_message)

try:

    ws.connect()

    for _ in range(30):

        if ws.connected:
            break

        time.sleep(0.5)

    if not ws.connected:

        print("DERIV CONNECTION: FAILED")
        raise SystemExit(1)

    print("DERIV CONNECTION: PASSED")
    print()
    print(
        "Existing valid history will be preserved."
    )
    print(
        "Only missing/incomplete timeframes will be requested."
    )
    print()

    ready = 0

    # XAUUSD is intentionally first.
    for market, symbol in MARKETS.items():

        print()
        print(
            f"--- {market} ({symbol}) ---"
        )

        market_ready = True

        for timeframe, granularity in TIMEFRAMES.items():

            saved = load_saved(
                symbol,
                timeframe,
            )

            if saved is not None:

                count = len(
                    saved.get("candles", [])
                )

                print(
                    f"  {timeframe}: "
                    f"{count} existing -> READY"
                )

                continue

            print(
                f"  {timeframe}: requesting "
                f"{COUNT} candles..."
            )

            candles = request_history(
                ws,
                symbol,
                timeframe,
                granularity,
            )

            if candles is None:

                print(
                    f"  {timeframe}: NOT READY"
                )

                market_ready = False

            else:

                save_candles(
                    market,
                    symbol,
                    timeframe,
                    granularity,
                    candles,
                )

                print(
                    f"  {timeframe}: "
                    f"{len(candles)} -> READY"
                )

            # Strong spacing between requests.
            time.sleep(REQUEST_DELAY)

        if market_ready:
            ready += 1

    print()
    print("=" * 70)
    print(" STAGE 16G SUMMARY")
    print("=" * 70)

    for market, symbol in MARKETS.items():

        states = []
        complete = True

        for timeframe in TIMEFRAMES:

            data = load_saved(
                symbol,
                timeframe,
            )

            if data is None:

                states.append(
                    f"{timeframe}:NOT READY"
                )

                complete = False

            else:

                count = len(
                    data.get("candles", [])
                )

                states.append(
                    f"{timeframe}:{count}"
                )

                if count < 200:
                    complete = False

        if complete:
            status = "READY"
        else:
            status = "PARTIAL"

        print(
            f"{market:<20} "
            + " | ".join(states)
            + f" | {status}"
        )

    print("-" * 70)

    fully_ready = 0

    for market, symbol in MARKETS.items():

        complete = True

        for timeframe in TIMEFRAMES:

            data = load_saved(
                symbol,
                timeframe,
            )

            if (
                data is None
                or len(data.get("candles", [])) < 200
            ):
                complete = False
                break

        if complete:
            fully_ready += 1

    print(
        f"Markets configured : {len(MARKETS)}"
    )
    print(
        f"Markets fully ready: {fully_ready}"
    )
    print(
        f"History directory  : {BASE_DIR}"
    )

    print("=" * 70)
    print()

    xau_complete = all(
        (
            load_saved(
                "frxXAUUSD",
                timeframe,
            )
            is not None
        )
        for timeframe in TIMEFRAMES
    )

    if xau_complete:

        print("STAGE 16G: PASSED")
        print()
        print(
            "XAUUSD has complete M1/M3/M5 historical data."
        )

    else:

        print("STAGE 16G: PARTIAL")
        print()
        print(
            "XAUUSD history is still missing one or more timeframes."
        )

finally:

    try:
        ws.stop()
    except Exception:
        pass

print()
print("Automatic trading : DISABLED")
print("Signal-only mode   : ENABLED")
print("XAUUSD priority    : ENABLED")
print("Data source        : Deriv")
print("Termux session remains open.")
print()
