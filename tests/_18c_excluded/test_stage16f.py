import time

from core.deriv_ws import DerivWebSocket
from core.candle_engine import CandleEngine

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

engine = CandleEngine()
ticks = {symbol: 0 for symbol in MARKETS.values()}
errors = 0


def on_message(data):
    global errors

    if data.get("msg_type") != "tick":
        return

    tick = data.get("tick", {})
    symbol = tick.get("symbol")

    if symbol not in ticks:
        return

    try:
        price = float(tick["quote"])
        epoch = float(tick["epoch"])

        engine.update_tick(
            symbol,
            price,
            epoch
        )

        ticks[symbol] += 1

    except Exception:
        errors += 1


print()
print("=" * 66)
print(" THE_FX.TRADER.BOT.ZW")
print(" STAGE 16F — FAULT-TOLERANT MULTI-MARKET MONITOR")
print("=" * 66)
print()

ws = DerivWebSocket(on_message=on_message)

try:

    # --------------------------------------------------
    # CONNECTION
    # --------------------------------------------------
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

    # --------------------------------------------------
    # FIRST SUBSCRIPTION PASS
    # --------------------------------------------------
    subscribed = set()

    for name, symbol in MARKETS.items():

        try:
            ws.subscribe_ticks(symbol)
            subscribed.add(symbol)

            print(
                f"[OK] {name:<20} {symbol}"
            )

        except Exception as exc:

            print(
                f"[RETRY] {name:<20} {symbol}"
            )

        # Respect local request protection.
        time.sleep(3.5)

    print()
    print("Initial subscriptions complete.")
    print("Monitoring live data...")
    print()

    # --------------------------------------------------
    # FIRST DATA WINDOW
    # --------------------------------------------------
    time.sleep(15)

    # --------------------------------------------------
    # RETRY MARKETS WITH ZERO TICKS
    # --------------------------------------------------
    missing = [
        (name, symbol)
        for name, symbol in MARKETS.items()
        if ticks[symbol] == 0
    ]

    if missing:

        print()
        print("Markets with no ticks detected:")
        for name, symbol in missing:
            print(f" - {name}: {symbol}")

        print()
        print("Beginning controlled retry pass...")
        print()

        for name, symbol in missing:

            for attempt in range(2):

                try:

                    ws.subscribe_ticks(symbol)

                    print(
                        f"[RETRY {attempt + 1}] "
                        f"{name:<20} {symbol}"
                    )

                    break

                except Exception as exc:

                    print(
                        f"[WAIT] {name:<20} "
                        f"{exc}"
                    )

                    time.sleep(5)

            # Longer spacing for retry requests.
            time.sleep(5)

        print()
        print("Retry pass complete.")
        print("Collecting additional live data...")
        time.sleep(15)

    # --------------------------------------------------
    # FINAL RESULTS
    # --------------------------------------------------
    print()
    print("=" * 66)
    print(" FINAL LIVE DATA RESULTS")
    print("=" * 66)

    print(
        f"{'MARKET':<20}"
        f"{'SYMBOL':<15}"
        f"{'TICKS':>8}"
        f"{'M1':>8}"
        f"{'STATUS':>12}"
    )

    print("-" * 66)

    live_count = 0
    no_data = []

    for name, symbol in MARKETS.items():

        count = ticks[symbol]

        current = engine.get_current(
            symbol,
            "M1"
        )

        candle = "YES" if current else "NO"

        if count > 0:
            status = "LIVE"
            live_count += 1
        else:
            status = "NO DATA"
            no_data.append((name, symbol))

        print(
            f"{name:<20}"
            f"{symbol:<15}"
            f"{count:>8}"
            f"{candle:>8}"
            f"{status:>12}"
        )

    print("-" * 66)

    print(f"Markets configured : {len(MARKETS)}")
    print(f"Markets live       : {live_count}")
    print(f"Markets no-data    : {len(no_data)}")
    print(f"Processing errors  : {errors}")

    print()
    print("=" * 66)

    # --------------------------------------------------
    # XAUUSD MUST BE LIVE
    # --------------------------------------------------
    xau_ticks = ticks["frxXAUUSD"]

    if xau_ticks <= 0:
        print("STAGE 16F: FAILED")
        print("Reason: XAUUSD did not produce live ticks.")

    elif live_count >= 8:
        print("STAGE 16F: PASSED")
        print()
        print(
            "Multi-market live monitoring is operational."
        )

        if no_data:
            print()
            print("Markets still without data:")

            for name, symbol in no_data:
                print(f" - {name}: {symbol}")

            print()
            print(
                "These remain NO DATA and will not generate "
                "fake signals."
            )

    else:
        print("STAGE 16F: FAILED")
        print(
            "Too few markets produced live data."
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
