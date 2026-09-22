import sys
from pathlib import Path

from config.settings import (
    BOT_NAME,
    VERSION,
    SIGNAL_ONLY,
    DEFAULT_TIMEFRAMES,
    REQUESTED_MARKETS,
    CONTACT,
    COPYRIGHT,
)


def check_python():
    return sys.version_info >= (3, 10)


def check_signal_only():
    return SIGNAL_ONLY is True


def check_configuration():
    return bool(BOT_NAME and VERSION and CONTACT and COPYRIGHT)


def check_timeframes():
    return len(DEFAULT_TIMEFRAMES) > 0


def check_markets():
    return len(REQUESTED_MARKETS) > 0


def check_directories():
    required = [
        Path("config"),
        Path("core"),
        Path("data"),
        Path("logs"),
        Path("signals"),
        Path("tests"),
    ]
    return all(path.is_dir() for path in required)


def run_diagnostics():
    checks = {
        "Python environment": check_python(),
        "Project structure": check_directories(),
        "Configuration": check_configuration(),
        "Signal-only mode": check_signal_only(),
        "Timeframes": check_timeframes(),
        "Markets": check_markets(),
    }

    print()
    print("=" * 50)
    print(f"       {BOT_NAME}")
    print("=" * 50)
    print()
    print(f"Version: {VERSION}")
    print()
    print("SYSTEM DIAGNOSTICS")
    print()

    for name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"[{status}] {name}")

    print()
    print("Deriv connection : NOT STARTED")
    print("Market analysis  : NOT STARTED")
    print("Signal engine    : NOT STARTED")
    print("Alerts           : NOT STARTED")
    print()

    if all(checks.values()):
        print("STATUS: SYSTEM READY")
        print()
        print("Signal-only protection: ENABLED")
        print("Automatic trading: DISABLED")
    else:
        print("STATUS: FOUNDATION ERROR")

    print()
    print(COPYRIGHT)
    print(CONTACT)
    print("=" * 50)
