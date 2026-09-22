import time
import unittest

from core.deriv_ws import DerivWebSocket, DerivRateLimitError


class DerivLiveConnectionTests(unittest.TestCase):

    def test_real_deriv_connection(self):
        connected = []
        errors = []

        def on_open():
            connected.append(True)
            print("[DERIV] WebSocket connected")

        def on_error(error):
            errors.append(error)
            print(f"[DERIV] WebSocket ERROR: {error!r}")

        client = DerivWebSocket(
            on_open=on_open,
            on_error=on_error,
        )

        try:
            client.connect()

            deadline = time.time() + 10

            while time.time() < deadline:
                if connected:
                    break
                time.sleep(0.25)

            self.assertTrue(
                connected,
                "Could not establish a Deriv WebSocket connection."
            )

            print("[DERIV] Connection test passed")

        finally:
            client.stop()

    def test_live_tick_reception(self):
        connected = []
        ticks = []
        errors = []

        def on_open():
            connected.append(True)
            print("[DERIV] WebSocket connected")

        def on_message(data):
            print(f"[DERIV] Message: {data}")

            if data.get("msg_type") == "tick":
                ticks.append(data)

        def on_error(error):
            errors.append(error)
            print(f"[DERIV] WebSocket ERROR: {error!r}")

        client = DerivWebSocket(
            on_message=on_message,
            on_error=on_error,
            on_open=on_open,
        )

        try:
            client.connect()

            deadline = time.time() + 10

            while time.time() < deadline:
                if connected:
                    break
                time.sleep(0.25)

            self.assertTrue(
                connected,
                "Could not establish a Deriv WebSocket connection."
            )

            # Only make one live request.
            try:
                client.subscribe_ticks("1HZ100V")
            except DerivRateLimitError as exc:
                self.skipTest(
                    f"Local rate protection blocked request: {exc}"
                )

            deadline = time.time() + 10

            while time.time() < deadline:
                if ticks:
                    break

                # A server-side rate limit is not a software failure.
                if any(
                    isinstance(error, DerivRateLimitError)
                    for error in errors
                ):
                    self.skipTest(
                        "Deriv server rate limit is currently active."
                    )

                time.sleep(0.25)

            self.assertTrue(
                ticks,
                "No live tick received within the test window."
            )

            print("[DERIV] Live tick reception passed")

        finally:
            client.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
