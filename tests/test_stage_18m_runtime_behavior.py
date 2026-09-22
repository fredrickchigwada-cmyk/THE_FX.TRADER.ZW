import unittest

from core.production_runtime import ProductionRuntime


class FakeWebSocket:
    def __init__(self, connected=False, rate_limited=False, stale=False):
        self.connected = connected
        self.rate_limited = rate_limited
        self.stale = stale
        self.connect_calls = 0
        self.active_symbol_requests = 0

    def connect(self):
        self.connect_calls += 1
        self.connected = True

    def request_active_symbols(self):
        self.active_symbol_requests += 1

    def is_rate_limited(self):
        return self.rate_limited

    def is_stale(self, seconds):
        return self.stale


class FakeNewsFeed:
    def __init__(self):
        self.refresh_calls = 0

    def refresh(self):
        self.refresh_calls += 1

    def xauusd_risk(self):
        return {
            "news_available": True,
            "risk": "MEDIUM",
            "bias": "BULLISH",
            "fresh_items": 2,
        }

    def snapshot(self):
        return {
            "news_available": True,
            "risk": "MEDIUM",
            "bias": "BULLISH",
            "fresh_items": 2,
        }

    def fresh_xauusd_news(self):
        return [{"title": "Test XAUUSD news"}]


class Stage18MRuntimeBehaviorTest(unittest.TestCase):

    def make_runtime(self):
        runtime = ProductionRuntime()
        runtime.ws = FakeWebSocket()
        runtime.news_feed = FakeNewsFeed()
        return runtime

    def test_connect_updates_connection_state(self):
        runtime = self.make_runtime()

        result = runtime.connect()

        self.assertTrue(result)
        self.assertTrue(runtime.status.connected)
        self.assertTrue(runtime.status.healthy)
        self.assertEqual(runtime.ws.connect_calls, 1)

        runtime.stop()

    def test_subscribe_primary_requests_discovery(self):
        runtime = self.make_runtime()
        runtime.status.connected = True

        result = runtime.subscribe_primary()

        self.assertTrue(result)
        self.assertEqual(runtime.ws.active_symbol_requests, 1)
        self.assertFalse(runtime.status.rate_limited)

        runtime.stop()

    def test_rate_limit_prevents_discovery_request(self):
        runtime = self.make_runtime()
        runtime.status.connected = True
        runtime.ws.rate_limited = True

        result = runtime.subscribe_primary()

        self.assertFalse(result)
        self.assertEqual(runtime.ws.active_symbol_requests, 0)
        self.assertTrue(runtime.status.rate_limited)
        self.assertIn("rate-limited", runtime.status.last_error)

        runtime.stop()

    def test_health_check_healthy_connection(self):
        runtime = self.make_runtime()
        runtime.ws.connected = True
        runtime.ws.rate_limited = False
        runtime.ws.stale = False

        result = runtime.health_check()

        self.assertTrue(result)
        self.assertTrue(runtime.status.connected)
        self.assertFalse(runtime.status.stale)
        self.assertFalse(runtime.status.rate_limited)
        self.assertTrue(runtime.status.healthy)

        runtime.stop()

    def test_health_check_rejects_stale_data(self):
        runtime = self.make_runtime()
        runtime.ws.connected = True
        runtime.ws.rate_limited = False
        runtime.ws.stale = True

        result = runtime.health_check()

        self.assertFalse(result)
        self.assertTrue(runtime.status.stale)
        self.assertFalse(runtime.status.healthy)

        runtime.stop()

    def test_refresh_news_updates_status(self):
        runtime = self.make_runtime()

        result = runtime.refresh_news(force=True)

        self.assertIsNotNone(result)
        self.assertEqual(runtime.news_feed.refresh_calls, 1)
        self.assertTrue(runtime.status.news_available)
        self.assertEqual(runtime.status.news_risk, "MEDIUM")
        self.assertEqual(runtime.status.news_bias, "BULLISH")
        self.assertEqual(runtime.status.news_items, 2)

        runtime.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
