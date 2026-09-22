#!/data/data/com.termux/files/usr/bin/bash
set -e

ROOT="$(pwd)"
SDK="$PREFIX/var/lib/proot-distro/containers/ubuntu/rootfs/root/.buildozer/android/platform/android-sdk"
PLATFORM="$SDK/platforms/android-35"
TOOLS="$SDK/build-tools/37.0.0"

BUILD="$ROOT/arm_build"
CLASSES="$BUILD/classes"
DEX="$BUILD/dex"
UNSIGNED="$BUILD/unsigned.apk"
ALIGNED="$BUILD/THE_FX.TRADER.BOT.ZW.apk"
FINAL="$HOME/storage/downloads/THE_FX.TRADER.BOT.ZW.apk"

echo "=========================================="
echo " THE_FX.TRADER.BOT.ZW"
echo " ARM64 APK BUILD"
echo "=========================================="

rm -rf "$BUILD"
mkdir -p "$CLASSES" "$DEX"

echo
echo "[1/7] Compiling Java..."

javac \
  -source 8 \
  -target 8 \
  -bootclasspath "$PLATFORM/android.jar" \
  -d "$CLASSES" \
  "$ROOT/app/src/main/java/com/thefxtrader/botzw/MainActivity.java"

echo "Java compilation: OK"

echo
echo "[2/7] Creating DEX..."

"$TOOLS/d8" \
  --lib "$PLATFORM/android.jar" \
  --output "$DEX" \
  "$CLASSES/com/thefxtrader/botzw/MainActivity.class"

echo "DEX compilation: OK"

echo
echo "[3/7] Compiling Android resources..."

"$PREFIX/bin/aapt" package \
  -f \
  -M "$ROOT/app/src/main/AndroidManifest.xml" \
  -S "$ROOT/app/src/main/res" \
  -I "$PLATFORM/android.jar" \
  -F "$UNSIGNED"

echo "Resources: OK"

echo
echo "[4/7] Adding classes.dex..."

python - "$UNSIGNED" "$DEX/classes.dex" <<'PY'
import sys
import zipfile

apk = sys.argv[1]
dex = sys.argv[2]

with zipfile.ZipFile(apk, "a") as z:
    z.write(dex, "classes.dex")
PY

echo "DEX added: OK"

echo
echo "[5/7] Aligning APK..."

zipalign -f -p 4 "$UNSIGNED" "$ALIGNED"

echo "ZIP alignment: OK"

echo
echo "[6/7] Signing APK..."

mkdir -p "$HOME/.android"

if [ ! -f "$HOME/.android/debug.keystore" ]; then
    keytool -genkeypair \
      -v \
      -keystore "$HOME/.android/debug.keystore" \
      -storepass android \
      -alias androiddebugkey \
      -keypass android \
      -keyalg RSA \
      -keysize 2048 \
      -validity 10000 \
      -dname "CN=Android Debug,O=Android,C=US"
fi

apksigner sign \
  --ks "$HOME/.android/debug.keystore" \
  --ks-pass pass:android \
  --ks-key-alias androiddebugkey \
  --key-pass pass:android \
  "$ALIGNED"

echo "APK signing: OK"

echo
echo "[7/7] Verifying APK..."

apksigner verify --verbose "$ALIGNED"

echo
echo "=========================================="
echo " APK BUILD SUCCESSFUL"
echo "=========================================="

ls -lh "$ALIGNED"

echo
echo "APK:"
echo "$ALIGNED"

echo
echo "Installing copy to Downloads..."

cp "$ALIGNED" "$FINAL"

echo
echo "=========================================="
echo " APK READY"
echo "=========================================="

ls -lh "$FINAL"

echo
echo "PACKAGE:"
"$PREFIX/bin/aapt" dump badging "$FINAL" | head -5

echo
echo "=========================================="
echo " THE_FX.TRADER.BOT.ZW BUILD COMPLETE"
echo "=========================================="
