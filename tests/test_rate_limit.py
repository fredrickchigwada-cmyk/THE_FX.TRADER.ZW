import time
import unittest

from core.deriv_ws import DerivWebSocket


class RateLimitTests(unittest.TestCase):

    def test_initially_not_rate_limited(self):
        client = DerivWebSocket()

        self.assertFalse(
            client.is_rate_limited()
        )

    def test_rate_limit_state(self):
        client = DerivWebSocket()

        client._handle_rate_limit()

        self.assertTrue(
            client.is_rate_limited()
        )

        self.assertGreater(
            client.rate_limit_remaining(),
            0
        )

    def test_rate_limit_backoff_increases(self):
        client = DerivWebSocket()

        first = client.backoff_seconds

        client._handle_rate_limit()

        second = client.backoff_seconds

        self.assertGreater(
            second,
            first
        )

    def test_rate_limit_has_maximum(self):
        client = DerivWebSocket()

        for _ in range(20):
            client._handle_rate_limit()

        self.assertLessEqual(
            client.backoff_seconds,
            client.MAX_BACKOFF
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
