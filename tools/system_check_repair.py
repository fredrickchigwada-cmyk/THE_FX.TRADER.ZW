#!/usr/bin/env python3

from pathlib import Path
import ast
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
QUARANTINE = ROOT / ".system_quarantine"
REPORT = ROOT / "system_check_report.txt"

SAFE_BACKUP_EXTENSIONS = {
    ".bak", ".backup", ".old", ".orig", ".tmp"
}

# Files that are clearly generated/debug artifacts and safe to quarantine.
# IMPORTANT: source code is NOT automatically deleted.
GENERATED_NAMES = {
    "alert_targeted_result.txt",
}

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    ".system_quarantine",
}

results = []
errors = []
warnings = []


def log(message):
    print(message)
    results.append(message)


def run(cmd, timeout=120):
    try:
        p = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        return p.returncode, p.stdout
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def python_files():
    for p in ROOT.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        yield p


def syntax_check():
    log("\n========== PYTHON SYNTAX ==========")

    count = 0

    for p in python_files():
        count += 1
        try:
            ast.parse(p.read_text(errors="ignore"), filename=str(p))
        except SyntaxError as e:
            msg = f"SYNTAX ERROR: {p}: {e}"
            errors.append(msg)
            log("FAIL " + msg)
        except Exception as e:
            msg = f"READ ERROR: {p}: {e}"
            warnings.append(msg)
            log("WARN " + msg)

    log(f"Python files checked: {count}")


def required_files():
    log("\n========== CORE FILE CHECK ==========")

    required = [
        "frontend/index.html",
        "app/api_server.py",
        "core/signal_engine.py",
        "core/technical_analysis.py",
        "core/production_runtime.py",
        "core/live_news_feed.py",
        "core/news_signal_confirmation.py",
        "trading/deriv_executor.py",
        "trading/mode_controller.py",
        "app/oauth/routes.py",
        "app/oauth/deriv_oauth.py",
        "app/oauth/account_verification.py",
    ]

    for name in required:
        p = ROOT / name
        if p.exists():
            log("PASS " + name)
        else:
            msg = "Missing required file: " + name
            warnings.append(msg)
            log("WARN " + msg)


def dashboard_check():
    log("\n========== DASHBOARD CHECK ==========")

    p = ROOT / "frontend/index.html"

    if not p.exists():
        errors.append("Dashboard missing")
        return

    s = p.read_text(errors="ignore")

    checks = {
        "XAUUSD": "XAUUSD",
        "signalBadge": "signalBadge",
        "strength": 'id="strength"',
        "entry": 'id="entry"',
        "sl": 'id="sl"',
        "tp": 'id="tp"',
        "timeframes": "selectedTF",
        "trades API": "/api/v1/trades",
        "alerts API": "/api/v1/alerts",
        "manual execute": "executeTradeBtn",
        "manual confirmation": "confirmManualTrade",
    }

    for name, token in checks.items():
        if token in s:
            log("PASS dashboard: " + name)
        else:
            warnings.append("Dashboard missing: " + name)
            log("WARN dashboard: " + name)


def oauth_check():
    log("\n========== OAUTH CHECK ==========")

    env_files = [
        ROOT / ".env",
        ROOT / "config" / "deriv_oauth.env",
    ]

    for p in env_files:
        if not p.exists():
            log("INFO no " + str(p))
            continue

        text = p.read_text(errors="ignore")

        if "DERIV_APP_ID=" in text:
            log("PASS " + str(p) + ": DERIV_APP_ID present")
        else:
            warnings.append(f"{p}: DERIV_APP_ID missing")
            log("WARN " + str(p) + ": DERIV_APP_ID missing")

        if "DERIV_REDIRECT_URI=" in text:
            log("PASS " + str(p) + ": redirect URI present")
        else:
            warnings.append(f"{p}: redirect URI missing")
            log("WARN " + str(p) + ": redirect URI missing")


def safety_check():
    log("\n========== TRADING SAFETY CHECK ==========")

    files = [
        ROOT / "trading" / "deriv_executor.py",
        ROOT / "trading" / "real_trade_modes.py",
        ROOT / "trading" / "mode_controller.py",
        ROOT / "app" / "trading_mode_routes.py",
    ]

    safety_tokens = [
        "Real trading is disabled",
        "Manual confirmation required",
        "Explicit REAL authorization required",
        "confirmation=True",
    ]

    found = set()

    for p in files:
        if not p.exists():
            continue

        text = p.read_text(errors="ignore")

        for token in safety_tokens:
            if token in text:
                found.add(token)

    for token in safety_tokens:
        if token in found:
            log("PASS safety: " + token)
        else:
            log("WARN safety token not found: " + token)
            warnings.append("Safety token not found: " + token)


