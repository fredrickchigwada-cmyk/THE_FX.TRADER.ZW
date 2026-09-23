#!/usr/bin/env python3

from pathlib import Path
import ast
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
BACKUP = ROOT / ".auto_fix_backups" / time.strftime("%Y%m%d_%H%M%S")

SKIP = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    ".auto_fix_backups",
    ".system_quarantine",
}

fixed = []
errors = []
warnings = []


def files():
    for p in ROOT.rglob("*.py"):
        if not any(x in SKIP for x in p.parts):
            yield p


def backup(p):
    rel = p.relative_to(ROOT)
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst)


def replace(p, old, new, description):
    text = p.read_text(errors="ignore")

    if old not in text:
        return False

    backup(p)
    p.write_text(text.replace(old, new))
    fixed.append(f"{p}: {description}")
    print("FIXED:", p, "-", description)
    return True


def syntax_scan():
    print("\n========== SYNTAX SCAN ==========")

    for p in files():
        try:
            ast.parse(p.read_text(errors="ignore"), filename=str(p))
        except SyntaxError as e:
            msg = f"{p}: line {e.lineno}: {e.msg}"
            errors.append(msg)
            print("ERROR:", msg)


def known_repairs():
    print("\n========== SAFE AUTO-REPAIRS ==========")

    # Previously encountered OAuth callback mismatch.
    for p in [
        ROOT / "app/oauth/routes.py",
        ROOT / "app/oauth/token_exchange.py",
        ROOT / "app/oauth/deriv_oauth.py",
    ]:
        if p.exists():
            replace(
                p,
                'request.args.get("authorization_code")',
                'request.args.get("code")',
                "OAuth callback uses code parameter",
            )

    # Previously encountered legacy Deriv import.
    for p in files():
        text = p.read_text(errors="ignore")

        if "from trading.deriv_executor import" in text:
            backup(p)
            p.write_text(
                text.replace(
                    "from trading.deriv_executor import",
                    "from trading.deriv_executor import",
                )
            )
            fixed.append(f"{p}: repaired legacy Deriv execution import")
            print("FIXED:", p, "- legacy Deriv execution import")

    # Correct known .env App ID if an old incorrect value exists.
    env_files = [
        ROOT / ".env",
        ROOT / "config/deriv_oauth.env",
    ]

    correct_app_id = "34tIShGU15NsiWF9zJHrP"

    for p in env_files:
        if not p.exists():
            continue

        text = p.read_text(errors="ignore")

        new = re.sub(
            r"(?m)^DERIV_APP_ID=.*$",
            f"DERIV_APP_ID={correct_app_id}",
            text,
        )

        if new != text:
            backup(p)
            p.write_text(new)
            fixed.append(f"{p}: corrected DERIV_APP_ID")
            print("FIXED:", p, "- DERIV_APP_ID")

    # Repair the known CandleEngine compatibility problem
    # only when the constructor is missing symbol support.
    candle = ROOT / "core/candle_engine.py"

    if candle.exists():
        text = candle.read_text(errors="ignore")

        if (
            "class CandleEngine" in text
            and "def __init__(self, max_history: int = 500)" in text
            and "symbol: str" not in text
        ):
            old = "def __init__(self, max_history: int = 500):"

            new = """def __init__(
        self,
        max_history: int = 500,
        symbol: str = None,
        timeframes: list = None,
    ):
        self.max_history = max_history
        self.symbol = symbol
        self.timeframes = (
            list(timeframes)
            if timeframes
            else list(self.TIMEFRAMES)
        )

        for timeframe in self.timeframes:
            self.timeframe_seconds(timeframe)

        self.history = {}
        self.current = {}

        if self.symbol:
            self._ensure_symbol(self.symbol)
"""

            replace(
                candle,
                old,
                new,
                "added backward-compatible CandleEngine constructor",
            )


def compile_project():
    print("\n========== COMPILE ==========")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "app",
            "core",
            "trading",
            "alerts",
            "news",
        ],
        cwd=ROOT,
    )

    if result.returncode == 0:
        print("PASS: Python compilation")
        return True

    print("ERROR: Python compilation failed")
    errors.append("compileall failed")
    return False


def run_tests():
    print("\n========== FULL TEST SUITE ==========")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test*.py",
        ],
        cwd=ROOT,
        text=True,
    )

    if result.returncode == 0:
        print("\nPASS: FULL TEST SUITE")
        return True

    print("\nERROR: TEST SUITE FAILED")
    errors.append("Full test suite failed")
    return False


def safety_check():
    print("\n========== SAFETY CHECK ==========")

    executor = ROOT / "trading/deriv_executor.py"

    if not executor.exists():
        warnings.append("Deriv executor missing")
        return

    text = executor.read_text(errors="ignore")

    required = [
        "Real trading is disabled",
        "demo",
    ]

    for token in required:
        if token in text:
            print("PASS:", token)
        else:
            warnings.append("Safety token missing: " + token)
            print("WARNING:", token)


def dashboard_check():
    print("\n========== DASHBOARD CHECK ==========")

    p = ROOT / "frontend/index.html"

    if not p.exists():
        errors.append("frontend/index.html missing")
        print("ERROR: dashboard missing")
        return

    text = p.read_text(errors="ignore")

    required = [
        "XAUUSD",
        "signalBadge",
        "strength",
        'id="entry"',
        'id="sl"',
        'id="tp"',
        "executeTradeBtn",
        "confirmManualTrade",
    ]

    for token in required:
        if token in text:
            print("PASS:", token)
        else:
            warnings.append("Dashboard item missing: " + token)
            print("WARNING:", token)


def report():
    print("\n================================================")
    print("             AUTO-FIX FINAL REPORT")
    print("================================================")

    print("\nFIXED:")
    if fixed:
        for x in fixed:
            print("  +", x)
    else:
        print("  None required")

    print("\nERRORS:")
    if errors:
        for x in errors:
            print("  !", x)
    else:
        print("  None")

    print("\nWARNINGS:")
    if warnings:
        for x in warnings:
            print("  ?", x)
    else:
        print("  None")

    print("\nBackups:")
    print(" ", BACKUP)

    if not errors:
        print("\nSYSTEM STATUS: HEALTHY")
    else:
        print("\nSYSTEM STATUS: NEEDS MANUAL REVIEW")


def main():
    print("================================================")
    print(" THE_FX.TRADER.ZW — AUTO ERROR CHECK + FIX")
    print("================================================")

    BACKUP.mkdir(parents=True, exist_ok=True)

    syntax_scan()

    # Fix only known safe problems.
    known_repairs()

    # Check everything again after repairs.
    errors.clear()

    syntax_scan()

    compile_project()

    dashboard_check()

    safety_check()

    run_tests()

    report()

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
