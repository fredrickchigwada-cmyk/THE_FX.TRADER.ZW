#!/usr/bin/env python3

import json
import threading
import time
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Make the project root importable when this file is launched directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.production_runtime import ProductionRuntime


HOST = "127.0.0.1"
PORT = 8765

runtime = ProductionRuntime()


class AndroidBridgeHandler(BaseHTTPRequestHandler):

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            snapshot = runtime.snapshot()

            self._send_json({
                "ok": True,
                "service": "THE_FX.TRADER.BOT.ZW",
                "backend": snapshot,
            })
            return

        if self.path == "/snapshot":
            self._send_json(runtime.snapshot())
            return

        self._send_json({
            "ok": False,
            "error": "NOT_FOUND"
        }, 404)

    def do_POST(self):
        if self.path == "/stop":
            runtime.stop()

            self._send_json({
                "ok": True,
                "stopped": True,
                "message": "Emergency stop activated."
            })
            return

        self._send_json({
            "ok": False,
            "error": "NOT_FOUND"
        }, 404)

    def log_message(self, format, *args):
        return


def run_backend():
    try:
        runtime.run()
    except Exception as exc:
        print("[BACKEND ERROR]", repr(exc))


def main():
    print("=" * 60)
    print("THE_FX.TRADER.BOT.ZW ANDROID BRIDGE")
    print("=" * 60)
    print(f"API: http://{HOST}:{PORT}")
    print("Signal-only: TRUE")
    print("Automatic trading: DISABLED")
    print("Primary market: XAUUSD")
    print("=" * 60)

    backend_thread = threading.Thread(
        target=run_backend,
        name="THE_FX_BACKEND",
        daemon=True,
    )

    backend_thread.start()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        AndroidBridgeHandler,
    )

    print("[BRIDGE] Android API started.")
    print("[BRIDGE] Waiting for Android APK connection...")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[BRIDGE] Stopping...")
    finally:
        runtime.stop()
        server.server_close()
        print("[BRIDGE] Stopped.")


if __name__ == "__main__":
    main()
