#!/data/data/com.termux/files/usr/bin/bash

set -u

PROJECT="$HOME/THE_FX_TRADER_BOT_ZW"
cd "$PROJECT" || {
    echo "[ERROR] Cannot enter $PROJECT"
    exit 1
}

clear

echo "============================================================"
echo "             THE_FX.TRADER.BOT.ZW"
echo "============================================================"
echo "Mode            : SIGNAL-ONLY"
echo "Automatic Trade : DISABLED"
echo "Primary Market  : XAUUSD"
echo "Data Source     : Deriv"
echo "API             : http://127.0.0.1:8765"
echo "============================================================"
echo

if ! command -v python >/dev/null 2>&1; then
    echo "[ERROR] Python is not installed."
    echo "Run: pkg install python"
    exit 1
fi

if [ ! -f "api/android_bridge.py" ]; then
    echo "[ERROR] api/android_bridge.py not found."
    exit 1
fi

echo "[1/3] Python:"
python --version

echo
echo "[2/3] Checking project..."
python -m py_compile api/android_bridge.py core/production_runtime.py

if [ $? -ne 0 ]; then
    echo "[ERROR] Python syntax check failed."
    exit 1
fi

echo "[OK] Python files compile correctly."

echo
echo "[3/3] Starting THE_FX.TRADER.BOT.ZW..."
echo
echo "------------------------------------------------------------"
echo "BOT RUNNING"
echo "------------------------------------------------------------"
echo "Keep this Termux session open."
echo "Press Ctrl+C only when you want to stop the bot."
echo

exec python -u api/android_bridge.py
