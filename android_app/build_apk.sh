#!/data/data/com.termux/files/usr/bin/bash

set -e

PROJECT="$HOME/THE_FX_TRADER_BOT_ZW/android_app"
SDK="$PREFIX/var/lib/proot-distro/containers/ubuntu/rootfs/root/.buildozer/android/platform/android-sdk"
ANDROID_JAR="$SDK/platforms/android-35/android.jar"

AAPT="$(command -v aapt)"
D8="$SDK/build-tools/35.0.0/d8"
ZIPALIGN="$(command -v zipalign)"
APKSIGNER="$(command -v apksigner)"

echo "=========================================="
echo " THE_FX.TRADER.BOT.ZW"
echo " ARM64 ANDROID BUILD"
echo "=========================================="

cd "$PROJECT"

rm -rf build/release
mkdir -p build/release/classes
mkdir -p build/release/dex

echo
echo "[1/7] Checking ARM-compatible tools..."

echo "aapt:     $AAPT"
echo "d8:       $D8"
echo "zipalign: $ZIPALIGN"
echo "apksigner:$APKSIGNER"

echo
echo "[2/7] Compiling Java..."

javac \
  -source 8 \
  -target 8 \
  -classpath "$ANDROID_JAR" \
  -d build/release/classes \
  app/src/main/java/com/thefxtrader/botzw/MainActivity.java

echo "JAVA: OK"

echo
echo "[3/7] Creating DEX..."

"$D8" \
  --lib "$ANDROID_JAR" \
  --output build/release/dex \
  build/release/classes/com/thefxtrader/botzw/MainActivity.class

echo "DEX: OK"

echo
echo "[4/7] Packaging with ARM-compatible AAPT..."

"$AAPT" package \
  -f \
  -M app/src/main/AndroidManifest.xml \
  -S app/src/main/res \
  -I "$ANDROID_JAR" \
  -F build/release/unsigned.apk

echo "AAPT PACKAGE: OK"

echo
echo "[5/7] Adding DEX..."

python - <<'PY'
import zipfile

apk = "build/release/unsigned.apk"
dex = "build/release/dex/classes.dex"
out = "build/release/unsigned_dex.apk"

with zipfile.ZipFile(apk, "r") as zin:
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        zout.write(dex, "classes.dex")

print("DEX INSERTION: OK")
PY

echo
echo "[6/7] Aligning and signing..."

"$ZIPALIGN" -f 4 \
  build/release/unsigned_dex.apk \
  build/release/aligned.apk

"$APKSIGNER" sign \
  --ks "$HOME/.android/debug.keystore" \
  --ks-pass pass:android \
  --key-pass pass:android \
  --ks-key-alias androiddebugkey \
  --out THE_FX_TRADER_BOT_ZW.apk \
  build/release/aligned.apk

echo
echo "[7/7] Verifying..."

"$APKSIGNER" verify --verbose THE_FX_TRADER_BOT_ZW.apk

echo
echo "=== APK INFORMATION ==="

"$AAPT" dump badging THE_FX_TRADER_BOT_ZW.apk

echo
echo "=========================================="
echo " BUILD SUCCESSFUL"
echo "=========================================="

ls -lh THE_FX_TRADER_BOT_ZW.apk

mkdir -p "$HOME/storage/downloads"

cp THE_FX_TRADER_BOT_ZW.apk \
  "$HOME/storage/downloads/THE_FX_TRADER_BOT_ZW.apk"

echo
echo "APK:"
echo "$HOME/storage/downloads/THE_FX_TRADER_BOT_ZW.apk"
