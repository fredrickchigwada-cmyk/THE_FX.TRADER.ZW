"""
Stage 17 — Production Runtime test
"""

from core.production_runtime import ProductionRuntime


def main():
    print("=" * 70)
    print("STAGE 17 — PRODUCTION RUNTIME TEST")
    print("=" * 70)

    runtime = ProductionRuntime()

    print("Runtime initialization : READY")
    print("Primary market         :", runtime.PRIMARY_MARKET)
    print("Primary symbol         :", runtime.PRIMARY_SYMBOL)
    print("Primary timeframe      :", runtime.PRIMARY_TIMEFRAME)
    print("Signal-only mode       :", "ENABLED")
    print("Trade execution        :", "DISABLED")

    assert runtime.PRIMARY_MARKET == "XAUUSD"
    assert runtime.PRIMARY_SYMBOL == "frxXAUUSD"
    assert runtime.PRIMARY_TIMEFRAME == "M1"

    print("Component wiring       : PASSED")

    print()
    print("Starting controlled 30-second production run...")
    print()

    result = runtime.run(duration=30)

    snapshot = runtime.snapshot()

    print("-" * 70)
    print("Runtime completed      :", result)
    print("Ticks received         :", snapshot["ticks"])
    print("Latest price           :", snapshot["last_price"])
    print("Connected after stop   :", snapshot["connected"])
    print("Running after stop     :", snapshot["running"])
    print("Rate limited           :", snapshot["rate_limited"])
    print("Stale                  :", snapshot["stale"])
    print("Last error             :", snapshot["last_error"] or "NONE")

    assert result is True
    assert snapshot["running"] is False
    assert snapshot["connected"] is False
    assert snapshot["trade_execution"] is False
    assert snapshot["signal_only"] is True

    print()
    print("Runtime shutdown       : PASSED")
    print("Signal-only safety     : PASSED")
    print()
    print("=" * 70)
    print("STAGE 17: PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()
