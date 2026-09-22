#!/usr/bin/env python3

from pathlib import Path
import ast
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

PASS = []
FAIL = []
WARN = []

def ok(msg):
    PASS.append(msg)
    print(f"[PASS] {msg}")

def fail(msg):
    FAIL.append(msg)
    print(f"[FAIL] {msg}")

def warn(msg):
    WARN.append(msg)
    print(f"[WARN] {msg}")

def exists(rel):
    p = ROOT / rel
    if p.exists():
        ok(f"Required file exists: {rel}")
        return True
    fail(f"Missing required file: {rel}")
    return False

def read(rel):
    p = ROOT / rel
    try:
        return p.read_text(errors="replace")
    except Exception as e:
        fail(f"Cannot read {rel}: {e}")
        return ""

print("=" * 70)
print("       THE_FX.TRADER.BOT.ZW — MASTER PRE-RELEASE CHECK")
print("=" * 70)
print()

# ------------------------------------------------------------
# 1. REQUIRED PROJECT FILES
# ------------------------------------------------------------

print("=== 1. PROJECT STRUCTURE ===")

required = [
    "main.py",
    "core/production_runtime.py",
    "core/deriv_ws.py",
    "core/candle_engine.py",
    "core/signal_engine.py",
    "core/market_discovery.py",
    "core/multi_market_runtime.py",
    "core/news_intelligence.py",
    "core/news_signal_confirmation.py",
    "core/integration_pipeline.py",
    "api/android_bridge.py",
    "android_app/build.gradle",
    "android_app/settings.gradle",
    "android_app/app/build.gradle",
    "android_app/app/src/main/AndroidManifest.xml",
    "android_app/app/src/main/java/com/thefxtrader/botzw/MainActivity.java",
    ".github/workflows/android-apk.yml",
]

for f in required:
    exists(f)

# ------------------------------------------------------------
# 2. PYTHON SYNTAX
# ------------------------------------------------------------

print()
print("=== 2. PYTHON SYNTAX ===")

python_files = list(ROOT.rglob("*.py"))

excluded = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
}

checked = 0

for p in python_files:
    if any(part in excluded for part in p.parts):
        continue

    try:
        ast.parse(p.read_text(errors="replace"), filename=str(p))
        checked += 1
    except Exception as e:
        fail(f"Python syntax error: {p}: {e}")

if checked:
    ok(f"Python syntax checked: {checked} files")

# ------------------------------------------------------------
# 3. ANDROID MANIFEST XML
# ------------------------------------------------------------

print()
print("=== 3. ANDROID MANIFEST ===")

manifest = ROOT / "android_app/app/src/main/AndroidManifest.xml"

if manifest.exists():
    try:
        ET.parse(manifest)
        ok("AndroidManifest.xml is valid XML")
    except Exception as e:
        fail(f"AndroidManifest.xml XML error: {e}")

# ------------------------------------------------------------
# 4. GRADLE CONFIGURATION
# ------------------------------------------------------------

print()
print("=== 4. GRADLE CONFIGURATION ===")

root_gradle = read("android_app/build.gradle")
app_gradle = read("android_app/app/build.gradle")
settings_gradle = read("android_app/settings.gradle")

if "com.android.application" in root_gradle:
    ok("Android application plugin configured")
else:
    fail("Android application plugin not found")

if "compileSdk 35" in app_gradle:
    ok("compileSdk 35 configured")
else:
    warn("compileSdk 35 was not found exactly; inspect app/build.gradle")

if "targetSdk 35" in app_gradle:
    ok("targetSdk 35 configured")
else:
    warn("targetSdk 35 was not found exactly")

if "applicationId 'com.thefxtrader.botzw'" in app_gradle:
    ok("Android application ID is correct")
else:
    fail("Unexpected Android application ID")

if "namespace 'com.thefxtrader.botzw'" in app_gradle:
    ok("Android namespace is correct")
else:
    fail("Unexpected Android namespace")

# Explicit buildToolsVersion can cause CI mismatch.
m = re.search(r"buildToolsVersion\s+['\"]([^'\"]+)['\"]", app_gradle)

if m:
    version = m.group(1)
    warn(
        f"Explicit buildToolsVersion {version} is configured; "
        "AGP default may be preferable."
    )
else:
    ok("No explicit buildToolsVersion override")

# ------------------------------------------------------------
# 5. ANDROID MANIFEST CONTENT
# ------------------------------------------------------------

print()
print("=== 5. ANDROID MANIFEST CONTENT ===")

manifest_text = read(
    "android_app/app/src/main/AndroidManifest.xml"
)

if "android.permission.INTERNET" in manifest_text:
    ok("Android INTERNET permission configured")
else:
    fail("Android INTERNET permission missing")

if "android:name=\".MainActivity\"" in manifest_text:
    ok("MainActivity registered")
else:
    fail("MainActivity registration missing")

if "android:exported=\"true\"" in manifest_text:
    ok("MainActivity exported flag configured")
else:
    fail("MainActivity exported flag missing")

