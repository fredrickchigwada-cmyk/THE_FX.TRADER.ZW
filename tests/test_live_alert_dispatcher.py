import os
import tempfile
import unittest

from core.alert_persistence import AlertPersistence
from core.android_alert_bridge import AndroidAlertBridge
from core.persistent_alert_router import PersistentAlertRouter
from core.live_alert_dispatcher import LiveAlertDispatcher
from core.signal_engine import Signal


class FakeResult:

    def __init__(self, returncode=0):
        self.returncode = returncode
        self.stdout = ""
        self.stderr = ""


class FakeAndroidRunner:

    def __init__(self):
        self.commands = []

    def __call__(self, command):

        self.commands.append(command)

        return FakeResult(0)


def make_signal(
    direction="BUY",
    strength=8,
    valid=True,
    symbol="XAUUSD",
    timeframe="M1",
):

    return Signal(
        symbol=symbol,
        timeframe=timeframe,
        direction=direction,
        strength=strength,
        confirmations=5,
        entry=100.0,
        stop_loss=95.0,
        tp1=105.0,
        tp2=110.0,
        invalidation=95.0,
        explanation="Controlled test signal",
        candle_confirmed=True,
        valid=valid,
    )


class LiveAlertDispatcherTest(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        path = os.path.join(
            self.temp_dir.name,
            "alert_settings.json",
        )

        router = PersistentAlertRouter(
            AlertPersistence(path)
        )

        runner = FakeAndroidRunner()

        android = AndroidAlertBridge(
            runner
        )

        self.runner = runner

        self.dispatcher = LiveAlertDispatcher(
            alert_router=router,
            android=android,
        )

    def tearDown(self):

        self.temp_dir.cleanup()

    def test_buy_dispatches(self):

        result = self.dispatcher.dispatch(
            make_signal("BUY"),
            now=1000,
        )

        self.assertEqual(
            result["status"],
            "DISPATCHED",
        )

        self.assertEqual(
            result["reason"],
            "ALERT_SENT_TO_ANDROID",
        )

        self.assertIsNotNone(
            result["alert"]
        )

        self.assertIn(
            "notification",
            result["android"],
        )

    def test_sell_dispatches(self):

        result = self.dispatcher.dispatch(
            make_signal("SELL"),
            now=1000,
        )

        self.assertEqual(
            result["status"],
            "DISPATCHED",
        )

        self.assertEqual(
            result["alert"].direction,
            "SELL",
        )

    def test_invalid_signal_blocked(self):

        result = self.dispatcher.dispatch(
            make_signal(
                valid=False
            ),
            now=1000,
        )

        self.assertEqual(
            result["status"],
            "BLOCKED",
        )

        self.assertEqual(
            result["reason"],
            "INVALID_SIGNAL",
        )

        self.assertEqual(
            len(self.runner.commands),
            0,
        )

    def test_disabled_market_blocked(self):

        result = self.dispatcher.dispatch(
            make_signal(
                symbol="EURUSD"
            ),
            now=1000,
        )

        self.assertEqual(
            result["status"],
            "BLOCKED",
        )

        self.assertEqual(
            result["reason"],
            "MARKET_DISABLED",
        )

        self.assertEqual(
            len(self.runner.commands),
            0,
        )

    def test_low_strength_blocked(self):

        result = self.dispatcher.dispatch(
            make_signal(
                strength=3
            ),
            now=1000,
        )

        self.assertEqual(
            result["status"],
            "BLOCKED",
        )

        self.assertEqual(
            result["reason"],
            "STRENGTH_TOO_LOW",
        )

    def test_duplicate_blocked(self):

        first = self.dispatcher.dispatch(
            make_signal("BUY"),
            now=1000,
        )

        second = self.dispatcher.dispatch(
            make_signal("BUY"),
            now=1100,
        )

        self.assertEqual(
            first["status"],
            "DISPATCHED",
        )

        self.assertEqual(
            second["status"],
            "BLOCKED",
        )

        self.assertEqual(
            second["reason"],
            "ALERT_COOLDOWN",
        )

    def test_android_notification_command(self):

        self.dispatcher.dispatch(
            make_signal("BUY"),
            now=1000,
        )

        notification_commands = [
            command
            for command in self.runner.commands
            if command[0]
            == "termux-notification"
        ]

        self.assertEqual(
            len(notification_commands),
            1,
        )

    def test_android_vibration_command(self):

        self.dispatcher.dispatch(
            make_signal("BUY"),
            now=1000,
        )

        vibration_commands = [
            command
            for command in self.runner.commands
            if command[0]
            == "termux-vibrate"
        ]

        self.assertEqual(
            len(vibration_commands),
            1,
        )

    def test_android_test(self):

        result = (
            self.dispatcher.test_android()
        )

        self.assertTrue(
            result["notification"].success
        )

        self.assertTrue(
            result["vibration"].success
        )

    def test_android_available(self):

        self.assertTrue(
            self.dispatcher.android_available()
        )

    def test_settings_available(self):

        settings = (
            self.dispatcher.settings()
        )

        self.assertIn(
            "config",
            settings,
        )

    def test_history_available(self):

        self.dispatcher.dispatch(
            make_signal("BUY"),
            now=1000,
        )

        self.assertEqual(
            len(
                self.dispatcher.alert_history()
            ),
            1,
        )

    def test_no_trade_methods(self):

        forbidden = {
            "buy",
            "sell",
            "place_order",
            "modify_order",
            "close_trade",
            "execute_trade",
        }

        available = set(
            dir(LiveAlertDispatcher)
        )

        self.assertTrue(
            forbidden.isdisjoint(
                available
            )
        )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )
