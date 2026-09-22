import unittest
from types import SimpleNamespace

from core.alert_integration import AlertIntegration


class FakeSignalEngine:
    def __init__(self, result):
        self.result = result

    def evaluate(self, **kwargs):
        return self.result


class FakeDispatcher:
    def __init__(self, result):
        self.result = result
        self.dispatched = []

    def dispatch(self, signal, now=None):
        self.dispatched.append((signal, now))
        return self.result

    def android_available(self):
        return True

    def settings(self):
        return {"alerts_enabled": True}

    def alert_history(self):
        return []

    def feedback_history(self):
        return []

    def test_android(self):
        return {"notification": True, "vibration": True}


class AlertIntegrationTest(unittest.TestCase):

    def make_signal(self, direction="BUY"):
        return SimpleNamespace(
            direction=direction,
            symbol="XAUUSD",
            timeframe="M1",
            strength=8,
        )

    def test_buy_dispatches(self):
        signal = self.make_signal("BUY")
        protected = object()

        engine = FakeSignalEngine(
            (signal, protected, "PROTECTED")
        )

        dispatcher = FakeDispatcher({
            "status": "DISPATCHED",
            "reason": "ALERT_SENT_TO_ANDROID",
        })

        integration = AlertIntegration(engine, dispatcher)

        result = integration.process(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertEqual(result.status, "DISPATCHED")
        self.assertEqual(
            result.reason,
            "ALERT_SENT_TO_ANDROID",
        )
        self.assertEqual(len(dispatcher.dispatched), 1)

    def test_sell_dispatches(self):
        signal = self.make_signal("SELL")
        protected = object()

        engine = FakeSignalEngine(
            (signal, protected, "PROTECTED")
        )

        dispatcher = FakeDispatcher({
            "status": "DISPATCHED",
            "reason": "ALERT_SENT_TO_ANDROID",
        })

        integration = AlertIntegration(engine, dispatcher)

        result = integration.process(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertEqual(result.status, "DISPATCHED")

    def test_wait_does_not_dispatch(self):
        signal = self.make_signal("WAIT")

        engine = FakeSignalEngine(
            (signal, None, "WAIT")
        )

        dispatcher = FakeDispatcher({
            "status": "DISPATCHED",
            "reason": "ALERT_SENT_TO_ANDROID",
        })

        integration = AlertIntegration(engine, dispatcher)

        result = integration.process(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertEqual(result.status, "WAIT")
        self.assertEqual(len(dispatcher.dispatched), 0)

    def test_unprotected_signal_blocked(self):
        signal = self.make_signal("BUY")

        engine = FakeSignalEngine(
            (signal, None, "COOLDOWN")
        )

        dispatcher = FakeDispatcher({
            "status": "DISPATCHED",
        })

        integration = AlertIntegration(engine, dispatcher)

        result = integration.process(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(len(dispatcher.dispatched), 0)

    def test_dispatcher_block_is_returned(self):
        signal = self.make_signal("BUY")
        protected = object()

        engine = FakeSignalEngine(
            (signal, protected, "PROTECTED")
        )

        dispatcher = FakeDispatcher({
            "status": "BLOCKED",
            "reason": "LOW_STRENGTH",
        })

        integration = AlertIntegration(engine, dispatcher)

        result = integration.process(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertEqual(result.status, "BLOCKED")
        self.assertEqual(result.reason, "LOW_STRENGTH")

    def test_invalid_engine_response(self):
        engine = FakeSignalEngine(None)

        dispatcher = FakeDispatcher({
            "status": "DISPATCHED",
        })

        integration = AlertIntegration(engine, dispatcher)

        result = integration.process(
            "XAUUSD",
            "M1",
            [],
        )

        self.assertEqual(result.status, "ERROR")
        self.assertEqual(
            result.reason,
            "INVALID_SIGNAL_ENGINE_RESPONSE",
        )

    def test_android_available(self):
        engine = FakeSignalEngine(
            (self.make_signal(), object(), "PROTECTED")
        )

        dispatcher = FakeDispatcher({})

        integration = AlertIntegration(engine, dispatcher)

        self.assertTrue(
            integration.android_available()
        )

    def test_settings_available(self):
        engine = FakeSignalEngine(
            (self.make_signal(), object(), "PROTECTED")
        )

        dispatcher = FakeDispatcher({})

        integration = AlertIntegration(engine, dispatcher)

        self.assertEqual(
            integration.settings()["alerts_enabled"],
            True,
        )

    def test_histories_available(self):
        engine = FakeSignalEngine(
            (self.make_signal(), object(), "PROTECTED")
        )

        dispatcher = FakeDispatcher({})

        integration = AlertIntegration(engine, dispatcher)

        self.assertEqual(
            integration.alert_history(),
            [],
        )

        self.assertEqual(
            integration.feedback_history(),
            [],
        )

    def test_android_test_available(self):
        engine = FakeSignalEngine(
            (self.make_signal(), object(), "PROTECTED")
        )

        dispatcher = FakeDispatcher({})

        integration = AlertIntegration(engine, dispatcher)

        result = integration.test_android()

        self.assertTrue(result["notification"])
        self.assertTrue(result["vibration"])

    def test_no_trade_methods(self):
        engine = FakeSignalEngine(
            (self.make_signal(), object(), "PROTECTED")
        )

        dispatcher = FakeDispatcher({})

        integration = AlertIntegration(engine, dispatcher)

        forbidden = [
            "buy",
            "sell",
            "place_order",
            "open_trade",
            "close_trade",
            "modify_trade",
            "execute_trade",
        ]

        for method in forbidden:
            self.assertFalse(
                hasattr(integration, method),
                method,
            )


if __name__ == "__main__":
    unittest.main()