# ------------------------------------------------------------
# 6. BOT IDENTITY / PRIMARY MARKET
# ------------------------------------------------------------

print()
print("=== 6. BOT IDENTITY & XAUUSD ===")

all_text = ""

for rel in [
    "core/production_runtime.py",
    "core/deriv_ws.py",
    "core/market_discovery.py",
    "core/multi_market_runtime.py",
    "core/signal_engine.py",
    "api/android_bridge.py",
]:
    all_text += "\n" + read(rel)

if "THE_FX.TRADER.BOT.ZW" in all_text:
    ok("Bot identity THE_FX.TRADER.BOT.ZW found")
else:
    warn("Bot identity string not found in core runtime files")

if "XAUUSD" in all_text:
    ok("XAUUSD primary market reference found")
else:
    fail("XAUUSD reference missing")

if "frxXAUUSD" in all_text:
    ok("Deriv XAUUSD symbol frxXAUUSD found")
else:
    warn("frxXAUUSD not found; dynamic discovery may be used")

# ------------------------------------------------------------
# 7. SIGNAL-ONLY SAFETY
# ------------------------------------------------------------

print()
print("=== 7. SIGNAL-ONLY SAFETY ===")

execution_patterns = [
    r"\border_send\b",
    r"\border_send_async\b",
    r"\bplace_order\b",
    r"\bmodify_order\b",
    r"\bclose_order\b",
    r"\btrade_request\b",
    r"\bmt5\b",
    r"\bMetaTrader\b",
]

execution_hits = []

# Scan production Python code only.
# Test files are intentionally excluded because protection tests
# legitimately contain names such as place_order/modify_order
# while verifying that those operations are blocked.
production_dirs = [
    ROOT / "core",
    ROOT / "api",
]

production_files = []

for directory in production_dirs:
    if directory.exists():
        production_files.extend(directory.rglob("*.py"))

for p in production_files:
    if any(part in excluded for part in p.parts):
        continue

    try:
        text = p.read_text(errors="replace")
    except Exception:
        continue

    for pattern in execution_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            execution_hits.append(
                f"{p.relative_to(ROOT)} -> {pattern}"
            )

if execution_hits:
    for hit in execution_hits[:30]:
        fail(f"Potential trade-execution reference: {hit}")
else:
    ok("No obvious trade-execution APIs found")

# Also ensure signal-only language exists.
if re.search(r"signal.?only", all_text, re.IGNORECASE):
    ok("Signal-only configuration/reference found")
else:
    warn("Signal-only text not found in inspected runtime files")

# ------------------------------------------------------------
# 8. ANDROID BRIDGE
# ------------------------------------------------------------

print()
print("=== 8. ANDROID BRIDGE ===")

bridge = read("api/android_bridge.py")
java = read(
    "android_app/app/src/main/java/com/thefxtrader/botzw/MainActivity.java"
)

if "8765" in bridge:
    ok("Android bridge port 8765 configured")
else:
    fail("Android bridge port 8765 missing")

if "/snapshot" in bridge:
    ok("Snapshot API endpoint found")
else:
    fail("Snapshot API endpoint missing")

if "/stop" in bridge:
    ok("Emergency stop endpoint found")
else:
    warn("Emergency stop endpoint not found")

if "127.0.0.1:8765" in java:
    ok("Android app points to local backend 127.0.0.1:8765")
else:
    warn("Android app does not contain the expected local API address")

# ------------------------------------------------------------
# 9. CORE SAFETY / DATA QUALITY
# ------------------------------------------------------------

print()
print("=== 9. DATA & SIGNAL SAFETY ===")

signal_engine = read("core/signal_engine.py")
runtime = read("core/production_runtime.py")
multi = read("core/multi_market_runtime.py")

for name, text in [
    ("signal engine", signal_engine),
    ("production runtime", runtime),
    ("multi-market runtime", multi),
]:
    if "WAIT" in text:
        ok(f"{name} supports WAIT")
    else:
        warn(f"{name} has no obvious WAIT reference")

if "stale" in runtime.lower():
    ok("Production runtime contains stale-data handling")
else:
    warn("Production runtime stale-data handling not detected")

if "rate" in runtime.lower() and "limit" in runtime.lower():
    ok("Production runtime contains rate-limit handling references")
else:
    warn("Rate-limit handling not detected in production runtime")

# ------------------------------------------------------------
# 10. NEWS LAYER
# ------------------------------------------------------------

print()
print("=== 10. NEWS INTELLIGENCE ===")

news = read("core/news_intelligence.py")
news_confirm = read("core/news_signal_confirmation.py")

if "NewsIntelligence" in news:
    ok("NewsIntelligence present")
else:
    fail("NewsIntelligence missing")

if "NewsSignalConfirmation" in news_confirm:
    ok("NewsSignalConfirmation present")
else:
    fail("NewsSignalConfirmation missing")

if "XAUUSD" in news:
    ok("News intelligence contains XAUUSD relevance")
else:
    warn("XAUUSD not found in news intelligence")

