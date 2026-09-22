"""
THE_FX.TRADER.BOT.ZW
Stage 12 startup entry point.

Signal-only architecture:
Deriv -> Market Data -> Candles -> Technical Analysis
-> Signal Engine -> Protection -> Alerts

NO automatic trade execution.
"""

from __future__ import annotations

import time

try:
    from config.settings import VERSION
except ImportError:
    VERSION = "1.0.0"

from core.system_controller import SystemController


def connection_check() -> bool:
    """
    Stage 12 placeholder connection check.

    The live Deriv service will be connected through the existing
    MarketService/Deriv WebSocket layer.

    Returning True here allows the system controller itself to be
    tested independently.
    """
    return True


def reconnect() -> bool:
    """
    Safe reconnect hook.

    This does not place or modify trades.
    """
    return connection_check()


def main():

    print("=" * 58)
    print("       THE_FX.TRADER.BOT.ZW")
    print("=" * 58)
    print()
    print(f"Version: {VERSION}")
    print()
    print("STAGE 12 — AUTO-START / WATCHDOG")
    print()
    print("[✓] Signal-only mode")
    print("[✓] Automatic trading disabled")
    print("[✓] Connection watchdog")
    print("[✓] Stale-data protection")
    print("[✓] Reconnect protection")
    print("[✓] Emergency STOP")
    print()

    controller = SystemController(
        connection_check=connection_check,
        reconnect=reconnect,
        watchdog_interval=10,
        stale_after=30,
    )

    if controller.start():
        print("[✓] Watchdog started")
    else:
        print("[!] Watchdog did not start")

    time.sleep(0.2)

    status = controller.status()

    print()
    print("SYSTEM STATUS")
    print(f"Running       : {status.running}")
    print(f"Connected     : {status.connected}")
    print(f"Healthy       : {status.healthy}")
    print(f"Stale         : {status.stale}")
    print(f"Reconnects    : {status.reconnects}")
    print(f"Checks        : {status.checks}")
    print(f"Emergency STOP: {status.emergency_stop}")
    print()
    print("Automatic trading: DISABLED")
    print()
    print("© 2026 THE_FX.TRADER.BOT.ZW — All Rights Reserved")
    print("+263 78 455 2452")
    print("=" * 58)

    controller.stop()


if __name__ == "__main__":
    main()
