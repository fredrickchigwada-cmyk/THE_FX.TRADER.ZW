import time
import unittest

from core.watchdog import Watchdog, SafetyController
from core.system_controller import SystemController


class TestStage12(unittest.TestCase):

    def test_watchdog_healthy(self):
        wd = Watchdog(
            check_fn=lambda: True,
            interval=1,
        )

        self.assertTrue(wd.check_once())

        status = wd.snapshot()

        self.assertTrue(status.healthy)
        self.assertTrue(status.connected)
        self.assertFalse(status.stale)

    def test_watchdog_reconnect(self):
        calls = {"check": 0, "reconnect": 0}

        def check():
            calls["check"] += 1
            return False

        def reconnect():
            calls["reconnect"] += 1
            return True

        wd = Watchdog(
            check_fn=check,
            reconnect_fn=reconnect,
            interval=1,
            reconnect_delay=0,
        )

        self.assertFalse(wd.check_once())

        status = wd.snapshot()

        self.assertEqual(status.reconnects, 1)
        self.assertTrue(status.connected)

    def test_watchdog_exception(self):
        def check():
            raise RuntimeError("test failure")

        wd = Watchdog(
            check_fn=check,
            interval=1,
        )

        self.assertFalse(wd.check_once())

        self.assertEqual(
            wd.snapshot().last_error,
            "test failure",
        )

    def test_watchdog_start_stop(self):
        wd = Watchdog(
            check_fn=lambda: True,
            interval=1,
        )

        self.assertTrue(wd.start())

        time.sleep(0.05)

        self.assertTrue(wd.snapshot().running)

        self.assertTrue(wd.stop())

        self.assertFalse(wd.snapshot().running)

    def test_safety_controller(self):
        safety = SafetyController()

        self.assertTrue(safety.allow_analysis())

        safety.stop()

        self.assertTrue(safety.is_stopped())
        self.assertFalse(safety.allow_analysis())

        safety.reset()

        self.assertFalse(safety.is_stopped())
        self.assertTrue(safety.allow_analysis())

    def test_system_controller(self):
        controller = SystemController(
            connection_check=lambda: True,
            watchdog_interval=1,
        )

        self.assertTrue(controller.start())

        time.sleep(0.05)

        status = controller.status()

        self.assertTrue(status.running)

        controller.stop()

    def test_emergency_stop(self):
        controller = SystemController(
            connection_check=lambda: True,
            watchdog_interval=1,
        )

        controller.start()

        time.sleep(0.05)

        controller.emergency_stop()

        self.assertTrue(
            controller.status().emergency_stop
        )

        self.assertFalse(
            controller.can_analyze()
        )

    def test_no_trade_methods(self):
        controller = SystemController(
            connection_check=lambda: True
        )

        forbidden = [
            "buy",
            "sell",
            "place_order",
            "modify_order",
            "close_order",
            "execute_trade",
        ]

        for name in forbidden:
            self.assertFalse(hasattr(controller, name))


if __name__ == "__main__":
    unittest.main()