# ------------------------------------------------------------
# 11. MULTI-MARKET
# ------------------------------------------------------------

print()
print("=== 11. MULTI-MARKET ===")

markets = [
    "XAUUSD",
    "BTCUSD",
    "STEP INDEX",
    "VOLATILITY 75",
    "VOLATILITY 10",
    "VOLATILITY 25",
    "VOLATILITY 50",
    "VOLATILITY 100",
    "BOOM 500",
    "BOOM 1000",
    "CRASH 500",
    "CRASH 1000",
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "NAS100",
    "US30",
]

for market in markets:
    if market in multi:
        ok(f"Requested market configured: {market}")
    else:
        warn(f"Requested market not found literally: {market}")

# ------------------------------------------------------------
# 12. GITHUB WORKFLOW
# ------------------------------------------------------------

print()
print("=== 12. GITHUB ACTIONS ===")

workflow = read(".github/workflows/android-apk.yml")

if "actions/checkout@" in workflow:
    ok("GitHub checkout action configured")
else:
    fail("GitHub checkout action missing")

if "actions/setup-java@" in workflow:
    ok("Java setup action configured")
else:
    fail("Java setup action missing")

if "java-version: '17'" in workflow:
    ok("GitHub workflow uses Java 17")
else:
    warn("Java 17 configuration not detected exactly")

if "platforms;android-35" in workflow:
    ok("Android 35 platform installation configured")
else:
    warn("Android 35 platform installation not found")

if "build-tools;36.0.0" in workflow:
    ok("Build Tools 36.0.0 installation configured")
else:
    warn("Build Tools 36.0.0 installation not found")

if "assembleDebug" in workflow:
    ok("Debug APK build command configured")
else:
    fail("assembleDebug command missing")

if "actions/upload-artifact@" in workflow:
    ok("APK/artifact upload configured")
else:
    warn("Artifact upload action not detected")

# ------------------------------------------------------------
# 13. GIT SYNC
# ------------------------------------------------------------

print()
print("=== 13. GIT SYNC ===")

def command(cmd):
    try:
        r = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=30,
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 99, "", str(e)

rc, local, err = command(["git", "rev-parse", "HEAD"])

if rc == 0:
    ok(f"Local Git commit: {local}")
else:
    warn(f"Could not read local Git commit: {err}")

rc, remote, err = command([
    "git", "ls-remote", "origin", "HEAD"
])

if rc == 0 and remote:
    remote_hash = remote.split()[0]
    ok(f"Remote Git commit: {remote_hash}")

    if local and local == remote_hash:
        ok("LOCAL = REMOTE")
    else:
        fail("LOCAL and REMOTE commits differ")
else:
    warn(f"Could not read remote Git commit: {err}")

rc, status, err = command(["git", "status", "--short"])

if rc == 0:
    if status:
        warn("Working tree has uncommitted changes:")
        print(status)
    else:
        ok("Git working tree is clean")
else:
    warn(f"Could not inspect Git status: {err}")

# ------------------------------------------------------------
# 14. TEST SUITE
# ------------------------------------------------------------

print()
print("=== 14. EXISTING TEST SUITE ===")

tests_dir = ROOT / "tests"

if tests_dir.exists():
    test_files = list(tests_dir.glob("test_*.py"))

    if test_files:
        print(f"Found {len(test_files)} test files")

        # Run pytest if available.
        rc, out, err = command([
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ])

        if rc == 0:
            ok("Existing pytest suite PASSED")
            if out:
                print(out[-3000:])
        elif rc == 5:
            warn("Pytest found no tests")
        elif rc == 1 and (
            "No module named pytest" in out
            or "No module named pytest" in err
        ):
            warn("Pytest is not installed in this Termux environment")
        elif rc == 1 and (
            "No module named pytest" in out
            or "No module named pytest" in err
        ):
            warn("Pytest is not installed in this Termux environment")
        else:
            fail("Existing pytest suite FAILED")
            if out:
                print(out[-3000:])
            if err:
                print(err[-3000:])
    else:
        warn("No test_*.py files found")
else:
    warn("tests directory not found")

# ------------------------------------------------------------
# 15. FINAL REPORT
# ------------------------------------------------------------

print()
print("=" * 70)
print("                    FINAL AUDIT")
print("=" * 70)

print(f"PASS   : {len(PASS)}")
print(f"FAIL   : {len(FAIL)}")
print(f"WARNING: {len(WARN)}")
print()

if FAIL:
    print("FAILURES:")
    for x in FAIL:
        print(" -", x)
    print()

if WARN:
    print("WARNINGS:")
    for x in WARN:
        print(" -", x)
    print()

if not FAIL:
    print("[RESULT] NO BLOCKING ERRORS FOUND")
    print()
    print("The project passed the automated pre-release audit.")
    print("Remaining warnings, if any, should be reviewed before release.")
else:
    print("[RESULT] BLOCKING ERRORS FOUND")
    print()
    print("Fix the FAIL items before proceeding to APK installation.")

print("=" * 70)

# Do not close Termux.
