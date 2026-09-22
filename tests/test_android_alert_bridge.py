import unittest

from core.android_alert_bridge import (
    AndroidAlertBridge,
)


class FakeResult:

    def __init__(
        self,
        returncode=0,
        stdout="",
        stderr="",
    ):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class FakeRunner:

    def __init__(
        self,
        returncode=0,
    ):
        self.returncode = returncode
        self.commands = []

    def __call__(
        self,
        command,
    ):

        self.commands.append(
            command
        )

        return FakeResult(
            returncode=self.returncode
        )


class AndroidAlertBridgeTest(
    unittest.TestCase
):

    def test_available(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        self.assertTrue(
            bridge.available()
        )

        self.assertEqual(
            runner.commands[0][0],
            "which",
        )

    def test_notification(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = bridge.notify(
            "BUY XAUUSD",
            "Strength 8/10",
        )

        self.assertTrue(
            result.success
        )

        self.assertEqual(
            result.action,
            "NOTIFICATION",
        )

        command = runner.commands[-1]

        self.assertEqual(
            command[0],
            "termux-notification",
        )

        self.assertIn(
            "--title",
            command,
        )

        self.assertIn(
            "--content",
            command,
        )

    def test_vibration(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = bridge.vibrate(
            700
        )

        self.assertTrue(
            result.success
        )

        self.assertEqual(
            result.action,
            "VIBRATION",
        )

        command = runner.commands[-1]

        self.assertEqual(
            command[0],
            "termux-vibrate",
        )

        self.assertIn(
            "700",
            command,
        )

    def test_sound_without_file_is_blocked(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = bridge.play_sound()

        self.assertFalse(
            result.success
        )

        self.assertEqual(
            result.action,
            "SOUND",
        )

        self.assertEqual(
            len(runner.commands),
            0,
        )

    def test_sound_command(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = bridge.play_sound(
            "/sdcard/buy.mp3"
        )

        self.assertTrue(
            result.success
        )

        command = runner.commands[-1]

        self.assertEqual(
            command[0],
            "termux-media-player",
        )

        self.assertIn(
            "/sdcard/buy.mp3",
            command,
        )

    def test_send_alert(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = bridge.send_alert(
            direction="BUY",
            symbol="XAUUSD",
            timeframe="M1",
            strength=8,
            message="Trend confirmation",
            vibration_ms=500,
        )

        self.assertTrue(
            result["notification"].success
        )

        self.assertTrue(
            result["vibration"].success
        )

        self.assertIsNone(
            result["sound"]
        )

        self.assertEqual(
            len(runner.commands),
            2,
        )

    def test_test_notification(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = (
            bridge.test_notification()
        )

        self.assertTrue(
            result.success
        )

    def test_test_vibration(self):

        runner = FakeRunner()

        bridge = AndroidAlertBridge(
            runner
        )

        result = (
            bridge.test_vibration()
        )

        self.assertTrue(
            result.success
        )

    def test_command_failure(self):

        runner = FakeRunner(
            returncode=1
        )

        bridge = AndroidAlertBridge(
            runner
        )

        result = bridge.notify(
            "TEST",
            "Failure",
        )

        self.assertFalse(
            result.success
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
            dir(AndroidAlertBridge)
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