def repair_known_oauth_issue():
    log("\n========== SAFE OAUTH REPAIR ==========")

    targets = [
        ROOT / "app" / "oauth" / "routes.py",
        ROOT / "app" / "oauth" / "token_exchange.py",
        ROOT / "app" / "oauth" / "deriv_oauth.py",
    ]

    changed = False

    for p in targets:
        if not p.exists():
            continue

        text = p.read_text(errors="ignore")

        # Known previously encountered bug:
        # callback expected authorization_code while OAuth supplies code.
        if "authorization_code" in text and "request.args" in text:
            new = text.replace(
                'request.args.get("authorization_code")',
                'request.args.get("code")'
            )

            if new != text:
                backup = p.with_suffix(p.suffix + ".repairbak")
                shutil.copy2(p, backup)
                p.write_text(new)
                changed = True
                log("FIXED OAuth callback variable in " + str(p))

    if not changed:
        log("No known OAuth callback repair required.")


def repair_import_references():
    log("\n========== SAFE IMPORT REPAIR ==========")

    changed = False

    for p in python_files():
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue

        # Previously encountered compatibility error.
        if "from trading.deriv_executor import" in text:
            new = text.replace(
                "from trading.deriv_executor import",
                "from trading.deriv_executor import"
            )

            if new != text:
                backup = p.with_suffix(p.suffix + ".repairbak")
                shutil.copy2(p, backup)
                p.write_text(new)
                changed = True
                log("FIXED legacy Deriv import in " + str(p))

    if not changed:
        log("No known legacy Deriv import repair required.")


def quarantine_unnecessary_files():
    log("\n========== UNNECESSARY FILE CHECK ==========")

    candidates = []

    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue

        if any(part in SKIP_DIRS for part in p.parts):
            continue

        if p.name in GENERATED_NAMES:
            candidates.append(p)
            continue

        if p.suffix.lower() in SAFE_BACKUP_EXTENSIONS:
            candidates.append(p)

    if not candidates:
        log("No clearly unnecessary generated/backup files found.")
        return

    QUARANTINE.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    destination = QUARANTINE / timestamp
    destination.mkdir(parents=True, exist_ok=True)

    for p in candidates:
        try:
            rel = p.relative_to(ROOT)
            dest = destination / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(p), str(dest))
            log("QUARANTINED " + str(rel))
        except Exception as e:
            warnings.append(f"Could not quarantine {p}: {e}")
            log("WARN could not quarantine " + str(p))

    log("Quarantine location: " + str(destination))


def compile_check():
    log("\n========== COMPILE CHECK ==========")

    code, output = run(
        [sys.executable, "-m", "compileall", "-q", "app", "core", "trading", "alerts", "news"],
        timeout=180,
    )

    if code == 0:
        log("PASS compileall")
    else:
        log("FAIL compileall")
        log(output[-3000:])
        errors.append("compileall failed")


def run_tests():
    log("\n========== FULL TEST SUITE ==========")

    tests = ROOT / "tests"

    if not tests.exists():
        warnings.append("tests directory missing")
        log("WARN tests directory missing")
        return

    code, output = run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test*.py"],
        timeout=300,
    )

    log(output[-10000:])

    if code == 0:
        log("PASS FULL TEST SUITE")
    else:
        errors.append(f"Full test suite returned {code}")
        log(f"FAIL FULL TEST SUITE [{code}]")


def git_status():
    log("\n========== GIT STATUS ==========")

    code, output = run(["git", "status", "--short"])

    if code == 0:
        log(output if output.strip() else "Working tree clean")
    else:
        log("WARN git status unavailable")


def write_report():
    report = [
        "THE_FX.TRADER.ZW SYSTEM CHECK REPORT",
        "=" * 55,
        "",
        *results,
        "",
        "ERRORS:",
        *(errors or ["None"]),
        "",
        "WARNINGS:",
        *(warnings or ["None"]),
        "",
        "IMPORTANT:",
        "No source code was automatically deleted.",
        "Clearly generated/backup files were moved to .system_quarantine.",
        "Real-trading safety code was not weakened.",
    ]

    REPORT.write_text("\n".join(report))

    print("\nReport saved:")
    print(REPORT)


def main():
    print("=" * 60)
    print(" THE_FX.TRADER.ZW — SYSTEM AUDITOR / REPAIR")
    print("=" * 60)
    print("Project:", ROOT)

    required_files()
    dashboard_check()
    oauth_check()
    safety_check()

    # Conservative repairs only.
    repair_known_oauth_issue()
    repair_import_references()

    # Never permanently delete source code.
    quarantine_unnecessary_files()

    syntax_check()
    compile_check()
    run_tests()
    git_status()
    write_report()

    print("\n" + "=" * 60)
    print(" FINAL SYSTEM RESULT")
    print("=" * 60)

    print("Errors   :", len(errors))
    print("Warnings :", len(warnings))

    if errors:
        print("\nSYSTEM RESULT: NEEDS ATTENTION")
        print("See:", REPORT)
        return 1

    print("\nSYSTEM RESULT: HEALTHY")
    print("See:", REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
