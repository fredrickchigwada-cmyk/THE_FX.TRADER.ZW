#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "=============================================="
echo " THE_FX.TRADER.BOT.ZW ANDROID BUILD"
echo "=============================================="

cd "$(dirname "$0")"

if command -v gradle >/dev/null 2>&1; then
    gradle --no-daemon clean
    gradle --no-daemon assembleDebug
    gradle --no-daemon assembleRelease
else
    echo "Gradle is not installed."
    exit 1
fi

echo
echo "APK OUTPUT:"
find app/build/outputs/apk -type f -name "*.apk" -exec ls -lh {} \;

echo
echo "BUILD COMPLETE"
